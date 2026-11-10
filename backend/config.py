import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
VIDEOS_DIR = BASE_DIR / "videos" / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
MODELS_DIR = BASE_DIR / "models"
TEMP_DIR = BASE_DIR / "temp"
DATABASE_PATH = BACKEND_DIR / "database" / "viralcut.db"

# Create required directories
for directory in [VIDEOS_DIR, OUTPUT_DIR, MODELS_DIR, TEMP_DIR, DATABASE_PATH.parent]:
    directory.mkdir(parents=True, exist_ok=True)

# Hardware Optimization Rules (Intel Core i3 8th Gen, 8GB RAM, CPU-only)
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")  # Options: tiny, base, small
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"
WHISPER_CPU_THREADS = int(os.getenv("WHISPER_CPU_THREADS", "4"))

# Video & File Upload Restrictions
SUPPORTED_EXTENSIONS = [".mp4", ".mov", ".mkv", ".avi"]
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "1536"))  # 1.5GB limit default

# FFmpeg Executables
import shutil
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

FFMPEG_CMD = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE_CMD = shutil.which("ffprobe") or "ffprobe"

# Server Settings
HOST = "127.0.0.1"
PORT = 8000
