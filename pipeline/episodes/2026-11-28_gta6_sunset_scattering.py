# Episode: GTA 6 loading-screen sunset — Rayleigh scattering (why sunsets are orange/pink)
import os, sys, math, json, random
sys.path.insert(0, "/home/claude/sbtt-videos/pipeline")
import sbtt_style as R
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

W, H, FPS = R.W, R.H, R.FPS
WHITE, YEL, PINK, CYAN, ORANGE, GREEN, BG = R.WHITE, R.YEL, R.PINK, R.CYAN, R.ORANGE, R.GREEN, R.BG
font, ease, clamp, arrow, caption = R.font, R.ease, R.clamp, R.arrow, R.caption
TM = json.load(open("timing.json"))
S = [l["start"] for l in TM["lines"]]
TOTAL = TM["total"]

BLUE = (70, 130, 255)
RED = (255, 70, 60)
VIOLET = (150, 90, 255)
PURPLE = (190, 90, 210)

CAPS = [
    "Everyone's a *GTA* *6* loading screen. But why is that sunset *orange* and *pink?*",
    "Sunlight looks white, but it's *every* *color* mixed together.",
    "Air molecules *scatter* it. *Blue* scatters about *5×* more than *red.*",
    "At noon: a *short* *path.* Scattered blue comes from everywhere. *Blue* *sky.*",
    "At sunset, the light crosses *dozens* *of* *times* more air.",
    "Along that long path, most of the *blue* is scattered *away.*",
    "What survives: *orange* and *red.* The sun, and the clouds it lights.",
    "Pinks and purples? *Red* light mixing with leftover *blue.*",
    "Why not *violet?* The sun sends *less,* and our eyes *barely* see it.",
    "That glow is just sunlight taking the *long* *way* through the air.",
    "Follow for the science behind the *next* *trend.*",
]
SCENES = [("s1", 0.0, S[1]), ("s2", S[1], S[3]), ("s3", S[3], S[5]), ("s4", S[5], S[7]),
          ("s5", S[7], S[9]), ("s6", S[9], TOTAL)]

def cur_caption(im, T):
    i = max(j for j in range(len(S)) if S[j] - 0.1 <= T) if T >= S[0] - 0.1 else None
    if i is not None:
        caption(im, CAPS[i], S[i] - 0.1, T, y=1380, size=60)

def lbl(d, xy, s, col, size=46):
    d.text(xy, s, font=font(size), fill=col, stroke_width=5, stroke_fill=(0, 0, 0))

def ctext(d, y, s, col, size=56):
    tw = d.textlength(s, font=font(size))
    lbl(d, ((W - tw) / 2, y), s, col, size)

def mix(a, b, f):
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))

# ---------- sunset "loading screen" card ----------
CX0, CY0, CX1, CY1 = 70, 340, 1010, 1290
HZ = 990
_card = None
def card():
    global _card
    if _card is not None:
        return _card
    w, h = CX1 - CX0, CY1 - CY0
    stops = [(0.0, (40, 20, 90)), (0.30, (150, 50, 150)), (0.52, (255, 90, 120)), (0.66, (255, 150, 70)), (0.69, (255, 205, 110))]
    ys = np.arange(h) / h
    col = np.zeros((h, 3))
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        m = (ys >= a) & (ys <= b)
        f = ((ys[m] - a) / (b - a))[:, None]
        col[m] = np.array(ca) * (1 - f) + np.array(cb) * f
    m = ys > stops[-1][0]
    col[m] = (60, 25, 80)
    arr = np.repeat(col[:, None, :], w, axis=1).astype(np.uint8)
    im = Image.fromarray(arr, "RGB")
    d = ImageDraw.Draw(im)
    hz = HZ - CY0
    # sun (half set)
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([w / 2 - 230, hz - 230, w / 2 + 230, hz + 230], fill=(255, 190, 90, 150))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    im.paste(glow, (0, 0), glow); d = ImageDraw.Draw(im)
    d.ellipse([w / 2 - 125, hz - 125, w / 2 + 125, hz + 125], fill=(255, 225, 140))
    # sea
    d.rectangle([0, hz, w, h], fill=(55, 25, 85))
    for k in range(9):
        yy = hz + 14 + k * 26
        hw = 150 - k * 12
        d.rounded_rectangle([w / 2 - hw, yy, w / 2 + hw, yy + 7], radius=3, fill=(255, 160, 90))
    # palms
    def palm(x0, lean):
        pts = [(x0 + lean * (s ** 1.6) * 120, hz + 10 - s * 520) for s in np.linspace(0, 1, 12)]
        d.line(pts, fill=(25, 10, 35), width=26, joint="curve")
        tx, ty = pts[-1]
        for a in (-160, -120, -70, -20, 20, 200, 160):
            r = math.radians(a)
            p = [(tx + math.cos(r) * L - 0 * L, ty + math.sin(r) * L * 0.5 + (L / 180) ** 2 * 60) for L in range(0, 200, 20)]
            d.line(p, fill=(25, 10, 35), width=16, joint="curve")
    palm(110, 0.6)
    palm(w - 100, -0.7)
    # generic person bust silhouette (left of sun)
    px = 300
    d.ellipse([px - 70, 430, px + 70, 600], fill=(25, 10, 35))
    d.rounded_rectangle([px - 150, 620, px + 150, h + 60], radius=110, fill=(25, 10, 35))
    d.rectangle([px - 35, 580, px + 35, 650], fill=(25, 10, 35))
    _card = im
    return im

def draw_card(im, prog, title=None, glowk=0.0):
    c = card()
    mask = Image.new("L", c.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, c.width - 1, c.height - 1], radius=36, fill=255)
    im.paste(c, (CX0, CY0), mask)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([CX0, CY0, CX1, CY1], radius=36, outline=WHITE, width=5)
    # loading bar
    bx0, bx1, by = CX0 + 50, 900, CY1 - 75
    lbl(d, (bx0, by - 62), "LOADING..." if prog < 1 else "LOADED", WHITE, 38)
    d.rounded_rectangle([bx0, by, bx1, by + 26], radius=13, fill=(20, 10, 30), outline=WHITE, width=3)
    if prog > 0.01:
        d.rounded_rectangle([bx0 + 4, by + 4, bx0 + 4 + (bx1 - bx0 - 8) * clamp(prog), by + 22], radius=10, fill=YEL)
    if title:
        ctext(d, CY0 + 40, title, WHITE, 56)
    return d

# ---------- s1: hook ----------
def s1(t, T):
    im, d = R.base()
    d = draw_card(im, ease(t / 6.0) * 0.8)
    if t > 3.2:
        k = ease((t - 3.2) / 0.4)
        f = font(int(64 * (0.6 + 0.4 * k)))
        s = "WHY THESE COLORS?"
        tw = d.textlength(s, font=f)
        d.text(((W - tw) / 2, CY0 + 50), s, font=f, fill=YEL, stroke_width=7, stroke_fill=(0, 0, 0))
    cur_caption(im, T)
    return R.fade(im, t, 99, fin=0.15)

# ---------- s2: white light + scattering ----------
RAINBOW = [(150, 90, 255), BLUE, CYAN, GREEN, YEL, ORANGE, RED]

def wave(d, x0, x1, y, lam, amp, col, phase, width=7):
    pts = [(x, y + amp * math.sin(2 * math.pi * (x - phase) / lam)) for x in range(int(x0), int(x1), 4)]
    if len(pts) > 1:
        d.line(pts, fill=col, width=width, joint="curve")

def molecule(d, x, y):
    d.ellipse([x - 34, y - 26, x + 6, y + 14], fill=(200, 210, 230), outline=(0, 0, 0), width=3)
    d.ellipse([x - 6, y - 14, x + 34, y + 26], fill=(200, 210, 230), outline=(0, 0, 0), width=3)

def s2(t, T):
    im, d = R.base()
    T2 = S[2] - S[1]
    if t < T2:
        lbl(d, (90, 380), "WHITE LIGHT", WHITE, 60)
        sx, sy = 170, 760
        R_ = 80
        d.ellipse([sx - R_, sy - R_, sx + R_, sy + R_], fill=(255, 240, 180), outline=(0, 0, 0), width=4)
        px, py = 520, 760
        tri = [(px, py - 150), (px - 130, py + 100), (px + 130, py + 100)]
        k = ease(t / 0.8)
        # incoming white beam to prism left face
        ex = sx + R_ + (px - 70 - sx - R_) * k
        d.line([(sx + R_, sy), (ex, sy)], fill=WHITE, width=16)
        d.polygon(tri, fill=(80, 100, 140), outline=WHITE)
        d.line(tri + [tri[0]], fill=WHITE, width=5)
        k2 = ease((t - 0.8) / 0.8)
        if k2 > 0:
            for i, c in enumerate(RAINBOW):
                a = math.radians(-14 + i * 5)
                L = 380 * k2
                p0 = (px + 60, py - 10 + i * 4)
                d.line([p0, (p0[0] + L * math.cos(a), p0[1] + L * math.sin(a))], fill=c, width=13)
        if t > 1.8:
            ctext(d, 1020, "= EVERY COLOR MIXED", YEL, 56)
    else:
        tt = t - T2
        lbl(d, (90, 380), "SCATTERING", CYAN, 60)
        mx = 540
        # blue row
        yb, yr = 680, 900
        lbl(d, (90, yb + 45), "short wave", BLUE, 40)
        wave(d, 70, mx - 40, yb, 46, 26, BLUE, tt * 220)
        molecule(d, mx, yb)
        kb = clamp((tt - 0.4) / 0.8)
        for a in range(0, 360, 30):
            r = math.radians(a)
            L = 60 + 110 * kb
            if kb > 0:
                arrow(d, (mx + 50 * math.cos(r), yb + 50 * math.sin(r)), (mx + L * math.cos(r) + 0.01, yb + L * math.sin(r)), BLUE, w=6, head=18)
        # red row
        lbl(d, (90, yr + 45), "long wave", RED, 40)
        wave(d, 70, mx - 40, yr, 120, 26, RED, tt * 220)
        molecule(d, mx, yr)
        wave(d, mx + 40, 880, yr, 120, 24, RED, tt * 220)
        if kb > 0:
            for a in (40, 140, 220, 320):
                r = math.radians(a)
                arrow(d, (mx + 50 * math.cos(r), yr + 50 * math.sin(r)), (mx + 90 * math.cos(r), yr + 90 * math.sin(r)), RED, w=4, head=12)
        # bars
        kk = ease((tt - 2.0) / 0.8)
        if kk > 0:
            lbl(d, (90, 1030), "scattered:", WHITE, 40)
            d.rounded_rectangle([250, 1095, 250 + 600 * kk, 1150], radius=14, fill=BLUE)
            d.rounded_rectangle([250, 1180, 250 + 115 * kk, 1235], radius=14, fill=RED)
            lbl(d, (110, 1095), "BLUE", BLUE, 40)
            lbl(d, (110, 1180), "RED", RED, 40)
            if kk > 0.95:
                lbl(d, (400, 1180), "about 5× less", WHITE, 40)
    cur_caption(im, T)
    return im

# ---------- s3: noon vs sunset path ----------
EC = (540, 2100)
ER = 1250
AR = 1430
OBS = (540, EC[1] - ER)

def earth(d, sky_col):
    d.ellipse([EC[0] - AR, EC[1] - AR, EC[0] + AR, EC[1] + AR], fill=sky_col)
    d.ellipse([EC[0] - ER, EC[1] - ER, EC[0] + ER, EC[1] + ER], fill=(30, 70, 60), outline=(0, 0, 0), width=4)
    x, y = OBS
    d.ellipse([x - 16, y - 92, x + 16, y - 60], fill=WHITE)
    d.line([(x, y - 60), (x, y - 22)], fill=WHITE, width=8)
    d.line([(x, y - 22), (x - 14, y)], fill=WHITE, width=8)
    d.line([(x, y - 22), (x + 14, y)], fill=WHITE, width=8)

def s3(t, T):
    im, d = R.base()
    T4 = S[4] - S[3]
    if t < T4:
        lbl(d, (90, 380), "NOON", YEL, 60)
        earth(d, (40, 90, 170))
        sx, sy = 540, 480
        d.ellipse([sx - 55, sy - 55, sx + 55, sy + 55], fill=(255, 240, 180), outline=(0, 0, 0), width=4)
        top = EC[1] - AR
        d.line([(sx, sy + 60), (sx, OBS[1] - 100)], fill=(255, 245, 210), width=12)
        d.line([(sx - 40, top), (sx - 40, OBS[1])], fill=YEL, width=5)
        lbl(d, (sx - 340, (top + OBS[1]) / 2 - 30), "short path", YEL, 42)
        rr = random.Random(3)
        if t > 1.5:
            for i in range(26):
                a = rr.uniform(0, 6.28); ph = (t * 1.2 + rr.random()) % 1
                r0 = 30 + ph * 300
                p = (sx + r0 * math.cos(a), top + 80 + r0 * 0.45 * math.sin(a))
                if p[1] < OBS[1] - 20:
                    d.ellipse([p[0] - 8, p[1] - 8, p[0] + 8, p[1] + 8], fill=BLUE, outline=(0, 0, 0), width=2)
        if t > 3.2:
            ctext(d, 1010, "BLUE SKY", BLUE, 72)
    else:
        tt = t - T4
        lbl(d, (90, 380), "SUNSET", ORANGE, 60)
        earth(d, (120, 60, 110))
        y0 = OBS[1] - 50
        sx = 30
        k = ease(tt / 0.8)
        d.ellipse([sx - 60, y0 - 60, sx + 60, y0 + 60], fill=(255, 170, 90), outline=(0, 0, 0), width=4)
        ex = sx + 60 + (OBS[0] - 30 - sx - 60) * k
        # beam colour shifts from white to orange along path
        n = 20
        for i in range(n):
            xa = sx + 60 + (ex - sx - 60) * i / n
            xb = sx + 60 + (ex - sx - 60) * (i + 1) / n
            d.line([(xa, y0), (xb, y0)], fill=mix((255, 245, 220), ORANGE, (i / n) ** 0.8), width=12)
        if tt > 1.0:
            d.line([(sx + 60, y0 + 40), (OBS[0] - 30, y0 + 40)], fill=YEL, width=5)
            lbl(d, (200, y0 + 55), "long path", YEL, 42)
        if tt > 1.8:
            ctext(d, 1030, "DOZENS OF TIMES", ORANGE, 62)
            ctext(d, 1110, "more air near the horizon", WHITE, 44)
    cur_caption(im, T)
    return im

# ---------- s4: the long way (blue scattered out) ----------
PCOLS = [BLUE, CYAN, GREEN, YEL, ORANGE, RED]
MEANS = [250, 470, 600, 1200, 1700, 3000]
PX0, PX1, PY = 210, 840, 720

def s4(t, T):
    im, d = R.base()
    T6 = S[6] - S[5]
    lbl(d, (90, 380), "THE LONG WAY", ORANGE, 60)
    # sky band
    d.rounded_rectangle([PX0 - 30, PY - 150, PX1 + 30, PY + 150], radius=30, fill=(28, 34, 60))
    lbl(d, (PX0 - 10, PY - 145), "air", (150, 160, 190), 34)
    d.ellipse([110 - 70, PY - 70, 110 + 70, PY + 70], fill=(255, 240, 190), outline=(0, 0, 0), width=4)
    # eye
    ex = 900
    d.ellipse([ex - 50, PY - 30, ex + 30, PY + 30], fill=WHITE, outline=(0, 0, 0), width=4)
    d.ellipse([ex - 32, PY - 18, ex - 4, PY + 18], fill=(40, 40, 60))
    rr = random.Random(7)
    L = PX1 - PX0
    for i in range(160):
        ci = i % 6
        x_sc = rr.expovariate(1 / MEANS[ci])
        birth = rr.uniform(-3, 12)
        dy = rr.uniform(-60, 60)
        ang = rr.choice([-1, 1]) * rr.uniform(0.6, 1.4)
        age = t - birth
        if age < 0:
            continue
        x = PX0 + age * 260
        if x_sc < L and x > PX0 + x_sc:
            # scattered: flies off
            sx = PX0 + x_sc
            s = (x - sx)
            px, py = sx + s * math.cos(ang) * 0.4, PY + dy * 0.5 + s * math.sin(ang)
            if abs(py - PY) > 220:
                continue
        else:
            if x > PX1 + 20:
                continue
            px, py = x, PY + dy * 0.5
        d.ellipse([px - 9, py - 9, px + 9, py + 9], fill=PCOLS[ci], outline=(0, 0, 0), width=2)
    # what reaches your eye
    lbl(d, (130, 930), "WHAT REACHES YOUR EYE", WHITE, 44)
    kk = ease((t - 0.8) / 1.0)
    for i, c in enumerate(PCOLS):
        frac = math.exp(-L / MEANS[i])
        x = 160 + i * 115
        hh = 230 * frac * kk
        d.rounded_rectangle([x, 1250 - max(hh, 6), x + 80, 1250], radius=10, fill=c)
    d.line([(140, 1252), (860, 1252)], fill=WHITE, width=4)
    if t > T6 + 0.3:
        lbl(d, (160, 995), "= mostly", WHITE, 44)
        lbl(d, (370, 995), "orange + red", ORANGE, 44)
    cur_caption(im, T)
    return im

# ---------- s5: pink + why not violet ----------
def s5(t, T):
    im, d = R.base()
    T8 = S[8] - S[7]
    if t < T8:
        lbl(d, (90, 380), "TWILIGHT PINK", PINK, 60)
        y = 640
        k = [ease((t - a) / 0.4) for a in (0.2, 0.9, 1.6)]
        if k[0] > 0:
            r = 95 * k[0]; d.ellipse([260 - r, y - r, 260 + r, y + r], fill=RED, outline=(0, 0, 0), width=4)
        lbl(d, (380, y - 45), "+", WHITE, 70)
        if k[1] > 0:
            r = 95 * k[1]; d.ellipse([540 - r, y - r, 540 + r, y + r], fill=BLUE, outline=(0, 0, 0), width=4)
        lbl(d, (660, y - 45), "=", WHITE, 70)
        if k[2] > 0:
            r = 95 * k[2]; d.ellipse([820 - r, y - r, 820 + r, y + r], fill=PURPLE, outline=(0, 0, 0), width=4)
        lbl(d, (180, y + 120), "red light", RED, 40)
        lbl(d, (450, y + 120), "leftover", BLUE, 40)
        lbl(d, (450, y + 165), "blue sky", BLUE, 40)
        # twilight gradient strip
        if t > 2.2:
            for yy in range(960, 1220, 4):
                f = (yy - 960) / 260
                c = mix((60, 40, 140), PINK, f * 1.4) if f < 0.7 else mix(PINK, ORANGE, (f - 0.7) / 0.3)
                d.rectangle([120, yy, 900, yy + 4], fill=c)
            d.rounded_rectangle([120, 960, 900, 1220], radius=6, outline=WHITE, width=4)
    else:
        tt = t - T8
        lbl(d, (90, 380), "WHY NOT VIOLET?", VIOLET, 60)
        x0, x1, y0, y1 = 150, 880, 560, 980
        d.line([(x0, y1), (x1, y1)], fill=WHITE, width=4)
        # spectrum bar
        for x in range(x0, x1):
            f = (x - x0) / (x1 - x0)
            idx = f * (len(RAINBOW) - 1)
            i = min(int(idx), len(RAINBOW) - 2)
            d.line([(x, y1 + 10), (x, y1 + 60)], fill=mix(RAINBOW[i], RAINBOW[i + 1], idx - i))
        lbl(d, (x0 - 10, y1 + 70), "violet", VIOLET, 36)
        tw = d.textlength("red", font=font(36))
        lbl(d, (x1 - tw, y1 + 70), "red", RED, 36)
        k1 = ease((tt - 0.4) / 1.0)
        k2 = ease((tt - 2.0) / 1.0)
        def curve(fn, k, col, w=8):
            n = int(80 * k)
            pts = []
            for j in range(n + 1):
                f = j / 80
                pts.append((x0 + f * (x1 - x0), y1 - fn(f) * (y1 - y0 - 60)))
            if len(pts) > 1:
                d.line(pts, fill=col, width=w, joint="curve")
        sun = lambda f: 0.45 + 0.55 * clamp(f / 0.3) - 0.12 * clamp((f - 0.3) / 0.7)
        eye = lambda f: math.exp(-((f - 0.5) / 0.17) ** 2)
        curve(sun, k1, YEL)
        if k1 > 0.9:
            lbl(d, (560, y0 + 20), "sunlight", YEL, 42)
        curve(eye, k2, CYAN)
        if k2 > 0.9:
            lbl(d, (680, y0 + 140), "your eyes", CYAN, 42)
        if tt > 3.4:
            d.rounded_rectangle([x0 - 10, y0 + 120, x0 + 120, y1 - 5], radius=16, outline=PINK, width=6)
            lbl(d, (x0 + 125, y0 + 120), "low", PINK, 44)
            ctext(d, 1150, "so the sky looks BLUE", BLUE, 52)
    cur_caption(im, T)
    return im

# ---------- s6: payoff + follow ----------
def s6(t, T):
    im, d = R.base()
    T10 = S[10] - S[9]
    if t < T10:
        d = draw_card(im, clamp(0.8 + t / 2.0))
        if t > 0.6:
            ctext(d, CY0 + 50, "LONG PATH = WARM LIGHT", YEL, 58)
        cur_caption(im, T)
        return im
    tt = t - T10
    rr = random.Random(5)
    for i in range(50):
        x = rr.uniform(0, W); y = (rr.uniform(0, H) + 120 * tt) % H
        c = rr.choice([ORANGE, PINK, YEL, PURPLE])
        if 330 < y < 1600 and not (680 < y < 1090 and 100 < x < 980):
            r = rr.uniform(10, 22)
            d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    f = font(84); s = "FOLLOW"; tw = d.textlength(s, font=f)
    d.text(((W - tw) / 2, 760), s, font=f, fill=YEL, stroke_width=8, stroke_fill=(0, 0, 0))
    caption(im, CAPS[10], 0.1, tt, y=930, size=64)
    return R.fade(im, t, SCENES[-1][2] - SCENES[-1][1], fout=0.5)

FN = dict(s1=s1, s2=s2, s3=s3, s4=s4, s5=s5, s6=s6)

if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    if sys.argv[1] == "still":
        ims = []
        for a in sys.argv[2:]:
            nm, tt = a.split("@"); tt = float(tt)
            st = [x[1] for x in SCENES if x[0] == nm][0]
            ims.append(FN[nm](tt, st + tt).convert("RGB"))
        for i, x in enumerate(ims): x.save(f"out/still{i}.png")
        sm = [x.resize((360, 640)) for x in ims]
        m = Image.new("RGB", (360 * len(sm), 640))
        for i, x in enumerate(sm): m.paste(x, (360 * i, 0))
        m.save("out/contact.png")
    else:
        for nm in sys.argv[2:]:
            a, b = [(x[1], x[2]) for x in SCENES if x[0] == nm][0]
            R.render_scene(lambda t, T, f=FN[nm]: f(t, T), a, b, f"out/{nm}.mp4")
