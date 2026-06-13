"""
YouTube Data API v3 client for the exercise tutorial feature.

Quota cost per unique exercise (first fetch, cache miss):
  search.list  → 100 units
  videos.list  →   1 unit
  Total        → 101 units

With Redis caching (TTL=24h), subsequent requests for the same exercise cost
0 units. The free tier (10,000 units/day) comfortably covers the full
exercise catalog of 137 exercises: 137 × 101 = 13,837 units — worst case,
cache completely cold.
"""
import hashlib
import logging
import re

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
CACHE_TTL  = 60 * 60 * 24   # 24 hours
MAX_RESULTS = 4
TIMEOUT     = 10             # seconds


class YouTubeError(Exception):
    """Raised when the YouTube API returns an unexpected response."""


def _cache_key(query: str) -> str:
    digest = hashlib.md5(query.encode()).hexdigest()
    return f"yt_tutorials:{digest}"


def _parse_duration(iso: str) -> str:
    """
    Convert ISO 8601 duration to MM:SS or H:MM:SS.

    Examples:
      "PT4M30S" → "4:30"
      "PT1H2M5S" → "1:02:05"
      "PT30S"   → "0:30"
    """
    if not iso:
        return ""
    hours   = int(re.search(r"(\d+)H", iso).group(1)) if "H" in iso else 0
    minutes = int(re.search(r"(\d+)M", iso).group(1)) if "M" in iso else 0
    seconds = int(re.search(r"(\d+)S", iso).group(1)) if "S" in iso else 0

    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def fetch_tutorials(search_query: str) -> list[dict]:
    """
    Return up to MAX_RESULTS tutorial videos for *search_query*, sorted by
    view count descending.  Results are cached in Redis for CACHE_TTL seconds.

    Each result dict contains:
      video_id       str   YouTube video ID  (used for IFrame embed)
      title          str
      channel        str
      thumbnail      str   Medium-res thumbnail URL
      view_count     int
      duration_label str   Human-readable, e.g. "4:30"
    """
    key = _cache_key(search_query)
    cached = cache.get(key)
    if cached is not None:
        return cached

    api_key = getattr(settings, "YOUTUBE_API_KEY", "")
    if not api_key:
        raise YouTubeError("YOUTUBE_API_KEY is not configured.")

    # ── Step 1: search ───────────────────────────────────────────────────────
    try:
        search_resp = requests.get(
            SEARCH_URL,
            params={
                "q":                  search_query,
                "part":               "snippet",
                "type":               "video",
                "order":              "viewCount",
                "maxResults":         MAX_RESULTS * 2,   # over-fetch, trim after stats
                "relevanceLanguage":  "en",
                "key":                api_key,
            },
            timeout=TIMEOUT,
        )
    except requests.Timeout:
        raise YouTubeError("YouTube search request timed out.")
    except requests.RequestException as exc:
        raise YouTubeError(f"YouTube search network error: {exc}")

    if search_resp.status_code != 200:
        logger.error("YouTube search returned %s", search_resp.status_code)
        raise YouTubeError(f"YouTube search failed (HTTP {search_resp.status_code}).")

    items       = search_resp.json().get("items", [])
    video_ids   = [
        item["id"]["videoId"]
        for item in items
        if item.get("id", {}).get("kind") == "youtube#video"
    ]

    if not video_ids:
        cache.set(key, [], CACHE_TTL)
        return []

    # ── Step 2: fetch statistics & content details ───────────────────────────
    try:
        stats_resp = requests.get(
            VIDEOS_URL,
            params={
                "id":   ",".join(video_ids),
                "part": "snippet,statistics,contentDetails",
                "key":  api_key,
            },
            timeout=TIMEOUT,
        )
    except requests.Timeout:
        raise YouTubeError("YouTube statistics request timed out.")
    except requests.RequestException as exc:
        raise YouTubeError(f"YouTube statistics network error: {exc}")

    if stats_resp.status_code != 200:
        logger.error("YouTube videos.list returned %s", stats_resp.status_code)
        raise YouTubeError(f"YouTube statistics failed (HTTP {stats_resp.status_code}).")

    videos = []
    for item in stats_resp.json().get("items", []):
        snippet  = item.get("snippet", {})
        stats    = item.get("statistics", {})
        details  = item.get("contentDetails", {})
        thumbs   = snippet.get("thumbnails", {})

        # Prefer medium thumbnail, fall back to default
        thumb_url = (
            thumbs.get("medium", {}).get("url")
            or thumbs.get("default", {}).get("url")
            or ""
        )

        videos.append({
            "video_id":      item["id"],
            "title":         snippet.get("title", ""),
            "channel":       snippet.get("channelTitle", ""),
            "thumbnail":     thumb_url,
            "view_count":    int(stats.get("viewCount", 0)),
            "duration_label": _parse_duration(details.get("duration", "")),
        })

    # Sort by view count (descending) and trim to MAX_RESULTS
    videos.sort(key=lambda v: v["view_count"], reverse=True)
    result = videos[:MAX_RESULTS]

    cache.set(key, result, CACHE_TTL)
    return result
