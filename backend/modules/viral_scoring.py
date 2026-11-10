import re
from typing import Dict, Any

# Weights defined in documentation:
# Hook: 25%, Emotion: 20%, Info: 15%, Storytelling: 15%, Context: 15%, Engagement: 10%
WEIGHTS = {
    "hook": 0.25,
    "emotion": 0.20,
    "information": 0.15,
    "storytelling": 0.15,
    "context": 0.15,
    "engagement": 0.10
}

# Lexical dictionaries
HOOK_STARTERS = [
    r'^(did you know|have you ever|what if|why do|how to|here is why|the secret|the biggest mistake|nobody talks about)',
    r'^(this is why|i tested|i discovered|stop doing|never do|watch this|you won\'t believe)',
    r'^(imagine|if you|can you believe|the truth about|the most|why cutting|do you have|people hear)',
    r'^(now here is|now here\'s|if after|the craving is not|habit is pretty much)'
]

HOOK_POWER_WORDS = {
    "secret", "insane", "crazy", "shocking", "unexpected", "mistake", "warning",
    "genius", "hack", "truth", "never", "always", "hidden", "ruined", "ultimate",
    "impossible", "magic", "weird", "bizarre", "forbidden", "trick", "neural"
}

EMOTION_WORDS = {
    "laugh", "funny", "hilarious", "joke", "crying", "scared", "fear", "angry",
    "amazed", "amazing", "incredible", "unbelievable", "blown away", "excited",
    "wild", "love", "hate", "disaster", "fail", "win", "shock", "genius",
    "stunned", "fascinating", "horrible", "awesome", "epic", "guilty", "shame", "sad"
}

INFO_KEYWORDS = {
    "because", "reason", "step", "method", "strategy", "algorithm", "system",
    "technique", "research", "study", "data", "proven", "result", "formula",
    "concept", "principle", "tip", "rule", "framework", "process", "neural", "network",
    "brain", "behavior", "craving", "cycle", "replacement", "pause"
}

VISUAL_WORDS = {
    "whiteboard", "draw", "drawing", "chart", "diagram", "graph",
    "eye", "dot", "circle", "phone", "look at this", "see here"
}

STORY_BEGIN_WORDS = {"once", "when", "first", "it started", "initially", "back in", "years ago", "why", "let's say"}
STORY_TWIST_WORDS = {"suddenly", "but", "however", "unexpectedly", "turns out", "problem was", "twist", "instead", "loop"}
STORY_RESOLVE_WORDS = {
    "finally", "that's why", "in the end", "which means", "and so", "conclusion",
    "result was", "that's it", "that is how", "starts with", "same thing", "promise",
    "tree trunk", "breaking the cycle", "not doing it"
}

ENGAGEMENT_WORDS = {
    "comment", "tell me", "what do you think", "agree", "disagree", "subscribe",
    "share", "try this", "let me know", "drop a comment", "relatable", "who else"
}

def analyze_hook(text: str) -> tuple[float, str]:
    """Score the opening statement (0 - 100)."""
    sentences = re.split(r'[.!?]+', text.strip())
    first_sentence = sentences[0].strip().lower() if sentences else ""
    words = set(re.findall(r'\b\w+\b', first_sentence))

    score = 45.0  # baseline
    reason_parts = []

    # Check question hook
    if "?" in text[:120] or any(first_sentence.startswith(q) for q in ["why", "how", "what", "is it", "can", "do you", "did you"]):
        score += 30.0
        reason_parts.append("provocative question hook")

    # Check patterned starters
    for pattern in HOOK_STARTERS:
        if re.search(pattern, first_sentence):
            score += 25.0
            reason_parts.append("strong curiosity starter")
            break

    # Check power words in first sentence
    matched_power = words.intersection(HOOK_POWER_WORDS)
    if matched_power:
        bonus = min(20.0, len(matched_power) * 10.0)
        score += bonus
        reason_parts.append(f"power words ({', '.join(list(matched_power)[:2])})")

    # Length fitness for a hook (ideal: 5 to 25 words)
    word_count = len(first_sentence.split())
    if 5 <= word_count <= 25:
        score += 10.0

    score = max(0.0, min(100.0, score))
    reason = ", ".join(reason_parts) if reason_parts else "standard opening statement"
    return round(score, 1), reason

def analyze_emotion(text: str) -> float:
    """Score emotional intensity (0 - 100)."""
    words = set(re.findall(r'\b\w+\b', text.lower()))
    matches = words.intersection(EMOTION_WORDS)
    exclamations = text.count("!")

    score = 40.0 + (len(matches) * 15.0) + (exclamations * 5.0)
    return round(max(0.0, min(100.0, score)), 1)

def analyze_information(text: str, has_visual: bool = False) -> float:
    """Score informational value and substance (0 - 100)."""
    words = set(re.findall(r'\b\w+\b', text.lower()))
    matches = words.intersection(INFO_KEYWORDS)
    visual_matches = words.intersection(VISUAL_WORDS)
    numbers = len(re.findall(r'\b\d+(?:[\.,]\d+)?%?\b', text))

    score = 35.0 + (len(matches) * 8.0) + (min(numbers, 3) * 8.0)
    if has_visual or visual_matches:
        score += 20.0  # Big bonus for visual drawing / chart demonstrations

    return round(max(0.0, min(100.0, score)), 1)

def analyze_storytelling(text: str) -> float:
    """Score presence of narrative arc (Beginning -> Conflict/Twist -> Resolution)."""
    words = set(re.findall(r'\b\w+\b', text.lower()))

    has_begin = bool(words.intersection(STORY_BEGIN_WORDS))
    has_twist = bool(words.intersection(STORY_TWIST_WORDS))
    has_resolve = any(rw in text.lower() for rw in STORY_RESOLVE_WORDS)

    arc_stages = sum([has_begin, has_twist, has_resolve])
    if arc_stages == 3:
        score = 95.0
    elif arc_stages == 2:
        score = 80.0
    elif arc_stages == 1:
        score = 65.0
    else:
        score = 50.0

    return round(score, 1)

def analyze_context_completeness(text: str) -> float:
    """Score standalone coherence and self-containment (0 - 100)."""
    score = 65.0
    first_words = text.strip().split()[:2]
    first_phrase = " ".join(first_words).lower()

    # Penalize dangling pronouns at start
    dangling = ["and then", "also", "he said", "she said", "they said", "but anyway", "what that", "instead of"]
    if any(first_phrase.startswith(d) for d in dangling):
        score -= 25.0
    else:
        score += 15.0

    # Reward clean terminal punctuation
    if text.strip()[-1:] in [".", "!", "?"]:
        score += 20.0
    else:
        score -= 20.0

    return round(max(0.0, min(100.0, score)), 1)

def analyze_engagement(text: str) -> float:
    """Score audience engagement and shareability (0 - 100)."""
    words = set(re.findall(r'\b\w+\b', text.lower()))
    matches = words.intersection(ENGAGEMENT_WORDS)

    score = 45.0 + (len(matches) * 15.0)
    if "?" in text:
        score += 15.0

    return round(max(0.0, min(100.0, score)), 1)

def generate_clip_title(text: str) -> str:
    """Generate an engaging, short working title for the clip."""
    lower = text.lower()

    # Domain-specific narrative title matchers
    if "whiteboard" in lower and "cutting off" in lower:
        return "Why Breaking Habits Is So Hard! (Whiteboard)"
    if "neural network" in lower and "crav" in lower:
        return "How Habits Wire Your Brain"
    if "tree trunk" in lower or "roots of a tree" in lower:
        return "The Brain Loop That Traps You"
    if "cognitive pause" in lower:
        return "The Cognitive Pause Trick"
    if "60 seconds" in lower and "close your eyes" in lower:
        return "The 60-Second Trick to Break ANY Habit"
    if "addiction" in lower and "habit" in lower:
        return "Habit vs Addiction: The Truth"
    if "overwhelm and shame" in lower:
        return "The Shame Cycle of Scrolling"

    sentences = re.split(r'[.!?]+', text.strip())
    first = sentences[0].strip() if sentences else "Interesting Moment"

    # If first sentence is a punchy question
    if "?" in first and len(first.split()) <= 10:
        return first

    # Otherwise synthesize a title from top keywords
    cleaned = re.sub(r'[^\w\s]', '', first)
    short_title = " ".join(cleaned.split()[:6])
    return f"{short_title.title()}!"

def score_clip_candidate(text: str, has_visual: bool = False) -> Dict[str, Any]:
    """
    Computes all component scores and calculates weighted viral potential score:
    viral_score = (hook * 0.25) + (emotion * 0.20) + (info * 0.15) + (story * 0.15) + (context * 0.15) + (engagement * 0.10)
    """
    hook_score, hook_reason = analyze_hook(text)
    emotion_score = analyze_emotion(text)
    info_score = analyze_information(text, has_visual=has_visual)
    story_score = analyze_storytelling(text)
    context_score = analyze_context_completeness(text)
    engagement_score = analyze_engagement(text)

    weighted_score = (
        (hook_score * WEIGHTS["hook"]) +
        (emotion_score * WEIGHTS["emotion"]) +
        (info_score * WEIGHTS["information"]) +
        (story_score * WEIGHTS["storytelling"]) +
        (context_score * WEIGHTS["context"]) +
        (engagement_score * WEIGHTS["engagement"])
    )

    # Extra viral potential boost for visual drawing/chart demonstrations
    if has_visual:
        weighted_score += 8.0

    final_score = round(max(10.0, min(99.0, weighted_score)), 1)
    title = generate_clip_title(text)

    # Primary reason summary
    top_factor = "Complete story arc with strong hook & payoff"
    if has_visual:
        top_factor = f"🎨 Visual Whiteboard Demonstration: {hook_reason}"
    elif hook_score >= 80:
        top_factor = f"Strong hook: {hook_reason}"
    elif story_score >= 85:
        top_factor = "Compelling narrative progression & punchline"
    elif emotion_score >= 75:
        top_factor = "High emotional impact & relatable struggle"
    elif info_score >= 75:
        top_factor = "Actionable scientific explanation & facts"

    return {
        "hook_score": hook_score,
        "emotional_score": emotion_score,
        "information_score": info_score,
        "storytelling_score": story_score,
        "context_score": context_score,
        "engagement_score": engagement_score,
        "viral_score": final_score,
        "has_visual": has_visual,
        "reason": top_factor,
        "title": title
    }
