"""
UNICEIF Music Bot — entrypoint.

Runs two Pyrogram clients:
  - `app`       : the bot account (BOT_TOKEN) users talk to
  - `assistant` : a userbot session that actually joins voice chats
                  (Telegram bots cannot join group calls themselves)

Then boots PyTgCalls on top of the assistant and registers all plugins.
"""

import asyncio
import logging
import sys

from pyrogram import Client

from config import API_ID, API_HASH, BOT_TOKEN, SESSION_STRING
from core.call import init_call_manager
from plugins import play, controls, admin
from keep_alive import start_keep_alive_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("UNICEIF.main")


def _require_config():
    missing = []
    if not API_ID:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not SESSION_STRING:
        missing.append("SESSION_STRING")
    if missing:
        logger.error("Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)


async def main():
    _require_config()

    app = Client(
        "uniceif_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        in_memory=True,
    )

    assistant = Client(
        "uniceif_assistant",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING,
        in_memory=True,
    )

    await start_keep_alive_server()
    logger.info("Keep-alive HTTP server started.")

    await app.start()
    await assistant.start()

    call_manager = init_call_manager(assistant)
    await call_manager.start()

    play.register(app)
    controls.register(app)
    admin.register(app)

    logger.info("UNICEIF Music Bot is up and running.")

    try:
        await asyncio.Event().wait()  # run forever
    finally:
        await app.stop()
        await assistant.stop()


if __name__ == "__main__":
    asyncio.run(main())
