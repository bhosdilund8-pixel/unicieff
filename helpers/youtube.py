"""
YouTube resolution helper.
Uses yt-dlp with a chain of fallback strategies so that if one extraction
method gets rate-limited or blocked, the bot smoothly tries the next —
no cookies required.
"""

import asyncio
import yt_dlp

from config import DURATION_LIMIT_MIN

_BASE_OPTS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "geo_bypass": True,
    "nocheckcertificate": True,
    "skip_download": True,
}

# Fallback ladder: each dict is merged over _BASE_OPTS and tried in order.
_FALLBACK_CHAIN = [
    {},  # plain default client
    {"extractor_args": {"youtube": {"player_client": ["android"]}}},
    {"extractor_args": {"youtube": {"player_client": ["ios"]}}},
    {"extractor_args": {"youtube": {"player_client": ["web_embedded"]}}},
    {"extractor_args": {"youtube": {"player_client": ["tv_embedded"]}}},
]


class TrackNotFound(Exception):
    pass


class TrackTooLong(Exception):
    pass


def _extract_sync(query: str):
    last_error = None
    search_term = query if query.startswith("http") else f"ytsearch1:{query}"

    for extra in _FALLBACK_CHAIN:
        opts = {**_BASE_OPTS, **extra}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(search_term, download=False)
                if "entries" in info:
                    info = info["entries"][0]

                duration = int(info.get("duration") or 0)
                if DURATION_LIMIT_MIN and duration > DURATION_LIMIT_MIN * 60:
                    raise TrackTooLong(
                        f"Track exceeds the {DURATION_LIMIT_MIN} minute limit."
                    )

                stream_url = info.get("url")
                if not stream_url and "formats" in info:
                    audio_formats = [
                        f for f in info["formats"] if f.get("acodec") != "none"
                    ]
                    if audio_formats:
                        stream_url = audio_formats[-1]["url"]

                if not stream_url:
                    raise TrackNotFound("No playable audio stream found.")

                return {
                    "title": info.get("title", "Unknown"),
                    "duration": duration,
                    "thumbnail": info.get("thumbnail"),
                    "webpage_url": info.get("webpage_url", query),
                    "stream_url": stream_url,
                }
        except TrackTooLong:
            raise
        except Exception as e:  # noqa: BLE001 — intentional broad fallback catch
            last_error = e
            continue

    raise TrackNotFound(f"Could not resolve track after all fallbacks: {last_error}")


async def resolve(query: str) -> dict:
    """Resolve a search query or URL into playable (audio-only) track info.

    Runs the blocking yt-dlp call in a thread so it never stalls the
    bot's asyncio event loop.
    """
    return await asyncio.to_thread(_extract_sync, query)


def _extract_video_sync(query: str):
    """Resolve a combined video+audio stream for /vplay (video chats)."""
    last_error = None
    search_term = query if query.startswith("http") else f"ytsearch1:{query}"

    video_opts_chain = [
        {"format": "best[height<=720]/best"},
        {
            "format": "best[height<=720]/best",
            "extractor_args": {"youtube": {"player_client": ["android"]}},
        },
        {
            "format": "best[height<=480]/best",
            "extractor_args": {"youtube": {"player_client": ["ios"]}},
        },
        {
            "format": "best",
            "extractor_args": {"youtube": {"player_client": ["web_embedded"]}},
        },
    ]

    for extra in video_opts_chain:
        opts = {**_BASE_OPTS, **extra}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(search_term, download=False)
                if "entries" in info:
                    info = info["entries"][0]

                duration = int(info.get("duration") or 0)
                if DURATION_LIMIT_MIN and duration > DURATION_LIMIT_MIN * 60:
                    raise TrackTooLong(
                        f"Track exceeds the {DURATION_LIMIT_MIN} minute limit."
                    )

                stream_url = info.get("url")
                if not stream_url:
                    raise TrackNotFound("No playable video+audio stream found.")

                return {
                    "title": info.get("title", "Unknown"),
                    "duration": duration,
                    "thumbnail": info.get("thumbnail"),
                    "webpage_url": info.get("webpage_url", query),
                    "stream_url": stream_url,
                    "width": info.get("width"),
                    "height": info.get("height"),
                }
        except TrackTooLong:
            raise
        except Exception as e:  # noqa: BLE001
            last_error = e
            continue

    raise TrackNotFound(f"Could not resolve video after all fallbacks: {last_error}")


async def resolve_video(query: str) -> dict:
    """Resolve a search query or URL into a combined video+audio stream.

    Note: YouTube is retiring high-res progressive (video+audio-in-one)
    formats, so video quality here is capped around 720p; above that,
    video and audio come as separate files that would need local muxing.
    """
    return await asyncio.to_thread(_extract_video_sync, query)
