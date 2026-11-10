import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from backend.config import VIDEOS_DIR, SUPPORTED_EXTENSIONS, MAX_UPLOAD_SIZE_MB

def validate_video_file(filename: str):
    """Validate that the file extension is supported."""
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video format: '{ext}'. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

async def save_uploaded_video(file: UploadFile) -> tuple[str, str, int]:
    """
    Stream and save the uploaded video to disk in 1MB chunks to minimize RAM usage.
    Returns: (video_id, destination_filepath, total_bytes_saved)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty.")

    validate_video_file(file.filename)
    
    video_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix.lower()
    saved_filename = f"{video_id}{ext}"
    dest_path = VIDEOS_DIR / saved_filename
    
    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    total_bytes = 0
    chunk_size = 1024 * 1024  # 1 MB chunk

    try:
        with open(dest_path, "wb") as buffer:
            while chunk := await file.read(chunk_size):
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    buffer.close()
                    if dest_path.exists():
                        dest_path.unlink()
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum allowed size of {MAX_UPLOAD_SIZE_MB} MB."
                    )
                buffer.write(chunk)
    except Exception as e:
        if dest_path.exists():
            dest_path.unlink()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to save video: {str(e)}")

    return video_id, str(dest_path), total_bytes
