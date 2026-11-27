# Episode: Christmas lights — series circuits & shunts ("the tree goes up" trend)
import os, sys, math, json, subprocess, random
sys.path.insert(0, "/home/claude/sbtt-videos/pipeline")
import sbtt_style as R
from PIL import Image, ImageDraw, ImageFilter

W, H, FPS = R.W, R.H, R.FPS
WHITE, YEL, PINK, CYAN, ORANGE, GREEN, BG = R.WHITE, R.YEL, R.PINK, R.CYAN, R.ORANGE, R.GREEN, R.BG
font, ease, clamp, arrow, caption = R.font, R.ease, R.clamp, R.arrow, R.caption
TM = json.load(open("timing.json"))
S = [l["start"] for l in TM["lines"]]
TOTAL = TM["total"]

CAPS = [
    "The *tree* is going up. Why can *one* *bulb* black out the *whole* string?",
    "Classic mini lights are wired in *series:* one single *path.*",
    "They *share* the wall voltage: just a *few* *volts* each.",
    "Current flows through *every* *filament,* one after another.",
    "One filament *breaks?* The loop is *open.* All *dark.*",
    "So most bulbs hide a tiny extra wire: a *shunt.*",
    "Full voltage hits the shunt, burns its *coating,* and it *conducts.*",
    "Current *skips* the dead bulb. The rest stay *lit.*",
    "Pull a bulb *out?* No shunt, no path. *Darkness.*",
    "Follow for the science behind the *next* *trend.*",
]
SCENES = [("s1", 0.0, S[1]), ("s2", S[1], S[4]), ("s3", S[4], S[5]), ("s4", S[5], S[7]),
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

# ---------- glow sprites ----------
_glow = {}
def glow(col, r):
    k = (col, r)
    if k not in _glow:
        n = r * 4
        g = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse([n/2 - r, n/2 - r, n/2 + r, n/2 + r], fill=col + (170,))
        _glow[k] = g.filter(ImageFilter.GaussianBlur(r * 0.55))
    return _glow[k]

def paste_glow(im, x, y, col, r, a=1.0):
    g = glow(col, r)
    if a < 0.99:
        g = g.copy(); g.putalpha(g.getchannel("A").point(lambda v: int(v * a)))
    im.paste(g, (int(x - g.width / 2), int(y - g.height / 2)), g)

DARKB = (50, 54, 70)
WIRE = (120, 200, 120)

def bulb(im, d, x, y, col, lit=1.0, broken=False, r=40):
    """bulb sitting on a horizontal wire at (x,y)."""
    if lit > 0.02:
        paste_glow(im, x, y, col, r + 22, lit)
        d = ImageDraw.Draw(im)
    fill = tuple(int(DARKB[i] + (col[i] - DARKB[i]) * lit) for i in range(3))
    d.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=(0, 0, 0), width=4)
    # filament zigzag across
    fc = (255, 255, 230) if lit > 0.5 else (140, 140, 150)
    pts = [(x - r + 6, y)]
    for i in range(1, 6):
        pts.append((x - r + 6 + i * (2 * r - 12) / 6, y + (-9 if i % 2 else 9)))
    pts.append((x + r - 6, y))
    if broken:
        d.line(pts[:3], fill=fc, width=5); d.line(pts[4:], fill=fc, width=5)
    else:
        d.line(pts, fill=fc, width=5)
    return d

# ---------- series loop ----------
LX0, LX1, LY0, LY1 = 170, 880, 560, 1130
BX = [300, 445, 590, 735]
BULBS = [(x, LY0) for x in BX] + [(x, LY1) for x in BX[::-1]]
COLS = [YEL, PINK, CYAN, GREEN, ORANGE, YEL, PINK, CYAN]
LOOP = [(LX0, LY0), (LX1, LY0), (LX1, LY1), (LX0, LY1), (LX0, LY0)]
PER = 2 * (LX1 - LX0) + 2 * (LY1 - LY0)

def loop_pt(s):
    s %= PER
    for (a, b) in zip(LOOP, LOOP[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if s <= L:
            f = s / L; return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        s -= L
    return LOOP[0]

def draw_loop(d, gap=None):
    d.line(LOOP, fill=WIRE, width=10, joint="curve")
    # wall source on the left edge
    cy = (LY0 + LY1) / 2
    d.rounded_rectangle([LX0 - 70, cy - 90, LX0 + 70, cy + 90], radius=22, fill=(30, 36, 60), outline=WHITE, width=5)
    d.line([(LX0 - 18, cy - 40), (LX0 - 18, cy + 0)], fill=WHITE, width=10)
    d.line([(LX0 + 18, cy - 40), (LX0 + 18, cy + 0)], fill=WHITE, width=10)
    tw = d.textlength("WALL", font=font(34))
    d.text((LX0 - tw / 2, cy + 22), "WALL", font=font(34), fill=WHITE)

def current_dots(d, t, skip=None, speed=160, stop_frac=1.0):
    for k in range(0, PER, 70):
        s = k + t * speed
        p = loop_pt(s)
        cy = (LY0 + LY1) / 2
        if abs(p[0] - LX0) < 2 and abs(p[1] - cy) < 95:
            continue
        if skip and any(abs(p[0] - bx) < 34 and abs(p[1] - by) < 34 for bx, by in skip):
            continue
        d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], fill=CYAN, outline=(0, 0, 0), width=2)

def draw_bulbs(im, d, lit, broken=(), skip=(), missing=()):
    for i, (x, y) in enumerate(BULBS):
        if i in missing:
            d.rectangle([x - 22, y - 14, x + 22, y + 14], fill=(70, 70, 80), outline=(0, 0, 0), width=3)
            d.rectangle([x - 6, y - 16, x + 6, y + 16], fill=BG)
            continue
        l = lit[i] if isinstance(lit, (list, tuple)) else lit
        d = bulb(im, d, x, y, COLS[i], l, broken=i in broken)
        if i in skip:
            d.line([(x - 30, y + 42), (x + 30, y + 42)], fill=CYAN, width=8)
            d.line([(x - 30, y), (x - 30, y + 42)], fill=CYAN, width=8)
            d.line([(x + 30, y), (x + 30, y + 42)], fill=CYAN, width=8)
    return d

# ---------- scenes ----------
def tree_lights():
    pts = []
    rows = []
    for y in (520, 680, 840, 1000):
        hw = (y + 20 - 360) / 790 * 310 * 0.85
        rows.append((y, 540 - hw, 540 + hw))
    for i, (y, xa, xb) in enumerate(rows):
        n = 4 + i
        for j in range(n):
            f = j / (n - 1)
            x = xa + (xb - xa) * (f if i % 2 == 0 else 1 - f)
            pts.append((x, y + 40 * math.sin(f * math.pi)))
    return pts
TL = tree_lights()

def s1(t, T):
    im, d = R.base()
    d.polygon([(540, 360), (230, 1150), (850, 1150)], fill=(30, 110, 60), outline=(20, 70, 40))
    d.rectangle([505, 1150, 575, 1240], fill=(110, 70, 40))
    d.polygon([(540, 330), (552, 360), (585, 362), (558, 380), (568, 412), (540, 393), (512, 412), (522, 380), (495, 362), (528, 360)], fill=YEL)
    d.line(TL, fill=(40, 60, 40), width=5)
    flick = 2.0 < t < 2.6
    dark = t >= 2.6
    for i, (x, y) in enumerate(TL):
        lit = 0.0 if dark else 1.0
        if i == 9 and flick:
            lit = 1.0 if int(t * 14) % 2 else 0.1
        if i == 9 and t >= 2.6:
            pass
        d = bulb(im, d, x, y, R.CONF_COLS[i % 6], lit, r=18)
    if dark:
        x, y = TL[9]
        d.ellipse([x - 40, y - 40, x + 40, y + 40], outline=PINK, width=6)
        k = ease((t - 2.8) / 0.4)
        if k > 0:
            f = font(int(200 * k) + 1)
            tw = d.textlength("?", font=f)
            d.text((540 - tw / 2, 560), "?", font=f, fill=PINK, stroke_width=8, stroke_fill=(0, 0, 0))
    cur_caption(im, T)
    return R.fade(im, t, 99, fin=0.15)

def s2(t, T):
    im, d = R.base()
    lbl(d, (90, 380), "IN SERIES", YEL, 60)
    draw_loop(d)
    T2, T3 = S[2] - S[1], S[3] - S[1]
    if t < T3:
        d = draw_bulbs(im, d, 1.0)
    else:  # sequential pulse through filaments
        tt = t - T3
        lit = [0.35 + 0.65 * clamp(1 - abs(((tt * 2.2) % 9) - i) / 1.2) for i in range(8)]
        d = draw_bulbs(im, d, lit)
    current_dots(d, t)
    if t > 1.0:
        lbl(d, (380, 470), "ONE PATH", CYAN, 46)
    if t > T2 + 0.3:
        lbl(d, (300, 800), "wall voltage", WHITE, 46)
        lbl(d, (300, 860), "shared by every bulb", YEL, 42)
        for x in BX:
            d.text((x - 22, LY0 + 44), "V", font=font(34), fill=YEL, stroke_width=3, stroke_fill=(0, 0, 0))
    if t > T3 + 0.3:
        lbl(d, (300, 950), "through each filament", CYAN, 42)
    cur_caption(im, T)
    return im

def s3(t, T):
    im, d = R.base()
    lbl(d, (90, 380), "ONE FILAMENT BREAKS", PINK, 56)
    draw_loop(d)
    tb = 0.8
    if t < tb:
        d = draw_bulbs(im, d, 1.0)
        current_dots(d, t)
    else:
        fadek = 1 - ease((t - tb) / 0.25)
        d = draw_bulbs(im, d, fadek, broken=(2,))
        x, y = BULBS[2]
        if t < tb + 0.4:
            rr = random.Random(int(t * 30))
            for _ in range(10):
                a = rr.uniform(0, 6.28); L = rr.uniform(20, 70)
                d.line([(x, y), (x + L * math.cos(a), y + L * math.sin(a))], fill=YEL, width=4)
        if t > tb + 0.6:
            lbl(d, (300, 790), "OPEN CIRCUIT", PINK, 60)
            lbl(d, (300, 870), "no current at all", WHITE, 44)
        d.ellipse([x - 48, y - 48, x + 48, y + 48], outline=PINK, width=6)
    cur_caption(im, T)
    return im

def s4(t, T):  # bulb close-up with shunt
    im, d = R.base()
    lbl(d, (90, 380), "INSIDE THE BULB", CYAN, 56)
    cx = 540
    T6 = S[6] - S[5]
    tbreak = T6 + 0.6
    tburn = T6 + 2.6
    broken = t > tbreak
    lit = 0.0 if broken else 1.0
    if lit > 0:
        paste_glow(im, cx, 640, YEL, 170, 0.8); d = ImageDraw.Draw(im)
    d.ellipse([cx - 180, 470, cx + 180, 930], outline=(200, 210, 230), width=7, fill=(40, 44, 60) if broken else (90, 80, 40))
    d.rectangle([cx - 110, 900, cx + 110, 1060], fill=(150, 150, 165), outline=(0, 0, 0), width=4)
    for yy in range(925, 1060, 30):
        d.line([(cx - 110, yy), (cx + 110, yy)], fill=(100, 100, 115), width=4)
    lx, rx, ytop = cx - 70, cx + 70, 640
    d.line([(lx, 1060), (lx, ytop)], fill=(210, 210, 220), width=8)
    d.line([(rx, 1060), (rx, ytop)], fill=(210, 210, 220), width=8)
    pts = [(lx, ytop)] + [(lx + i * 140 / 8, ytop + (-18 if i % 2 else 18)) for i in range(1, 8)] + [(rx, ytop)]
    fc = (255, 250, 210) if not broken else (150, 150, 160)
    if broken:
        d.line(pts[:4], fill=fc, width=6); d.line(pts[5:], fill=fc, width=6)
    else:
        d.line(pts, fill=fc, width=6)
    if tbreak < t < tbreak + 0.4:
        rr = random.Random(int(t * 30))
        for _ in range(10):
            a = rr.uniform(0, 6.28); L = rr.uniform(20, 80)
            d.line([(cx, ytop), (cx + L * math.cos(a), ytop + L * math.sin(a))], fill=YEL, width=4)
    # shunt coil between leads
    ys = 810
    if t < tbreak:
        sc = (110, 120, 150)
    elif t < tburn:
        sc = ORANGE if int(t * 8) % 2 else (255, 200, 120)
    else:
        sc = CYAN
    d.line([(lx, ys), (rx, ys)], fill=sc, width=10)
    for i in range(7):
        x = lx + 12 + i * 19
        d.ellipse([x - 10, ys - 16, x + 10, ys + 16], outline=sc, width=5)
    if t > 0.8:
        lbl(d, (90, 610), "filament", YEL, 44)
        arrow(d, (290, 660), (lx - 15, ytop + 10), YEL, w=6, head=22)
    if t > 1.6:
        lbl(d, (90, 830), "shunt", CYAN, 50)
        arrow(d, (240, 860), (lx - 15, ys), CYAN, w=6, head=22)
    if tbreak + 0.4 < t < tburn:
        lbl(d, (cx + 200, 700), "full\nvoltage!", ORANGE, 46)
    if t > tburn:
        lbl(d, (cx + 200, 700), "coating\nburns\nthrough", CYAN, 44)
        # current through leads + shunt
        path = [(lx, 1060), (lx, ys), (rx, ys), (rx, 1060)]
        segs = list(zip(path, path[1:])); tot = sum(math.hypot(b[0]-a[0], b[1]-a[1]) for a, b in segs)
        for k in range(0, int(tot), 50):
            s = (k + (t - tburn) * 140) % tot
            for a, b in segs:
                L = math.hypot(b[0]-a[0], b[1]-a[1])
                if s <= L:
                    p = (a[0] + (b[0]-a[0]) * s / L, a[1] + (b[1]-a[1]) * s / L)
                    d.ellipse([p[0]-9, p[1]-9, p[0]+9, p[1]+9], fill=YEL, outline=(0, 0, 0), width=2); break
                s -= L
    cur_caption(im, T)
    return im

def s5(t, T):
    im, d = R.base()
    T8 = S[8] - S[7]
    draw_loop(d)
    if t < T8:
        lbl(d, (90, 380), "SHUNT = BYPASS", GREEN, 56)
        d = draw_bulbs(im, d, [0 if i == 2 else 1 for i in range(8)], broken=(2,), skip=(2,))
        current_dots(d, t, skip=[BULBS[2]])
        if t > 0.8:
            lbl(d, (300, 800), "rest stay lit", GREEN, 56)
    else:
        tt = t - T8
        lbl(d, (90, 380), "BULB PULLED OUT", PINK, 56)
        x, y = BULBS[1]
        lift = ease((tt - 0.3) / 0.7)
        dark = tt > 1.0
        lit = [0 if (dark or i == 2) else 1 for i in range(8)]
        d = draw_bulbs(im, d, lit, broken=(2,), skip=(2,), missing=(1,) if tt > 0.3 else ())
        if tt > 0.3:
            d = bulb(im, d, x, y + 140 * lift, COLS[1], 0.0 if dark else 1.0)
            if lift < 1:
                pass
        if not dark:
            current_dots(d, t, skip=[BULBS[2]])
        else:
            d.ellipse([x - 50, y - 50, x + 50, y + 50], outline=PINK, width=6)
            if tt > 1.3:
                lbl(d, (300, 790), "NO PATH", PINK, 64)
                lbl(d, (300, 875), "whole section dark", WHITE, 44)
    cur_caption(im, T)
    return im

def s6(t, T):
    im, d = R.base()
    rr = random.Random(11)
    for i in range(60):
        x = rr.uniform(0, W); y = (rr.uniform(-H, H) + 140 * t) % H
        c = rr.choice(R.CONF_COLS)
        x2 = x + 30 * math.sin(t * 2 + i)
        if 330 < y < 1600 and not (680 < y < 1090 and 120 < x2 < 960):
            d = bulb(im, d, x2, y, c, 1.0, r=16)
    f = font(84); s = "FOLLOW"; tw = d.textlength(s, font=f)
    d.text(((W - tw) / 2, 760), s, font=f, fill=YEL, stroke_width=8, stroke_fill=(0, 0, 0))
    caption(im, CAPS[9], 0.1, t, y=930, size=64)
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
