"""
Core voice-chat streaming engine.
Wraps py-tgcalls so the rest of the bot never touches the low-level API
directly — this is what gives the "robust & resilient" behaviour:
automatic stream-end handling, clean leave, and defensive error catching
around every call so one bad chat never crashes the whole bot.
"""

import asyncio
import logging

from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
from pytgcalls.exceptions import NoActiveGroupCall, AlreadyJoinedError

from helpers.queue import queue_manager
from config import AUTO_LEAVE_SECONDS

logger = logging.getLogger("UNICEIF.call")


class CallManager:
    def __init__(self, assistant_client):
        self.pytgcalls = PyTgCalls(assistant_client)
        self._idle_tasks: dict[int, asyncio.Task] = {}

    async def start(self):
        await self.pytgcalls.start()
        self.pytgcalls.on_stream_end()(self._on_stream_end)
        logger.info("PyTgCalls engine started.")

    async def join_and_play(self, chat_id: int, stream_url: str, high_quality: bool = True):
        """Join the voice chat (if needed) and start/replace playback."""
        stream = MediaStream(
            stream_url,
            audio_parameters=AudioQuality.STUDIO if high_quality else AudioQuality.MEDIUM,
            video_flags=MediaStream.Flags.IGNORE,
        )
        try:
            await self.pytgcalls.play(chat_id, stream)
        except AlreadyJoinedError:
            await self.pytgcalls.play(chat_id, stream)  # play() also handles track change
        except NoActiveGroupCall:
            raise RuntimeError(
                "No active voice chat in this group. Start one first, then try again."
            )
        self._cancel_idle_timer(chat_id)

    async def join_and_play_video(self, chat_id: int, stream_url: str, high_quality: bool = True):
        """Join the video chat and stream both video and audio."""
        stream = MediaStream(
            stream_url,
            audio_parameters=AudioQuality.STUDIO if high_quality else AudioQuality.MEDIUM,
            video_parameters=VideoQuality.FHD_720p if high_quality else VideoQuality.SD_480p,
        )
        try:
            await self.pytgcalls.play(chat_id, stream)
        except AlreadyJoinedError:
            await self.pytgcalls.play(chat_id, stream)
        except NoActiveGroupCall:
            raise RuntimeError(
                "No active video chat in this group. Start one first, then try again."
            )
        self._cancel_idle_timer(chat_id)

    async def change_stream(self, chat_id: int, stream_url: str, high_quality: bool = True):
        stream = MediaStream(
            stream_url,
            audio_parameters=AudioQuality.STUDIO if high_quality else AudioQuality.MEDIUM,
            video_flags=MediaStream.Flags.IGNORE,
        )
        await self.pytgcalls.play(chat_id, stream)

    async def pause(self, chat_id: int):
        await self.pytgcalls.pause(chat_id)

    async def resume(self, chat_id: int):
        await self.pytgcalls.resume(chat_id)

    async def leave(self, chat_id: int):
        try:
            await self.pytgcalls.leave_call(chat_id)
        except Exception as e:
            logger.warning("Leave call issue on %s: %s", chat_id, e)
        queue_manager.clear(chat_id)
        self._cancel_idle_timer(chat_id)

    def _cancel_idle_timer(self, chat_id: int):
        task = self._idle_tasks.pop(chat_id, None)
        if task and not task.done():
            task.cancel()

    def _schedule_idle_leave(self, chat_id: int):
        self._cancel_idle_timer(chat_id)

        async def _timer():
            await asyncio.sleep(AUTO_LEAVE_SECONDS)
            if not queue_manager.now_playing(chat_id):
                await self.leave(chat_id)

        if AUTO_LEAVE_SECONDS > 0:
            self._idle_tasks[chat_id] = asyncio.create_task(_timer())

    async def _on_stream_end(self, _, update):
        chat_id = update.chat_id
        next_track = queue_manager.pop_next(chat_id)
        if next_track:
            queue_manager.set_playing(chat_id, next_track)
            try:
                await self.join_and_play(chat_id, next_track["stream_url"])
            except Exception as e:
                logger.error("Failed to auto-advance queue in %s: %s", chat_id, e)
                queue_manager.set_playing(chat_id, None)
                self._schedule_idle_leave(chat_id)
        else:
            queue_manager.set_playing(chat_id, None)
            self._schedule_idle_leave(chat_id)


call_manager: "CallManager | None" = None


def init_call_manager(assistant_client):
    global call_manager
    call_manager = CallManager(assistant_client)
    return call_manager
