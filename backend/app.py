import os
import uuid
import logging
from typing import Optional
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import BASE_DIR, HOST, PORT, WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE
from backend.database.db import (
    init_db,
    create_video_record,
    get_video,
    list_videos,
    delete_video,
    get_transcript,
    get_clips_by_video_id,
    get_clip,
    update_clip_status,
    delete_clips_for_video,
    record_youtube_upload,
    update_youtube_upload_status,
    get_youtube_upload,
    list_youtube_uploads,
    get_dashboard_analytics
)
from backend.modules.video_input import save_uploaded_video
from backend.modules.clip_detection import detect_and_rank_clips
from backend.modules.youtube_upload import get_youtube_uploader
from backend.services.processing_service import process_video_pipeline, render_clip_pipeline
from pydantic import BaseModel, Field

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("viralcut")

# Ensure database is initialized on import
init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database
    logger.info("Initializing ViralCut AI Database...")
    init_db()
    logger.info("Database initialized successfully.")
    yield
    # Shutdown
    logger.info("ViralCut AI Backend shutting down.")


app = FastAPI(
    title="ViralCut AI - Backend API",
    description="Intelligent YouTube Shorts Generator Video Processing Engine",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Frontend static assets if available
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

@app.get("/")
def root(request: Request):
    accept = request.headers.get("accept", "")
    index_file = FRONTEND_DIST / "index.html"
    if "text/html" in accept and index_file.exists():
        return FileResponse(str(index_file))
    return {
        "project": "ViralCut AI",
        "status": "online",
        "phase": "Phase 4 - Full-Stack Application & YouTube Upload",
        "whisper_config": {
            "model": WHISPER_MODEL,
            "device": WHISPER_DEVICE,
            "compute_type": WHISPER_COMPUTE_TYPE
        }
    }

@app.get("/dashboard")
def dashboard_view():
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    raise HTTPException(status_code=404, detail="Frontend build not found.")

@app.post("/api/videos/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Accepts video upload (MP4, MOV, MKV, AVI), saves it to disk,
    records it in SQLite, and launches the processing pipeline in the background.
    """
    logger.info(f"Incoming video upload: {file.filename}")
    video_id, file_path, file_size = await save_uploaded_video(file)
    
    # Create database record
    video_record = create_video_record(
        video_id=video_id,
        filename=file.filename,
        filepath=file_path,
        file_size=file_size
    )

    # Trigger Phase 1 processing pipeline as background task
    background_tasks.add_task(process_video_pipeline, video_id)

    return {
        "success": True,
        "message": "Video uploaded successfully. Processing pipeline started in background.",
        "video": video_record
    }

@app.get("/api/videos")
def get_all_videos():
    """List all videos with their current status and metadata."""
    videos = list_videos()
    return {"count": len(videos), "videos": videos}

@app.get("/api/videos/{video_id}")
def get_video_details(video_id: str):
    """Get metadata and current processing status of a specific video."""
    video = get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")
    return video

@app.get("/api/videos/{video_id}/status")
def get_video_status_endpoint(video_id: str):
    """Lightweight endpoint for polling video processing status."""
    video = get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")
    return {
        "id": video["id"],
        "status": video["status"],
        "error_message": video["error_message"],
        "duration": video["duration"]
    }

@app.get("/api/videos/{video_id}/transcript")
def get_video_transcript_endpoint(video_id: str):
    """Retrieve timestamped transcription and segments for a video."""
    video = get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")

    transcript = get_transcript(video_id)
    if not transcript:
        if video["status"] in ["uploaded", "extracting_metadata", "extracting_audio", "transcribing"]:
            return JSONResponse(
                status_code=202,
                content={
                    "message": "Transcription is currently in progress.",
                    "status": video["status"]
                }
            )
        elif video["status"] == "failed":
            raise HTTPException(
                status_code=500,
                detail=f"Transcription failed: {video['error_message']}"
            )
        else:
            raise HTTPException(status_code=404, detail="Transcript not found.")

    return transcript

class DetectClipsRequest(BaseModel):
    min_duration: float = Field(default=35.0, ge=5.0, le=120.0)
    max_duration: float = Field(default=75.0, ge=10.0, le=180.0)
    max_clips: int = Field(default=10, ge=1, le=50)

class UpdateClipRequest(BaseModel):
    status: Optional[str] = None
    title: Optional[str] = None

class RenderClipRequest(BaseModel):
    layout_mode: str = Field(default="auto", description="'auto', 'blur_background', or 'smart_crop'")
    include_subtitles: bool = Field(default=True)

class YouTubeUploadRequest(BaseModel):
    privacy_status: str = Field(default="public", description="'public', 'unlisted', or 'private'")
    custom_title: Optional[str] = None
    custom_description: Optional[str] = None

@app.get("/api/dashboard/analytics")
def get_dashboard_analytics_endpoint():
    """Returns real-time dashboard analytics and recent activity."""
    return get_dashboard_analytics()

@app.get("/api/youtube/status")
def get_youtube_status_endpoint():
    """Checks YouTube Data API v3 OAuth configuration and authorization status."""
    uploader = get_youtube_uploader()
    return uploader.get_auth_status()

@app.post("/api/clips/{clip_id}/upload-youtube")
def upload_clip_to_youtube_endpoint(clip_id: str, req: YouTubeUploadRequest = YouTubeUploadRequest()):
    """
    Publishes an approved rendered short directly to YouTube Shorts.
    """
    clip = get_clip(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found.")

    if not clip.get("output_path") or not os.path.exists(clip["output_path"]):
        raise HTTPException(
            status_code=400,
            detail="Cannot publish: Short has not been rendered yet. Please render the clip first."
        )

    title = req.custom_title or clip["title"] or "Viral Short by ViralCut AI"
    description = req.custom_description or clip["description"] or f"{title}\n\n#Shorts #Viral"
    upload_id = str(uuid.uuid4())

    # Record initial pending upload in SQLite
    record_youtube_upload(
        upload_id=upload_id,
        clip_id=clip_id,
        video_id=clip["video_id"],
        title=title,
        description=description,
        privacy_status=req.privacy_status
    )

    try:
        uploader = get_youtube_uploader()
        tags = [t.strip("#") for t in (clip.get("hashtags") or "").split() if t]
        result = uploader.upload_short(
            video_path=clip["output_path"],
            title=title,
            description=description,
            tags=tags,
            privacy_status=req.privacy_status
        )

        update_youtube_upload_status(
            upload_id=upload_id,
            status="published",
            youtube_video_id=result["youtube_video_id"],
            youtube_url=result["youtube_url"]
        )

        return {
            "success": True,
            "message": "Video successfully uploaded to YouTube Shorts.",
            "upload": get_youtube_upload(upload_id)
        }

    except Exception as e:
        logger.exception(f"YouTube upload failed for clip {clip_id}: {e}")
        update_youtube_upload_status(
            upload_id=upload_id,
            status="failed",
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"YouTube upload failed: {str(e)}")

@app.get("/api/youtube/uploads")
def list_youtube_uploads_endpoint():
    """Lists all published and pending YouTube Shorts uploads."""
    uploads = list_youtube_uploads()
    return {"count": len(uploads), "uploads": uploads}

@app.post("/api/clips/{clip_id}/render")
def render_clip_endpoint(clip_id: str, req: RenderClipRequest = RenderClipRequest()):
    """
    Renders the finished 9:16 vertical Short for an approved clip.
    Includes face-tracked framing, audio normalization, and burned-in styled subtitles.
    """
    clip = get_clip(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found.")

    try:
        updated_clip = render_clip_pipeline(
            clip_id=clip_id,
            layout_mode=req.layout_mode,
            include_subtitles=req.include_subtitles
        )
        return {
            "success": True,
            "message": "Vertical short successfully rendered.",
            "clip": updated_clip
        }
    except Exception as e:
        logger.exception(f"Render failed for clip {clip_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Rendering failed: {str(e)}")

@app.get("/api/clips/{clip_id}/video")
def get_clip_video_file(clip_id: str):
    """
    Serves the rendered 9:16 MP4 video file for browser preview or downloading.
    """
    clip = get_clip(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found.")

    output_path = clip.get("output_path")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Short has not been rendered yet.")

    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"Short_{clip_id}.mp4"
    )

@app.post("/api/videos/{video_id}/detect-clips")
def trigger_clip_detection_endpoint(video_id: str, req: DetectClipsRequest = DetectClipsRequest()):
    """
    Manually triggers or re-runs Phase 2 AI viral clip detection on a transcribed video.
    """
    transcript = get_transcript(video_id)
    if not transcript:
        raise HTTPException(
            status_code=400,
            detail="Cannot detect clips: video transcript not found or transcription still in progress."
        )

    clips = detect_and_rank_clips(
        video_id=video_id,
        segments=transcript["segments"],
        min_duration=req.min_duration,
        max_duration=req.max_duration,
        max_clips=req.max_clips
    )
    return {
        "success": True,
        "video_id": video_id,
        "clip_count": len(clips),
        "clips": clips
    }

@app.get("/api/videos/{video_id}/clips")
def get_video_clips_endpoint(video_id: str):
    """
    Returns all detected candidate clips for a video, ranked by viral score descending.
    """
    video = get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")

    clips = get_clips_by_video_id(video_id)
    return {
        "video_id": video_id,
        "count": len(clips),
        "clips": clips
    }

@app.get("/api/clips/{clip_id}")
def get_clip_details_endpoint(clip_id: str):
    """Retrieve details, transcript, and 6-dimension scores for a specific clip."""
    clip = get_clip(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found.")
    return clip

@app.patch("/api/clips/{clip_id}")
def update_clip_endpoint(clip_id: str, req: UpdateClipRequest):
    """Update clip status ('approved', 'rejected') or edit title."""
    clip = get_clip(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found.")

    new_status = req.status or clip["status"]
    update_clip_status(clip_id, new_status, title=req.title)
    return {
        "success": True,
        "message": f"Clip {clip_id} updated.",
        "clip": get_clip(clip_id)
    }

@app.delete("/api/videos/{video_id}")
def delete_video_endpoint(video_id: str):
    """Delete video from database and remove file from disk."""
    video = get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")

    delete_clips_for_video(video_id)
    file_path = Path(video["filepath"])
    if file_path.exists():
        file_path.unlink()

    delete_video(video_id)
    return {"success": True, "message": f"Video {video_id} and associated clips deleted."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host=HOST, port=PORT, reload=True)
