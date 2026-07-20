"""
Minimal keep-alive HTTP server.

Render's free tier only offers Web Services (not Background Workers),
and free Web Services spin down after ~15 minutes with no HTTP traffic.
This tiny server gives Render something to bind to, and gives an external
uptime pinger (e.g. UptimeRobot) something to hit every few minutes so
the instance never sleeps.

This is a workaround, not an official Render feature — see README for
the honest limits of this approach.
"""

import os
from aiohttp import web


async def _health(request):
    return web.json_response({"status": "ok", "bot": "UNICEIF Music Bot"})


async def start_keep_alive_server():
    app = web.Application()
    app.router.add_get("/", _health)
    app.router.add_get("/health", _health)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    return runner
