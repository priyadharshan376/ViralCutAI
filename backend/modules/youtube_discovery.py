import math
import re
import logging
from typing import List, Dict, Any, Optional
import yt_dlp

from backend.modules.youtube_download import get_base_ydl_opts

logger = logging.getLogger(__name__)

# Curated high-clip-yield & high-views niche presets
DISCOVERY_PRESETS: List[Dict[str, str]] = [
    {
        "id": "millionaire_mindset",
        "name": "💰 Motivation & Millionaire Mindset",
        "query": "millionaire mindset discipline success habits speech interview",
        "description": "High-retention wealth, discipline, and millionaire mindset talks"
    },
    {
        "id": "podcast_clips",
        "name": "🎙️ Podcast Clips",
        "query": "podcast full episode best moments interview life advice",
        "description": "Long-form spoken podcasts packed with viral moments & debates"
    },
    {
        "id": "luxury_lifestyle",
        "name": "💎 Luxury & Rich Lifestyle",
        "query": "billionaire luxury lifestyle supercars mansion tour wealth secrets",
        "description": "Aspirational luxury, billionaire habits, and rich lifestyle stories"
    },
    {
        "id": "mystery_crime",
        "name": "🕵️ Mystery & True Crime",
        "query": "unsolved mystery true crime documentary story explained",
        "description": "Gripping suspense, true crime cases, and unsolved mysteries"
    },
    {
        "id": "ai_future",
        "name": "🤖 AI & Future Technology",
        "query": "AI future technology breakthrough explained podcast",
        "description": "Trending AI breakthroughs, robotics, and future tech predictions"
    },
    {
        "id": "psychology",
        "name": "🧠 Psychology & Human Behaviour",
        "query": "human psychology dark psychology behaviour facts lecture",
        "description": "Fascinating human behaviour, persuasion, and brain facts"
    },
    {
        "id": "gta6_gaming",
        "name": "🎮 GTA 6 & Gaming Hype",
        "query": "GTA 6 trailer breakdown hidden details gameplay secrets",
        "description": "Massive-view GTA 6 hype, Rockstar details, leaks & gameplay breakdowns"
    },
]

HIGH_CLIP_KEYWORDS = [
    "podcast", "interview", "episode", "ep.", "ep ", "talk", "speech",
    "conversation", "advice", "secrets", "secret", "rules", "habits", "habit",
    "mindset", "story", "stories", "truth", "mistakes", "mistake", "explained",
    "how to", "why ", "billionaire", "millionaire", "founder", "ceo",
    "masterclass", "q&a", "debate", "breakdown", "documentary", "lessons",
    "psychology", "discipline", "success", "ft.", "feat.", "|", "with ",
    # High-views Gaming / GTA 6 / Luxury / Mystery / Entertainment signals
    "gta 6", "gta vi", "gta", "rockstar", "gameplay", "trailer", "easter eggs",
    "hidden details", "details you missed", "walkthrough", "gaming", "ps5",
    "mythbusters", "mods", "insane", "crazy", "reaction", "highlights",
    "luxury", "mansion", "supercar", "true crime", "mystery", "unsolved",
    "detective", "disappeared", "dark psychology", "body language"
]

LOW_CLIP_PENALTIES = [
    "lofi", "lo-fi", "ambient", "rain sounds", "white noise", "sleep music",
    "10 hours", "8 hours", "playlist", "full album", "bgm", "instrumental",
    "no talking", "meditation music", "karaoke", "music video", "official video",
    "lyric video", "soundtrack", "asmr sleep", "compilation"
]

HOOK_TRIGGERS = [
    "why", "how", "secret", "truth", "never", "stop", "worst", "best",
    "nobody", "everyone", "changed my life", "dark", "insane", "crazy",
    "shocking", "biggest", "rules", "signs", "things", "million", "billion"
]


def _pick_best_thumbnail(entry: Dict[str, Any]) -> str:
    thumbs = entry.get("thumbnails") or []
    if thumbs:
        # Pick highest resolution available
        sorted_t = sorted(
            thumbs,
            key=lambda t: (t.get("width") or 0) * (t.get("height") or 0),
            reverse=True
        )
        if sorted_t[0].get("url"):
            return sorted_t[0]["url"]
    vid = entry.get("id", "")
    return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else ""


def score_youtube_video_for_clipping(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Evaluates a YouTube video entry across 5 clip-potential dimensions (0-100):
    1. Optimal Long-Form Duration (25 pts)
    2. Viral Reach & Views (25 pts)
    3. Spoken-Word / Clipability Format (25 pts)
    4. Viral Hook Title Triggers (15 pts)
    5. Estimated Shorts Yield Bonus (10 pts)
    """
    vid = entry.get("id") or ""
    title = (entry.get("title") or "").strip()
    duration = float(entry.get("duration") or 0)
    views = int(entry.get("view_count") or 0)
    channel = (entry.get("channel") or entry.get("uploader") or "Unknown Channel").strip()
    is_live = bool(entry.get("is_live")) or (entry.get("live_status") == "is_live")

    if not vid or not title or is_live:
        return None

    # Skip YouTube Shorts or clips under 3 minutes (180s)
    if duration < 180:
        return None

    title_lower = title.lower()
    reasons: List[str] = []

    # 1. Duration Score (25 pts) - Ideal sweet spot is 10m to 90m
    if 600 <= duration <= 5400:
        duration_score = 25.0
        reasons.append(f"Ideal Length ({int(duration // 60)}m)")
    elif 300 <= duration < 600:
        duration_score = 18.0
        reasons.append(f"Compact ({int(duration // 60)}m)")
    elif 5400 < duration <= 10800:
        duration_score = 19.0
        reasons.append(f"Deep-Dive ({int(duration // 60)}m)")
    elif duration > 10800:
        duration_score = 12.0
    else:
        duration_score = 12.0

    # 2. Viral Reach & Views Score (25 pts)
    if views > 0:
        log_v = math.log10(max(views, 1))
        # log10(10k)=4, log10(100k)=5, log10(1M)=6, log10(10M)=7
        views_score = min(25.0, max(4.0, (log_v - 2.5) * 5.5))
        if views >= 1_000_000:
            reasons.append("1M+ Viral Reach")
        elif views >= 100_000:
            reasons.append("100K+ Proven Audience")
    else:
        views_score = 8.0

    # 3. Spoken-Word / Clipability Format Score (25 pts)
    pos_hits = sum(1 for kw in HIGH_CLIP_KEYWORDS if kw in title_lower)
    neg_hits = sum(1 for kw in LOW_CLIP_PENALTIES if kw in title_lower)

    if neg_hits > 0:
        # Heavily penalize music/ambient/non-speech videos
        format_score = max(0.0, 6.0 - (neg_hits * 5.0))
    else:
        format_score = min(25.0, 11.0 + (pos_hits * 3.5))
        if pos_hits >= 2:
            reasons.append("High Spoken-Word Density")

    # 4. Viral Hook Title Triggers (15 pts)
    hook_hits = sum(1 for h in HOOK_TRIGGERS if h in title_lower)
    has_number = bool(re.search(r'\b\d+\b', title))
    has_question = "?" in title
    hook_score = min(15.0, (hook_hits * 3.5) + (3.0 if has_number else 0.0) + (2.5 if has_question else 0.0))
    if hook_score >= 9.0:
        reasons.append("Strong Hook Title")

    # 5. Estimated Shorts Yield Bonus (10 pts)
    # Roughly 1 great 45-60s Short every ~3.5-4 minutes of spoken content
    estimated_clips = min(25, max(2, int(duration // 220)))
    if 5 <= estimated_clips <= 20:
        yield_score = 10.0
    elif estimated_clips >= 3:
        yield_score = 7.0
    else:
        yield_score = 4.0

    total_score = round(min(99.0, duration_score + views_score + format_score + hook_score + yield_score), 1)

    # Filter out obvious music-only results with very low format score
    if neg_hits > 0 and total_score < 55:
        return None

    url = f"https://www.youtube.com/watch?v={vid}"
    return {
        "id": vid,
        "title": title,
        "channel": channel,
        "url": url,
        "duration": int(duration),
        "view_count": views,
        "thumbnail": _pick_best_thumbnail(entry),
        "clip_potential_score": total_score,
        "estimated_clips": estimated_clips,
        "reasons": reasons[:3] if reasons else ["Clippable Long-Form"],
        "score_breakdown": {
            "duration": round(duration_score, 1),
            "reach": round(views_score, 1),
            "spoken_format": round(format_score, 1),
            "hook_strength": round(hook_score, 1),
            "clip_yield": round(yield_score, 1),
        }
    }


def discover_best_youtube_videos(
    query: str,
    min_duration_minutes: int = 5,
    max_duration_minutes: int = 180,
    max_results: int = 12,
    sort_by: str = "clip_potential"
) -> Dict[str, Any]:
    """
    Searches YouTube using yt-dlp flat extraction, filters out Shorts/music/live streams,
    and ranks the highest-potential long-form videos for clipping into Shorts.
    sort_by: 'clip_potential' (balanced 0-100 score) or 'max_views' (highest view-count viral hype).
    """
    clean_query = (query or "").strip()
    if not clean_query:
        clean_query = "podcast mindset self improvement interview"

    # Fetch a wider pool (28 candidates) so the ranking algorithm picks the cream of the crop
    pool_size = min(35, max(20, max_results * 2 + 6))
    search_expr = f"ytsearch{pool_size}:{clean_query}"

    ydl_opts = get_base_ydl_opts()
    ydl_opts.update({
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    })

    min_sec = max(180, int(min_duration_minutes) * 60)
    max_sec = max(min_sec + 60, int(max_duration_minutes) * 60)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_expr, download=False)

        entries = info.get("entries") or []
        scored: List[Dict[str, Any]] = []
        seen_ids = set()

        for entry in entries:
            if not entry:
                continue
            vid = entry.get("id")
            if not vid or vid in seen_ids:
                continue
            seen_ids.add(vid)

            dur = float(entry.get("duration") or 0)
            if dur < min_sec or dur > max_sec:
                continue

            result = score_youtube_video_for_clipping(entry)
            if result:
                scored.append(result)

        # Sort by chosen objective: balanced clip potential or pure maximum views
        if sort_by == "max_views":
            scored.sort(key=lambda x: (x["view_count"], x["clip_potential_score"]), reverse=True)
        else:
            scored.sort(key=lambda x: (x["clip_potential_score"], x["view_count"]), reverse=True)
        top_videos = scored[:max_results]

        return {
            "success": True,
            "query": clean_query,
            "total_scanned": len(entries),
            "qualified_count": len(scored),
            "videos": top_videos
        }
    except Exception as e:
        logger.error(f"YouTube discovery failed for query '{clean_query}': {e}")
        raise ValueError(f"YouTube discovery search failed: {str(e)}")
