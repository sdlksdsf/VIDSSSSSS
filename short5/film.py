"""How A Bruise Changes Colour - realistic-still explainer (short 5)."""
import json, math, random, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 24
TL = json.load(open("build/s5/timeline.json"))["lines"]
def ls(i): return TL[i]["t0"]
def le(i): return TL[i]["t1"]
def wt(i, word):
    for w in TL[i]["words"]:
        if w["w"].lower().strip('.,?') == word.lower().strip('.,?'): return w["t0"]
    raise KeyError(word)
END = le(9) + .7; DUR = END + .1
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)
def eout(t): t = clamp(t); return 1 - (1 - t) ** 3
def lerp(a, b, t): return a + (b - a) * t
_F = {}
def font(size, p="fonts/Fredoka.ttf"):
    k = (int(size), p)
    if k not in _F: _F[k] = ImageFont.truetype(p, int(size))
    return _F[k]
# ------------------------------------------------------------ images (work at 1.25x for zoom room)
BW, BH = 1350, 2400
def L(n): return Image.open(f"short5/img/{n}.png").convert("RGB").resize((BW, BH), Image.LANCZOS)
def stages(b, e, alphas=(.95, .8, .6)):
    """base + red bruise image -> [base, red, purple, green, yellow]; mask from the difference of the two renders."""
    B = np.asarray(L(b), np.float32); E = np.asarray(L(e), np.float32)
    d = np.abs(E - B).sum(2); m = np.clip((d - 30) / 90, 0, 1)
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(12)), np.float32) / 255
    lumE = E.mean(2, keepdims=True); lumB = B.mean(2, keepdims=True); tex = np.clip(lumE / (lumB + 1), .35, 1.2)
    out = [B, E]
    rs = np.random.default_rng(2); nz = np.asarray(Image.fromarray((rs.random((BH // 40, BW // 40)) * 255).astype(np.uint8)).resize((BW, BH), Image.BICUBIC), np.float32) / 255
    mot = (.55 + .9 * nz)[..., None]; dark = np.clip((lumB - lumE) / 70, 0, 1)        # keep the blotchy pattern of the rendered bruise
    for col, a in (((92, 62, 128), alphas[0]), ((112, 132, 72), alphas[1]), ((214, 180, 92), alphas[2])):
        tint = np.array(col, np.float32) * (.5 + lumB / 255 * .8) * (1 - .3 * dark)
        mm = np.clip((m ** 1.6)[..., None] * a * mot * (.55 + .6 * dark), 0, .92); out.append(np.clip(B * (1 - mm) + tint * mm, 0, 255))
    return out, m
SK, SKM = stages("c0_skin", "c1_red", (1.0, .95, .8)); SH, SHM = stages("b_shin", "d1_red")
A_HIT = np.asarray(L("a_hit"), np.float32); CELLS = np.asarray(L("w_cells"), np.float32); E_END = np.asarray(L("e_end"), np.float32)
def centroid(m): ys, xs = np.nonzero(m > .5); return xs.mean() / BW, ys.mean() / BH
SKC = centroid(SKM); SHC = centroid(SHM)
def mix(seq, u):          # blend along a list of images, u in [0, len-1]
    i = int(clamp(u, 0, len(seq) - 1.0001)); f = u - i; return seq[i] * (1 - f) + seq[i + 1] * f if f > 1e-3 else seq[i]
def view(arr, z, cx=.5, cy=.5, dx=0, dy=0):
    """crop the 9:16 window of zoom z centred at (cx,cy) fractions; returns PIL 1080x1920"""
    w = BW / z; h = BH / z; x0 = clamp(cx * BW - w / 2, 0, BW - w) + dx; y0 = clamp(cy * BH - h / 2, 0, BH - h) + dy
    x0 = clamp(x0, 0, BW - w); y0 = clamp(y0, 0, BH - h)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return im.transform((W, H), Image.AFFINE, (w / W, 0, x0, 0, h / H, y0), Image.BICUBIC)
def toscreen(fx, fy, z, cx, cy):
    w = BW / z; h = BH / z; x0 = clamp(cx * BW - w / 2, 0, BW - w); y0 = clamp(cy * BH - h / 2, 0, BH - h)
    return (fx * BW - x0) / w * W, (fy * BH - y0) / h * H
# ------------------------------------------------------------ overlays
def rbc(d, x, y, r, col, a=255):
    d.ellipse([x - r, y - r * .8, x + r, y + r * .8], fill=col + (a,)); d.ellipse([x - r * .45, y - r * .36, x + r * .45, y + r * .36], fill=tuple(int(c * .72) for c in col) + (a,))
    d.arc([x - r, y - r * .8, x + r, y + r * .8], 200, 320, fill=(255, 255, 255, int(a * .5)), width=max(2, int(r * .12)))
def blood_cells(im, t, t0, c, col, n=46, spread=250, seed=1, fade=1.0):
    r = random.Random(seed); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(n):
        an = r.uniform(0, 6.28); dist = math.sqrt(r.uniform(0, 1)) * spread; born = t0 + r.uniform(0, 1.2); k = t - born; sz = r.uniform(13, 24)
        if k <= 0: continue
        g = eout(k / .7); wob = math.sin(t * 1.3 + i) * 8
        rbc(d, c[0] + math.cos(an) * dist * g + wob, c[1] + math.sin(an) * dist * g * 1.1 + math.cos(t * 1.1 + i * 2) * 8, sz, col, int(235 * clamp(k / .15) * fade))
    lay = lay.filter(ImageFilter.GaussianBlur(.8)); im.paste(lay, (0, 0), lay)
def white_cells(im, t, t0, c, n=6, eat=0.0):
    r = random.Random(5); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(n):
        an = i / n * 6.28 + .4; start = (c[0] + math.cos(an) * 900, c[1] + math.sin(an) * 1100); tgt = (c[0] + math.cos(an) * r.uniform(90, 230), c[1] + math.sin(an) * r.uniform(110, 260))
        k = smooth((t - t0 - i * .13) / 1.3); x = lerp(start[0], tgt[0], k); y = lerp(start[1], tgt[1], k); R = 78 + 10 * math.sin(t * 3 + i)
        pts = [(x + math.cos(a) * R * (1 + .14 * math.sin(a * 5 + t * 4 + i)), y + math.sin(a) * R * (1 + .14 * math.cos(a * 4 - t * 3 + i))) for a in np.linspace(0, 6.28, 40)]
        d.polygon(pts, fill=(245, 245, 255, 150), outline=(255, 255, 255, 230)); d.ellipse([x - R * .45, y - R * .4, x + R * .35, y + R * .4], fill=(170, 150, 215, 190))
        d.ellipse([x - R * .6, y - R * .7, x - R * .2, y - R * .4], fill=(255, 255, 255, 150))
    lay = lay.filter(ImageFilter.GaussianBlur(1.2)); im.paste(lay, (0, 0), lay)
def pill(im, s, k):
    if k <= 0: return
    d = ImageDraw.Draw(im, "RGBA"); z = .6 + .4 * eout(k / .18); f = font(84 * z); w = d.textlength(s, font=f) + 90 * z; h = 130 * z; x = W / 2; y = H * .115
    d.rounded_rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], h / 2, fill=(255, 255, 255, 240)); d.text((x, y - 4), s, font=f, fill=(20, 24, 40), anchor="mm")
def vignette(im):
    global _V
    try: _V
    except NameError:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); r = np.sqrt(((xx - W / 2) / (W * .75)) ** 2 + ((yy - H / 2) / (H * .75)) ** 2); _V = np.clip(1.06 - .5 * r ** 2.2, .5, 1.06)[..., None]
    return Image.fromarray(np.clip(np.asarray(im, np.float32) * _V, 0, 255).astype(np.uint8))
# ------------------------------------------------------------ shots
T_SMACK = wt(0, 'smack'); T_POP = wt(2, 'pop.') - .05; T_BLUE = wt(5, 'turns'); T_GREEN = wt(7, 'green,') - .1; T_YEL = wt(7, 'yellow.') - .1; T_GONE = wt(8, 'gone.') - .15
CUTS = [ls(1) - .1, ls(2) - .1, ls(4) - .1, ls(6) - .12, wt(7, 'They') - .08, wt(7, 'and') - .05, ls(9) - .1]
def base_frame(t):
    if t < CUTS[0]:                                   # 0 walk into the table - smack
        k = t - T_SMACK; pre = clamp(t / max(T_SMACK, .1)); z = lerp(1.0, 1.12, pre) if k < 0 else 1.12 + .22 * eout(k / .12) - .08 * smooth((k - .12) / .8)
        sh = math.exp(-max(k, 0) * 7) * 34 if k >= 0 else 0; dx = -90 * (1 - pre) ** 2
        im = view(A_HIT, z, .52, .56, dx + math.sin(t * 70) * sh, math.cos(t * 83) * sh)
        if 0 <= k < .5:
            d = ImageDraw.Draw(im, "RGBA"); c = (W * .50, H * .52); g = eout(k / .25); a = int(255 * (1 - k / .5))
            for i in range(12):
                an = i / 12 * 6.28 + .2; r0 = 90 + 120 * g; r1 = r0 + (90 if i % 2 else 160) * g
                d.line([c[0] + math.cos(an) * r0, c[1] + math.sin(an) * r0, c[0] + math.cos(an) * r1, c[1] + math.sin(an) * r1], fill=(255, 255, 255, a), width=16)
            if k < .07: im = Image.blend(im, Image.new("RGB", (W, H), (255, 255, 255)), .55 * (1 - k / .07))
        return im
    if t < CUTS[1]:                                   # 1 the skin doesn't break
        u = (t - CUTS[0]) / (CUTS[1] - CUTS[0]); return view(SH[0], lerp(1.05, 1.5, smooth(u)), SHC[0], lerp(.45, SHC[1], smooth(u)))
    if t < CUTS[2]:                                   # 2-3 under it: vessels pop, blood sits there
        u = (t - CUTS[1]) / (CUTS[2] - CUTS[1]); k = t - T_POP; g = smooth(k / 1.5) if k > 0 else 0
        z = lerp(2.6, 1.0, eout((t - CUTS[1]) / .5)) if t < CUTS[1] + .5 else lerp(1.0, 1.75, smooth((t - CUTS[1] - .5) / (CUTS[2] - CUTS[1] - .5)))
        cy = lerp(.30, SKC[1], smooth(u)); sh = math.exp(-max(k, 0) * 6) * 16 if k >= 0 else 0
        im = view(mix(SK[:2], g), z, SKC[0], cy, math.sin(t * 60) * sh, math.cos(t * 71) * sh)
        if k > 0:
            c = toscreen(SKC[0], SKC[1], z, SKC[0], cy); blood_cells(im, t, T_POP, c, (150, 16, 24), spread=150 * z)
            if k < .3:
                d = ImageDraw.Draw(im, "RGBA")
                for i in range(3):
                    r = (60 + i * 70) * eout(k / .3) * z; d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=(255, 255, 255, int(220 * (1 - k / .3))), width=10)
        return im
    if t < CUTS[3]:                                   # 4-5 dark mark -> blue and purple
        u = (t - CUTS[2]) / (CUTS[3] - CUTS[2]); g = smooth((t - T_BLUE) / 1.4) if t > T_BLUE else 0
        im = view(mix(SH[1:3], g), lerp(1.6, 1.3, smooth(u * 1.4)), SHC[0], SHC[1])
        if t >= ls(5): pill(im, "DAY 2", t - ls(5) - .15)
        return im
    if t < CUTS[4]:                                   # 6 body sends in cells
        u = (t - CUTS[3]) / (CUTS[4] - CUTS[3]); z = lerp(1.45, 1.8, smooth(u)); im = view(SK[2], z, SKC[0], SKC[1]); c = toscreen(SKC[0], SKC[1], z, SKC[0], SKC[1])
        blood_cells(im, t, CUTS[3] - 3, c, (78, 40, 120), n=36, spread=140 * z, seed=3); white_cells(im, t, CUTS[3] + .1, c); return im
    if t < CUTS[5]:                                   # 7a they eat the old blood
        u = (t - CUTS[4]) / (CUTS[5] - CUTS[4]); return view(CELLS, lerp(1.25, 1.6, u), lerp(.5, .42, u), lerp(.42, .46, u), math.sin(t * 2) * 6, math.cos(t * 1.7) * 6)
    if t < CUTS[6]:                                   # 7b-8 green, then yellow, then gone
        if t < T_GREEN: u = 2.0
        elif t < T_YEL: u = 2 + smooth((t - T_GREEN) / .5)
        elif t < T_GONE: u = 3 + smooth((t - T_YEL) / .5)
        else: u = 4.0
        seq = [SH[1], SH[1], SH[2], SH[3], SH[4]]; arr = mix(seq, u)
        if t >= T_GONE: g = smooth((t - T_GONE) / .7); arr = SH[4] * (1 - g) + SH[0] * g
        uu = (t - CUTS[5]) / (CUTS[6] - CUTS[5]); im = view(arr, lerp(1.55, 1.25, smooth(uu)), SHC[0], SHC[1])
        if t >= T_GONE: pill(im, "DAY 14", t - T_GONE)
        elif t >= T_YEL: pill(im, "DAY 10", t - T_YEL)
        elif t >= T_GREEN: pill(im, "DAY 6", t - T_GREEN)
        return im
    u = (t - CUTS[6]) / (END - CUTS[6]); return view(E_END, lerp(1.0, 1.14, eout(u)), .5, .6)   # 9 like it never happened
def events(): return dict(end=END, dur=DUR, cuts=CUTS, smack=T_SMACK, pop=T_POP, blue=T_BLUE, cells=CUTS[3] + .1, eat=CUTS[4], green=T_GREEN, yellow=T_YEL, gone=T_GONE, last=CUTS[6])
# ------------------------------------------------------------ captions
def _groups():
    G = []
    for l in TL:
        cur = []
        for w in l['words']:
            if cur and (len(cur) >= 3 or sum(len(x['w']) for x in cur) + len(w['w']) > 14): G.append(cur); cur = []
            cur.append(w)
        if cur: G.append(cur)
    return G
GROUPS = _groups(); CF = "fonts/LuckiestGuy-Regular.ttf"
def captions(img, t):
    for gi, g in enumerate(GROUPS):
        t0 = g[0]['t0'] - .04; t1 = g[-1]['t1'] + .16
        if gi + 1 < len(GROUPS): t1 = min(t1, GROUPS[gi + 1][0]['t0'] - .04)
        if t0 <= t < t1: break
    else: return img
    k = clamp((t - t0) / .09); size = int(92 * (.8 + .2 * eout(k) + .05 * math.sin(k * math.pi))); f = font(size, CF); dr = ImageDraw.Draw(img)
    words = [w['w'].upper() for w in g]; widths = [dr.textlength(w, font=f) for w in words]; sp = size * .26; tw = sum(widths) + sp * (len(words) - 1); x = (W - tw) / 2; y = int(H * .80)
    for i, wd in enumerate(words):
        act = g[i]['t0'] - .03 <= t < g[i]['t1'] + .03 or (i == len(g) - 1 and t >= g[i]['t0'])
        dr.text((x + 4, y + 6), wd, font=f, fill=(0, 0, 0), anchor='ls', stroke_width=int(size * .1), stroke_fill=(0, 0, 0))
        dr.text((x, y), wd, font=f, fill=(255, 226, 50) if act else (255, 255, 255), anchor='ls', stroke_width=int(size * .1), stroke_fill=(12, 12, 16)); x += widths[i] + sp
    return img
def frame(t):
    if t >= END: return Image.new('RGB', (W, H), (0, 0, 0))
    im = base_frame(t).convert('RGB')
    for c in CUTS:                                    # quick cross-dissolve over each cut
        if c - .1 <= t < c: im = Image.blend(im, base_frame(c + .001).convert('RGB'), (t - (c - .1)) / .1 * .6)
    return captions(vignette(im), t)
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
