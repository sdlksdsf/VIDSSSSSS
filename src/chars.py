"""Blocky R6-style character rig (head, torso, 2 arms, 2 legs) with decal faces."""
import math
from engine import *

SKIN = (236, 188, 150)
def darker(c, k=0.8): return tuple(x * k for x in c[:3])

def face_decals(f, skin, hair, age=0.0):
    eyes = f.get('eyes', 'open'); mouth = f.get('mouth', 'smile'); brows = f.get('brows'); talk = f.get('talk')
    ex, ey = 0.235, 0.10; P = []; K = (25, 25, 30); Wt = (250, 250, 250)
    look = f.get('look', (0, 0))
    for sx in (-1, 1):
        cx = sx * ex
        if eyes == 'open':
            P.append((ell(cx, ey, .078, .125), K)); P.append((ell(cx + .025, ey + .05, .025, .035, 8), Wt))
        elif eyes == 'wide':
            P.append((ell(cx, ey, .112, .14), Wt)); P.append((ell(cx + look[0] * .04, ey + look[1] * .04, .055, .068, 10), K))
        elif eyes == 'closed':
            P.append((rect(cx, ey - .02, .19, .04), K))
        elif eyes == 'happy':
            P.append((arc(cx, ey - .06, .1, .13, 20, 160, .045), K))
        elif eyes == 'tired':
            P.append((ell(cx, ey, .12, .10), Wt)); P.append((ell(cx + look[0] * .04, ey - .02 + look[1] * .03, .055, .06, 10), K))
            P.append((rect(cx, ey + .085, .27, .08), darker(skin, .9)))          # heavy lid
            P.append((arc(cx, ey - .03, .14, .13, 200, 340, .03), darker(skin, .68)))  # bag
            P.append((arc(cx, ey - .09, .15, .13, 215, 325, .022), darker(skin, .75)))
        elif eyes == 'sad':
            P.append((ell(cx, ey, .078, .11), K)); P.append((ell(cx + .025, ey + .04, .025, .03, 8), Wt))
    bc = darker(hair, .8)
    if brows == 'up':
        for sx in (-1, 1): P.append((rect(sx * ex, ey + .27, .2, .045, sx * -6), bc))
    elif brows == 'sad':
        for sx in (-1, 1): P.append((rect(sx * ex, ey + .24, .2, .045, sx * -16), bc))
    elif brows == 'angry':
        for sx in (-1, 1): P.append((rect(sx * ex, ey + .2, .2, .05, sx * 18), bc))
    elif brows == 'flat':
        for sx in (-1, 1): P.append((rect(sx * ex, ey + .22, .2, .045, 0), bc))
    my = -0.24
    if talk is not None:
        P.append((ell(0, my - .02, .12, .03 + .11 * talk, 12), (70, 25, 30)))
    elif mouth == 'smile':
        P.append((arc(0, my + .1, .27, .2, 205, 335, .05), K))
    elif mouth == 'grin':
        P.append((ell(0, my + .06, .25, .2, 12, 180, 360), (70, 25, 30))); P.append((rect(0, my + .035, .44, .05), Wt))
    elif mouth == 'open':
        P.append((ell(0, my - .02, .12, .14, 12), (70, 25, 30)))
    elif mouth == 'o':
        P.append((ell(0, my - .02, .075, .09, 12), (70, 25, 30)))
    elif mouth == 'flat':
        P.append((rect(0, my, .26, .045), K))
    elif mouth == 'frown':
        P.append((arc(0, my - .17, .22, .16, 35, 145, .048), K))
    elif mouth == 'wobble':
        P.append((rect(-.08, my, .13, .042, 12), K)); P.append((rect(.06, my, .13, .042, -12), K))
    if age > 0.5:
        a = int(255 * clamp((age - .5) * 2)); wc = darker(skin, .72) + (a,)
        P.append((rect(0, .45, .5, .022), wc)); P.append((rect(0, .385, .36, .02), wc))
        for sx in (-1, 1):
            P.append((rect(sx * .41, .03, .1, .02, sx * 25), wc)); P.append((rect(sx * .41, .1, .1, .02, sx * -20), wc))
            P.append((rect(sx * .33, -.2, .02, .2, sx * -14), wc))
    return P

def character(sc, pos, yaw=0, pose=None, look=None, shadow=True, hero=False, nohead=False):
    _start = len(sc.objs)
    p = dict(al=(0, 0), ar=(0, 0), ll=0, lr=0, head=(0, 0), lean=0, y=0, roll=0, pitch=0)
    p.update(pose or {})
    L = dict(skin=SKIN, shirt=(200, 50, 50), pants=(45, 60, 110), hair=(70, 45, 30), style='short', gray=0.0, age=0.0,
             scale=1.0, head=1.0, cap=False, gown=False, face={}, sleeves='long', logo=None, shoes=(40, 40, 45), streak=0.0)
    L.update(look or {})
    skin = mix(L['skin'], (214, 190, 172), 0.35 * clamp(L['age']))
    hair = mix(L['hair'], (205, 205, 210), L['gray'])
    shirt = (40, 44, 78) if L['gown'] else L['shirt']; pants = (36, 40, 72) if L['gown'] else L['pants']
    sil = L.get('sil')
    if sil: skin = hair = shirt = pants = sil; L['shoes'] = sil; L['logo'] = None; L['streak'] = 0
    sc_ = L['scale']
    root = T(*pos) @ RY(yaw) @ RZ(p['roll']) @ RX(p['pitch']) @ S(sc_) @ T(0, p['y'], 0)
    kw = dict(shadow=shadow)
    # legs
    for sx, a in ((1, p['ll']), (-1, p['lr'])):
        Ml = root @ T(sx * .5, 2, 0) @ RX(-a)
        if L['gown']:
            sc.box(Ml @ T(0, -1, 0), (.98, 2, .98), pants, **kw)
        else:
            sc.box(Ml @ T(0, -.85, 0), (.98, 1.7, .98), pants, **kw)
            sc.box(Ml @ T(0, -1.85, .04), (1.0, .3, 1.08), L['shoes'], **kw)
    Mt = root @ T(0, 2, 0) @ RX(p['lean'])
    dec = []
    if L['gown'] and not sil:
        dec.append(('+z', [(rect(0, .55, .5, .9), (235, 235, 235)), (rect(0, .3, .16, .7), (190, 40, 40))]))
    elif L['logo'] == 'clock':
        dec.append(('+z', [(ell(0, .25, .42, .42, 16), (245, 245, 245)), (rect(0, .38, .07, .3), (40, 40, 50)), (rect(.1, .25, .24, .07), (40, 40, 50))]))
    elif L['logo'] == 'stripe':
        dec.append(('+z', [(rect(0, .2, 2.0, .34), (245, 245, 245))]))
    elif L['logo'] == 'apron':
        dec.append(('+z', [(rect(0, -.1, 1.3, 1.7), (250, 240, 225))]))
    sc.box(Mt @ T(0, 1, 0), (2, 2, 1), shirt, decals=dec, **kw)
    # arms
    hands = {}
    for sx, (rx, rz) in ((1, p['al']), (-1, p['ar'])):
        Ma = Mt @ T(sx * 1.5, 2, 0) @ RZ(sx * rz) @ RX(-rx)
        hands[sx] = xf(Ma, [(0, -1.9, 0)])[0]
        if L['sleeves'] == 'short' and not L['gown']:
            sc.box(Ma @ T(0, -.4, 0), (.98, .8, .98), shirt, **kw); sc.box(Ma @ T(0, -1.4, 0), (.94, 1.2, .94), skin, **kw)
        else:
            sc.box(Ma @ T(0, -.72, 0), (.98, 1.44, .98), shirt, **kw); sc.box(Ma @ T(0, -1.72, 0), (.92, .56, .92), skin, **kw)
    # head
    if hero: sc.mark_hero(_start)
    if nohead: return dict(root=root, torso=Mt, hand_l=hands[1], hand_r=hands[-1])
    hs = L['head']; hy, hp = p['head']
    Mh = Mt @ T(0, 2, 0) @ RY(hy) @ RX(-hp) @ S(hs)
    r = 0.64
    sc.prism(Mh @ T(0, .62, 0), r, 1.24, skin, n=14, decals=[] if sil else [('+z', face_decals(L['face'], skin, hair, L['age']))], **kw)
    st = L['style']
    if st != 'bald':
        if not L['cap']:
            sc.box(Mh @ T(0, 1.33, -.03), (1.36, .26, 1.36), hair, bias=-.05, **kw)
        sc.box(Mh @ T(0, .78 if st != 'long' else .45, -.6), (1.36, .98 if st != 'long' else 1.7, .2), hair, **kw)
        for sx in (-1, 1):
            sc.box(Mh @ T(sx * .63, .88 if st != 'long' else .6, -.12), (.12, .66 if st != 'long' else 1.3, .9), hair, **kw)
        fr = sc.box(Mh @ T(0, 1.12, .58), (1.3, .2, .16), hair, bias=-.1, **kw)
        if L['streak'] > 0:
            sc.box(Mh @ T(.36, 1.14, .6), (.24, .24, .2), mix(hair, (215, 215, 220), L['streak']), bias=-.2, shadow=False)
            if not L['cap']: sc.box(Mh @ T(.36, 1.37, .25), (.24, .2, .7), mix(hair, (215, 215, 220), L['streak']), bias=-.2, shadow=False)
        if st == 'bun':
            sc.box(Mh @ T(0, 1.6, -.25), (.6, .5, .6), hair, **kw)
    if L['cap']:
        k = (34, 38, 68)
        sc.box(Mh @ T(0, 1.34, 0), (1.34, .3, 1.34), k, bias=-.05, **kw)
        sc.box(Mh @ T(0, 1.53, 0), (2.0, .08, 2.0), k, bias=-.3, **kw)
        sc.box(Mh @ T(.9, 1.3, .9), (.08, .5, .08), (240, 200, 60), bias=-.4, shadow=False)
    if hero: sc.mark_hero(_start)
    return dict(root=root, torso=Mt, head=Mh, hand_l=hands[1], hand_r=hands[-1])

def walk(t, rate=2.0, amp=32):
    s = math.sin(t * rate * 2 * math.pi) * amp
    return dict(ll=s, lr=-s, al=(-s * .9, 2), ar=(s * .9, 2), y=abs(math.cos(t * rate * 2 * math.pi)) * .08)
def run(t, rate=3.0, amp=55):
    s = math.sin(t * rate * 2 * math.pi) * amp
    return dict(ll=s, lr=-s, al=(-s, 4), ar=(s, 4), lean=12, y=abs(math.cos(t * rate * 2 * math.pi)) * .2)
def idle(t, ph=0):
    b = math.sin(t * 2.2 + ph)
    return dict(al=(b * 2, 3 + b), ar=(-b * 2, 3 + b), y=b * .015, head=(math.sin(t * .9 + ph) * 4, 0))
