import os
import re
import uuid
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

import yt_dlp
from backend.config import VIDEOS_DIR, FFMPEG_CMD, BASE_DIR, BACKEND_DIR

logger = logging.getLogger(__name__)

YOUTUBE_URL_REGEX = re.compile(
    r'^(https?://)?(www\.|m\.)?(youtube\.com/(watch\?v=|shorts/|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})'
)

def is_valid_youtube_url(url: str) -> bool:
    """Validate if string is a recognized YouTube URL."""
    return bool(YOUTUBE_URL_REGEX.search(url.strip()))

def get_base_ydl_opts() -> Dict[str, Any]:
    """
    Constructs robust yt-dlp options configured with Node.js JS runtime,
    FFmpeg binary, and optional cookies.txt if provided.
    """
    opts: Dict[str, Any] = {
        'quiet': False,
        'no_warnings': True,
        'nocheckcertificate': True
    }

    # Enable Node.js runtime to solve YouTube's n-sig & bot verification challenges
    node_path = shutil.which("node") or "C:\\Program Files\\nodejs\\node.exe"
    if os.path.exists(node_path):
        opts['js_runtimes'] = {'node': {'path': node_path}}

    # Set FFmpeg location
    ffmpeg_exe = shutil.which("ffmpeg") or FFMPEG_CMD
    if ffmpeg_exe and os.path.exists(ffmpeg_exe):
        opts['ffmpeg_location'] = ffmpeg_exe

    # Check for optional cookies.txt in root or backend
    for candidate in [
        BASE_DIR / "cookies.txt",
        BACKEND_DIR / "cookies.txt",
        BASE_DIR / "youtube_cookies.txt",
    ]:
        if candidate.exists():
            opts['cookiefile'] = str(candidate.resolve())
            logger.info(f"Loaded YouTube cookies from {candidate}")
            break

    return opts

def inspect_youtube_video(url: str) -> Dict[str, Any]:
    """
    Fetches video metadata (title, duration, thumbnail, author, available resolutions)
    without downloading the full video file.
    """
    clean_url = url.strip()
    ydl_opts = get_base_ydl_opts()
    ydl_opts.update({
        'quiet': True,
        'no_warnings': True
    })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            
            # Extract available resolutions
            formats = info.get('formats', [])
            heights = set()
            for f in formats:
                h = f.get('height')
                if h and isinstance(h, int) and h in [360, 480, 720, 1080, 1440, 2160]:
                    heights.add(h)
            
            sorted_resolutions = sorted(list(heights), reverse=True)
            resolution_options = [f"{h}p" for h in sorted_resolutions]
            if not resolution_options:
                resolution_options = ["1080p", "720p", "480p", "Best Available"]

            return {
                "success": True,
                "title": info.get("title", "YouTube Video"),
                "duration": info.get("duration", 0),
                "channel": info.get("uploader", "") or info.get("channel", ""),
                "thumbnail": info.get("thumbnail", ""),
                "available_resolutions": resolution_options,
                "view_count": info.get("view_count", 0),
                "url": clean_url
            }
    except Exception as e:
        logger.error(f"Failed to inspect YouTube URL '{clean_url}': {e}")
        # Helpful error context if YouTube flags cookies
        err_msg = str(e)
        if "Sign in to confirm you’re not a bot" in err_msg or "Sign in to confirm you're not a bot" in err_msg:
            err_msg = "YouTube bot check triggered. Please place a cookies.txt file in the project folder or verify network access."
        raise ValueError(f"Could not load YouTube video: {err_msg}")

def download_youtube_video(
    url: str,
    video_id: str,
    target_resolution: str = "720"
) -> Dict[str, Any]:
    """
    Downloads YouTube video at chosen resolution (e.g. 1080, 720, 480, or best)
    and saves it to VIDEOS_DIR / f"{video_id}.mp4".
    """
    clean_url = url.strip()
    target_dir = Path(VIDEOS_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(target_dir / f"{video_id}.%(ext)s")

    # Clean target resolution: '1080p' -> '1080'
    res_num = re.sub(r'[^0-9]', '', str(target_resolution))

    if res_num and res_num.isdigit():
        height_val = int(res_num)
        # Select best mp4 video stream <= height_val + best audio, fallback to any codec
        format_selector = (
            f"bestvideo[height<={height_val}][ext=mp4]+bestaudio[ext=m4a]/"
            f"bestvideo[height<={height_val}]+bestaudio/"
            f"best[height<={height_val}]/best"
        )
    else:
        format_selector = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"

    ydl_opts = get_base_ydl_opts()
    ydl_opts.update({
        'format': format_selector,
        'outtmpl': out_template,
        'merge_output_format': 'mp4',
        'retries': 3,
        'fragment_retries': 3,
    })

    try:
        logger.info(f"[{video_id}] Starting yt-dlp download for: {clean_url} (target res: {target_resolution})")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=True)
            video_title = info.get("title", f"YouTube_{video_id}")
            duration = info.get("duration", 0)

        expected_filepath = target_dir / f"{video_id}.mp4"
        if not expected_filepath.exists():
            # In case extension was mkv or webm
            candidates = list(target_dir.glob(f"{video_id}.*"))
            if candidates:
                expected_filepath = candidates[0]
            else:
                raise FileNotFoundError(f"Downloaded video file not found for video_id {video_id}")

        file_size = expected_filepath.stat().st_size
        safe_filename = re.sub(r'[\\/*?:"<>|]', "", video_title)[:80] + ".mp4"

        logger.info(f"[{video_id}] YouTube download completed: {expected_filepath} ({file_size / (1024*1024):.1f} MB)")

        return {
            "video_id": video_id,
            "filename": safe_filename,
            "filepath": str(expected_filepath.resolve()),
            "file_size": file_size,
            "duration": duration,
            "title": video_title,
            "thumbnail": info.get("thumbnail", "")
        }
    except Exception as e:
        logger.error(f"[{video_id}] yt-dlp download failed: {e}")
        err_msg = str(e)
        if "Sign in to confirm you’re not a bot" in err_msg or "Sign in to confirm you're not a bot" in err_msg:
            err_msg = "YouTube bot check triggered. Please place a cookies.txt in the ViralCutAI folder or try again in a few moments."
        raise RuntimeError(f"YouTube download error: {err_msg}")
