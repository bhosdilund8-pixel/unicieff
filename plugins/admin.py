"""
Admin & per-key access management: /auth /deauth /tier /ping
"""

from pyrogram import Client, filters
from pyrogram.types import Message

from helpers.filters import authorize_chat, revoke_chat, get_tier, is_owner_or_sudo
from config import PING_TEXT


def register(app: Client):

    @app.on_message(filters.command("start"))
    async def start_cmd(client: Client, message: Message):
        await message.reply_text(
            "👋 **UNICEIF Music Bot**\n\n"
            "Add me to a group, start a voice chat, then use `/play <song>`.\n"
            "Use `/auth <key>` in a group to unlock your paid tier.\n"
            "Use `/help` for the full command list."
        )

    @app.on_message(filters.command("help"))
    async def help_cmd(client: Client, message: Message):
        await message.reply_text(
            "**Commands**\n"
            "`/play <song/URL>` — play or queue audio in the voice chat\n"
            "`/vplay <song/URL>` — stream video+audio in the video chat\n"
            "`/pause` `/resume` `/skip` `/stop`\n"
            "`/queue` — show the current queue\n"
            "`/nowplaying` — show current track\n"
            "`/auth <key>` — unlock a paid tier for this chat\n"
            "`/tier` — show this chat's current tier\n"
            "`/ping` — check bot status"
        )

    @app.on_message(filters.command("ping"))
    async def ping_cmd(client: Client, message: Message):
        await message.reply_text(PING_TEXT)

    @app.on_message(filters.command("auth") & filters.group)
    async def auth_cmd(client: Client, message: Message):
        if len(message.command) < 2:
            await message.reply_text("Usage: `/auth <key>`")
            return
        key = message.command[1]
        if authorize_chat(message.chat.id, key):
            tier = get_tier(message.chat.id)
            await message.reply_text(f"✅ This chat is now on the **{tier}** tier.")
        else:
            await message.reply_text("❌ Invalid key.")

    @app.on_message(filters.command("deauth") & filters.group)
    async def deauth_cmd(client: Client, message: Message):
        if not is_owner_or_sudo(message.from_user.id):
            await message.reply_text("Only the bot owner/sudo users can do that.")
            return
        revoke_chat(message.chat.id)
        await message.reply_text("Access key revoked for this chat. Reverted to free tier.")

    @app.on_message(filters.command("tier") & filters.group)
    async def tier_cmd(client: Client, message: Message):
        await message.reply_text(f"This chat's current tier: **{get_tier(message.chat.id)}**")
