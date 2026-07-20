"""
Run this ONCE, locally on your own machine (not on Render), to generate
the SESSION_STRING for the assistant account that will join voice chats.

    python generate_session.py

Log in with the Telegram account you want to use as the "assistant"
(NOT your bot — a real user account, since bots can't join voice chats).
Copy the printed string into Render's SESSION_STRING environment variable.

Keep this string secret — it is equivalent to full access to that account.
"""

from pyrogram import Client

API_ID = int(input("API_ID: "))
API_HASH = input("API_HASH: ")

with Client("assistant_session_gen", api_id=API_ID, api_hash=API_HASH, in_memory=True) as app:
    print("\nYour SESSION_STRING (keep this secret):\n")
    print(app.export_session_string())
