"""
brand.py
Turns a free-text description (e.g. "I'm a UGC creator, beauty is my niche")
into the structured brand brief the rest of the agent runs on: voice,
audience, themes, platforms. This is what lets the Streamlit app work for
ANY brand/creator without editing code.
"""

from groq_client import ask_json

DEFAULT_BRIEF = {
    "brand_name": "My Brand",
    "voice": "warm, approachable, a little witty",
    "audience": "general social media audience",
    "themes": [
        "product spotlight",
        "behind-the-scenes",
        "educational tips",
        "community engagement",
        "trending/topical",
    ],
    "platforms": ["Instagram", "TikTok"],
    "posts_per_day": 1,
    "banned_words": [],
}


def _system_prompt() -> str:
    return """You are a brand strategist. Given a short free-text description of a
creator, brand, or business, infer a structured content brand brief.

Respond with a single JSON object only, matching this schema:
{
  "brand_name": "a short name/handle for the brand (invent something plausible if none given)",
  "voice": "3-6 words describing tone (e.g. 'playful, confident, a bit cheeky')",
  "audience": "one sentence describing who follows/watches this content",
  "themes": ["4-6 recurring content pillars/themes specific to this niche"],
  "platforms": ["2-3 platforms most relevant to this niche, ordered by priority"],
  "banned_words": ["1-3 words/phrases that would sound off-brand, or empty list"]
}

Be specific to the niche described. A beauty UGC creator's themes should be
about beauty UGC (get-ready-with-me, product reviews, dupes, transformations),
not generic corporate themes."""


def derive_brand_brief(description: str) -> dict:
    """Call Groq once to turn free text into a structured brand brief."""
    if not description or not description.strip():
        return DEFAULT_BRIEF

    user_prompt = f'Creator/brand description: "{description.strip()}"'
    brief = ask_json(_system_prompt(), user_prompt, temperature=0.6)

    # Defensive defaults in case the model omits a field
    for key, fallback in DEFAULT_BRIEF.items():
        brief.setdefault(key, fallback)
    return brief
