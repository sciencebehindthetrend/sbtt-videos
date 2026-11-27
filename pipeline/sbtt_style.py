import sys, math, random, subprocess, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30

FONT_B = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
FONT_M = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
BG = (14, 18, 32)
GRID = (26, 32, 52)
WHITE = (245, 247, 255)
YEL = (255, 210, 63)
PINK = (255, 77, 141)
CYAN = (61, 220, 255)
ORANGE = (255, 140, 40)
GREEN = (90, 230, 140)
CONF_COLS = [YEL, PINK, CYAN, GREEN, (180, 120, 255), ORANGE]

_fonts = {}
def font(size, bold=True):
    k = (size, bold)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(FONT_B if bold else FONT_M, size)
    return _fonts[k]

def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

# ---------- background ----------
_bg = None

def make_bg():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for x in range(0, W, 60):
        d.line([(x, 0), (x, H)], fill=GRID, width=1)
    for y in range(0, H, 60):
        d.line([(0, y), (W, y)], fill=GRID, width=1)
    # vignette
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-300, -200, W + 300, H + 200], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(220))
    dark = Image.new("RGB", (W, H), (6, 8, 16))
    return Image.composite(im, dark, vig)

def base():
    global _bg
    if _bg is None:
        _bg = make_bg()
    im = _bg.copy()
    d = ImageDraw.Draw(im)
    # series banner (below platform top UI)
    txt = "THE SCIENCE BEHIND THE TREND"
    f = font(34)
    tw = d.textlength(txt, font=f)
    x0 = (W - tw) / 2
    d.rounded_rectangle([x0 - 28, 238, x0 + tw + 28, 298], radius=30, fill=YEL)
    d.text((x0, 243), txt, font=f, fill=BG)
    return im, d

# ---------- captions ----------
def parse(text):
    # *word* = highlighted
    out = []
    for w in text.split(" "):
        hl = w.startswith("*")
        w2 = w.strip("*")
        out.append((w2, hl or w.endswith("*")))
    return out

def caption(im, text, t_in, t, y=1250, size=66, maxw=880):
    if t < t_in:
        return
    k = ease((t - t_in) / 0.25)
    words = parse(text)
    f = font(size)
    d = ImageDraw.Draw(im)
    lines, cur, curw = [], [], 0
    sp = d.textlength(" ", font=f)
    for w, hl in words:
        ww = d.textlength(w, font=f)
        if cur and curw + sp + ww > maxw:
            lines.append((cur, curw)); cur, curw = [], 0
        curw = curw + (sp if cur else 0) + ww
        cur.append((w, hl, ww))
    if cur:
        lines.append((cur, curw))
    lh = int(size * 1.25)
    yy = y + (1 - k) * 40
    for ln, lw in lines:
        x = (W - lw) / 2
        for w, hl, ww in ln:
            d.text((x, yy), w, font=f, fill=YEL if hl else WHITE,
                   stroke_width=7, stroke_fill=(0, 0, 0))
            x += ww + sp
        yy += lh

def captions(im, t, cues, **kw):
    cur = None
    for (a, b, txt) in cues:
        if a <= t < b:
            cur = (a, txt)
    if cur:
        caption(im, cur[1], cur[0], t, **kw)

def fade(im, t, dur, fin=0.0, fout=0.0):
    a = 1.0
    if fin and t < fin:
        a = t / fin
    if fout and t > dur - fout:
        a = min(a, (dur - t) / fout)
    if a < 1:
        im = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), im, clamp(a))
    return im

def arrow(d, p0, p1, col, w=10, head=34):
    d.line([p0, p1], fill=col, width=w)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    a1 = ang + math.radians(150); a2 = ang - math.radians(150)
    d.polygon([p1, (p1[0] + head * math.cos(a1), p1[1] + head * math.sin(a1)),
               (p1[0] + head * math.cos(a2), p1[1] + head * math.sin(a2))], fill=col)


def draw_confetto(d, x, y, ang, col, sz):
    # flipping rectangle: apparent height varies with cos
    hw = sz
    hh = max(2.0, abs(math.cos(ang)) * sz * 0.55)
    ca, sa = math.cos(ang * 0.5), math.sin(ang * 0.5)
    pts = []
    for (px, py) in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)):
        pts.append((x + px * ca - py * sa, y + px * sa + py * ca))
    d.polygon(pts, fill=col)



# ================= pipeline helpers =================
import json as _json, subprocess as _sp, os as _os

FONT_B = FONT_B  # Poppins Bold; if missing, install: apt fonts or pip download from Google Fonts on GitHub

def tts(lines, outdir, voice="am_michael", speed=1.1, gap=0.3, lead=0.15):
    """lines: list of narration strings. Writes lNN.wav + timing.json; returns timing dict.
    Needs kokoro-onnx + model files kokoro-v1.0.int8.onnx / voices-v1.0.bin in outdir/.. (see PIPELINE.md)."""
    import soundfile as sf
    from kokoro_onnx import Kokoro
    k = Kokoro(_os.environ.get("KOKORO_MODEL", "kokoro-v1.0.int8.onnx"), _os.environ.get("KOKORO_VOICES", "voices-v1.0.bin"))
    t, out = lead, []
    for i, txt in enumerate(lines):
        s, sr = k.create(txt, voice=voice, speed=speed, lang="en-us")
        sf.write(f"{outdir}/l{i:02d}.wav", s, sr)
        out.append(dict(i=i, start=round(t, 3), dur=len(s) / sr, txt=txt))
        t += len(s) / sr + gap
    tm = dict(lines=out, total=round(t - gap + 1.0, 3), sr=sr)
    _json.dump(tm, open(f"{outdir}/timing.json", "w"), indent=1)
    return tm

def mix_voice(tm, outdir, pops=()):
    """Place narration lines at their start times (+ optional 'pop' SFX at given seconds) -> voice.wav"""
    import numpy as np, soundfile as sf
    sr = tm.get("sr", 24000)
    buf = np.zeros(int(tm["total"] * sr) + sr, dtype=np.float32)
    for l in tm["lines"]:
        s, _ = sf.read(f"{outdir}/l{l['i']:02d}.wav", dtype="float32")
        i0 = int(l["start"] * sr); buf[i0:i0 + len(s)] += s
    rng = np.random.default_rng(1); n = int(0.35 * sr); tt = np.arange(n) / sr
    pop = (0.55 * np.convolve(rng.standard_normal(n), np.ones(6) / 6, mode="same") + 0.7 * np.sin(2 * np.pi * 90 * tt * np.exp(-tt * 8))) * np.exp(-tt * 22)
    for p in pops:
        i0 = int(p * sr); buf[i0:i0 + n] += 0.6 * pop.astype(np.float32)
    buf = buf[:int(tm["total"] * sr)]; buf = buf / max(1e-6, np.abs(buf).max()) * 0.89
    sf.write(f"{outdir}/voice.wav", buf, sr)

def render_scene(fn, t0, t1, path):
    """fn(local_t, global_T) -> PIL image (W x H). Encodes frames [t0, t1) to path (atomic rename)."""
    n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    tmp = path[:-4] + ".part.mp4"
    p = _sp.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-f", "mp4", tmp], stdin=_sp.PIPE)
    for i in range(n0, n1):
        p.stdin.write(fn((i - n0) / FPS, i / FPS).convert("RGB").tobytes())
    p.stdin.close()
    if p.wait() == 0:
        _os.replace(tmp, path)

def assemble(scene_files, voice_wav, out_mp4, max_bytes=2_900_000):
    """concat scenes + voice, loudness-normalised; re-encodes until under max_bytes (Drive upload limit ~3 MB)."""
    lst = out_mp4 + ".txt"
    open(lst, "w").write("".join(f"file '{_os.path.abspath(f)}'\n" for f in scene_files))
    joined = out_mp4 + ".joined.mp4"
    _sp.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined], check=True)
    for crf in (24, 26, 28, 30, 32):
        _sp.run(["ffmpeg", "-y", "-loglevel", "error", "-i", joined, "-i", voice_wav, "-map", "0:v", "-map", "1:a",
                 "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
                 "-af", "loudnorm=I=-14:TP=-1.5", "-shortest", "-movflags", "+faststart", out_mp4], check=True)
        if _os.path.getsize(out_mp4) <= max_bytes:
            return crf
    return None
