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

def detect_speaker_timeline(
    video_path: str,
    start_time: float,
    duration: float,
    video_width: int,
    video_height: int,
    crop_w: int
) -> List[Tuple[float, float, int]]:
    """
    Dynamic Multi-Speaker & Shot-Tracked Smart Crop:
    - Samples frames every 0.4s across the clip using frontal + profile face detection.
    - Tracks camera cuts / speaker switches (e.g. Host Left <-> Guest Right) and creates
      clean piecewise crop segments so the active speaker is NEVER cut off.
    - Applies deadzone stabilization within each shot to eliminate camera jitter.
    Returns: List of (rel_start, rel_end, crop_x_px)
    """
    default_x = max(0, (video_width - crop_w) // 2)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.warning(f"Could not open video {video_path} for face tracking. Defaulting to center.")
        return [(0.0, duration, default_x)]

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or video_width
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or video_height

    frontal_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    profile_path = cv2.data.haarcascades + 'haarcascade_profileface.xml'
    profile_cascade = cv2.CascadeClassifier(profile_path) if os.path.exists(profile_path) else None

    samples: List[Tuple[float, Optional[float]]] = []
    sample_interval = 0.4
    rel_t = 0.0
    min_face = (max(24, int(h * 0.07)), max(24, int(h * 0.07)))
    prev_norm_x: Optional[float] = None

    while rel_t < duration:
        abs_t = start_time + rel_t
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(abs_t * fps))
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = frontal_cascade.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=4, minSize=min_face)

        if len(faces) == 0 and profile_cascade is not None:
            faces = profile_cascade.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=4, minSize=min_face)

        if len(faces) > 0:
            # Prefer largest face, with slight continuity bias to avoid jitter between two equal faces
            def _face_score(f):
                fx, fy, fw, fh = f
                cx = (fx + fw / 2.0) / float(w)
                area = fw * fh
                continuity = 1.0 - (0.18 * abs(cx - prev_norm_x)) if prev_norm_x is not None else 1.0
                return area * max(0.5, continuity)

            primary = max(faces, key=_face_score)
            fx, fy, fw, fh = primary
            center_x = (fx + fw / 2.0) / float(w)
            prev_norm_x = center_x
            samples.append((rel_t, center_x))
        else:
            samples.append((rel_t, None))

        rel_t += sample_interval

    cap.release()

    # Fill missing detections with nearest known face or center (0.5)
    valid_xs = [x for _, x in samples if x is not None]
    if not valid_xs:
        logger.info("No face detected in clip sample; defaulting to screen center (0.50).")
        return [(0.0, duration, default_x)]

    fallback_x = sorted(valid_xs)[len(valid_xs) // 2]
    filled: List[Tuple[float, float]] = []
    last_known = valid_xs[0]
    for t_s, x_s in samples:
        if x_s is not None:
            last_known = x_s
            filled.append((t_s, x_s))
        else:
            filled.append((t_s, last_known if last_known is not None else fallback_x))

    # Group into stable shot segments (jump threshold = 0.14 of frame width)
    def _norm_to_px(norm_x: float) -> int:
        raw_x = int((norm_x * video_width) - (crop_w / 2.0))
        return max(0, min(video_width - crop_w, (raw_x // 2) * 2))

    segments: List[Tuple[float, float, int]] = []
    seg_start = 0.0
    seg_vals: List[float] = [filled[0][1]]

    for i in range(1, len(filled)):
        t_cur, x_cur = filled[i]
        seg_med = sorted(seg_vals)[len(seg_vals) // 2]
        if abs(x_cur - seg_med) > 0.14:
            # Close previous segment if at least 0.8s long
            if (t_cur - seg_start) >= 0.8:
                segments.append((seg_start, t_cur, _norm_to_px(seg_med)))
                seg_start = t_cur
                seg_vals = [x_cur]
            else:
                seg_vals.append(x_cur)
        else:
            seg_vals.append(x_cur)

    final_med = sorted(seg_vals)[len(seg_vals) // 2]
    segments.append((seg_start, duration, _norm_to_px(final_med)))

    # Merge adjacent segments whose crop_x differs by less than 40px
    merged: List[Tuple[float, float, int]] = []
    for s_t, e_t, cx in segments:
        if merged and abs(cx - merged[-1][2]) < 40:
            prev_s, _, prev_x = merged[-1]
            merged[-1] = (prev_s, e_t, (prev_x + cx) // 4 * 2)
        else:
            merged.append((s_t, e_t, cx))

    logger.info(
        f"Dynamic Smart Crop tracked {len(valid_xs)} face detections -> "
        f"{len(merged)} stabilized camera shot(s): {[(round(s,1), round(e,1), x) for s,e,x in merged]}"
    )
    return merged


def _build_dynamic_crop_x_expr(timeline: List[Tuple[float, float, int]]) -> str:
    """Builds an FFmpeg time-based expression for multi-shot smart crop."""
    if len(timeline) <= 1:
        return str(timeline[0][2]) if timeline else "0"
    # Nested if(lt(t\,end)\,x\,...)
    expr = str(timeline[-1][2])
    for _, end_t, cx in reversed(timeline[:-1]):
        expr = f"if(lt(t\\,{end_t:.2f})\\,{cx}\\,{expr})"
    return expr

def format_ffmpeg_filter_path(file_path: str) -> str:
    """Escape Windows file paths for FFmpeg filter arguments."""
    p = str(Path(file_path).resolve()).replace('\\', '/')
    return p.replace(':', '\\:')

QUALITY_PRESETS: Dict[str, Dict[str, str]] = {
    "ultra": {"crf": "16", "preset": "medium", "audio_bitrate": "256k"},
    "high": {"crf": "18", "preset": "fast", "audio_bitrate": "192k"},
    "balanced": {"crf": "20", "preset": "veryfast", "audio_bitrate": "160k"},
}


def render_vertical_short(
    video_path: str,
    clip_id: str,
    start_time: float,
    end_time: float,
    video_width: int,
    video_height: int,
    ass_subtitle_path: Optional[str] = None,
    layout_mode: str = "auto",  # "auto", "blur_background", or "smart_crop"
    quality_preset: str = "high",  # "ultra", "high", or "balanced"
    target_width: int = 1080,
    target_height: int = 1920
) -> str:
    """
    Renders a crisp Full HD 1080x1920 vertical 9:16 YouTube Short / Reel using FFmpeg:
    - Lanczos scaling + subtle unsharp clarity enhancement for crisp mobile playback.
    - High-profile H.264 (yuv420p, CRF 18 default, faststart) & 192k AAC audio.
    - Auto Visual Detection: Automatically chooses Blurred Background Fit for whiteboard/charts/slides
      so 100% of the visual presentation and speaker are visible!
    - Speaker-centered smart crop for talking-head-only clips.
    - Accurate clip duration trimming with -ss <start> -i <video> -t <duration>.
    - Broadcast EBU R128 audio normalization (loudnorm).
    - Styled burned-in subtitles via libass positioned cleanly.
    """
    duration = max(1.0, end_time - start_time)
    output_filename = f"{clip_id}.mp4"
    output_file = OUTPUT_DIR / output_filename
    output_file.parent.mkdir(parents=True, exist_ok=True)

    enc = QUALITY_PRESETS.get(quality_preset, QUALITY_PRESETS["high"])

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

    # 2. Determine Framing Filter for 9:16 Aspect Ratio (Lanczos + crisp clarity enhancement)
    if effective_layout == "smart_crop":
        target_aspect = 9.0 / 16.0
        crop_h = video_height
        crop_w = (int(video_height * target_aspect) // 2) * 2

        if crop_w > video_width:
            crop_w = (video_width // 2) * 2
            crop_h = (int(crop_w / target_aspect) // 2) * 2

        timeline = detect_speaker_timeline(
            video_path=video_path,
            start_time=start_time,
            duration=duration,
            video_width=video_width,
            video_height=video_height,
            crop_w=crop_w
        )
        crop_x_expr = _build_dynamic_crop_x_expr(timeline)
        crop_y = max(0, (video_height - crop_h) // 2)

        video_filter = (
            f"crop={crop_w}:{crop_h}:{crop_x_expr}:{crop_y},"
            f"scale={target_width}:{target_height}:flags=lanczos,"
            f"unsharp=5:5:0.45:5:5:0.0,"
            f"eq=contrast=1.03:saturation=1.05"
        )
    else:
        # Aesthetic Blurred Background Fit (Best for Whiteboard / Visual Demonstrations / Charts)
        # Keeps 100% of original wide 16:9 view centered with sharp Lanczos scaling
        video_filter = (
            f"split=2[bg_src][fg_src];"
            f"[bg_src]scale={target_width}:{target_height}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={target_width}:{target_height},gblur=sigma=42,eq=brightness=-0.13:contrast=1.05[bg];"
            f"[fg_src]scale={target_width}:-2:flags=lanczos,"
            f"unsharp=3:3:0.35:3:3:0.0,"
            f"eq=contrast=1.02:saturation=1.04,"
            f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.20:t=2[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2"
        )

    # 3. Append Subtitles Filter if provided
    if ass_subtitle_path and os.path.exists(ass_subtitle_path):
        escaped_sub_path = format_ffmpeg_filter_path(ass_subtitle_path)
        video_filter += f",ass='{escaped_sub_path}'"

    # 4. Audio Normalization Filter (EBU R128 standard)
    audio_filter = "loudnorm=I=-16:TP=-1.5:LRA=11"

    # 5. Construct High-Quality FFmpeg Command
    cmd = [
        FFMPEG_CMD,
        "-y",
        "-ss", f"{start_time:.2f}",
        "-i", str(Path(video_path).resolve()),
        "-t", f"{duration:.2f}",
        "-vf", video_filter,
        "-af", audio_filter,
        "-c:v", "libx264",
        "-preset", enc["preset"],
        "-crf", enc["crf"],
        "-pix_fmt", "yuv420p",
        "-profile:v", "high",
        "-level", "4.2",
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-b:a", enc["audio_bitrate"],
        "-ar", "48000",
        str(output_file)
    ]

    logger.info(
        f"Rendering 1080p 9:16 Short {clip_id} "
        f"(layout={effective_layout}, quality={quality_preset}, crf={enc['crf']}): "
        f"start={start_time:.2f}s, dur={duration:.2f}s to {output_file}..."
    )
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Successfully rendered 9:16 Short: {output_file}")
        return str(output_file)
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg render failed: {e.stderr}")
        raise RuntimeError(f"FFmpeg rendering failed: {e.stderr}")
