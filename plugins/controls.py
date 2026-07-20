"""
Playback control commands: /pause /resume /skip /stop /queue /nowplaying
"""

from pyrogram import Client, filters
from pyrogram.types import Message

from helpers.queue import queue_manager
import core.call as call_module


def register(app: Client):

    @app.on_message(filters.command("pause") & filters.group)
    async def pause_cmd(client: Client, message: Message):
        await call_module.call_manager.pause(message.chat.id)
        await message.reply_text("⏸ Paused.")

    @app.on_message(filters.command("resume") & filters.group)
    async def resume_cmd(client: Client, message: Message):
        await call_module.call_manager.resume(message.chat.id)
        await message.reply_text("▶️ Resumed.")

    @app.on_message(filters.command("stop") & filters.group)
    async def stop_cmd(client: Client, message: Message):
        await call_module.call_manager.leave(message.chat.id)
        await message.reply_text("⏹ Stopped and left the voice chat.")

    @app.on_message(filters.command(["skip", "next"]) & filters.group)
    async def skip_cmd(client: Client, message: Message):
        chat_id = message.chat.id
        next_track = queue_manager.pop_next(chat_id)
        if not next_track:
            await call_module.call_manager.leave(chat_id)
            await message.reply_text("⏭ Skipped. Queue is empty, leaving voice chat.")
            return

        queue_manager.set_playing(chat_id, next_track)
        await call_module.call_manager.change_stream(chat_id, next_track["stream_url"])
        await message.reply_text(f"⏭ Skipped. Now playing **{next_track['title']}**")

    @app.on_message(filters.command(["queue", "q"]) & filters.group)
    async def queue_cmd(client: Client, message: Message):
        chat_id = message.chat.id
        current = queue_manager.now_playing(chat_id)
        pending = queue_manager.peek_all(chat_id)

        if not current:
            await message.reply_text("Queue is empty. Use `/play <song>` to start.")
            return

        lines = [f"🎶 **Now Playing:** {current['title']}"]
        if pending:
            lines.append("\n**Up next:**")
            for i, t in enumerate(pending, start=1):
                lines.append(f"{i}. {t['title']}")
        await message.reply_text("\n".join(lines))

    @app.on_message(filters.command(["nowplaying", "np"]) & filters.group)
    async def now_playing_cmd(client: Client, message: Message):
        current = queue_manager.now_playing(message.chat.id)
        if not current:
            await message.reply_text("Nothing is playing right now.")
            return
        mins, secs = divmod(current["duration"], 60)
        await message.reply_text(
            f"🎶 **{current['title']}**\n⏱ {mins:02d}:{secs:02d}\n🔗 {current['webpage_url']}"
        )
