"""Read-only official YouTube Data API discovery. No estimated channel revenue."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API = "https://www.googleapis.com/youtube/v3/"


def _get(endpoint: str, params: dict, key: str):
    params["key"] = key
    request = Request(API + endpoint + "?" + urlencode(params),
                      headers={"User-Agent": "Automate-ytb/0.1"})
    try:
        with urlopen(request, timeout=20) as response:
            data = json.load(response)
    except Exception as error:
        # Avoid writing raw URLs containing user API credentials to logs.
        raise RuntimeError("YouTube Data API unavailable or quota exhausted.") from None
    if "items" not in data:
        raise RuntimeError("Unexpected YouTube Data API response.")
    return data["items"]


def discover_niches(queries: list[str], *, days=90, min_views=20000,
                    max_subscribers=100000, limit=20, api_key=None):
    key = api_key or os.environ.get("YOUTUBE_API_KEY", "")
    if not key:
        raise ValueError("Set YOUTUBE_API_KEY for official YouTube research.")
    if not (1 <= days <= 365 and 1 <= limit <= 50 and len(queries) <= 10):
        raise ValueError("Use 1-365 days, at most 10 queries and a limit of 1-50.")
    if not all(2 <= len(q) <= 100 for q in queries):
        raise ValueError("Each research query must be 2-100 characters.")
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace("+00:00", "Z")
    ids = []
    for query in queries:
        found = _get("search", {"part": "snippet", "type": "video",
            "q": query, "order": "viewCount", "maxResults": 25,
            "publishedAfter": since, "safeSearch": "moderate"}, key)
        ids += [x["id"]["videoId"] for x in found if x.get("id", {}).get("videoId")]
    unique = list(dict.fromkeys(ids))[:50]
    if not unique:
        return {"method": "youtube-data-api-v3", "results": [],
                "revenueVerified": False, "note": "Search returned no qualifying videos."}
    vids = _get("videos", {"part": "snippet,statistics,contentDetails",
                         "id": ",".join(unique)}, key)
    channel_ids = list(dict.fromkeys(v.get("snippet", {}).get("channelId")
                                         for v in vids if v.get("snippet", {}).get("channelId")))
    channels = _get("channels", {"part": "snippet,statistics",
                                "id": ",".join(channel_ids[:50])}, key)
    by_channel = {c["id"]: c for c in channels}
    result = []
    for v in vids:
        stat = v.get("statistics", {})
        views = int(stat.get("viewCount", 0))
        if views < min_views:
            continue
        channel_id = v.get("snippet", {}).get("channelId", "")
        channel = by_channel.get(channel_id, {})
        subscribers = channel.get("statistics", {}).get("subscriberCount")
        if subscribers is None:
            continue
        subscribers = int(subscribers)
        if subscribers > max_subscribers:
            continue
        age = max(1., (datetime.now(timezone.utc) -
                datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
                ).total_seconds() / 86400)
        # Calculate only directly observable signals, not income or CPM/RPM.
        views_per_day = round(views / age)
        result.append({
            "channel": channel.get("snippet", {}).get("title", "unknown"),
            "channelId": channel_id,
            "subscribers": subscribers,
            "video": v["snippet"].get("title", ""),
            "url": "https://www.youtube.com/watch?v=" + v["id"],
            "views": views,
            "videoAgeDays": round(age, 1),
            "observedViewsPerDay": views_per_day,
            "nicheHypothesis": "review-manually",
            "revenueEstimate": None,
            "requiresHumanReview": True
        })
    result.sort(key=lambda x: (-x["observedViewsPerDay"], -x["views"]))
    return {"method": "youtube-data-api-v3",
            "assessedUniqueVideos": len(unique),
            "revenueVerified": False, "results": result[:limit],
            "note": "Results are video-level signals, not unsaturated niche proof. "
                    "Search API quota and audience selection bias apply."}
