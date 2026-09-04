"""
video_prompt_helper.py
Given a content idea, drafts a short video script (hook/body/CTA) and
formats generation prompts for common AI video tools. This does NOT call
any video-gen API - it produces the text you'd paste into those tools.
"""

from groq_client import ask_json


def _system_prompt(brand_brief: dict) -> str:
    return f"""You are a short-form video scriptwriter for the brand "{brand_brief['brand_name']}".
Brand voice: {brand_brief['voice']}
Audience: {brand_brief['audience']}

Respond with a single JSON object only, matching:
{{
  "hook": "first 2-3 seconds, must stop the scroll",
  "body": ["3-5 short beats as an array of strings"],
  "cta": "closing call to action line",
  "on_screen_text": ["short caption overlays, one per beat"],
  "video_gen_prompt": "a single descriptive prompt suitable for text-to-video tools (Runway/Pika/Kling/Sora-style), describing visuals, camera movement, pacing, and mood",
  "voiceover_script": "full spoken narration if a voiceover were used",
  "best_platforms_for_this": ["1-2 platforms this specific video idea suits best, with a short reason folded into the string, e.g. 'TikTok - short punchy hook works best here'"]
}}"""


def generate_video_package(brand_brief: dict, idea: str, platform: str = "TikTok") -> dict:
    user_prompt = f'Draft a {platform} video package for this idea: "{idea}"'
    return ask_json(_system_prompt(brand_brief), user_prompt)


VIDEO_TOOL_LANDSCAPE = [
    {
        "tool": "Runway (Gen-3/Gen-4)",
        "best_for": "Cinematic text-to-video, image-to-video, camera control",
        "notes": "Strong for stylized b-roll; paid credits per generation.",
    },
    {
        "tool": "Pika Labs",
        "best_for": "Fast, casual text-to-video for social clips",
        "notes": "Good iteration speed; free tier available.",
    },
    {
        "tool": "Kling AI",
        "best_for": "Longer, higher-fidelity video generation",
        "notes": "Strong motion coherence; credit-based pricing.",
    },
    {
        "tool": "Luma Dream Machine",
        "best_for": "Quick realistic video from text/image",
        "notes": "Fast turnaround, good for concept previews.",
    },
    {
        "tool": "HeyGen",
        "best_for": "AI avatar / talking-head videos",
        "notes": "Best when a brand wants a consistent presenter without filming.",
    },
    {
        "tool": "ElevenLabs",
        "best_for": "AI voiceover generation",
        "notes": "Pair with the voiceover_script output above.",
    },
    {
        "tool": "CapCut",
        "best_for": "Editing, captions, auto-subtitles, templates",
        "notes": "Free, good for final assembly step after clips are generated.",
    },
]
