import os
import cv2
import logging
import subprocess
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from backend.config import FFMPEG_CMD, OUTPUT_DIR, TEMP_DIR

logger = logging.getLogger(__name__)

def detect_visual_content(video_path: str, start_time: float, duration: float) -> Tuple[bool, str]:
    """
    Robust CPU detector for visual demonstrations:
    - Whiteboard drawings
    - Charts, diagrams, slides
    - High-detail visual presentations
    Returns: (has_visual: bool, visual_type: str)
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.warning(f"Could not open video {video_path} for visual detection.")
        return False, "none"

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720

    sample_count = min(12, max(4, int(duration // 2)))
    sample_times = np.linspace(start_time, start_time + duration, num=sample_count)

    whiteboard_frames = 0
    chart_frames = 0
    total_samples = 0

    for t in sample_times:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
        ret, frame = cap.read()
        if not ret:
            continue
        total_samples += 1

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = float(np.mean(gray))

        # Whiteboard detection: high brightness canvas (> 85) with drawn content
        if mean_brightness > 85.0:
            whiteboard_frames += 1

        # Edge analysis for charts / drawings across screen thirds
        edges = cv2.Canny(gray, 50, 150)
        third = w // 3
        left_edge = float(np.mean(edges[:, :third]))
        right_edge = float(np.mean(edges[:, 2 * third:]))

        if (left_edge > 6.0 or right_edge > 6.0) and mean_brightness > 40.0:
            chart_frames += 1

    cap.release()

    if total_samples == 0:
        return False, "none"

    if (whiteboard_frames / total_samples) >= 0.25:
        logger.info(f"Visual detector: Whiteboard drawing confirmed ({whiteboard_frames}/{total_samples} frames).")
        return True, "whiteboard_drawing"

    if (chart_frames / total_samples) >= 0.35:
        logger.info(f"Visual detector: Chart / Diagram confirmed ({chart_frames}/{total_samples} frames).")
        return True, "chart_or_diagram"

    return False, "talking_head"

def detect_speaker_focus(video_path: str, start_time: float, duration: float) -> float:
    """
    Robust CPU face detector using OpenCV Haar Cascades.
    Samples frames across duration to find speaker's horizontal center position.
    Returns normalized center position (0.0 = left edge, 0.5 = center, 1.0 = right edge).
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.warning(f"Could not open video {video_path} for face detection. Defaulting to center (0.50).")
        return 0.5

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720

    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)

    detected_centers: List[float] = []
    sample_interval = 0.5
    current_time = start_time
    end_time = start_time + duration

    while current_time < end_time:
        frame_idx = int(current_time * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(int(h * 0.08), int(h * 0.08))
        )

        if len(faces) > 0:
            primary_face = max(faces, key=lambda f: f[2] * f[3])
            fx, fy, fw, fh = primary_face
            center_x = (fx + fw / 2.0) / float(w)
            detected_centers.append(center_x)

        current_time += sample_interval

    cap.release()

    if detected_centers:
        detected_centers.sort()
        median_x = detected_centers[len(detected_centers) // 2]
        logger.info(f"Speaker face tracking found center at {median_x:.2f} ({median_x*100:.1f}%) across {len(detected_centers)} detections.")
        return median_x
    else:
        logger.info("No face detected in clip sample; defaulting to screen center (0.50).")
        return 0.5

def format_ffmpeg_filter_path(file_path: str) -> str:
    """Escape Windows file paths for FFmpeg filter arguments."""
    p = str(Path(file_path).resolve()).replace('\\', '/')
    return p.replace(':', '\\:')

def render_vertical_short(
    video_path: str,
    clip_id: str,
    start_time: float,
    end_time: float,
    video_width: int,
    video_height: int,
    ass_subtitle_path: Optional[str] = None,
    layout_mode: str = "auto",  # "auto", "blur_background", or "smart_crop"
    target_width: int = 720,
    target_height: int = 1280
) -> str:
    """
    Renders a vertical 9:16 YouTube Short / Reel using FFmpeg:
    - Auto Visual Detection: Automatically chooses Blurred Background Fit for whiteboard/charts/slides
      so 100% of the visual presentation and speaker are visible!
    - Speaker-centered smart crop for talking-head-only clips.
    - Accurate clip duration trimming with -ss <start> -i <video> -t <duration>.
    - Broadcast EBU R128 audio normalization (loudnorm).
    - Styled burned-in subtitles via libass positioned cleanly below visual demonstrations.
    """
    duration = max(1.0, end_time - start_time)
    output_filename = f"{clip_id}.mp4"
    output_file = OUTPUT_DIR / output_filename
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. Resolve Layout Mode (Auto detection)
    effective_layout = layout_mode
    if layout_mode == "auto":
        is_visual, visual_type = detect_visual_content(video_path, start_time, duration)
        if is_visual:
            effective_layout = "blur_background"
            logger.info(f"Clip {clip_id} contains {visual_type}. Auto-selected Blurred Background Fit layout.")
        else:
            effective_layout = "smart_crop"
            logger.info(f"Clip {clip_id} is pure talking-head. Auto-selected Smart Face Crop layout.")

    # 2. Determine Framing Filter for 9:16 Aspect Ratio
    if effective_layout == "smart_crop":
        target_aspect = 9.0 / 16.0
        crop_h = video_height
        crop_w = (int(video_height * target_aspect) // 2) * 2

        if crop_w > video_width:
            crop_w = (video_width // 2) * 2
            crop_h = (int(crop_w / target_aspect) // 2) * 2

        center_x_norm = detect_speaker_focus(video_path, start_time, duration)
        raw_x = int((center_x_norm * video_width) - (crop_w / 2.0))
        crop_x = max(0, min(video_width - crop_w, (raw_x // 2) * 2))
        crop_y = max(0, (video_height - crop_h) // 2)

        video_filter = f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale={target_width}:{target_height}"
    else:
        # Aesthetic Blurred Background Fit (Best for Whiteboard / Visual Demonstrations / Charts)
        # Keeps 100% of original wide 16:9 view centered, with blurred and darkened ambient top/bottom
        video_filter = (
            f"split=2[bg_src][fg_src];"
            f"[bg_src]scale={target_width}:{target_height}:force_original_aspect_ratio=increase,"
            f"crop={target_width}:{target_height},gblur=sigma=28,eq=brightness=-0.10:contrast=1.05[bg];"
            f"[fg_src]scale={target_width}:-2,"
            f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.15:t=1[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
        )

    # 3. Append Subtitles Filter if provided
    if ass_subtitle_path and os.path.exists(ass_subtitle_path):
        escaped_sub_path = format_ffmpeg_filter_path(ass_subtitle_path)
        video_filter += f",ass='{escaped_sub_path}'"

    # 4. Audio Normalization Filter (EBU R128 standard)
    audio_filter = "loudnorm=I=-16:TP=-1.5:LRA=11"

    # 5. Construct FFmpeg Command
    cmd = [
        FFMPEG_CMD,
        "-y",
        "-ss", f"{start_time:.2f}",
        "-i", str(Path(video_path).resolve()),
        "-t", f"{duration:.2f}",
        "-vf", video_filter,
        "-af", audio_filter,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        str(output_file)
    ]

    logger.info(f"Rendering 9:16 Short {clip_id} (layout={effective_layout}): start={start_time:.2f}s, dur={duration:.2f}s to {output_file}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Successfully rendered 9:16 Short: {output_file}")
        return str(output_file)
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg render failed: {e.stderr}")
        raise RuntimeError(f"FFmpeg rendering failed: {e.stderr}")
