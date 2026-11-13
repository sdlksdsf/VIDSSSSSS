"""In This Town Nobody Turns Off the Lights - shots, captions, renderer."""
import json, math, random, sys, os
sys.path.insert(0, 'src'); sys.path.insert(0, 'short2')
import numpy as np
from PIL import Image, ImageDraw
from world import *

TL = json.load(open("build/s2/timeline.json")); P = TL["phrases"]; DUR = TL["duration"]; FPS = 24
def ps(i): return P[i]["t0"]
def pe(i): return P[i]["t1"]
def wt(i, j): return P[i]["words"][j]["t0"]
LEAD = 0.07
def cut(i): return ps(i) - LEAD
TC = 0.86                         # the click
END = pe(38) + 1.30               # final click to black
MAYOR_CLIPS = ('06', '10')
def talk(t, clips=MAYOR_CLIPS):
    for p in P:
        if p['clip'] in clips and p['t0'] - .02 <= t <= p['t1']: return .25 + .75 * abs(math.sin(t * 21))
    return None
def pulse(lt, t0, d=.25): return clamp(1 - (lt - t0) / d) if lt >= t0 else 0.0
def seat(s=1.0, hip=1.25, **o):
    p = dict(ll=88, lr=88, y=hip / s - 2, al=(62, 8), ar=(62, 8), head=(0, -10)); p.update(o); return p
ARMS_UP = lambda t, i=0: dict(al=(168 + 10 * math.sin(t * 19 + i), 14), ar=(168 + 10 * math.sin(t * 17 + i * 2), 14), y=.12 * abs(math.sin(t * 9 + i)), head=(6 * math.sin(t * 13 + i), 6))

def walkers(sc, t, n=10, seed=1, on=1.0, tired=False, z0=-44, span=50, xs=(6.8, 9.6), mid=True):
    r = random.Random(seed)
    for i in range(n):
        sd = r.choice((-1, 1)); x = sd * r.uniform(*xs) if (i % 4 or not mid) else r.uniform(-4, 4); dr_ = r.choice((-1, 1)); sp = r.uniform(1.6, 2.6)
        z = ((r.uniform(0, span) + dr_ * sp * t) % span) + z0
        folk(sc, i + seed * 10, (x, 0, z), 0 if dr_ > 0 else 180, walk(t + i * .3, 1.7, 28), lant=on, tired=tired, kid=(i % 5 == 2))

def crack(k, c=(W * .5, H * .40), seed=4):
    def f(dr):
        r = random.Random(seed)
        for i in range(15):
            an = i * 2 * math.pi / 15 + r.uniform(-.15, .15); x, y = c; L = r.uniform(500, 1300) * min(1, k * 3 + .25); n = 7
            for j in range(n):
                an2 = an + r.uniform(-.35, .35); x2 = x + math.cos(an2) * L / n; y2 = y + math.sin(an2) * L / n
                dr.line([x, y, x2, y2], fill=(255, 255, 255, 235), width=max(2, 9 - j)); dr.line([x + 3, y + 3, x2 + 3, y2 + 3], fill=(60, 80, 130, 150), width=2)
                if j in (2, 4) and i % 2 == 0:
                    an3 = an2 + r.choice((-1, 1)) * 1.1; dr.line([x2, y2, x2 + math.cos(an3) * 150, y2 + math.sin(an3) * 150], fill=(255, 255, 255, 200), width=3)
                x, y = x2, y2
        dr.ellipse([c[0] - 46, c[1] - 46, c[0] + 46, c[1] + 46], fill=(255, 255, 255, 240))
    return f
def sparks(pt, k, seed=1, col=(255, 230, 120)):
    def f(dr):
        if not (0 <= k <= 1): return
        r = random.Random(seed); x, y = pt
        for i in range(22):
            an = r.uniform(0, 6.28); v = r.uniform(120, 520); px_ = x + math.cos(an) * v * k; py_ = y + math.sin(an) * v * k + 500 * k * k
            s = r.uniform(5, 13) * (1 - k); dr.ellipse([px_ - s, py_ - s, px_ + s, py_ + s], fill=col + (int(255 * (1 - k)),))
        a = int(255 * max(0, 1 - k * 4)); dr.ellipse([x - 90, y - 90, x + 90, y + 90], fill=(255, 255, 255, a))
    return f
def bigtext(txt, pt, k, size=150, col=(255, 235, 70)):
    def f(dr):
        if k <= 0: return
        s = int(size * (.6 + .4 * ease_out(min(1, k * 4)))); f_ = font(s, "fonts/Bangers-Regular.ttf")
        dr.text(pt, txt, font=f_, fill=col + (255,), anchor='mm', stroke_width=int(s * .09), stroke_fill=(20, 16, 50, 255))
    return f

# ================================================================ SHOTS
def A1(lt, d, t):      # 0.0  bright bedroom, one finger, one switch
    on = 1.0 if lt < TC else 0.0; u = clamp(lt / TC)
    sc = scene('room', lit=on)
    room(sc, w=13, d=10, h=11, wall=(110, 190, 255), floor=(250, 190, 110), win=(-3.4, 6.0, 3.6, 4.0))
    floorlamp(sc, -5.0, -3.6, on, col=(255, 120, 170)); floorlamp(sc, 4.9, -3.8, on, 6.0, col=(120, 255, 170))
    bx(sc, -3.4, 1.0, -3.6, 2.6, 2.0, 1.6, (255, 150, 60)); floorlamp(sc, -3.4, -3.6, on, 3.2, col=(255, 230, 90))
    if on: light(sc, (0, 9.5, 0), (1, .9, .7), 22, .8, .0)
    sx_ = 2.72
    sc.box(T(sx_, 3.05, -4.9), (.9, 1.3, .14), (250, 250, 250), shadow=False, bias=-.2)
    sc.box(T(sx_, 3.05 + (.2 if on else -.2), -4.8), (.3, .42, .14), (255, 70, 70), shadow=False, bias=-.4)
    face = dict(eyes='happy', mouth='grin') if on else dict(eyes='wide', mouth='o', brows='up', look=(math.sin(t * 9), 0))
    c = kid(sc, (0, 0, -4.1), 0, dict(al=(0, lerp(35, 90, ease_out(u))), ar=(0, 5), head=(10 * u if on else 0, 0), y=0 if on else .03 * math.sin(t * 30)), face)
    if not on: glow(sc, xf(c['head'], [(0, .7, .7)])[0], 2.6, (120, 160, 255), .45)
    sh = shake(t, .10 * pulse(lt, TC, .3))
    cam = Cam(lerp(V(.6, 3.6, 9.5), V(1.3, 3.3, 5.2), ease_out(u)) + sh, V(1.1, 3.2, -4.5) + sh, 50)
    ov = [bigtext("CLICK!", (W * .5, H * .22), lt - TC + .05, 190)] if lt >= TC else []
    return sc, cam, dict(overlay=ov, vig=.25 if on else .5, bloom=.8 if on else .5)

DARKWIN = {3: ((1, 1),)}
def A2(lt, d, t):      # every head in the street turns to the one dark window
    u = clamp(lt / d); sc = scene('night', 1.0)
    street(sc, t, dark=DARKWIN)
    for i, (x, z) in enumerate(((3.5, 1), (6.8, -1.5), (1.5, -3), (7.5, 3.5), (4.6, -6), (8.4, -8))):
        c = folk(sc, i + 3, (x, 0, z), 90 - (z + 4) * 4, dict(al=(0, 4), ar=(20, 6), head=(0, 22)), SCREAM if lt > .45 else dict(eyes='wide', mouth='o'), kid=(i == 2))
        if lt > .12: sc.text(xf(c['head'], [(0, 2.4, 0)])[0], '!', 1.5 * (1 + .3 * pulse(lt, .12, .2)), (255, 70, 70), stroke=(255, 255, 255), bias=-5)
    dog(sc, (-1.5, 0, 2.5), 60, t, trot=False)
    cam = Cam(lerp(V(-10, 4.5, 19), V(-7, 5.5, 14), ease_out(u)), lerp(V(8, 6, -3), V(10.9, 7.6, -4), ease_out(u)), lerp(62, 52, ease_out(u)))
    return sc, cam, {}

A3_HIT = 1.42
def A3(lt, d, t):      # the whole town screams; somebody throws a lamp at you
    sc = scene('night', 1.0); street(sc, t)
    spots = [(-4.4, -2.5), (-2.2, -1.5), (0, -2.5), (2.2, -1.5), (4.4, -2.5), (-3.3, -5.5), (-1.1, -5), (1.1, -5.5), (3.3, -5), (-5.5, -8), (0, -8.5), (5.5, -8)]
    for i, (x, z) in enumerate(spots):
        f = dict(SCREAM); f['talk'] = .7 + .3 * math.sin(t * 20 + i)
        folk(sc, i + 1, (x + .12 * math.sin(t * 23 + i), 0, z), 0, ARMS_UP(t, i), f, kid=(i in (2, 7)), lant=(.45 if i % 2 else None))
    dog(sc, (6.8, 0, -1), 160, t)
    k = clamp((lt - .95) / (A3_HIT - .95))
    cp = V(0, lerp(3.4, 3.8, clamp(lt / 1.2)), lerp(17, 13.5, ease_out(clamp(lt / .9))))
    if 0 < k < 1:      # the flying lamp
        p = lerp(V(1.2, 6.5, -7), cp + V(0, .3, -1.6), k) + V(0, math.sin(k * math.pi) * 1.6, 0)
        M = T(*p) @ RZ(k * 500) @ RX(k * 260)
        sc.box(M @ T(0, -.5, 0), (.3, 1.0, .3), (70, 70, 90), shadow=False, bias=-8); sc.box(M @ T(0, -1.05, 0), (.9, .2, .9), (70, 70, 90), shadow=False, bias=-8)
        sc.prism(M @ T(0, .35, 0), .7, .9, (255, 240, 170), n=8, shadow=False, bias=-8.5); glow(sc, p, 2.2, (255, 220, 120), .9)
    hit = lt >= A3_HIT; sh = shake(t, .06 + .25 * pulse(lt, A3_HIT, .35))
    cam = Cam(cp + sh, V(0, 4.6, -4) + sh, 56, roll=3 * math.sin(t * 3))
    ov = [crack(lt - A3_HIT)] if hit else []
    return sc, cam, dict(overlay=ov, flash=.9 * pulse(lt, A3_HIT, .22))

def B(lt, d, t):       # the town: every lamp, every window, a hundred years
    u = clamp(lt / d); e = smooth(u); sc = scene('night', 1.0); street(sc, t)
    walkers(sc, t, 12, 1)
    for z in (2, -10):
        for sd in (-1, 1): moths(sc, (sd * 7, 8, z + sd * 3), t, 4, z + sd)
    dog(sc, (-3 + 1.2 * lt, 0, 4 - 2.5 * lt), 155, t)
    cam = Cam(V(0, lerp(4.5, 11.5, e), lerp(26, 20, e)), V(0, lerp(8, 9.0, e), -30), 56)
    return sc, cam, {}

def C(lt, d, t):       # kids sleep in sunglasses
    u = clamp(lt / d); sc = scene('room', 1.0)
    room(sc, w=16, d=12, h=12, wall=(190, 130, 255), floor=(255, 200, 130), win=(4.6, 6.2, 3.6, 3.6))
    bed(sc, 0, -1.6, w=4.6)
    c = kid(sc, (0, 2.3, 1.0), 0, dict(pitch=-90, al=(0, 14), ar=(0, 14)), dict(eyes='closed', mouth='o'))
    shades(sc, c); bx(sc, 0, 2.55, .3, 4.5, .55, 3.0, (70, 130, 250), shadow=False, bias=-2)
    zzz(sc, (1.2, 3.6, -3.2), t, s=.9)
    for i, (x, z, col) in enumerate(((-3.6, -4.6, (255, 120, 170)), (3.6, -4.6, (120, 255, 170)), (-3.9, 1.6, (255, 230, 90)), (3.9, 1.6, (90, 220, 255)))):
        floorlamp(sc, x, z, 1.0, 5.6, col)
    light(sc, (0, 9, 0), (1, .92, .75), 20, .7, 0)
    folk(sc, 6, (lerp(9.5, 6.2, ease_out(u)), 0, -2.5), -90, walk(t, 1.2, 14), dict(eyes='tired', mouth='smile'), lant=1.0)   # mum tiptoes in with one more lamp
    cam = Cam(V(lerp(4.4, 3.4, u), lerp(12.5, 11, u), lerp(12.5, 11, u)), V(.4, 2.8, -1.6), 46)
    return sc, cam, dict(bloom=.8)

def D(lt, d, t):       # dogs wear flashlights
    sc = scene('night', 1.0); street(sc, t, banner=False)
    zd = 1.5 - 6.5 * lt
    dog(sc, (.5, 0, zd), 180, t)
    for i, (x, z) in enumerate(((7.2, -1), (8.6, -5), (7.6, -9.5), (9.2, -13), (7.4, -17))):
        folk(sc, i + 20, (x, 0, z), -90, idle(t, i), dict(eyes='tired' if i % 2 else 'happy', mouth='smile'), kid=(i == 1))
    cam = Cam(V(-5.6, 2.2, zd + 1.2), V(1.5, 2.8, zd - 1.0), 64)
    return sc, cam, {}

def E_(lt, d, t):      # even the fridge has a night-light
    u = clamp(lt / d); sc = scene('room', 1.0)
    room(sc, w=15, d=11, h=14, wall=(255, 205, 80), floor=(120, 220, 210))
    light(sc, (0, 10, 1), (1, .95, .8), 22, .7, 0)
    F = [(rect(0, 1.0, 3.7, .12), (170, 185, 200)), (rect(-1.45, 2.3, .22, 1.6), (150, 165, 185)), (rect(-1.45, -.8, .22, 2.2), (150, 165, 185)),
         (rect(-.55, -1.2, .16, .5), (25, 25, 30)), (rect(.75, -1.2, .16, .5), (25, 25, 30)), (arc(.1, -1.9, .5, .35, 200, 340, .09), (25, 25, 30))]
    sc.box(T(-1.6, 4.3, -3.6), (4.2, 8.6, 3.2), (236, 244, 252), decals=[('+z', F)])
    c2 = (60, 120, 250)
    sc.box(T(-1.6, 8.9, -3.6), (4.3, .7, 3.3), c2, shadow=False); sc.box(T(-1.0, 9.6, -3.6), (2.8, .8, 2.4), c2, shadow=False); sc.box(T(.2, 10.2, -3.6), (1.4, .6, 1.4), c2, shadow=False); sc.sprite((1.2, 10.0, -3.4), .5, .5, (255, 255, 255))
    nl = (1.25, 1.5, -1.9); pu = .75 + .25 * math.sin(t * 5)
    sc.box(T(*nl) @ RZ(45), (.8, .8, .3), (255, 240, 120), unlit=True, shadow=False, bias=-1); sc.box(T(*nl), (.8, .8, .32), (255, 250, 170), unlit=True, shadow=False, bias=-1.1)
    light(sc, nl, (1, .9, .4), 7, 1.0 * pu, .9 * pu, 2.6)
    bx(sc, 4.9, 1.7, -4.2, 4.4, 3.4, 2.2, (250, 140, 90)); bx(sc, 4.9, 3.5, -4.2, 4.6, .3, 2.4, (250, 250, 250))
    nod = 16 + 14 * math.sin(t * 2.2)
    c = folk(sc, 9, (4.6, 0, -1.4), -20, dict(al=(4, 4), ar=(24, 5), head=(0, -nod), lean=4), dict(eyes='closed', mouth='o'), lant=None, look=dict(shirt=(60, 190, 110)))
    sc.box(T(*c['hand_r']) @ T(0, .1, .2), (.5, .9, .5), (250, 250, 250), shadow=False); zzz(sc, xf(c['head'], [(.6, 1.6, 0)])[0], t, s=.7)
    cam = Cam(lerp(V(2.4, 5.2, 17), V(1.8, 4.2, 12.5), smooth(u)), lerp(V(.2, 5.4, -3), V(.3, 4.4, -3), smooth(u)), 52)
    return sc, cam, dict(bloom=.8)

F_OUT = pe(8) + .12 - cut(7)
def F(lt, d, t):       # they say the Dark is alive
    u = clamp(lt / F_OUT); out = lt >= F_OUT
    fl = 0.0 if out else (1.0 if (math.sin(t * 31) + math.sin(t * 47 + 1) > -.9 + 1.2 * u) else .15)
    sc = scene('night', .30 if out else .72 + .12 * fl, stars=.6)
    base(sc, (40, 40, 70), 60); tiles(sc, -14, 14, -4.4, 12, 2.5, (120, 116, 150), (108, 104, 140))
    br = []
    for i in range(16):
        for j in range(6): br.append((rect(-19 + i * 2.5 + (j % 2) * 1.25, -6 + j * 2.2, 2.3, 2.0), (200, 86, 96) if (i + j) % 3 else (214, 100, 104)))
    sc.box(T(0, 7, -5), (40, 14, 1), (150, 60, 76), layer=0, shadow=False, decals=[('+z', br)])
    lamp(sc, 5.6, -2.6, 0 if out else 1, flick=fl, side=1)
    # the shadow hand creeping along the wall
    g = ease_out(u) if not out else 1 + .25 * ease_out((lt - F_OUT) / .3)
    tip = lerp(-13, -.6, min(g, 1)) + (g - 1) * 6 if g > 1 else lerp(-13, -.6, g)
    sh_c = (16, 6, 46); kw = dict(unlit=True, alpha=235, layer=0)
    y0 = 6.2 + .3 * math.sin(t * 3)
    sc.poly([(-21, y0 - 1.5, -4.45), (tip - 3.4, y0 - 1.3, -4.45), (tip - 3.4, y0 + 1.3, -4.45), (-21, y0 + 1.5, -4.45)], sh_c, **kw)
    sc.poly([(tip - 3.6, y0 - 2, -4.45), (tip - 1.2, y0 - 2, -4.45), (tip - 1.2, y0 + 2, -4.45), (tip - 3.6, y0 + 2, -4.45)], sh_c, **kw)
    for i in range(4):
        fy = y0 - 1.75 + i * 1.16; cu = .6 * math.sin(t * 5 + i)
        sc.poly([(tip - 1.3, fy - .4, -4.45), (tip + 1.6, fy - .36 + cu * .3, -4.45), (tip + 1.75, fy + cu * .3, -4.45), (tip + 1.6, fy + .36 + cu * .3, -4.45), (tip - 1.3, fy + .4, -4.45)], sh_c, **kw)
    ppl = [(.8, -2.4, 4), (2.9, -1.8, 12), (4.8, -2.6, 17)]
    for i, (x, z, k) in enumerate(ppl):
        if out and i == 0:
            q = clamp((lt - F_OUT) / .5)
            for j in range(7):
                a = j * .9; sc.sprite((x + math.cos(a) * q * 2.2, 2.6 + math.sin(a) * q * 2.2, z), .8 * (1 - q), .8 * (1 - q), (190, 170, 255), alpha=int(230 * (1 - q)))
            lantern(sc, (x + .9, max(.5, 2.4 - 14 * q * q), z + .6), 0.0); continue
        f = dict(eyes='wide', mouth='wobble' if not out else 'open', brows='sad', look=(-1, 0))
        folk(sc, k, (x + .05 * math.sin(t * 40 + i), 0, z), -20, dict(al=(40, 30), ar=(50, 20), head=(28, 0), lean=-6, y=.04 * math.sin(t * 30)), f, lant=(0.0 if out else .5 + .5 * fl), kid=(i == 1))
    cam = Cam(V(-1.6, 4.4, lerp(19, 16.5, u)) + shake(t, .12 * pulse(lt, F_OUT, .3)), V(-.4, 5.2, -4), 56)
    return sc, cam, dict(vig=.5, sat=1.2)

def G(lt, d, t):       # we'd moved in that morning
    u = clamp(lt / d); sc = scene('day')
    street(sc, t, on=lambda z: .45, day=True)
    truck(sc, -2.6, -9, 0)
    for x, z in ((-13, 6), (13, 2), (-13, -22), (13, -24)): tree(sc, x * 1.0, z, .9, night=False)
    z = lerp(-4.5, 1.0, u)
    c = kid(sc, (2.6, 0, z), 0, dict(walk(t, 1.9, 26), al=(72, -6), ar=(72, -6)), dict(eyes='happy', mouth='grin'))
    hp = (c['hand_l'] + c['hand_r']) / 2
    sc.box(T(hp[0], hp[1] + .3, hp[2] + .5), (2.3, 1.7, 1.7), (214, 160, 100), decals=[('+z', [(rect(0, 0, 2.3, .3), (240, 220, 180))])], bias=-1)
    for i, (x, zz, yaw) in enumerate(((7.6, -2, -70), (8.8, -7, -75), (-7.4, -1, 70), (-8.6, -6, 75), (7.4, 3.5, -100))):
        folk(sc, i + 30, (x, 0, zz), yaw, dict(al=(0, 4), ar=(26, 6), head=(0, 4)), dict(eyes='tired', mouth='flat', brows='flat'), kid=(i == 3))
    cam = Cam(V(lerp(6.6, 5.4, u), 2.8, lerp(14, 12, u)), V(.8, 4.0, -3), 56)
    return sc, cam, dict(sat=1.35, bloom=.35, vig=.2)

def Hs(lt, d, t):       # at school they called me Lights Out
    u = clamp(lt / d); sc = scene('room', 1.0)
    room(sc, w=22, d=12, h=13, wall=(80, 205, 160), floor=(250, 205, 130))
    for x in (-6, 0, 6): light(sc, (x, 11.5, 0), (1, .97, .85), 16, .55, .6, 3.5); bx(sc, x, 12.6, 0, 4, .3, 1, (255, 255, 240), unlit=True, shadow=False)
    sc.box(T(1.5, 7.2, -5.7), (11, 4.6, .3), (30, 90, 70), shadow=False); sc.box(T(1.5, 7.2, -5.75), (11.5, 5.1, .2), (160, 110, 70), shadow=False)
    sc.text((1.5, 7.9, -5.4), "LIGHTS OUT", 1.5, (250, 250, 250), bias=-2); sc.text((1.5, 6.0, -5.4), "HA HA HA", .9, (255, 230, 90), bias=-2)
    def desk(x, z): bx(sc, x, 2.1, z + 1.5, 3.2, .3, 1.8, (200, 140, 80)); bx(sc, x, 1.0, z + 2.2, 2.8, 2.0, .2, (160, 110, 70))
    desk(-3.2, 1.2); kid(sc, (-3.2, 0, 1.2), 8, seat(.76, head=(10, -28), al=(40, 6), ar=(40, 6)), dict(eyes='sad', mouth='frown', brows='sad'))
    for i, (x, z) in enumerate(((3.6, -1.2), (7.4, -1.6), (-.2, -3.4), (5.5, -3.8))):
        desk(x, z); L = flook(i + 50, True, dict(eyes='happy', mouth='grin'))
        b = .1 * abs(math.sin(t * 9 + i))
        c = character(sc, (x, 0, z), -25, seat(L['scale'], ar=(86, -18) if i % 2 == 0 else (60, 8), al=(60, 8), y=1.25 / L['scale'] - 2 + b, head=(-20, 4)), L)
    cam = Cam(V(lerp(-1.4, -.6, u), 5.4, lerp(16.5, 14.5, u)), V(.6, 4.2, 0), 52)
    return sc, cam, dict(bloom=.7)

def I(lt, d, t):       # everyone here looked so... tired
    u = clamp(lt / d); sc = scene('night', 1.0); street(sc, t, banner=False)
    xs = (-4.6, 0, 4.6)
    for i, x in enumerate(xs):
        k = clamp((lt - i * d / 3.4) / (d / 3)); y = math.sin(k * math.pi)
        drop = ease_in(clamp((u - .78) / .2)) if i == 2 else 0
        f = dict(eyes='closed' if (y > .5 or drop > .3) else 'tired', mouth='flat', brows='flat')
        if y > .15: f['talk'] = y * 1.25
        c = folk(sc, (8, 21, 14)[i], (x, 0, -3), 0, dict(al=(2, 4), ar=(150 * y if i != 1 else 20, 20 * y), head=(0, 12 * y - 40 * drop), lean=8 * drop), f, lant=.9)
        if drop > .6: zzz(sc, xf(c['head'], [(.5, 1.5, .5)])[0], t, s=.7)
    walkers(sc, t, 7, 4, tired=True, z0=-46, span=36, mid=False)
    cx = lerp(-5.2, 5.0, smooth(u))
    cam = Cam(V(cx * .9, 4.9, 5.2), V(cx, 4.95, -3), 52)
    return sc, cam, {}

def porch(sc, on=1.0, day=False, win_on=True):
    base(sc, (60, 170, 80) if day else (34, 96, 70))
    tiles(sc, -16, 16, 0.5, 14, 3, (190, 186, 205), (176, 172, 196))
    r = random.Random(2); wins = [(rect(0, -3.7, 2.6, 5.0), (120, 70, 46)), (ell(.8, -3.7, .22, .22, 8), (250, 210, 80)), (rect(0, -6.1, 2.6, .16), (255, 220, 110, -1) if win_on else (20, 20, 40))]
    for sx in (-1, 1):
        wins += [(rect(sx * 5, -1.6, 3.3, 3.3), (250, 250, 250)), (rect(sx * 5, -1.6, 2.8, 2.8), WIN_ON if win_on else WIN_OFF), (rect(sx * 5, -1.6, .2, 2.8), (250, 250, 250)), (rect(sx * 5, -1.6, 2.8, .2), (250, 250, 250))]
    sc.box(T(0, 6.5, -8), (17, 12.4, 8), (70, 200, 190), decals=[('+z', wins)])
    sc.box(T(0, 13.2, -8), (18.4, 1.0, 9.2), (40, 110, 120)); sc.box(T(0, .35, -1.6), (17, .5, 5), (200, 150, 96))
    sc.box(T(0, 8.6, -1.8), (18, .5, 5.4), (40, 110, 120))
    for sx in (-1, 1): bx(sc, sx * 8, 4.4, .5, .5, 8, .5, (250, 250, 250))
    bp = (0, 7.5, -1.2)
    bx(sc, 0, 8.1, -1.2, .08, .6, .08, (40, 40, 60), shadow=False); sc.sprite(bp, .42, .5, mix((70, 74, 100), (255, 246, 190), on), bias=-1)
    if on > .03: light(sc, bp, WARM, 16, 1.3 * on, .9 * on, 5)
    for sx in (-1, 1):
        house(sc, sx * 24, -10, HOUSE[2 + sx], '+z', w=12, d=8, on=1.0, seed=7 + sx)
        if not day or True: lamp(sc, sx * 13, 6, 1.0, side=sx)
    stringlights(sc, 3, 1.0, y=10.5, x0=-13, x1=13, n=13)
    return bp
def chair(sc, x, z, rock):
    M = T(x, .6, z) @ RX(rock); c = (150, 96, 60)
    sc.box(M @ T(0, 1.15, 0), (2.4, .25, 2.2), c); sc.box(M @ T(0, 2.9, -1.05), (2.4, 3.4, .25), c)
    for sx in (-1, 1): sc.box(M @ T(sx * 1.1, .5, 0), (.22, 1.1, .22), c); sc.box(M @ T(sx * 1.1, .05, 0), (.22, .2, 3.0), c)
J_POP = wt(17, 3) + .05 - cut(16)
def J(lt, d, t):       # Old Pete's bulb burned out
    u = clamp(lt / d); out = lt >= J_POP
    fl = 1.0 if lt < J_POP - .7 else (1.0 if math.sin(t * 43) + math.sin(t * 29) > -.3 else .2)
    on = 0.0 if out else fl
    sc = scene('night', .5 if out else .8 + .2 * fl); bp = porch(sc, on)
    rk = 7 * math.sin(t * 2.4) if not out else 2
    chair(sc, -3.4, -2.2, rk)
    f = dict(eyes='happy', mouth='smile') if not out else dict(eyes='wide', mouth='o', brows='up', look=(1, 1))
    c = character(sc, (-3.4, .6, -2.2), 12, seat(.98, hip=1.35, head=(24 if out else 0, 16 if out else -4), pitch=rk), dict(PETE, face=f))
    if not out: moths(sc, bp, t, 4, 1)
    cam = Cam(V(lerp(3.0, 2.0, u), 4.4, lerp(17.5, 14.5, u)) + shake(t, .1 * pulse(lt, J_POP, .25)), V(-1.2, 5.2, -3), 52)
    ov = [sparks(px(cam, bp), (lt - J_POP) / .5)] if out else []
    return sc, cam, dict(overlay=ov, flash=.5 * pulse(lt, J_POP, .12), vig=.3 + .25 * out)

def K(lt, d, t):       # a black shape slid under his door
    u = clamp(lt / d); e = smooth(clamp(u * 1.12)); inside = u > .86
    sc = scene('night', .32, stars=.6); porch(sc, 0.0, win_on=not inside)
    chair(sc, -3.4, -2.2, 4 * math.sin(t * 2.4) * (1 - u))
    p = lerp(V(7.5, .62, 5.5), V(0, .62, -3.7), e); w = math.sin(t * 9)
    sq = 1 - .8 * clamp((u - .8) / .14)
    for i in range(6):
        q = lerp(V(7.5, .62, 5.5), V(0, .62, -3.7), smooth(clamp(u * 1.12 - i * .035)))
        if q[2] < -3.6 or (i and sq < .3): continue
        q = q + V(math.sin(t * 7 + i) * .25 * i * .3, (0 if q[2] < .9 else -.56), 0)
        sc.prism(T(*q) @ RY(40), (1.5 - i * .2) * (1 + .08 * w), .14, (14, 8, 44), n=12, shadow=False, bias=-1 - i * .01, rz=(1.2 - i * .16) * sq)
    if sq > .3:
        hy = p[1] + (0 if p[2] < .9 else -.56) + .5
        for sx in (-1, 1):
            ep = (p[0] + sx * .42, hy + .1 * w, p[2] - .2)
            sc.sprite(ep, .26, .32, (255, 244, 170), bias=-3); glow(sc, ep, 1.6, (255, 220, 120), .8)
        sc.prism(T(p[0], hy - .1, p[2]), .9, .9, (14, 8, 44), n=10, shadow=False, bias=-2)
    cam = Cam(V(lerp(5.5, 3.2, u), lerp(2.4, 1.7, u), lerp(8.5, 4.6, u)), lerp(V(4, 1, 2), V(0, 1.4, -3.8), e), 54)
    return sc, cam, dict(vig=.6, flash=.0)

def L_(lt, d, t):      # by morning, Pete was gone
    u = clamp(lt / d); sc = scene('day'); porch(sc, 0.0, day=True, win_on=False)
    chair(sc, -3.4, -2.2, 9 * math.sin(t * 2.6) * math.exp(-lt * .5))
    for sx in (-1, 1): bx(sc, -3.4 + sx * .5, .75, -.4, .7, .3, 1.2, (240, 80, 80), yaw=sx * 12)
    bx(sc, -1.6, .68, -.9, 1.3, .12, .5, (30, 30, 40), yaw=30)
    sc.text((-3.4, 6.2 + .2 * math.sin(t * 4), -2.2), '?', 2.2, (255, 255, 255), stroke=(40, 40, 80), bias=-4)
    for i, (x, z) in enumerate(((5.6, 1.6), (7.6, 2.4), (9.4, 1.0))):
        folk(sc, i + 60, (x, 0, z), -110, dict(al=(120, 30) if i == 0 else (0, 4), ar=(30, 8), head=(-10, 6), y=.03 * math.sin(t * 20 + i)), dict(eyes='wide', mouth='o', brows='sad'), kid=(i == 1))
    cam = Cam(V(lerp(4.4, 3.0, u), 4.6, lerp(18, 15.5, u)), V(.4, 4.6, -2.5), 54)
    return sc, cam, dict(sat=1.3, bloom=.35, tint=(1.04, 1.0, .93))

M_CLOSE = ps(24) - .1 - cut(21)
def M(lt, d, t):       # the mayor
    close = lt >= M_CLOSE; sc = scene('night', 1.0); street(sc, t, banner=False)
    tk = talk(t); f = dict(eyes='open', mouth='frown', brows='angry')
    if tk is not None: f['talk'] = tk
    jab = pulse(lt, 0.05, .3) * 12
    mayor(sc, (0, 0, 0), 0, dict(ar=(84 + jab, -8), al=(10, 26), lean=6, head=(0, -8)), f, t=t)
    for i, (x, z) in enumerate(((-4.6, -3.2), (-2.4, -4.6), (2.6, -4.4), (4.8, -3), (-6.4, -6), (0, -6.5), (6.4, -6.2))):
        folk(sc, i + 70, (x, 0, z), 0, dict(ar=(150 + 10 * math.sin(t * 6 + i), 10), al=(0, 5), y=.05 * abs(math.sin(t * 7 + i))), dict(eyes='tired', mouth='frown', brows='angry'), lant=1.0, kid=(i == 2))
    if close:
        k = ease_out((lt - M_CLOSE) / .25)
        cam = Cam(V(.8, 5.0, lerp(11.5, 10, k)), V(0, 5.7, 0), 38, roll=-7)
    else:
        u = clamp(lt / M_CLOSE); cam = Cam(V(1.6, 1.8, lerp(13, 11, ease_out(u))) + shake(t, .08 * pulse(lt, .05, .3)), V(0, 5.2, 0), 54, roll=4)
    return sc, cam, dict(vig=.4 + .2 * close)

N_OFF0 = pe(25) - .2 - cut(25); N_DARK = pe(26) + .12 - cut(25)
def N(lt, d, t):       # they left me in the square and switched off the last lamp
    k = clamp((lt - N_OFF0) / (N_DARK - N_OFF0)); dark = lt >= N_DARK
    front = lerp(-80, 8, k) if not dark else 99
    on = lambda z: 1.0 if z > front else 0.0
    lit = 0.0 if dark else lerp(1.0, .30, k)
    sc = scene('night', lit, stars=.3); street(sc, t, on=on, near=False)
    if not dark: lamp(sc, -3.4, -2.6, 1.0, side=-1)
    else: lamp(sc, -3.4, -2.6, 0.0, side=-1)
    c = kid(sc, (0, 0, -1), 0, seat(.76, hip=.5, al=(70, -14), ar=(70, -14), head=(18 * math.sin(t * 2.5), -6), y=.5 / .76 - 2 + .02 * math.sin(t * 30)), dict(eyes='wide', mouth='wobble', brows='sad', look=(math.sin(t * 2.5), 0)))
    if dark:
        for sx in (-1, 1): sc.sprite(xf(c['head'], [(sx * .235, .72, .68)])[0], .11, .14, (255, 255, 255), bias=-6)
    r = random.Random(5)
    for i in range(9):
        x = r.uniform(-8.5, 8.5); z = -9 - i * 2.4 - 5.5 * lt
        folk(sc, i + 80, (x, 0, z), 180, walk(t + i * .2, 1.9, 30), lant=(1.0 if on(z) else 0.0), kid=(i == 4))
    u = clamp(lt / d)
    cam = Cam(V(0, lerp(7.5, 5.2, u), lerp(11, 8.5, u)), V(0, lerp(3.4, 2.6, u), -6), 52)
    return sc, cam, dict(vig=.45 + .4 * dark, bloom=.65)

def O(lt, d, t):       # two huge eyes opened above me
    e = ease_out((lt - .25) / .55) * (1 - .9 * pulse(lt, 1.25, .12))
    sc = scene('night', 0.0, stars=0.0); sc.ambcol = (.13, .15, .36)
    base(sc, (40, 44, 90), 140)
    dark_body(sc, (0, -3, -30), 1.7, eyes=e, t=t)
    if e > .02: light(sc, (0, 14, -6), (1, .85, .5), 60, 1.6 * e, 0)
    c = kid(sc, (0, 0, 0), 180, dict(al=(30, 20), ar=(30, 20), head=(0, 30), lean=-8, y=.03 * math.sin(t * 34)), {})
    u = clamp(lt / d)
    cam = Cam(V(1.2, 1.3, lerp(8.5, 7.2, u)) + shake(t, .05 * e), V(0, lerp(9, 11.5, ease_out(u)), -10), 62)
    return sc, cam, dict(vig=.55)

def P_(lt, d, t):      # a giant hand came down...
    u = clamp(lt / d); e = smooth(clamp(lt / (d - .35)))
    sc = scene('night', 0.0, stars=.0); sc.ambcol = (.16, .18, .42)
    base(sc, (40, 44, 90), 140); tiles(sc, -12, 12, -12, 12, 3, (70, 74, 130), (64, 68, 122))
    light(sc, (-3, 9, 7), (1, .86, .55), 40, 2.2, 0)
    kid(sc, (0, 0, 0), 20, dict(al=(165, 30), ar=(165, 30), lean=14, head=(0, -24), ll=20, lr=20, y=-.25 + .03 * math.sin(t * 36)), dict(eyes='closed', mouth='wobble', brows='sad'))
    hy = lerp(21, 6.6, e)
    dark_hand(sc, T(0, hy, -1.4) @ RX(28) @ RZ(180), 1.25, curl=.25 + .2 * math.sin(t * 2), bias=6)
    hb = .5 + .5 * math.sin(t * 2 * math.pi * 2.2)
    cam = Cam(V(lerp(6.5, 5.2, u), lerp(1.4, 2.0, u), lerp(14, 12, u)) + shake(t, .04), V(0, lerp(8.5, 6.0, u), 0), 62)
    return sc, cam, dict(vig=.55 + .25 * hb * u, fade=clamp((lt - (d - .16)) / .14))

def Q(lt, d, t):       # ...and tucked me in
    u = clamp(lt / d); e = ease_out(clamp(lt / .8))
    sc = scene('night', 0.0, stars=1.0); sc.ambcol = (.42, .50, .95)
    base(sc, (50, 110, 96), 140); tiles(sc, -12, 12, -12, 12, 3, (120, 124, 190), (110, 114, 180))
    light(sc, (-3, 9, 2), (1, .88, .55), 30, 1.6, 0)
    bx(sc, 0, .3, -2.9, 2.6, .6, 1.5, (255, 255, 255))
    surprised = lt > .45
    c = kid(sc, (0, .42, 1.2), 0, dict(pitch=-90, al=(0, 10), ar=(0, 10), head=(0, 0)), dict(eyes='wide' if surprised else 'closed', mouth='o' if surprised else 'wobble', brows='up' if surprised else 'sad', look=(0, 1)))
    bz = lerp(2.6, -.35, e)
    blanket(sc, T(0, 1.05, bz), 3.6, 3.4)
    dark_hand(sc, T(0, 3.4 + (1 - e) * .8 + 5 * ease_in(clamp((lt - .95) / .5)), bz - 2.9) @ RX(62) @ RZ(180), .8, curl=.9, bias=5)
    for i in range(5):
        a = t * 1.5 + i * 1.3; sc.sprite((math.cos(a) * 3 + .5, 2.5 + i * .5, math.sin(a) * 2), .1, .1, (255, 240, 160)); glow(sc, (math.cos(a) * 3 + .5, 2.5 + i * .5, math.sin(a) * 2), .8, (255, 230, 140), .5)
    cam = Cam(V(lerp(3.4, 2.8, u), lerp(9.5, 8.6, u), lerp(6.0, 5.2, u)), V(0, 1.0, -1.5), 50)
    return sc, cam, dict(vig=.4, fade=1 - clamp(lt / .2))

def sleeper(sc, i, x, z, t, look=None, cap=True, zs=.7, face=None):
    bed(sc, x, z, w=3.6, l=6.6)
    L = flook(i, False, face or dict(eyes='closed', mouth='smile' if i % 2 else 'o')); L.update(look or {})
    c = character(sc, (x, 2.3, z + 2.4), 0, dict(pitch=-90, al=(0, 10), ar=(0, 10)), L)
    bx(sc, x, 2.55, z + 1.0, 3.7, .5, 3.4, SAT[(i * 3) % 8], shadow=False, bias=-2)
    if cap: nightcap(sc, c, SAT[(i * 3 + 2) % 8])
    zzz(sc, (x + .6, 3.8, z - 2.2), t + i * .37, s=zs)
    return c
def R(lt, d, t):       # the Dark didn't take people. It put them to bed.
    u = clamp(lt / d); sc = scene('night', 0.0, stars=1.0); sc.ambcol = (.46, .52, 1.0)
    base(sc, (44, 120, 100), 140); tiles(sc, -18, 18, -12, 14, 3, (120, 124, 190), (110, 114, 180))
    dark_body(sc, (0, -1, -24), 1.25, eyes=1, mood='kind', t=t, blush=1)
    light(sc, (0, 12, 0), (1, .86, .6), 44, 1.0, 0)
    sc.sprite((-13, 34, -60), 4, 4, (255, 250, 220), layer=0); glow(sc, (-13, 34, -60), 14, (200, 210, 255), .6)
    sleeper(sc, 90, -4.2, -3, t, dict(PETE), zs=1.0); sleeper(sc, 12, 4.2, -3, t); sleeper(sc, 4, -11.5, -6, t); sleeper(sc, 17, 11.5, -6, t)
    wv = 20 * math.sin(t * 5)
    dark_hand(sc, T(-15, 9 + .4 * math.sin(t * 2), -13) @ RZ(18 + wv * .3) @ RY(180), 1.3, curl=.1, bias=8)
    kid(sc, (0, 0, 5.2), 180, dict(al=(0, 6), ar=(150 + 15 * math.sin(t * 8), 12), head=(0, 22)), {})
    cam = Cam(V(0, lerp(6, 9.5, smooth(u)), lerp(15, 21, smooth(u))), V(0, lerp(7.5, 5.6, u), -10), 62)
    return sc, cam, dict(vig=.35, sat=1.35)

def S_(lt, d, t):      # nobody here had slept in a hundred years
    u = clamp(lt / d); sc = scene('night', lerp(.75, .45, u), stars=.6); street(sc, t, on=lambda z: lerp(1, .55, u), banner=False)
    for i, x in enumerate((-4.4, 0, 4.4)):
        t0 = .25 + i * .5; k = clamp((lt - t0) / .45); fall = ease_in(k); y = clamp((lt - t0 + .45) / .45) if lt < t0 else 0
        f = dict(eyes='closed' if (k > .1 or y > .4) else 'tired', mouth='o' if k > .1 else 'flat')
        if 0 < y and k == 0: f['talk'] = y
        c = folk(sc, (8, 21, 14)[i], (x, .45 * fall, -3 - 2.2 * fall), 0, dict(pitch=-90 * fall, al=(150 * y * (1 - fall), 12), ar=(10, 8), head=(0, 10 * y)), f, lant=.7 * (1 - fall), kid=(i == 1))
        if k >= 1: zzz(sc, (x + .5, 1.6, -3.2), t + i * .3, s=.75)
    dog(sc, (7.2, 0, -.5), 200, t, on=1 - clamp((lt - 1.6) / .2), sleep=lt > 1.6, trot=False)
    if lt > 1.75: zzz(sc, (7.4, 1.8, -.2), t, s=.6)
    cam = Cam(V(lerp(-1.5, 1.0, u), lerp(3.6, 3.0, u), lerp(9.6, 8.6, u)), V(0, lerp(3.6, 2.6, smooth(u)), -3), 52)
    return sc, cam, {}

def T_(lt, d, t):      # one by one, the lights went out
    u = clamp(lt / d); k = clamp((lt - .25) / (d - .9))
    front = lerp(24, -84, k); on = lambda z: 1.0 if z < front else 0.0
    sc = scene('night', lerp(.9, .0, k), stars=(.3, .6, 1.0)[min(2, int(k * 3))])
    sc.ambcol = tuple(lerp(a, b, k) for a, b in zip(sc.ambcol, (.40, .47, .95)))
    street(sc, t, on=on)
    r = random.Random(11)
    for i in range(12):
        sd = r.choice((-1, 1)); x = sd * r.uniform(6.8, 9.4); z = 4 - i * 4.2
        if on(z):
            y = .5 + .5 * math.sin(t * 2 + i); folk(sc, i + 100, (x, 0, z), 90 * -sd, dict(ar=(140 * y, 16), al=(0, 4), head=(0, 10 * y)), dict(eyes='tired', mouth='flat', talk=y), lant=1.0, kid=(i % 4 == 1))
        else:
            folk(sc, i + 100, (x, .45, z + 2), 0, dict(pitch=-90, al=(0, 10), ar=(0, 10)), dict(eyes='closed', mouth='smile'), lant=0.0, kid=(i % 4 == 1)); zzz(sc, (x, 1.6, z - 1.6), t + i * .4, s=.8)
    dog(sc, (2.5, 0, 5), 200, t, on=0, sleep=True, trot=False); zzz(sc, (2.7, 1.8, 5.2), t, s=.6)
    cam = Cam(V(0, lerp(9, 14, smooth(u)), lerp(15, 18, u)), V(0, lerp(6, 8, u), -30), 54)
    return sc, cam, dict(vig=.35, sat=1.35)

U_REV = ps(36) - .12 - cut(35)
def factory(sc, t, sign=1.0):
    base(sc, (44, 120, 100), 140); tiles(sc, -18, 18, -6, 14, 3, (120, 124, 190), (110, 114, 180))
    r = random.Random(1); wins, _ = winset(26, 15, 5, 2, sign, r, door=True)
    sc.box(T(0, 7.5, -10), (27, 15, 8), (250, 110, 90), decals=[('+z', wins)]); sc.box(T(0, 15.6, -10), (28.5, 1.2, 9), (150, 50, 60))
    for x in (-9, 9): bx(sc, x, 19.5, -11, 2.4, 7, 2.4, (190, 80, 80))
    sc.box(T(0, 18.6, -6.4), (22, 4.2, .4), mix((40, 30, 70), (70, 30, 110), sign), shadow=False)
    sc.text((0, 18.7, -6.1), "MAYOR'S BULBS", 2.2, mix((80, 80, 110), (255, 240, 120), sign), stroke=mix((40, 40, 60), (255, 120, 40), sign), sw=.07, bias=-2)
    if sign > .05:
        glow(sc, (0, 18.6, -6), 14, (255, 190, 80), .6 * sign); light(sc, (0, 12, 0), WARM, 40, 1.2 * sign, 0)
        for i in range(12):
            x = -10.5 + i * 1.9; c = STR[i % 5]; tw = .6 + .4 * math.sin(t * 8 + i * 2)
            sc.sprite((x, 16.2, -6.1), .3, .3, c); glow(sc, (x, 16.2, -6.1), 1.6, c, .6 * tw * sign)
    for i, (x, y, z) in enumerate(((6.5, 1, -2), (8.6, 1, -2.6), (7.4, 3, -2.4), (-7.2, 1, -2.4), (-9.2, 1, -3))):
        bx(sc, x, y, z, 2, 2, 2, (214, 160, 100), yaw=i * 11); sc.sprite((x, y + 1.35, z), .45, .5, (255, 246, 190)); glow(sc, (x, y + 1.3, z), 1.6, (255, 220, 120), .5 * sign)
    for i, (x, z) in enumerate(((-4.6, -1.5), (-3.2, -.6), (4.2, -1.0))):
        sc.prism(T(x, .8, z), .9, 1.6, (90, 200, 110), n=8); sc.text((x, .9, z + .95), '$', 1.0, (255, 240, 120), bias=-2)
def U(lt, d, t):       # and the mayor? he owned the light bulb factory
    rev = lt >= U_REV; k = ease_out((lt - U_REV) / .35) if rev else 0
    sc = scene('night', .25, stars=1.0); sc.ambcol = (.46, .52, 1.0); factory(sc, t)
    lk = math.sin(t * 6)
    f = dict(eyes='wide', mouth='wobble' if rev else 'flat', brows='up', look=(lk, 0))
    mayor(sc, (0, 0, 2), 0, dict(al=(0, 6) if not rev else (40, 40), ar=(0, 6) if not rev else (40, 40), head=(18 * lk * (1 - k), 0), y=.03 * math.sin(t * 30) * rev), f, t=t)
    if rev:
        for i in range(3): sc.sprite((-.9 - i * .25, 7.2 - ((lt * 2 + i * .3) % 1) * 1.2, 2.9), .1, .16, (130, 210, 255), bias=-6)
    cam = Cam(lerp(V(.3, 5.6, 6.6), V(0, 4.4, 20), k), lerp(V(0, 6.0, 2), V(0, 9.6, -4), k), lerp(34, 60, k))
    return sc, cam, dict(vig=.35)

V_TUCK = 1.05; V_SLEEP = pe(38) + .06 - cut(37); V_OFF = END - .02 - cut(37)
def V_(lt, d, t):      # so the Dark tucked him in first
    sl = lt >= V_SLEEP; k = ease_out(clamp((lt - .1) / (V_TUCK - .1))); fk = ease_out(clamp((lt - V_SLEEP) / .3)) if sl else 0
    flick = 1.0 if lt < V_SLEEP + .25 else (1.0 if math.sin(t * 50) > .2 else .25)
    sc = scene('night', .25, stars=1.0); sc.ambcol = (.46, .52, 1.0); factory(sc, t, sign=flick)
    tk = talk(t)
    f = dict(eyes='closed', mouth='o') if sl else dict(eyes='wide', mouth='open', brows='up', look=(0, 1))
    if tk is not None and not sl: f = dict(eyes='open', mouth='open', brows='angry', talk=tk)
    tucked = lt > V_TUCK
    fl = 0 if sl else (math.sin(t * 22) * 30 if tk is not None else 0)
    c = mayor(sc, (0, .5 * fk, 2 + .9 * fk), 0, dict(pitch=-90 * fk, al=(20 + fl, 26) if not sl else (0, 8), ar=(20 - fl, 26) if not sl else (0, 8), head=(0, 26 * (1 - clamp(lt / .5)) * (not tucked))), f, hat=not tucked, t=t, bulbs=0 if sl else 1)
    if tucked:
        nightcap(sc, c, (60, 120, 250))
        hk = clamp((lt - V_TUCK) / .5); hp = V(-2.2 - 5 * hk, 7.8 + 6 * ease_out(hk) - 14 * hk * hk, 2 - 3 * hk)
        if hp[1] > .3: sc.box(T(*hp) @ RZ(hk * 300), (1.5, 1.4, 1.5), (30, 26, 50), shadow=False); sc.box(T(*hp) @ RZ(hk * 300) @ T(0, -.7, 0), (2.3, .16, 2.3), (30, 26, 50), shadow=False)
        if sl: blanket(sc, T(0, 1.25, .9), 4.6, 3.6); bx(sc, 0, .3, -2.9, 3.4, .6, 1.8, (255, 255, 255)); zzz(sc, (1.4, 2.4, -3.0), t, s=1.2)
        else: sc.box(c['torso'] @ T(0, .6, .1), (2.3, 1.6, 1.3), (60, 110, 250), shadow=False, bias=-1)
    hy = lerp(26, 11.2, k) + 9 * ease_in(clamp((lt - V_TUCK - .15) / .6))
    dark_hand(sc, T(0, hy, .6) @ RX(20) @ RZ(180), 1.1, curl=.5, bias=6)
    u = clamp(lt / d)
    cam = Cam(V(lerp(2.5, 1.2, u), lerp(3.8, 3.2, u) + 5.5 * fk, lerp(19, 16, u) - 8 * fk) + shake(t, .1 * pulse(lt, V_TUCK, .25)), V(0, lerp(7.0, 1.4, fk), -.8), 56)
    return sc, cam, dict(vig=.4, flash=.25 * pulse(lt, V_TUCK, .15))

SHOTS = [(0, A1), (1.08, A2), (ps(1) - .22, A3), (cut(2), B), (cut(4), C), (cut(5), D), (cut(6), E_), (cut(7), F), (cut(10), G), (cut(12), Hs), (cut(14), I),
         (cut(16), J), (cut(18), K), (cut(19), L_), (cut(21), M), (cut(25), N), (cut(27), O), (cut(28), P_), (cut(29) - .12, Q), (cut(30), R), (cut(32), S_),
         (cut(33), T_), (cut(35), U), (cut(37), V_), (END, None)]

def events():
    ix = {fn.__name__: i for i, (t0, fn) in enumerate(SHOTS) if fn}
    st = {n: SHOTS[i][0] for n, i in ix.items()}; du = {n: SHOTS[i + 1][0] - SHOTS[i][0] for n, i in ix.items()}
    return dict(st=st, du=du, cuts=[t for t, f in SHOTS], end=END, dur=DUR, click=TC, hit=st['A3'] + A3_HIT, f_out=st['F'] + F_OUT, j_pop=st['J'] + J_POP,
                m_close=st['M'] + M_CLOSE, n_off0=st['N'] + N_OFF0, n_dark=st['N'] + N_DARK, u_rev=st['U'] + U_REV, v_tuck=st['V_'] + V_TUCK, v_sleep=st['V_'] + V_SLEEP)

# ================================================================ captions
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
    words = [w['w'].upper() for w in g]
    widths = [dr.textlength(w, font=f) for w in words]; sp = size * .26
    lines = [[]]; lw = 0
    for i, wd in enumerate(widths):
        if lines[-1] and lw + wd > W * .86: lines.append([]); lw = 0
        lines[-1].append(i); lw += wd + sp
    y = int(H * .715) - (len(lines) - 1) * size * .55
    may = clip in MAYOR_CLIPS; base = (255, 170, 110) if may else (255, 255, 255)
    for ln in lines:
        tw_ = sum(widths[i] for i in ln) + sp * (len(ln) - 1); x = (W - tw_) / 2
        for i in ln:
            act = g[i]['t0'] - .03 <= t < g[i]['t1'] + .03 or (i == len(g) - 1 and t >= g[i]['t0'])
            col = ((255, 90, 70) if may else (255, 226, 50)) if act else base
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
    sc, cam, P_ = fn(t - t0, d, t)
    img = post(sc.render(cam), sc, cam, P_)
    return captions(img, t) if caps else img

def sheet(ims, out, cols=6):
    n = len(ims); cols = min(n, cols); rows = (n + cols - 1) // cols
    sh = Image.new('RGB', (cols * 270, rows * 480))
    for k, im in enumerate(ims): sh.paste(im.resize((270, 480)), ((k % cols) * 270, (k // cols) * 480))
    sh.save(out, quality=85)

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "sheet":      # sheet <frac> <ids> <out>
        ids = [int(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 and sys.argv[3] != 'all' else range(len(SHOTS) - 1)
        fr = float(sys.argv[2]); ims = []
        import time
        for i in ids:
            t0 = SHOTS[i][0]; d = SHOTS[i + 1][0] - t0; q = time.time()
            try: ims.append(frame(t0 + d * fr))
            except Exception:
                import traceback; traceback.print_exc(); print("shot", i, SHOTS[i][1].__name__); ims.append(Image.new('RGB', (270, 480), (255, 0, 255)))
            print(i, SHOTS[i][1].__name__, round(time.time() - q, 2), flush=True)
        sheet(ims, sys.argv[4])
    elif mode == "strip":    # strip <out> <times...>
        sheet([frame(float(x)) for x in sys.argv[3:]], sys.argv[2])
    elif mode == "render":   # render <part> <nparts> <outdir> [shot ids]
        part, nparts = int(sys.argv[2]), int(sys.argv[3]); out = sys.argv[4]; os.makedirs(out, exist_ok=True)
        N = int(math.ceil(DUR * FPS))
        only = None if len(sys.argv) < 6 else [int(x) for x in sys.argv[5].split(',')]
        for n in range(N):
            if n % nparts != part: continue
            t = n / FPS
            if only is not None and shot_at(t) not in only: continue
            frame(t).save(f"{out}/{n:05d}.jpg", quality=92)
        print("done", part)
