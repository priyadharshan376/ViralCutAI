import re
from typing import Dict, Any, List, Optional

# Prominent Public Figures, Creators, Games, and Entities for Knowledge Graph SEO
KNOWN_ENTITIES: List[Dict[str, Any]] = [
    # Tech / Founders / Visionaries
    {
        "name": "Elon Musk",
        "aliases": ["elon musk", "elon", "musk", "spacex", "tesla", "neuralink", "starship", "xai"],
        "hashtags": ["#ElonMusk", "#Tesla", "#SpaceX"],
        "tags": ["Elon Musk", "Elon Musk interview", "Tesla", "SpaceX", "Elon Musk advice"],
        "category": "Science & Technology",
        "role": "Tech Visionary & Founder"
    },
    {
        "name": "Sam Altman",
        "aliases": ["sam altman", "altman", "openai", "chatgpt"],
        "hashtags": ["#SamAltman", "#OpenAI", "#ChatGPT"],
        "tags": ["Sam Altman", "OpenAI", "ChatGPT", "Sam Altman interview"],
        "category": "Science & Technology",
        "role": "CEO of OpenAI"
    },
    {
        "name": "Jensen Huang",
        "aliases": ["jensen huang", "jensen", "nvidia"],
        "hashtags": ["#JensenHuang", "#Nvidia"],
        "tags": ["Jensen Huang", "Nvidia", "Nvidia CEO"],
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
        "hashtags": ["#GTA6", "#GTAVI", "#RockstarGames", "#ViceCity", "#GTA6Gameplay"],
        "tags": ["GTA 6", "GTA VI", "GTA 6 gameplay", "GTA 6 trailer", "Vice City", "Rockstar Games", "Jason and Lucia"],
        "category": "Gaming",
        "role": "Rockstar Games Open World"
    },
    {
        "name": "Rockstar Games",
        "aliases": ["rockstar games", "rockstar", "rdr2", "red dead"],
        "hashtags": ["#RockstarGames", "#GTA", "#GamingDetails"],
        "tags": ["Rockstar Games", "GTA", "Red Dead Redemption", "gaming news"],
        "category": "Gaming",
        "role": "Video Game Developer & Publisher"
    },

    # Creators & Streamers
    {
        "name": "MrBeast",
        "aliases": ["mrbeast", "mr beast", "jimmy donaldson"],
        "hashtags": ["#MrBeast", "#ViralMoments"],
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

# Topic & Keyword Rules to extract tags describing WHAT IS IN THE VIDEO
TOPIC_TAG_RULES: List[tuple] = [
    # Mindset / Performance / Habits
    (["morning routine", "wake up early", "morning habit", "5 am"], ["#MorningRoutine", "#DailyHabits"]),
    (["dopamine", "addiction", "reset", "detox"], ["#DopamineDetox", "#FocusHacks"]),
    (["sleep", "circadian", "melatonin", "rest", "recovery"], ["#SleepOptimization", "#DeepSleep"]),
    (["discipline", "self discipline", "lazy", "procrastination"], ["#SelfDiscipline", "#Discipline"]),
    (["mental toughness", "hard things", "suffer", "pain", "push through", "endure"], ["#MentalToughness", "#StayHard"]),
    (["focus", "attention", "distraction", "deep work", "concentrate"], ["#DeepWork", "#FocusHacks"]),
    (["habit", "atomic habit", "routine", "behavior", "consistency"], ["#HabitBuilding", "#SuccessHabits"]),
    (["body language", "manipulation", "dark psychology", "eye contact"], ["#BodyLanguage", "#DarkPsychology"]),
    (["stoic", "stoicism", "marcus aurelius", "seneca"], ["#Stoicism", "#StoicWisdom"]),
    (["confidence", "self esteem", "charisma"], ["#Charisma", "#ConfidenceBoost"]),

    # Wealth / Business / Money
    (["sales", "closing", "cold call", "negotiation"], ["#SalesTips", "#NegotiationSkills"]),
    (["investing", "stocks", "real estate", "passive income"], ["#Investing", "#WealthBuilding"]),
    (["money", "cash flow", "net worth", "millionaire", "billionaire", "wealth"], ["#MoneyMindset", "#FinancialFreedom"]),
    (["startup", "business", "founder", "entrepreneur", "scale"], ["#Entrepreneurship", "#BusinessGrowth"]),
    (["pricing", "high ticket", "offer", "acquisition", "marketing"], ["#BusinessStrategy", "#HighTicket"]),

    # Gaming & GTA 6
    (["water physics", "physics", "engine"], ["#WaterPhysics", "#GameEngine"]),
    (["crowd density", "graphics", "npc", "pedestrian"], ["#CrowdDensity", "#NextGenGraphics"]),
    (["open world", "map", "vice city", "leonida"], ["#ViceCityMap", "#OpenWorldGames"]),
    (["gameplay", "walkthrough", "secrets", "easter egg"], ["#GameplayHighlights", "#GamingSecrets"]),

    # Luxury & Lifestyle
    (["supercar", "bugatti", "ferrari", "lamborghini", "hypercar"], ["#Supercars", "#ExoticCars"]),
    (["mansion", "penthouse", "villa", "real estate"], ["#LuxuryMansion", "#MegaMansion"]),
    (["private jet", "yacht", "rolex", "luxury"], ["#LuxuryLifestyle", "#BillionaireLife"]),

    # Mystery & Crime
    (["unsolved", "mystery", "fbi", "cold case", "crime"], ["#UnsolvedMysteries", "#ColdCase"]),
    (["detective", "investigation", "suspect", "disappeared", "murder"], ["#CrimeDocumentary", "#MysteryStories"]),

    # Science & Tech (specific to content)
    (["space", "rocket", "mars", "starship", "spacex", "orbit"], ["#SpaceX", "#SpaceExploration", "#RocketScience"]),
    (["electric car", "battery", "ev", "cybertruck", "tesla"], ["#Tesla", "#ElectricVehicles"]),
    (["coding", "software", "developer", "algorithm"], ["#SoftwareEngineering", "#Coding"]),
    (["chip", "semiconductor", "gpu", "hardware"], ["#Hardware", "#NvidiaGPU"]),
    # Artificial Intelligence ONLY if explicitly mentioned in the text
    (["artificial intelligence", "chatgpt", "openai", "agi", "machine learning", "large language model"], ["#ArtificialIntelligence", "#ChatGPT", "#OpenAI"])
]

NICHE_PROFILES: Dict[str, Dict[str, Any]] = {
    "gta6": {
        "keywords": ["gta 6", "gta6", "gta vi", "vice city", "rockstar", "jason", "lucia", "grand theft auto"],
        "hashtags": ["#Shorts", "#GTA6", "#GTAVI", "#RockstarGames", "#ViceCity", "#Gameplay", "#ViralShorts", "#PDX"],
        "tags": ["GTA 6", "GTA VI", "GTA 6 gameplay", "GTA 6 trailer", "Rockstar Games", "Vice City", "gaming shorts", "viral gaming", "PS5", "open world", "PDX"],
        "emoji": "🎮🔥",
        "fallback_title": "Insane GTA 6 Detail You Missed!",
        "topic_label": "Grand Theft Auto VI Breakdown & Secrets",
        "engagement_q": "💬 What feature or location are you most hyped for in GTA 6? Drop your thoughts below!",
        "niche_line": "🎮 Daily GTA 6 leaks, gameplay highlights, and gaming breakdowns.",
        "category": "Gaming",
    },
    "gaming": {
        "keywords": ["gameplay", "gaming", "ps5", "xbox", "pc gaming", "fps", "clutch", "boss", "walkthrough", "mod", "mods", "gamer", "esports", "minecraft", "fortnite", "valorant", "call of duty"],
        "hashtags": ["#Shorts", "#Gaming", "#Gameplay", "#Gamer", "#ViralGaming", "#ViralShorts", "#PDX"],
        "tags": ["gaming", "gameplay", "viral gaming", "insane gameplay", "funny gaming moments", "gamer", "PDX", "youtube shorts"],
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
    "tech": {
        "keywords": ["tech", "technology", "hardware", "software", "chips", "breakthrough", "coding", "future", "algorithm", "nvidia", "apple", "engineering", "gadgets"],
        "hashtags": ["#Shorts", "#Tech", "#FutureTech", "#TechNews", "#Innovation", "#ViralShorts", "#PDX"],
        "tags": ["tech", "technology", "tech news", "future technology", "coding", "innovation", "PDX"],
        "emoji": "⚡💻",
        "fallback_title": "This Tech Breakthrough Changes Everything!",
        "topic_label": "Technology & Modern Innovation",
        "engagement_q": "💬 What do you think is the most exciting technology being built right now? Share your perspective!",
        "niche_line": "⚡ Daily tech breakthroughs, modern innovation, and future trends.",
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
    for key in ["gta6", "mystery_crime", "luxury", "gaming", "tech", "business", "mindset"]:
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


def extract_content_tags(
    clip_text: str,
    source_title: str = "",
    entities: Optional[List[Dict[str, Any]]] = None
) -> List[str]:
    """
    Extracts targeted tags describing WHAT IS IN THE VIDEO based on actual topics,
    concepts, actions, and spoken subjects.
    """
    corpus = f"{source_title} {clip_text}".lower()
    tags_found: List[str] = []

    # 1. Check topic rules
    for keywords, rule_tags in TOPIC_TAG_RULES:
        if any(kw in corpus for kw in keywords):
            for t in rule_tags:
                if t not in tags_found:
                    tags_found.append(t)

    # 2. Add entity hashtags
    if entities:
        for ent in entities:
            for ht in ent.get("hashtags", []):
                if ht not in tags_found:
                    tags_found.append(ht)

    return tags_found


def extract_key_takeaways(clip_text: str, max_points: int = 3) -> List[str]:
    """
    Extracts 2-3 impactful narrative takeaways or turning points from the clip transcript.
    """
    raw_sentences = [s.strip() for s in re.split(r'[.!?]+', (clip_text or "").strip()) if len(s.strip()) > 14]
    if not raw_sentences:
        return [
            "The counter-intuitive insight that separates success from common mistakes.",
            "Why conventional thinking fails in high-stakes situations.",
            "The exact framework you can apply immediately."
        ]

    signpost_words = ["because", "the reason", "if you", "you must", "never", "always", "the problem is", "the truth is", "what happens is", "when you", "the key is", "in reality", "most people", "you have to"]
    highlighted = []

    for s in raw_sentences:
        s_lower = s.lower()
        if any(sp in s_lower for sp in signpost_words):
            cleaned = re.sub(r'^(and|so|but|yeah|like|you know|i mean)\s+', '', s, flags=re.IGNORECASE).strip()
            if len(cleaned) > 16:
                highlighted.append(cleaned[0].upper() + cleaned[1:])

    if not highlighted:
        highlighted = [s[0].upper() + s[1:] for s in raw_sentences[:max_points]]

    unique_points = []
    for p in highlighted:
        if p not in unique_points:
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
        if not line_clean:
            continue
        # Skip URLs, social links, timestamps, sponsorship tags
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
    Generates intelligent, highly engaging YouTube Shorts metadata:
    1. NEVER adds #shorts or #short to the title (clean, punchy hook titles).
    2. Identifies WHO/WHAT is in the video (Person/Guest/Game/Topic).
    3. Adds targeted tags describing WHAT IS IN THE VIDEO.
    4. NO software names (no ViralCut, no ShortCut) anywhere.
    5. NO external source links (no Source Link URLs).
    6. NO forced AI tags or AI mentions unless topic is explicitly Artificial Intelligence.
    """
    combined_context = f"{base_title} {source_filename} {source_title} {source_channel} {source_description} {clip_text} {source_tags}"
    profile = detect_niche_profile(combined_context)
    entities = extract_video_entities(clip_text, source_title, source_channel, source_description)

    # 1. Clean Title: Strictly REMOVE any #shorts / #short tag. Keep it clean and hook-driven!
    raw_title = (base_title or "").strip()
    # Strip any #shorts, #short, or #SHORTS tag
    clean_title = re.sub(r'#shorts?\b', '', raw_title, flags=re.IGNORECASE).strip()
    clean_title = re.sub(r'\s{2,}', ' ', clean_title).strip()

    primary_entity = entities[0]["name"] if entities else None

    if not clean_title:
        if primary_entity:
            clean_title = f"{primary_entity}: {profile['fallback_title']}"
        else:
            clean_title = profile["fallback_title"]

    clean_title = re.sub(r'#shorts?\b', '', clean_title, flags=re.IGNORECASE).strip()
    clean_title = re.sub(r'\s{2,}', ' ', clean_title).strip()

    if not clean_title.endswith("!") and not clean_title.endswith("?"):
        clean_title += "!"

    # 2. Tags describing WHAT IS IN THE VIDEO
    content_tags = extract_content_tags(clip_text, source_title, entities)

    # Combine with core discovery tags (without forcing #AI)
    niche_hashtags = [h for h in profile["hashtags"] if h.lower() not in ["#shorts", f"#{channel_name.lower()}"]]
    
    # Do NOT include #AI or #ArtificialIntelligence unless explicitly mentioned in clip/title
    has_explicit_ai = any(w in combined_context.lower() for w in ["artificial intelligence", "chatgpt", "openai", "machine learning", "deep learning"])
    if not has_explicit_ai:
        content_tags = [t for t in content_tags if t.lower() not in ["#ai", "#artificialintelligence", "#futuretech"]]
        niche_hashtags = [t for t in niche_hashtags if t.lower() not in ["#ai", "#artificialintelligence"]]

    all_hashtags = ["#Shorts", "#YouTubeShorts"] + content_tags + niche_hashtags + [f"#{channel_name}"]

    # Deduplicate while preserving order
    seen_ht = set()
    dedup_hashtags = []
    for h in all_hashtags:
        h_clean = h.strip()
        if h_clean and h_clean.lower() not in seen_ht:
            seen_ht.add(h_clean.lower())
            dedup_hashtags.append(h_clean)

    hashtags_str = " ".join(dedup_hashtags[:12])

    seo_tags = list(dict.fromkeys(
        [t.strip("#") for t in content_tags] +
        profile["tags"] +
        [channel_name, "viral shorts", "trending shorts"]
    ))[:25]
    if not has_explicit_ai:
        seo_tags = [t for t in seo_tags if t.lower() not in ["ai", "artificial intelligence"]]

    # 3. Descriptive Breakdown & Narrative Context
    sentences = [s.strip() for s in re.split(r'[.!?]+', (clip_text or "").strip()) if len(s.strip()) > 10]
    hook_quote = f'"{sentences[0]}"' if sentences else f'"{clean_title}"'
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

    # YouTube Source Credits (Channel and Video Title only -- NO external link URL)
    yt_context_block = ""
    if source_title:
        yt_context_block += f"📺 ORIGINAL VIDEO: {source_title}\n"
    if source_channel:
        yt_context_block += f"🎬 SOURCE CHANNEL: @{source_channel} (Credit to creators)\n"

    # Context excerpt from original YouTube video if available
    desc_excerpt = clean_source_description_excerpt(source_description)
    context_note = f"\n📌 BACKGROUND CONTEXT:\n{desc_excerpt}\n" if (desc_excerpt and len(desc_excerpt) > 40) else ""

    # Build the full PDX High-Engagement Description (NO software name, NO source link, NO forced AI)
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
""".strip()

    return {
        "title": clean_title[:95],
        "description": description,
        "hashtags": hashtags_str,
        "tags": seo_tags,
        "category": profile["category"],
        "entities_found": [e["name"] for e in entities],
        "content_tags": content_tags,
        "primary_entity": primary_entity,
        "topic_label": profile["topic_label"]
    }
