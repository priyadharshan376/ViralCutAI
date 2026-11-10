import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from backend.config import TEMP_DIR
from backend.database.db import (
    update_video_metadata,
    update_video_status,
    save_transcript,
    get_video,
    get_transcript,
    get_clip,
    update_clip_render_result
)
from backend.modules.audio_extraction import get_video_metadata, extract_audio
from backend.modules.transcription import get_transcriber
from backend.modules.clip_detection import detect_and_rank_clips
from backend.modules.subtitle_generator import extract_clip_subtitles, generate_ass_file
from backend.modules.metadata_generator import generate_shorts_metadata
from backend.modules.video_editor import render_vertical_short

logger = logging.getLogger(__name__)

def process_video_pipeline(video_id: str):
    """
    Complete Video Processing Pipeline:
    1. Extract Video Metadata via ffprobe
    2. Extract Audio (16kHz mono WAV) via ffmpeg
    3. Transcribe Audio via Faster-Whisper CPU INT8
    4. Store Transcript and Segments in SQLite
    5. Phase 2: Detect & Rank Viral Clips
    6. Clean up temporary audio files
    """
    video_record = get_video(video_id)
    if not video_record:
        logger.error(f"Video ID '{video_id}' not found in database.")
        return

    video_path = video_record["filepath"]
    temp_audio_path = str(TEMP_DIR / f"{video_id}.wav")

    try:
        # Step 1: Extract Video Metadata
        logger.info(f"[{video_id}] Extracting video metadata...")
        update_video_status(video_id, "extracting_metadata")
        metadata = get_video_metadata(video_path)
        update_video_metadata(video_id, metadata)
        logger.info(f"[{video_id}] Metadata extracted: {metadata}")

        # Step 2: Extract Audio
        logger.info(f"[{video_id}] Extracting audio to {temp_audio_path}...")
        update_video_status(video_id, "extracting_audio")
        extract_audio(video_path, temp_audio_path)

        # Step 3: Transcribe with Faster-Whisper
        logger.info(f"[{video_id}] Transcribing audio with Faster-Whisper...")
        update_video_status(video_id, "transcribing")
        transcriber = get_transcriber()
        transcript_result = transcriber.transcribe(temp_audio_path)

        # Step 4: Save Transcript in Database
        save_transcript(
            video_id=video_id,
            full_text=transcript_result["full_text"],
            language=transcript_result["language"],
            language_probability=transcript_result["language_probability"],
            duration=transcript_result["duration"],
            segments=transcript_result["segments"]
        )

        # Step 5: Phase 2 - Detect and Rank Viral Clips
        logger.info(f"[{video_id}] Analyzing transcript and detecting viral clips...")
        update_video_status(video_id, "detecting_clips")
        detected_clips = detect_and_rank_clips(
            video_id=video_id,
            segments=transcript_result["segments"],
            min_duration=35.0,
            max_duration=75.0
        )
        logger.info(f"[{video_id}] Successfully detected and saved {len(detected_clips)} clips.")

        # Step 6: Update Video Status to Ready / Completed
        update_video_status(video_id, "completed")
        logger.info(f"[{video_id}] Pipeline completed successfully. Status: completed.")

    except Exception as e:
        logger.exception(f"[{video_id}] Pipeline failed: {str(e)}")
        update_video_status(video_id, "failed", error_message=str(e))

    finally:
        # Clean up temporary WAV file to free SSD space
        if os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                logger.info(f"[{video_id}] Cleaned up temp audio file: {temp_audio_path}")
            except Exception as err:
                logger.warning(f"Could not remove temp audio file: {err}")

def render_clip_pipeline(
    clip_id: str,
    layout_mode: str = "auto",
    include_subtitles: bool = True
) -> Dict[str, Any]:
    """
    Phase 3: Converts an approved or detected clip into a finished 9:16 YouTube Short.
    1. Extracts clip subtitles & builds styled ASS file with dynamic vertical positioning.
    2. Generates YouTube Shorts metadata (Title, Description, Hashtags).
    3. Renders 9:16 vertical video with auto visual detection / face tracking & audio normalization.
    4. Updates database with output path and metadata.
    """
    clip = get_clip(clip_id)
    if not clip:
        raise ValueError(f"Clip {clip_id} not found.")

    video = get_video(clip["video_id"])
    if not video:
        raise ValueError(f"Parent video {clip['video_id']} not found.")

    # Determine layout mode: if layout_mode is default 'auto' and clip specifies layout, use it
    selected_layout = layout_mode
    if selected_layout == "auto" and clip.get("layout_mode") and clip["layout_mode"] != "auto":
        selected_layout = clip["layout_mode"]

    transcript = get_transcript(clip["video_id"])
    segments = transcript["segments"] if transcript else []

    ass_path = None
    if include_subtitles and segments:
        sub_lines = extract_clip_subtitles(
            segments=segments,
            clip_start=clip["start_time"],
            clip_end=clip["end_time"]
        )
        if sub_lines:
            ass_output = str(TEMP_DIR / f"{clip_id}.ass")
            # If visual presentation (blur_background), position subtitle below the 16:9 box (margin 220)
            # so the whiteboard drawing and speaker are completely unobstructed!
            margin_v = 220 if (selected_layout == "blur_background" or clip.get("has_visual")) else 150
            ass_path = generate_ass_file(sub_lines, ass_output, margin_v=margin_v)

    # Generate YouTube metadata
    metadata = generate_shorts_metadata(
        clip_text=clip["transcript_text"],
        base_title=clip["title"]
    )

    # Render vertical video
    output_path = render_vertical_short(
        video_path=video["filepath"],
        clip_id=clip_id,
        start_time=clip["start_time"],
        end_time=clip["end_time"],
        video_width=video["width"] or 1280,
        video_height=video["height"] or 720,
        ass_subtitle_path=ass_path,
        layout_mode=selected_layout
    )

    # Clean up temp ASS subtitle file
    if ass_path and os.path.exists(ass_path):
        try:
            os.remove(ass_path)
        except Exception as e:
            logger.warning(f"Could not delete temp ASS file: {e}")

    # Update database
    update_clip_render_result(
        clip_id=clip_id,
        output_path=output_path,
        title=metadata["title"],
        description=metadata["description"],
        hashtags=metadata["hashtags"]
    )

    return get_clip(clip_id)

