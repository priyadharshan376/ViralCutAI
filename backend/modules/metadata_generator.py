import re
from typing import Dict, Any, List, Optional

# Prominent Public Figures, Creators, Games, and Entities for Knowledge Graph SEO
KNOWN_ENTITIES: List[Dict[str, Any]] = [
    # Tech / Founders / Visionaries
    {
        "name": "Elon Musk",
        "aliases": ["elon musk", "elon", "musk", "spacex", "tesla", "xai", "neuralink"],
        "hashtags": ["#ElonMusk", "#Tesla", "#SpaceX", "#xAI"],
        "tags": ["Elon Musk", "Elon Musk interview", "Tesla", "SpaceX", "xAI", "Elon Musk advice"],
        "category": "Science & Technology",
        "role": "Tech Visionary & Founder"
    },
    {
        "name": "Sam Altman",
        "aliases": ["sam altman", "altman", "openai", "chatgpt", "gpt-4", "gpt-5"],
        "hashtags": ["#SamAltman", "#OpenAI", "#ChatGPT", "#ArtificialIntelligence"],
        "tags": ["Sam Altman", "OpenAI", "ChatGPT", "Sam Altman interview", "AGI"],
        "category": "Science & Technology",
        "role": "CEO of OpenAI"
    },
    {
        "name": "Jensen Huang",
        "aliases": ["jensen huang", "jensen", "nvidia"],
        "hashtags": ["#JensenHuang", "#Nvidia", "#AIHardware"],
        "tags": ["Jensen Huang", "Nvidia", "AI chips", "Nvidia CEO"],
        "category": "Science & Technology",
        "role": "CEO of Nvidia"
    },
    {
        "name": "Jeff Bezos",
        "aliases": ["jeff bezos", "bezos", "amazon", "blue origin"],
        "hashtags": ["#JeffBezos", "#Amazon", "#Billionaire", "#Wealth"],
        "tags": ["Jeff Bezos", "Amazon founder", "Jeff Bezos advice", "Blue Origin"],
        "category": "Education",
        "role": "Founder of Amazon"
    },
    {
        "name": "Mark Zuckerberg",
        "aliases": ["mark zuckerberg", "zuckerberg", "zuck", "meta"],
        "hashtags": ["#MarkZuckerberg", "#Meta"],
        "tags": ["Mark Zuckerberg", "Meta", "Zuckerberg interview"],
        "category": "Science & Technology",
        "role": "Founder & CEO of Meta"
    },
    {
        "name": "Steve Jobs",
        "aliases": ["steve jobs", "jobs", "apple"],
        "hashtags": ["#SteveJobs", "#Apple", "#Innovation"],
        "tags": ["Steve Jobs", "Apple", "Steve Jobs speech", "Steve Jobs advice"],
        "category": "Education",
        "role": "Co-founder of Apple"
    },

    # Podcast Hosts & Prominent Interviewers
    {
        "name": "Joe Rogan",
        "aliases": ["joe rogan", "rogan", "jre", "powerfuljre", "the joe rogan experience"],
        "hashtags": ["#JoeRogan", "#JRE", "#JoeRoganExperience"],
        "tags": ["Joe Rogan", "The Joe Rogan Experience", "JRE clips", "Joe Rogan podcast"],
        "category": "Entertainment",
        "role": "Host of The Joe Rogan Experience"
    },
    {
        "name": "Lex Fridman",
        "aliases": ["lex fridman", "lex", "fridman"],
        "hashtags": ["#LexFridman", "#LexFridmanPodcast"],
        "tags": ["Lex Fridman", "Lex Fridman Podcast", "Lex Fridman interview"],
        "category": "Education",
        "role": "Host of Lex Fridman Podcast"
    },
    {
        "name": "Dr. Andrew Huberman",
        "aliases": ["andrew huberman", "huberman", "huberman lab", "dr huberman"],
        "hashtags": ["#AndrewHuberman", "#HubermanLab", "#Neuroscience", "#Health"],
        "tags": ["Andrew Huberman", "Huberman Lab", "neuroscience", "dopamine", "sleep routine"],
        "category": "Education",
        "role": "Neuroscientist & Stanford Professor"
    },
    {
        "name": "Chris Williamson",
        "aliases": ["chris williamson", "modern wisdom"],
        "hashtags": ["#ChrisWilliamson", "#ModernWisdom"],
        "tags": ["Chris Williamson", "Modern Wisdom podcast", "life advice"],
        "category": "Education",
        "role": "Host of Modern Wisdom"
    },
    {
        "name": "Steven Bartlett",
        "aliases": ["steven bartlett", "diary of a ceo", "doac"],
        "hashtags": ["#StevenBartlett", "#DiaryOfACEO"],
        "tags": ["Steven Bartlett", "The Diary Of A CEO", "DOAC clips", "entrepreneurship"],
        "category": "Education",
        "role": "Host of The Diary Of A CEO"
    },
    {
        "name": "Patrick Bet-David",
        "aliases": ["patrick bet-david", "pbd", "valuetainment"],
        "hashtags": ["#PatrickBetDavid", "#Valuetainment"],
        "tags": ["Patrick Bet-David", "Valuetainment", "PBD podcast", "business advice"],
        "category": "Education",
        "role": "Host of PBD Podcast"
    },

    # Mindset, Psychology & High Performance
    {
        "name": "Dr. Jordan Peterson",
        "aliases": ["jordan peterson", "peterson", "dr jordan peterson"],
        "hashtags": ["#JordanPeterson", "#Psychology", "#Discipline", "#LifeAdvice"],
        "tags": ["Jordan Peterson", "Jordan Peterson advice", "psychology", "12 rules for life", "discipline"],
        "category": "Education",
        "role": "Clinical Psychologist & Author"
    },
    {
        "name": "Andrew Tate",
        "aliases": ["andrew tate", "tristan tate", "top g", "tate speech"],
        "hashtags": ["#AndrewTate", "#TopG", "#Motivation", "#Discipline"],
        "tags": ["Andrew Tate", "Andrew Tate motivation", "Top G", "discipline speech", "success mindset"],
        "category": "Education",
        "role": "Entrepreneur & Speaker"
    },
    {
        "name": "David Goggins",
        "aliases": ["david goggins", "goggins", "stay hard", "cant hurt me", "never finished"],
        "hashtags": ["#DavidGoggins", "#StayHard", "#Motivation", "#MentalToughness"],
        "tags": ["David Goggins", "Stay Hard", "Goggins motivation", "mental toughness", "Cant Hurt Me"],
        "category": "Education",
        "role": "Navy SEAL & Ultra-Endurance Athlete"
    },
    {
        "name": "Alex Hormozi",
        "aliases": ["alex hormozi", "hormozi", "acquisition.com", "100m offers", "100m leads"],
        "hashtags": ["#AlexHormozi", "#BusinessGrowth", "#Entrepreneur", "#Money"],
        "tags": ["Alex Hormozi", "100M Offers", "Acquisition.com", "business advice", "sales tips"],
        "category": "Education",
        "role": "Entrepreneur & Investor"
    },
    {
        "name": "Robert Greene",
        "aliases": ["robert greene", "48 laws of power", "laws of human nature", "art of seduction"],
        "hashtags": ["#RobertGreene", "#48LawsOfPower", "#Psychology", "#Strategy"],
        "tags": ["Robert Greene", "48 Laws of Power", "The Laws of Human Nature", "power dynamics"],
        "category": "Education",
        "role": "Bestselling Author & Historian"
    },
    {
        "name": "Naval Ravikant",
        "aliases": ["naval ravikant", "naval", "almanack of naval"],
        "hashtags": ["#NavalRavikant", "#WealthCreation", "#Wisdom", "#Philosophy"],
        "tags": ["Naval Ravikant", "how to get rich", "specific knowledge", "leverage", "happiness"],
        "category": "Education",
        "role": "Entrepreneur & Angel Investor"
    },

    # Gaming & GTA 6
    {
        "name": "Grand Theft Auto VI",
        "aliases": ["gta 6", "gta6", "gta vi", "vice city", "jason and lucia", "grand theft auto vi"],
        "hashtags": ["#GTA6", "#GTAVI", "#RockstarGames", "#ViceCity", "#GamingShorts", "#GTA6Leaks"],
        "tags": ["GTA 6", "GTA VI", "GTA 6 gameplay", "GTA 6 trailer", "Vice City", "Rockstar Games", "Jason and Lucia"],
        "category": "Gaming",
        "role": "Rockstar Games' Next-Gen Open World"
    },
    {
        "name": "Rockstar Games",
        "aliases": ["rockstar games", "rockstar", "rdr2", "red dead"],
        "hashtags": ["#RockstarGames", "#GTA", "#Gaming"],
        "tags": ["Rockstar Games", "GTA", "Red Dead Redemption", "gaming news"],
        "category": "Gaming",
        "role": "Video Game Developer & Publisher"
    },

    # Creators & Streamers
    {
        "name": "MrBeast",
        "aliases": ["mrbeast", "mr beast", "jimmy donaldson"],
        "hashtags": ["#MrBeast", "#ViralShorts"],
        "tags": ["MrBeast", "MrBeast shorts", "Jimmy Donaldson", "viral entertainment"],
        "category": "Entertainment",
        "role": "Content Creator & Philanthropist"
    },
    {
        "name": "IShowSpeed",
        "aliases": ["ishowspeed", "speed"],
        "hashtags": ["#IShowSpeed", "#Speed"],
        "tags": ["IShowSpeed", "Speed stream", "funny moments"],
        "category": "Gaming",
        "role": "Streamer & Entertainer"
    },
    {
        "name": "Kai Cenat",
        "aliases": ["kai cenat", "kai"],
        "hashtags": ["#KaiCenat", "#AMP"],
        "tags": ["Kai Cenat", "Kai stream", "AMP"],
        "category": "Entertainment",
        "role": "Streamer & Content Creator"
    },
]

NICHE_PROFILES: Dict[str, Dict[str, Any]] = {
    "gta6": {
        "keywords": ["gta 6", "gta6", "gta vi", "vice city", "rockstar", "jason", "lucia", "grand theft auto"],
        "hashtags": ["#Shorts", "#GTA6", "#GTAVI", "#RockstarGames", "#GamingShorts", "#Gameplay", "#ViralShorts", "#PDX"],
        "tags": ["GTA 6", "GTA VI", "GTA 6 gameplay", "GTA 6 trailer", "Rockstar Games", "Vice City", "gaming shorts", "viral gaming", "PS5", "open world", "PDX"],
        "emoji": "🎮🔥",
        "fallback_title": "Insane GTA 6 Detail You Missed!",
        "topic_label": "Grand Theft Auto VI Breakdown & Secrets",
        "engagement_q": "💬 What feature or location are you most hyped for in GTA 6? Drop your thoughts below!",
        "niche_line": "🎮 Daily GTA 6 leaks, gameplay highlights, and viral gaming Shorts.",
        "category": "Gaming",
    },
    "gaming": {
        "keywords": ["gameplay", "gaming", "ps5", "xbox", "pc gaming", "fps", "clutch", "boss", "walkthrough", "mod", "mods", "gamer", "esports", "minecraft", "fortnite", "valorant", "call of duty"],
        "hashtags": ["#Shorts", "#Gaming", "#GamingShorts", "#Gameplay", "#Gamer", "#ViralGaming", "#ViralShorts", "#PDX"],
        "tags": ["gaming", "gaming shorts", "gameplay", "viral gaming", "insane gameplay", "funny gaming moments", "gamer", "PDX", "youtube shorts"],
        "emoji": "🕹️⚡",
        "fallback_title": "Insane Gameplay Moment!",
        "topic_label": "High-Intensity Gameplay & Gaming Highlights",
        "engagement_q": "💬 Have you ever pulled off a moment like this? Tell us in the comments!",
        "niche_line": "🕹️ Epic gameplay clips, viral gaming highlights, and secrets daily.",
        "category": "Gaming",
    },
    "mystery_crime": {
        "keywords": ["mystery", "true crime", "unsolved", "crime", "detective", "murder", "disappeared", "suspect", "case", "investigation", "serial", "fbi", "cold case"],
        "hashtags": ["#Shorts", "#TrueCrime", "#Mystery", "#Unsolved", "#CrimeStory", "#Documentary", "#ViralShorts", "#PDX"],
        "tags": ["true crime", "unsolved mystery", "mystery shorts", "crime documentary", "scary stories", "cold case", "real mystery", "PDX"],
        "emoji": "🕵️🔍",
        "fallback_title": "The Unsolved Mystery Nobody Can Explain!",
        "topic_label": "True Crime Investigation & Unsolved Mysteries",
        "engagement_q": "💬 What do you think really happened here? Leave your theory in the comments!",
        "niche_line": "🕵️ Gripping true crime cases, mysteries, and unsolved stories daily.",
        "category": "Entertainment",
    },
    "luxury": {
        "keywords": ["luxury", "mansion", "supercar", "yacht", "private jet", "rolex", "bugatti", "lamborghini", "ferrari", "penthouse", "rich lifestyle", "net worth"],
        "hashtags": ["#Shorts", "#Luxury", "#LuxuryLifestyle", "#Billionaire", "#RichLifestyle", "#Wealth", "#Success", "#PDX"],
        "tags": ["luxury lifestyle", "billionaire lifestyle", "supercars", "luxury mansion", "rich lifestyle", "wealth", "millionaire", "PDX"],
        "emoji": "💎🥂",
        "fallback_title": "Inside a Billionaire's Luxury Lifestyle!",
        "topic_label": "Ultra-Luxury Lifestyle & Extreme Wealth",
        "engagement_q": "💬 If you had unlimited money, what's the very first thing you would buy? Drop it below!",
        "niche_line": "💎 Daily luxury lifestyle, billionaire wealth, and dream setups.",
        "category": "Entertainment",
    },
    "tech_ai": {
        "keywords": ["ai", "artificial intelligence", "chatgpt", "openai", "robot", "coding", "software", "tech", "future", "algorithm", "nvidia", "apple", "agi", "llm"],
        "hashtags": ["#Shorts", "#AI", "#Tech", "#ArtificialIntelligence", "#FutureTech", "#TechShorts", "#ViralShorts", "#PDX"],
        "tags": ["AI", "artificial intelligence", "tech news", "future technology", "coding", "tech shorts", "viral tech", "PDX"],
        "emoji": "🤖⚡",
        "fallback_title": "This AI Tech Changes Everything!",
        "topic_label": "AI Breakthroughs & Future Technology",
        "engagement_q": "💬 Do you think AI is advancing faster than humanity is ready for? Share your perspective!",
        "niche_line": "🤖 Daily AI breakthroughs, tech insights, and future trends.",
        "category": "Science & Technology",
    },
    "business": {
        "keywords": ["business", "money", "entrepreneur", "billionaire", "millionaire", "startup", "investing", "wealth", "rich", "income", "ceo", "founder", "sales", "revenue"],
        "hashtags": ["#Shorts", "#Business", "#Entrepreneur", "#Wealth", "#Money", "#Success", "#Mindset", "#PDX"],
        "tags": ["business", "entrepreneurship", "how to make money", "wealth mindset", "founder advice", "business shorts", "PDX"],
        "emoji": "💰🚀",
        "fallback_title": "The Harsh Truth About Wealth!",
        "topic_label": "Entrepreneurship, Wealth & Financial Freedom",
        "engagement_q": "💬 Do you agree or disagree with this business principle? Let us know below!",
        "niche_line": "💰 Daily business rules, wealth lessons, and founder breakdowns.",
        "category": "Education",
    },
    "mindset": {
        "keywords": ["habit", "brain", "mind", "psychology", "dopamine", "discipline", "subconscious", "focus", "motivation", "neuroscience", "routine", "stoic", "stoicism"],
        "hashtags": ["#Shorts", "#Mindset", "#Psychology", "#Discipline", "#Habits", "#SelfImprovement", "#ViralShorts", "#PDX"],
        "tags": ["mindset", "psychology facts", "discipline", "habit loops", "self improvement", "focus hacks", "motivation", "PDX"],
        "emoji": "🧠⚡",
        "fallback_title": "Insane Mindset Trick You Must Know!",
        "topic_label": "Human Psychology, Discipline & Peak Performance",
        "engagement_q": "💬 What daily habit transformed your life the most? Share your answer in the comments!",
        "niche_line": "💡 Visual breakdowns, psychology facts, and mindset upgrades daily.",
        "category": "Education",
    },
}

GENERAL_VIRAL_PROFILE: Dict[str, Any] = {
    "hashtags": ["#Shorts", "#Viral", "#Trending", "#MustWatch", "#Facts", "#ViralShorts", "#PDX"],
    "tags": ["viral shorts", "trending", "must watch", "youtube shorts", "daily clips", "PDX"],
    "emoji": "🔥🎬",
    "fallback_title": "Wait Until You See This!",
    "topic_label": "High-Impact Moments & Viral Stories",
    "engagement_q": "💬 What was your immediate reaction to this? Let us know in the comments below!",
    "niche_line": "🎬 New high-impact Shorts uploaded daily!",
    "category": "Entertainment",
}


def detect_niche_profile(combined_text: str) -> Dict[str, Any]:
    text_lower = combined_text.lower()
    for key in ["gta6", "mystery_crime", "luxury", "gaming", "tech_ai", "business", "mindset"]:
        profile = NICHE_PROFILES[key]
        if any(kw in text_lower for kw in profile["keywords"]):
            return profile
    return GENERAL_VIRAL_PROFILE


def extract_video_entities(
    text: str,
    source_title: str = "",
    source_channel: str = "",
    source_description: str = ""
) -> List[Dict[str, Any]]:
    """
    Extracts prominent public figures, podcast hosts, guests, and games from
    transcript, title, channel name, and source description to power YouTube's
    Knowledge Graph and viewer interest indexing.
    """
    corpus = f"{source_title} {source_channel} {source_description} {text}".lower()
    found: List[Dict[str, Any]] = []
    seen_names = set()

    for item in KNOWN_ENTITIES:
        if any(alias in corpus for alias in item["aliases"]):
            if item["name"] not in seen_names:
                found.append(item)
                seen_names.add(item["name"])

    # Regex heuristic for titles like "X Interview" or "X on Y Podcast"
    if source_title:
        # Pattern: Guest Name on / with / feat
        patterns = [
            r'(?:interview with|featuring|feat\.?|with)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'#\d+\s*[-–—]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?:on|joins|discusses|explains|reveals)',
            r'\|\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\|',
        ]
        for pat in patterns:
            match = re.search(pat, source_title)
            if match:
                raw_name = match.group(1).strip()
                if raw_name not in seen_names and len(raw_name.split()) >= 2:
                    tag_clean = "#" + "".join(raw_name.split())
                    found.append({
                        "name": raw_name,
                        "aliases": [raw_name.lower()],
                        "hashtags": [tag_clean],
                        "tags": [raw_name, f"{raw_name} interview"],
                        "category": "Entertainment",
                        "role": "Featured Guest"
                    })
                    seen_names.add(raw_name)

    return found


def extract_key_takeaways(clip_text: str, max_points: int = 3) -> List[str]:
    """
    Extracts 2-3 impactful narrative takeaways or turning points from the clip transcript.
    """
    raw_sentences = [s.strip() for s in re.split(r'[.!?]+', (clip_text or "").strip()) if len(s.strip()) > 14]
    if not raw_sentences:
        return [
            "The counter-intuitive insight that separates success from common mistakes.",
            "Why conventional advice fails in high-stakes situations.",
            "The exact framework you can apply immediately."
        ]

    signpost_words = ["because", "the reason", "if you", "you must", "never", "always", "the problem is", "the truth is", "what happens is", "when you", "the key is", "in reality", "most people"]
    highlighted = []

    for s in raw_sentences:
        s_lower = s.lower()
        if any(sp in s_lower for sp in signpost_words):
            # Clean fillers
            cleaned = re.sub(r'^(and|so|but|yeah|like|you know|i mean)\s+', '', s, flags=re.IGNORECASE).strip()
            if len(cleaned) > 16:
                highlighted.append(cleaned[0].upper() + cleaned[1:])

    # Fallback to first few sentences if no signposts found
    if not highlighted:
        highlighted = [s[0].upper() + s[1:] for s in raw_sentences[:max_points]]

    # Ensure unique and truncated neatly
    unique_points = []
    for p in highlighted:
        if p not in unique_points:
            # End with period
            if not p.endswith((".", "!", "?")):
                p += "."
            unique_points.append(p[:140])
            if len(unique_points) >= max_points:
                break

    return unique_points


def clean_source_description_excerpt(source_desc: str, max_chars: int = 220) -> str:
    """
    Extracts a clean, informative excerpt from the original YouTube video description,
    removing URLs, affiliate links, and boilerplate disclosures.
    """
    if not source_desc:
        return ""
    lines = source_desc.splitlines()
    cleaned_lines = []
    for line in lines:
        line_clean = line.strip()
        # Skip URLs, social links, timestamps, sponsorship tags
        if not line_clean:
            continue
        if re.search(r'https?://|www\.|bit\.ly|t\.co|instagram|twitter|tiktok|patreon|sponsor|discord|merch', line_clean, re.I):
            continue
        if re.match(r'^\d{1,2}:\d{2}', line_clean):
            continue
        cleaned_lines.append(line_clean)
        if len(" ".join(cleaned_lines)) >= max_chars:
            break

    excerpt = " ".join(cleaned_lines).strip()
    return excerpt[:max_chars].strip()


def generate_shorts_metadata(
    clip_text: str,
    base_title: str = "",
    channel_name: str = "PDX",
    source_filename: str = "",
    source_title: str = "",
    source_channel: str = "",
    source_description: str = "",
    source_url: str = "",
    source_tags: str = ""
) -> Dict[str, Any]:
    """
    Generates intelligent, highly engaging YouTube Shorts metadata designed to maximize
    viewer retention and recommendation reach.
    
    1. Identifies WHO/WHAT is in the video (Person/Guest/Game/Topic).
    2. Writes a rich breakdown describing what happens in the video.
    3. Integrates context & credits from the original YouTube source.
    4. Curates targeted hashtags & tags to trigger YouTube's recommendation engine.
    """
    combined_context = f"{base_title} {source_filename} {source_title} {source_channel} {source_description} {clip_text} {source_tags}"
    profile = detect_niche_profile(combined_context)
    entities = extract_video_entities(clip_text, source_title, source_channel, source_description)

    # 1. High-CTR Hook Title (Max 60 chars for mobile discovery)
    title = (base_title or "").strip()
    primary_entity = entities[0]["name"] if entities else None

    if not title:
        if primary_entity:
            title = f"{primary_entity}: {profile['fallback_title']}"
        else:
            title = profile["fallback_title"]

    if not title.endswith("!") and not title.endswith("?"):
        title += "!"

    if len(title) <= 50 and "#shorts" not in title.lower():
        title = f"{title} #Shorts"

    # 2. Dynamic Hashtags & SEO Tags
    entity_hashtags = []
    entity_tags = []
    for ent in entities:
        for ht in ent.get("hashtags", []):
            if ht not in entity_hashtags:
                entity_hashtags.append(ht)
        for tg in ent.get("tags", []):
            if tg not in entity_tags:
                entity_tags.append(tg)

    # Channel and Niche hashtags
    niche_hashtags = list(profile["hashtags"])
    all_hashtags = ["#Shorts", "#YouTubeShorts"] + entity_hashtags[:4] + [h for h in niche_hashtags if h not in ["#Shorts", "#PDX"]] + [f"#{channel_name}"]
    # Deduplicate while preserving order
    seen_ht = set()
    dedup_hashtags = []
    for h in all_hashtags:
        h_clean = h.strip()
        if h_clean and h_clean.lower() not in seen_ht:
            seen_ht.add(h_clean.lower())
            dedup_hashtags.append(h_clean)

    hashtags_str = " ".join(dedup_hashtags[:12])

    seo_tags = list(dict.fromkeys(entity_tags + profile["tags"] + [channel_name, "viral shorts", "trending shorts"]))[:25]

    # 3. Descriptive Breakdown & Narrative Context
    sentences = [s.strip() for s in re.split(r'[.!?]+', (clip_text or "").strip()) if len(s.strip()) > 10]
    hook_quote = f'"{sentences[0]}"' if sentences else f'"{profile["fallback_title"]}"'
    takeaways = extract_key_takeaways(clip_text, max_points=3)

    # Entity / Featuring Line
    if entities:
        entity_names = [e["name"] for e in entities[:3]]
        if len(entity_names) == 1:
            feat_line = f"🎙️ FEATURING: {entity_names[0]}"
        elif len(entity_names) == 2:
            feat_line = f"🎙️ FEATURING: {entity_names[0]} & {entity_names[1]}"
        else:
            feat_line = f"🎙️ FEATURING: {', '.join(entity_names[:-1])} & {entity_names[-1]}"
    elif source_channel:
        feat_line = f"🎙️ FEATURING: {source_channel}"
    else:
        feat_line = f"🎯 TOPIC: {profile['topic_label']}"

    # YouTube Source Credits
    yt_context_block = ""
    if source_title:
        yt_context_block += f"📺 ORIGINAL VIDEO: {source_title}\n"
    if source_channel:
        yt_context_block += f"🎬 SOURCE CHANNEL: @{source_channel} (Full credit to creators)\n"

    # Context excerpt from original YouTube video if available
    desc_excerpt = clean_source_description_excerpt(source_description)
    context_note = f"\n📌 BACKGROUND CONTEXT:\n{desc_excerpt}\n" if (desc_excerpt and len(desc_excerpt) > 40) else ""

    # Build the full PDX High-Engagement Description
    description = f"""🔥 {hook_quote} {profile['emoji']}

{feat_line}
{yt_context_block.strip()}
{context_note}
📌 IN THIS SHORT:
In this high-impact moment, {primary_entity if primary_entity else 'the speaker'} breaks down critical insights on {profile['topic_label'].lower()}, revealing lessons that most people miss until it's too late.

💡 KEY TAKEAWAYS:
• {takeaways[0] if len(takeaways) > 0 else 'High-leverage insight distilled in under 60 seconds.'}
• {takeaways[1] if len(takeaways) > 1 else 'The hidden turning point you need to watch for.'}
• {takeaways[2] if len(takeaways) > 2 else 'Practical wisdom you can apply today.'}

{profile['engagement_q']}

👉 Subscribe to @{channel_name} for daily high-impact wisdom, 1080p clips & breakdowns!
{profile['niche_line']}

{hashtags_str}

---
Rendered in 1080p Full HD with ViralCut AI for {channel_name}.
{f'Source Link: {source_url}' if source_url else ''}
""".strip()

    return {
        "title": title[:100],
        "description": description,
        "hashtags": hashtags_str,
        "tags": seo_tags,
        "category": profile["category"],
        "entities_found": [e["name"] for e in entities],
        "primary_entity": primary_entity,
        "topic_label": profile["topic_label"]
    }
