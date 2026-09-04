# Social Media Agent

An AI agent that takes a **brand brief** and produces a **7-day content calendar**
(ideas, captions, hashtags, platform, posting time), simulates the daily posting
of that calendar, and can draft short-form **video scripts + AI video-gen tool
prompts** for any idea.

> One-sentence spec: *this agent takes a brand brief and produces a scheduled,
> non-repetitive week of platform-native social posts, plus optional video
> scripts for turning any post into a short-form video.*

Built for the 24-hour AI Agent Challenge — Social Media Agent (Beginner track,
extended with a scheduling algo and a video-prompt helper).

---

## 1. Setup

```bash
git clone <your-repo-url>
cd social-media-agent
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and add a free API key from https://console.groq.com/keys:

```
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

## 2. Run the app (primary interface)

```bash
streamlit run app.py
```

This opens a browser UI where you:

1. **Describe your brand in plain English** in the sidebar — e.g. *"I'm a
   UGC creator, beauty is my niche"* — and click **Generate brand brief**.
   One Groq call turns that into a structured brief (voice, audience,
   themes, platforms), which you can then edit directly in the sidebar.
2. **💬 Ask the agent** — type a question like *"what should I post today?"*
   or *"give me an idea for a GRWM video"* and get back an idea, hook,
   caption, CTA, hashtags, and which platform(s) suit it best. Each question
   is one Groq call, made only when you click **Ask** — nothing runs on
   page load or on every keystroke.
3. **📅 7-day calendar** — click **Generate 7-day calendar** to build the full
   week (platform + theme + time slot per day, plus idea/caption/hashtags),
   with a progress bar since it's 7 sequential Groq calls. You can simulate
   "posting" any day from the UI, and download the calendar as JSON.
4. **🎬 Video script helper** — type any idea and get a hook/body/CTA script,
   on-screen text, a voiceover script, a paste-ready prompt for text-to-video
   tools (Runway/Pika/Kling/Sora-style), and a reference table of which AI
   video tool fits which job.

No terminal interaction needed after startup — everything runs through the
browser UI, and Groq is only called when you press a button.

### Optional: CLI version

A lighter-weight command-line version of the same core logic is also
included (uses the static default brief in `config.py` instead of the
free-text brief generator):

```bash
python main.py calendar     # generate a 7-day calendar (core deliverable)
python main.py simulate     # same, plus a simulated daily-posting loop
python main.py video "overwatering myths"   # video script + tool prompts
python main.py tools        # just print the video-gen tool reference table
```

---

## 3. Design choices & the "algo"

**Brand brief is derived from free text, not hardcoded.** `brand.py` sends a
one-line description (e.g. *"I'm a UGC creator, beauty is my niche"*) to
Groq and gets back a structured brief — this is what lets the same code work
for any creator/brand without touching a config file. The brief is editable
afterward in the sidebar in case the model's guess needs correcting.

**Why Groq + Llama 3.3 70B.** Free tier, fast inference (useful for iterating
quickly during a 24-hour build), and quality is sufficient for caption/idea
generation. Swappable — `groq_client.py` is the only file that knows which
provider is in use.

**The scheduling "algo" is a transparent rules-based heuristic, not ML:**
1. Platform per day: weighted random draw from the brief's platform list
   order, so higher-priority platforms get more slots without ever
   excluding a platform.
2. Theme per day: rotates through the brief's `themes` list, explicitly
   avoiding whatever theme was used in the last 2 days.
3. Time slot: pulled from `BEST_TIME_WINDOWS`, a small table of commonly
   cited platform engagement windows (documented industry benchmarks, not
   per-account analytics - a real deployment would replace this with the
   brand's actual Instagram/TikTok Insights data).
4. Repetition guard: the LLM is given the last 5 ideas and told to avoid
   their angle; additionally, a cheap Jaccard word-overlap check on captions
   (no embeddings API needed) regenerates a post once if it's too similar to
   one from the last 3 days.

**Why simulated posting, not real platform APIs.** Instagram/TikTok/LinkedIn
posting APIs require OAuth app review (often days to weeks for Instagram
Graph API business verification), and most have no simple free tier for
posting on someone else's behalf. `simulate_post()` in `scheduler.py` is the
single seam where a real API call would go - swap its body for
`tweepy.Client.create_tweet(...)` or a webhook POST and the rest of the
pipeline (scheduling, content generation, logging) needs no changes.

**Video generation is prompts/scripts only, not rendered video.** Actually
generating video (Runway/Pika/Kling/etc.) requires paid API credits and
render time incompatible with a 24-hour scope. Instead the agent produces
the script and a ready-to-paste generation prompt, and documents which tool
fits which job.

---

## 4. Tradeoffs & what I'd improve with more time

- **No real platform posting** - documented above; the honest tradeoff of
  the 24-hour window. Next step would be one real integration (e.g.
  Twitter/X API v2 free tier, or a Discord/Slack webhook) behind the
  existing `simulate_post()` seam.
- **Best-time-to-post table is generic, not personalized** - a real version
  would pull an account's actual Insights/Analytics API data.
- **Repetition guard is a simple word-overlap heuristic**, not semantic
  similarity - an embeddings-based check would catch paraphrased repeats
  that share no words.
- **No image/video generation pipeline**, by design - the video helper stops
  at scripts + prompts.
- **No persistence beyond flat JSON files** - fine for a demo; a real
  deployment would use a proper database and a real cron/task-queue
  scheduler instead of session-only state.

---

## 5. Sample output

See `sample_output/calendar.json` for a full generated 7-day calendar and
`sample_output/video_script_sample.md` for a generated video script package.
Using the app or `python main.py simulate` also produces
`data/posting_log.json`.

---

## 6. Video-Gen Tool Landscape (reference)

| Tool | Best for | Notes |
|---|---|---|
| Runway (Gen-3/Gen-4) | Cinematic text-to-video, image-to-video, camera control | Strong for stylized b-roll; paid credits per generation |
| Pika Labs | Fast, casual text-to-video for social clips | Good iteration speed; free tier available |
| Kling AI | Longer, higher-fidelity video generation | Strong motion coherence; credit-based pricing |
| Luma Dream Machine | Quick realistic video from text/image | Fast turnaround, good for concept previews |
| HeyGen | AI avatar / talking-head videos | Best for a consistent presenter without filming |
| ElevenLabs | AI voiceover generation | Pair with the `voiceover_script` field from the video helper |
| CapCut | Editing, captions, auto-subtitles, templates | Free, good for final assembly after clips are generated |

---

## 7. Project structure

```
social-media-agent/
├── app.py                    # Streamlit UI (primary interface)
├── brand.py                  # free-text description -> structured brand brief
├── daily_advisor.py          # answers ad-hoc "what should I post today" questions
├── config.py                 # static default brief, used by the CLI only
├── groq_client.py             # LLM provider wrapper (swap providers here only)
├── content_generator.py       # idea + caption + hashtag generation for the calendar
├── scheduler.py                # the scheduling algo + simulated daily posting
├── video_prompt_helper.py      # video script + tool-prompt generation
├── main.py                     # optional CLI entry point
├── data/posting_log.json       # simulated post history (created at runtime)
├── sample_output/              # generated calendar.json + video_script_sample.md
└── requirements.txt
```
