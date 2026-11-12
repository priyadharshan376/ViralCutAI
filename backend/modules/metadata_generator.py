import re
from typing import Dict, Any, List

NICHE_PROFILES: Dict[str, Dict[str, Any]] = {
    "gta6": {
        "keywords": ["gta 6", "gta6", "gta vi", "vice city", "rockstar", "jason", "lucia", "grand theft auto"],
        "hashtags": ["#Shorts", "#GTA6", "#GTAVI", "#RockstarGames", "#GamingShorts", "#Gameplay", "#ViralShorts", "#PDX"],
        "tags": ["GTA 6", "GTA VI", "GTA 6 gameplay", "GTA 6 trailer", "Rockstar Games", "Vice City", "gaming shorts", "viral gaming", "PS5", "open world", "PDX"],
        "emoji": "🎮🔥",
        "fallback_title": "Insane GTA 6 Detail You Missed!",
        "fallback_hook": "This GTA 6 detail is blowing everyone's mind!",
        "fallback_summary": "Breaking down the craziest Rockstar Games details, secrets, and gameplay highlights.",
        "niche_line": "🎮 Daily GTA 6 leaks, gameplay highlights, and viral gaming Shorts.",
        "category": "Gaming",
    },
    "gaming": {
        "keywords": ["gameplay", "gaming", "ps5", "xbox", "pc gaming", "fps", "clutch", "boss", "walkthrough", "mod", "mods", "gamer", "esports", "minecraft", "fortnite", "valorant", "call of duty"],
        "hashtags": ["#Shorts", "#Gaming", "#GamingShorts", "#Gameplay", "#Gamer", "#ViralGaming", "#ViralShorts", "#PDX"],
        "tags": ["gaming", "gaming shorts", "gameplay", "viral gaming", "insane gameplay", "funny gaming moments", "gamer", "PDX", "youtube shorts"],
        "emoji": "🕹️⚡",
        "fallback_title": "Insane Gameplay Moment!",
        "fallback_hook": "You won't believe what just happened in this gameplay!",
        "fallback_summary": "High-intensity gameplay highlights, hidden secrets, and epic moments in under 60 seconds.",
        "niche_line": "🕹️ Epic gameplay clips, viral gaming highlights, and secrets daily.",
        "category": "Gaming",
    },
    "mystery_crime": {
        "keywords": ["mystery", "true crime", "unsolved", "crime", "detective", "murder", "disappeared", "suspect", "case", "investigation", "serial", "fbi", "cold case"],
        "hashtags": ["#Shorts", "#TrueCrime", "#Mystery", "#Unsolved", "#CrimeStory", "#Documentary", "#ViralShorts", "#PDX"],
        "tags": ["true crime", "unsolved mystery", "mystery shorts", "crime documentary", "scary stories", "cold case", "real mystery", "PDX"],
        "emoji": "🕵️🔍",
        "fallback_title": "The Unsolved Mystery Nobody Can Explain!",
        "fallback_hook": "This real-life mystery still baffles investigators!",
        "fallback_summary": "Uncovering the chilling clues and twists behind this true crime case in 60 seconds.",
        "niche_line": "🕵️ Gripping true crime cases, mysteries, and unsolved stories daily.",
        "category": "Entertainment",
    },
    "luxury": {
        "keywords": ["luxury", "mansion", "supercar", "yacht", "private jet", "rolex", "bugatti", "lamborghini", "ferrari", "penthouse", "rich lifestyle", "net worth"],
        "hashtags": ["#Shorts", "#Luxury", "#LuxuryLifestyle", "#Billionaire", "#RichLifestyle", "#Wealth", "#Success", "#PDX"],
        "tags": ["luxury lifestyle", "billionaire lifestyle", "supercars", "luxury mansion", "rich lifestyle", "wealth", "millionaire", "PDX"],
        "emoji": "💎🥂",
        "fallback_title": "Inside a Billionaire's Luxury Lifestyle!",
        "fallback_hook": "This is what extreme wealth really looks like!",
        "fallback_summary": "Exploring ultra-luxury lifestyles, supercars, mansions, and how billionaires live.",
        "niche_line": "💎 Daily luxury lifestyle, billionaire wealth, and dream setups.",
        "category": "Entertainment",
    },
    "tech_ai": {
        "keywords": ["ai", "artificial intelligence", "chatgpt", "openai", "robot", "coding", "software", "tech", "future", "algorithm", "nvidia", "apple"],
        "hashtags": ["#Shorts", "#AI", "#Tech", "#ArtificialIntelligence", "#FutureTech", "#TechShorts", "#ViralShorts", "#PDX"],
        "tags": ["AI", "artificial intelligence", "tech news", "future technology", "coding", "tech shorts", "viral tech", "PDX"],
        "emoji": "🤖⚡",
        "fallback_title": "This AI Tech Changes Everything!",
        "fallback_hook": "This new AI breakthrough is moving faster than anyone predicted!",
        "fallback_summary": "Breaking down the biggest AI and technology shifts in under 60 seconds.",
        "niche_line": "🤖 Daily AI breakthroughs, tech insights, and future trends.",
        "category": "Science & Technology",
    },
    "business": {
        "keywords": ["business", "money", "entrepreneur", "billionaire", "millionaire", "startup", "investing", "wealth", "rich", "income", "ceo", "founder"],
        "hashtags": ["#Shorts", "#Business", "#Entrepreneur", "#Wealth", "#Money", "#Success", "#Mindset", "#PDX"],
        "tags": ["business", "entrepreneurship", "how to make money", "wealth mindset", "founder advice", "business shorts", "PDX"],
        "emoji": "💰🚀",
        "fallback_title": "The Harsh Truth About Wealth!",
        "fallback_hook": "Most people miss this one rule about building wealth!",
        "fallback_summary": "Actionable business lessons and founder secrets distilled into 60 seconds.",
        "niche_line": "💰 Daily business rules, wealth lessons, and founder breakdowns.",
        "category": "Education",
    },
    "mindset": {
        "keywords": ["habit", "brain", "mind", "psychology", "dopamine", "discipline", "subconscious", "focus", "motivation", "neuroscience", "routine"],
        "hashtags": ["#Shorts", "#Mindset", "#Psychology", "#Discipline", "#Habits", "#SelfImprovement", "#ViralShorts", "#PDX"],
        "tags": ["mindset", "psychology facts", "discipline", "habit loops", "self improvement", "focus hacks", "motivation", "PDX"],
        "emoji": "🧠⚡",
        "fallback_title": "Insane Mindset Trick You Must Know!",
        "fallback_hook": "Why does your brain fall into the same traps?",
        "fallback_summary": "Decode the psychology behind focus, discipline, and habits in 60 seconds.",
        "niche_line": "💡 Visual breakdowns, psychology facts, and mindset upgrades daily.",
        "category": "Education",
    },
}

GENERAL_VIRAL_PROFILE: Dict[str, Any] = {
    "hashtags": ["#Shorts", "#Viral", "#Trending", "#MustWatch", "#Facts", "#ViralShorts", "#PDX"],
    "tags": ["viral shorts", "trending", "must watch", "youtube shorts", "daily clips", "PDX"],
    "emoji": "🔥🎬",
    "fallback_title": "Wait Until You See This!",
    "fallback_hook": "Wait until you hear what happens next!",
    "fallback_summary": "The best high-retention highlight clipped in crisp 1080p.",
    "niche_line": "🎬 New high-impact Shorts uploaded daily!",
    "category": "Entertainment",
}


def detect_niche_profile(combined_text: str) -> Dict[str, Any]:
    text_lower = combined_text.lower()
    # Check most specific profiles first
    for key in ["gta6", "mystery_crime", "luxury", "gaming", "tech_ai", "business", "mindset"]:
        profile = NICHE_PROFILES[key]
        if any(kw in text_lower for kw in profile["keywords"]):
            return profile
    return GENERAL_VIRAL_PROFILE


def generate_shorts_metadata(
    clip_text: str,
    base_title: str = "",
    channel_name: str = "PDX",
    source_filename: str = ""
) -> Dict[str, Any]:
    """
    Generates niche-aware, high-CTR YouTube Shorts metadata maximized for discovery & views.
    Automatically adapts hashtags, tags, and description for Gaming/GTA 6, Tech/AI,
    Business, Mindset, or General Viral entertainment.
    """
    combined_context = f"{base_title} {source_filename} {clip_text}"
    profile = detect_niche_profile(combined_context)

    # 1. Clean & Optimize High-CTR Title
    title = base_title.strip() if base_title else profile["fallback_title"]
    if not title.endswith("!") and not title.endswith("?"):
        title += "!"

    if len(title) <= 50 and "#shorts" not in title.lower():
        title = f"{title} #Shorts"

    hashtags_list = list(profile["hashtags"])
    hashtags_str = " ".join(hashtags_list[:8])

    seo_tags = list(profile["tags"])

    # 2. Build Niche-Matched Description
    sentences = [s.strip() for s in re.split(r'[.!?]+', (clip_text or "").strip()) if len(s.strip()) > 10]
    hook_sentence = sentences[0] if sentences else profile["fallback_hook"]
    summary_sentence = sentences[1] if len(sentences) > 1 else profile["fallback_summary"]

    description = f"""{hook_sentence}! {profile['emoji']}

{summary_sentence}

{profile['niche_line']}
👉 Subscribe for daily Shorts on {channel_name}: @{channel_name}

{hashtags_str}

---
Created in 1080p Full HD with ViralCut AI for {channel_name}.
"""

    return {
        "title": title[:100],
        "description": description.strip(),
        "hashtags": hashtags_str,
        "tags": seo_tags[:25],
        "category": profile["category"]
    }
