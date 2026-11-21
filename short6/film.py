"""Short 6 (REMAKE): 'In This Town, If You Forget A Name...' - shots, robust captions, renderer."""
import json, math, random, sys, os
sys.path.insert(0, 'src'); sys.path.insert(0, 'short2')
import numpy as np
from PIL import Image, ImageDraw
from world import *

TL = json.load(open("build/s6b/timeline.json")); P = TL["lines"]; FPS = 24
def ps(i): return P[i]["t0"]
def pe(i): return P[i]["t1"]
LEAD = 0.06
def cut(i): return ps(i) - LEAD
END = pe(25) + .55; DUR = END + .15
def talk(t, spk):
    for p in P:
        if p['spk'] == spk and p['t0'] - .02 <= t <= p['t1']: return .25 + .75 * abs(math.sin(t * 23))
    return None
def pulse(lt, t0, d=.25): return clamp(1 - (lt - t0) / d) if lt >= t0 else 0.0
def yaw_to(p, q): return math.degrees(math.atan2(q[0] - p[0], q[2] - p[2]))
def F(spk, t, **f):
    tk = talk(t, spk)
    if tk is not None: f = dict(f); f['talk'] = tk
    return f

# ---------------------------------------------------------------- cast
REDL = dict(shirt=(240, 50, 50), pants=(40, 60, 150), hair=(70, 44, 28), skin=(244, 198, 158), scale=.80, head=1.22, shoes=(250, 250, 250))
DEXL = dict(shirt=(30, 190, 170), pants=(50, 60, 110), hair=(60, 40, 30), skin=(240, 196, 158), scale=.82, head=1.18, sleeves='short', shoes=(250, 250, 250))
GARYL = dict(shirt=(140, 140, 158), pants=(60, 60, 80), hair=(40, 40, 48), skin=(236, 184, 140), scale=.80, head=1.16, sleeves='short', shoes=(40, 40, 50))
CHIEFL = dict(shirt=(255, 170, 40), pants=(70, 55, 55), hair=(50, 50, 55), skin=(232, 180, 138), scale=1.14, head=1.04, shoes=(30, 30, 35))
def red(sc, pos, yaw=0, pose=None, face=None, **o):
    L = dict(REDL); L['face'] = face or {}; L.update(o)
    c = character(sc, pos, yaw, pose, L, hero=True)
    sc.box(c['torso'] @ T(0, .75, .52), (.9, .5, .06), (255, 255, 255), shadow=False, bias=-.3)       # hoodie pocket
    sc.box(c['torso'] @ T(0, 2.0, -.62), (1.5, .7, .4), (200, 36, 40), shadow=False)                  # hood
    return c
def haze(sc, c, k, t=0):
    if k <= 0: return
    hp = xf(c['head'], [(0, 1.0, 0)])[0]
    w = 1.5 + .1 * math.sin(t * 8)
    sc.sprite(hp, w, w, (255, 255, 255), alpha=int(115 * k), bias=-2)
    sc.sprite(hp, w * .7, w * .7, (228, 228, 238), alpha=int(90 * k), bias=-2.1)
def dex(sc, pos, yaw=0, pose=None, face=None, blur=0.0, t=0, **o):
    L = dict(DEXL)
    if blur > 0:
        for k in ('shirt', 'pants', 'hair', 'skin', 'shoes'): L[k] = mix(L[k], (205, 205, 212), blur * .5)
    L['face'] = face if blur <= 0 else {}
    L.update(o)
    c = character(sc, pos, yaw, pose, L)
    haze(sc, c, blur, t)
    return c
def gary(sc, pos, yaw=0, pose=None, face=None, **o):
    L = dict(GARYL); L['face'] = face or {}; L.update(o)
    return character(sc, pos, yaw, pose, L)
def chief(sc, pos, yaw=0, pose=None, face=None, **o):
    L = dict(CHIEFL); L['face'] = face or {}; L.update(o)
    c = character(sc, pos, yaw, pose, L); h = c['head']
    k = (190, 40, 40)
    sc.box(h @ T(0, 1.44, 0), (1.4, .34, 1.4), k, shadow=False, bias=-.2)
    sc.box(h @ T(0, 1.66, 0), (1.72, .1, 1.72), k, shadow=False, bias=-.4)
    sc.box(h @ T(0, 1.72, 0), (1.1, .22, 1.1), (255, 214, 60), shadow=False, bias=-.5)
    sc.box(c['torso'] @ T(0, 1.5, .52), (.4, .9, .06), (255, 255, 255), shadow=False, bias=-.2)
    return c
def baker(sc, pos, yaw=0, pose=None, t=0, **o):
    L = dict(shirt=(220, 190, 140), pants=(90, 80, 70), hair=(90, 80, 70), skin=(236, 184, 140), scale=1.05, head=1.05, style='bald', sleeves='short')
    L['face'] = {}; L.update(o)
    c = character(sc, pos, yaw, pose, L)
    haze(sc, c, 1.0, t)
    return c
def kid(sc, pos, yaw=0, pose=None, face=None, **o):
    L = dict(shirt=(250, 150, 60), pants=(70, 90, 160), hair=(120, 70, 40), skin=(242, 194, 154), scale=.78, head=1.2, sleeves='short', shoes=(250, 250, 250))
    L['face'] = face or {}; L.update(o)
    return character(sc, pos, yaw, pose, L)
def nametag(sc, c, txt, s=.5, col=(250, 250, 255), tc=(30, 40, 90)):
    p = xf(c['torso'], [(0, 1.55, .53)])[0]
    sc.box(T(*p) @ RY(0), (.8 * s, .34 * s, .04), col, shadow=False, bias=-1.2)
    sc.text(p + V(0, 0, .03), txt, .30 * s, tc, stroke=(255, 255, 255, 160), sw=.05, bias=-1.4)

# ---------------------------------------------------------------- sets
def day(warm=0.0):
    if warm:
        sc = Scene(sun=(-.5, -.8, -.4), amb=.72, dif=.44, sky=((255, 150, 90), (255, 225, 170)), fog=((255, 210, 160), 60, 200, .8), shadow=.34, shadow_col=(120, 60, 40))
        sc.ambcol = (1.0, .9, .78)
    else:
        sc = Scene(sun=(-.45, -1, -.35), amb=.70, dif=.46, sky=((40, 140, 255), (170, 225, 255)), fog=((170, 225, 255), 50, 190, .8), shadow=.36)
    sc.lights = []; sc.glows = []; sc.lit = 1
    return sc
def town(sc, t, walkers=8):
    street(sc, t, on=lambda z: 1.0, day=True, strings=False, banner=False, hall=True)
    for i, z in enumerate((-9, -23, -37, -51)):
        for sd in (-1, 1): tree(sc, sd * 12.2, z + 3 * sd, .9 + .15 * (i % 2), night=False)
    r = random.Random(23)
    for i in range(walkers):
        sd = r.choice((-1, 1)); x = sd * r.uniform(7.0, 9.8); dr_ = r.choice((-1, 1)); sp = r.uniform(1.7, 2.8)
        z = ((r.uniform(0, 46) + dr_ * sp * t) % 46) - 52
        folk(sc, i + 30, (x, 0, z), 0 if dr_ > 0 else 180, walk(t + i * .3, 1.7, 28), lant=None, kid=(i % 4 == 2))
def bakery(sc, t):
    sc.box(T(0, 3.4, -4), (11, 6.8, .5), (230, 190, 130), decals=[('+z', [(rect(-3.4, .4, 6.8, 2.2), (90, 60, 40)), (rect(-3.4, .4, 6.8, .3), (250, 220, 160))])])
    sc.box(T(0, 5.2, -4.2), (11.4, 1.0, .9), (120, 70, 50))
    sc.text((0, 5.2, -3.7), "BAKER", 1.1, (255, 240, 200), stroke=(60, 30, 20), bias=-1)
    sc.box(T(-3.2, 1.1, -1.2), (2.6, 2.2, 1.2), (200, 160, 110))
    sc.box(T(-3.2, 2.35, -1.2), (2.6, .12, 1.2), (240, 210, 160), shadow=False)
    for i in range(4):
        sc.box(T(-4.4 + i * .7, 2.55, -1.0), (.55, .4, .5), (235, 170, 90), shadow=False, bias=-.4)
        sc.box(T(-4.4 + i * .7, 2.72, -1.0), (.5, .12, .45), (210, 140, 70), shadow=False, bias=-.5)
    glow(sc, (-2.2, 3.4, -1.2), 3, (255, 220, 140), .25)
def school(sc, t, broke=0.0):
    sc.box(T(0, 4, -6), (13, 8, 8), (235, 220, 200), decals=[('+z', [(rect(-4, .8, 8, 2.4), (70, 110, 190)), (rect(-4, .8, 8, .35), (255, 255, 255))])])
    sc.box(T(0, 6.2, -6.2), (13.4, 1.0, 8.4), (120, 70, 50))
    sc.text((0, 6.2, -5.7), "SCHOOL", 1.2, (255, 255, 255), stroke=(60, 40, 30), bias=-1)
    sc.box(T(0, 9.0, -6.2), (13.4, .8, 8.4), (150, 90, 70))
    if broke > 0:
        k = ease_out(broke)
        sc.box(T(lerp(0, 3.4, k), lerp(9.0, -.5, k), lerp(-6.2, -2.2, k)) @ RZ(k * 24), (13.4, .8, 8.4), (150, 90, 70))
    for sx in (-1, 1):
        sc.box(T(sx * 5.6, 0, -2), (.5, 8, .5), (120, 90, 70))
def rubble(sc, t, seed=7):
    r = random.Random(seed)
    for i in range(16):
        x = r.uniform(-5.5, 5.5); z = r.uniform(-4.5, 2.5); s = r.uniform(.7, 1.8)
        sc.box(T(x, s * .6, z) @ RY(r.uniform(0, 6)), (1.5 * s, 1.2 * s, 1.5 * s), r.choice([(120, 110, 100), (140, 120, 100), (100, 95, 90)]), bias=-.2)
    for i in range(7):
        sc.box(T(r.uniform(-4, 4), r.uniform(1.5, 3.5), r.uniform(-3.5, 1.5)) @ RY(r.uniform(0, 6)), (r.uniform(.5, 1.0), r.uniform(.5, 1.0), r.uniform(.5, 1.0)), (90, 80, 70), bias=-.4)
def dust(sc, p, t, n=6, up=3.0, col=(200, 190, 175)):
    for i in range(n):
        u = (t * .5 + i / n) % 1
        sc.sprite((p[0] + math.sin(u * 9 + i) * .8, p[1] + u * up, p[2] + math.cos(u * 7 + i) * .8), .5 + u * .7, .5 + u * .7, col, alpha=int(160 * (1 - u)), bias=-2)

# ---------------------------------------------------------------- overlays
BANG = "fonts/Bangers-Regular.ttf"; LG = "fonts/LuckiestGuy-Regular.ttf"
def bigtext(txt, pt, k, size=150, col=(255, 235, 70), rot=0, st=(20, 16, 50)):
    def f(dr):
        if k <= 0: return
        s = int(size * (.55 + .45 * ease_out(min(1, k * 5))) * (1 + .04 * math.sin(k * 22)))
        f_ = font(s, BANG)
        if rot:
            tmp = Image.new('RGBA', (int(s * len(txt) * .7) + 80, int(s * 1.6)), (0, 0, 0, 0)); d2 = ImageDraw.Draw(tmp)
            d2.text((tmp.width / 2, tmp.height / 2), txt, font=f_, fill=col + (255,), anchor='mm', stroke_width=int(s * .09), stroke_fill=st + (255,))
            tmp = tmp.rotate(rot, expand=True, resample=Image.BICUBIC); dr._image.paste(tmp, (int(pt[0] - tmp.width / 2), int(pt[1] - tmp.height / 2)), tmp)
        else: dr.text(pt, txt, font=f_, fill=col + (255,), anchor='mm', stroke_width=int(s * .09), stroke_fill=st + (255,))
    return f
def PP(**k):
    d = dict(sat=1.26, bloom=.42, vig=.18, con=1.06, tint=(1.03, 1.0, .97)); d.update(k); return d

# ---------------------------------------------------------------- shots
PULL = 1.55
class Cam2(Cam):
    def __init__(s, pos, target, fov=40, roll=0, pull=None):
        pos = V(*pos); target = V(*target); Cam.__init__(s, target + (pos - target) * (pull or PULL), target, fov, roll)

def A0(lt, d, t):       # 0-1: the rule
    sc = day(); town(sc, t)
    for i, z in enumerate((-6, -14, -22)):
        p = (lerp(-4.5, -2.5, ease_out(clamp(lt / 1.2))), 0, z + 2)
        folk(sc, i + 40, p, 180, walk(t + i * .4, 1.8, 26), lant=None, kid=(i % 3 == 0))
    red(sc, (-1.6, 0, 2.5), 12, walk(t, 1.6, 26), dict(eyes='open', mouth='smile', brows='up'))
    cam = Cam2(V(.2, 3.4, lerp(11, 7.2, ease_out(lt / d))), V(-1.4, 2.7, 1.5), 46)
    ov = [bigtext("IF YOU FORGET A NAME...", (W / 2, H * .16), lt - .1, 96, (255, 255, 255), 0, (20, 30, 90)),
          bigtext("THEIR FACE GOES BLURRY.", (W / 2, H * .25), lt - .7, 84, (255, 235, 70), 0, (20, 30, 90))]
    return sc, cam, PP(overlay=ov, flash=.2 * pulse(lt, .1, .1))
def A1(lt, d, t):       # 2-3: smudge gag
    sc = day(); bakery(sc, t)
    b = math.sin(t * 7)
    baker(sc, (-2.2, 0, -2.2), 0, dict(y=.04 * b, head=(math.sin(t * 3) * 6, 0)), t=t)
    kid(sc, (-4.0, 0, -1.0), 20, dict(al=(60 + 20 * b, 10), ar=(30, 30), head=(14, 4), y=.03 * b), dict(eyes='open', mouth='smile', brows='up'))
    k = ease_out(clamp((lt - .35) / .5))
    cam = Cam2(V(-1.2, 3.0, lerp(7.5, 6.0, k)), V(-2.6, 2.8, -2.0), 44)
    ov = [bigtext("SMUDGE", (W / 2, H * .15), lt - .5, 210, (255, 140, 60), 6, (40, 20, 10))]
    return sc, cam, PP(overlay=ov)
def B(lt, d, t):        # 4-7: I remember everyone
    sc = day(); school(sc, t, 0)
    tk = talk(t, 'R')
    red(sc, (-1.4, 0, 2.2), 20, dict(al=(70 + (20 if tk else 0), 10), ar=(30, 30), head=(8, 4), y=.03 * math.sin(t * 8)), F('R', t, eyes='smile', mouth='grin', brows='up'))
    for i, (x, z) in enumerate(((3.2, 3.0), (4.6, 1.2), (3.0, -1.4), (5.0, -3.2))):
        kk = kid(sc, (x, 0, z), yaw_to((x, 0, z), (-1.4, 0, 2.2)), idle(t, i), dict(eyes='open', mouth='smile'))
        nametag(sc, kk, ["SAM", "LISA", "TOM", "AMY"][i], .55)
    dex(sc, (1.6, 0, 2.6), -40, idle(t, 2), {}, blur=1.0, t=t)
    cam = Cam2(V(-.4, 3.2, lerp(7.8, 6.8, lt / d)), V(-.9, 3.0, 1.6), 42)
    return sc, cam, PP()
def C(lt, d, t):        # 8-9: I saw a blur
    sc = day(); school(sc, t, 0)
    b = math.sin(t * 8)
    dex(sc, (1.5, 0, 2.4), -35, dict(al=(40 + 30 * b, 10), ar=(40 + 30 * b, 10), head=(0, 4), y=.05 * abs(math.sin(t * 6))), {}, blur=1.0, t=t)
    red(sc, (-1.5, 0, 2.2), 20, dict(al=(70, 10), ar=(30, 30), head=(-14, 6), y=.03 * b), dict(eyes='wide', mouth='o', brows='up', look=(1, 0)))
    kk = ease_out(clamp(lt / .8))
    cam = Cam2(lerp(V(-.6, 3.3, 7.4), V(1.9, 3.6, 5.6), kk), lerp(V(-1.2, 3.0, 1.8), V(1.5, 3.1, 2.4), kk), 42)
    ov = [bigtext("...BUDDY?", (W / 2, H * .16), lt - .4, 130, (255, 255, 255), 0, (20, 30, 90))] if lt < d * .6 else []
    return sc, cam, PP(overlay=ov)
D_CRASH = .45
def DD(lt, d, t):       # 10-13: roof caves in, fire chief
    crash = lt >= D_CRASH; sh = ease_out((lt - D_CRASH) / .35)
    sc = day(); school(sc, t, 1.0 if crash else 0)
    if crash:
        dust(sc, (0, 2, -4), t - D_CRASH, 8, 4.2)
        for i in range(10):
            u = ((t * .9 + i * .31) % 1)
            sc.sprite((lerp(-4, 4, (i / 9)) + math.sin(u * 8) * .6, u * 5.5, lerp(-4, 1, (i / 9)) + math.cos(u * 7) * .6), .8 + u * .6, .8 + u * .6, (190, 180, 165), alpha=int(150 * (1 - u)), bias=-2)
    for i, (x, z) in enumerate(((-4.5, 4.5), (4.5, 4.5), (-5.0, 2.5), (5.0, 2.5))):
        folk(sc, i + 50, (x, 0, z), yaw_to((x, 0, z), (0, 0, 0)), dict(y=.05 * abs(math.sin(t * 10 + i)), al=(20, 40), ar=(20, 40), lean=-10), face=dict(eyes='wide', mouth='open', brows='up'), lant=None, kid=(i % 2 == 0))
    run_in = ease_out(clamp((lt - D_CRASH - .3) / .7))
    cp = (lerp(8.5, 3.4, run_in), 0, lerp(4.0, 2.0, run_in))
    chief(sc, cp, yaw_to(cp, (-1.2, 0, 2.0)), run(t, 2.6, 40) if run_in < 1 else dict(al=(30, -20), ar=(30, -20), lean=6, head=(0, -6)), dict(eyes='open', mouth='flat', brows='flat'))
    cam = Cam2(V(.6, 3.2, 8.6) + shake(t, .18 * pulse(lt, D_CRASH, .5)), V(0, 3.0, -1.0), 50)
    ov = [bigtext("CRASH!", (W / 2, H * .13), lt - D_CRASH, 300, (255, 235, 70), -6, (40, 20, 10))] if crash else []
    return sc, cam, PP(overlay=ov, flash=.45 * pulse(lt, D_CRASH, .1))
E_BASE = .5
def EE(lt, d, t):       # 14: shouts into the rubble
    sc = day(); rubble(sc, t)
    sh1 = lt >= E_BASE; sh2 = lt >= E_BASE + .85; sh3 = lt >= E_BASE + 1.7; deflated = lt >= E_BASE + 2.5
    b = math.sin(t * 9)
    shout = max(pulse(lt, E_BASE, .3), pulse(lt, E_BASE + .85, .3), pulse(lt, E_BASE + 1.7, .3))
    climb = ease_out(clamp(lt / E_BASE))
    pose = dict(ll=lerp(0, -40, climb), lr=lerp(0, 40, climb), al=(lerp(40, 110, climb), 10), ar=(lerp(40, 60, climb), 10), lean=lerp(0, 14, climb), head=(0, lerp(0, 26, climb)), y=.05 * b)
    if deflated: pose = dict(al=(30, 10), ar=(30, 10), lean=-8, head=(0, -10), y=-.03)
    red(sc, (-1.0, 0, 2.6), 18, pose, dict(eyes='wide' if not deflated else 'tired', mouth='o' if shout else ('frown' if deflated else 'flat'), brows='up' if not deflated else 'sad', look=(0, .3)))
    gary(sc, (3.6, 0, 3.4), -120, dict(y=.12 * abs(math.sin(t * 11)), al=(20, 40), ar=(20, 40), lean=-6), dict(eyes='happy', mouth='grin'))
    cam = Cam2(V(-.8, 3.0, lerp(7.6, 6.2, lt / d)) + shake(t, .05 * shout), V(-1.0, 2.9, 2.2), 44)
    ov = [bigtext("BUDDY!", (W / 2, H * .14), lt - E_BASE, 240, (255, 255, 255), 4, (20, 30, 90))] if sh1 and lt < E_BASE + .8 else \
         [bigtext("DUDE!", (W / 2, H * .14), lt - E_BASE - .85, 240, (255, 255, 255), -4, (20, 30, 90))] if sh2 and lt < E_BASE + 1.65 else \
         [bigtext("BEST FRIEND!", (W / 2, H * .14), lt - E_BASE - 1.7, 210, (255, 255, 255), 2, (20, 30, 90))] if sh3 and lt < E_BASE + 2.4 else []
    return sc, cam, PP(overlay=ov)
def FF(lt, d, t):       # 15-17: gary's line, red determined
    sc = day(); rubble(sc, t)
    if lt < d * .45:
        gary(sc, (1.2, 0, 2.8), 10, dict(y=.14 * abs(math.sin(t * 12)), al=(20, 50), ar=(20, 50), lean=-8, head=(0, 8)), F('G', t, eyes='happy', mouth='grin'))
        cam = Cam2(V(.4, 3.0, 6.6), V(1.2, 3.0, 2.8), 40)
        ov = [bigtext("HA!", (W * .7, H * .18), lt - .1, 150, (255, 235, 70), -8)]
    else:
        k = smooth((lt - d * .45) / .5)
        red(sc, (-1.2, 0, 2.8), 18, dict(al=(80, 10), ar=(40, 40), lean=6, head=(0, 10), y=.03 * math.sin(t * 9)), dict(eyes='open', mouth='flat', brows='up'))
        cam = Cam2(V(-.6, 3.0, lerp(7.0, 6.2, k)), V(-1.2, 2.9, 2.8), 42)
        ov = []
    return sc, cam, PP(overlay=ov)
def GG(lt, d, t):       # 18: flashback, first day
    sc = day(warm=1)
    school(sc, t, 0)
    b = math.sin(t * 7)
    red(sc, (-1.6, 0, 3.0), 25, idle(t, 1), dict(eyes='open', mouth='smile', brows='up'))
    dx = dex(sc, (1.2, 0, 3.2), -25, dict(al=(60 + 25 * b, 10), ar=(30, 30), head=(0, 4), y=.04 * b), dict(eyes='smile', mouth='grin'), blur=0.0, t=t)
    hp = tuple(dx['hand_r'])
    sc.box(T(*hp), (.8, .4, .3), (235, 180, 90), shadow=False, bias=-1)
    sc.box(T(hp[0], hp[1] + .42, hp[2]), (.75, .12, .26), (210, 150, 70), shadow=False, bias=-1.2)
    glow(sc, (0, 3.5, 3.0), 6, (255, 220, 150), .35)
    cam = Cam2(V(-.2, 3.1, lerp(7.2, 6.2, ease_out(lt / d))), V(0, 3.0, 3.0), 44)
    return sc, cam, PP(tint=(1.05, .98, .92), bloom=.35)
H_SNAP = .5
def HH(lt, d, t):       # 19-22: Dex! face snaps clear
    snap = lt >= H_SNAP; bl = 1 - ease_out(clamp((lt - H_SNAP) / .4))
    sc = day(); rubble(sc, t)
    if snap: dust(sc, (1.5, 1.5, 2.0), t - H_SNAP, 7, 3.5, (220, 210, 195))
    b = math.sin(t * 9)
    shout = pulse(lt, H_SNAP, .4)
    red(sc, (-1.2, 0, 2.6), 16, dict(al=(lerp(70, 130, shout), 10), ar=(30, 30), lean=lerp(0, 10, shout), head=(0, lerp(4, 22, shout)), y=.04 * b), dict(eyes='wide', mouth='o' if shout else 'grin', brows='up', look=(1, .2)))
    dex(sc, (1.5, 0, 2.4), -30, dict(y=.05 * abs(math.sin(t * 6)), al=(30, 30), ar=(30, 30), head=(0, 6)), dict(eyes='grin', mouth='grin', brows='up') if snap else {}, blur=bl, t=t)
    cam = Cam2(V(.2, 3.0, lerp(7.4, 5.9, clamp(lt / d))) + shake(t, .06 * shout), V(.1, 2.9, 2.3), 44)
    ov = [bigtext("DEX!", (W / 2, H * .12), lt - H_SNAP, 330, (255, 255, 255), 0, (20, 30, 90))] if shout else \
         [bigtext("CLEAR!", (W * .68, H * .19), lt - H_SNAP - .15, 200, (90, 255, 140), -6, (20, 60, 30))] if snap else []
    return sc, cam, PP(overlay=ov, flash=.5 * pulse(lt, H_SNAP, .1))
def II(lt, d, t):       # 23-25: chase + punchline
    sc = day(warm=1); town(sc, t, walkers=6)
    hid = lt > d * .35
    b = math.sin(t * 9)
    dex(sc, (lerp(1.5, 3.4, ease_out(clamp((lt - d * .35) / .6))), 0, 2.2), -40 if not hid else -75, dict(al=(30, 10), ar=(30, 10), head=(-20 if hid else 0, 4), y=.04 * b), dict(eyes='happy', mouth='grin', brows='up'), blur=0.0, t=t)
    red(sc, (lerp(-1.4, -2.6, ease_out(clamp(lt / .6))), 0, lerp(2.4, 2.2, lt / d)), 12, run(t, 2.4, 40), dict(eyes='happy', mouth='grin', brows='up'))
    for i, z in enumerate((-6, -14)):
        folk(sc, i + 60, ((i - .5) * 9, 0, z), 0, dict(y=.1 * abs(math.sin(t * 8 + i)), al=(20, 50), ar=(20, 50)), face=dict(eyes='happy', mouth='grin'), lant=None, kid=(i % 2 == 0))
    cam = Cam2(V(.0, 3.2, lerp(8.4, 6.6, lt / d)), V(.2, 2.9, 2.2), 48)
    k = clamp((lt - d * .75) / .25)
    ov = [bigtext("HIS FACE IS FINE.", (W / 2, H * .18), k, 96, (255, 255, 255), 0, (20, 30, 90)),
          bigtext("MINE ISN'T.", (W / 2, H * .27), max(0, k - .15), 110, (255, 235, 70), 0, (20, 30, 90))]
    return sc, cam, PP(overlay=ov, tint=(1.05, .97, .92), bloom=.4)

SHOTS = [(0, A0), (cut(2), A1), (cut(4), B), (cut(8), C), (cut(10), DD), (cut(12), EE), (cut(15), FF), (cut(17), GG), (cut(19), HH), (cut(23), II), (END, None)]

def events():
    ix = {fn.__name__: i for i, (t0, fn) in enumerate(SHOTS) if fn}; st = {n: SHOTS[i][0] for n, i in ix.items()}
    return dict(st=st, cuts=[t for t, f in SHOTS], end=END, dur=DUR, rule=st['A0'], smudge=st['A1'] + .5, roof=st['DD'] + D_CRASH,
                shout1=st['EE'] + E_BASE, shout2=st['EE'] + E_BASE + .85, shout3=st['EE'] + E_BASE + 1.7, laugh=st['FF'] + .2,
                flashback=st['GG'], dexclear=st['HH'] + H_SNAP, chase=st['II'], punch=st['II'] + 2.0)

# ================================================================ captions (robust, line-synced)
SPK = dict(R=((255, 255, 255), (255, 226, 50)), D=((150, 205, 255), (60, 150, 255)), G=((235, 235, 245), (150, 150, 170)))
def captions(img, t):
    show = None
    for p in P:
        if p['t0'] - .03 <= t < p['t1'] + .12 and t < END:
            show = p; break
    if show is None: return img
    spk = show['spk']; words = show['text'].split(); n = len(words)
    dur = max(.01, show['t1'] - show['t0'])
    def wt(i): return show['t0'] + dur * i / n, show['t0'] + dur * (i + 1) / n
    size = 104 if spk == 'R' else 108
    f = font(size, LG); dr = ImageDraw.Draw(img, 'RGBA')
    U = [w.upper() for w in words]
    widths = [dr.textlength(w, font=f) for w in U]; sp = size * .24
    lines = [[]]; lw = 0
    for i, wd in enumerate(widths):
        if lines[-1] and lw + wd > W * .86: lines.append([]); lw = 0
        lines[-1].append(i); lw += wd + sp
    line_h = size * 1.12
    y0 = int(H * .695) - (len(lines) - 1) * line_h
    maxw = max(sum(widths[i] for i in ln) + sp * (len(ln) - 1) for ln in lines)
    pad = size * .55
    dr.rounded_rectangle([(W - maxw) / 2 - pad, y0 - size * .4, (W + maxw) / 2 + pad, y0 + len(lines) * line_h + size * .12], size * .3, fill=(8, 8, 18, 155))
    base, hi = SPK[spk]
    y = y0
    for ln in lines:
        tw = sum(widths[i] for i in ln) + sp * (len(ln) - 1); x = (W - tw) / 2
        for i in ln:
            a, b_ = wt(i); act = a - .03 <= t < b_ + .03 or (i == n - 1 and t >= a)
            dr.text((x + 4, y + 6), U[i], font=f, fill=(0, 0, 0), anchor='ls', stroke_width=int(size * .1), stroke_fill=(0, 0, 0))
            dr.text((x, y), U[i], font=f, fill=hi if act else base, anchor='ls', stroke_width=int(size * .1), stroke_fill=(12, 12, 16))
            x += widths[i] + sp
        y += line_h
    return img

def shot_at(t):
    for i in range(len(SHOTS) - 1):
        if SHOTS[i][0] <= t < SHOTS[i + 1][0]: return i
    return None
def frame(t, caps=True):
    i = shot_at(t)
    if i is None or SHOTS[i][1] is None: return Image.new('RGB', (W, H), (0, 0, 0))
    t0, fn = SHOTS[i]; d = SHOTS[i + 1][0] - t0
    sc, cam, P_2 = fn(t - t0, d, t)
    img = post(sc.render(cam), sc, cam, P_2)
    return captions(img, t) if caps else img
def sheet(ims, out, cols=6):
    n = len(ims); cols = min(n, cols); rows = (n + cols - 1) // cols
    sh = Image.new('RGB', (cols * 270, rows * 480))
    for k, im in enumerate(ims): sh.paste(im.resize((270, 480)), ((k % cols) * 270, (k // cols) * 480))
    sh.save(out, quality=85)

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "sheet":
        ids = [int(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 and sys.argv[3] != 'all' else range(len(SHOTS) - 1)
        fr = float(sys.argv[2]); ims = []
        for i in ids:
            t0 = SHOTS[i][0]; d = SHOTS[i + 1][0] - t0
            try: ims.append(frame(t0 + d * fr))
            except Exception:
                import traceback; traceback.print_exc(); print("shot", i, SHOTS[i][1].__name__); ims.append(Image.new('RGB', (270, 480), (255, 0, 255)))
        sheet(ims, sys.argv[4])
    elif mode == "strip":
        sheet([frame(float(x)) for x in sys.argv[3:]], sys.argv[2])
    elif mode == "render":
        part, nparts = int(sys.argv[2]), int(sys.argv[3]); out = sys.argv[4]; os.makedirs(out, exist_ok=True)
        N_ = int(math.ceil(DUR * FPS)); only = None if len(sys.argv) < 6 else [int(x) for x in sys.argv[5].split(',')]
        for n in range(N_):
            if n % nparts != part: continue
            t = n / FPS
            if only is not None and shot_at(t) not in only: continue
            frame(t).save(f"{out}/{n:05d}.jpg", quality=92)
        print("done", part)
