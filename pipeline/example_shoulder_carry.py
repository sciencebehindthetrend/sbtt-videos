# EXAMPLE episode script (shoulder carry). Copy its structure for new episodes; do NOT reuse its drawings.
import os, sys, math, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbtt_style as R
from PIL import Image, ImageDraw

W, H, FPS = R.W, R.H, R.FPS
WHITE, YEL, PINK, CYAN, ORANGE, GREEN, BG = R.WHITE, R.YEL, R.PINK, R.CYAN, R.ORANGE, R.GREEN, R.BG
font, ease, clamp, arrow, caption = R.font, R.ease, R.clamp, R.arrow, R.caption
TM = json.load(open("timing.json"))
S = [l["start"] for l in TM["lines"]]
TOTAL = TM["total"]

CAPS = [
    "Everyone's doing the *shoulder* *carry.* But why is it *way* *easier* than in your arms?",
    "Same person, *same* *weight.* Only *where* it sits changes.",
    "In your arms, the weight is *in* *front* of your spine.",
    "That distance creates *torque:* weight × distance.",
    "Your *back* *muscles* pull back… from just a few cm away.",
    "Short lever, so they need *several* *times* the person's weight.",
    "On your shoulders: right *above* your spine. Distance ≈ *0.*",
    "Almost *no* *torque.* Your *skeleton* carries the load.",
    "The catch: a *higher* center of mass, so it *wobbles.*",
    "Follow for the science behind the *next* *trend.*",
]
SCENES = [("s1", 0.0, S[1]), ("s2", S[1], S[2]), ("s3", S[2], S[6]), ("s4", S[6], S[8]),
          ("s5", S[8], S[9]), ("s6", S[9], TOTAL)]

def cur_caption(im, T):
    i = max(j for j in range(len(S)) if S[j] - 0.1 <= T) if T >= S[0] - 0.1 else None
    if i is not None:
        caption(im, CAPS[i], S[i] - 0.1, T, y=1380, size=60)

# ---------- figures (side view, facing right) ----------
LW = 12
SC = 0.7
def carrier(d, x, gy, lean=0.0, arms="front", sway=0.0):
    """x = spine x at hip, gy = ground y. Returns key points."""
    hip = (x + sway * 0.3, gy - 360 * SC)
    neck = (hip[0] + math.sin(lean) * 300 * SC + sway, hip[1] - math.cos(lean) * 300 * SC)
    head_c = (neck[0] + 6, neck[1] - 46)
    # legs
    d.line([hip, (x - 22, gy - 125), (x - 15, gy)], fill=WHITE, width=LW, joint="curve")
    d.line([hip, (x + 28, gy - 125), (x + 25, gy)], fill=WHITE, width=LW, joint="curve")
    d.line([(x - 33, gy), (x + 3, gy)], fill=WHITE, width=LW)
    d.line([(x + 15, gy), (x + 55, gy)], fill=WHITE, width=LW)
    # torso
    d.line([hip, neck], fill=WHITE, width=LW + 6)
    d.ellipse([head_c[0] - 34, head_c[1] - 34, head_c[0] + 34, head_c[1] + 34], outline=WHITE, width=LW - 2)
    sh = (neck[0], neck[1] + 18)
    if arms == "front":
        d.line([sh, (sh[0] + 66, sh[1] + 84), (sh[0] + 147, sh[1] + 66)], fill=WHITE, width=LW - 2, joint="curve")
    else:  # holding legs of rider
        d.line([sh, (sh[0] + 50, sh[1] + 28), (sh[0] + 66, sh[1] - 28)], fill=WHITE, width=LW - 2, joint="curve")
    return dict(hip=hip, neck=neck, sh=sh, head=head_c)

def rider_lying(d, cx, cy, col=YEL):
    # person held horizontally in arms (simplified)
    d.rounded_rectangle([cx - 105, cy - 27, cx + 84, cy + 27], radius=27, fill=col)
    d.ellipse([cx + 77, cy - 42, cx + 154, cy + 35], fill=col)

def rider_seated(d, cx, base_y, col=YEL, sway=0.0):
    # seated on shoulders: torso up, legs hanging in front
    top = (cx + sway * 1.6, base_y - 182)
    d.line([(cx, base_y), top], fill=col, width=42)
    d.ellipse([top[0] - 38, top[1] - 84, top[0] + 38, top[1] - 7], fill=col)
    d.line([(cx, base_y), (cx + 63, base_y + 21), (cx + 66, base_y + 119)], fill=col, width=28, joint="curve")
    return top

def weight_arrow(d, x, y, L=170, lab=True):
    arrow(d, (x, y), (x, y + L), PINK, w=14, head=40)
    if lab:
        d.text((x + 22, y + L - 60), "weight", font=font(42), fill=PINK, stroke_width=4, stroke_fill=(0, 0, 0))

def torque_arc(d, cx, cy, r, strength, col=ORANGE):
    if strength <= 0.02:
        return
    a0, a1 = -100, -100 + 160 * strength
    d.arc([cx - r, cy - r, cx + r, cy + r], a0, a1, fill=col, width=14)
    a = math.radians(a1)
    p = (cx + r * math.cos(a), cy + r * math.sin(a))
    t = a + math.pi / 2
    h = 38
    d.polygon([(p[0] + h * math.cos(t), p[1] + h * math.sin(t)),
               (p[0] + 22 * math.cos(a), p[1] + 22 * math.sin(a)),
               (p[0] - 22 * math.cos(a), p[1] - 22 * math.sin(a))], fill=col)

def dim(d, x0, x1, y, label, col=CYAN):
    d.line([(x0, y), (x1, y)], fill=col, width=6)
    for x in (x0, x1):
        d.line([(x, y - 22), (x, y + 22)], fill=col, width=6)
    tw = d.textlength(label, font=font(44))
    d.text(((x0 + x1) / 2 - tw / 2, y - 72), label, font=font(44), fill=col, stroke_width=4, stroke_fill=(0, 0, 0))

GY = 1240

# ---------- scenes (t = local time, T = global) ----------
def s1(t, T):
    im, d = R.base()
    d.text((90, 380), "ARMS", font=font(60), fill=PINK)
    d.text((620, 380), "SHOULDERS", font=font(60), fill=GREEN)
    d.line([(540, 470), (540, 1240)], fill=R.GRID, width=4)
    S1 = 0.85
    # small figures: draw on separate layer then scale
    for side in (0, 1):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        if side == 0:
            k = carrier(ld, 420, 1500, lean=-0.12 + 0.04 * math.sin(t * 5))
            rider_lying(ld, k["sh"][0] + 119, k["sh"][1] + 74)
        else:
            k = carrier(ld, 420, 1500, arms="up")
            rider_seated(ld, k["neck"][0], k["neck"][1] - 30)
        lay = lay.resize((int(W * S1), int(H * S1)))
        im.paste(lay, (int(side * 520 - 60), -80), lay)
    d = ImageDraw.Draw(im)
    if t > 1.2:
        d.text((150, 1215), "HARD", font=font(70), fill=PINK, stroke_width=6, stroke_fill=(0, 0, 0))
        d.text((690, 1215), "EASY", font=font(70), fill=GREEN, stroke_width=6, stroke_fill=(0, 0, 0))
    cur_caption(im, T)
    return R.fade(im, t, 99, fin=0.15)

def s2(t, T):
    im, d = R.base()
    for i, (x, c) in enumerate([(300, PINK), (780, GREEN)]):
        k = ease((t - 0.2 * i) / 0.6)
        y = 600 + (1 - k) * 300
        d.rounded_rectangle([x - 120, y, x + 120, y + 240], radius=40, fill=YEL)
        d.ellipse([x - 70, y - 150, x + 70, y - 10], fill=YEL)
        weight_arrow(d, x, y + 260, L=200, lab=False)
    if t > 0.8:
        f = font(130)
        tw = d.textlength("=", font=f)
        d.text((540 - tw / 2, 690), "=", font=f, fill=WHITE)
        d.text((380, 1110), "same weight", font=font(56), fill=PINK)
    cur_caption(im, T)
    return im

def s3(t, T):  # arms carry: lever arm, torque, back muscles
    im, d = R.base()
    d.text((90, 380), "IN YOUR ARMS", font=font(56), fill=PINK)
    lean = -0.10
    k = carrier(d, 380, GY, lean=lean)
    spine_x = k["hip"][0]
    rx, ry = k["sh"][0] + 119, k["sh"][1] + 74
    rider_lying(d, rx, ry)
    load_x = rx + 30
    weight_arrow(d, load_x, ry + 40, L=140)
    Tl3 = S[3] - S[2]; Tl4 = S[4] - S[2]; Tl5 = S[5] - S[2]
    if t > 0.8:  # vertical line through spine/hip
        for yy in range(int(k["neck"][1]), GY, 34):
            d.line([(spine_x, yy), (spine_x, yy + 16)], fill=CYAN, width=5)
    if t > 1.2:
        dim(d, spine_x, load_x, ry + 230, "distance", CYAN)
    if t > Tl3:
        torque_arc(d, spine_x, k["hip"][1], 170, ease((t - Tl3) / 1.2))
        if t > Tl3 + 0.8:
            d.text((90, 460), "torque = weight × distance", font=font(46), fill=ORANGE, stroke_width=4, stroke_fill=(0, 0, 0))
    if t > Tl4:  # back muscle force, behind spine
        mx = spine_x - 30
        g = ease((t - Tl4) / 0.8)
        big = 1.0 if t < Tl5 else 1.0 + 0.9 * ease((t - Tl5) / 0.8)
        L = 110 * g * big
        arrow(d, (mx, k["hip"][1] + 10), (mx, k["hip"][1] + 10 - L), GREEN, w=int(14 * big), head=int(40 * big))
        d.text((spine_x - 300, k["hip"][1] - 120), "back\nmuscles", font=font(42), fill=GREEN, stroke_width=4, stroke_fill=(0, 0, 0))
        if t > Tl5 + 0.6:
            d.text((spine_x - 300, k["hip"][1] + 10), "HUGE", font=font(56), fill=GREEN, stroke_width=5, stroke_fill=(0, 0, 0))
    cur_caption(im, T)
    return im

def s4(t, T):  # shoulder carry
    im, d = R.base()
    d.text((90, 380), "ON YOUR SHOULDERS", font=font(56), fill=GREEN)
    k = carrier(d, 470, GY, lean=0.0, arms="up")
    top = rider_seated(d, k["neck"][0], k["neck"][1] - 30)
    spine_x = k["hip"][0]
    for yy in range(int(top[1]) - 120, GY, 34):
        d.line([(spine_x, yy), (spine_x, yy + 16)], fill=CYAN, width=5)
    weight_arrow(d, spine_x + 60, k["neck"][1] - 150, L=110)
    if t > 1.0:
        d.text((spine_x + 120, k["hip"][1] + 60), "distance ≈ 0", font=font(48), fill=CYAN, stroke_width=4, stroke_fill=(0, 0, 0))
    Tl7 = S[7] - S[6]
    if t > Tl7:
        torque_arc(d, spine_x, k["hip"][1], 170, 0.06)
        g = ease((t - Tl7 - 0.5) / 0.8)
        if g > 0:
            # compression through skeleton
            for yy in (k["neck"][1] + 50, k["hip"][1] - 70):
                arrow(d, (spine_x - 55, yy - 45 * g), (spine_x - 55, yy + 45 * g), YEL, w=10, head=30)
            d.text((spine_x - 330, k["hip"][1] - 190), "skeleton\ncarries it", font=font(44), fill=YEL, stroke_width=4, stroke_fill=(0, 0, 0))
    cur_caption(im, T)
    return im

def s5(t, T):  # wobble / center of mass
    im, d = R.base()
    d.text((90, 380), "THE CATCH", font=font(56), fill=ORANGE)
    sw = 40 * math.sin(t * 2.6)
    k = carrier(d, 520, GY, arms="up", sway=sw * 0.25)
    top = rider_seated(d, k["neck"][0], k["neck"][1] - 30, sway=sw * 0.6)
    # combined center of mass: high
    cx, cy = k["neck"][0] + sw * 0.35, k["neck"][1] - 10
    d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=ORANGE, outline=(0, 0, 0), width=4)
    d.text((cx + 40, cy - 30), "center of mass", font=font(42), fill=ORANGE, stroke_width=4, stroke_fill=(0, 0, 0))
    for yy in range(int(cy) + 30, GY, 34):
        d.line([(cx, yy), (cx, yy + 16)], fill=ORANGE, width=5)
    d.line([(470, GY + 20), (590, GY + 20)], fill=GREEN, width=10)
    d.text((420, GY + 40), "feet = base", font=font(40), fill=GREEN)
    cur_caption(im, T)
    return im

def s6(t, T):
    im, d = R.base()
    import random
    rr = random.Random(11)
    for i in range(80):
        x = rr.uniform(0, W); y = (rr.uniform(-H, H) + 140 * t) % H
        R.draw_confetto(d, x + 30 * math.sin(t * 3 + i), y, t * 6 + i, rr.choice(R.CONF_COLS), 14)
    f = font(84); s = "FOLLOW"; tw = d.textlength(s, font=f)
    d.text(((W - tw) / 2, 760), s, font=f, fill=YEL, stroke_width=8, stroke_fill=(0, 0, 0))
    caption(im, CAPS[9], 0.1, t, y=930, size=64)
    return R.fade(im, t, SCENES[-1][2] - SCENES[-1][1], fout=0.5)

FN = dict(s1=s1, s2=s2, s3=s3, s4=s4, s5=s5, s6=s6)

def frames(name):
    a, b = [(x[1], x[2]) for x in SCENES if x[0] == name][0]
    n0, n1 = int(round(a * FPS)), int(round(b * FPS))
    return [(i - n0) / FPS for i in range(n0, n1)], [i / FPS for i in range(n0, n1)]

def render(name):
    lt, gt = frames(name)
    os.makedirs("out", exist_ok=True)
    tmp = f"out/{name}.part.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                          "-pix_fmt", "yuv420p", "-f", "mp4", tmp], stdin=subprocess.PIPE)
    for t, T in zip(lt, gt):
        p.stdin.write(FN[name](t, T).convert("RGB").tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, f"out/{name}.mp4")

if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    if sys.argv[1] == "still":
        ims = []
        for a in sys.argv[2:]:
            nm, tt = a.split("@"); tt = float(tt)
            st = [x[1] for x in SCENES if x[0] == nm][0]
            ims.append(FN[nm](tt, st + tt).convert("RGB").resize((300, 533)))
        m = Image.new("RGB", (300 * len(ims), 533))
        for i, x in enumerate(ims): m.paste(x, (300 * i, 0))
        m.save("out/contact.png")
    else:
        for nm in sys.argv[2:]:
            render(nm)
