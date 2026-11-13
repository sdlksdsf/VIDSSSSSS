"""Tiny software 3D engine for blocky (Roblox-style) scenes.
Painter's algorithm over convex parts, flat lambert shading, planar sun shadows,
distance fog, 2x supersampling. Pure numpy + Pillow."""
import math, numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, SS = 1080, 1920, 2
FONT = "fonts/LuckiestGuy-Regular.ttf"
_fonts = {}
def font(size, path=FONT):
    k = (path, int(size))
    if k not in _fonts: _fonts[k] = ImageFont.truetype(path, int(size))
    return _fonts[k]

def T(x, y, z):
    m = np.eye(4); m[:3, 3] = (x, y, z); return m
def S(x, y=None, z=None):
    y = x if y is None else y; z = x if z is None else z
    return np.diag([x, y, z, 1.0])
def _rot(a, i, j):
    a = math.radians(a); m = np.eye(4); c, s = math.cos(a), math.sin(a)
    m[i, i] = c; m[i, j] = -s; m[j, i] = s; m[j, j] = c; return m
def RX(a): return _rot(a, 1, 2)
def RY(a): return _rot(a, 2, 0)
def RZ(a): return _rot(a, 0, 1)
def V(*a): return np.array(a, dtype=float)
def lerp(a, b, t): return a + (b - a) * t
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)
def ease_out(t): t = clamp(t); return 1 - (1 - t) ** 3
def ease_in(t): t = clamp(t); return t ** 3
def mix(c1, c2, t): return tuple(lerp(a, b, t) for a, b in zip(c1, c2))
def hexc(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

# unit cube faces, ordered CCW seen from outside
_FN = {'+x': (0, 1), '-x': (0, -1), '+y': (1, 1), '-y': (1, -1), '+z': (2, 1), '-z': (2, -1)}
def _cube():
    faces = {}
    for name, (a, s) in _FN.items():
        u, v = (a + 1) % 3, (a + 2) % 3; pts = []
        for du, dv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            p = [0, 0, 0]; p[a] = s * .5; p[u] = du * .5; p[v] = dv * .5; pts.append(p)
        if s < 0: pts.reverse()
        faces[name] = np.array(pts, float)
    return faces
CUBE = _cube()

def xf(M, pts):
    pts = np.asarray(pts, float)
    return pts @ M[:3, :3].T + M[:3, 3]

class Cam:
    def __init__(s, pos, target, fov=40, roll=0):
        s.pos = V(*pos); f = V(*target) - s.pos; f /= np.linalg.norm(f)
        r = np.cross(f, V(0, 1, 0)); r /= np.linalg.norm(r); u = np.cross(r, f)
        if roll:
            a = math.radians(roll); r, u = r * math.cos(a) + u * math.sin(a), u * math.cos(a) - r * math.sin(a)
        s.R = np.stack([r, u, f]); s.f = (H * SS / 2) / math.tan(math.radians(fov) / 2); s.near = 0.15
    def to_cam(s, p): return (np.asarray(p, float) - s.pos) @ s.R.T
    def proj(s, c):
        return [(W * SS / 2 + s.f * x / z, H * SS / 2 - s.f * y / z) for x, y, z in c]
    def clip(s, c):
        out = []; n = len(c)
        for i in range(n):
            a, b = c[i], c[(i + 1) % n]; ia, ib = a[2] >= s.near, b[2] >= s.near
            if ia: out.append(a)
            if ia != ib:
                t = (s.near - a[2]) / (b[2] - a[2]); out.append(a + (b - a) * t)
        return out

class Scene:
    def __init__(s, sun=(-0.45, -1, -0.35), amb=0.62, dif=0.48, fog=None, sky=None, shadow=0.34, shadow_col=(15, 20, 45)):
        L = V(*sun); s.L = L / np.linalg.norm(L); s.amb, s.dif = amb, dif
        s.fog = fog            # (color, d0, d1, max)
        s.sky = sky            # (top, bottom) or PIL image
        s.objs = []; s.shadows = []; s.shadow = shadow; s.shadow_col = shadow_col; s.ground_y = 0.0
    def mark_hero(s, start):
        for o in s.objs[start:]: o['hero'] = True
    # ---- primitives
    def poly(s, pts, color, layer=1, bias=0, unlit=False, alpha=255, two_sided=True):
        pts = np.asarray(pts, float)
        s.objs.append(dict(k='mesh', faces=[(pts, color, None)], c=pts.mean(0), layer=layer, bias=bias, unlit=unlit, alpha=alpha, two=two_sided))
    def box(s, M, size, color, faces=None, shadow=True, layer=1, bias=0, decals=None, unlit=False, alpha=255, skip=()):
        Ms = M @ S(*size); fl = []
        for name, pts in CUBE.items():
            if name in skip: continue
            col = (faces or {}).get(name, color)
            fl.append((xf(Ms, pts), col, name))
        o = dict(k='mesh', faces=fl, c=xf(M, [(0, 0, 0)])[0], layer=layer, bias=bias, unlit=unlit, alpha=alpha, two=False, decals=[])
        for d in (decals or []): s._decal(o, M, size, d)
        s.objs.append(o)
        if shadow and alpha == 255:
            s.shadows.append(xf(Ms, [(x, y, z) for x in (-.5, .5) for y in (-.5, .5) for z in (-.5, .5)]))
        return o
    def _decal(s, o, M, size, d):
        # d = (face, [(pts2d, color), ...]) in local units on that face, origin = face centre
        face, polys = d; a, sg = _FN[face]; u, v = (a + 1) % 3, (a + 2) % 3
        if face in ('+z', '-z'): u, v = 0, 1
        if face in ('+x', '-x'): u, v = 2, 1
        if face in ('+y', '-y'): u, v = 0, 2
        n = np.zeros(3); n[a] = sg; nw = M[:3, :3] @ n; nw /= np.linalg.norm(nw)
        for pts2, col in polys:
            P = np.zeros((len(pts2), 3)); P[:, a] = sg * (size[a] / 2 + 0.012)
            flip = -1 if face in ('-z', '+x') else 1
            P[:, u] = [p[0] * flip for p in pts2]; P[:, v] = [p[1] for p in pts2]
            o['decals'].append((xf(M, P), col, nw))
    def prism(s, M, r, h, color, n=14, top=None, shadow=True, layer=1, bias=0, decals=None, rz=None):
        rz = r if rz is None else rz
        ang = [2 * math.pi * (i + .5) / n for i in range(n)]
        ring = [(r * math.sin(a), rz * math.cos(a)) for a in ang]
        fl = []
        for i in range(n):
            (x0, z0), (x1, z1) = ring[i], ring[(i + 1) % n]
            fl.append((xf(M, [(x0, -h / 2, z0), (x1, -h / 2, z1), (x1, h / 2, z1), (x0, h / 2, z0)]), color, None))
        fl.append((xf(M, [(x, h / 2, z) for x, z in ring]), top or color, None))
        fl.append((xf(M, [(x, -h / 2, z) for x, z in reversed(ring)]), color, None))
        o = dict(k='mesh', faces=fl, c=xf(M, [(0, 0, 0)])[0], layer=layer, bias=bias, unlit=False, alpha=255, two=False, decals=[])
        for d in (decals or []): s._decal(o, M, (2 * r, h, 2 * rz * math.cos(math.pi / n)), d)
        s.objs.append(o)
        if shadow: s.shadows.append(xf(M, [(x, y, z) for x, z in ring for y in (-h / 2, h / 2)]))
        return o
    def sprite(s, pos, rx, ry, color, hi=None, layer=1, bias=0, alpha=255, shadow=False, rect=False):
        s.objs.append(dict(k='sprite', c=V(*pos), rx=rx, ry=ry, col=color, hi=hi, layer=layer, bias=bias, alpha=alpha, rect=rect))
        if shadow:
            s.shadows.append(np.array([(pos[0] + rx * math.cos(a), pos[1], pos[2] + rx * math.sin(a)) for a in np.linspace(0, 6.28, 10)]))
    def text(s, pos, txt, size, color, stroke=None, sw=0.12, layer=1, bias=0, fontpath=FONT, bg=None, pad=0.3):
        s.objs.append(dict(k='text', c=V(*pos), txt=txt, size=size, col=color, stroke=stroke, sw=sw, layer=layer, bias=bias, fp=fontpath, bg=bg, pad=pad))
    def ground(s, color, half=120, grid=None, cell=4, y=0, zrange=None, xrange=None):
        x0, x1 = xrange or (-half, half); z0, z1 = zrange or (-half, half)
        s.poly([(x0, y, z0), (x0, y, z1), (x1, y, z1), (x1, y, z0)], color, layer=0)
        if grid:
            w = 0.06
            for x in np.arange(math.ceil(x0 / cell) * cell, x1 + .1, cell):
                s.poly([(x - w, y, z0), (x - w, y, z1), (x + w, y, z1), (x + w, y, z0)], grid, layer=0)
            for z in np.arange(math.ceil(z0 / cell) * cell, z1 + .1, cell):
                s.poly([(x0, y, z - w), (x0, y, z + w), (x1, y, z + w), (x1, y, z - w)], grid, layer=0)
    # ---- render
    def _shade(s, col, n, dist, unlit):
        if not unlit:
            k = s.amb + s.dif * max(0.0, -float(n @ s.L)) + 0.05 * n[1]
            col = (col[0] * k, col[1] * k, col[2] * k)
        if s.fog:
            fc, d0, d1, fm = s.fog; t = clamp((dist - d0) / (d1 - d0)) * fm
            col = mix(col, fc, t)
        return tuple(int(clamp(c, 0, 255)) for c in col[:3])
    def render_mask(s, cam):
        w, h = W * SS // 2, H * SS // 2; img = Image.new('L', (w, h), 0); dr = ImageDraw.Draw(img); k = 0.5
        for o in sorted(s.objs, key=lambda o: (o['layer'], -(np.linalg.norm(o['c'] - cam.pos) + o['bias']))):
            v = 255 if o.get('hero') else 0
            if o['k'] == 'mesh':
                if o['alpha'] < 255 and not v: continue
                for pts, col, _ in o['faces']:
                    n = np.cross(pts[1] - pts[0], pts[2] - pts[0])
                    if n @ (cam.pos - pts[0]) <= 0 and not o['two']: continue
                    c = cam.clip(list(cam.to_cam(pts)))
                    if len(c) < 3: continue
                    dr.polygon([(x * k, y * k) for x, y in cam.proj(c)], fill=v)
            elif o['k'] == 'sprite' and o['alpha'] == 255:
                c = cam.to_cam(o['c'])
                if c[2] < cam.near: continue
                (x, y), = cam.proj([c]); rx = cam.f * o['rx'] / c[2]; ry = cam.f * o['ry'] / c[2]
                dr.ellipse([(x - rx) * k, (y - ry) * k, (x + rx) * k, (y + ry) * k], fill=v)
        return img.resize((W, H), Image.BILINEAR)
    def render(s, cam):
        w, h = W * SS, H * SS
        if isinstance(s.sky, Image.Image): img = s.sky.copy()
        else:
            top, bot = s.sky or ((90, 160, 240), (190, 225, 250))
            g = np.linspace(0, 1, h)[:, None]; col = np.array(top)[None] * (1 - g) + np.array(bot)[None] * g
            img = Image.fromarray(np.repeat(col[:, None, :], 2, 1).astype(np.uint8)).resize((w, h))
        dr = ImageDraw.Draw(img, 'RGBA')
        def key(o):
            d = np.linalg.norm(o['c'] - cam.pos); return (o['layer'], -(d + o['bias']))
        objs = sorted(s.objs, key=key); shadows_done = False
        for o in objs:
            if o['layer'] > 0 and not shadows_done:
                shadows_done = True; s._shadows(img, cam); dr = ImageDraw.Draw(img, 'RGBA')
            dist = np.linalg.norm(o['c'] - cam.pos)
            if o['k'] == 'mesh':
                a = o['alpha']
                for pts, col, _ in o['faces']:
                    n = np.cross(pts[1] - pts[0], pts[2] - pts[0]); ln = np.linalg.norm(n)
                    if ln < 1e-9: continue
                    n /= ln; facing = n @ (cam.pos - pts[0])
                    if facing <= 0:
                        if not o['two']: continue
                        n = -n
                    c = cam.clip(list(cam.to_cam(pts)))
                    if len(c) < 3: continue
                    fd = np.linalg.norm(pts.mean(0) - cam.pos) if o['layer'] == 0 else dist
                    rgb = s._shade(col, n, fd, o['unlit'])
                    dr.polygon(cam.proj(c), fill=rgb + (a,) if a < 255 else rgb)
                for pts, col, nw in o.get('decals', ()):
                    if nw @ (cam.pos - pts[0]) <= 0.02: continue
                    c = cam.clip(list(cam.to_cam(pts)))
                    if len(c) < 3: continue
                    rgb = s._shade(col[:3], nw, dist, False)
                    dr.polygon(cam.proj(c), fill=rgb + ((col[3],) if len(col) > 3 else ()))
            elif o['k'] == 'sprite':
                c = cam.to_cam(o['c'])
                if c[2] < cam.near: continue
                (x, y), = cam.proj([c]); rx = cam.f * o['rx'] / c[2]; ry = cam.f * o['ry'] / c[2]
                rgb = s._shade(o['col'], V(0, 1, 0), dist, True) + (o['alpha'],)
                fn = dr.rectangle if o['rect'] else dr.ellipse
                fn([x - rx, y - ry, x + rx, y + ry], fill=rgb)
                if o['hi']:
                    dr.ellipse([x - rx * .55, y - ry * .65, x + rx * .1, y - ry * .05], fill=tuple(o['hi']) + (o['alpha'],))
            elif o['k'] == 'text':
                c = cam.to_cam(o['c'])
                if c[2] < cam.near: continue
                (x, y), = cam.proj([c]); px = cam.f * o['size'] / c[2]
                if px < 4: continue
                f = font(px, o['fp']); sw = int(px * o['sw']) if o['stroke'] else 0
                if o['bg']:
                    bb = dr.textbbox((x, y), o['txt'], font=f, anchor='mm'); p = cam.f * o['pad'] / c[2]
                    dr.rounded_rectangle([bb[0] - p, bb[1] - p, bb[2] + p, bb[3] + p], radius=p, fill=o['bg'])
                dr.text((x, y), o['txt'], font=f, fill=o['col'], anchor='mm', stroke_width=sw, stroke_fill=o['stroke'])
        if not shadows_done: s._shadows(img, cam)
        return img.reduce(SS)
    def _shadows(s, img, cam):
        if not s.shadows or s.shadow <= 0: return
        mask = Image.new('L', img.size, 0); md = ImageDraw.Draw(mask); L = s.L; gy = s.ground_y + 0.01; any_ = False
        for pts in s.shadows:
            pts = pts[pts[:, 1] >= gy - 0.05] if len(pts) else pts
            if len(pts) < 3: continue
            t = (pts[:, 1] - gy) / L[1]; g = pts - L[None] * t[:, None]
            hull = _hull(g[:, [0, 2]])
            if len(hull) < 3: continue
            P = np.array([(x, gy, z) for x, z in hull]); c = cam.clip(list(cam.to_cam(P)))
            if len(c) < 3: continue
            md.polygon(cam.proj(c), fill=int(255 * s.shadow)); any_ = True
        if any_: img.paste(s.shadow_col, mask=mask)

def _hull(p):
    p = sorted(set(map(tuple, np.round(p, 4))))
    if len(p) < 3: return p
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo = []
    for q in p:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], q) <= 0: lo.pop()
        lo.append(q)
    up = []
    for q in reversed(p):
        while len(up) >= 2 and cr(up[-2], up[-1], q) <= 0: up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]

# ---------- 2D shape helpers for decals
def ell(cx, cy, rx, ry, n=14, a0=0, a1=360):
    return [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n, endpoint=(a1 - a0) < 360)]
def arc(cx, cy, rx, ry, a0, a1, th, n=10):
    o = [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a))) for a in np.linspace(a0, a1, n)]
    i = [(cx + (rx - th) * math.cos(math.radians(a)), cy + (ry - th) * math.sin(math.radians(a))) for a in np.linspace(a1, a0, n)]
    return o + i
def rect(cx, cy, w, h, rot=0):
    c, s_ = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return [(cx + x * c - y * s_, cy + x * s_ + y * c) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
