"""Only One Country Is In All 4 Hemispheres - map animation (short 4)."""
import json, math, random, sys, os, pickle
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS, SS = 1080, 1920, 24, 2
TL = json.load(open("build/s4/timeline.json"))["lines"]
def ls(i): return TL[i]["t0"]
def le(i): return TL[i]["t1"]
def wt(i, word):
    for w in TL[i]["words"]:
        if w["w"].lower().strip('.,?') == word.lower().strip('.,?'): return w["t0"]
    raise KeyError(word)
END = le(14) + .55; DUR = END + .1
_F = {}
def font(size, p="fonts/LuckiestGuy-Regular.ttf"):
    k = (int(size), p)
    if k not in _F: _F[k] = ImageFont.truetype(p, int(size))
    return _F[k]
BANG = "fonts/Bangers-Regular.ttf"; FRE = "fonts/Fredoka.ttf"
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)
def eout(t): t = clamp(t); return 1 - (1 - t) ** 3
def lerp(a, b, t): return a + (b - a) * t
def pulse(t, t0, d=.25): return clamp(1 - (t - t0) / d) if t >= t0 else 0.0

# ---------------------------------------------------------------- data
def load(res):
    pk = f"build/s4/geo{res}.pkl"
    if os.path.exists(pk): return pickle.load(open(pk, "rb"))
    G = json.load(open(f"short4/data/ne_{res}m_admin_0_countries.geojson")); out = []
    for f in G["features"]:
        g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        rings = [np.radians(np.array(p[0], float)[:, :2]) for p in polys if len(p[0]) >= 4]
        out.append((f["properties"]["ADMIN"], rings))
    os.makedirs("build/s4", exist_ok=True); pickle.dump(out, open(pk, "wb")); return out
GEO = {110: load(110), 50: load(50)}
def ring_of(name, res=50): return max([r for n, rs in GEO[res] if n == name for r in rs], key=len)
G_ = [(3.38, 172.98), (3.17, 172.83), (2.0, 173.27), (1.85, 172.95), (1.42, 173.0), (.92, 173.0), (.4, 173.87), (.23, 173.4), (.17, 173.6), (-.67, 174.35), (-1.33, 174.83), (-1.33, 175.98), (-1.35, 176.45), (-1.87, 175.55), (-2.5, 175.98), (-2.63, 176.82), (-.86, 169.5)]
P_ = [(-2.8, -171.7), (-3.13, -171.08), (-3.58, -171.52), (-3.6, -174.12), (-3.72, -170.72), (-4.45, -171.25), (-4.5, -172.17), (-4.68, -174.52)]
L_ = [(4.7, -160.4), (3.9, -159.4), (1.9, -157.4), (-4.0, -154.9), (-5.6, -155.9), (-10.0, -150.2), (-10.1, -152.3), (-11.4, -151.8)]
ISL = G_ + P_ + L_          # 33 islands (lat, lon)
OLD = [(60, 180), (30, 180), (12, 180), (6, 180), (0, 180), (-6, 180), (-10, 180), (-15, -172.5), (-45, -172.5), (-52, 180), (-70, 180)]
NEW = [(60, 180), (30, 180), (12, 180), (8, -164), (6, -150), (0, -150), (-6, -150), (-12, -150), (-15, -172.5), (-45, -172.5), (-52, 180), (-70, 180)]
OLD = OLD[:3] + [(8, 180)] + OLD[3:]      # same point count as NEW for the morph

# ---------------------------------------------------------------- projection
class View:
    def __init__(s, lon, lat, R, cx=W / 2, cy=H * .40): s.l0 = math.radians(lon); s.p0 = math.radians(lat); s.R = R; s.cx = cx; s.cy = cy
    def proj(s, ll):           # ll: (n,2) radians lon,lat -> x,y px, cosc
        dl = ll[:, 0] - s.l0; cp = np.cos(ll[:, 1]); sp = np.sin(ll[:, 1])
        cc = math.sin(s.p0) * sp + math.cos(s.p0) * cp * np.cos(dl)
        x = cp * np.sin(dl); y = math.cos(s.p0) * sp - math.sin(s.p0) * cp * np.cos(dl)
        return x, y, cc
    def pt(s, lat, lon):
        x, y, c = s.proj(np.radians(np.array([[lon, lat]], float))); return s.cx + s.R * x[0], s.cy - s.R * y[0], c[0]
    def line(s, pts, n=24):    # densified polyline of (lat,lon) -> list of screen segments on the front side
        out = []; cur = []
        for (a, b), (c, d) in zip(pts[:-1], pts[1:]):
            dlon = ((d - b + 180) % 360) - 180
            for i in range(n + 1):
                u = i / n; x, y, cc = s.pt(a + (c - a) * u, b + dlon * u)
                if cc > .02: cur.append((x, y))
                elif cur: out.append(cur); cur = []
        if cur: out.append(cur)
        return out
_STARS = None
def stars():
    global _STARS
    if _STARS is None:
        im = Image.new('RGB', (W, H)); a = np.zeros((H, W, 3), np.float32); yy = np.linspace(0, 1, H)[:, None]
        a[:] = (6, 8, 26); a[..., 2] += 30 * (1 - yy); a[..., 0] += 14 * yy
        im = Image.fromarray(a.astype(np.uint8)); d = ImageDraw.Draw(im); r = random.Random(4)
        for i in range(260):
            x, y = r.uniform(0, W), r.uniform(0, H); s = r.choice((1, 1, 1, 2, 2, 3)); c = r.randint(120, 255); d.ellipse([x, y, x + s, y + s], fill=(c, c, min(255, c + 20)))
        _STARS = im
    return _STARS.copy()
OCEAN = (16, 74, 150); SHALLOW = (40, 122, 196); LAND = (88, 158, 84); LAND2 = (70, 132, 70); EDGE = (30, 70, 44)
def basemap(v, hi=None, res=110, dim=0.0, grat=True):
    hi = hi or {}; S = SS; big = Image.new('RGB', (W * S, H * S), OCEAN if v.R > 1400 else (0, 0, 0)); d = ImageDraw.Draw(big)
    R, cx, cy = v.R * S, v.cx * S, v.cy * S; globe = v.R <= 1400
    if globe: d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=OCEAN)
    if grat:
        for lat in range(-75, 90, 15):
            for seg in v.line([(lat, lo) for lo in range(-180, 181, 30)], 10): d.line([(x * S, y * S) for x, y in seg], fill=(30, 92, 168), width=S)
        for lon in range(-180, 180, 15):
            for seg in v.line([(la, lon) for la in range(-90, 91, 30)], 10): d.line([(x * S, y * S) for x, y in seg], fill=(30, 92, 168), width=S)
    polys = []
    for name, rings in GEO[res]:
        for r in rings:
            x, y, cc = v.proj(r)
            if cc.max() < 0: continue
            back = cc < 0
            if back.any():
                n = np.sqrt(x * x + y * y) + 1e-9; x = np.where(back, x / n, x); y = np.where(back, y / n, y)
            px = cx + R * x; py = cy - R * y
            if px.max() < 0 or px.min() > W * S or py.max() < 0 or py.min() > H * S: continue
            polys.append((name, list(zip(px.tolist(), py.tolist()))))
    for name, p in polys: d.line(p + [p[0]], fill=SHALLOW, width=int(S * (7 if globe else 12)), joint='curve')
    for name, p in polys:
        c = hi.get(name); base = LAND if (hash(name) % 3) else LAND2
        d.polygon(p, fill=c or base, outline=(255, 255, 255) if c else EDGE)
        if c: d.line(p + [p[0]], fill=(255, 255, 255), width=S * 3)
    im = big.resize((W, H), Image.LANCZOS)
    if globe:
        a = np.asarray(im, np.float32); yy, xx = np.mgrid[0:H:4, 0:W:4].astype(np.float32)
        rr = np.sqrt((xx - v.cx) ** 2 + (yy - v.cy) ** 2) / v.R
        lx = (xx - v.cx) / v.R * -.45 + (yy - v.cy) / v.R * -.5; z = np.sqrt(np.clip(1 - rr ** 2, 0, 1))
        sh = np.clip(.42 + .58 * (z * .75 + lx * .9 + .25), .25, 1.12); sh = np.where(rr <= 1, sh, 1)
        glow = np.clip(1 - np.abs(rr - 1.0) / .09, 0, 1) ** 2 * (rr > 1) + np.clip(1 - (1 - rr) / .06, 0, 1) ** 2 * (rr <= 1) * .6
        shI = np.asarray(Image.fromarray((sh * 200).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) / 200
        gI = np.asarray(Image.fromarray((np.clip(glow, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) / 255
        st = np.asarray(stars(), np.float32)
        mask = np.asarray(Image.fromarray(((rr <= 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32)[..., None] / 255
        a = (a * shI[..., None]) * mask + st * (1 - mask); a = a + (np.array((110, 190, 255), np.float32) - a) * gI[..., None] * .75
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if dim: im = Image.blend(im, Image.new('RGB', (W, H), (4, 8, 24)), dim)
    return im

# ---------------------------------------------------------------- drawing helpers
def text(d, xy, s, size, fill=(255, 255, 255), stroke=(10, 14, 30), fp=BANG, anchor='mm', sw=.09):
    if size < 3: return
    f = font(size, fp); d.text((xy[0] + size * .04, xy[1] + size * .06), s, font=f, fill=(0, 0, 0), anchor=anchor, stroke_width=int(size * sw), stroke_fill=(0, 0, 0))
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=int(size * sw), stroke_fill=stroke)
def pop(k, d=.18): return (.5 + .5 * eout(k / d)) * (1 + .08 * math.sin(clamp(k / d) * math.pi)) if k > 0 else 0
def glowline(im, segs, col, w=8, dash=None, t=0):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for seg in segs:
        if len(seg) < 2: continue
        if dash:
            acc = -((t * 60) % (dash * 2)); 
            for a, b in zip(seg[:-1], seg[1:]):
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                if int((acc // dash)) % 2 == 0: d.line([a, b], fill=col + (255,), width=w)
                acc += L
        else: d.line(seg, fill=col + (255,), width=w, joint='curve')
    g = lay.filter(ImageFilter.GaussianBlur(w * 1.6)); im.paste(g, (0, 0), g); im.paste(lay, (0, 0), lay); return im
def xmark(d, c, s, k):
    if k <= 0: return
    z = s * (1.6 - .6 * eout(k / .14)); 
    for a, b in (((-1, -1), (1, 1)), ((-1, 1), (1, -1))):
        d.line([c[0] + a[0] * z, c[1] + a[1] * z, c[0] + b[0] * z, c[1] + b[1] * z], fill=(0, 0, 0), width=int(s * .42))
        d.line([c[0] + a[0] * z, c[1] + a[1] * z, c[0] + b[0] * z, c[1] + b[1] * z], fill=(255, 40, 40), width=int(s * .28))
def island(d, x, y, r, col=(255, 226, 60)):
    d.ellipse([x - r - 4, y - r - 4, x + r + 4, y + r + 4], fill=(10, 20, 40)); d.ellipse([x - r, y - r, x + r, y + r], fill=col)
def tintpoly(im, pts, col, a):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(lay).polygon(pts, fill=col + (int(a),)); im.paste(lay, (0, 0), lay); return im
def flag(im, cx, cy, w, k):
    if k <= 0: return
    z = pop(k); w = int(w * z); h = int(w * .5); f = Image.new('RGB', (w, h), (206, 17, 38)); d = ImageDraw.Draw(f)
    sr = h * .2; d.ellipse([w / 2 - sr, h * .56 - sr, w / 2 + sr, h * .56 + sr], fill=(252, 209, 22))
    for i in range(13):
        a = math.pi + i * math.pi / 12; d.line([w / 2 + math.cos(a) * sr, h * .56 + math.sin(a) * sr, w / 2 + math.cos(a) * sr * 1.6, h * .56 + math.sin(a) * sr * 1.6], fill=(252, 209, 22), width=max(2, w // 90))
    d.polygon([(w * .40, h * .2), (w * .5, h * .12), (w * .62, h * .2), (w * .5, h * .17)], fill=(252, 209, 22))      # frigatebird
    d.rectangle([0, h * .56, w, h], fill=(0, 56, 147))
    for j in range(3):
        y0 = h * (.60 + j * .135); pts = [(x, y0 + math.sin(x / w * 6 * math.pi) * h * .025) for x in range(0, w + 1, 6)]
        d.line(pts, fill=(255, 255, 255), width=max(3, int(h * .06)))
    b = Image.new('RGB', (w + 12, h + 12), (255, 255, 255)); b.paste(f, (6, 6)); im.paste(b, (int(cx - w / 2) - 6, int(cy - h / 2) - 6))

# ---------------------------------------------------------------- camera
KZ = (-168.5, -2.5, 1500)
CAM = [(0, -60, 18, 470), (2.95, 40, 22, 470), (ls(1) + .35, 95, 58, 640), (le(1) + .2, 98, 58, 660), (ls(2) + .4, -100, 40, 720), (le(2) + .15, -98, 40, 740),
       (ls(3) + .9, -160, 4, 600), (le(3) + .2, -168.5, -2.5, 900), (ls(4) + .4,) + KZ, (le(11) + .2,) + KZ, (ls(12) + .5, -168.5, -1, 1150), (END + 1, -168.5, -1, 1250)]
def cam(t):
    for (t0, a0, b0, r0), (t1, a1, b1, r1) in zip(CAM[:-1], CAM[1:]):
        if t0 <= t <= t1:
            u = smooth((t - t0) / (t1 - t0)); da = ((a1 - a0 + 180) % 360) - 180
            if t0 == 0: da = a1 - a0; u = (t - t0) / (t1 - t0)
            return View(a0 + da * u, lerp(b0, b1, u), math.exp(lerp(math.log(r0), math.log(r1), u)))
    return View(*CAM[-1][1:])
def dots(d, v, n=33, r=9, col=(255, 226, 60), scale=None):
    for i, (la, lo) in enumerate(ISL[:n]):
        x, y, c = v.pt(la, lo)
        if c > 0: island(d, x, y, r if scale is None else r * scale(i), col)
def cross_lines(im, v, t, a=1.0):
    glowline(im, v.line([(0, lo) for lo in range(-180, 181, 20)], 8), (255, 226, 60), 7)
    glowline(im, v.line([(la, 180) for la in range(-90, 91, 20)], 8) + v.line([(la, 0) for la in range(-90, 91, 20)], 8), (80, 230, 255), 7)

# ---------------------------------------------------------------- scenes
def sc_hook(t):                    # 0: only one country ... all four hemispheres
    v = cam(t); im = basemap(v); cross_lines(im, v, t); d = ImageDraw.Draw(im)
    text(d, (W / 2, H * .085), "ONLY 1 COUNTRY", 150 * pop(t + .2), (255, 226, 60))
    k4 = t - wt(0, 'all')
    if k4 > 0:
        for i, (lab, col, dx, dy) in enumerate((("N", (255, 226, 60), -1, -1), ("E", (80, 230, 255), 1, -1), ("S", (255, 120, 60), -1, 1), ("W", (120, 255, 140), 1, 1))):
            kk = k4 - i * .14
            if kk > 0:
                z = pop(kk); x = W / 2 + dx * 330; y = v.cy + dy * 330; s = 78 * z
                d.rounded_rectangle([x - s, y - s, x + s, y + s], 24, fill=col, outline=(10, 14, 30), width=8); text(d, (x, y + 6), lab, 120 * z, (10, 14, 30), (255, 255, 255), sw=.04)
    text(d, (W / 2, v.cy), "?", 330 * pop(t - .9), (255, 255, 255), (220, 30, 40))
    return im
def sc_not(t, i):                  # 1, 2: it's not Russia / the United States
    name = ("Russia", "United States of America")[i - 1]; lab = ("RUSSIA", "USA")[i - 1]; v = cam(t)
    k = t - ls(i) - .12; im = basemap(v, {name: (235, 50, 50)} if k > 0 else {}); d = ImageDraw.Draw(im)
    kx = t - (wt(1, 'Russia') if i == 1 else wt(2, 'United')) - .12
    text(d, (W / 2, H * .085), "NOT " + lab, 150 * pop(k), (255, 90, 80))
    xmark(d, (W / 2, v.cy), 190, kx)
    return im
def sc_search(t):                  # 3: most people can't even find it on a map
    v = cam(t); im = basemap(v); d = ImageDraw.Draw(im); k = t - ls(3)
    a = k * 3.2; x = W / 2 + math.cos(a) * 230 * (1 - .5 * clamp(k / 2)); y = v.cy + math.sin(a * 1.3) * 200 * (1 - .5 * clamp(k / 2)); r = 120
    d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 255, 255), width=14); d.line([x + r * .7, y + r * .7, x + r * 1.5, y + r * 1.5], fill=(255, 255, 255), width=22)
    text(d, (x, y + 8), "?", 130, (255, 226, 60))
    text(d, (W / 2, H * .085), "WHERE IS IT?", 140 * pop(k), (255, 255, 255))
    return im
def india(v, k):
    r = np.degrees(ring_of("India")); lon = r[:, 0] - 79 + KZ[0]; lat = r[:, 1] - 22 + KZ[1] + 1.5
    pts = [v.pt(a, b)[:2] for a, b in zip(lat, lon)]; c = (W / 2, v.cy + 40); z = .3 + .7 * eout(k / .35)
    return [(c[0] + (x - c[0]) * z, c[1] + (y - c[1]) * z - (1 - eout(k / .35)) * 500) for x, y in pts]
def sc_islands(t):                 # 4: thirty-three tiny islands ... bigger than India
    v = cam(t); im = basemap(v, res=50); k = t - ls(4); ki = t - wt(4, 'bigger') + .1
    n = int(clamp((t - wt(4, '33')) / (wt(4, 'scattered') - wt(4, '33') + .5)) * 33)
    if ki > 0:
        p = india(v, ki); im = tintpoly(im, p, (255, 140, 40), 150 * clamp(ki / .2)); ImageDraw.Draw(im).line(p + [p[0]], fill=(255, 255, 255), width=6)
    d = ImageDraw.Draw(im)
    dots(d, v, n, 10, scale=lambda i: 1 + 1.5 * pulse(t, wt(4, '33') + i * (wt(4, 'scattered') - wt(4, '33') + .5) / 33, .2))
    text(d, (W / 2, H * .085), f"{max(n, 0)} ISLANDS", 160 * pop(k), (255, 226, 60))
    if ki > 0: text(d, (W / 2, v.cy + 60), "INDIA", 150 * pop(ki - .25), (255, 255, 255), (150, 60, 0)); text(d, (W / 2, H * .16), "OCEAN BIGGER THAN INDIA", 78 * pop(ki - .1), (255, 255, 255))
    return im
def skyline(d, cx, by, s):
    r = random.Random(3); x = cx - 170 * s
    for i in range(11):
        w = r.uniform(22, 38) * s; h = r.uniform(70, 230) * s * (1.5 if i == 5 else 1)
        d.rectangle([x, by - h, x + w, by], fill=(60, 70, 110), outline=(10, 14, 30), width=3)
        for j in range(int(h // (22 * s))):
            d.rectangle([x + w * .25, by - h + 10 * s + j * 22 * s, x + w * .75, by - h + 20 * s + j * 22 * s], fill=(255, 226, 120))
        if i == 5: d.line([x + w / 2, by - h, x + w / 2, by - h - 60 * s], fill=(60, 70, 110), width=5)
        x += w + 3 * s
def sc_merge(t):                   # 5: put all its land together ... New York City
    v = cam(t); im = basemap(v, res=50); d = ImageDraw.Draw(im); k = t - ls(5); m = smooth((k - .15) / 1.1); kn = t - wt(5, 'about')
    c = (W * (.5 - .2 * smooth(kn / .4)), v.cy); r = random.Random(8)
    for i, (la, lo) in enumerate(ISL):
        x, y, _ = v.pt(la, lo); an = r.uniform(0, 6.28); rr = math.sqrt(r.uniform(0, 1)) * 62
        island(d, lerp(x, c[0] + math.cos(an) * rr, m), lerp(y, c[1] + math.sin(an) * rr, m), lerp(10, 17, m))
    if m >= 1: d.ellipse([c[0] - 84, c[1] - 84, c[0] + 84, c[1] + 84], fill=(255, 226, 60), outline=(10, 20, 40), width=6)
    text(d, (W / 2, H * .085), "ALL ITS LAND", 150 * pop(k), (255, 226, 60))
    if kn > 0:
        z = pop(kn - .1); text(d, (W / 2, v.cy), "=", 170 * z, (255, 255, 255)); nx = W * .73
        if z > 0: d.ellipse([nx - 92 * z, v.cy - 92 * z, nx + 92 * z, v.cy + 92 * z], fill=(170, 190, 230), outline=(10, 20, 40), width=6); skyline(d, nx, v.cy + 50 * z, .45 * z)
        text(d, (c[0], v.cy + 150), "811 KM²", 66 * z, (255, 226, 60)); text(d, (nx, v.cy + 150), "NEW YORK CITY", 62 * z, (255, 255, 255)); text(d, (nx, v.cy + 215), "784 KM²", 62 * z, (200, 215, 255))
    return im
def dl_pts(m): return [(lerp(a[0], b[0], m), a[1] + (((b[1] - a[1] + 180) % 360) - 180) * m) for a, b in zip(OLD, NEW)]
def side_poly(v, pts, east):
    ln = [p for seg in v.line(pts, 12) for p in seg]
    if len(ln) < 2: return None
    return ln + ([(W + 50, ln[-1][1]), (W + 50, ln[0][1])] if east else [(-50, ln[-1][1]), (-50, ln[0][1])])
def sc_dateline(t):                # 6-9
    v = cam(t); im = basemap(v, res=50); m = smooth((t - wt(8, 'moved') + .1) / .9) if t >= ls(8) else 0.0
    pts = dl_pts(m); split = t >= wt(7, 'half') - .05; after = t >= ls(9)
    if split and not after:
        a = 95 * clamp((t - wt(7, 'half')) / .25)
        pw = side_poly(v, pts, False); pe = side_poly(v, pts, True)
        if pw: im = tintpoly(im, pw, (255, 200, 40), a)
        if pe: im = tintpoly(im, pe, (90, 60, 200), a)
    if after:
        s = smooth((t - ls(9)) / 1.6); x = lerp(W + 300, -300, s); lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
        dd.rectangle([min(x, W), 0, max(x, W) + 1, H], fill=(255, 200, 60, 70)); dd.rectangle([min(0, x) - 1, 0, max(0, x), H], fill=(10, 10, 60, 120 if s < 1 else 0)); lay = lay.filter(ImageFilter.GaussianBlur(60)); im.paste(lay, (0, 0), lay)
    glowline(im, v.line(pts, 12), (255, 255, 255), 9, dash=26, t=t); d = ImageDraw.Draw(im)
    dots(d, v, 33, 10)
    k6 = t - ls(6)
    if not split: text(d, (W / 2, H * .085), "THE DATE LINE", 150 * pop(k6), (255, 255, 255))
    elif t < ls(8):
        kk = t - wt(7, 'half'); xw, yw, _ = v.pt(-2, 171); xe, ye, _ = v.pt(-2, -161)
        text(d, (W / 2, H * .085), "2 DAYS AT ONCE", 150 * pop(kk), (255, 226, 60))
        text(d, (max(170, xw), v.cy - 330), "MONDAY", 96 * pop(kk), (255, 226, 60)); text(d, (min(W - 190, xe), v.cy - 330), "SUNDAY", 96 * pop(t - wt(7, 'yesterday') + .15), (190, 170, 255))
    elif not after:
        kk = t - wt(8, '1995,') + .05; text(d, (W / 2, H * .085), "1995", 230 * pop(kk), (255, 90, 80), (255, 255, 255))
        if m > 0:
            x, y, _ = v.pt(0, lerp(180, -150, m)); x = min(x, W - 80); d.polygon([(x + 70, y), (x + 10, y - 44), (x + 10, y + 44)], fill=(255, 255, 255), outline=(10, 14, 30))
        if m > .9: text(d, (W / 2, v.cy - 330), "ALL MONDAY", 100 * pop(t - wt(8, 'moved') - .8), (255, 226, 60))
    else:
        kk = t - wt(9, 'first') + .05; text(d, (W / 2, H * .085), "#1 TO SEE THE DAY", 128 * pop(kk), (255, 226, 60))
        x, y, _ = v.pt(1.9, -157.4); kz = t - wt(9, 'every')
        if kz > 0:
            r = 40 + 30 * ((t * 1.5) % 1); d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 255, 255), width=6); text(d, (min(x, W - 200), y - 110), "UTC+14", 96 * pop(kz), (255, 255, 255), (200, 90, 0))
    return im
def sc_sea(t):                     # 10, 11: less than two metres above the sea / first to disappear
    k = t - ls(10); rise = smooth((t - ls(11) - .1) / 2.0) if t >= ls(11) else 0; a = np.zeros((H, W, 3), np.float32); yy = np.linspace(0, 1, H)[:, None]
    a[:] = lerp(np.array((70, 170, 255.)), np.array((190, 235, 255.)), yy * 1.4).clip(0, 255)[:, None, :] if False else 0
    top = np.array((60, 160, 250.)); bot = np.array((200, 238, 255.)); a[:] = top + (bot - top) * np.clip(yy * 1.5, 0, 1)[..., None]
    im = Image.fromarray(a.astype(np.uint8)); d = ImageDraw.Draw(im)
    sea0 = H * .50; land_top = sea0 - 62; sea = sea0 - rise * 150
    d.ellipse([W * .68, H * .1, W * .68 + 190, H * .1 + 190], fill=(255, 240, 150))
    for i, (cx_, cy_) in enumerate(((.2, .16), (.55, .24))):
        x = (cx_ * W + t * 14 * (i + 1)) % (W + 300) - 150; d.ellipse([x - 120, cy_ * H - 36, x + 120, cy_ * H + 36], fill=(255, 255, 255)); d.ellipse([x - 50, cy_ * H - 66, x + 70, cy_ * H + 20], fill=(255, 255, 255))
    d.polygon([(W * .08, sea0 + 500), (W * .16, sea0 + 20), (W * .24, land_top), (W * .78, land_top), (W * .86, sea0 + 20), (W * .94, sea0 + 500)], fill=(240, 214, 150), outline=(150, 120, 70))
    for px_, hh, ph in ((.34, 300, 0), (.62, 240, 1.3)):
        x = W * px_; sway = math.sin(t * 1.6 + ph) * 14; d.line([x, land_top, x + sway, land_top - hh], fill=(130, 90, 50), width=22)
        for an in (-150, -110, -70, -30, 200, 250):
            r_ = math.radians(an); d.line([x + sway, land_top - hh, x + sway + math.cos(r_) * 130, land_top - hh + math.sin(r_) * 70 + 26], fill=(50, 160, 70), width=26)
    hx = W * .47; d.rectangle([hx, land_top - 100, hx + 130, land_top], fill=(190, 120, 70), outline=(90, 50, 30), width=4); d.polygon([(hx - 22, land_top - 100), (hx + 65, land_top - 178), (hx + 152, land_top - 100)], fill=(214, 60, 50), outline=(90, 30, 30)); d.rectangle([hx + 48, land_top - 56, hx + 82, land_top], fill=(90, 50, 30))
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    wave = [(x, sea + math.sin(x / 70 + t * 3) * 9 + math.sin(x / 31 - t * 2) * 4) for x in range(-10, W + 20, 10)]
    dd.polygon(wave + [(W + 10, H), (-10, H)], fill=(20, 110, 210, 176)); dd.line(wave, fill=(255, 255, 255, 230), width=7); im.paste(lay, (0, 0), lay); d = ImageDraw.Draw(im)
    if t < ls(11) + .3:
        kr = t - wt(10, 'less'); rx = W * .80
        if kr > 0:
            z = eout(kr / .3); d.line([rx, sea0, rx, sea0 - 62 * z], fill=(255, 255, 255), width=10)
            for yq in (sea0, sea0 - 62 * z): d.line([rx - 30, yq, rx + 30, yq], fill=(255, 255, 255), width=10)
            text(d, (rx + 20, sea0 - 150), "2 M", 130 * pop(t - wt(10, '2') + .05), (255, 226, 60))
        text(d, (W / 2, H * .085), "BARELY ABOVE WATER", 118 * pop(k), (255, 255, 255))
    else:
        text(d, (W / 2, H * .085), "SINKING", 190 * pop(t - ls(11) - .3), (255, 90, 80), (255, 255, 255))
        for i in range(5):
            u = ((t * .9 + i * .21) % 1); x = W * (.2 + .15 * i); y = sea + 150 - u * 90; d.polygon([(x, y - 34), (x - 30, y + 14), (x + 30, y + 14)], fill=(255, 255, 255), outline=(10, 40, 90))
    return im
def sc_reveal(t):                  # 12-14
    v = cam(t); wrong = t >= ls(13); right = t >= wt(14, 'Kiribas.') - .08
    im = basemap(v, res=50, dim=.25 if wrong else 0); k = t - wt(12, 'Kiribati.') + .12
    for (la0, la1, lo0, lo1, col) in ((0, 25, 150, 180, (255, 226, 60)), (0, 25, -180, -130, (80, 230, 255)), (-25, 0, 150, 180, (255, 120, 60)), (-25, 0, -180, -130, (120, 255, 140))):
        p = [v.pt(a, b)[:2] for a, b in ((la0, lo0), (la0, lo1), (la1, lo1), (la1, lo0))]; im = tintpoly(im, p, col, 60 * clamp((t - ls(12)) / .4))
    cross_lines(im, v, t); d = ImageDraw.Draw(im); dots(d, v, 33, 9)
    for lab, la, lo in (("N+E", 14, 163), ("N+W", 14, -147), ("S+E", -15, 163), ("S+W", -15, -147)):
        x, y, _ = v.pt(la, lo); text(d, (clamp(x, 120, W - 120), y), lab, 80 * pop(t - ls(12) - .2), (255, 255, 255))
    if k > 0 and not right:
        text(d, (W / 2, H * .095), "KIRIBATI", 250 * pop(k), (255, 226, 60), (200, 30, 40))
        if wrong:
            kk = t - wt(13, "don't") + .05
            if kk > 0: z = eout(kk / .18); d.line([W * .08, H * .095 + 6, W * .08 + W * .84 * z, H * .095 + 6], fill=(0, 0, 0), width=40); d.line([W * .08, H * .095, W * .08 + W * .84 * z, H * .095], fill=(255, 40, 40), width=24)
    if right:
        kr = t - wt(14, 'Kiribas.') + .08; text(d, (W / 2, H * .095), "KI-RI-BAS", 250 * pop(kr), (120, 255, 140), (10, 80, 30)); text(d, (W / 2, H * .185), '"TI" SOUNDS LIKE "S"', 78 * pop(kr - .2), (255, 255, 255))
    if k > 0: flag(im, W / 2, v.cy + 430, 430, k - .15)
    return im

def base_frame(t):
    if t < ls(1) - .02: return sc_hook(t)
    if t < ls(2) - .1: return sc_not(t, 1)
    if t < ls(3) - .1: return sc_not(t, 2)
    if t < ls(4) - .05: return sc_search(t)
    if t < ls(5) - .05: return sc_islands(t)
    if t < ls(6) - .08: return sc_merge(t)
    if t < ls(10) - .08: return sc_dateline(t)
    if t < ls(12) - .1: return sc_sea(t)
    return sc_reveal(t)
CUTS = [ls(1) - .02, ls(2) - .1, ls(3) - .1, ls(4) - .05, ls(5) - .05, ls(6) - .08, ls(10) - .08, ls(12) - .1]
def events():
    return dict(end=END, dur=DUR, cuts=CUTS, n=wt(0, 'all'), x1=wt(1, 'Russia') - .12 + .0, x2=wt(2, 'United') - .12, isl0=wt(4, '33'), isl1=wt(4, 'scattered') + .5, india=wt(4, 'bigger') - .1,
                merge=ls(5) + .15, nyc=wt(5, 'about'), split=wt(7, 'half'), y1995=wt(8, '1995,'), move=wt(8, 'moved') - .1, sun=ls(9), utc=wt(9, 'every'), sea=ls(10), rise=ls(11),
                reveal=wt(12, 'Kiribati.') - .12, strike=wt(13, "don't"), right=wt(14, 'Kiribas.') - .08)

# ---------------------------------------------------------------- captions
def _groups():
    G = []
    for l in TL:
        cur = []
        for w in l['words']:
            if cur and (len(cur) >= 3 or sum(len(x['w']) for x in cur) + len(w['w']) > 13): G.append(cur); cur = []
            cur.append(w)
        if cur: G.append(cur)
    return G
GROUPS = _groups()
def captions(img, t):
    for gi, g in enumerate(GROUPS):
        t0 = g[0]['t0'] - .04; t1 = g[-1]['t1'] + .14
        if gi + 1 < len(GROUPS): t1 = min(t1, GROUPS[gi + 1][0]['t0'] - .04)
        if t0 <= t < t1 and t < END: break
    else: return img
    k = clamp((t - t0) / .09); sc_ = .78 + .22 * eout(k) + .06 * math.sin(k * math.pi); size = int(108 * sc_); f = font(size); dr = ImageDraw.Draw(img)
    words = [w['w'].upper() for w in g]; widths = [dr.textlength(w, font=f) for w in words]; sp = size * .26; lines = [[]]; lw = 0
    for i, wd in enumerate(widths):
        if lines[-1] and lw + wd > W * .86: lines.append([]); lw = 0
        lines[-1].append(i); lw += wd + sp
    y = int(H * .735) - (len(lines) - 1) * size * .55
    for ln in lines:
        tw_ = sum(widths[i] for i in ln) + sp * (len(ln) - 1); x = (W - tw_) / 2
        for i in ln:
            act = g[i]['t0'] - .03 <= t < g[i]['t1'] + .03 or (i == len(g) - 1 and t >= g[i]['t0'])
            dr.text((x + 5, y + 7), words[i], font=f, fill=(0, 0, 0), anchor='ls', stroke_width=int(size * .1), stroke_fill=(0, 0, 0))
            dr.text((x, y), words[i], font=f, fill=(255, 226, 50) if act else (255, 255, 255), anchor='ls', stroke_width=int(size * .1), stroke_fill=(12, 12, 16))
            x += widths[i] + sp
        y += size * 1.1
    return img
def frame(t):
    if t >= END: return Image.new('RGB', (W, H), (0, 0, 0))
    im = base_frame(t).convert('RGB')
    fl = max([pulse(t, c, .1) for c in CUTS] + [0]) * .25
    if fl > 0: im = Image.blend(im, Image.new('RGB', (W, H), (255, 255, 255)), fl)
    return captions(im, t)
def sheet(ims, out, cols=8):
    n = len(ims); cols = min(n, cols); rows = (n + cols - 1) // cols; sh = Image.new('RGB', (cols * 216, rows * 384))
    for k, im in enumerate(ims): sh.paste(im.resize((216, 384)), ((k % cols) * 216, (k // cols) * 384))
    sh.save(out, quality=85)
if __name__ == "__main__":
    if sys.argv[1] == "strip": sheet([frame(float(x)) for x in sys.argv[3:]], sys.argv[2])
    else:
        part, nparts, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]; os.makedirs(out, exist_ok=True)
        for n in range(int(math.ceil(DUR * FPS))):
            if n % nparts == part: frame(n / FPS).save(f"{out}/{n:05d}.jpg", quality=92)
        print("done", part)
