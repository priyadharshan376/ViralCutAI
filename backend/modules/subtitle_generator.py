import os
from pathlib import Path
from typing import List, Dict, Any

def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS timestamp format: H:MM:SS.cs"""
    seconds = max(0.0, seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

def format_srt_time(seconds: float) -> str:
    """Format seconds into SRT timestamp format: HH:MM:SS,mmm"""
    seconds = max(0.0, seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def extract_clip_subtitles(
    segments: List[Dict[str, Any]],
    clip_start: float,
    clip_end: float,
    max_words_per_line: int = 4
) -> List[Dict[str, Any]]:
    """
    Extracts subtitle lines relative to clip start [0.0, duration].
    Breaks speech into punchy, mobile-friendly 2-4 word phrases.
    """
    lines = []
    
    for seg in segments:
        seg_start = float(seg["start"])
        seg_end = float(seg["end"])

        # Check if segment overlaps with clip
        if seg_end <= clip_start or seg_start >= clip_end:
            continue

        words = seg.get("words", [])
        if words:
            # Group words into short chunks
            current_chunk = []
            chunk_start = None

            for w in words:
                w_start = float(w["start"])
                w_end = float(w["end"])

                # Check if word is within clip range
                if w_end <= clip_start or w_start >= clip_end:
                    continue

                if chunk_start is None:
                    chunk_start = max(0.0, w_start - clip_start)

                current_chunk.append(w["word"].strip())

                if len(current_chunk) >= max_words_per_line:
                    chunk_end = max(chunk_start + 0.3, w_end - clip_start)
                    lines.append({
                        "start": round(chunk_start, 2),
                        "end": round(chunk_end, 2),
                        "text": " ".join(current_chunk).upper()
                    })
                    current_chunk = []
                    chunk_start = None

            if current_chunk:
                chunk_end = max(chunk_start + 0.3, min(seg_end, clip_end) - clip_start)
                lines.append({
                    "start": round(chunk_start, 2),
                    "end": round(chunk_end, 2),
                    "text": " ".join(current_chunk).upper()
                })
        else:
            # Fallback to segment text if word timestamps are not present
            rel_start = max(0.0, seg_start - clip_start)
            rel_end = max(rel_start + 0.5, min(seg_end, clip_end) - clip_start)
            lines.append({
                "start": round(rel_start, 2),
                "end": round(rel_end, 2),
                "text": seg["text"].strip().upper()
            })

    return lines

def generate_ass_file(
    subtitle_lines: List[Dict[str, Any]],
    output_path: str,
    font_size: int = 24,
    primary_color: str = "&H0000FFFF",  # Bold Yellow (BGR format)
    outline_color: str = "&H00000000",  # Black outline
    margin_v: int = 150                 # Pixels from bottom of 720x1280
) -> str:
    """
    Generates a styled ASS subtitle file for 9:16 vertical video.
    """
    ass_path = Path(output_path)
    ass_path.parent.mkdir(parents=True, exist_ok=True)

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ViralShorts,Arial,{font_size},{primary_color},&H000000FF,{outline_color},&H80000000,-1,0,0,0,100,100,1,0,1,3.5,1.5,2,30,30,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogue_lines = []
    for line in subtitle_lines:
        start_str = format_ass_time(line["start"])
        end_str = format_ass_time(line["end"])
        text = line["text"].replace("\n", "\\N")
        dialogue_lines.append(
            f"Dialogue: 0,{start_str},{end_str},ViralShorts,,0,0,0,,{text}"
        )

    content = header + "\n".join(dialogue_lines) + "\n"

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(ass_path)
