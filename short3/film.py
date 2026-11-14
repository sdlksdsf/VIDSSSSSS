"""He Said I Stole His Wallet - shots, captions, renderer (short 3)."""
import json, math, random, sys, os
sys.path.insert(0, 'src'); sys.path.insert(0, 'short2')
import numpy as np
from PIL import Image, ImageDraw
from world import *

TL = json.load(open("build/s3/timeline.json")); P = TL["phrases"]; FPS = 24
def ps(i): return P[i]["t0"]
def pe(i): return P[i]["t1"]
LEAD = 0.06
def cut(i): return ps(i) - LEAD
END = pe(40) + .40; DUR = END + .12
def talk(t, spk):
    for p in P:
        if p['spk'] == spk and p['t0'] - .02 <= t <= p['t1']: return .25 + .75 * abs(math.sin(t * 23))
    return None
def pulse(lt, t0, d=.25): return clamp(1 - (lt - t0) / d) if lt >= t0 else 0.0
def yaw_to(p, q): return math.degrees(math.atan2(q[0] - p[0], q[2] - p[2]))
def seat(s=1.0, hip=1.25, **o):
    p = dict(ll=88, lr=88, y=hip / s - 2, al=(62, 8), ar=(62, 8), head=(0, -10)); p.update(o); return p
def F(spk, t, **f):
    tk = talk(t, spk)
    if tk is not None: f = dict(f); f['talk'] = tk
    return f

# ---------------------------------------------------------------- cast
REDL = dict(shirt=(240, 50, 50), pants=(40, 60, 150), hair=(70, 44, 28), skin=(244, 198, 158), scale=.78, head=1.22, shoes=(250, 250, 250), logo=None)
KEVL = dict(shirt=(20, 190, 170), pants=(36, 40, 60), hair=(26, 26, 32), skin=(236, 184, 140), scale=1.12, head=1.06, shoes=(245, 245, 245), logo='stripe')
COPL = dict(shirt=(40, 86, 220), pants=(26, 36, 90), hair=(110, 70, 40), skin=(206, 152, 110), scale=1.16, head=1.04, shoes=(20, 20, 24))
MARL = dict(shirt=(196, 110, 240), pants=(120, 70, 170), hair=(236, 236, 242), skin=(248, 208, 184), scale=.80, head=1.16, style='bun', age=1.0, shoes=(250, 250, 250))
def wallet(sc, p, s=1.0, yaw=0):
    sc.box(T(*p) @ RY(yaw), (.75 * s, .55 * s, .22 * s), (150, 84, 40), shadow=False, bias=-.6)
    sc.box(T(*p) @ RY(yaw) @ T(0, .12 * s, 0), (.78 * s, .08 * s, .25 * s), (200, 130, 60), shadow=False, bias=-.7)
def red(sc, pos, yaw=0, pose=None, face=None, wal='l', hood=True, **o):
    L = dict(REDL); L['face'] = face or {}; L.update(o)
    c = character(sc, pos, yaw, pose, L)
    sc.box(c['torso'] @ T(0, .75, .52), (.9, .5, .06), (255, 255, 255), shadow=False, bias=-.3)       # hoodie pocket
    sc.box(c['torso'] @ T(0, 2.0, -.62), (1.5, .7, .4), (200, 36, 40), shadow=False)                  # hood
    if wal: wallet(sc, c['hand_' + wal] + V(0, .05, 0), 1.0, yaw)
    return c
def moth(sc, p, t, s=1.0, flap=True):
    a = math.sin(t * 40) * .9 if flap else .25
    sc.sprite(p, .09 * s, .16 * s, (120, 100, 80), bias=-3)
    for sx in (-1, 1):
        q = V(*p) + V(sx * .2 * s * math.cos(a), .12 * s * math.sin(a) + .05, 0)
        sc.sprite(q, .2 * s * abs(math.cos(a)) + .04, .17 * s, (214, 196, 160), bias=-2.9)
def kevin(sc, pos, yaw=0, pose=None, face=None, blush=0.0, mth=None, t=0, cuffs=False, **o):
    L = dict(KEVL); L['face'] = face or {}; L.update(o); L['skin'] = mix(L['skin'], (240, 70, 60), blush * .75)
    c = character(sc, pos, yaw, pose, L)
    sc.box(c['head'] @ T(0, 1.5, .1), (1.1, .22, 1.0), L['hair'], shadow=False)                       # quiff
    sc.box(c['torso'] @ T(0, 1.82, .52), (.5, .12, .05), (255, 210, 60), shadow=False, bias=-.3)      # fake gold chain
    if mth: moth(sc, xf(c['head'], [(.25, 1.78, .2)])[0], t, 1.0, flap=mth > 1)
    if cuffs:
        m = (c['hand_l'] + c['hand_r']) / 2; sc.box(T(*m), (1.6 * L['scale'], .22, .5), (190, 196, 210), shadow=False, bias=-1)
    return c
def cop(sc, pos, yaw=0, pose=None, face=None, **o):
    L = dict(COPL); L['face'] = face or {}; L.update(o)
    c = character(sc, pos, yaw, pose, L); h = c['head']; nv = (22, 30, 80)
    sc.box(h @ T(0, 1.5, 0), (1.42, .42, 1.42), nv, shadow=False, bias=-.2); sc.box(h @ T(0, 1.34, .78), (1.3, .1, .5), (14, 16, 30), shadow=False, bias=-.3)
    sc.box(h @ T(0, 1.52, .73), (.3, .26, .05), (255, 214, 60), shadow=False, bias=-.5)
    sc.box(c['torso'] @ T(.5, 1.45, .52), (.34, .4, .05), (255, 214, 60), shadow=False, bias=-.3)
    sc.box(c['torso'] @ T(0, .12, 0), (2.06, .26, 1.06), (20, 20, 26), shadow=False, bias=-.2)
    return c
def marg(sc, pos, yaw=0, pose=None, face=None, cane=True, **o):
    L = dict(MARL); L['face'] = face or {}; L.update(o)
    c = character(sc, pos, yaw, pose, L); h = c['head']
    for i in range(7):
        x = -.72 + i * .24; sc.sprite(xf(c['torso'], [(x, 1.8 - .3 * math.sin((i + .5) / 7 * math.pi), .56)])[0], .09, .09, (255, 255, 250), bias=-1)
    for sx in (-1, 1): sc.box(h @ T(sx * .26, .73, .66), (.36, .3, .04), (255, 255, 255), shadow=False, bias=-.6, alpha=120); sc.box(h @ T(sx * .26, .89, .67), (.4, .05, .04), (200, 40, 90), shadow=False, bias=-.7)
    if cane: p = c['hand_r']; sc.box(T(p[0], p[1] / 2, p[2]), (.14, p[1], .14), (120, 76, 40), shadow=False)
    return c
def fries(sc, p, s=1.0):
    sc.box(T(*p), (.5 * s, .6 * s, .3 * s), (235, 40, 40), shadow=False, bias=-.8)
    for i in range(5): sc.box(T(p[0] - .2 * s + i * .1 * s, p[1] + .42 * s + (i % 2) * .08, p[2]), (.07 * s, .5 * s, .07 * s), (255, 214, 60), shadow=False, bias=-.9)
def pcar(sc, x, z, yaw, t, on=1.0):
    M = T(x, 0, z) @ RY(yaw); Wt = (246, 246, 250); B = (30, 70, 210); G = (150, 215, 250)
    sc.box(M @ T(0, 1.5, 0), (4.4, 1.7, 9.2), Wt, decals=[('+x', [(rect(0, 0, 9.2, .5), B)]), ('-x', [(rect(0, 0, 9.2, .5), B)]), ('+z', [(rect(-1.4, .2, .9, .5), (255, 250, 190, -1)), (rect(1.4, .2, .9, .5), (255, 250, 190, -1)), (rect(0, -.3, 2.2, .5), (40, 44, 60))])])
    sc.box(M @ T(0, 3.1, -.5), (4.0, 1.6, 4.8), Wt, decals=[('+x', [(rect(0, 0, 4.2, 1.1), G)]), ('-x', [(rect(0, 0, 4.2, 1.1), G)]), ('+z', [(rect(0, 0, 3.4, 1.1), G)]), ('-z', [(rect(0, 0, 3.4, 1.1), G)])])
    for zz in (3.0, -3.0):
        for sx in (-1, 1): sc.box(M @ T(sx * 2.05, .8, zz), (.6, 1.6, 1.6), (26, 26, 32))
    ph = int(t * 6) % 2
    for sx, col in ((-1, (255, 40, 50)), (1, (50, 110, 255))):
        k = on * (1.0 if (sx > 0) == bool(ph) else .25)
        sc.box(M @ T(sx * .8, 4.1, -.5), (1.4, .4, .6), mix((90, 90, 100), col, .3 + .7 * k), shadow=False, unlit=True)
        p = xf(M, [(sx * .8, 4.3, -.5)])[0]
        if k > .3: glow(sc, p, 5, col, .9 * k); light(sc, p, tuple(c / 255 for c in col), 16, 1.1 * k, 0)
    for sx in (-1, 1): sc.text(xf(M, [(sx * 2.24, 1.55, .3)])[0], "POLICE", .62, (255, 255, 255), stroke=B, bias=-2)
def dog3(sc, pos, yaw, t, sit=False, wag=True):
    M = T(*pos) @ RY(yaw); c = (236, 170, 90); d2 = (170, 108, 54); E = (25, 25, 30)
    b = 0 if sit else abs(math.sin(t * 13)) * .12
    Mb = M @ T(0, b, 0) @ (RX(-28) if sit else np.eye(4))
    sc.box(Mb @ T(0, 1.15, 0), (1.05, .95, 2.1), c)
    for i, (x, z) in enumerate(((-.36, .75), (.36, .75), (-.36, -.75), (.36, -.75))):
        a = 0 if sit else math.sin(t * 13 + (0 if i in (0, 3) else math.pi)) * 34
        sc.box(M @ T(x, .75 + b, z) @ RX(a) @ T(0, -.38, 0), (.3, .78, .3), d2)
    sc.box(Mb @ T(0, 1.55, -1.1) @ RX(-35 + (25 * math.sin(t * 18) if wag else 0)) @ T(0, .35, 0), (.2, .7, .2), d2, shadow=False)
    Mh = Mb @ T(0, 1.9, 1.25)
    sc.box(Mh, (.98, .92, .92), c, decals=[('+z', [(ell(-.22, .12, .08, .11, 8), E), (ell(.22, .12, .08, .11, 8), E), (ell(0, -.12, .12, .08, 8), E)])])
    sc.box(Mh @ T(0, -.14, .58), (.5, .4, .3), (250, 225, 190), shadow=False, bias=-.1)
    for sx in (-1, 1): sc.box(Mh @ T(sx * .5, .3, -.1), (.16, .6, .4), d2, shadow=False)
    return xf(Mh, [(0, -.3, .8)])[0]

# ---------------------------------------------------------------- world
def day(sunset=0.0):
    sc = scene('day')
    if sunset:
        sc = Scene(sun=(-.6, -.62, -.3), amb=.66, dif=.50, sky=((255, 120, 90), (255, 220, 130)), fog=((255, 200, 140), 40, 170, .8), shadow=.40, shadow_col=(60, 20, 70))
        sc.lights = []; sc.glows = []; sc.lit = 1; sc.ambcol = (1.0, .86, .74)
    return sc
def env(sc, t, walkers=9, dogp=None, sunset=False):
    street(sc, t, on=lambda z: 1.0 if sunset else 0.0, day=True, strings=False, banner=False, hall=True)
    for i, z in enumerate((-9, -23, -37, -51)):
        for sd in (-1, 1): tree(sc, sd * 12.2, z + 3 * sd, .9 + .15 * (i % 2), night=False)
    for i, (x, z) in enumerate(((-11.6, 3), (11.4, -3), (-11.2, -16), (11.8, -29))):
        for j in range(3): sc.sprite((x + j * .5 - .5, .35, z + (j % 2) * .4), .22, .22, ((255, 90, 150), (255, 220, 60), (255, 255, 255))[(i + j) % 3], bias=-1)
    # bus stop
    bx(sc, -8.2, 3.2, -11, .22, 6.4, .22, (60, 66, 90)); sc.box(T(-8.2, 6.0, -11), (2.2, 1.5, .2), (40, 120, 250), shadow=False); sc.text((-8.2, 6.0, -10.8), "BUS", .9, (255, 255, 255), bias=-2)
    bx(sc, -9.2, .9, -14.5, 1.2, .3, 4.4, (240, 190, 70)); bx(sc, -9.2, .45, -13, .9, .9, .3, (90, 90, 110)); bx(sc, -9.2, .45, -16, .9, .9, .3, (90, 90, 110))
    for i, (x, z, c) in enumerate(((0, 60, 1), (-40, -30, .8), (46, -60, 1.2))):
        pass
    r = random.Random(11)
    for i in range(walkers):
        sd = r.choice((-1, 1)); x = sd * r.uniform(7.0, 9.8); dr_ = r.choice((-1, 1)); sp = r.uniform(1.7, 2.8)
        z = ((r.uniform(0, 46) + dr_ * sp * t) % 46) - 52
        folk(sc, i + 30, (x, 0, z), 0 if dr_ > 0 else 180, walk(t + i * .3, 1.7, 28), lant=None, kid=(i % 4 == 2))
    for i in range(4):
        x = ((i * 31 + t * (3 + i)) % 120) - 60; sc.sprite((x, 30 + i * 3, -90 - i * 6), 9 + i, 2.6, (255, 255, 255), bias=50); sc.sprite((x + 5, 31.6 + i * 3, -90 - i * 6), 5, 2.2, (255, 255, 255), bias=50)

CROWD = [(-7.4, -.6), (-6.2, -3.4), (-4.2, -5.4), (-1.6, -6.6), (1.2, -6.9), (3.8, -6.0), (6.0, -4.0), (7.4, -1.2), (-5.6, -6.6), (5.4, -7.2), (0, -9.0)]
HOME = [(-9, 4), (-9.4, -12), (-8.6, -20), (-3, -22), (3, -24), (8.8, -18), (9.2, -10), (9.4, 5), (-8, -28), (8, -30), (0, -32)]
MOODS = dict(look=dict(eyes='open', mouth='flat', brows='up'), laugh=dict(eyes='happy', mouth='grin'), gasp=dict(eyes='wide', mouth='open', brows='up'),
             smile=dict(eyes='open', mouth='smile'), mad=dict(eyes='open', mouth='frown', brows='angry'))
def crowd(sc, t, g=1.0, mood='look', at=(0, 3, 0), skip=(), film=True, n=11):
    for i in range(n):
        if i in skip: continue
        gi = clamp(g * 1.6 - (i % 5) * .15); e = smooth(gi)
        p = V(lerp(HOME[i][0], CROWD[i][0], e), 0, lerp(HOME[i][1], CROWD[i][1], e)); kidf = i in (2, 6)
        moving = 0 < gi < 1
        yaw = yaw_to(p, (CROWD[i][0], 0, CROWD[i][1])) if moving else yaw_to(p, at)
        if gi == 0: yaw = (0, 180)[i % 2]
        m = mood if gi > .5 else 'smile'
        if moving: pose = walk(t + i, 2.0, 34)
        elif m == 'laugh': pose = dict(y=.16 * abs(math.sin(t * 11 + i * 1.7)), al=(30 + 20 * math.sin(t * 11 + i), 20), ar=(100 if i % 3 == 0 else 30, 10), lean=-8 + 10 * math.sin(t * 11 + i), head=(0, 10))
        elif m == 'gasp': pose = dict(al=(135, -22), ar=(135, -22), lean=-10, head=(0, 4)) if i % 2 else dict(al=(20, 40), ar=(20, 40), lean=-12)
        else: pose = idle(t, i)
        look = {}
        if i == 3 and film and gi >= 1: pose = dict(pose); pose['ar'] = (112, -8); pose['al'] = (112, -8)
        c = folk(sc, i + 3, tuple(p), yaw, pose, face=MOODS[m], lant=None, kid=kidf)
        if i == 3 and film and gi >= 1:
            hp = (c['hand_l'] + c['hand_r']) / 2 + V(0, .3, 0); sc.box(T(*hp) @ RY(yaw), (.5, .9, .1), (20, 20, 26), shadow=False, bias=-1)
            sc.sprite(hp + V(0, .28, -.1), .07, .07, (255, 40, 40) if int(t * 2) % 2 else (120, 20, 20), bias=-2)

# ---------------------------------------------------------------- overlays
BANG = "fonts/Bangers-Regular.ttf"; FRE = "fonts/Fredoka.ttf"; LG = "fonts/LuckiestGuy-Regular.ttf"
def bigtext(txt, pt, k, size=150, col=(255, 235, 70), rot=0, st=(20, 16, 50)):
    def f(dr):
        if k <= 0: return
        s = int(size * (.55 + .45 * ease_out(min(1, k * 5))) * (1 + .05 * math.sin(k * 30)))
        f_ = font(s, BANG)
        if rot:
            tmp = Image.new('RGBA', (int(s * len(txt) * .7) + 80, int(s * 1.6)), (0, 0, 0, 0)); d2 = ImageDraw.Draw(tmp)
            d2.text((tmp.width / 2, tmp.height / 2), txt, font=f_, fill=col + (255,), anchor='mm', stroke_width=int(s * .09), stroke_fill=st + (255,))
            tmp = tmp.rotate(rot, expand=True, resample=Image.BICUBIC); dr._image.paste(tmp, (int(pt[0] - tmp.width / 2), int(pt[1] - tmp.height / 2)), tmp)
        else: dr.text(pt, txt, font=f_, fill=col + (255,), anchor='mm', stroke_width=int(s * .09), stroke_fill=st + (255,))
    return f
def rays(k, col=(255, 255, 255), c=(W / 2, H * .42)):
    def f(dr):
        for i in range(14):
            a = i * 2 * math.pi / 14 + k * .6; b = a + .11
            dr.polygon([c, (c[0] + math.cos(a) * 2400, c[1] + math.sin(a) * 2400), (c[0] + math.cos(b) * 2400, c[1] + math.sin(b) * 2400)], fill=col + (34,))
    return f
def idcard(k, cy=.40, s=1.0, ring=0.0, age=0.0, tilt=0):
    def f(dr):
        if k <= 0: return
        z = s * (.3 + .7 * ease_out(min(1, k * 4))) * (1 + .04 * math.sin(min(1, k * 4) * math.pi)); w, h = 900, 580
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, w - 1, h - 1], 46, fill=(250, 250, 255, 255), outline=(20, 30, 80, 255), width=10)
        d.rounded_rectangle([10, 10, w - 11, 120], 38, fill=(40, 110, 250, 255)); d.rectangle([10, 80, w - 11, 124], fill=(40, 110, 250, 255))
        d.text((w / 2, 68), "ID CARD", font=font(76, LG), fill=(255, 255, 255, 255), anchor='mm')
        # photo
        d.rounded_rectangle([40, 160, 360, 540], 24, fill=(150, 220, 255, 255), outline=(20, 30, 80, 255), width=6)
        d.rectangle([92, 440, 308, 536], fill=(196, 110, 240, 255))
        d.rounded_rectangle([118, 236, 282, 430], 30, fill=(248, 208, 184, 255))
        d.rounded_rectangle([108, 214, 292, 270], 20, fill=(236, 236, 242, 255)); d.ellipse([160, 168, 240, 232], fill=(236, 236, 242, 255))
        for x in (160, 240):
            d.ellipse([x - 13, 300, x + 13, 334], fill=(25, 25, 30, 255)); d.ellipse([x - 30, 286, x + 30, 348], outline=(200, 40, 90, 255), width=6)
        d.arc([156, 340, 244, 408], 20, 160, fill=(25, 25, 30, 255), width=8)
        for i in range(8):
            x = 124 + i * 22; y = 446 + 30 * math.sin((i + .5) / 8 * math.pi); d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=(255, 255, 255, 255), outline=(170, 170, 190, 255), width=2)
        if ring > 0: d.ellipse([84, 410, 316, 524], outline=(255, 60, 50, 255), width=int(12 * min(1, ring * 3)) + 1)
        d.text((400, 190), "NAME", font=font(40, FRE), fill=(90, 100, 140, 255), anchor='ls')
        d.text((400, 280), "MARGARET", font=font(86, LG), fill=(20, 30, 80, 255), anchor='ls')
        d.text((400, 360), "AGE", font=font(40, FRE), fill=(90, 100, 140, 255), anchor='ls')
        a = 150 + int(40 * age * abs(math.sin(age * 9)))
        d.text((400, 372 + 75, ), "74", font=font(a, LG), fill=(240, 50, 50, 255) if age > 0 else (20, 30, 80, 255), anchor='lm')
        im = im.resize((int(w * z), int(h * z)), Image.LANCZOS)
        if tilt: im = im.rotate(tilt, expand=True, resample=Image.BICUBIC)
        x = int(W / 2 - im.width / 2); y = int(H * cy - im.height / 2)
        sh = Image.new('RGBA', im.size, (0, 0, 0, 90)); dr._image.paste(sh, (x + 14, y + 18), im.split()[3].point(lambda v: v * 90 // 255))
        dr._image.paste(im, (x, y), im)
    return f
def PP(**k):
    d = dict(sat=1.34, bloom=.5, vig=.22, con=1.08, tint=(1.03, 1.0, .97)); d.update(k); return d

# ---------------------------------------------------------------- shots
PULL = 1.42
class Cam2(Cam):
    def __init__(s, pos, target, fov=40, roll=0, pull=None):
        pos = V(*pos); target = V(*target); Cam.__init__(s, target + (pos - target) * (pull or PULL), target, fov, roll)

RP = V(-1.5, 0, 0); KP = V(1.9, 0, 0)
def A(lt, d, t):       # I picked a wallet up off the sidewalk
    k = smooth((lt - .35) / .7); sc = day(); env(sc, t); crowd(sc, t, 0)
    dog3(sc, (5.4, 0, -4 + t * 1.2), 0, t)
    kz = lerp(-13, -4.6, clamp(lt / d)); kevin(sc, (1.2, 0, kz), yaw_to((1.2, 0, kz), RP), run(t, 3.2), dict(eyes='wide', mouth='open', brows='angry'))
    pose = dict(lean=lerp(38, 0, k), ll=lerp(40, 0, k), lr=lerp(-30, 0, k), y=lerp(-.5, 0, k), al=(lerp(30, 70, k), 6), ar=(10, 6), head=(0, lerp(30, 6, k)))
    c = red(sc, tuple(RP), 20, pose, dict(eyes='open' if k < .6 else 'wide', mouth='o' if k < .6 else 'smile', brows='up'), wal='l')
    cam = Cam2(lerp(V(.6, 1.0, 6.2), V(.4, 2.6, 8.6), k), lerp(V(-1.0, 1.6, 0), V(-.6, 2.9, 0), k), 46)
    return sc, cam, PP()
B_HIT = .55
def B(lt, d, t):       # and some guy grabbed my arm and screamed
    h = ease_out(clamp(lt / B_HIT)); hit = lt >= B_HIT; sc = day(); env(sc, t); crowd(sc, t, 0)
    dog3(sc, (5.4, 0, -4 + t * 1.2), 0, t)
    kp = lerp(V(1.2, 0, -4.6), V(.75, 0, -.5), h)
    kevin(sc, tuple(kp), yaw_to(kp, RP + V(.4, 0, .4)), dict(ar=(84, 4), al=(20, 20), lean=14) if h > .7 else run(t, 3.2), dict(eyes='wide', mouth='open', brows='angry'))
    j = math.sin(t * 40) * .5 * pulse(lt, B_HIT, .4)
    red(sc, tuple(RP), 20 + 14 * hit, dict(al=(74, 14), ar=(30 * hit, 30 * hit), lean=-8 * hit, head=(-40 * hit, 6), roll=j * 4), dict(eyes='wide', mouth='open' if hit else 'smile', brows='up', look=(-1, 0)), wal='l')
    cam = Cam2(V(.6, 2.9, 8.2 - .8 * h) + shake(t, .22 * pulse(lt, B_HIT, .35)), V(-.3, 3.1, -.2), 46)
    ov = [bigtext("!?", (W * .25, H * .2), (lt - B_HIT) * 1.5, 230, (255, 60, 50), 12)] if hit else []
    return sc, cam, PP(flash=.5 * pulse(lt, B_HIT, .12), overlay=ov)
def C(lt, d, t):       # THIEF!
    sc = day(); env(sc, t, walkers=0)
    red(sc, (-2.4, 0, 1.6), 150, dict(al=(74, 14), lean=-6), dict(eyes='wide', mouth='o', brows='up'), wal='l')
    kevin(sc, (0, 0, 0), 4, dict(ar=(96, -14), al=(30, 34), lean=10, head=(0, -6), y=.06 * math.sin(t * 40)), dict(eyes='wide', mouth='open', brows='angry', talk=.6 + .4 * abs(math.sin(t * 30))))
    z = ease_out(lt / .25)
    cam = Cam2(V(.4, 3.6, lerp(9, 6.2, z)) + shake(t, .16), V(0, 5.2, 0), 44, roll=-7)
    return sc, cam, PP(overlay=[rays(t, (255, 60, 40), (W / 2, H * .36)), bigtext("THIEF!", (W / 2, H * .185), lt, 330, (255, 50, 40), 6, (255, 255, 255))], vig=.4)
D_BALL = .45
def D(lt, d, t):       # He stole my wallet! - every head turns
    sc = day(); env(sc, t); g = .30 + .25 * clamp(lt / d)
    crowd(sc, t, g, 'gasp')
    r = random.Random(11)
    mp = dog3(sc, (5.2, 0, 2.4), -70, t, sit=True, wag=False)
    by = max(.3, mp[1] - 6 * max(0, lt - D_BALL) ** 2 + (1.2 * abs(math.sin((lt - D_BALL) * 9)) * max(0, 1 - (lt - D_BALL)) if lt > D_BALL + .4 else 0))
    sc.sprite((mp[0] - .1, by if lt > D_BALL else mp[1], mp[2] + .1), .3, .3, (120, 230, 60), bias=-2, shadow=True)
    kevin(sc, tuple(KP), -62, dict(ar=(92, 6), al=(28, 30), lean=8, y=.05 * math.sin(t * 40)), F('K', t, eyes='wide', mouth='open', brows='angry'))
    red(sc, tuple(RP), 62, dict(al=(60, 10), ar=(20, 40), lean=-8), dict(eyes='wide', mouth='o', brows='up', look=(math.sin(t * 7), 0)), wal='l')
    cam = Cam2(V(1.5, lerp(7.5, 6.6, lt / d), lerp(17, 15.5, lt / d)), V(0, 2.6, -2), 50, pull=1.05)
    return sc, cam, PP(overlay=[bigtext("?!", (W * .5, H * .12), lt - .1, 170, (255, 235, 70))])
def E_(lt, d, t):      # Sir, it was on the ground!
    sc = day(); env(sc, t); crowd(sc, t, .55 + .3 * lt / d, 'look', at=tuple(RP + V(0, 3, 0)))
    kevin(sc, (2.6, 0, -.6), -70, dict(al=(55, -34), ar=(55, -34)), dict(eyes='open', mouth='frown', brows='angry'))
    b = math.sin(t * 9)
    red(sc, tuple(RP), 38, dict(al=(80 + 6 * b, 20), ar=(40, 46), head=(18, 8), y=.03 * b), F('R', t, eyes='wide', mouth='o', brows='sad', look=(1, .5)), wal='l')
    cam = Cam2(V(-.4, 3.1, lerp(8.4, 7.6, lt / d)), V(-.9, 2.75, 0), 40)
    return sc, cam, PP()
def Fk(lt, d, t):      # There was a thousand dollars in there! Pay up, or I call the cops.
    pay = t >= ps(6) - .05; k = smooth((t - ps(6) + .05) / .25)
    sc = day(); env(sc, t); crowd(sc, t, 1, 'look', at=tuple(KP + V(0, 4, 0)))
    red(sc, (-2.2, 0, 1.2), 100, dict(al=(60, 10), head=(0, 14)), dict(eyes='wide', mouth='flat', brows='up'), wal='l')
    b = math.sin(t * 8)
    pose = dict(al=(lerp(55, 20, k), lerp(-34, 30, k)), ar=(lerp(55, 78, k), lerp(-34, 0, k)), lean=-4 + 10 * k, head=(0, -8), y=.03 * b)
    c = kevin(sc, tuple(KP), -38, pose, F('K', t, eyes='open', mouth='grin', brows='angry'))
    if pay:
        for i in range(3): sc.sprite(c['hand_r'] + V(-.1 + .12 * i, .3 + .25 * abs(math.sin(t * 9 + i)), .1), .1, .1, (255, 220, 60), bias=-2)
    cam = Cam2(V(.9, 3.4, lerp(9.6, 8.6, lt / d)), V(1.2, 3.9, 0), 42)
    ov = [bigtext("$1,000", (W * .5, H * .16), t - ps(5) - .45, 250, (90, 255, 110), -5)]
    if pay: ov = [bigtext("PAY UP", (W * .5, H * .16), t - ps(6), 250, (255, 235, 70), 5)]
    return sc, cam, PP(overlay=ov)
def G(lt, d, t):       # A thousand dollars?
    sc = day(); env(sc, t); crowd(sc, t, 1, 'look', at=tuple(RP + V(0, 3, 0)))
    k = smooth(lt / .4)
    red(sc, tuple(RP), 30, dict(al=(lerp(60, 62, k), -14), ar=(lerp(0, 58, k), -14), head=(0, lerp(8, -16, k))), F('R', t, eyes='open', mouth='flat', brows='flat'), wal='l')
    cam = Cam2(V(-.6, 3.3, 6.6), V(-1.1, 2.95, 0), 38)
    return sc, cam, PP()
def Hs(lt, d, t):      # Bro, there's a bus ticket and a coupon for free fries.
    sc = Scene(sun=(-.3, -1, -.6), amb=.78, dif=.36, sky=((20, 150, 255), (120, 230, 255)), shadow=0); sc.lights = []; sc.glows = []
    k1 = ease_out((t - ps(8) - .55) / .3); k2 = ease_out((t - ps(9) - .45) / .3); op = ease_out(lt / .3)
    br = (190, 110, 50); br2 = (140, 76, 36)
    for sx in (-1, 1):
        sc.box(T(sx * 1.52 * 1, 0, 0) @ RY(sx * lerp(80, 12, op)) @ T(0, 0, 0), (3.0, 2.3, .22), br, shadow=False)
        sc.box(T(sx * 1.52, -.25, .14) @ RY(sx * lerp(80, 12, op)), (2.6, 1.5, .1), br2, shadow=False, bias=-.2)
        sc.box(T(sx * 3.3, -1.6, .6) @ RZ(sx * 18), (1.2, 3.2, 1.2), (244, 198, 158), shadow=False, bias=-1); sc.box(T(sx * 3.9, -3.6, .6) @ RZ(sx * 18), (1.3, 2.2, 1.3), (240, 50, 50), shadow=False, bias=-1)
    if k1 > 0:
        M = T(-1.5, -.2 + 1.7 * k1, .3) @ RZ(8); sc.box(M, (2.3, 1.2, .04), (255, 255, 255), shadow=False, bias=-2 - k1)
        sc.box(M @ T(0, .42, .03), (2.3, .3, .02), (40, 120, 250), shadow=False, bias=-2.2 - k1)
        if k1 > .5: sc.text(xf(M, [(0, -.1, .1)])[0], "BUS TICKET", .34, (30, 40, 90), bias=-4)
    if k2 > 0:
        M = T(1.5, -.2 + 1.9 * k2, .3) @ RZ(-9); sc.box(M, (2.4, 1.3, .04), (255, 214, 50), shadow=False, bias=-2 - k2)
        sc.box(M @ T(-.78, 0, .03), (.5, .7, .02), (235, 40, 40), shadow=False, bias=-2.3 - k2)
        if k2 > .5: sc.text(xf(M, [(.3, .22, .1)])[0], "FREE", .42, (220, 30, 40), bias=-4); sc.text(xf(M, [(.3, -.25, .1)])[0], "FRIES", .42, (220, 30, 40), bias=-4)
    glow(sc, (0, .5, -2), 9, (255, 255, 200), .5)
    cam = Cam2(V(0, 2.2, lerp(15, 12.5, lt / d)), V(0, .9, 0), 40, pull=1.45)
    ov = []
    if k2 > 0: ov.append(bigtext("THAT'S IT.", (W / 2, H * .2), (t - ps(9) - .75), 200, (255, 235, 70), -4))
    return sc, cam, PP(overlay=ov, bloom=.3)
def mothpos(u):        # flight out of the wallet up to Kevin's hair
    a = V(-1.2, 2.6, .8); b = V(1.9, 6.7, .2); p = lerp(a, b, smooth(u)); return p + V(math.sin(u * 14) * .7 * (1 - u), math.sin(u * 9) * .5 * (1 - u) + 1.2 * math.sin(u * math.pi), .6 * math.sin(u * math.pi))
def I(lt, d, t):       # A moth flew out. Even he looked broke.  (crowd laughs, Kevin goes red)
    u = clamp(lt / 1.25); land = u >= 1; bl = smooth((t - ps(11)) / .8)
    sc = day(); env(sc, t); crowd(sc, t, 1, 'laugh' if lt > .9 else 'look', at=tuple(KP + V(0, 4, 0)))
    red(sc, tuple(RP), 62, dict(al=(96, -14), ar=(92, -14), head=(0, lerp(-16, 20, u))), F('R', t, eyes='open', mouth='grin' if land else 'o', brows='up', look=(1, 1)), wal='l')
    kevin(sc, tuple(KP), -50, dict(al=(8, 8), ar=(8, 8), head=(0, 26 * (1 - u) * 0 + 0), y=0), dict(eyes='wide', mouth='wobble', brows='up' if not land else 'angry', look=(0, 1)), blush=bl, mth=1 if land else None, t=t)
    if not land: moth(sc, tuple(mothpos(u)), t, 1.5)
    kk = smooth((lt - 1.2) / .6)
    cam = Cam2(lerp(V(.2, 3.6, 9.5), V(1.4, 5.2, 7.2), kk), lerp(V(.2, 3.6, 0), V(1.7, 5.3, 0), kk), 44)
    ov = []
    if lt > 1.0:
        for i, (x, y, r_) in enumerate(((.2, .15, 10), (.78, .2, -12), (.5, .09, 3))):
            ov.append(bigtext("HA" + "HA" * (i % 2), (W * x, H * y + 12 * math.sin(t * 14 + i)), lt - 1.0 - i * .15, 150, (255, 235, 70), r_))
    return sc, cam, PP(overlay=ov)
def J(lt, d, t):       # Because you already took it!
    sc = day(); env(sc, t); crowd(sc, t, 1, 'look', at=tuple(KP + V(0, 4, 0)))
    red(sc, (-2.4, 0, 1.4), 105, dict(al=(60, 10)), dict(eyes='open', mouth='flat', brows='flat'), wal='l')
    kevin(sc, tuple(KP), -42, dict(ar=(88, 8), al=(24, 30), lean=12, y=.05 * math.sin(t * 36)), F('K', t, eyes='wide', mouth='open', brows='angry'), blush=1, mth=1, t=t)
    cam = Cam2(V(.6, 3.6, 8.2) + shake(t, .05), V(1.3, 4.3, 0), 42, roll=4)
    return sc, cam, PP()
def K_(lt, d, t):      # In four seconds? I'm a kid, not a magician.
    mg = t >= ps(15) + .25; sh = smooth((t - ps(14)) / .25)
    sc = day(); env(sc, t); crowd(sc, t, 1, 'laugh' if t > pe(15) - .1 else 'look', at=tuple(RP + V(0, 3, 0)))
    kevin(sc, (2.8, 0, -.8), -70, dict(al=(8, 8), ar=(8, 8)), dict(eyes='open', mouth='frown', brows='angry'), blush=1, mth=1, t=t)
    c = red(sc, tuple(RP), 30, dict(al=(lerp(60, 40, sh), lerp(10, 58, sh)), ar=(lerp(10, 40, sh), lerp(6, 58, sh)), y=.1 * sh, head=(10, 4)), F('R', t, eyes='open', mouth='smile', brows='up' if sh < 1 else 'flat'), wal='l')
    if mg:
        h = c['head']; pk = ease_out((t - ps(15) - .25) / .2)
        sc.box(h @ T(0, 1.5, 0), (2.0, .12, 2.0), (26, 26, 34), shadow=False, bias=-1); sc.box(h @ T(0, 1.5 + .6 * pk, 0), (1.2, 1.2 * pk, 1.2), (26, 26, 34), shadow=False, bias=-1.2)
        sc.box(h @ T(0, 1.72, 0), (1.24, .22, 1.24), (240, 50, 50), shadow=False, bias=-1.4)
        for i in range(6):
            a = i * 1.05 + t * 3; sc.sprite(xf(h, [(math.cos(a) * 1.5, 1.4 + math.sin(a * 1.3) * .7, math.sin(a) * .6)])[0], .1, .1, (255, 240, 120), bias=-3)
    cam = Cam2(V(-.5, 3.2, lerp(7.8, 7.0, lt / d)), V(-1.0, 3.0, 0), 40)
    ov = [bigtext("4 SECONDS?", (W * .5, H * .15), t - ps(13) - .2, 190, (255, 235, 70), -4)] if t < ps(14) else []
    return sc, cam, PP(overlay=ov)
L_ARR = 1.0
def L_(lt, d, t):      # And the second they showed up, he started crying.
    a = ease_out(lt / L_ARR); cry = t >= ps(17) - .1; kn = smooth((t - ps(17) + .1) / .3)
    sc = day(); env(sc, t); crowd(sc, t, 1, 'look', at=tuple(KP + V(0, 3, 0)), skip=(5, 6, 9))
    pcar(sc, 6.2, lerp(-40, -6.5, a), 0, t)
    if a >= 1: cop(sc, (lerp(8.6, 4.4, smooth((lt - L_ARR) / .9)), 0, lerp(-5, -1.6, smooth((lt - L_ARR) / .9))), -60, walk(t, 1.8, 26) if lt < L_ARR + .9 else None, dict(eyes='open', mouth='flat', brows='flat'))
    red(sc, tuple(RP), 62, dict(al=(60, 10), head=(20, 6)), dict(eyes='wide', mouth='o' if cry else 'flat', brows='up', look=(1, 0)), wal='l')
    c = kevin(sc, (KP[0], -1.9 * kn * 1.12, 0), -30, dict(ll=lerp(0, -88, kn), lr=lerp(0, -88, kn), al=(lerp(8, 150, kn), -20 * kn), ar=(lerp(8, 150, kn), -20 * kn), head=(0, 12 * kn), y=.04 * math.sin(t * 30) * kn),
              dict(eyes='closed' if cry else 'open', mouth='open' if cry else 'grin', brows='sad' if cry else 'angry'), blush=.6, mth=1, t=t)
    if cry:
        for sx in (-1, 1):
            for i in range(4):
                u = ((t * 2.2 + i * .25) % 1); p = xf(c['head'], [(sx * (.3 + u * 1.3), .75 + .9 * u - 2.6 * u * u, .7)])[0]; sc.sprite(p, .11, .16, (90, 190, 255), bias=-3)
    kk = smooth((t - ps(17) + .2) / .4)
    cam = Cam2(lerp(V(-5, 6.0, 13), V(.8, 2.6, 9.0), kk), lerp(V(3.6, 2.8, -4), V(1.5, 2.6, 0), kk), 48, pull=1.15)
    ov = [bigtext("WAAAH!", (W * .5, H * .16), t - ps(17) - .3, 220, (90, 200, 255), 5)] if cry else []
    return sc, cam, PP(overlay=ov)
def M(lt, d, t):       # Officer, this kid robbed me!
    sc = day(); env(sc, t, walkers=5); pcar(sc, 6.2, -6.5, 0, t)
    crowd(sc, t, 1, 'look', at=(0, 3, 2), skip=(5, 6, 9, 3, 4))
    gulp = lt > 1.1
    red(sc, (-1.6, 0, 2.6), 16, dict(al=(60, 10), ar=(6, 6), head=(-30, 18), y=-.06 * pulse(lt, 1.1, .3)), dict(eyes='wide', mouth='wobble' if gulp else 'flat', brows='sad', look=(-1, 1)), wal='l')
    cop(sc, (.3, 0, -.4), -14, dict(al=(40, -30), ar=(40, -30), head=(-14, -14)), dict(eyes='open', mouth='flat', brows='angry'))
    c = kevin(sc, (3.4, -2.1, .8), -40, dict(ll=-88, lr=-88, ar=(96, 30), al=(140, -20), head=(-20, 14)), F('K', t, eyes='sad', mouth='open', brows='sad'), blush=.5, mth=1, t=t)
    for i in range(3):
        u = ((t * 2.2 + i * .33) % 1); sc.sprite(xf(c['head'], [(.3 + u * 1.2, .75 + .9 * u - 2.6 * u * u, .7)])[0], .11, .16, (90, 190, 255), bias=-3)
    cam = Cam2(V(-.4, 1.9, lerp(10.2, 9.4, lt / d)), V(-.3, 3.3, 0), 50)
    ov = [bigtext("GULP", (W * .2, H * .36), lt - 1.1, 130, (255, 255, 255), 10)] if gulp else []
    return sc, cam, PP(overlay=ov)
def N(lt, d, t):       # That's when I noticed the ID inside.
    k = smooth((lt - .5) / .7); sc = day(); env(sc, t, walkers=4); crowd(sc, t, 1, 'look', at=(0, 3, 2), skip=(3, 4))
    cop(sc, (2.6, 0, -1.6), -30, dict(al=(40, -30), ar=(40, -30), head=(-10, -10)), dict(eyes='open', mouth='flat', brows='angry'))
    c = red(sc, tuple(RP), 20, dict(al=(96, -18), ar=(92, -18), head=(0, lerp(10, -24, k))), dict(eyes='wide' if k < .9 else 'open', mouth='o' if k < 1 else 'smile', brows='up', look=(0, -1)), wal='l')
    hp = c['hand_l']; sc.box(T(hp[0] - .1, hp[1] + .25 + .3 * k, hp[2] + .05) @ RY(20), (.5, .34, .03), (250, 250, 255), shadow=False, bias=-1.5)
    sc.box(T(hp[0] - .1, hp[1] + .37 + .3 * k, hp[2] + .08) @ RY(20), (.5, .1, .03), (40, 110, 250), shadow=False, bias=-1.7)
    gl = .5 + .5 * math.sin(t * 9); glow(sc, (hp[0] - .1, hp[1] + .5, hp[2] + .3), 1.6, (255, 255, 200), .8 * k * gl)
    cam = Cam2(V(-.7, lerp(3.3, 2.9, k), lerp(7.2, 5.6, k)), V(-1.2, lerp(3.0, 2.9, k), 0), 38)
    ov = [bigtext("WAIT...", (W * .5, H * .15), lt - .9, 200, (255, 235, 70), -4)]
    return sc, cam, PP(overlay=ov, vig=.22 + .3 * k)
def O(lt, d, t):       # Sir. What's your name?
    sc = day(); env(sc, t, walkers=4); crowd(sc, t, 1, 'look', at=tuple(RP + V(0, 3, 0)))
    cop(sc, (3.4, 0, -1.8), -50, dict(al=(40, -30), ar=(40, -30)), dict(eyes='open', mouth='flat', brows='flat'))
    red(sc, tuple(RP), 34, dict(al=(20, 30), ar=(60, 6), head=(14, 8), lean=6), F('R', t, eyes='open', mouth='smile', brows='angry', look=(1, 0)), wal='r')
    cam = Cam2(V(-.5, 3.2, 6.6), V(-1.0, 2.95, 0), 38)
    return sc, cam, PP()
def P_(lt, d, t):      # ...Kevin.
    sc = day(); env(sc, t, walkers=4); crowd(sc, t, 1, 'look', at=tuple(KP + V(0, 4, 0)))
    kevin(sc, tuple(KP), -24, dict(al=(8, 30), ar=(120, -42), head=(0, -8)), F('K', t, eyes='open', mouth='grin', brows='up', look=(-1, 0)), mth=1, t=t)
    cam = Cam2(V(1.3, 4.6, 7.0), V(1.7, 4.9, 0), 38)
    return sc, cam, PP()
def Q(lt, d, t):       # Weird. Because this wallet belongs to Margaret. And she's seventy-four.
    ck = t - ps(27) + .05; ag = clamp((t - ps(28) - .3) / .8) if t > ps(28) + .3 else 0
    sc = day(); env(sc, t, walkers=4); crowd(sc, t, 1, 'gasp' if ck > .4 else 'look', at=tuple(RP + V(0, 3, 0)))
    kevin(sc, (2.8, 0, -.8), -66, dict(al=(8, 8), ar=(8, 8)), dict(eyes='wide', mouth='flat', brows='up', look=(-1, 0)), mth=1, t=t)
    up = smooth((lt - .3) / .4)
    c = red(sc, tuple(RP), 30, dict(al=(lerp(40, 150, up), 10), ar=(20, 20), head=(10, 6)), F('R', t, eyes='open', mouth='smile', brows='angry', look=(1, 0)), wal=None)
    hp = c['hand_l']; sc.box(T(hp[0], hp[1] + .3, hp[2]) @ RY(30), (.6, .42, .04), (250, 250, 255), shadow=False, bias=-1.5); sc.box(T(hp[0], hp[1] + .46, hp[2] + .02) @ RY(30), (.6, .1, .03), (40, 110, 250), shadow=False, bias=-1.7)
    cam = Cam2(V(-.2, 3.0, lerp(7.4, 8.2, clamp(ck))), V(-.7, lerp(3.1, 4.4, clamp(ck * 2)), 0), 42)
    ov = []
    if ck > 0: ov = [rays(t * .5, (255, 255, 255), (W / 2, H * .36)), idcard(ck, .36, 1.05, age=ag, tilt=-4)]
    return sc, cam, PP(overlay=ov, flash=.4 * pulse(ck, 0, .12))
def R(lt, d, t):       # That's an old photo. / You're wearing pearls. / It was a phase.
    pr = t >= ps(30) - .05 and t < ps(31) - .08; ph = t >= ps(31) - .08
    sc = day(); env(sc, t, walkers=4); crowd(sc, t, 1, 'laugh' if t > pe(31) - .15 else 'look', at=tuple(KP + V(0, 4, 0)))
    cop(sc, (4.6, 0, -1.4), -62, dict(al=(40, -30), ar=(40, -30), head=(0, -4)), dict(eyes='open', mouth='flat', brows='up' if ph else 'flat', look=(-1, 0)))
    red(sc, (-2.6, 0, 1.6), 100, dict(al=(120, 10)), F('R', t, eyes='open', mouth='smile', brows='flat'), wal=None)
    b = math.sin(t * 30) * .03
    c = kevin(sc, tuple(KP), -20, dict(al=(20, 34), ar=(30 if not ph else 140, 30 if not ph else -30), head=((-14 if pr else 10 * math.sin(t * 5)), -4), y=b),
              F('K', t, eyes='wide', mouth='wobble', brows='sad', look=(math.sin(t * 6), 0)), blush=.3 + .4 * ph, mth=1, t=t)
    for i in range(3):
        u = ((t * 1.3 + i * .37) % 1); sc.sprite(xf(c['head'], [((-.6, .62, -.45)[i], 1.1 - u * .9, .68)])[0], .09, .14, (120, 210, 255), bias=-3)
    cam = Cam2(V(1.5, 4.7, lerp(7.6, 6.9, lt / d)), V(1.9, 4.85, 0), 40)
    ov = [idcard(t - ps(30) + .05, .19, .62, ring=t - ps(30) - .2, tilt=5)] if pr else []
    return sc, cam, PP(overlay=ov)
def S_(lt, d, t):      # That's my wallet! He snatched it at the bus stop!
    w = smooth(lt / .8); sc = day(); env(sc, t, walkers=4)
    crowd(sc, t, 1, 'gasp', at=(-3.4, 3, -3), skip=(2, 3))
    for i, sx in ((2, -1), (3, 1)):
        p = (CROWD[i][0] + sx * 1.2 * w - 1.2, 0, CROWD[i][1]); folk(sc, i + 3, p, yaw_to(p, (-3, 0, -2)), dict(lean=-10, al=(20, 40), ar=(20, 40)), face=MOODS['gasp'], lant=None, kid=(i == 2))
    mp = lerp(V(-3.6, 0, -8.5), V(-3.2, 0, -2.2), w); b = math.sin(t * 20)
    marg(sc, tuple(mp), 16, dict(al=(96 + 5 * b, 4), ar=(20, 10), lean=10, ll=30 * math.sin(t * 16) * (w < 1), lr=-30 * math.sin(t * 16) * (w < 1), y=.05 * abs(b)), F('M', t, eyes='open', mouth='frown', brows='angry'))
    kevin(sc, (2.8, 0, .6), -80, dict(al=(8, 8), ar=(8, 8), lean=-10, head=(-30, 0)), dict(eyes='wide', mouth='open', brows='up', look=(-1, 0)), mth=1, t=t)
    red(sc, (-.2, 0, 1.8), -120, dict(ar=(60, 10), head=(-20, 0)), dict(eyes='wide', mouth='o', brows='up'), wal=None)
    cam = Cam2(V(-1.6, 3.0, lerp(8.2, 5.6, w)), V(-2.9, 2.9, -2.2), 44)
    ov = [bigtext("MARGARET!", (W * .5, H * .14), lt - .5, 200, (255, 150, 220), -4)]
    return sc, cam, PP(overlay=ov)
T_COVER = pe(34) + .08 - cut(34)
def T_(lt, d, t):      # I didn't run three blocks with that thing just to lose it to a kid!
    cov = lt >= T_COVER; sc = day(); env(sc, t, walkers=4); crowd(sc, t, 1, 'gasp' if cov else 'look', at=tuple(KP + V(0, 4, 0)))
    cop(sc, (4.8, 0, -1.2), -66, dict(al=(40, -30), ar=(40, -30)), dict(eyes='open', mouth='flat', brows='up' if cov else 'flat', look=(-1, 0)))
    b = math.sin(t * 34)
    pose = dict(al=(140, -30), ar=(140, -30), head=(0, 0), lean=-6) if cov else dict(al=(60 + 40 * b, 30), ar=(60 - 40 * b, 30), lean=12, y=.08 * abs(b), head=(8 * b, -6))
    kevin(sc, tuple(KP), -14, pose, dict(eyes='wide', mouth='flat', brows='up', look=(math.sin(t * 9), 0)) if cov else F('K', t, eyes='wide', mouth='open', brows='angry'), blush=0 if cov else 1, mth=1, t=t)
    z = clamp(lt / T_COVER)
    cam = Cam2(V(1.6, 4.4, lerp(9.2, 6.6, z) + 1.2 * ease_out((lt - T_COVER) / .2) * cov) + shake(t, .06 * (not cov)), V(1.9, 4.7, 0), 40, roll=-4 * (not cov))
    ov = [bigtext("...", (W * .5, H * .15), lt - T_COVER - .1, 260, (255, 255, 255))] if cov else []
    return sc, cam, PP(overlay=ov, flash=.3 * pulse(lt, T_COVER, .1))
U_CUFF = ps(36) + .35 - cut(35)
def U(lt, d, t):       # You have the right to remain silent. I'd start now.
    cf = lt >= U_CUFF; sc = day(); env(sc, t, walkers=4); crowd(sc, t, 1, 'laugh' if t > pe(36) - .1 else 'look', at=(2, 4, 0), skip=(4, 5))
    pcar(sc, 7.4, -7.5, 0, t)
    kevin(sc, (3.3, 0, .2), -60, dict(al=(40, -34), ar=(40, -34), head=(0, 24 if cf else 0), lean=8), dict(eyes='sad', mouth='frown' if cf else 'flat', brows='sad'), mth=1, t=t, cuffs=cf)
    cop(sc, (.6, 0, 0), 8, dict(al=(20, 20), ar=(8, 6), head=(-6, 0)), F('C', t, eyes='open', mouth='flat', brows='flat'))
    cam = Cam2(V(.9, 4.9, lerp(8.8, 7.8, lt / d)) + shake(t, .1 * pulse(lt, U_CUFF, .2)), V(1.5, 5.0, 0), 42)
    ov = [bigtext("CLICK", (W * .74, H * .40), lt - U_CUFF, 150, (255, 255, 255), -10)] if cf else []
    return sc, cam, PP(overlay=ov)
def V_(lt, d, t):      # Margaret gave me the coupon. Best fries I ever had. / Can I get one fry? / No.
    sc = day(1); env(sc, t, walkers=8, sunset=False)
    sc.box(T(0, 1.2, 1.2), (7.0, .3, 1.8), (255, 190, 60)); sc.box(T(0, 2.3, .4), (7.0, 1.6, .3), (255, 190, 60))
    for sx in (-1, 1): bx(sc, sx * 3.0, .6, 1.2, .3, 1.2, 1.6, (90, 90, 110))
    pcar(sc, -5.5, -9, 90, t, on=.6)
    ask = t >= ps(39) - .1; no = t >= ps(40) - .05
    cop(sc, (5.4, 0, -3.6), -30, dict(al=(40, -30), ar=(40, -30)), dict(eyes='open', mouth='smile' if no else 'flat', brows='flat'))
    kevin(sc, (3.2, 0, -2.4), -22, dict(al=(40, -34), ar=(40, -34), lean=16 * ask, head=(0, -10 * ask + 26 * no)), F('K', t, eyes='sad', mouth='frown', brows='sad'), mth=None, t=t, cuffs=True)
    mun = math.sin(t * 9)
    c = red(sc, (-1.2, 0, 1.3), 6, seat(.78, 1.35, ar=(66 + 30 * max(0, mun), -10), al=(60, 6), head=(34 * (ask and not no) - 10 * no, -4)), F('R', t, eyes='happy', mouth='grin'), wal=None)
    fries(sc, c['hand_r'] + V(0, .2, .1), .9)
    moth(sc, tuple(c['hand_r'] + V(.05, .95, .15)), t, 1.0, flap=False)
    m = marg(sc, (1.3, 0, 1.3), -6, seat(.80, 1.35, ar=(60, 6), al=(66 + 30 * max(0, -mun), -10), head=(0 if not ask else 0, -4)), F('M', t, eyes='closed' if no else 'happy', mouth='flat' if no else 'smile', brows='flat' if no else None), cane=False)
    fries(sc, m['hand_l'] + V(0, .2, .1), .9); wallet(sc, (0, 1.65, 1.5), 1.2, 0)
    k = clamp(lt / d)
    cam = Cam2(V(lerp(1.5, 1.1, k), lerp(3.9, 3.6, k), lerp(13.6, 12.6, k)), V(.7, 3.4, 0), 54, pull=1.0)
    ov = [bigtext("NO.", (W * .72, H * .2), t - ps(40) + .02, 300, (255, 150, 220), -6)] if no else []
    return sc, cam, PP(overlay=ov, tint=(1.05, .98, .93), bloom=.4, fade=clamp((t - END + .08) / .06))

SHOTS = [(0, A), (cut(1), B), (cut(2), C), (cut(3), D), (cut(4), E_), (cut(5), Fk), (cut(7), G), (cut(8), Hs), (cut(10), I), (cut(12), J), (cut(13), K_),
         (cut(16), L_), (cut(18), M), (cut(19), N), (cut(23), O), (cut(25), P_), (cut(26), Q), (cut(29), R), (cut(32), S_), (cut(34), T_), (cut(35), U), (cut(37), V_), (END, None)]

def events():
    ix = {fn.__name__: i for i, (t0, fn) in enumerate(SHOTS) if fn}; st = {n: SHOTS[i][0] for n, i in ix.items()}
    return dict(st=st, cuts=[t for t, f in SHOTS], end=END, dur=DUR, grab=st['B'] + B_HIT, thief=ps(2), ball=st['D'] + D_BALL, pay=ps(6), ticket=ps(8) + .55, coupon=ps(9) + .45,
                moth=st['I'], laugh1=st['I'] + 1.0, laugh2=pe(15) - .1, siren=st['L_'], cry=ps(17), gulp=st['M'] + 1.1, notice=st['N'] + .5, idpop=ps(27) - .05, age=ps(28) + .3,
                laugh3=pe(31) - .15, marg=st['S_'], cover=st['T_'] + T_COVER, cuff=st['U'] + U_CUFF, laugh4=pe(36) - .1, bench=st['V_'], no=ps(40))

# ================================================================ captions
SPK = dict(R=((255, 255, 255), (255, 226, 50)), K=((255, 176, 90), (255, 80, 60)), M=((255, 170, 225), (255, 90, 190)), C=((140, 205, 255), (60, 150, 255)))
def _groups():
    G_ = []
    for p in P:
        cur = []
        for w in p['words']:
            if cur and (len(cur) >= 3 or sum(len(x['w']) for x in cur) + len(w['w']) > 13):
                G_.append((cur, p['spk'])); cur = []
            cur.append(w)
        if cur: G_.append((cur, p['spk']))
    return G_
GROUPS = _groups()
def captions(img, t):
    for gi, (g, spk) in enumerate(GROUPS):
        t0 = g[0]['t0'] - .04; t1 = g[-1]['t1'] + .14
        if gi + 1 < len(GROUPS): t1 = min(t1, GROUPS[gi + 1][0][0]['t0'] - .04)
        if t0 <= t < t1 and t < END: break
    else: return img
    k = clamp((t - t0) / .09); sc_ = .78 + .22 * ease_out(k) + .06 * math.sin(k * math.pi)
    size = int((112 if spk != 'R' else 104) * sc_); f = font(size, LG); dr = ImageDraw.Draw(img)
    words = [w['w'].upper() for w in g]
    widths = [dr.textlength(w, font=f) for w in words]; sp = size * .26
    lines = [[]]; lw = 0
    for i, wd in enumerate(widths):
        if lines[-1] and lw + wd > W * .86: lines.append([]); lw = 0
        lines[-1].append(i); lw += wd + sp
    y = int(H * .715) - (len(lines) - 1) * size * .55
    base, hi = SPK[spk]
    for ln in lines:
        tw_ = sum(widths[i] for i in ln) + sp * (len(ln) - 1); x = (W - tw_) / 2
        for i in ln:
            act = g[i]['t0'] - .03 <= t < g[i]['t1'] + .03 or (i == len(g) - 1 and t >= g[i]['t0'])
            dr.text((x + 5, y + 7), words[i], font=f, fill=(0, 0, 0), anchor='ls', stroke_width=int(size * .1), stroke_fill=(0, 0, 0))
            dr.text((x, y), words[i], font=f, fill=hi if act else base, anchor='ls', stroke_width=int(size * .1), stroke_fill=(12, 12, 16))
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
