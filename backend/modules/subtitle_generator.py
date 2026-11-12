import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Popular YouTube Shorts / Reels / TikTok subtitle presets (1080x1920 PlayRes)
SUBTITLE_STYLES: Dict[str, Dict[str, Any]] = {
    "hormozi": {
        "id": "hormozi",
        "name": "Hormozi Bold",
        "description": "Chunky uppercase Impact captions with electric yellow word-by-word pop",
        "font": "Impact",
        "font_size": 76,
        "primary_color": "&H00FFFFFF",     # White base
        "highlight_color": "&H0000EAFF",   # Electric Yellow/Gold (BGR)
        "outline_color": "&H00000000",     # Black outline
        "back_color": "&H80000000",
        "border_style": 1,
        "outline": 5.5,
        "shadow": 3.0,
        "bold": -1,
        "uppercase": True,
        "max_words": 3,
        "highlight_word": True,
        "pop_scale": 110,
        "preview_bg": "#111827",
        "preview_text": "#FFFFFF",
        "preview_accent": "#FFEA00",
    },
    "mrbeast": {
        "id": "mrbeast",
        "name": "MrBeast Pop",
        "description": "Giant high-energy Impact captions with thick outline & neon green word pop",
        "font": "Impact",
        "font_size": 84,
        "primary_color": "&H00FFFFFF",     # White base
        "highlight_color": "&H0048FF33",   # Neon Green (BGR)
        "outline_color": "&H00000000",
        "back_color": "&H90000000",
        "border_style": 1,
        "outline": 6.5,
        "shadow": 3.5,
        "bold": -1,
        "uppercase": True,
        "max_words": 3,
        "highlight_word": True,
        "pop_scale": 112,
        "preview_bg": "#0f172a",
        "preview_text": "#FFFFFF",
        "preview_accent": "#33FF48",
    },
    "tiktok_box": {
        "id": "tiktok_box",
        "name": "TikTok Pill Box",
        "description": "Clean readable captions inside a dark contrast box with yellow highlight",
        "font": "Segoe UI",
        "font_size": 58,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H0000EAFF",   # Yellow highlight
        "outline_color": "&HAA000000",     # Semi-opaque dark box
        "back_color": "&HAA000000",
        "border_style": 3,                 # Opaque box behind text
        "outline": 16.0,
        "shadow": 0.0,
        "bold": -1,
        "uppercase": False,
        "max_words": 4,
        "highlight_word": True,
        "pop_scale": 100,                  # Keep box height steady
        "preview_bg": "#000000",
        "preview_text": "#FFFFFF",
        "preview_accent": "#FFEA00",
    },
    "neon_cyan": {
        "id": "neon_cyan",
        "name": "Neon Cyber Cyan",
        "description": "Tech & AI favorite — bold glowing cyan highlights over electric dark outline",
        "font": "Verdana",
        "font_size": 62,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H00FFFF00",   # Cyan (BGR)
        "outline_color": "&H00552200",     # Deep dark blue outline
        "back_color": "&H90220000",
        "border_style": 1,
        "outline": 5.0,
        "shadow": 3.0,
        "bold": -1,
        "uppercase": True,
        "max_words": 3,
        "highlight_word": True,
        "pop_scale": 108,
        "preview_bg": "#082f49",
        "preview_text": "#FFFFFF",
        "preview_accent": "#00FFFF",
    },
    "iman_clean": {
        "id": "iman_clean",
        "name": "Creator Minimal",
        "description": "Sleek modern sentence-case captions with warm amber focus (Ali/Iman style)",
        "font": "Segoe UI",
        "font_size": 58,
        "primary_color": "&H00F5F5F5",
        "highlight_color": "&H0038B8FF",   # Warm Amber (#FFB838 in BGR)
        "outline_color": "&H00121212",
        "back_color": "&H75000000",
        "border_style": 1,
        "outline": 3.5,
        "shadow": 2.5,
        "bold": -1,
        "uppercase": False,
        "max_words": 4,
        "highlight_word": True,
        "pop_scale": 104,
        "preview_bg": "#1e293b",
        "preview_text": "#F5F5F5",
        "preview_accent": "#FFB838",
    },
    "podcast_yellow": {
        "id": "podcast_yellow",
        "name": "Cinema Yellow",
        "description": "Classic podcast & documentary warm-yellow subtitles without flashing",
        "font": "Arial",
        "font_size": 58,
        "primary_color": "&H0026E0FF",     # Warm Cinema Gold/Yellow
        "highlight_color": "&H0026E0FF",
        "outline_color": "&H00000000",
        "back_color": "&H80000000",
        "border_style": 1,
        "outline": 4.2,
        "shadow": 2.2,
        "bold": -1,
        "uppercase": False,
        "max_words": 5,
        "highlight_word": False,
        "pop_scale": 100,
        "preview_bg": "#18181b",
        "preview_text": "#FFE026",
        "preview_accent": "#FFE026",
    },
    "red_hook": {
        "id": "red_hook",
        "name": "Red Alert Hook",
        "description": "High-contrast white & crimson red emphasis for urgent hooks & facts",
        "font": "Impact",
        "font_size": 76,
        "primary_color": "&H00FFFFFF",
        "highlight_color": "&H003B3BFF",   # Crimson Red (#FF3B3B in BGR)
        "outline_color": "&H00000000",
        "back_color": "&H85000000",
        "border_style": 1,
        "outline": 5.5,
        "shadow": 3.0,
        "bold": -1,
        "uppercase": True,
        "max_words": 3,
        "highlight_word": True,
        "pop_scale": 110,
        "preview_bg": "#2a0a0a",
        "preview_text": "#FFFFFF",
        "preview_accent": "#FF3B3B",
    },
}


def get_subtitle_styles_metadata() -> List[Dict[str, Any]]:
    """Returns frontend-friendly list of available subtitle styles."""
    return [
        {
            "id": s["id"],
            "name": s["name"],
            "description": s["description"],
            "preview_bg": s["preview_bg"],
            "preview_text": s["preview_text"],
            "preview_accent": s["preview_accent"],
            "uppercase": s["uppercase"],
        }
        for s in SUBTITLE_STYLES.values()
    ]


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


def _escape_ass_text(text: str) -> str:
    """Escape characters that have special meaning in ASS override blocks."""
    return text.replace("{", "(").replace("}", ")").replace("\n", " ").strip()


def extract_clip_subtitles(
    segments: List[Dict[str, Any]],
    clip_start: float,
    clip_end: float,
    max_words_per_line: int = 3,
    uppercase: bool = True
) -> List[Dict[str, Any]]:
    """
    Extracts subtitle lines relative to clip start [0.0, duration].
    Preserves individual word timestamps so dynamic styles can animate word-by-word highlights.
    """
    lines = []

    for seg in segments:
        seg_start = float(seg["start"])
        seg_end = float(seg["end"])

        if seg_end <= clip_start or seg_start >= clip_end:
            continue

        words = seg.get("words", [])
        if words:
            current_chunk: List[Dict[str, Any]] = []
            chunk_start: Optional[float] = None

            for w in words:
                w_start = float(w["start"])
                w_end = float(w["end"])

                if w_end <= clip_start or w_start >= clip_end:
                    continue

                rel_w_start = max(0.0, w_start - clip_start)
                rel_w_end = max(rel_w_start + 0.08, min(w_end, clip_end) - clip_start)
                word_txt = _escape_ass_text(w["word"])
                if not word_txt:
                    continue
                if uppercase:
                    word_txt = word_txt.upper()

                if chunk_start is None:
                    chunk_start = rel_w_start

                current_chunk.append({
                    "word": word_txt,
                    "start": round(rel_w_start, 2),
                    "end": round(rel_w_end, 2),
                })

                if len(current_chunk) >= max_words_per_line:
                    chunk_end = max(chunk_start + 0.25, rel_w_end)
                    lines.append({
                        "start": round(chunk_start, 2),
                        "end": round(chunk_end, 2),
                        "text": " ".join(item["word"] for item in current_chunk),
                        "words": current_chunk,
                    })
                    current_chunk = []
                    chunk_start = None

            if current_chunk and chunk_start is not None:
                chunk_end = max(chunk_start + 0.25, min(seg_end, clip_end) - clip_start)
                lines.append({
                    "start": round(chunk_start, 2),
                    "end": round(chunk_end, 2),
                    "text": " ".join(item["word"] for item in current_chunk),
                    "words": current_chunk,
                })
        else:
            rel_start = max(0.0, seg_start - clip_start)
            rel_end = max(rel_start + 0.5, min(seg_end, clip_end) - clip_start)
            raw_text = _escape_ass_text(seg["text"])
            if uppercase:
                raw_text = raw_text.upper()
            if raw_text:
                lines.append({
                    "start": round(rel_start, 2),
                    "end": round(rel_end, 2),
                    "text": raw_text,
                    "words": [],
                })

    return lines


def generate_ass_file(
    subtitle_lines: List[Dict[str, Any]],
    output_path: str,
    style_name: str = "hormozi",
    margin_v: int = 240,
    play_res_x: int = 1080,
    play_res_y: int = 1920,
    hook_banner_text: Optional[str] = None
) -> str:
    """
    Generates a crisp 1080x1920 ASS subtitle file using one of the popular creator presets.
    Supports active word-by-word highlight animations and an optional 2.8s Opening Hook Banner
    to reduce early 3-second swipes.
    """
    style = SUBTITLE_STYLES.get(style_name, SUBTITLE_STYLES["hormozi"])
    ass_path = Path(output_path)
    ass_path.parent.mkdir(parents=True, exist_ok=True)

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ViralShorts,{style['font']},{style['font_size']},{style['primary_color']},&H000000FF,{style['outline_color']},{style['back_color']},{style['bold']},0,0,0,100,100,1,0,{style['border_style']},{style['outline']},{style['shadow']},2,50,50,{margin_v},1
Style: HookBanner,Impact,58,&H0000EAFF,&H000000FF,&HCC000000,&HCC000000,-1,0,0,0,100,100,1,0,3,18,0,8,70,70,190,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogue_lines: List[str] = []

    if hook_banner_text:
        clean_hook = _escape_ass_text(hook_banner_text).replace("#SHORTS", "").replace("#Shorts", "").replace("#shorts", "").strip()
        if len(clean_hook) > 48:
            clean_hook = clean_hook[:45].rsplit(" ", 1)[0] + "..."
        if clean_hook:
            dialogue_lines.append(
                f"Dialogue: 1,0:00:00.00,0:00:02.80,HookBanner,,0,0,0,,{clean_hook.upper()}"
            )
    use_word_highlight = bool(style.get("highlight_word"))
    highlight_color = style["highlight_color"]
    pop_scale = int(style.get("pop_scale", 100))

    for line in subtitle_lines:
        chunk_start = float(line["start"])
        chunk_end = max(chunk_start + 0.15, float(line["end"]))
        words = line.get("words") or []

        if use_word_highlight and len(words) > 1:
            # Emit one non-overlapping event per spoken word in the chunk
            for idx, w in enumerate(words):
                ev_start = chunk_start if idx == 0 else max(chunk_start, float(w["start"]))
                if idx + 1 < len(words):
                    next_start = float(words[idx + 1]["start"])
                    ev_end = max(ev_start + 0.05, min(chunk_end, next_start))
                else:
                    ev_end = max(ev_start + 0.05, chunk_end)

                if ev_end <= ev_start:
                    continue

                rendered_tokens = []
                for j, token in enumerate(words):
                    token_text = token["word"]
                    if j == idx:
                        if pop_scale != 100:
                            rendered_tokens.append(
                                f"{{\\c{highlight_color}&\\fscx{pop_scale}\\fscy{pop_scale}}}{token_text}{{\\r}}"
                            )
                        else:
                            rendered_tokens.append(
                                f"{{\\c{highlight_color}&}}{token_text}{{\\r}}"
                            )
                    else:
                        rendered_tokens.append(token_text)

                dialogue_lines.append(
                    f"Dialogue: 0,{format_ass_time(ev_start)},{format_ass_time(ev_end)},ViralShorts,,0,0,0,,{' '.join(rendered_tokens)}"
                )
        elif use_word_highlight and len(words) == 1:
            w_text = words[0]["word"]
            if pop_scale != 100:
                styled_text = f"{{\\c{highlight_color}&\\fscx{pop_scale}\\fscy{pop_scale}}}{w_text}{{\\r}}"
            else:
                styled_text = f"{{\\c{highlight_color}&}}{w_text}{{\\r}}"
            dialogue_lines.append(
                f"Dialogue: 0,{format_ass_time(chunk_start)},{format_ass_time(chunk_end)},ViralShorts,,0,0,0,,{styled_text}"
            )
        else:
            text = line["text"].replace("\n", "\\N")
            dialogue_lines.append(
                f"Dialogue: 0,{format_ass_time(chunk_start)},{format_ass_time(chunk_end)},ViralShorts,,0,0,0,,{text}"
            )

    content = header + "\n".join(dialogue_lines) + "\n"
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(ass_path)
