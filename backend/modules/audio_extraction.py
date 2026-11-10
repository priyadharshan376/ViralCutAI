import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Any
from backend.config import FFMPEG_CMD, FFPROBE_CMD

logger = logging.getLogger(__name__)

def get_video_metadata(video_path: str) -> Dict[str, Any]:
    """
    Extract video metadata (duration, resolution, framerate, codecs) using ffprobe.
    """
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found at: {video_path}")

    cmd = [
        FFPROBE_CMD,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"FFprobe execution failed: {e.stderr}")
        raise RuntimeError(f"FFprobe failed to inspect video: {e.stderr}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse FFprobe JSON: {e}")
        raise RuntimeError("Failed to decode video metadata from FFprobe.")

    # Extract streams
    video_stream = None
    audio_stream = None
    for stream in probe_data.get("streams", []):
        if stream.get("codec_type") == "video" and not video_stream:
            video_stream = stream
        elif stream.get("codec_type") == "audio" and not audio_stream:
            audio_stream = stream

    # Parse duration
    format_info = probe_data.get("format", {})
    duration = float(format_info.get("duration", 0.0))
    if duration == 0.0 and video_stream:
        duration = float(video_stream.get("duration", 0.0))

    # Parse resolution
    width = int(video_stream.get("width", 0)) if video_stream else 0
    height = int(video_stream.get("height", 0)) if video_stream else 0

    # Parse framerate
    fps = 0.0
    if video_stream:
        r_frame_rate = video_stream.get("r_frame_rate", "0/1")
        if "/" in r_frame_rate:
            num, denom = r_frame_rate.split("/")
            fps = float(num) / float(denom) if float(denom) > 0 else 0.0

    video_codec = video_stream.get("codec_name", "") if video_stream else ""
    audio_codec = audio_stream.get("codec_name", "") if audio_stream else ""

    return {
        "duration": round(duration, 2),
        "width": width,
        "height": height,
        "fps": round(fps, 2),
        "video_codec": video_codec,
        "audio_codec": audio_codec,
        "size_bytes": int(format_info.get("size", 0)),
        "bitrate": int(format_info.get("bit_rate", 0)) if format_info.get("bit_rate") else 0
    }

def extract_audio(video_path: str, output_audio_path: str) -> str:
    """
    Extract audio as 16kHz mono 16-bit PCM WAV for optimal Faster-Whisper processing.
    """
    in_path = Path(video_path)
    out_path = Path(output_audio_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        raise FileNotFoundError(f"Source video not found: {video_path}")

    cmd = [
        FFMPEG_CMD,
        "-y",               # Overwrite existing
        "-i", str(in_path), # Input file
        "-vn",              # Disable video
        "-acodec", "pcm_s16le", # 16-bit PCM WAV
        "-ar", "16000",     # 16 kHz sample rate
        "-ac", "1",         # Mono channel
        str(out_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return str(out_path)
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg audio extraction failed: {e.stderr}")
        raise RuntimeError(f"FFmpeg failed to extract audio: {e.stderr}")
