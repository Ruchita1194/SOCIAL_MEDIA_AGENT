"""
content_generator.py
Generates a content idea + caption + hashtags for a single (day, platform,
theme) slot, for whatever brand_brief dict is passed in.
"""

from groq_client import ask_json


def _system_prompt(brand_brief: dict) -> str:
    banned = ", ".join(brand_brief.get("banned_words", [])) or "none"
    return f"""You are a social media content strategist for the brand "{brand_brief['brand_name']}".

Brand voice: {brand_brief['voice']}
Target audience: {brand_brief['audience']}
Words you must never use: {banned}

Always respond with a single JSON object only, no extra text, matching this schema:
{{
  "idea": "one-sentence content concept",
  "caption": "ready-to-post caption in brand voice, 2-4 sentences",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"]
}}"""


def generate_post(brand_brief: dict, theme: str, platform: str, recent_ideas: list) -> dict:
    """Generate one piece of content for a given theme/platform.

    recent_ideas: short list of prior ideas (last ~5 days) passed in so the
    model actively avoids repeating angles, examples, or phrasing.
    """
    avoid_block = (
        "Avoid repeating these recent ideas or their angle:\n- " + "\n- ".join(recent_ideas)
        if recent_ideas else "No prior ideas to avoid yet."
    )

    user_prompt = f"""Create one {platform} post for the content theme: "{theme}".

{avoid_block}

Keep the caption native to {platform}'s style (e.g. punchier/shorter for TikTok,
more polished for LinkedIn, visual-first for Instagram)."""

    return ask_json(_system_prompt(brand_brief), user_prompt)
