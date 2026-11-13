"""The Kid Who Could Stop Time - shot definitions, grading, captions."""
import json, math, random, sys, os
import numpy as np
from PIL import Image, ImageDraw
from engine import *
from chars import *
from sets import *

TL = json.load(open("build/timeline.json")); P = TL["phrases"]; DUR = TL["duration"]; FPS = 24
def ps(i): return P[i]["t0"]
def pe(i): return P[i]["t1"]
def wt(i, j): return P[i]["words"][j]["t0"]
END = pe(38) + 0.04          # hard cut to black
LEAD = 0.07

# ---------------------------------------------------------------- characters
ELI = dict(shirt=(208, 52, 52), pants=(45, 60, 112), hair=(74, 46, 30), logo='clock', skin=(238, 190, 152))
def eli(stage, face=None, **o):
    L = dict(ELI)
    L.update({'kid': dict(scale=.72, head=1.18, sleeves='short'), 'teen': dict(scale=.9, head=1.07),
              'adult': dict(scale=.98), 'old': dict(scale=1.0, age=1.0, gray=1.0, head=1.12)}[stage])
    L['face'] = face or {}; L.update(o); return L
MAX = dict(shirt=(60, 150, 95), pants=(60, 60, 70), hair=(226, 186, 96), skin=(200, 150, 110), logo='stripe')
MOM = dict(shirt=(150, 96, 190), pants=(70, 80, 120), hair=(150, 72, 42), style='long', logo='apron', skin=(238, 190, 152))

def shake(t, a):
    return V(math.sin(t * 37.1) + .5 * math.sin(t * 71.3), math.sin(t * 43.7 + 1) + .5 * math.sin(t * 83.9), 0) * a

def bird(sc, x, y, z, yaw, flap):
    M = T(x, y, z) @ RY(yaw); c = (236, 236, 240)
    sc.box(M, (.55, .5, 1.3), c, shadow=False); sc.box(M @ T(0, .15, .75), (.4, .4, .4), c, shadow=False)
    sc.box(M @ T(0, .1, 1.02), (.14, .12, .2), (240, 170, 60), shadow=False)
    sc.box(M @ T(0, 0, -.8), (.4, .1, .5), (200, 200, 210), shadow=False)
    for sx in (-1, 1):
        sc.box(M @ T(sx * .25, .1, 0) @ RZ(sx * flap) @ T(sx * .75, 0, 0), (1.5, .1, .8), (214, 214, 224), shadow=False)

def yard_kids(sc, tw, bonk=None):
    spec = [(-2.6, -5.5, 30, 0.0), (3.0, -8, -20, .3), (-0.8, -11.5, 10, .6), (4.2, -13, -40, .1), (-4.2, -9, 50, .8)]
    for i, (x, z, yaw, ph) in enumerate(spec):
        pose = run(tw * .9 + ph); y = 0
        if i == 1: pose = dict(al=(170, 20), ar=(170, 20), ll=25, lr=-30, y=max(0, math.sin(min(tw, 3) * 2.2 + .4)) * 1.6)
        L = extra_look(i + 20, kid=True)
        if bonk is not None and i == 2:
            pose = dict(pitch=-70 * bonk, al=(120 * bonk, 30), ar=(120 * bonk, 30), y=.4 * bonk)
            if bonk > 0: L['face'] = dict(eyes='wide', mouth='o', brows='up')
        character(sc, (x, 0, z), yaw, pose, L)

def street_people(sc, tw, n=9, seed=2):
    r = random.Random(seed)
    for i in range(n):
        side = r.choice([-1, 1]); x = side * r.uniform(6.8, 9.2) if i % 3 else r.uniform(-4, 4)
        z0 = r.uniform(-34, 8); d = r.choice([-1, 1]); sp = r.uniform(2.2, 3.4)
        z = z0 + d * sp * tw
        if abs(x) < 6:
            z = -9 - (abs(z) % 26)
        character(sc, (x, 0, z), 0 if d > 0 else 180, walk(tw * .9 + r.random(), amp=34), extra_look(i + 40, kid=(i % 4 == 1)))
    car(sc, -3.2, -30 + 9 * tw, (220, 70, 60)); car(sc, 3.2, 26 - 8 * tw, (70, 130, 210), yaw=180); car(sc, -3.2, -62 + 9 * tw, (240, 200, 70))

def burst(pt, k, col=(255, 235, 120)):
    def f(dr):
        if not (0 <= k <= 1): return
        x, y = pt; a = int(255 * (1 - k))
        for i in range(10):
            an = i * math.pi / 5 + .3; r0 = 30 + 150 * k; r1 = r0 + 70 * (1 - k * .5)
            dr.line([x + math.cos(an) * r0, y + math.sin(an) * r0, x + math.cos(an) * r1, y + math.sin(an) * r1], fill=col + (a,), width=int(14 * (1 - k) + 3))
        dr.ellipse([x - 40 * (1 - k), y - 40 * (1 - k), x + 40 * (1 - k), y + 40 * (1 - k)], fill=(255, 255, 255, a))
    return f
def px(cam, p):
    c = cam.to_cam(p)
    if c[2] < .05: return (W / 2, H / 2)
    (x, y), = cam.proj([c]); return (x / SS, y / SS)
def wave(cam, p, k, inv=False):
    return dict(c=px(cam, p), r=ease_out(k) * 2500 if k < 1 else 1e6, inv=inv)

# ---------------------------------------------------------------- shots
S1_TF = 0.55                  # the snap lands half a second in: the premise is SHOWN before it is said
S1_STEP = 1.90                # Eli strolls out of the ball's path
S1_WINK = wt(1, 3) - .02      # "...time." -> looks straight at the viewer
def speedlines(k, seed):
    def f(dr):
        r = random.Random(seed)
        for i in range(46):
            an = r.uniform(0, 2 * math.pi); r0 = r.uniform(560, 900); r1 = r0 + r.uniform(200, 700)
            cx, cy = W / SS / 2, H / SS * .40
            dr.line([(cx + math.cos(an) * r0, cy + math.sin(an) * r0 * 1.5), (cx + math.cos(an) * r1, cy + math.sin(an) * r1 * 1.5)],
                    fill=(255, 255, 255, int(190 * k)), width=r.choice([3, 5, 8]))
    return f
def S1(lt, d, t):
    tf = S1_TF; tw = min(lt, tf); u = tw / tf; af = lt - tf
    sc = Scene(fog=FOG_DAY, sky=sky_day()); yard(sc); yard_kids(sc, tw + 1.25)
    sx = smooth((lt - S1_STEP) / .42); wk = smooth((lt - S1_WINK) / .16)
    if af < .30: face = dict(eyes='wide', mouth='o', brows='up')
    elif af < .85: face = dict(eyes='open', mouth='o', brows='up')
    elif wk > .5: face = dict(eyes='happy', mouth='grin')
    else: face = dict(eyes='open', mouth='grin')
    rel = smooth((af - .55) / .5)                       # he relaxes once he realises it worked
    hop = math.sin(clamp((lt - S1_STEP) / .42) * math.pi)
    pose = dict(ar=(lerp(lerp(70, 116, smooth(u * 1.5)), 96, sx), 18), al=(lerp(62, 6, rel), lerp(26, 6, rel)), lean=lerp(-10, 0, rel),
                roll=-9 * hop, y=.28 * hop, ll=18 * hop, lr=-14 * hop,
                head=(lerp(0, -14, wk), lerp(0, -4, rel) * (1 - wk)))
    c = character(sc, (-1.2 * sx, 0, 0), 0, pose, eli('kid', face), hero=True)
    b0 = V(.95, 3.55, 7.6); b1 = V(.1, 3.02, 1.22)
    nud = ease_out((lt - S1_STEP - .34) / .5)             # a little flick once he is clear
    b = lerp(b0, b1, u ** .9) + V(.42 * nud, .10 * math.sin(nud * math.pi), 0)
    dn = (b0 - b1) / np.linalg.norm(b0 - b1)
    for i in range(1, 7):
        sc.sprite(b + dn * (.34 * i * (.5 + .5 * u)), .50 - .05 * i, .50 - .05 * i, (255, 120, 110), alpha=int((120 - 17 * i) * (1 - nud)), bias=-.2)
    sc.sprite(b, .54, .54, (225, 55, 55), hi=(255, 150, 150), shadow=True, bias=-.3)
    r = random.Random(4)
    for i in range(16):                                   # turf kicked up by his flinch, left hanging in the air
        an = r.uniform(0, 6.28); rr = r.uniform(.5, 1.5); h = r.uniform(.3, 1.9) * (u ** .5); sz = r.uniform(.08, .17)
        sc.box(T(math.cos(an) * rr * (.5 + .5 * u), .1 + h, math.sin(an) * rr * (.5 + .5 * u) + .2) @ RY(i * 40) @ RX(i * 25 + tw * 300), (sz, sz, sz),
               r.choice([(98, 172, 86), (120, 92, 60), (80, 150, 72)]), shadow=False)
    for i in range(3 if af < .9 else 0):                  # sweat drops
        sc.sprite(V(-.75 - .12 * i, 4.35 - .22 * i - .4 * (1 - u), .55), .07, .10, (170, 220, 255), hi=(255, 255, 255), bias=-.4)
    a0 = math.atan2(2.2, 5.2); r0 = math.hypot(2.2, 5.2)
    if af < 0:
        cam = Cam(V(lerp(2.9, 2.2, u), 3.2, lerp(7.0, 5.2, u)) + shake(t, .06), (0, 3.0, .6), fov=lerp(52, 43, u))
    else:
        k = 1 - math.exp(-af * 2.6)                       # whip around, then drift (bullet time)
        sw = smooth((lt - S1_STEP + .12) / .6)
        a = a0 + math.radians(lerp(0, 30, k) - 72 * sw); rr = lerp(r0, 6.3, k) - 1.9 * wk
        tg = lerp(V(0, 3.0, .6), V(-1.2, 3.55, .1), max(sx * .55, wk * .9))
        cam = Cam((math.sin(a) * rr + tg[0], lerp(3.2, 3.5, wk), math.cos(a) * rr), tg, fov=43)
    post = {}
    if af < 0:
        post['overlay'] = [speedlines(.55 + .45 * u, int(t * FPS))]
    else:
        post.update(freeze=wave(cam, c['hand_r'], af / .40), flash=max(0, .6 - af * 3.2), overlay=[burst(px(cam, c['hand_r']), af / .3)])
    return sc, cam, post

def S2a(lt, d, t):
    ts = d - .30; tw = min(lt, ts); af = lt - ts
    sc = Scene(fog=FOG_DAY, sky=sky_day()); street(sc); street_people(sc, tw + 1)
    k = smooth(lt / (ts - .12))
    c = character(sc, (1.3, 0, 0), 0, dict(ar=(lerp(20, 118, k), 22), head=(8, 0)), eli('kid', dict(eyes='open', mouth='smile', brows='flat')), hero=True)
    cam = Cam((lerp(3.2, 2.9, lt / d), 3.3, lerp(8.6, 7.6, lt / d)), (1.0, 2.75, 0), fov=40)
    post = {}
    if af >= 0: post = dict(freeze=wave(cam, c['hand_r'], af / .5), flash=max(0, .5 - af * 3), overlay=[burst(px(cam, c['hand_r']), af / .3)])
    return sc, cam, post

def S2b(lt, d, t):
    sc = Scene(fog=FOG_DAY, sky=sky_day()); street(sc); street_people(sc, 1 + P[2]['t1'] - P[2]['t0'])
    character(sc, (-2.4, 0, -5), 20, dict(al=(150, 30), ar=(150, 30), ll=40, lr=-20, y=1.5, pitch=-10), extra_look(77, kid=True))   # kid frozen mid-jump
    bx(sc, -2.4, .9, -5, 1.0, .18, 3.0, (60, 60, 70), yaw=20)
    u = lt / d
    character(sc, (0, 0, lerp(0, 2.2, u)), 0, dict(walk(lt * .7, amp=24), head=(math.sin(lt * 2.4) * 45, 8)), eli('kid', dict(eyes='open', mouth='grin')), hero=True)
    cam = Cam((lerp(2.5, 5, smooth(u)), lerp(4.5, 10.5, smooth(u)), lerp(12, 20, smooth(u))), (0, 3.2, -5), fov=50)
    return sc, cam, dict(freeze=dict(c=px(cam, (0, 3, 0)), r=900 + lt * 5000))

def S2c(lt, d, t):
    sc = Scene(fog=FOG_DAY, sky=sky_day()); street(sc, clock=False); u = lt / d
    r = random.Random(11)
    for i in range(9):
        bird(sc, r.uniform(-4.5, 4.5), r.uniform(8, 15.5), r.uniform(-12, 1), r.uniform(-60, 60), r.choice([-35, -10, 20, 40]))
    character(sc, (0, 0, 0), 15, dict(al=(lerp(60, 158, smooth(u * 2)), 8), head=(0, 38)), eli('kid', dict(eyes='wide', mouth='open')), hero=True)
    a = lerp(.25, .5, u)
    cam = Cam((math.sin(a) * 7.5, 1.3, math.cos(a) * 7.5), (0, lerp(5.2, 6.0, u), -2.5), fov=60)
    return sc, cam, dict(freeze=1)

def S2d(lt, d, t):
    sc = Scene(fog=((128, 138, 160), 25, 110, .92), sky=((66, 76, 104), (128, 138, 160)), amb=.6, dif=.3, shadow=.2); street(sc, rain=True, clock=False); u = lt / d
    street_people(sc, 3.3, n=6, seed=8)
    ez = lerp(-3.2, -.6, u); r = random.Random(4)
    c = character(sc, (0, 0, ez), 0, dict(walk(lt * .8, amp=22), ar=(lerp(40, 96, smooth(u * 1.6)), 10), head=(-10, 12)), eli('kid', dict(eyes='open', mouth='smile')), hero=True)
    for i in range(190):
        x, y, z = r.uniform(-5.5, 5.5), r.uniform(.4, 10), r.uniform(-14, 6)
        if abs(x) < 1.5 and z > ez - .9 and y < 4.6: continue
        sc.sprite((x, y, z), .085, .15, (170, 215, 255), hi=(245, 250, 255))
    h = c['hand_r']; k = clamp((u - .62) * 4)
    sc.sprite((h[0] + .1 + k * .8, h[1] + .15 + k * .9, h[2] + .45 + k * 1.2), .13 + .05 * math.sin(lt * 30) * (1 - k), .2, (190, 228, 255), hi=(255, 255, 255))
    cam = Cam((lerp(-1.8, -1.2, u), 3.1, lerp(5.6, 4.6, u)), (0, 3.0, -1), fov=44)
    return sc, cam, dict(freeze=1, cold=.6)

def S2e(lt, d, t):
    sc = Scene(amb=.68, dif=.36, sky=((250, 232, 190),) * 2, sun=(-.3, -1, -.5)); kitchen(sc); u = lt / d
    character(sc, (-1.4, 0, -1.6), 12, dict(ar=(88, 12), al=(18, 28), lean=10, head=(0, -6)), dict(MOM, face=dict(eyes='open', brows='angry', talk=.95)))
    sc.text((.5, 7.5, -1.6), "CLEAN YOUR RO—", .7, (40, 40, 50), bg=(255, 255, 255), pad=.3, fontpath="fonts/Fredoka.ttf")
    table(sc, -6.5, 1.5, w=5, d=4)
    e = smooth(u)
    character(sc, (lerp(1.6, 3.4, e), 0, lerp(.6, 3.4, e)), 35, dict(walk(lt * 1.3, amp=30), al=(70, 12), ar=(70, 12), head=(lerp(-70, -30, u), 0), y=.12), eli('kid', dict(eyes='happy', mouth='grin')), hero=True)
    cam = Cam((lerp(2.4, 3.0, u), 4.6, lerp(16.5, 15, u)), (.6, 3.9, 0), fov=44)
    return sc, cam, dict(freeze=1)

def S3a(lt, d, t):
    sc = Scene(fog=FOG_DAY, sky=sky_day()); yard(sc); yard_kids(sc, wt(1, 2) + .65); u = lt / d
    sc.sprite((.1, 3.02, 1.25), .52, .52, (225, 55, 55), hi=(255, 150, 150), shadow=True)
    j = abs(math.sin(lt * 5.2)); s = math.sin(lt * 10.4) * 25
    character(sc, (2.4, 0, 3.4), lerp(-20, 30, u), dict(al=(170, 42 + s), ar=(170, 42 - s), y=j * 1.3, ll=j * 25, lr=-j * 25, head=(0, 10)), eli('kid', dict(eyes='happy', mouth='grin')), hero=True)
    a = math.radians(lerp(-25, 45, smooth(u))); cam = Cam((2.4 + math.sin(a) * 8.6, 1.9, 3.4 + math.cos(a) * 8.6), (2.2, 3.3, 3), fov=50)
    return sc, cam, dict(freeze=1)

def seated(sc, x, z, look, pose=None, hero=False, yaw=0):
    s = look.get('scale', 1); p = dict(ll=88, lr=88, y=1.25 / s - 2, al=(62, 8), ar=(62, 8), head=(0, -18)); p.update(pose or {})
    return character(sc, (x, 0, z), yaw, p, look, hero=hero)

def S3b(lt, d, t):
    sc = Scene(amb=.68, dif=.36, sky=((226, 232, 214),) * 2, sun=(-.3, -1, -.5)); classroom(sc); u = lt / d
    sc.text((0, 11.2, -9.6), "MATH TEST", 1.5, (240, 240, 230))
    i = 0
    for z in (0, -4.6, -9.2):
        for x in (-4.6, 0, 4.6):
            desk(sc, x, z + 1.2); i += 1
            sc.box(T(x + .2, 2.15, z + 1.2), (1.3, .05, 1.7), (250, 250, 250), shadow=False, bias=-.5)
            if (x, z) == (0, 0): continue
            seated(sc, x, z - .5, extra_look(i + 60, kid=True, face=dict(eyes='closed' if i % 2 else 'open', mouth='flat')))
    k = smooth(u * 2.2)
    seated(sc, 0, -.5, eli('kid', dict(eyes='open', mouth='grin' if u > .5 else 'smile', look=(1, 0))), dict(roll=-20 * k * (1 - smooth((u - .55) * 4)), head=(48 * k * (1 - smooth((u - .55) * 4)), -4), ar=(64 + 6 * math.sin(lt * 30), 8)), hero=True)
    if u > .55:
        g = ease_out((u - .55) * 5)
        sc.text((1.6, 4.9 + g * .8, 1.4), "A+", .95 * g + .01, (235, 50, 50), stroke=(255, 255, 255), sw=.14, bias=-3)
    cam = Cam((lerp(-1.6, -1.0, u), 4.7, lerp(9.4, 8.4, u)), (.7, 3.0, -.2), fov=44)
    return sc, cam, dict(freeze=1)

def S3c(lt, d, t):
    ts = d * .5; af = lt - ts; u = lt / d
    sc = Scene(fog=FOG_DAY, sky=sky_day()); yard(sc)
    bz = 1.25 if af < 0 else 1.25 - 60 * af
    bonk = None if af < 0 else clamp((af - .13) * 5)
    if bz < -11.5: bz = -11.5 + (af - .2125) * 9; by = 3.02 + (af - .2125) * 14 - (af - .2125) ** 2 * 40
    else: by = 3.02
    yard_kids(sc, wt(1, 2) + .65 + max(0, af), bonk=bonk)
    sc.sprite((.1, max(.5, by), bz), .52, .52, (225, 55, 55), hi=(255, 150, 150), shadow=True)
    k = smooth(lt / (ts - .1)); hop = math.sin(clamp(lt / (ts - .1)) * math.pi)
    face = dict(eyes='open', mouth='smile') if af < .15 else dict(eyes='happy', mouth='grin')
    c = character(sc, (-2.0 * k, 0, 0), 0, dict(y=hop * .5, al=(10, 10 + hop * 30 + (40 if af > .2 else 0)), ar=((112 if af < .1 and af > -.25 else 10), 18 + (40 if af > .2 else 0)), head=(lerp(30, 35, u), 0), ll=hop * 20, lr=-hop * 20), eli('kid', face), hero=True)
    cam = Cam((lerp(3.6, 2.6, u), 3.6, lerp(7.2, 6.6, u)), (-2.0 * k * .8 - .2, 2.8, -.8), fov=50)
    post = dict(freeze=1) if af < 0 else dict(freeze=wave(cam, c['hand_r'], af / .35, inv=True), flash=max(0, .4 - af * 3), overlay=[burst(px(cam, c['hand_r']), af / .3)])
    if af >= .35: post['freeze'] = 0
    return sc, cam, post

def S3d(lt, d, t):
    sc = Scene(amb=.68, dif=.36, sky=((250, 232, 190),) * 2, sun=(-.3, -1, -.5)); kitchen(sc); u = lt / d
    table(sc, 0, -1.2, w=6.6, d=2.8, h=2.1)
    sc.box(T(-.2, 2.4, -1.2), (2.4, .2, 2.4), (214, 170, 110), shadow=False, decals=[('+y', [(ell(0, 0, 1.05, 1.05, 20), (236, 220, 190))])])
    character(sc, (-1.9, 0, -3.9), 14, dict(al=(84, -8), ar=(84, -8), lean=26, head=(0, -4)), extra_look(31, kid=True, face=dict(eyes='happy', mouth='grin')))
    k = smooth(u * 3.4); lift = smooth((u - .32) * 2.8); bite = u > .66
    face = dict(eyes='happy', talk=.5 + .5 * math.sin(lt * 16)) if bite else dict(eyes='open', mouth='grin' if lift < .8 else 'open')
    c = character(sc, (1.9, 0, -3.7), -10, dict(ar=(lerp(20, 80, k) + lift * 62, lerp(0, 24, lift)), al=(5, 8), lean=lerp(0, 24, k) * (1 - lift), head=(lerp(0, 8, lift), 0)), eli('kid', face), hero=True)
    sp = lerp(V(.3, 2.6, -1.3), c['hand_r'] + V(.35, .15, .3), clamp(k * 1.4 - .3) if lift == 0 else 1)
    n0 = len(sc.objs)
    sc.box(T(*sp) @ RY(lerp(15, -30, lift)) @ RX(lerp(0, -22, lift)), (.95 * (1 - .45 * clamp((u - .7) * 3)), .14, 1.3), (246, 200, 90), shadow=False, bias=-.8, decals=[('+y', [(ell(-.2, .3, .2, .2, 8), (200, 60, 50)), (ell(.25, -.2, .2, .2, 8), (200, 60, 50)), (ell(-.1, -.5, .17, .17, 8), (200, 60, 50))])])
    sc.mark_hero(n0)
    cam = Cam((lerp(.8, 1.2, u), lerp(6.6, 6.0, u), lerp(7.6, 6.8, u)), (.9, 3.4, -3.2), fov=44)
    return sc, cam, dict(freeze=1)

def S4a(lt, d, t):
    sc = Scene(fog=FOG_DAY, sky=sky_day()); street(sc); street_people(sc, lt + 5, seed=6); u = lt / d
    g = smooth(u * 1.15); z = lerp(-6, -1, u)
    L = eli('kid', dict(eyes='open', mouth='smile')); L.update(scale=lerp(.72, .9, g) * (1 + .04 * math.sin(g * math.pi * 3) * (1 - g)), head=lerp(1.18, 1.07, g), sleeves='short' if g < .5 else 'long')
    character(sc, (0, 0, z), 0, walk(lt * 1.25), L)
    cam = Cam((1.2, lerp(3.2, 4.0, g), z + 8.6), (0, lerp(2.5, 3.2, g), z), fov=42)
    return sc, cam, dict(flash=max(0, .35 - lt * 2.5))

def snap_close(lt, d, stage, setname, look=None, seedt=0, cut_flash=True):
    ts = d * .42; af = lt - ts
    if setname == 'yard':
        sc = Scene(fog=FOG_DAY, sky=sky_day()); yard(sc); yard_kids(sc, min(lt, ts) + .5 + seedt)
    elif setname == 'class':
        sc = Scene(amb=.68, dif=.36, sky=((226, 232, 214),) * 2, sun=(-.3, -1, -.5)); classroom(sc)
        for i, (x, z) in enumerate(((-4.6, -4), (4.6, -4), (0, -8))): desk(sc, x, z + 1.2); seated(sc, x, z - .5, extra_look(i + 90))
    elif setname == 'street':
        sc = Scene(fog=FOG_DAY, sky=sky_day()); street(sc); street_people(sc, min(lt, ts) + 2 + seedt, seed=3)
    else:
        sc = Scene(amb=.68, dif=.36, sky=((250, 232, 190),) * 2, sun=(-.3, -1, -.5)); kitchen(sc); table(sc, -5, -1)
    L = eli(stage, dict(eyes='open' if af < .08 else 'happy', mouth='smile' if af < .08 else 'grin', brows='flat')); L.update(look or {})
    s = L['scale']; k = smooth(lt / (ts - .05))
    c = character(sc, (0, 0, 2), 0, dict(ar=(lerp(40, 120, k), 22), head=(8, 0)), L, hero=True)
    hy = 4.45 * s
    cam = Cam((2.0, hy - .2, 2 + 8.2 * (.7 + .3 * s) - lt * .6), (-.45, hy - .95, 2), fov=40)
    post = dict(flash=max(0, .3 - lt * 3) if cut_flash else 0)
    if af >= 0: post = dict(freeze=wave(cam, c['hand_r'], af / .3), flash=max(0, .45 - af * 4), overlay=[burst(px(cam, c['hand_r']), af / .25)])
    return sc, cam, post

def S4b(lt, d, t):
    n = 3; seg = d / n; i = min(n - 1, int(lt / seg))
    return snap_close(lt - i * seg, seg, 'teen', ['yard', 'class', 'kitchen'][i], seedt=i)

def bed(sc):
    bx(sc, 0, .8, -1.6, 6.2, 1.6, 10.4, (120, 84, 60), layer=0, bias=3); bx(sc, 0, 1.75, -1.6, 5.8, .5, 10, (245, 245, 240), shadow=False, layer=0)
    bx(sc, 0, 2.2, -5.4, 4.2, .5, 2.2, (255, 255, 255), shadow=False, layer=0, bias=-6)
    bx(sc, 0, 3, -6.75, 6.4, 6, .5, (120, 84, 60), layer=0)
    bx(sc, 4.9, 1.5, -5.3, 2.4, 3, 2.4, (140, 100, 70))

def S4c(lt, d, t):
    sc = Scene(amb=.6, dif=.34, sky=((86, 96, 150),) * 2, sun=(.3, -1, -.5), shadow=.25); bedroom(sc); bed(sc); u = lt / d
    ts = d * .42; af = lt - ts; ring = af < 0
    jx = math.sin(lt * 70) * .08 if ring else 0
    bx(sc, 4.9 + jx, 3.5, -5.2, 2.0, 1.0, 1.0, (40, 42, 50), shadow=False, yaw=-12)
    sc.text((4.8 + jx, 3.5, -4.6), "6:59", .62, (255, 80, 60), bias=-2)
    if ring:
        for i in range(3): sc.text((4.9 + (i - 1) * 1.0, 4.8 + .3 * math.sin(lt * 20 + i), -5), "!", .9, (255, 220, 80), stroke=(60, 40, 0), bias=-2)
    k = smooth(lt / (ts - .05)); drop = smooth(af * 2.5) if af > .25 else 0
    L = eli('teen', dict(eyes='closed', mouth='flat' if af < .2 else 'smile'), streak=.25)
    c = character(sc, (0, 2.45, -.6), 0, dict(pitch=-90, ar=(lerp(0, 86, k) * (1 - drop), 6), al=(0, 4)), L, hero=True, shadow=False)
    bx(sc, 0, 2.75, .1, 6.0, 1.5, 6.4, (70, 110, 200), shadow=False, bias=-2.5)
    if af > .5:
        for i in range(3):
            q = (af - .5 - i * .22)
            if q > 0: sc.text((-.9 - i * .5 - q * .4, 4.2 + i * .9 + q * 1.2, -4.6), "Z", .6 + i * .25, (255, 255, 255), stroke=(40, 50, 110), bias=-3)
    cam = Cam((lerp(8.2, 7.4, u), lerp(8.6, 8.0, u), lerp(-.4, -1.0, u)), (.6, 3.0, -3.7), fov=46)
    post = dict(tint=(.88, .92, 1.1))
    if af >= 0: post.update(freeze=wave(cam, c['hand_r'], af / .35), flash=max(0, .4 - af * 4), overlay=[burst(px(cam, c['hand_r']), af / .25)])
    return sc, cam, post

def S4d(lt, d, t):
    sc = Scene(amb=.62, dif=.36, sky=((86, 96, 150),) * 2, sun=(.3, -1, -.5), shadow=.25); bedroom(sc); u = lt / d
    table(sc, 0, 1.6, w=8, d=3.6, h=2.7)
    L = eli('teen', dict(eyes='open', mouth='flat', brows='flat', look=(0, -1)), streak=.4)
    seated(sc, -.9, -.9, L, dict(ar=(66 + 5 * math.sin(lt * 26), 10), al=(66, 10), head=(math.sin(lt * 3) * 6, -12), y=1.9 / .9 - 2), hero=True)
    n0 = len(sc.objs)
    sc.box(T(-.9, 2.92, 1.2), (2.4, .08, 1.6), (250, 250, 250), shadow=False, bias=-1)
    nb = 1 + int(u * 11); r = random.Random(3)
    for i in range(nb):
        col = r.choice(PAL_S); dx = r.uniform(-.15, .15); pop = 1 if i < nb - 1 else ease_out((u * 11) % 1 * 2)
        sc.box(T(2.3 + dx, 3.08 + i * .42 + (1 - pop) * 1.2, 1.6) @ RY(r.uniform(-12, 12)), (1.7, .4, 2.2), col, shadow=False, bias=-1 - i * .05, decals=[('+z', [(rect(0, 0, 1.5, .2), (250, 250, 245))])])
    sc.mark_hero(n0)
    bx(sc, -3.3, 3.6, 1.2, .3, 1.6, .3, (60, 60, 70)); bx(sc, -3.0, 4.5, 1.4, 1.2, .5, 1.0, (250, 210, 90), unlit=True)
    cam = Cam((lerp(1.6, 2.4, u), lerp(5.8, 6.2, u), lerp(13, 12, u)), (.5, lerp(4.2, 4.6, u), .6), fov=44)
    return sc, cam, dict(freeze=1, tint=(.9, .94, 1.08))

def S4e(lt, d, t):
    sc = Scene(fog=FOG_DAY, sky=sky_day()); street(sc); street_people(sc, 7.7, n=12, seed=12); u = lt / d
    r = random.Random(2)
    for i in range(6): bird(sc, r.uniform(-5, 5), r.uniform(7, 12), r.uniform(-20, -4), r.uniform(-60, 60), r.choice([-30, 10, 35]))
    character(sc, (0, 0, lerp(3, -2.5, u)), 180, dict(walk(lt * .62, amp=22), head=(math.sin(lt * 1.6) * 20, -8)), eli('adult', dict(eyes='open', mouth='flat'), streak=.6, scale=.95), hero=True)
    cam = Cam((lerp(1.5, 3, smooth(u)), lerp(4.2, 15, smooth(u)), lerp(13, 21, smooth(u))), (0, 3, lerp(-3, -9, u)), fov=50)
    return sc, cam, dict(freeze=1, sat=.92)

def bench_scene(lt, u, age, cam):
    sc = Scene(fog=FOG_DAY, sky=sky_day()); street(sc); street_people(sc, 7.7, n=12, seed=12)
    bench(sc, 8.4, 0, yaw=-90)
    character(sc, (7.6, 0, 5.2), 180, walk(.33), extra_look(51)); character(sc, (9.3, 0, -5.5), 0, walk(.6), extra_look(52)); character(sc, (6.9, 0, -9), 0, walk(.1), extra_look(55, kid=True))
    L = eli('adult', dict(eyes='sad' if age < .55 else 'tired', mouth='flat' if age < .7 else 'frown', brows='sad'), streak=clamp(.75 + age), gray=smooth(age * 1.1), age=age, scale=lerp(.95, 1.0, age))
    seated(sc, 8.4, 0, L, dict(al=(34, 14), ar=(34, 14), head=(0, lerp(-14, -24, age)), y=1.14 / L['scale'] - 2, lean=lerp(4, 12, age)), hero=True, yaw=-90)
    return sc

def S4f(lt, d, t):
    u = lt / d; cam = Cam((lerp(.6, 1.5, u), 3.7, lerp(5.4, 4.6, u)), (8.0, 2.9, .1), fov=42)
    return bench_scene(lt, u, 0, cam), cam, dict(freeze=1, sat=.85, vig=.25)

GRAD_WARM = dict(tint=(1.06, 1.0, .9), sat=1.12)
def grad_crowd(sc, lt, rows=5, zfar=-20, toward=180):
    r = random.Random(21); i = 0
    for z in np.linspace(-7, zfar, rows):
        for x in np.linspace(-9, 9, 6):
            i += 1; j = max(0, math.sin(lt * 5 + i)) * .6 if i % 3 == 0 else 0
            pose = dict(al=(165, 20), ar=(165, 20), y=j) if i % 3 == 0 else idle(lt, i)
            character(sc, (x + r.uniform(-.6, .6), 0, z + r.uniform(-.6, .6)), toward, pose, extra_look(100 + i, gown=True))
    return r

def S5a(lt, d, t):
    sc = Scene(fog=FOG_DAY, sky=sky_day()); grad(sc); u = lt / d; r = grad_crowd(sc, lt)
    for i in range(12):
        ph = (lt * .55 + i * .083) % 1; x = r.uniform(-9, 9); z = r.uniform(-19, -7)
        sc.box(T(x, 6 + 20 * ph * (1 - ph) * 1.3, z) @ RY(ph * 500 + i * 40) @ RX(ph * 300), (1.9, .1, 1.9), (34, 38, 68), shadow=False)
    cam = Cam((lerp(-2, 1, u), lerp(13, 7.5, smooth(u)), lerp(15, 7, smooth(u))), (0, lerp(7, 8, u), -22), fov=52)
    return sc, cam, dict(GRAD_WARM, flash=max(0, .5 - lt * 2))

def grad_bg(sc, lt):
    r = random.Random(31)
    for i in range(9):
        x = r.uniform(-9, 9); z = r.uniform(13, 30)
        character(sc, (x, 0, z), r.uniform(0, 360), idle(lt, i), extra_look(130 + i, gown=True))

MAXG = dict(MAX, gown=True, cap=True, head=1.1)
def S5b(lt, d, t):
    sc = Scene(fog=FOG_DAY, sky=sky_day(), sun=(-.4, -1, .5)); grad(sc); grad_bg(sc, lt); u = lt / d
    character(sc, (1.4, 0, 0), 0, dict(al=(0, 4), ar=(0, 4)), eli('old', {}, gown=True), nohead=True)
    z = lerp(11.5, 4.4, u)
    character(sc, (-.6, 0, z), 180, dict(walk(lt * 1.15, amp=30), al=(165, 18 + 16 * math.sin(lt * 9))), dict(MAXG, face=dict(eyes='happy', mouth='grin')))
    cam = Cam((-1.25, 3.7, -4.2), (-.55, 4.35, 6), fov=40)
    return sc, cam, dict(GRAD_WARM)

def max_close(lt, face, camz, camx=.5, sat=1.0, head=(0, 0), fov=34):
    sc = Scene(fog=FOG_DAY, sky=sky_day(), sun=(-.4, -1, -.5)); grad(sc); u = lt
    r = random.Random(31)
    for i in range(7):
        character(sc, (r.uniform(-7, 7), 0, r.uniform(-18, -8)), r.uniform(0, 360), idle(lt, i), extra_look(130 + i, gown=True))
    character(sc, (0, 0, 0), 0, dict(idle(lt), head=head, al=(0, 4), ar=(0, 4)), dict(MAXG, face=face))
    cam = Cam((camx, 4.7, camz), (0, 4.2, 0), fov=fov)
    return sc, cam, dict(tint=(lerp(1, 1.06, sat), 1, lerp(1, .9, sat)), sat=lerp(.72, 1.12, sat), vig=lerp(.35, 0, sat))

def S5c(lt, d, t):
    u = lt / d; t1 = (ps(23) - LEAD - (ps(22) - LEAD)); ts = (wt(22, 1) - ps(22)) + .12
    if lt < ts: face = dict(eyes='happy', mouth='grin')
    elif lt < t1: face = dict(eyes='open', mouth='flat', brows='up')
    else: face = dict(eyes='wide', mouth='o' if lt > t1 + .25 else 'flat', brows='up')
    return max_close(lt, face, lerp(9.0, 7.0, smooth(u)), sat=1 - smooth((lt - ts) / 1.2), head=(0, lerp(0, 5, u)))

def S6(lt, d, t):
    u = lt / d; talk = 0
    for i in (24, 25):
        for w in P[i]['words']:
            if w['t0'] <= t <= w['t1']: talk = .35 + .65 * abs(math.sin((t - w['t0']) * 17))
    return max_close(lt, dict(eyes='wide', brows='sad', talk=talk), lerp(6.4, 5.6, u), camx=-1.0, sat=0, head=(-8, 4), fov=32)

def S7a(lt, d, t):
    sc = Scene(fog=FOG_DAY, sky=sky_day(), sun=(-.4, -1, .5)); grad(sc); grad_bg(sc, lt); u = lt / d
    b = abs(math.sin(lt * 13)) * .09 * (1 - smooth(u * 1.3) * .6)
    character(sc, (0, 0, 0), 0, dict(y=b, ar=(lerp(10, 74, smooth(u * 3)), 26 + 16 * math.sin(lt * 13)), al=(4, 5), head=(0, 4)), eli('old', {}, gown=True, cap=True, style='bald'))
    character(sc, (-2.7, 0, 3.4), 160, dict(idle(lt), head=(0, 3)), dict(MAXG, face=dict(eyes='wide', brows='sad', mouth='flat')))
    cam = Cam((lerp(3.0, 2.7, u), 5.3, lerp(-7.0, -6.4, u)), (-1.5, 4.1, 3), fov=40)
    return sc, cam, dict(sat=.85, vig=.3)

def hands_pov(lt, rx, jit, fov, setf, roll=0, dy=0, spread=-27):
    """First-person look down at two blocky hands (built directly, no rig)."""
    sc = setf(); lift = (rx - 46) / 26.0; sep = .6 + (abs(spread) - 16) * .012
    skin = (226, 196, 172)
    for sx, ph in ((-1, 0.0), (1, 1.7)):
        jx = jit * .012 * (math.sin(lt * 47 + ph) + .6 * math.sin(lt * 83 + ph * 2)); jy = jit * .012 * (math.sin(lt * 53 + ph) + .6 * math.sin(lt * 71 + ph))
        h = V(sx * sep + jx, .5 + lift * .6 + dy + jy, 2.5 + lift * .3)
        dv = V(sx * .16, -.30, -.94); dv = dv / np.linalg.norm(dv)
        r = np.cross(V(0, 1, 0), dv); r = r / np.linalg.norm(r); up = np.cross(dv, r)
        def M(c):
            m = np.eye(4); m[:3, 0] = r; m[:3, 1] = up; m[:3, 2] = dv; m[:3, 3] = c; return m
        sc.box(M(h), (.9, .9, 1.1), skin, shadow=False, layer=2)
        sc.box(M(h + dv * 3.55), (1.02, 1.02, 6.0), (52, 58, 100), shadow=False, layer=2, bias=.5)
    cam = Cam((0, 5.0 + dy, -.2), (0, 1.6 + dy, 2.3), fov=fov, roll=roll)
    return sc, cam

def _gradset():
    sc = Scene(fog=FOG_DAY, sky=sky_day(), sun=(-.4, -1, .5)); grad(sc); return sc
def S7b(lt, d, t):
    u = lt / d; sc, cam = hands_pov(lt, lerp(46, 70, smooth(u * 2.5)), 2.6, 52, _gradset)
    return sc, cam, dict(sat=.8, vig=.4)
def S7c(lt, d, t):
    u = lt / d; sc, cam = hands_pov(lt, 70, 3.4, lerp(52, 74, ease_out(u)), _gradset, roll=math.sin(lt * 3) * 5, dy=-.5 * ease_out(u))
    hb = max(0, math.sin(lt * 9)) ** 6
    return sc, cam, dict(sat=lerp(.8, .45, u), vig=lerp(.4, .8, u) + hb * .12)

def S8a(lt, d, t):
    sc = Scene(amb=.7, dif=.3, shadow=0); corridor(sc); u = lt / d
    z = lerp(10, -58, u ** 1.15); st = lt * 9.5
    cam = Cam(V(math.sin(st * .5) * .25, 4.7 + abs(math.sin(st)) * .4, z) + shake(t, .04), (0, 5.3, -80), fov=66, roll=math.sin(st * .5) * 3.2)
    return sc, cam, dict(sat=.75, vig=.55, flash=max(0, .35 - lt * 3))
def S8b(lt, d, t):
    sc = Scene(amb=.7, dif=.3, shadow=0); corridor(sc); u = lt / d
    k = ease_out(lt / .55); z = lerp(-58, -72.6, k)
    character(sc, (0, 1.0, -79.4), 0, {}, dict(sil=mix((48, 58, 76), (160, 180, 192), 1 - k * .85), scale=.9, cap=True, head=1.1), shadow=False)
    cam = Cam(V(0, 4.9 + math.sin(lt * 5) * .03, z) + shake(t, .05 * (1 - k)), (0, lerp(5.3, 4.6, k), -80), fov=lerp(66, 46, k))
    return sc, cam, dict(sat=.6, vig=.7)

OLD = dict(eyes='tired', mouth='frown', brows='sad')
def mirror_scene(face, pose=None, frame=True, cap=False):
    sc = Scene(amb=.66, dif=.34, sun=(.35, -1, -.6), shadow=0); bathroom(sc)
    character(sc, (0, 0, 0), 0, pose or {}, eli('old', face, gown=True, cap=cap))
    if frame:
        zf = 3.6; wd = (86, 62, 46); cx, cy, hw, hh = 0, 4.4, 1.75, 2.9; wl = (196, 214, 214)
        for x0, x1, y0, y1 in ((-30, cx - hw, -5, 20), (cx + hw, 30, -5, 20), (cx - hw, cx + hw, cy + hh, 20), (cx - hw, cx + hw, -5, cy - hh)):
            sc.poly([(x0, y0, zf), (x1, y0, zf), (x1, y1, zf), (x0, y1, zf)], wl, layer=3, unlit=True)
        for x, y, w, h in ((cx - hw - .15, cy, .5, 2 * hh + .8), (cx + hw + .15, cy, .5, 2 * hh + .8), (cx, cy + hh + .15, 2 * hw + .8, .5), (cx, cy - hh - .15, 2 * hw + .8, .5)):
            sc.box(T(x, y, zf + .1), (w, h, .3), wd, layer=4, shadow=False)
        sc.poly([(cx - hw, cy + .6, zf - .02), (cx - hw, cy + 1.9, zf - .02), (cx + .2, cy + hh, zf - .02), (cx - .8, cy + hh, zf - .02)], (255, 255, 255), layer=2, unlit=True, alpha=34)
        sc.poly([(cx + hw, cy - 1.6, zf - .02), (cx + hw, cy - 2.3, zf - .02), (cx + .6, cy - hh, zf - .02), (cx + 1.1, cy - hh, zf - .02)], (255, 255, 255), layer=2, unlit=True, alpha=26)
        bx(sc, 0, cy - hh - 1.3, zf + .9, 5.2, .7, 2.0, (240, 240, 244), layer=5, shadow=False)
    return sc
MIRROR_GRADE = dict(sat=.82, tint=(.96, 1.0, 1.05), vig=.5)
def S9a(lt, d, t):
    u = lt / d; sc = mirror_scene(dict(OLD, look=(0, 1)), frame=False)
    cam = Cam((.7, lerp(6.1, 5.7, smooth(u)), 4.6), (0, lerp(5.45, 5.1, smooth(u)), 0), fov=30)
    return sc, cam, dict(MIRROR_GRADE, flash=max(0, .7 - lt * 4))
def S9b(lt, d, t):
    u = lt / d; f = dict(OLD); 
    if .5 < u < .66: f['eyes'] = 'closed'
    f['look'] = (math.sin(lt * 4) * .8, 0)
    sc = mirror_scene(f, frame=False)
    cam = Cam((lerp(.3, .12, u), 4.8, lerp(3.9, 3.5, u)), (0, 4.6, 0), fov=26)
    return sc, cam, dict(MIRROR_GRADE, flash=max(0, .3 - lt * 4))
def S9c(lt, d, t):
    u = lt / d; k = smooth((u - .15) * 1.6)
    sc = mirror_scene(dict(OLD, mouth='frown' if u < .5 else 'wobble'), dict(ar=(lerp(0, 128, k), lerp(4, 34, k)), head=(lerp(0, -5, k), 0)))
    cam = Cam((0, lerp(4.75, 4.45, smooth(u)), lerp(5.2, 13.5, smooth(u))), (0, lerp(4.6, 4.4, smooth(u)), 0), fov=40)
    return sc, cam, dict(MIRROR_GRADE, flash=max(0, .3 - lt * 4))

def S10a(lt, d, t):
    n = 3; seg = d / n; i = min(n - 1, int(lt / seg))
    st = [('kid', 'yard', {}), ('teen', 'street', dict(streak=.5)), ('adult', 'kitchen', dict(streak=1, gray=.55, age=.45))][i]
    sc, cam, post = snap_close(lt - i * seg, seg, st[0], st[1], st[2], seedt=i * 2)
    post['sat'] = .8; post['vig'] = .45; return sc, cam, post
def S10b(lt, d, t):
    sc = Scene(fog=FOG_DAY, sky=sky_day()); street(sc); street_people(sc, 7.7, n=10, seed=12); u = lt / d
    r = random.Random(5)
    for i in range(7): bird(sc, r.uniform(-7, 7), r.uniform(24, 40), r.uniform(-72, -56), r.uniform(-60, 60), r.choice([-30, 10, 35]))
    cam = Cam((lerp(2.5, 1.5, u), 5, lerp(-36, -44, u)), (0, lerp(33, 37, u), -84), fov=52)
    return sc, cam, dict(freeze=1, vig=.45, flash=max(0, .3 - lt * 4))
def S10c(lt, d, t):
    u = lt / d; age = smooth(u * 1.12)
    cam = Cam((lerp(1.5, 3.0, u), 3.7, lerp(4.6, 3.4, u)), (8.0, 3.0, .08), fov=42)
    return bench_scene(lt, u, age, cam), cam, dict(freeze=1, sat=.85, vig=.45, flash=max(0, .3 - lt * 4))
def S10d(lt, d, t):
    u = lt / d; f = dict(OLD)
    if u > .62: f['eyes'] = 'closed'
    sc = mirror_scene(f, dict(head=(0, lerp(0, -24, smooth(u * 1.3))), lean=lerp(0, 5, u)))
    cam = Cam((0, 4.45, lerp(12.5, 10.8, u)), (0, 4.4, 0), fov=40)
    return sc, cam, dict(MIRROR_GRADE, flash=max(0, .3 - lt * 4))
def _bath():
    sc = Scene(amb=.66, dif=.34, sun=(.35, -1, -.6), shadow=.2); bathroom(sc); sc.ground((132, 156, 164), half=30, grid=(120, 144, 152), cell=2); return sc
def S10e(lt, d, t):
    u = clamp(lt / (END - (ps(38) - LEAD)))
    sc, cam = hands_pov(lt, lerp(72, 52, smooth(u)), 1.2 * (1 - u), lerp(52, 46, u), _bath, spread=lerp(-27, -16, u))
    return sc, cam, dict(sat=lerp(.8, .5, u), vig=lerp(.5, .9, u), fade=smooth((u - .45) * 1.5) * .55)

def cut(i): return ps(i) - LEAD
SHOTS = [(0, S1), (cut(2), S2a), (cut(3), S2b), (cut(4), S2c), (cut(5), S2d), (cut(6), S2e), (cut(7), S3a), (cut(9), S3b), (cut(10), S3c), (cut(11), S3d),
         (cut(12), S4a), (cut(13), S4b), (cut(14), S4c), (cut(15), S4d), (cut(16), S4e), (cut(18), S4f), (cut(19), S5a), (cut(21), S5b), (cut(22), S5c),
         (cut(24) - .1, S6), (cut(26), S7a), (cut(27), S7b), (cut(28), S7c), (cut(29), S8a), (cut(30), S8b), (cut(31), S9a), (cut(32), S9b), (cut(33), S9c),
         (cut(34), S10a), (cut(35), S10b), (cut(36), S10c), (cut(37), S10d), (cut(38), S10e), (END, None)]

def events():
    def dur(i): return SHOTS[i + 1][0] - SHOTS[i][0]
    ix = {fn.__name__: i for i, (t0, fn) in enumerate(SHOTS) if fn}
    st = lambda n: SHOTS[ix[n]][0]; du = lambda n: dur(ix[n])
    E = dict(flick=S1_STEP + .34, wink=S1_WINK, snaps=[S1_TF, st('S2a') + du('S2a') - .30] + [st('S4b') + du('S4b') / 3 * (i + .42) for i in range(3)] + [st('S4c') + du('S4c') * .42]
             + [st('S10a') + du('S10a') / 3 * (i + .42) for i in range(3)],
             unfreeze=[st('S3c') + du('S3c') * .5], cuts=[t for t, f in SHOTS], st={n: st(n) for n in ix}, du={n: du(n) for n in ix}, end=END, dur=DUR,
             smile_stop=st('S5c') + (wt(22, 1) - ps(22)) + .12)
    return E

# ---------------------------------------------------------------- grading
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_vig = (((_xx - W / 2) / (W * .75)) ** 2 + ((_yy - H / 2) / (H * .75)) ** 2).astype(np.float32)
LUM = np.array([.3, .59, .11], np.float32)
def grade(img, sc, cam, post):
    a = np.asarray(img, np.float32)
    fz = post.get('freeze', 0)
    if fz:
        if isinstance(fz, dict):
            dist = np.sqrt((_xx - fz['c'][0]) ** 2 + (_yy - fz['c'][1]) ** 2)
            fm = np.clip((fz['r'] - dist) / 40 + .5, 0, 1); ring = np.exp(-((dist - fz['r']) / 60) ** 2) if fz['r'] < 3000 else None
            if fz.get('inv'): fm = 1 - fm
        else: fm = np.full((H, W), float(fz), np.float32); ring = None
        mask = np.asarray(sc.render_mask(cam), np.float32) / 255
        fm = fm * (1 - mask)
        lum = a @ LUM
        cold = lum[..., None] * np.array([.74, .92, 1.2], np.float32) * .93 + np.array([8, 14, 30], np.float32)
        frozen = cold * .72 + a * .28
        a = a + (frozen - a) * fm[..., None]
        if ring is not None: a += ring[..., None] * np.array([150, 200, 255], np.float32) * .9
    sat = post.get('sat', 1.0)
    if sat != 1.0:
        lum = (a @ LUM)[..., None]; a = lum + (a - lum) * sat
    if 'tint' in post: a *= np.array(post['tint'], np.float32)
    v = post.get('vig', .18)
    if v: a *= (1 - np.clip(_vig * v * 1.6, 0, .92))[..., None]
    fl = post.get('flash', 0)
    if fl > 0: a += (255 - a) * min(1, fl)
    fd = post.get('fade', 0)
    if fd > 0: a *= (1 - fd)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if post.get('overlay'):
        dr = ImageDraw.Draw(img, 'RGBA')
        for f in post['overlay']: f(dr)
    return img

# ---------------------------------------------------------------- captions
def _groups():
    G = []
    for p in P:
        cur = []
        for w in p['words']:
            if cur and (len(cur) >= 3 or sum(len(x['w']) for x in cur) + len(w['w']) > 13):
                G.append((cur, p['clip'])); cur = []
            cur.append(w)
        if cur: G.append((cur, p['clip']))
    return G
GROUPS = _groups()
CAPF = "fonts/LuckiestGuy-Regular.ttf"
def captions(img, t):
    for gi, (g, clip) in enumerate(GROUPS):
        t0 = g[0]['t0'] - .04; t1 = g[-1]['t1'] + .12
        if gi + 1 < len(GROUPS): t1 = min(t1, GROUPS[gi + 1][0][0]['t0'] - .04)
        if t0 <= t < t1 and t < END: break
    else: return img
    k = clamp((t - t0) / .09); sc_ = .78 + .22 * ease_out(k) + .06 * math.sin(k * math.pi)
    size = int(104 * sc_); f = font(size, CAPF); dr = ImageDraw.Draw(img)
    words = [w['w'].upper().replace('...', '…') for w in g]
    widths = [dr.textlength(w, font=f) for w in words]; sp = size * .26
    lines = [[]]; lw = 0
    for i, wd in enumerate(widths):
        if lines[-1] and lw + wd > W * .86: lines.append([]); lw = 0
        lines[-1].append(i); lw += wd + sp
    y = int(H * .715) - (len(lines) - 1) * size * .55
    base = (150, 255, 170) if clip == '06' else (255, 255, 255)
    for ln in lines:
        tw_ = sum(widths[i] for i in ln) + sp * (len(ln) - 1); x = (W - tw_) / 2
        for i in ln:
            act = g[i]['t0'] - .03 <= t < g[i]['t1'] + .03 or (i == len(g) - 1 and t >= g[i]['t0'])
            col = (255, 222, 60) if act and clip != '06' else base
            dr.text((x + 5, y + 7), words[i], font=f, fill=(0, 0, 0), anchor='ls', stroke_width=int(size * .1), stroke_fill=(0, 0, 0))
            dr.text((x, y), words[i], font=f, fill=col, anchor='ls', stroke_width=int(size * .1), stroke_fill=(12, 12, 16))
            x += widths[i] + sp
        y += size * 1.1
    return img

def shot_at(t):
    for i in range(len(SHOTS) - 1):
        if SHOTS[i][0] <= t < SHOTS[i + 1][0]: return i
    return None
def frame(t, caps=True):
    i = shot_at(t)
    if i is None or SHOTS[i][1] is None: return Image.new('RGB', (W, H), (0, 0, 0))
    t0, fn = SHOTS[i]; d = SHOTS[i + 1][0] - t0
    sc, cam, post = fn(t - t0, d, t)
    img = grade(sc.render(cam), sc, cam, post)
    return captions(img, t) if caps else img

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "sheet":      # contact sheet of selected shots
        ids = [int(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else range(len(SHOTS) - 1)
        fr = float(sys.argv[2]); ims = []
        for i in ids:
            t0 = SHOTS[i][0]; d = SHOTS[i + 1][0] - t0
            try: ims.append(frame(t0 + d * fr).resize((360, 640)))
            except Exception as e:
                import traceback; traceback.print_exc(); print("shot", i, SHOTS[i][1].__name__); ims.append(Image.new('RGB', (360, 640), (255, 0, 255)))
        n = len(ims); cols = min(n, 4); rows = (n + cols - 1) // cols
        sh = Image.new('RGB', (cols * 360, rows * 640))
        for k, im in enumerate(ims): sh.paste(im, ((k % cols) * 360, (k // cols) * 640))
        sh.save(sys.argv[4] if len(sys.argv) > 4 else "build/sheet.jpg", quality=85)
    elif mode == "render":   # render frames [part of nparts]
        part, nparts = int(sys.argv[2]), int(sys.argv[3]); out = sys.argv[4]; os.makedirs(out, exist_ok=True)
        N = int(math.ceil(DUR * FPS))
        only = None if len(sys.argv) < 6 else [int(x) for x in sys.argv[5].split(',')]
        for n in range(N):
            if n % nparts != part: continue
            t = n / FPS
            if only is not None and shot_at(t) not in only: continue
            frame(t).save(f"{out}/{n:05d}.jpg", quality=93)
            if n % 100 == part: print(n, N, flush=True)
