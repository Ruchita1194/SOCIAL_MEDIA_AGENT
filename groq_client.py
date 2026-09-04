"""
groq_client.py
Thin wrapper around the Groq chat completions API. Keeping this isolated
means every other module just calls `ask()` and doesn't care which LLM
provider is behind it — swap providers by editing only this file.
"""

import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


def ask(system_prompt: str, user_prompt: str, json_mode: bool = False, temperature: float = 0.8) -> str:
    """Send one prompt to Groq and return the text response."""
    kwargs = dict(
        model=_MODEL,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = _client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def ask_json(system_prompt: str, user_prompt: str, temperature: float = 0.8) -> dict:
    """Same as ask(), but parses the result as JSON with fence-stripping."""
    raw = ask(system_prompt, user_prompt, json_mode=True, temperature=temperature)
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)
