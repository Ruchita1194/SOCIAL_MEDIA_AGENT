"""
daily_advisor.py
Answers a single ad-hoc question like "what should I post today" (or any
free-text question) with a structured recommendation: idea, hook, caption,
CTA, hashtags, and which platform(s) to post it on.
"""

from datetime import datetime

from groq_client import ask_json

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _system_prompt(brand_brief: dict) -> str:
    banned = ", ".join(brand_brief.get("banned_words", [])) or "none"
    platforms = ", ".join(brand_brief.get("platforms", [])) or "Instagram, TikTok"
    themes = ", ".join(brand_brief.get("themes", [])) or "general content"
    return f"""You are a social media strategist for "{brand_brief['brand_name']}".

Brand voice: {brand_brief['voice']}
Audience: {brand_brief['audience']}
Content themes to draw from: {themes}
Platforms this brand uses: {platforms}
Words to never use: {banned}

You answer one question at a time from the creator (e.g. "what should I post
today?", "give me an idea for a get-ready-with-me video", "what's a good hook
for a product review?"). Always ground your answer in the brand voice,
audience, and themes above.

Respond with a single JSON object only, matching this schema:
{{
  "idea": "one-sentence content concept answering their question",
  "hook": "a scroll-stopping opening line/visual for the first 2-3 seconds",
  "caption": "ready-to-post caption in brand voice, 2-4 sentences",
  "cta": "a specific call to action line",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
  "best_platforms": ["1-2 platforms best suited to this specific idea, each as a short string with a brief reason, e.g. 'TikTok - trend-driven format fits the fast hook'"],
  "reasoning": "1-2 sentences on why this idea fits their brand/audience right now"
}}"""


def ask_daily_question(brand_brief: dict, question: str, recent_ideas: list = None) -> dict:
    """Answer one free-text question with a structured content recommendation."""
    recent_ideas = recent_ideas or []
    today = DAY_NAMES[datetime.now().weekday()]

    avoid_block = (
        "Avoid repeating these recent ideas:\n- " + "\n- ".join(recent_ideas)
        if recent_ideas else ""
    )

    user_prompt = f"""Today is {today}. The creator asks: "{question}"

{avoid_block}

Give one concrete, ready-to-use recommendation - not a list of options."""

    return ask_json(_system_prompt(brand_brief), user_prompt, temperature=0.8)
