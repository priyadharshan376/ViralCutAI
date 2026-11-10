import re
from typing import List, Dict, Any, Tuple

# Starting words/phrases that signal a broken, mid-sentence clip start
REJECT_START_WORDS = [
    "and", "but", "what that", "which", "instead of", "because",
    "that represents", "that's why", "that means", "so then", "like", "or",
    "and then", "so what you ended up", "also", "then", "which means", "where"
]

# Ending words that signal a cut-off cliffhanger
REJECT_END_WORDS = [
    "and", "but", "or", "because", "so", "if", "when", "which",
    "let's say", "what happens", "you know", "super sad", "no", "where",
    "like", "as", "well", "than"
]

# High-impact opening hook patterns
HOOK_STARTERS = [
    r'^(why|how|what if|what happens|did you know|do you have|can you|have you)',
    r'^(the craving is not|habit is pretty much|people hear the word|if you have these feelings)',
    r'^(now here is|now here\'s|here is what|you have to have what|every single time you)',
    r'^(let\'s say you are overwhelmed|if after \d+ seconds|we were talking about)'
]

# Resolving takeaway phrases
RESOLVING_PHRASES = [
    "that's it", "that is it", "the same thing", "same thing", "promise",
    "starts with", "roots of a tree", "tree trunk", "breaking the cycle",
    "cycle", "reduce", "not doing it", "do something else", "worth it",
    "and that's why", "that is how"
]

# Visual cue words
VISUAL_KEYWORDS = [
    "whiteboard", "draw", "drawing", "chart", "diagram", "graph",
    "eye", "dot", "circle", "phone", "look at this", "see here",
    "over here", "sketch", "line", "slide"
]

def ends_with_terminal_punctuation(text: str) -> bool:
    """Check if text ends with a period, exclamation mark, or question mark."""
    return bool(re.search(r'[.!?]["\']?\s*$', text.strip()))

def evaluate_story_start(text: str) -> Tuple[bool, float, str]:
    """
    Evaluates whether a segment functions as a clean, engaging narrative start.
    Returns: (is_valid, bonus_score, hook_type)
    """
    clean = text.strip()
    lower = clean.lower()

    if not clean or not clean[0].isupper():
        return False, 0.0, "non_capitalized"

    # Reject dangling connective words
    for reject in REJECT_START_WORDS:
        if lower.startswith(reject + " ") or lower == reject:
            return False, 0.0, "dangling_start"

    # 1. Question hook
    if "?" in clean[:80] or any(lower.startswith(q) for q in ["why", "how", "what", "is it", "can", "did you", "do you"]):
        return True, 30.0, "question_hook"

    # 2. Patterned hook starter
    for pattern in HOOK_STARTERS:
        if re.search(pattern, lower):
            return True, 25.0, "bold_claim_hook"

    # 3. Visual presentation starter
    if any(k in lower for k in ["whiteboard", "neural network", "draw", "chart", "look at this"]):
        return True, 25.0, "visual_hook"

    # 4. Standard clean sentence starter
    return True, 10.0, "clean_premise"

def evaluate_story_end(text: str) -> Tuple[bool, float]:
    """
    Evaluates whether a segment functions as a satisfying narrative conclusion.
    Returns: (is_valid, bonus_score)
    """
    clean = text.strip()
    if not ends_with_terminal_punctuation(clean):
        return False, 0.0

    bare = clean.rstrip('.!?').strip().lower()
    words = bare.split()
    if not words:
        return False, 0.0

    last_word = words[-1]
    last_two = " ".join(words[-2:]) if len(words) >= 2 else last_word

    # Reject trailing dangling words
    for reject in REJECT_END_WORDS:
        if last_word == reject or last_two == reject:
            return False, 0.0

    # Reward strong resolving phrases
    for rp in RESOLVING_PHRASES:
        if rp in bare:
            return True, 25.0

    return True, 10.0

def segment_transcript(
    segments: List[Dict[str, Any]],
    min_duration: float = 35.0,
    max_duration: float = 75.0
) -> List[Dict[str, Any]]:
    """
    Intelligent Narrative Story Arc Detection:
    Groups transcript segments into complete, self-contained story clips:
    1. Identifies compelling narrative hooks (questions, bold claims, problem setups).
    2. Extends through the narrative explanation / demonstration (target 35-75s).
    3. Concludes cleanly on a definitive resolving thought or punchline.
    4. Identifies visual whiteboard / chart demonstrations to prioritize high-value visual stories.
    """
    if not segments:
        return []

    total_duration = segments[-1]["end"] - segments[0]["start"]

    # For extremely short videos (< 35s), return single full-length candidate
    if total_duration <= 35.0:
        full_text = " ".join(s["text"].strip() for s in segments)
        return [{
            "start_time": round(segments[0]["start"], 2),
            "end_time": round(segments[-1]["end"], 2),
            "duration": round(total_duration, 2),
            "text": full_text,
            "has_visual": any(vk in full_text.lower() for vk in VISUAL_KEYWORDS),
            "visual_cues": [vk for vk in VISUAL_KEYWORDS if vk in full_text.lower()],
            "segment_indices": list(range(len(segments)))
        }]

    candidates = []
    n = len(segments)

    # Step through candidate starting segments
    for i in range(n):
        start_seg = segments[i]
        is_valid_start, start_bonus, hook_type = evaluate_story_start(start_seg["text"])

        # Allow non-hook segments only every 4th segment to ensure broad coverage
        if not is_valid_start and i % 4 != 0:
            continue

        start_time = start_seg["start"]
        current_text_parts = []
        current_indices = []

        for j in range(i, n):
            seg = segments[j]
            current_text_parts.append(seg["text"].strip())
            current_indices.append(j)

            duration = seg["end"] - start_time

            # Exceeded maximum duration
            if duration > max_duration:
                break

            # Reached target narrative length
            if duration >= min_duration:
                is_valid_end, end_bonus = evaluate_story_end(seg["text"])

                if is_valid_end:
                    full_text = " ".join(current_text_parts)
                    detected_visuals = [vk for vk in VISUAL_KEYWORDS if vk in full_text.lower()]
                    has_visual = len(detected_visuals) > 0

                    # Optimal duration curve (peak around 45s - 65s)
                    dur_fitness = 100.0 - abs(duration - 52.0) * 1.4
                    visual_score = 25.0 if has_visual else 0.0

                    story_score = dur_fitness + start_bonus + end_bonus + visual_score

                    candidates.append({
                        "start_time": round(start_time, 2),
                        "end_time": round(seg["end"], 2),
                        "duration": round(duration, 2),
                        "text": full_text,
                        "has_visual": has_visual,
                        "visual_cues": detected_visuals,
                        "hook_type": hook_type,
                        "story_score": round(story_score, 1),
                        "segment_indices": list(current_indices)
                    })

    # Fallback if no window matched strict ending criteria
    if not candidates:
        full_text = " ".join(s["text"].strip() for s in segments)
        candidates.append({
            "start_time": round(segments[0]["start"], 2),
            "end_time": round(min(segments[-1]["end"], segments[0]["start"] + max_duration), 2),
            "duration": round(min(total_duration, max_duration), 2),
            "text": full_text[:400],
            "has_visual": False,
            "visual_cues": [],
            "hook_type": "fallback",
            "story_score": 50.0,
            "segment_indices": list(range(min(n, 15)))
        })

    return candidates
