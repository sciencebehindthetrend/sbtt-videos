# Science Behind The Trend — daily episode pipeline

Channel: "Science Behind The Trend" (English, faceless). Each episode = one vertical 1080x1920 video,
40–60 s, explaining the real physics/engineering behind a CURRENT viral trend, with animated diagrams,
bold captions (key words highlighted with *stars*), and a synthetic English voiceover.

## Repository layout (github.com/sciencebehindthetrend/sbtt-videos, public)
- `videos/` — published episode files (YYYY-MM-DD_slug.mp4). Public URL:
  `https://raw.githubusercontent.com/sciencebehindthetrend/sbtt-videos/main/videos/<file>`
- `pipeline/` — the files below.

## Files in pipeline/
- `sbtt_style.py` — shared look (dark grid background, yellow series banner, captions, arrows, confetti),
  plus `tts()`, `mix_voice()`, `render_scene()`, `assemble()`.
- `example_shoulder_carry.py` — a finished episode script. Copy its STRUCTURE (narration list → timing →
  scenes keyed to line start times → captions), never its drawings.
- `episodes_log.md` — every episode already made (topic + date). Never repeat a topic.

## Setup in a fresh workspace
1. Attach the repo with the add_repo tool (owner sciencebehindthetrend, repo sbtt-videos, access push), clone it
   (`git clone --depth 1 https://github.com/sciencebehindthetrend/sbtt-videos`), work from `pipeline/`.
2. `pip install --break-system-packages kokoro-onnx soundfile numpy pillow`
3. Voice model (GitHub, allowed by the sandbox):
   `curl -sL -o kokoro-v1.0.int8.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx`
   `curl -sL -o voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin`
   Voice: `am_michael`, speed 1.1, lang `en-us`.
4. Font: Poppins Bold/Medium at /usr/share/fonts/truetype/google-fonts/. If absent, fetch Poppins from the
   google/fonts GitHub repo and fix FONT_B / FONT_M in sbtt_style.py. Avoid glyphs Poppins lacks (→ ≈ are risky; × is fine).

## Episode steps
1. Find a trend that is rising or peaking NOW (web search: "TikTok trends this week", virlo.ai/trends).
   Pick one with a genuine, explainable physics angle not in episodes_log.md.
2. Write 8–11 short narration lines (hook in line 1, payoff, "Follow for the science behind the next trend." last).
   Every physics claim must be correct; prefer qualitative statements over numbers you can't verify.
3. `tts()` → timing; build 5–6 scenes whose boundaries sit on line start times; captions = shortened lines.
4. Keep everything inside the safe zone: nothing important above y=230, below y=1650, or in the right 150 px
   between y=900 and 1650. Captions at y≈1380.
5. Render 3–5 key stills, LOOK at them, fix overlaps, then render all scenes and `assemble(..., max_bytes=40_000_000)`
   (no 3 MB limit with GitHub; keep full quality).
6. Copy the mp4 to `videos/YYYY-MM-DD_slug.mp4`, commit (author sciencebehindthetrend <sciencebehindthetrend@gmail.com>)
   and `git -c push.negotiate=true push origin HEAD:main`. Video URL = the raw.githubusercontent.com URL above.
7. Buffer (organization "My organization" 6b0844039aae838b0c34e3db), channels:
   - TikTok `6b0845298541f09ecbb067ac` — metadata.tiktok.isAiGenerated=true
   - YouTube `6b0845068541f09ecbb0665d` — type short, categoryId "28", madeForKids false, isAiGenerated true, title ends with #shorts
   - Instagram `6b0844d28541f09ecbb06495` — type reel, shouldShareToFeed true, isAiGenerated true
   Create the three posts as DRAFTS (saveToDraft: true) — the owner approves publication himself.
8. Append the episode (date, trend, topic, video file name) to pipeline/episodes_log.md, commit and push.
9. Notify the owner (in French): topic, why that trend, the captions, and that 3 drafts wait in Buffer for his approval.
