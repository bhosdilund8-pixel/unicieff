"""
/play command — the core user-facing feature.
Resolves the query via yt-dlp, enforces per-tier duration limits,
and either starts playback immediately or queues the track.
"""

from pyrogram import Client, filters
from pyrogram.types import Message

from helpers.youtube import resolve, resolve_video, TrackNotFound, TrackTooLong
from helpers.queue import queue_manager
from helpers.filters import tier_limits
import core.call as call_module


def register(app: Client):

    @app.on_message(filters.command(["play", "p"]) & filters.group)
    async def play_cmd(client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply_text(
                "Usage: `/play <song name or YouTube URL>`", quote=True
            )
            return

        query = message.text.split(None, 1)[1]
        status = await message.reply_text("🔎 Searching...", quote=True)

        try:
            track = await resolve(query)
        except TrackTooLong as e:
            await status.edit_text(f"⛔ {e}")
            return
        except TrackNotFound as e:
            await status.edit_text(f"❌ Couldn't find that track.\n`{e}`")
            return

        limits = tier_limits(message.chat.id)
        max_dur = limits["max_duration_min"]
        if max_dur and track["duration"] > max_dur * 60:
            await status.edit_text(
                f"⛔ This track is longer than your plan's {max_dur} min limit. "
                f"Upgrade with `/auth <key>` for longer playback."
            )
            return

        call_manager = call_module.call_manager
        chat_id = message.chat.id

        if queue_manager.now_playing(chat_id):
            queue_manager.add(chat_id, track)
            position = len(queue_manager.peek_all(chat_id))
            await status.edit_text(
                f"➕ Queued **{track['title']}** (position #{position})"
            )
            return

        try:
            await call_manager.join_and_play(chat_id, track["stream_url"])
        except RuntimeError as e:
            await status.edit_text(f"⚠️ {e}")
            return
        except Exception as e:  # noqa: BLE001
            await status.edit_text(f"⚠️ Playback failed: `{e}`")
            return

        queue_manager.set_playing(chat_id, track)
        mins, secs = divmod(track["duration"], 60)
        await status.edit_text(
            f"🎶 **Now playing:** {track['title']}\n"
            f"⏱ {mins:02d}:{secs:02d}\n"
            f"🔗 {track['webpage_url']}"
        )

    @app.on_message(filters.command(["vplay", "vp"]) & filters.group)
    async def vplay_cmd(client: Client, message: Message):
        """Stream video + audio into a video chat (not just voice chat)."""
        if len(message.command) < 2:
            await message.reply_text(
                "Usage: `/vplay <song/URL>` — streams video+audio into a "
                "**video chat** (make sure video chat, not just voice, is started).",
                quote=True,
            )
            return

        query = message.text.split(None, 1)[1]
        status = await message.reply_text("🔎 Searching (video)...", quote=True)

        try:
            track = await resolve_video(query)
        except TrackTooLong as e:
            await status.edit_text(f"⛔ {e}")
            return
        except TrackNotFound as e:
            await status.edit_text(f"❌ Couldn't find a playable video stream.\n`{e}`")
            return

        limits = tier_limits(message.chat.id)
        max_dur = limits["max_duration_min"]
        if max_dur and track["duration"] > max_dur * 60:
            await status.edit_text(
                f"⛔ This track is longer than your plan's {max_dur} min limit."
            )
            return

        call_manager = call_module.call_manager
        chat_id = message.chat.id

        try:
            await call_manager.join_and_play_video(chat_id, track["stream_url"])
        except RuntimeError as e:
            await status.edit_text(f"⚠️ {e}")
            return
        except Exception as e:  # noqa: BLE001
            await status.edit_text(f"⚠️ Video playback failed: `{e}`")
            return

        queue_manager.set_playing(chat_id, track)
        mins, secs = divmod(track["duration"], 60)
        res = f"{track.get('width', '?')}x{track.get('height', '?')}"
        await status.edit_text(
            f"🎬 **Now streaming (video):** {track['title']}\n"
            f"⏱ {mins:02d}:{secs:02d} · {res}\n"
            f"🔗 {track['webpage_url']}"
        )
