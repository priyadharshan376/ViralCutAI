import uuid
import logging
from typing import List, Dict, Any
from backend.modules.transcript_analysis import segment_transcript
from backend.services.ai_service import get_ai_service
from backend.database.db import save_clip, delete_clips_for_video, get_video
from backend.modules.metadata_generator import generate_shorts_metadata

logger = logging.getLogger(__name__)

def is_heavily_overlapping(
    candidate: Dict[str, Any],
    kept_clips: List[Dict[str, Any]],
    min_separation_seconds: float = 40.0,
    max_overlap_ratio: float = 0.15
) -> bool:
    """
    Checks if a candidate clip overlaps with any already selected clip.
    Rejects clips that:
    1. Start within min_separation_seconds of an existing clip.
    2. Share more than max_overlap_ratio (20%) of duration with an existing clip.
    """
    c_start = candidate["start_time"]
    c_end = candidate["end_time"]
    c_dur = candidate.get("duration", c_end - c_start)

    for kept in kept_clips:
        k_start = kept["start_time"]
        k_end = kept["end_time"]
        k_dur = kept.get("duration", k_end - k_start)

        # 1. Start time proximity
        if abs(c_start - k_start) < min_separation_seconds:
            return True

        # 2. Time interval overlap
        overlap_start = max(c_start, k_start)
        overlap_end = min(c_end, k_end)
        if overlap_end > overlap_start:
            overlap = overlap_end - overlap_start
            min_len = min(c_dur, k_dur)
            if (overlap / min_len) > max_overlap_ratio:
                return True

    return False

def suppress_overlapping_clips(
    scored_candidates: List[Dict[str, Any]],
    overlap_threshold: float = 0.15,
    min_separation: float = 20.0
) -> List[Dict[str, Any]]:
    """
    Suppresses redundant overlapping clips, keeping only the highest-scoring candidate
    for each unique time window across the video.
    """
    # Sort descending by viral score
    sorted_clips = sorted(scored_candidates, key=lambda c: c["viral_score"], reverse=True)
    kept_clips: List[Dict[str, Any]] = []

    for candidate in sorted_clips:
        if not is_heavily_overlapping(candidate, kept_clips, min_separation_seconds=min_separation, max_overlap_ratio=overlap_threshold):
            kept_clips.append(candidate)

    # Sort final kept clips chronologically by start_time for a logical presentation
    return sorted(kept_clips, key=lambda c: c["start_time"])

def detect_and_rank_clips(
    video_id: str,
    segments: List[Dict[str, Any]],
    min_duration: float = 35.0,
    max_duration: float = 75.0,
    max_clips: int = 10,
    persist_to_db: bool = True
) -> List[Dict[str, Any]]:
    """
    Story-Arc-Driven AI Viral Clip Detection:
    1. Segments transcript into complete narrative arcs (Hook -> Exploration -> Resolution).
    2. Identifies visual whiteboard / chart demonstrations.
    3. Scores each candidate on the 6 viral dimensions + visual demonstration bonuses.
    4. Suppresses overlaps so every clip is a distinct, self-contained story.
    5. Ranks candidates and stores them in SQLite.
    """
    logger.info(f"[{video_id}] Starting story-arc viral clip detection for {len(segments)} segments...")

    # Step 1: Segment transcript into narrative arcs
    windows = segment_transcript(segments, min_duration=min_duration, max_duration=max_duration)
    logger.info(f"[{video_id}] Generated {len(windows)} candidate story windows.")

    if not windows:
        return []

    # Step 2: Score candidates
    ai_service = get_ai_service()
    scored_candidates = []

    for win in windows:
        has_visual = win.get("has_visual", False)
        analysis = ai_service.analyze_and_score_clip(win["text"], has_visual=has_visual)
        
        # Recommended vertical layout mode: blur_background if visual drawings/charts are present
        recommended_layout = "blur_background" if has_visual else "auto"

        scored_candidates.append({
            "id": str(uuid.uuid4()),
            "video_id": video_id,
            "start_time": win["start_time"],
            "end_time": win["end_time"],
            "duration": win["duration"],
            "transcript_text": win["text"],
            "has_visual": has_visual,
            "layout_mode": recommended_layout,
            "status": "detected",
            **analysis
        })

    # Step 3: Suppress overlapping clips
    distinct_clips = suppress_overlapping_clips(scored_candidates)

    # Step 4: Top N clips sorted by viral score
    final_clips = sorted(distinct_clips, key=lambda c: c["viral_score"], reverse=True)[:max_clips]
    # Re-order the final selection chronologically for clean review
    final_clips = sorted(final_clips, key=lambda c: c["start_time"])
    logger.info(f"[{video_id}] Selected {len(final_clips)} distinct narrative story clips across video.")

    # Step 5: Enrich with High-Engagement PDX Metadata (YouTube context & entity awareness)
    video_rec = get_video(video_id) or {}
    for clip in final_clips:
        meta = generate_shorts_metadata(
            clip_text=clip["transcript_text"],
            base_title=clip.get("title", ""),
            channel_name="PDX",
            source_filename=video_rec.get("filename", ""),
            source_title=video_rec.get("source_title", ""),
            source_channel=video_rec.get("source_channel", ""),
            source_description=video_rec.get("source_description", ""),
            source_url=video_rec.get("source_url", ""),
            source_tags=video_rec.get("source_tags", "")
        )
        clip["title"] = meta["title"]
        clip["description"] = meta["description"]
        clip["hashtags"] = meta["hashtags"]
        clip["subtitle_style"] = "hormozi"

    # Step 6: Persist to DB
    if persist_to_db:
        delete_clips_for_video(video_id)
        for clip in final_clips:
            save_clip(clip)

    return final_clips
