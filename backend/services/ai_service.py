import os
import json
import logging
from typing import Dict, Any, List, Optional
from backend.modules.viral_scoring import score_clip_candidate

logger = logging.getLogger(__name__)

class AIService:
    """
    Hybrid AI Content Analysis service:
    - Supports Cloud LLMs (Gemini / OpenAI API) when API keys are configured.
    - Gracefully falls back to the deterministic weighted rule-based viral scoring algorithm.
    """
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")

    def analyze_and_score_clip(self, text: str, has_visual: bool = False) -> Dict[str, Any]:
        """
        Analyze a transcript segment for viral potential with story arc and visual awareness.
        """
        # Base rule-based algorithmic score
        base_scores = score_clip_candidate(text, has_visual=has_visual)

        # Optional Cloud LLM refinement if API key exists
        if self.gemini_api_key:
            try:
                llm_result = self._call_gemini_analysis(text)
                if llm_result:
                    # Blend LLM and rule-based scores
                    return self._merge_scores(base_scores, llm_result)
            except Exception as e:
                logger.warning(f"Cloud LLM call skipped, falling back to rule engine: {e}")

        return base_scores

    def _call_gemini_analysis(self, text: str) -> Optional[Dict[str, Any]]:
        """Call Gemini API via REST if configured."""
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        prompt = f"""
        Analyze this video transcript excerpt for YouTube Shorts viral potential.
        Return ONLY valid JSON with keys:
        hook_score (0-100), emotional_score (0-100), information_score (0-100),
        storytelling_score (0-100), context_score (0-100), engagement_score (0-100),
        reason (short explanation), title (catchy YouTube Short title).

        Transcript:
        "{text}"
        """
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            data = res.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)
        return None

    def _merge_scores(self, base: Dict[str, Any], llm: Dict[str, Any]) -> Dict[str, Any]:
        """Blend rule-based score with LLM analysis (50/50 weighting)."""
        merged = {}
        for key in ["hook_score", "emotional_score", "information_score", "storytelling_score", "context_score", "engagement_score"]:
            llm_val = float(llm.get(key, base[key]))
            merged[key] = round((base[key] * 0.5) + (llm_val * 0.5), 1)

        from backend.modules.viral_scoring import WEIGHTS
        weighted = (
            (merged["hook_score"] * WEIGHTS["hook"]) +
            (merged["emotional_score"] * WEIGHTS["emotion"]) +
            (merged["information_score"] * WEIGHTS["information"]) +
            (merged["storytelling_score"] * WEIGHTS["storytelling"]) +
            (merged["context_score"] * WEIGHTS["context"]) +
            (merged["engagement_score"] * WEIGHTS["engagement"])
        )
        merged["viral_score"] = round(weighted, 1)
        merged["reason"] = llm.get("reason", base["reason"])
        merged["title"] = llm.get("title", base["title"])
        return merged

_ai_service_instance = None

def get_ai_service() -> AIService:
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance
