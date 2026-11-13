"""Short 2 world: lighting (point lights, glows, bloom), props, townsfolk and sets."""
import math, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, 'src')
from engine import *
from chars import *

WARM = (1.0, .78, .42)
SAT = [(238, 62, 62), (255, 196, 40), (52, 190, 110), (60, 130, 245), (170, 86, 230), (255, 120, 175), (40, 200, 215), (255, 140, 50)]
HOUSE = [(240, 90, 80), (255, 190, 60), (80, 170, 240), (120, 205, 120), (190, 120, 240), (255, 140, 170), (70, 205, 200), (250, 150, 70)]
PANTS = [(50, 70, 190), (60, 60, 80), (120, 70, 50), (30, 120, 110), (110, 60, 150)]
HAIR = [(66, 42, 30), (30, 30, 36), (236, 186, 80), (190, 84, 40), (120, 74, 50), (250, 120, 60), (240, 240, 245)]
SKINS = [(240, 192, 152), (206, 152, 110), (150, 104, 74), (252, 218, 188), (120, 80, 60)]

# ------------------------------------------------------------------ scene + light
_sky = {}
def night_sky(stars=.5, top=(8, 10, 40), bot=(64, 40, 120)):
    k = (round(stars, 1), top, bot)
    if k not in _sky:
        w, h = W * SS, H * SS; g = np.linspace(0, 1, h)[:, None] ** .8
        col = np.array(top)[None] * (1 - g) + np.array(bot)[None] * g
        a = np.repeat(col[:, None, :], w, 1).astype(np.float32); r = np.random.RandomState(5)
        img = Image.fromarray(a.astype(np.uint8)); dr = ImageDraw.Draw(img)
        for i in range(int(520 * stars)):
            x, y = r.randint(0, w), int(r.rand() ** 1.4 * h * .62); s = r.choice([2, 2, 3, 3, 4, 6]); b = r.randint(170, 256)
            dr.ellipse([x - s, y - s, x + s, y + s], fill=(b, b, min(255, b + 30)))
            if s == 6: dr.line([x - 16, y, x + 16, y], fill=(255, 255, 255), width=2); dr.line([x, y - 16, x, y + 16], fill=(255, 255, 255), width=2)
        _sky[k] = img
    return _sky[k]

def scene(mode='night', lit=1.0, stars=.3):
    """lit: 1 = every lamp in town blazing, 0 = true darkness."""
    if mode == 'day':
        sc = Scene(sun=(-.45, -1, -.35), amb=.70, dif=.46, sky=((40, 140, 255), (170, 225, 255)), fog=((170, 225, 255), 50, 190, .8), shadow=.36)
    elif mode == 'room':
        sc = Scene(sun=(-.3, -1, -.5), amb=.62, dif=.30, sky=((20, 20, 50), (40, 30, 80)), shadow=.22)
        sc.ambcol = tuple(lerp(a, b, lit) for a, b in zip((.20, .26, .62), (1.0, .93, .80)))
    else:
        sc = Scene(sun=(-.35, -1, -.45), amb=.56, dif=.24, sky=night_sky(stars), fog=(mix((10, 12, 40), (70, 44, 110), lit), 45, 170, .85), shadow=.26, shadow_col=(8, 8, 30))
        sc.ambcol = tuple(lerp(a, b, lit) for a, b in zip((.24, .30, .70), (.86, .74, .78)))
    sc.lights = []; sc.glows = []; sc.lit = lit
    return sc

def light(sc, pos, col=WARM, rad=15, inten=1.0, glow=.6, gr=4.0, gcol=None):
    if inten > 0: sc.lights.append((tuple(float(v) for v in pos), col, rad, inten))
    if glow > 0: sc.glows.append((V(*pos), gr, gcol or tuple(255 * c for c in col), glow))
def glow(sc, pos, r, col, st): sc.glows.append((V(*pos), r, col, st))

_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_vig = (((_xx - W / 2) / (W * .75)) ** 2 + ((_yy - H / 2) / (H * .75)) ** 2).astype(np.float32)
LUM = np.array([.3, .59, .11], np.float32)
def post(img, sc, cam, P):
    q = 4; h, w = H // q, W // q
    a = np.asarray(img, np.float32)
    # additive glows (halos round every lamp, window, eye)
    if sc.glows:
        buf = np.zeros((h, w, 3), np.float32)
        for pos, r, col, st in sc.glows:
            c = cam.to_cam(pos)
            if c[2] < .3: continue
            x = (W * SS / 2 + cam.f * c[0] / c[2]) / SS / q; y = (H * SS / 2 - cam.f * c[1] / c[2]) / SS / q; pr = min(500., cam.f * r / c[2] / SS / q)
            if pr < 1 or x < -pr or x > w + pr or y < -pr or y > h + pr: continue
            x0, x1 = max(0, int(x - pr)), min(w, int(x + pr) + 1); y0, y1 = max(0, int(y - pr)), min(h, int(y + pr) + 1)
            yy, xx = np.ogrid[y0:y1, x0:x1]
            g = np.clip(1 - np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / pr, 0, 1) ** 2 * st
            buf[y0:y1, x0:x1] += g[..., None] * np.array(col, np.float32)
        g = np.asarray(Image.fromarray(np.clip(buf, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32)
        a = a + g * (1 - a / 255)
    # bloom
    bl = P.get('bloom', .65)
    if bl:
        sm = np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((w, h), Image.BILINEAR), np.float32)
        br = sm * np.clip(((sm @ LUM) - 165) / 80, 0, 1)[..., None]
        b = Image.fromarray(br.astype(np.uint8)).filter(ImageFilter.GaussianBlur(7)).resize((W, H), Image.BILINEAR)
        a = a + np.asarray(b, np.float32) * bl * (1 - a / 300)
    sat = P.get('sat', 1.28)
    lum = (a @ LUM)[..., None]; a = lum + (a - lum) * sat
    a = (a - 118) * P.get('con', 1.08) + 118
    if 'tint' in P: a *= np.array(P['tint'], np.float32)
    v = P.get('vig', .30)
    if v: a *= (1 - np.clip(_vig * v * 1.6, 0, .92))[..., None]
    fl = P.get('flash', 0)
    if fl > 0: a += (255 - a) * min(1, fl)
    fd = P.get('fade', 0)
    if fd > 0: a *= (1 - min(1, fd))
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if P.get('overlay'):
        dr = ImageDraw.Draw(img, 'RGBA')
        for f in P['overlay']: f(dr)
    return img

def px(cam, p):
    c = cam.to_cam(p)
    if c[2] < .05: return (W / 2, H / 2)
    (x, y), = cam.proj([c]); return (x / SS, y / SS)
def shake(t, a):
    return V(math.sin(t * 37.1) + .5 * math.sin(t * 71.3), math.sin(t * 43.7 + 1) + .5 * math.sin(t * 83.9), 0) * a
def bx(sc, x, y, z, sx, sy, sz, col, yaw=0, **kw):
    return sc.box(T(x, y, z) @ RY(yaw), (sx, sy, sz), col, **kw)

# ------------------------------------------------------------------ props
def base(sc, col, half=140, y=-.02):
    sc.poly([(-half, y, -half), (-half, y, half), (half, y, half), (half, y, -half)], col, layer=0, bias=900)

def tiles(sc, x0, x1, z0, z1, cell, c1, c2=None, y=.0):
    c2 = c2 or c1; i = 0
    for x in np.arange(x0, x1 - 1e-6, cell):
        j = 0
        for z in np.arange(z0, z1 - 1e-6, cell):
            xe, ze = min(x + cell, x1), min(z + cell, z1)
            sc.poly([(x, y, z), (x, y, ze), (xe, y, ze), (xe, y, z)], c1 if (i + j) % 2 else c2, layer=0); j += 1
        i += 1

WIN_ON = (255, 226, 120, -1); WIN_OFF = (34, 40, 86)
def winset(fw, h, nx, ny, on, r, door=True, dark=()):
    out = []; any_on = False
    for i in range(nx):
        for j in range(ny):
            cx = -fw / 2 + fw * (i + .5) / nx; cy = -h / 2 + h * (j + .62) / ny
            if door and j == 0 and i == nx // 2 and nx % 2 == 1:
                out.append((rect(cx, -h / 2 + 2.3, 2.2, 4.6), (110, 66, 44))); out.append((ell(cx + .6, -h / 2 + 2.3, .2, .2, 8), (250, 210, 80))); continue
            l = r.random() < on and (i, j) not in dark; any_on |= l
            ww, wh = fw / nx * .56, h / ny * .46
            out.append((rect(cx, cy, ww + .5, wh + .5), (250, 250, 250)))
            out.append((rect(cx, cy, ww, wh), WIN_ON if l else WIN_OFF))
            if not l: out.append((rect(cx - ww * .2, cy + wh * .15, ww * .12, wh * .5, -20), (70, 80, 130)))
            else: out.append((rect(cx, cy, .22, wh), (250, 250, 250))); out.append((rect(cx, cy, ww, .22), (250, 250, 250)))
    return out, any_on

def house(sc, x, z, col, face='-x', w=11, h=12, d=10, on=1.0, seed=0, nx=3, ny=2, dark=()):
    r = random.Random(seed); fw = d if face in ('+x', '-x') else w
    wins, any_on = winset(fw, h, nx, ny, on, r, dark=dark)
    sc.box(T(x, h / 2, z), (w, h, d), col, decals=[(face, wins)])
    sc.box(T(x, h + .5, z), (w + 1.2, 1.0, d + 1.2), darker(col, .62))
    sc.box(T(x, h + 1.8, z), (w * .62, 1.6, d * .62), darker(col, .72))
    if any_on and on > .05:
        n = {'-x': (-1, 0), '+x': (1, 0), '+z': (0, 1), '-z': (0, -1)}[face]
        glow(sc, (x + n[0] * w / 2, h * .55, z + n[1] * d / 2), 8, (255, 190, 90), .30 * on)

def lamp(sc, x, z, on=1.0, h=8.5, side=1, flick=1.0):
    bx(sc, x, h / 2, z, .36, h, .36, (40, 44, 70))
    bx(sc, x - side * .8, h, z, 2.0, .28, .36, (40, 44, 70), shadow=False)
    p = (x - side * 1.6, h - .45, z)
    bx(sc, p[0], p[1] + .3, p[2], .9, .3, .9, (40, 44, 70), shadow=False)
    k = on * flick
    sc.sprite(p, .5, .5, mix((70, 74, 100), (255, 244, 190), k), layer=1, bias=-.5)
    if k > .03: light(sc, p, WARM, 17, 1.15 * k, .5 * k, 4.2)

STR = [(255, 70, 70), (255, 210, 50), (60, 220, 255), (255, 100, 220), (90, 255, 130)]
def stringlights(sc, z, on=1.0, y=9.4, x0=-9.5, x1=9.5, n=11, ph=0, t=0):
    for i in range(n):
        u = i / (n - 1); x = lerp(x0, x1, u); yy = y - 1.5 * math.sin(u * math.pi)
        c = STR[(i + ph) % 5]; tw = .75 + .25 * math.sin(t * 5 + i * 1.7 + z)
        if on > .03:
            sc.sprite((x, yy, z), .26, .26, c, layer=1); glow(sc, (x, yy, z), 1.5, c, .55 * on * tw)
        else: sc.sprite((x, yy, z), .2, .2, (50, 54, 90), layer=1)

def lantern(sc, p, on=1.0, s=1.0):
    sc.box(T(p[0], p[1] - .35 * s, p[2]), (.5 * s, .62 * s, .5 * s), mix((60, 64, 96), (255, 232, 140), on), unlit=True, shadow=False)
    sc.box(T(p[0], p[1], p[2]), (.6 * s, .12 * s, .6 * s), (50, 40, 40), shadow=False)
    if on > .03: light(sc, (p[0], p[1] - .3, p[2]), WARM, 8, .8 * on, .38 * on, 1.9)

def moths(sc, p, t, n=4, seed=0):
    r = random.Random(seed)
    for i in range(n):
        a = t * r.uniform(2.5, 4.5) + r.uniform(0, 6); rr = r.uniform(.8, 1.7)
        sc.sprite((p[0] + math.cos(a) * rr, p[1] + math.sin(a * 1.7) * .6 - .2, p[2] + math.sin(a) * rr), .09, .09, (255, 250, 220))

def zzz(sc, p, t, n=3, s=.8, col=(255, 255, 255)):
    for i in range(n):
        u = (t * .55 + i / n) % 1
        sc.text((p[0] + .9 * u + .3 * math.sin(u * 7), p[1] + 2.4 * u, p[2]), 'Z', s * (.5 + .8 * u), col + (int(255 * min(1, 2.5 * (1 - u))),), stroke=(20, 20, 60, int(255 * min(1, 2.5 * (1 - u)))), bias=-3)

# ------------------------------------------------------------------ people
def flook(i, kid=False, face=None, tired=False):
    r = random.Random(i * 13 + 5)
    L = dict(shirt=SAT[i % len(SAT)], pants=r.choice(PANTS), hair=r.choice(HAIR), skin=r.choice(SKINS),
             style=r.choice(['short', 'short', 'long', 'bun']), logo=r.choice([None, 'stripe', None]),
             face=face or (dict(eyes='tired', mouth='flat') if tired else dict(eyes='open', mouth='smile')))
    L.update(scale=r.uniform(.7, .78), head=1.18, sleeves='short') if kid else L.update(scale=r.uniform(.94, 1.05))
    return L
SCREAM = dict(eyes='wide', mouth='open', brows='up')
def folk(sc, i, pos, yaw=0, pose=None, face=None, lant=1.0, kid=False, tired=False, look=None):
    L = flook(i, kid, face, tired); L.update(look or {})
    c = character(sc, pos, yaw, pose, L)
    if lant is not None and lant is not False: lantern(sc, c['hand_r'], lant)
    return c

KID = dict(shirt=(240, 58, 58), pants=(48, 84, 215), hair=(84, 50, 30), skin=(242, 194, 154), scale=.76, head=1.2, sleeves='short', logo='stripe', shoes=(250, 250, 250))
def kid(sc, pos, yaw=0, pose=None, face=None, **o):
    L = dict(KID); L['face'] = face or {}; L.update(o)
    return character(sc, pos, yaw, pose, L)

MAYOR = dict(shirt=(128, 52, 196), pants=(60, 30, 110), hair=(240, 240, 245), skin=(248, 200, 170), scale=1.12, head=1.1, style='short', shoes=(30, 30, 40))
def mayor(sc, pos, yaw=0, pose=None, face=None, hat=True, bulbs=1.0, t=0):
    L = dict(MAYOR); L['face'] = face or dict(eyes='open', mouth='frown', brows='angry')
    c = character(sc, pos, yaw, pose, L); Mh = c['head']; Mt = c['torso']
    sc.box(Mh @ T(0, .40, .66), (.86, .16, .1), (240, 240, 245), shadow=False, bias=-.3)       # moustache
    if hat:
        sc.box(Mh @ T(0, 1.46, 0), (2.0, .14, 2.0), (30, 26, 50), bias=-.3)
        sc.box(Mh @ T(0, 2.1, 0), (1.3, 1.2, 1.3), (30, 26, 50), bias=-.35)
        sc.box(Mh @ T(0, 1.68, 0), (1.34, .26, 1.34), (255, 205, 60), bias=-.4, shadow=False)
    sc.box(Mt @ T(0, 1.5, .52), (.5, .9, .06), (255, 205, 60), shadow=False, bias=-.2)          # golden tie
    for i, (x, y) in enumerate(((-.62, 1.7), (.62, 1.7), (-.62, .9), (.62, .9), (-.62, .2), (.62, .2))):
        p = xf(Mt, [(x, y, .56)])[0]; k = bulbs * (.7 + .3 * math.sin(t * 6 + i * 2))
        sc.sprite(p, .15, .15, mix((90, 90, 110), (255, 244, 170), k), bias=-.4)
        if k > .05: glow(sc, p, .9, (255, 220, 110), .5 * k)
    return c

PETE = dict(shirt=(60, 170, 110), pants=(110, 80, 60), hair=(225, 225, 230), skin=(236, 196, 170), age=1.0, gray=1.0, scale=.98, head=1.1)
def shades(sc, c): sc.box(c['head'] @ T(0, .72, .67), (1.26, .34, .08), (16, 16, 22), shadow=False, bias=-.3); sc.box(c['head'] @ T(-.3, .78, .72), (.3, .08, .02), (120, 130, 160), shadow=False, bias=-.4)
def nightcap(sc, c, col=(60, 120, 250)):
    Mh = c['head']
    sc.box(Mh @ T(0, 1.5, 0), (1.42, .5, 1.42), col, bias=-.3); sc.box(Mh @ T(.25, 1.95, -.1), (.95, .5, .95), col, bias=-.35)
    sc.box(Mh @ T(.7, 2.2, -.2), (.55, .4, .55), col, bias=-.4); sc.sprite(xf(Mh, [(1.1, 2.1, -.2)])[0], .26, .26, (255, 255, 255), bias=-.5)

def dog(sc, pos, yaw, t, on=1.0, sleep=False, trot=True):
    M = T(*pos) @ RY(yaw); c = (226, 160, 84); d2 = (160, 100, 50)
    b = abs(math.sin(t * 13)) * .12 if trot and not sleep else 0
    M = M @ T(0, b - (.55 if sleep else 0), 0)
    sc.box(M @ T(0, 1.15, 0), (1.05, .95, 2.1), c)
    for i, (x, z) in enumerate(((-.36, .75), (.36, .75), (-.36, -.75), (.36, -.75))):
        a = 0 if sleep or not trot else math.sin(t * 13 + (0 if i in (0, 3) else math.pi)) * 34
        if not sleep: sc.box(M @ T(x, .75, z) @ RX(a) @ T(0, -.38, 0), (.3, .78, .3), d2)
    sc.box(M @ T(0, 1.55, -1.1) @ RX(-35 + (0 if sleep else 25 * math.sin(t * 18))) @ T(0, .35, 0), (.2, .7, .2), d2, shadow=False)
    E = (25, 25, 30)
    face = [(rect(-.22, .12, .13, .04) if sleep else ell(-.22, .12, .07, .1, 8), E), (rect(.22, .12, .13, .04) if sleep else ell(.22, .12, .07, .1, 8), E), (ell(0, -.12, .12, .08, 8), E), (rect(0, -.3, .3, .05), E)]
    Mh = M @ T(0, 1.85 - (.3 if sleep else 0), 1.25)
    sc.box(Mh, (.98, .92, .92), c, decals=[('+z', face)])
    sc.box(Mh @ T(0, -.14, .58), (.5, .4, .3), (250, 225, 190), shadow=False, bias=-.1)
    for sx in (-1, 1): sc.box(Mh @ T(sx * .5, .3, -.1), (.16, .6, .4), d2, shadow=False)
    # the flashlight strapped to its head
    sc.box(Mh @ T(0, .52, 0), (1.02, .12, .96), (230, 50, 50), shadow=False, bias=-.2)
    sc.box(Mh @ T(0, .78, .05), (.34, .34, .95), (70, 80, 110), shadow=False, bias=-.3)
    lp = xf(Mh, [(0, .78, .58)])[0]
    sc.sprite(lp, .2, .2, mix((80, 80, 100), (255, 250, 200), on), bias=-.5)
    if on > .05:
        a, b_, c_ = xf(Mh, [(0, .78, .6), (-1.7, -.6, 6.5), (1.7, -.6, 6.5)])
        sc.poly([a, b_, c_], (255, 240, 150), alpha=int(70 * on), unlit=True, bias=-1)
        f = xf(Mh, [(0, -1.5, 4.5)])[0]; light(sc, (f[0], .6, f[2]), WARM, 7, 1.0 * on, .55 * on, 1.6); glow(sc, lp, 1.6, (255, 240, 170), .7 * on)

def truck(sc, x, z, yaw=0):
    M = T(x, 0, z) @ RY(yaw)
    sc.box(M @ T(0, 4.2, -1.5), (5, 6, 9), (255, 200, 50), decals=[('+x', [(rect(0, .3, 6.4, 2.0), (250, 250, 250)), (rect(-1.6, .3, 1.2, 1.2), (240, 70, 70)), (rect(0, .3, 1.2, 1.2), (60, 130, 245)), (rect(1.6, .3, 1.2, 1.2), (60, 200, 120))]), ('-x', [(rect(0, .3, 6.4, 2.0), (250, 250, 250))])])
    sc.box(M @ T(0, 2.9, 4.4), (4.8, 3.4, 2.8), (240, 70, 60), decals=[('+z', [(rect(0, .5, 3.8, 1.5), (160, 220, 250)), (rect(-1.6, -1.0, .8, .5), (255, 250, 190, -1)), (rect(1.6, -1.0, .8, .5), (255, 250, 190, -1))]), ('+x', [(rect(.2, .5, 1.6, 1.4), (160, 220, 250))]), ('-x', [(rect(.2, .5, 1.6, 1.4), (160, 220, 250))])])
    for zz in (3.8, -3.6):
        for sx in (-1, 1): sc.box(M @ T(sx * 2.3, .9, zz), (.7, 1.8, 1.8), (30, 30, 36))

def tree(sc, x, z, s=1.0, night=True):
    g = (40, 150, 90) if night else (70, 190, 80)
    bx(sc, x, 2 * s, z, 1.0 * s, 4 * s, 1.0 * s, (120, 80, 50)); bx(sc, x, 5.4 * s, z, 4.2 * s, 3.2 * s, 4.2 * s, g); bx(sc, x, 7.5 * s, z, 2.7 * s, 1.5 * s, 2.7 * s, mix(g, (255, 255, 255), .12))

# ------------------------------------------------------------------ sets
LAMPZ = (2, -10, -22, -34, -46)
def street(sc, t=0, on=None, day=False, strings=True, banner=True, dark=None, near=True, fountain=False, hall=True):
    """Main street. on(z) -> 0..1 says how lit things at depth z are."""
    on = on or (lambda z: 1.0)
    base(sc, (60, 170, 80) if day else (34, 96, 70))
    tiles(sc, -6, 6, -64, 20, 3, (84, 88, 112), (92, 96, 122))
    tiles(sc, -10.5, -6, -64, 20, 3, (190, 186, 205), (176, 172, 196)); tiles(sc, 6, 10.5, -64, 20, 3, (190, 186, 205), (176, 172, 196))
    for z in np.arange(-62, 20, 6): sc.poly([(-.25, .01, z), (-.25, .01, z + 3), (.25, .01, z + 3), (.25, .01, z)], (255, 214, 70), layer=0, bias=-4)
    zs = [9, -4, -17, -30, -43, -56] if near else [-4, -17, -30, -43, -56]
    for i, z in enumerate(zs):
        for sd in (-1, 1):
            k = i * 2 + (sd > 0)
            house(sc, sd * 16.4, z, HOUSE[(k * 3 + 1) % 8], '+x' if sd < 0 else '-x', h=11 + (k * 5) % 4, on=on(z), seed=k + 40, dark=(dark or {}).get(k, ()))
    if hall:
        r = random.Random(3); wins, _ = winset(30, 16, 7, 3, on(-66), r)
        sc.box(T(0, 9, -70), (34, 18, 8), (250, 236, 200), decals=[('+z', wins)]); sc.box(T(0, 18.6, -70), (36, 1.2, 9), (200, 80, 80)); sc.box(T(0, 22, -70), (8, 6, 6), (250, 236, 200))
        if on(-66) > .05: glow(sc, (0, 10, -66), 16, (255, 200, 100), .35 * on(-66))
    for i, z in enumerate(LAMPZ):
        for sd in (-1, 1): lamp(sc, sd * 8.6, z + (3 if sd > 0 else -3), on(z), side=sd)
    if strings:
        for i, z in enumerate((-2, -14, -26, -38, -50)): stringlights(sc, z, on(z), ph=i, t=t)
    if banner:
        k = on(-8)
        sc.box(T(0, 12.6, -8), (17, 2.6, .2), mix((60, 30, 40), (255, 80, 90), .35 + .65 * k), unlit=True, shadow=False)
        sc.text((0, 12.6, -7.8), "100 YEARS OF LIGHT", 1.5, mix((90, 90, 110), (255, 250, 200), k), stroke=(90, 20, 40), bias=-1)
        for sx in (-1, 1): bx(sc, sx * 8.6, 10.5, -8, .16, 6.5, .16, (40, 44, 70), shadow=False)
    if fountain:
        sc.prism(T(0, .5, -8), 3.4, 1.0, (200, 200, 220), n=12); sc.prism(T(0, 1.02, -8), 2.9, .06, (70, 190, 255), n=12, shadow=False)

def room(sc, w=20, d=14, h=12, wall=(120, 200, 255), floor=(238, 190, 120), win=None, lit=1.0):
    tiles(sc, -w / 2, w / 2, -d / 2, d / 2 + 6, 2.5, floor, darker(floor, .93))
    dec = []
    if win:   # window in the back wall looking out on the glowing town
        cx, cy, ww, wh = win
        dec += [(rect(cx, cy - h / 2, ww + .8, wh + .8), (250, 250, 250)), (rect(cx, cy - h / 2, ww, wh), (255, 214, 120, -1)), (rect(cx, cy - h / 2, .3, wh), (250, 250, 250)), (rect(cx, cy - h / 2, ww, .3), (250, 250, 250))]
        for i in range(5): dec.append((rect(cx - ww / 2 + ww * (i + .5) / 5, cy - h / 2 - wh / 2 + .9 + (i % 3) * .5, ww / 7, 1.8 + (i % 3)), (250, 150, 70, -1)))
        glow(sc, (cx, cy, -d / 2 + .3), 5, (255, 190, 90), .5)
    sc.box(T(0, h / 2, -d / 2 - .25), (w, h, .5), wall, layer=0, shadow=False, decals=[('+z', dec + [(rect(0, -h / 2 + .4, w, .8), (250, 250, 250))])])
    sc.box(T(-w / 2 - .25, h / 2, 2), (.5, h, d + 6), darker(wall, .9), layer=0, shadow=False); sc.box(T(w / 2 + .25, h / 2, 2), (.5, h, d + 6), darker(wall, .9), layer=0, shadow=False)
    base(sc, darker(floor, .8), 60)

def floorlamp(sc, x, z, on=1.0, h=5.2, col=(255, 120, 170)):
    bx(sc, x, .12, z, 1.1, .24, 1.1, (60, 60, 80)); bx(sc, x, h / 2, z, .2, h, .2, (60, 60, 80))
    sc.prism(T(x, h + .5, z), .95, 1.2, mix(darker(col, .35), mix(col, (255, 255, 220), .5), on), n=10, shadow=False)
    if on > .03: light(sc, (x, h + .3, z), WARM, 12, .7 * on, .7 * on, 3.4)

def bed(sc, x, z, col=(70, 130, 250), w=4.4, l=7.4):
    bx(sc, x, .7, z, w, 1.4, l, (150, 100, 70)); bx(sc, x, 1.65, z, w - .2, .5, l - .2, (250, 250, 250))
    bx(sc, x, 2.3, z - l / 2 - .2, w, 3.4, .4, (130, 84, 56)); bx(sc, x, 2.15, z - l / 2 + 1.0, w - 1.2, .5, 1.5, (255, 255, 255))

# ------------------------------------------------------------------ The Dark
DK = (44, 30, 98); DK2 = (74, 54, 150)
def dark_body(sc, pos, s=1.0, eyes=1.0, mood='scary', t=0, blush=0.0):
    x, y, z = pos; b = math.sin(t * 1.4) * .25 * s
    for i, (r, hh, yy) in enumerate(((11, 9, 4.5), (10, 6, 11.5), (8.2, 5, 16.6), (5.6, 3, 20.2))):
        sc.prism(T(x, y + (yy + b * (i + 1) / 4) * s, z), r * s, hh * s, mix(DK, DK2, i * .12), n=16, shadow=False, bias=20 - i)
    ey = y + (15.2 + b) * s
    if eyes > .02:
        for sx in (-1, 1):
            p = (x + sx * 3.5 * s, ey, z + 8 * s)
            if mood == 'scary':
                sc.sprite(p, 1.9 * s, 2.3 * s * eyes, (255, 244, 170), bias=-30); sc.sprite((p[0], p[1] - .2 * s * eyes, p[2] + .1), .7 * s, 1.1 * s * eyes, (30, 20, 60), bias=-31)
                glow(sc, p, 9 * s, (255, 220, 120), .8 * eyes)
            else:   # sleepy, kind
                sc.sprite(p, 1.9 * s, 1.5 * s, (255, 246, 200), bias=-30); sc.sprite((p[0], p[1] - .35 * s, p[2] + .1), .85 * s, .85 * s, (30, 20, 60), bias=-31)
                sc.sprite((p[0] + .3 * s, p[1] - .1 * s, p[2] + .2), .28 * s, .28 * s, (255, 255, 255), bias=-32)
                sc.sprite((p[0], p[1] + 1.25 * s, p[2] + .15), 2.1 * s, .8 * s, mix(DK, DK2, .2), bias=-33, rect=True)     # heavy eyelid
                glow(sc, p, 7 * s, (255, 225, 150), .5)
    if mood != 'scary':
        for i in range(9):
            u = i / 8 - .5; sc.sprite((x + u * 5 * s, ey - 3.4 * s - (.25 - u * u) * 4.5 * s, z + 8.3 * s), .34 * s, .34 * s, (255, 246, 200), bias=-30)
        if blush:
            for sx in (-1, 1): glow(sc, (x + sx * 5.6 * s, ey - 2.4 * s, z + 8 * s), 2.6 * s, (255, 110, 170), .55 * blush)

def dark_hand(sc, M, s=1.0, curl=0.0, bias=0):
    """Blocky giant hand; local +y = along the fingers, palm faces -z."""
    c = (96, 74, 200); kw = dict(shadow=False, bias=bias)
    sc.box(M @ T(0, 0, 0), (5 * s, 5 * s, 1.6 * s), c, **kw)
    for i in range(4):
        Mf = M @ T((-1.86 + i * 1.24) * s, 2.5 * s, 0) @ RX(-curl * (30 + 6 * i))
        sc.box(Mf @ T(0, 1.4 * s, 0), (1.1 * s, 2.8 * s, 1.3 * s), (116, 92, 226), **kw)
    sc.box(M @ T(3.1 * s, -.3 * s, 0) @ RZ(-35) @ T(0, 1.2 * s, 0), (1.2 * s, 2.6 * s, 1.3 * s), (116, 92, 226), **kw)
    sc.box(M @ T(0, -6.5 * s, 0), (3.4 * s, 9 * s, 1.5 * s), (80, 60, 170), **kw)

def blanket(sc, M, w=3.4, l=3.2, t=0):
    cols = [(60, 110, 250), (80, 130, 255)]
    st = [(rect(-.9, .5, .5, .5, 45), (255, 226, 90)), (rect(.7, -.3, .5, .5, 45), (255, 226, 90)), (rect(-.2, -.9, .36, .36, 45), (255, 255, 255)), (rect(1.0, .9, .36, .36, 45), (255, 255, 255))]
    sc.box(M, (w, .5, l), cols[0], decals=[('+y', st)], shadow=False, bias=-1)
    sc.box(M @ T(0, .05, -l / 2 + .25), (w + .1, .56, .6), (255, 255, 255), shadow=False, bias=-1.2)
