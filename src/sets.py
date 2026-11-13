"""Sets and extras."""
import math, random
from engine import *
from chars import *

def bx(sc, x, y, z, sx, sy, sz, col, yaw=0, **kw):
    return sc.box(T(x, y, z) @ RY(yaw), (sx, sy, sz), col, **kw)

def windows(w, h, nx, ny, col=(150, 205, 240), mx=.12, my=.12):
    out = []; cw, ch = w / nx, h / ny
    for i in range(nx):
        for j in range(ny):
            out.append((rect(-w / 2 + cw * (i + .5), -h / 2 + ch * (j + .5), cw * (1 - 2 * mx) * .8, ch * (1 - 2 * my) * .7), col))
    return out

def tree(sc, x, z, s=1.0):
    bx(sc, x, 2 * s, z, 1.1 * s, 4 * s, 1.1 * s, (120, 80, 50))
    bx(sc, x, 5.6 * s, z, 4.6 * s, 3.4 * s, 4.6 * s, (70, 150, 70))
    bx(sc, x, 7.8 * s, z, 3 * s, 1.6 * s, 3 * s, (85, 170, 80))

def clouds(sc, seed=1, z=-90, n=7):
    r = random.Random(seed)
    for i in range(n):
        x = r.uniform(-70, 70); y = r.uniform(38, 60); w = r.uniform(12, 22)
        bx(sc, x, y, z - r.uniform(0, 30), w, 4, 8, (255, 255, 255), shadow=False, unlit=True, layer=0)
        bx(sc, x + w * .2, y + 3, z - 31, w * .5, 3.5, 6, (255, 255, 255), shadow=False, unlit=True, layer=0)

PAL_S = [(60, 120, 200), (240, 190, 60), (90, 170, 110), (220, 110, 60), (150, 90, 190), (230, 120, 160), (70, 180, 190), (240, 240, 240)]
PAL_P = [(50, 60, 100), (70, 70, 80), (110, 80, 60), (40, 90, 80), (90, 100, 130)]
PAL_H = [(60, 40, 30), (30, 30, 35), (210, 170, 90), (150, 75, 40), (110, 70, 50), (230, 120, 60)]
PAL_K = [(236, 188, 150), (200, 150, 110), (150, 105, 75), (250, 215, 185), (120, 80, 60)]
def extra_look(i, kid=False, gown=False, face=None):
    r = random.Random(i * 7 + 3)
    L = dict(shirt=r.choice(PAL_S), pants=r.choice(PAL_P), hair=r.choice(PAL_H), skin=r.choice(PAL_K),
             style=r.choice(['short', 'short', 'long', 'bun']), logo=r.choice([None, 'stripe', None]),
             face=face or dict(eyes=r.choice(['open', 'open', 'happy']), mouth=r.choice(['smile', 'grin', 'open', 'smile'])))
    if kid: L.update(scale=r.uniform(.68, .78), head=1.18, sleeves='short')
    else: L.update(scale=r.uniform(.94, 1.04))
    if gown: L.update(gown=True, cap=True)
    return L

def sky_day(): return ((70, 150, 245), (185, 225, 252))
FOG_DAY = ((185, 225, 252), 45, 170, .85)

def yard(sc, court=True, school_z=-34):
    sc.ground((98, 172, 86), grid=(108, 182, 96))
    if court:
        sc.poly([(-11, .01, -16), (-11, .01, 10), (11, .01, 10), (11, .01, -16)], (214, 170, 120), layer=0)
        for a in ([(-11, -16), (-11, 10), (-10.6, 10), (-10.6, -16)], [(10.6, -16), (10.6, 10), (11, 10), (11, -16)],
                  [(-11, -3.2), (-11, -2.8), (11, -2.8), (11, -3.2)], [(-11, -16), (-11, -15.6), (11, -15.6), (11, -16)], [(-11, 9.6), (-11, 10), (11, 10), (11, 9.6)]):
            sc.poly([(x, .02, z) for x, z in a], (250, 250, 250), layer=0)
    sc.box(T(0, 8, school_z), (56, 16, 10), (196, 108, 82), decals=[('+z', windows(52, 12, 9, 3) + [(rect(0, -5.2, 5, 5.6), (90, 60, 45))])])
    sc.box(T(0, 16.6, school_z), (58, 1.2, 11), (120, 70, 60))
    for x, z in ((-17, -20), (18, -22), (-24, -8), (25, -6), (-20, 6), (21, 8)): tree(sc, x, z, 1.25)
    clouds(sc)

def car(sc, x, z, col, yaw=0):
    M = T(x, 0, z) @ RY(yaw)
    sc.box(M @ T(0, 1.3, 0), (3.6, 1.5, 7.4), col, decals=[('+z', [(rect(-1.2, .1, .7, .4), (255, 240, 170)), (rect(1.2, .1, .7, .4), (255, 240, 170))]), ('-z', [(rect(-1.2, .1, .7, .4), (220, 40, 40)), (rect(1.2, .1, .7, .4), (220, 40, 40))])])
    sc.box(M @ T(0, 2.75, -.3), (3.2, 1.4, 4), mix(col, (255, 255, 255), .15), decals=[('+z', [(rect(0, 0, 2.7, 1.0), (150, 205, 240))]), ('-z', [(rect(0, 0, 2.7, 1.0), (150, 205, 240))]), ('+x', [(rect(0, 0, 3.4, 1.0), (150, 205, 240))]), ('-x', [(rect(0, 0, 3.4, 1.0), (150, 205, 240))])])
    for sx in (-1, 1):
        for sz in (-1, 1): sc.box(M @ T(sx * 1.75, .6, sz * 2.3), (.5, 1.2, 1.2), (35, 35, 40))

BCOL = [(214, 120, 96), (230, 196, 120), (120, 160, 200), (170, 190, 150), (200, 150, 180), (150, 140, 170), (225, 170, 110)]
def street(sc, rain=False, clock=True):
    sc.ground((120, 124, 132) if not rain else (95, 100, 112))
    sc.poly([(-6, .01, -120), (-6, .01, 60), (6, .01, 60), (6, .01, -120)], (72, 76, 86) if not rain else (58, 62, 74), layer=0)
    for z in range(-100, 40, 6):
        sc.poly([(-.25, .02, z), (-.25, .02, z + 3), (.25, .02, z + 3), (.25, .02, z)], (235, 225, 150), layer=0)
    for sx in (-1, 1):
        sc.poly([(sx * 6, .02, -120), (sx * 6, .02, 60), (sx * 6.5, .02, 60), (sx * 6.5, .02, -120)], (200, 200, 205), layer=0)
    r = random.Random(5); z = 30
    for sx in (-1, 1):
        z = 34
        while z > -70:
            d = r.uniform(12, 18); h = r.uniform(14, 34); col = r.choice(BCOL)
            face = '+x' if sx < 0 else '-x'
            ny = int(h // 4.5); nx = int(d // 4)
            sc.box(T(sx * 19, h / 2, z - d / 2), (12, h, d - .4), col, decals=[(face, windows(d - 2, h - 3, nx, ny))])
            sc.box(T(sx * 19, h + .5, z - d / 2), (12.8, 1, d), mix(col, (60, 60, 70), .4))
            z -= d
    for sx in (-1, 1):
        for z in (14, -6, -26, -46):
            tree(sc, sx * 9.5, z + (5 if sx > 0 else -4), .9)
            bx(sc, sx * 7.2, 4, z + (12 if sx > 0 else 3), .35, 8, .35, (60, 62, 70)); bx(sc, sx * 6.5, 8, z + (12 if sx > 0 else 3), 1.8, .3, .5, (60, 62, 70))
    if clock:
        H_ = 46
        sc.box(T(0, H_ / 2, -84), (14, H_, 14), (210, 190, 150), decals=[('+z', [(ell(0, 15, 5.4, 5.4, 28), (60, 50, 45)), (ell(0, 15, 4.8, 4.8, 28), (250, 246, 235)),
            (rect(0, 17.1, .5, 4.2), (40, 35, 35)), (rect(1.3, 15.9, .5, 3.2, -55), (40, 35, 35)), (ell(0, 15, .5, .5, 10), (190, 50, 50))] +
            [(rect(4.2 * math.sin(a), 15 + 4.2 * math.cos(a), .35, .9, -math.degrees(a)), (60, 50, 45)) for a in [i * math.pi / 6 for i in range(12)]])])
        sc.box(T(0, H_ + 3, -84), (10, 6, 10), (150, 70, 60))
    clouds(sc, 3)

def bench(sc, x, z, yaw=0):
    M = T(x, 0, z) @ RY(yaw); w = (150, 100, 60)
    sc.box(M @ T(0, 1.0, 0), (5, .25, 1.5), w); sc.box(M @ T(0, 1.9, -.7), (5, 1.3, .22), w)
    for sx in (-1, 1): sc.box(M @ T(sx * 2.2, .5, 0), (.3, 1, 1.4), (60, 62, 70))

def room(sc, floor=(205, 170, 125), wall=(238, 226, 200), w=22, d=14, h=13, back_decals=None, side=True, tiles=None):
    sc.ground(floor, half=40, grid=tiles, cell=2)
    sc.box(T(0, h / 2, -d / 2), (w, h, .5), wall, layer=0, shadow=False, decals=[('+z', back_decals or [])])
    sc.box(T(0, .35, -d / 2 + .3), (w, .7, .2), mix(wall, (120, 100, 80), .5), layer=0, shadow=False)
    if side:
        sc.box(T(-w / 2, h / 2, 0), (.5, h, d + 20), mix(wall, (0, 0, 0), .06), layer=0, shadow=False)
        sc.box(T(w / 2, h / 2, 0), (.5, h, d + 20), mix(wall, (0, 0, 0), .06), layer=0, shadow=False)

def kitchen(sc):
    win = [(rect(4.5, 2.2, 5.2, 4.2), (245, 245, 245)), (rect(4.5, 2.2, 4.6, 3.6), (150, 210, 245)), (rect(4.5, 2.2, .25, 3.6), (245, 245, 245)), (rect(4.5, 2.2, 4.6, .25), (245, 245, 245))]
    room(sc, floor=(232, 222, 205), wall=(250, 232, 190), back_decals=win, tiles=(214, 202, 184))
    bx(sc, -1, 1.7, -5.6, 14, 3.4, 2.2, (120, 160, 170), layer=0); bx(sc, -1, 3.5, -5.6, 14.3, .3, 2.5, (240, 240, 240), layer=0)
    bx(sc, -8.6, 4.2, -5.4, 3.6, 8.4, 2.6, (225, 230, 235), layer=0, decals=[('+z', [(rect(0, 1, 3.3, .1), (160, 165, 170)), (rect(-1.3, 1.9, .2, 1.2), (150, 155, 160)), (rect(-1.3, -.3, .2, 1.6), (150, 155, 160))])])
    bx(sc, -1, 8.6, -6.2, 9, 2.6, 1.2, (150, 100, 70), layer=0, decals=[('+z', [(rect(-2.2, 0, .12, 2.2), (110, 70, 50)), (rect(2.2, 0, .12, 2.2), (110, 70, 50))])])

def table(sc, x, z, w=7, d=4.4, h=2.6, col=(170, 115, 70)):
    bx(sc, x, h, z, w, .35, d, col)
    for sx in (-1, 1):
        for sz in (-1, 1): bx(sc, x + sx * (w / 2 - .4), h / 2, z + sz * (d / 2 - .4), .4, h, .4, mix(col, (0, 0, 0), .2))

def classroom(sc):
    board = [(rect(0, 1.2, 15, 5.6), (150, 110, 70)), (rect(0, 1.2, 14.2, 4.8), (50, 110, 80))]
    room(sc, floor=(196, 160, 118), wall=(226, 232, 214), w=26, d=20, back_decals=board, tiles=(184, 148, 108))

def desk(sc, x, z):
    bx(sc, x, 2.0, z, 3.4, .25, 2.2, (214, 180, 130)); bx(sc, x, 1, z + .7, 2.8, 2, .2, (120, 125, 135))

def bedroom(sc, night=True):
    wall = (86, 96, 150) if night else (150, 170, 220)
    win = [(rect(5, 2.4, 5.4, 4.6), (240, 240, 245)), (rect(5, 2.4, 4.8, 4.0), (22, 28, 70) if night else (150, 210, 245)), (ell(6, 3.3, .8, .8, 14), (250, 245, 200)),
           (rect(5, 2.4, .22, 4.0), (240, 240, 245)), (rect(-5.5, 2.5, 3.4, 4.4), (240, 200, 90)), (rect(-5.5, 2.5, 2.8, 3.8), (200, 80, 80)), (ell(-5.5, 2.6, .9, .9, 5), (250, 230, 120))]
    room(sc, floor=(150, 110, 80), wall=wall, w=24, d=14, back_decals=win, tiles=(140, 102, 74))
    sc.poly([(-6, .02, -5), (-6, .02, 3), (6, .02, 3), (6, .02, -5)], (90, 130, 190), layer=0)

def grad(sc):
    sc.ground((98, 172, 86), grid=(108, 182, 96))
    sc.poly([(-4, .01, -26), (-4, .01, 60), (4, .01, 60), (4, .01, -26)], (200, 60, 60), layer=0)
    sc.box(T(0, 9, -44), (60, 18, 10), (196, 108, 82), decals=[('+z', windows(56, 13, 9, 3))])
    sc.box(T(0, 18.6, -44), (62, 1.2, 11), (120, 70, 60))
    bx(sc, 0, 1, -30, 26, 2, 8, (150, 110, 80))
    for sx in (-1, 1): bx(sc, sx * 11, 7, -33, .6, 12, .6, (240, 240, 240))
    bx(sc, 0, 12, -33, 23, 4, .3, (40, 70, 150), shadow=False)
    sc.text((0, 12, -32.7), "CLASS OF 2026", 2.3, (255, 220, 80), stroke=(20, 30, 80), sw=.1)
    bx(sc, 0, 3.4, -29, 2.2, 2.8, 1.4, (120, 80, 55))
    r = random.Random(9)
    for i, (x, z) in enumerate(((-14, -22), (15, -24), (-22, -6), (23, -4), (-19, 10), (20, 12))): tree(sc, x, z, 1.25)
    for i in range(14):
        x = r.uniform(-24, 24); y = r.uniform(9, 17); z = r.uniform(-28, -20)
        sc.sprite((x, y, z), .9, 1.1, r.choice([(240, 80, 80), (250, 200, 70), (90, 150, 240), (120, 200, 120)]), hi=(255, 255, 255))
        bx(sc, x, y - 3, z, .06, 4, .06, (230, 230, 230), shadow=False)
    clouds(sc, 4)

def corridor(sc):
    sc.sky = ((228, 226, 214), (228, 226, 214))
    sc.ground((188, 176, 150), half=10, zrange=(-80, 14), xrange=(-6, 6), grid=(172, 160, 136), cell=3)
    lock = []
    for i in range(46):
        c = (70, 120, 170) if i % 2 == 0 else (62, 108, 156)
        lock.append((rect(-46 + i * 2.0, -1.4, 1.84, 7.4), c)); lock.append((rect(-46 + i * 2.0 + .6, -1.0, .16, .7), (30, 40, 60)))
        lock.append((rect(-46 + i * 2.0, 1.4, 1.2, .16), (40, 80, 120)))
    for sx in (-1, 1):
        sc.box(T(sx * 6, 5.5, -33), (.6, 11, 94), (236, 228, 206), layer=0, shadow=False, decals=[('-x' if sx > 0 else '+x', lock)])
    sc.poly([(-6, 11, -80), (6, 11, -80), (6, 11, 14), (-6, 11, 14)], (246, 244, 236), layer=0, unlit=True)
    for z in range(-70, 10, 10):
        sc.poly([(-1.6, 10.95, z), (1.6, 10.95, z), (1.6, 10.95, z + 3), (-1.6, 10.95, z + 3)], (255, 255, 245), layer=0, unlit=True)
    sc.box(T(0, 5.5, -80), (12.6, 11, .6), (214, 222, 222), layer=0, shadow=False,
           decals=[('+z', [(rect(0, 0, 5.2, 8.2), (60, 46, 38)), (rect(0, 0, 4.5, 7.5), (232, 246, 252)), ([(-2.25, 1.2), (-.4, 3.75), (.9, 3.75), (-2.25, -.6)], (255, 255, 255))])])

def bathroom(sc):
    sc.sky = ((150, 190, 196), (150, 190, 196))
    tiles = []
    for i in range(12):
        for j in range(8):
            tiles.append((rect(-11 + i * 2, -7 + j * 2, 1.86, 1.86), (168, 208, 212) if (i + j) % 2 else (156, 198, 204)))
    sc.box(T(0, 7, -5), (26, 16, .5), (130, 170, 178), layer=0, shadow=False, decals=[('+z', tiles)])
    sc.ground((120, 140, 150), half=30)
