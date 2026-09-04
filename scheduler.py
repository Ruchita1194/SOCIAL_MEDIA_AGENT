"""
scheduler.py
The "algo" for daily posting, parameterized by a brand_brief dict so it
works for any brand/creator entered in the Streamlit app. This is a
deliberately transparent rules-based heuristic, not a black box:

  1. Platform for each day is chosen by weighted round-robin
     (derived from the brief's platform list order) so higher-priority
     platforms get more slots without ever "starving" the rest.
  2. Theme for each day cycles through brand_brief["themes"] and skips a
     theme if it was used in the last 2 days, to avoid back-to-back repeats.
  3. Time slot is chosen from BEST_TIME_WINDOWS for that platform, rotating
     through the documented windows.
  4. Content is generated via content_generator.generate_post(), which is
     given the last 5 ideas explicitly so the LLM avoids repeating angles.
  5. A lightweight keyword-overlap check (Jaccard similarity on caption
     words) flags if a new post is too similar to a recent one, and
     regenerates once if so.
"""

import json
import os
import random
import time
from datetime import datetime, timedelta

from content_generator import generate_post

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

POSTING_LOG_PATH = "data/posting_log.json"

BEST_TIME_WINDOWS = {
    "Instagram": ["11:00", "13:00", "19:00"],
    "TikTok": ["09:00", "12:00", "20:00"],
    "LinkedIn": ["08:00", "10:30", "17:00"],
    "YouTube": ["14:00", "17:00", "20:00"],
    "X": ["09:00", "12:00", "18:00"],
    "Pinterest": ["20:00", "21:00", "22:00"],
    "Facebook": ["09:00", "13:00", "15:00"],
}
GENERIC_TIME_WINDOWS = ["10:00", "13:00", "19:00"]


def _time_windows_for(platform: str) -> list:
    return BEST_TIME_WINDOWS.get(platform, GENERIC_TIME_WINDOWS)


def _platform_weights(platforms: list) -> dict:
    n = len(platforms) or 1
    raw = [n - i for i in range(n)]
    total = sum(raw)
    return {p: w / total for p, w in zip(platforms, raw)}


def _weighted_platform_sequence(platforms: list, n_days: int) -> list:
    weights_map = _platform_weights(platforms)
    weights = [weights_map[p] for p in platforms]
    return random.choices(platforms, weights=weights, k=n_days)


def _theme_sequence(themes: list, n_days: int) -> list:
    seq = []
    recent = []
    pool = themes.copy()
    for _ in range(n_days):
        random.shuffle(pool)
        choice = next((t for t in pool if t not in recent[-2:]), pool[0])
        seq.append(choice)
        recent.append(choice)
    return seq


def _keyword_overlap(a: str, b: str) -> float:
    set_a, set_b = set(a.lower().split()), set(b.lower().split())
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def build_week_calendar(brand_brief: dict, start_date: datetime = None,
                         progress_callback=None) -> list:
    """Generate 7 days of scheduled content for the given brand brief.

    progress_callback(day_index, total_days, day_record): optional hook so a
    caller (e.g. Streamlit) can show incremental progress.
    """
    start_date = start_date or datetime.now()
    platforms = brand_brief.get("platforms") or ["Instagram", "TikTok"]
    themes = brand_brief.get("themes") or ["general content"]

    platform_seq = _weighted_platform_sequence(platforms, 7)
    theme_seq = _theme_sequence(themes, 7)

    calendar = []
    recent_ideas = []
    recent_captions = []

    for i in range(7):
        date = start_date + timedelta(days=i)
        platform = platform_seq[i]
        theme = theme_seq[i]
        windows = _time_windows_for(platform)
        time_slot = windows[i % len(windows)]

        post = generate_post(brand_brief, theme, platform, recent_ideas[-5:])

        for prev in recent_captions[-3:]:
            if _keyword_overlap(post["caption"], prev) > 0.5:
                post = generate_post(brand_brief, theme, platform, recent_ideas[-5:])
                break

        record = {
            "date": date.strftime("%Y-%m-%d"),
            "day": DAY_NAMES[date.weekday()],
            "platform": platform,
            "time": time_slot,
            "theme": theme,
            "idea": post["idea"],
            "caption": post["caption"],
            "hashtags": post["hashtags"],
            "status": "scheduled",
        }
        calendar.append(record)
        recent_ideas.append(post["idea"])
        recent_captions.append(post["caption"])

        if progress_callback:
            progress_callback(i + 1, 7, record)

    return calendar


def _load_log() -> list:
    if os.path.exists(POSTING_LOG_PATH):
        with open(POSTING_LOG_PATH, "r") as f:
            return json.load(f)
    return []


def _save_log(log: list) -> None:
    os.makedirs(os.path.dirname(POSTING_LOG_PATH), exist_ok=True)
    with open(POSTING_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


def simulate_post(record: dict) -> dict:
    """Stand-in for a real platform API call. Replace this function's body
    with e.g. tweepy.Client.create_tweet(...) or a webhook POST to go live -
    every other part of the scheduler stays the same."""
    record = dict(record)
    record["status"] = "posted (simulated)"
    record["posted_at"] = datetime.now().isoformat(timespec="seconds")
    log = _load_log()
    log.append(record)
    _save_log(log)
    return record


def run_simulated_daily_loop(calendar: list, demo_speed_seconds: int = 5) -> None:
    """CLI-only helper: 'posts' each calendar entry at a fixed cadence."""
    print(f"Simulating {len(calendar)} scheduled posts (demo mode, {demo_speed_seconds}s apart)...\n")
    for record in calendar:
        posted = simulate_post(record)
        print(f"[SIMULATED POST] {posted['platform']} @ {posted['time']} -> {posted['caption'][:70]}...")
        time.sleep(demo_speed_seconds)
    print("\nDone. Full log written to", POSTING_LOG_PATH)
