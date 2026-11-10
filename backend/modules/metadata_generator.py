import re
from typing import Dict, Any, List

DEFAULT_HASHTAGS = ["#Shorts", "#YouTubeShorts", "#Viral", "#Trending", "#MustWatch"]

TOPIC_KEYWORDS = {
    "ai": ["#AI", "#ArtificialIntelligence", "#Tech"],
    "artificial intelligence": ["#AI", "#ArtificialIntelligence", "#Tech"],
    "tech": ["#Tech", "#Technology", "#Innovation"],
    "business": ["#Business", "#Entrepreneur", "#Success", "#Money"],
    "podcast": ["#Podcast", "#Interview", "#Mindset"],
    "secret": ["#Secret", "#LifeHacks", "#Facts"],
    "mistake": ["#Tips", "#Advice", "#Lessons"]
}

def generate_shorts_metadata(
    clip_text: str,
    base_title: str = "",
    channel_name: str = "ViralCut AI"
) -> Dict[str, Any]:
    """
    Generates YouTube Shorts metadata (Title, Description, Hashtags, Category).
    """
    # 1. Clean Title (Ensure under 60 chars)
    title = base_title.strip() if base_title else "Insane Moment You Must See!"
    if not title.endswith("!") and not title.endswith("?"):
        title += "!"

    # Append #Shorts to title if space permits
    if len(title) <= 50 and "#shorts" not in title.lower():
        title = f"{title} #Shorts"

    # 2. Extract Topic Hashtags
    text_lower = clip_text.lower()
    custom_tags = list(DEFAULT_HASHTAGS)

    for keyword, tags in TOPIC_KEYWORDS.items():
        if keyword in text_lower:
            for t in tags:
                if t not in custom_tags:
                    custom_tags.append(t)

    hashtags_str = " ".join(custom_tags[:8])

    # 3. Generate Description
    sentences = re.split(r'[.!?]+', clip_text.strip())
    summary = " ".join([s.strip() for s in sentences if s.strip()][:2])

    description = f"""{summary}

🔔 Subscribe for more daily insights and viral highlights!
👍 Like & comment what you think about this moment.

{hashtags_str}

Created with {channel_name}
"""

    return {
        "title": title[:100],
        "description": description.strip(),
        "hashtags": hashtags_str,
        "category": "Entertainment"
    }
