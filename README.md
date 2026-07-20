# UNICEIF Music Bot

A Telegram voice-chat music bot built on Pyrogram + PyTgCalls + yt-dlp.

- No cookies needed — multi-client fallback chain (android/ios/web/tv embed)
- Per-chat queue, pause/resume/skip/stop
- Per-key tiered access (Free → Pro → Enterprise)
- Auto-leaves idle voice chats to save resources
- Deploys straight to Render as a background worker

## How it actually works (read this first)

Telegram **bots cannot join voice chats** — only real user accounts can.
So this project runs two Telegram clients:

1. **The bot** (`BOT_TOKEN`) — what users type commands to.
2. **The assistant** (`SESSION_STRING`) — a normal user account that
   silently joins the voice chat and streams the audio. You must control
   this account (it can be a throwaway account, not your personal one).

This two-client pattern is standard for every Telegram VC music bot —
there's no way around it, since it's how Telegram's voice chat API works.

## What you need to prepare before deploying

1. **API_ID / API_HASH** — create an app at https://my.telegram.org
2. **BOT_TOKEN** — create a bot with [@BotFather](https://t.me/BotFather)
3. **SESSION_STRING** — run `python generate_session.py` **locally on your
   own computer** (never on a server you don't fully trust) and log in
   with the account you want as the assistant. Copy the printed string.
4. **OWNER_ID** — your numeric Telegram user ID (get it from
   [@userinfobot](https://t.me/userinfobot))
5. A Telegram **group** where:
   - Both the bot and the assistant account are members
   - The assistant is promoted to admin (needed to manage voice chats
     reliably in some groups)
   - A voice chat has been started

## Local test run

```bash
git clone <your-fork-url>
cd UNICEIF-MusicBot
pip install -r requirements.txt
cp .env.example .env   # then fill in real values
export $(cat .env | xargs)   # or use a process manager that loads .env
python main.py
```

## Deploying on Render

1. Push this folder to your own GitHub repo.
2. On Render: **New → Blueprint** → point it at your repo (uses `render.yaml`).
   Alternatively: **New → Background Worker** → connect repo → Environment: Docker.
3. Fill in the environment variables Render prompts for (the ones marked
   `sync: false` in `render.yaml`): `API_ID`, `API_HASH`, `BOT_TOKEN`,
   `SESSION_STRING`, `OWNER_ID`, `SUDO_USERS`, `ACCESS_KEYS`.
4. Deploy. Render builds the Docker image (includes ffmpeg) and starts
   `python main.py` as a long-running worker — this is what gives you
   24/7 uptime as long as your Render plan keeps the worker running
   (free-tier workers on Render can spin down on inactivity — use a
   paid worker plan for guaranteed always-on hosting).

## Commands

| Command | Description |
|---|---|
| `/play <song/URL>` | Play or queue a track |
| `/pause` `/resume` | Pause / resume playback |
| `/skip` | Skip to next queued track |
| `/stop` | Stop and leave the voice chat |
| `/queue` | Show current queue |
| `/nowplaying` | Show currently playing track |
| `/auth <key>` | Unlock a paid tier for this chat |
| `/tier` | Show this chat's tier |
| `/ping` | Health check |

## Tiers & access keys

Set `ACCESS_KEYS` as `key:tier` pairs, comma-separated, e.g.:

```
ACCESS_KEYS=free-demo:free,pro-demo:pro,ent-demo:enterprise
```

Users run `/auth pro-demo` in their group to unlock that tier for that
chat. Tiers currently gate max track duration — extend `helpers/filters.py`
to gate other features (concurrent streams, bitrate, etc.) as you grow.

## Honest notes on the claims in the spec

- **"No cookies needed"**: true as implemented — yt-dlp fallback clients
  avoid needing browser cookies for most public videos. Some
  age-restricted or region-locked videos may still fail; that's a
  YouTube-side restriction, not something any bot can bypass reliably.
- **"0 lag / smooth"**: actual stream quality depends on your Render
  instance's CPU/bandwidth and Telegram's own voice chat infrastructure.
  `AudioQuality.STUDIO` is used by default; drop to `MEDIUM` in
  `core/call.py` if you're on a small instance and see buffering.
- **"Free to Enterprise tiers"**: the tiering logic is real and working,
  but it's enforced entirely by your bot (in-memory here) — for
  production-grade billing you'll want to back `ACCESS_KEYS` and
  `_authorized_chats` with a real database instead of the in-memory
  dict shipped here.
- **YouTube's Terms of Service** restrict downloading/streaming content
  outside their own player for many use cases — you're responsible for
  how you operate this bot in your jurisdiction and under YouTube's ToS.

## Extending

- Swap `helpers/queue.py`'s in-memory dict for Redis to survive restarts
  and scale across multiple worker instances.
- Add Spotify/SoundCloud resolvers alongside `helpers/youtube.py`.
- Add a `/broadcast` admin command reading from `LOG_GROUP_ID` for
  ops alerts.
