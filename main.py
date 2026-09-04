"""
main.py
CLI entry point for the Social Media Agent (the Streamlit app in app.py is
the primary interface - run with `streamlit run app.py`; this CLI is kept
as a lighter-weight way to reproduce the same core deliverables).

Usage:
    python main.py calendar          # generate & print a 7-day content calendar (saves JSON)
    python main.py simulate          # run the simulated daily-posting loop over that calendar
    python main.py video "<idea>"    # generate a video script + tool prompts for one idea
    python main.py tools             # print the AI video-gen tool landscape
"""

import json
import sys

from scheduler import build_week_calendar, run_simulated_daily_loop
from video_prompt_helper import generate_video_package, VIDEO_TOOL_LANDSCAPE
from config import BRAND_BRIEF


def print_tool_landscape():
    print("\nVideo-Gen Tool Landscape:")
    for t in VIDEO_TOOL_LANDSCAPE:
        print(f"- {t['tool']}: {t['best_for']} - {t['notes']}")


def cmd_calendar():
    print(f"Generating 7-day content calendar for {BRAND_BRIEF['brand_name']}...\n")
    calendar = build_week_calendar(BRAND_BRIEF)
    for day in calendar:
        print(f"{day['day']} {day['date']} | {day['platform']} @ {day['time']} | theme: {day['theme']}")
        print(f"  Idea: {day['idea']}")
        print(f"  Caption: {day['caption']}")
        print(f"  Hashtags: {' '.join(day['hashtags'])}\n")

    out_path = "sample_output/calendar.json"
    with open(out_path, "w") as f:
        json.dump(calendar, f, indent=2)
    print(f"Saved to {out_path}")
    return calendar


def cmd_simulate():
    calendar = cmd_calendar()
    print("\n--- Starting simulated daily posting loop ---\n")
    run_simulated_daily_loop(calendar, demo_speed_seconds=3)


def cmd_video(idea: str):
    print(f"Generating video package for idea: {idea}\n")
    package = generate_video_package(BRAND_BRIEF, idea)
    print(json.dumps(package, indent=2))
    print_tool_landscape()

    with open("sample_output/video_script_sample.md", "w") as f:
        f.write(f"# Video Script: {idea}\n\n")
        f.write(f"**Hook:** {package['hook']}\n\n")
        f.write("**Body:**\n")
        for beat in package["body"]:
            f.write(f"- {beat}\n")
        f.write(f"\n**CTA:** {package['cta']}\n\n")
        f.write(f"**Best platform(s):** {', '.join(package['best_platforms_for_this'])}\n\n")
        f.write(f"**Voiceover script:**\n{package['voiceover_script']}\n\n")
        f.write(f"**Video-gen prompt (Runway/Pika/Kling/Sora style):**\n{package['video_gen_prompt']}\n")
    print("\nSaved to sample_output/video_script_sample.md")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1]
    if command == "calendar":
        cmd_calendar()
    elif command == "simulate":
        cmd_simulate()
    elif command == "video":
        if len(sys.argv) < 3:
            print("Usage: python main.py video \"<idea text>\"")
            sys.exit(1)
        cmd_video(sys.argv[2])
    elif command == "tools":
        print_tool_landscape()
    else:
        print(__doc__)
