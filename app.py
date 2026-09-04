"""
app.py
Streamlit UI for the Social Media Agent.

Run with:
    streamlit run app.py

Three things it does:
  1. Turns a free-text description ("I'm a UGC creator, beauty is my niche")
     into a structured brand brief (one Groq call, only on button click).
  2. Chat-style "what should I post today?" advisor - answers any single
     question with idea/hook/caption/CTA/hashtags/best platforms.
  3. Full 7-day content calendar generator, reusing the same scheduling
     algo as the CLI version.

Groq is only called when a button is pressed - nothing runs on page load
or on every keystroke.
"""

import streamlit as st

from brand import derive_brand_brief, DEFAULT_BRIEF
from daily_advisor import ask_daily_question
from scheduler import build_week_calendar, simulate_post
from video_prompt_helper import generate_video_package, VIDEO_TOOL_LANDSCAPE

st.set_page_config(page_title="Social Media Agent", page_icon="🪄", layout="wide")

# ---------------------------------------------------------------------------
# Session state setup
# ---------------------------------------------------------------------------
if "brand_brief" not in st.session_state:
    st.session_state.brand_brief = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of dicts: {question, result}
if "calendar" not in st.session_state:
    st.session_state.calendar = None

st.title("🪄 Social Media Agent")
st.caption("Brand brief → daily ideas, captions & CTAs → a 7-day posting calendar. Powered by Groq.")

# ---------------------------------------------------------------------------
# Step 1: Brand brief setup (sidebar)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("1. Your brand")
    st.write("Describe yourself/your brand in a sentence or two.")
    description = st.text_area(
        "e.g. \"I'm a UGC creator, beauty is my niche\"",
        placeholder="I'm a UGC creator, beauty is my niche",
        height=80,
        key="brand_description",
    )

    if st.button("Generate brand brief", type="primary", use_container_width=True):
        if description.strip():
            with st.spinner("Thinking about your brand..."):
                st.session_state.brand_brief = derive_brand_brief(description)
                st.session_state.chat_history = []
                st.session_state.calendar = None
        else:
            st.warning("Type a short description first.")

    st.divider()
    st.caption("Or skip this and use a generic default brief:")
    if st.button("Use default brief", use_container_width=True):
        st.session_state.brand_brief = dict(DEFAULT_BRIEF)
        st.session_state.chat_history = []
        st.session_state.calendar = None

    if st.session_state.brand_brief:
        st.divider()
        st.subheader("Current brief")
        brief = st.session_state.brand_brief
        brief["brand_name"] = st.text_input("Brand name", brief.get("brand_name", ""))
        brief["voice"] = st.text_input("Voice", brief.get("voice", ""))
        brief["audience"] = st.text_area("Audience", brief.get("audience", ""), height=60)
        themes_text = st.text_area(
            "Themes (one per line)",
            "\n".join(brief.get("themes", [])),
            height=110,
        )
        brief["themes"] = [t.strip() for t in themes_text.split("\n") if t.strip()]
        platforms_text = st.text_input("Platforms (comma separated)", ", ".join(brief.get("platforms", [])))
        brief["platforms"] = [p.strip() for p in platforms_text.split(",") if p.strip()]
        st.session_state.brand_brief = brief

if not st.session_state.brand_brief:
    st.info("👈 Start by describing your brand in the sidebar, then click **Generate brand brief**.")
    st.stop()

brand_brief = st.session_state.brand_brief

# ---------------------------------------------------------------------------
# Tabs: Ask the agent / 7-day calendar / video helper
# ---------------------------------------------------------------------------
tab_ask, tab_calendar, tab_video = st.tabs(
    ["💬 Ask the agent", "📅 7-day calendar", "🎬 Video script helper"]
)

# --- Tab 1: Ask the agent -------------------------------------------------
with tab_ask:
    st.subheader(f"Ask anything about what to post — for {brand_brief['brand_name']}")
    st.caption('Try: "what should I post today?" or "give me an idea for a get-ready-with-me video"')

    question = st.text_input("Your question", placeholder="What should I post today?", key="question_input")
    ask_clicked = st.button("Ask", type="primary")

    if ask_clicked:
        if question.strip():
            recent = [h["result"]["idea"] for h in st.session_state.chat_history[-5:]]
            with st.spinner("Coming up with something..."):
                result = ask_daily_question(brand_brief, question, recent_ideas=recent)
            st.session_state.chat_history.append({"question": question, "result": result})
        else:
            st.warning("Type a question first.")

    for turn in reversed(st.session_state.chat_history):
        q, r = turn["question"], turn["result"]
        with st.chat_message("user"):
            st.write(q)
        with st.chat_message("assistant"):
            st.markdown(f"**💡 Idea:** {r['idea']}")
            st.markdown(f"**🪝 Hook:** {r['hook']}")
            st.markdown(f"**✍️ Caption:** {r['caption']}")
            st.markdown(f"**📣 CTA:** {r['cta']}")
            st.markdown(f"**🏷️ Hashtags:** {' '.join(r['hashtags'])}")
            st.markdown(f"**📱 Best platform(s):** {', '.join(r['best_platforms'])}")
            st.caption(r.get("reasoning", ""))

# --- Tab 2: 7-day calendar -------------------------------------------------
with tab_calendar:
    st.subheader("Generate a 7-day content calendar")
    st.caption("Picks platform, theme, and time slot per day, then writes idea/caption/hashtags for each.")

    if st.button("Generate 7-day calendar", type="primary"):
        progress_bar = st.progress(0, text="Starting...")

        def _on_progress(i, total, record):
            progress_bar.progress(i / total, text=f"Day {i}/{total}: {record['day']} — {record['platform']}")

        with st.spinner("Building your week..."):
            st.session_state.calendar = build_week_calendar(brand_brief, progress_callback=_on_progress)
        progress_bar.empty()

    if st.session_state.calendar:
        for day in st.session_state.calendar:
            with st.expander(f"{day['day']} {day['date']} — {day['platform']} @ {day['time']} — {day['theme']}"):
                st.markdown(f"**Idea:** {day['idea']}")
                st.markdown(f"**Caption:** {day['caption']}")
                st.markdown(f"**Hashtags:** {' '.join(day['hashtags'])}")
                st.markdown(f"**Status:** {day['status']}")
                if st.button(f"Simulate posting this ({day['date']})", key=f"post_{day['date']}"):
                    posted = simulate_post(day)
                    st.success(f"Posted (simulated) at {posted['posted_at']}")

        st.download_button(
            "Download calendar as JSON",
            data=__import__("json").dumps(st.session_state.calendar, indent=2),
            file_name="calendar.json",
            mime="application/json",
        )

# --- Tab 3: Video script helper -------------------------------------------
with tab_video:
    st.subheader("Turn any idea into a video script")
    idea_input = st.text_input("Content idea", placeholder="e.g. overwatering myths / dupe comparison / GRWM")
    platform_choice = st.selectbox("Platform", brand_brief.get("platforms", ["TikTok"]) + ["TikTok", "Instagram", "YouTube"], index=0)

    if st.button("Draft video script", type="primary"):
        if idea_input.strip():
            with st.spinner("Writing the script..."):
                package = generate_video_package(brand_brief, idea_input, platform_choice)
            st.markdown(f"**🪝 Hook:** {package['hook']}")
            st.markdown("**Body beats:**")
            for beat in package["body"]:
                st.markdown(f"- {beat}")
            st.markdown(f"**📣 CTA:** {package['cta']}")
            st.markdown(f"**On-screen text:** {', '.join(package['on_screen_text'])}")
            st.markdown(f"**Best platform(s) for this idea:** {', '.join(package['best_platforms_for_this'])}")
            with st.expander("Voiceover script"):
                st.write(package["voiceover_script"])
            with st.expander("Video-gen prompt (paste into Runway/Pika/Kling/Sora-style tools)"):
                st.code(package["video_gen_prompt"], language=None)
        else:
            st.warning("Type an idea first.")

    st.divider()
    st.caption("Reference: which AI video-gen tool to use for what")
    st.table(VIDEO_TOOL_LANDSCAPE)
