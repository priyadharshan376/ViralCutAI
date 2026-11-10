import re
from typing import Dict, Any, List

DEFAULT_HASHTAGS = [
    "#Shorts",
    "#PDX",
    "#Psychology",
    "#Habits",
    "#Mindset",
    "#SelfImprovement",
    "#Neuroscience",
    "#ViralShorts"
]

TOPIC_KEYWORDS = {
    "habit": ["#Habits", "#AtomicHabits", "#BehaviorChange", "#BrainLoop"],
    "brain": ["#Neuroscience", "#BrainHacks", "#CognitiveScience", "#PsychologyFacts"],
    "mind": ["#Mindset", "#MentalModels", "#Focus", "#DeepWork"],
    "trick": ["#LifeHacks", "#ProductivityHacks", "#SelfImprovement", "#SuccessTips"],
    "learn": ["#Learning", "#VisualLearning", "#Whiteboard", "#Science"],
    "ai": ["#AI", "#ArtificialIntelligence", "#Tech", "#Future"],
    "business": ["#Business", "#Entrepreneur", "#Success", "#Money"],
    "podcast": ["#Podcast", "#Interview", "#Mindset", "#Wisdom"]
}

BASE_SEO_TAGS = [
    "PDX", "PDX Shorts", "psychology", "habit loops", "how to break habits",
    "neuroscience", "mental models", "cognitive science", "self improvement",
    "productivity", "brain science", "whiteboard breakdown", "viral shorts",
    "psychology facts", "focus hacks", "motivation", "daily shorts"
]

def generate_shorts_metadata(
    clip_text: str,
    base_title: str = "",
    channel_name: str = "PDX"
) -> Dict[str, Any]:
    """
    Generates high-engagement YouTube Shorts metadata tailored for PDX:
    - Punchy, high-CTR Title (< 60 chars with #Shorts)
    - Rich, structured Description with hook, core takeaways, and CTA
    - Curated Hashtags (#Shorts, #PDX, etc.)
    - Comprehensive SEO Search Tags
    """
    # 1. Clean & Optimize Title
    title = base_title.strip() if base_title else "Insane Mindset Trick You Must Know!"
    if not title.endswith("!") and not title.endswith("?"):
        title += "!"

    # Append #Shorts to title if space permits (< 60 chars)
    if len(title) <= 50 and "#shorts" not in title.lower():
        title = f"{title} #Shorts"

    # 2. Extract Topic Hashtags
    text_lower = clip_text.lower()
    custom_hashtags = list(DEFAULT_HASHTAGS)

    for keyword, tags in TOPIC_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in custom_hashtags:
                    custom_hashtags.append(t)

    hashtags_str = " ".join(custom_hashtags[:8])

    # 3. Build Topic-Aware Tags for YouTube Tag List
    seo_tags = list(BASE_SEO_TAGS)
    for word in ["dopamine", "routine", "cue", "reward", "discipline", "subconscious"]:
        if word in text_lower and word not in seo_tags:
            seo_tags.append(word)

    # 4. Generate High-Retention Rich Description
    sentences = [s.strip() for s in re.split(r'[.!?]+', clip_text.strip()) if len(s.strip()) > 10]
    hook_sentence = sentences[0] if sentences else "Why does your brain fall into the same traps?"
    summary_sentence = sentences[1] if len(sentences) > 1 else "Decode the science behind your habits in 60 seconds."
    takeaway_sentence = sentences[2] if len(sentences) > 2 else "Apply this practical mental model today."

    description = f"""{hook_sentence}! 🧠⚡

{summary_sentence}

Key Takeaways:
• {takeaway_sentence}
• Break the subconscious cycle before it starts
• Master your focus with evidence-based mental models

💡 Visual breakdowns, psychology facts, and practical neuroscience.
🎬 New Shorts published daily on {channel_name}!

👉 Hit Subscribe to master your mind in under 60 seconds: @{channel_name}

{hashtags_str}

---
Created and automated with ViralCut AI for {channel_name}.
"""

    return {
        "title": title[:100],
        "description": description.strip(),
        "hashtags": hashtags_str,
        "tags": seo_tags[:25],
        "category": "Entertainment"
    }
