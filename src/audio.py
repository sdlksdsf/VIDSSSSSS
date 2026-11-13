"""Synthesised music + sound effects, mixed with the narration -> build/mix.wav"""
import numpy as np, wave, json, sys
from scipy.signal import fftconvolve, butter, lfilter
sys.path.insert(0, 'src')
import film
SR = 44100; E = film.events(); DUR = E['dur']; N = int(DUR * SR) + SR
rng = np.random.default_rng(7)
def tt(d): return np.arange(int(d * SR)) / SR
def env(n, a=.005, r=.05):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
def filt(x, lo=None, hi=None, order=2):
    if lo and hi: b, a = butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band')
    elif lo: b, a = butter(order, lo / (SR / 2), 'high')
    else: b, a = butter(order, hi / (SR / 2), 'low')
    return lfilter(b, a, x)
def put(bus, x, t, g=1.0):
    i = int(t * SR)
    if i < 0: x = x[-i:]; i = 0
    if i >= len(bus): return
    x = x[:len(bus) - i]; bus[i:i + len(x)] += x * g
def note(n): return 440 * 2 ** ((n - 69) / 12)

def marimba(f, d=.5):
    t = tt(d); return (np.sin(2 * np.pi * f * t) * np.exp(-t * 7) + .35 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 28) + .15 * np.sin(2 * np.pi * f * 10 * t) * np.exp(-t * 60)) * env(len(t), .002, .02)
def piano(f, d=2.0, bright=1.0):
    t = tt(d); x = np.zeros(len(t))
    for k in range(1, 8):
        x += np.sin(2 * np.pi * f * k * (1 + .0004 * k * k) * t) / k ** 1.3 * np.exp(-t * (1.6 + .9 * k)) * bright ** (k - 1)
    return x * env(len(t), .004, .08)
def pad(fs, d):
    t = tt(d); x = np.zeros(len(t))
    for f in fs:
        for dt in (-.004, 0, .005):
            x += np.sin(2 * np.pi * f * (1 + dt) * t + rng.uniform(0, 6)) + .3 * np.sin(4 * np.pi * f * (1 + dt) * t)
    return x / (len(fs) * 3) * env(len(t), d * .3, d * .35)
def bassn(f, d=.5):
    t = tt(d); return (np.sin(2 * np.pi * f * t) + .3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 5) * env(len(t), .004, .03)
def tick(hi=True):
    t = tt(.05); return filt(rng.standard_normal(len(t)), 2500 if hi else 1500, 6000 if hi else 3500) * np.exp(-t * 160) + .5 * np.sin(2 * np.pi * (2100 if hi else 1500) * t) * np.exp(-t * 220)

# ---------------- sfx
def snap():
    t = tt(.12); x = filt(rng.standard_normal(len(t)), 1200, 5000) * np.exp(-t * 130) * 1.5 + np.sin(2 * np.pi * 1000 * t) * np.exp(-t * 90) * .7; return x
def freeze_fx():
    d = 1.3; t = tt(d); f = 1400 * np.exp(-t * 6) + 70; ph = 2 * np.pi * np.cumsum(f) / SR
    sweep = np.sin(ph) * np.exp(-t * 3.2) * (1 + .4 * np.sin(2 * np.pi * 28 * t)) * .5
    boom = np.sin(2 * np.pi * (52 + 30 * np.exp(-t * 14)) * t) * np.exp(-t * 4) * .9
    shim = filt(rng.standard_normal(len(t)), 5000) * np.exp(-t * 3.5) * .16
    return sweep + boom + shim
def unfreeze_fx():
    d = .6; t = tt(d); f = 100 + 1500 * (t / d) ** 2; ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(len(t), .02, .1) * .4 + filt(rng.standard_normal(len(t)), 3000) * (t / d) ** 2 * env(len(t), .01, .05) * .25
def whoosh(d=.35, lo=300, hi=3000):
    t = tt(d); x = rng.standard_normal(len(t)); g = np.exp(-((t - d * .55) / (d * .22)) ** 2)
    return (filt(x, lo, hi) * .6 + filt(x, hi) * .2 * (t / d)) * g
def pop():
    t = tt(.09); f = 380 + 700 * t / .09; return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30)
def bonk():
    t = tt(.5); return np.sin(2 * np.pi * 170 * t) * np.exp(-t * 18) + .5 * np.sin(2 * np.pi * (420 + 60 * np.sin(2 * np.pi * 11 * t)) * t) * np.exp(-t * 7)
def crunch():
    t = tt(.16); x = filt(rng.standard_normal(len(t)), 1500, 7000); g = (rng.random(len(t) // 220 + 1) > .45).repeat(220)[:len(t)]
    return x * g * np.exp(-t * 14)
def alarm(d):
    t = tt(d); sq = np.sign(np.sin(2 * np.pi * 2300 * t)) * (np.sin(2 * np.pi * 9 * t) > 0) * (np.sin(2 * np.pi * 2.2 * t + 1) > -.3)
    return filt(sq, 1500, 5000) * env(len(t), .01, .01) * .35
def thud():
    t = tt(.16); return np.sin(2 * np.pi * (120 - 200 * t) * t) * np.exp(-t * 30) + filt(rng.standard_normal(len(t)), None, 900) * np.exp(-t * 60) * .5
def noisebed(d, lo, hi, rate=.4):
    t = tt(d); x = filt(rng.standard_normal(len(t)), lo, hi)
    m = .6 + .4 * np.sin(2 * np.pi * rate * t + rng.uniform(0, 6)) * np.sin(2 * np.pi * rate * .37 * t + 1)
    return x * m * env(len(t), d * .2, d * .3)
def cheer(d):
    t = tt(d); x = np.zeros(len(t))
    for i in range(14):
        f0 = rng.uniform(500, 1500); a = .5 + .5 * np.sin(2 * np.pi * rng.uniform(2, 7) * t + rng.uniform(0, 6))
        x += filt(rng.standard_normal(len(t)), f0, f0 * 2.2) * a
    return x / 6 * env(len(t), d * .15, d * .4)
def heart():
    t = tt(.5); a = np.sin(2 * np.pi * (58 + 40 * np.exp(-t * 40)) * t) * np.exp(-t * 22)
    b = np.zeros(len(t)); k = int(.15 * SR); b[k:] = a[:-k] * .75; return a + b
def impact():
    d = 3.2; t = tt(d); sub = np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-t * 9)) / SR) * np.exp(-t * 1.5)
    crack = filt(rng.standard_normal(len(t)), None, 2500) * np.exp(-t * 18) * 1.2
    cl = sum(piano(note(n), d, 1.1) for n in (33, 40, 45, 46)) * .5
    return np.tanh((sub * 1.4 + crack + cl) * 1.3)
def scratch():
    d = .45; t = tt(d); f = 520 * np.exp(-t * 7) + 30; return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), .005, .2) * .6 + filt(rng.standard_normal(len(t)), 800, 4000) * np.exp(-t * 12) * .3

music = np.zeros(N); sfx = np.zeros(N); dry = np.zeros(N)
st, du = E['st'], E['du']
# ---------------- music A: playful (0 -> "As he got older")
CH = {'C': (48, 52, 55), 'Am': (45, 48, 52), 'F': (41, 45, 48), 'G': (43, 47, 50), 'Em': (40, 43, 47), 'Dm': (38, 41, 45)}
bar = 2.0; tA1 = st['S4a']
prog = ['C', 'Am', 'F', 'G']
k = 0; t = E['snaps'][0] + .55          # music only starts once the world has frozen
while t < tA1 - .1:
    r, th, fi = CH[prog[k % 4]]; pat = [r, th, fi, r + 12, fi, th, fi, r + 12]
    for j, n in enumerate(pat):
        if t + j * .25 < tA1 - .05:
            put(music, marimba(note(n + 12)), t + j * .25, .34 if j % 2 == 0 else .24)
            if j % 2 == 1: put(music, tick(j % 4 == 1), t + j * .25, .10)
    put(music, bassn(note(r - 12), .9), t, .5); put(music, bassn(note(r - 12), .5), t + 1.0, .38); put(music, bassn(note(fi - 12), .4), t + 1.5, .3)
    t += bar; k += 1
# ---------------- music B: thinning piano ("older" -> "quiet")
tB1 = st['S5a']; t = tA1; k = 0; progB = ['Am', 'F', 'C', 'G', 'Am', 'F']
while t < tB1 - 1.2:
    r, th, fi = CH[progB[k % 6]]; fade = 1 - .55 * (t - tA1) / (tB1 - tA1)
    seq = [r, fi, th + 12, fi] if t < st['S4e'] else [r, th + 12]
    step = bar / len(seq)
    for j, n in enumerate(seq): put(music, piano(note(n + 12), 2.2, .8), t + j * step, .36 * fade)
    put(music, pad([note(r), note(fi), note(th + 12)], bar + .6), t, .16 * fade)
    if t < st['S4e']: put(music, bassn(note(r - 12), 1.2), t, .4 * fade)
    t += bar; k += 1
# ---------------- music C: graduation (bright, cut off when the smile drops)
tC0 = st['S5a']; tC1 = E['smile_stop']; t = tC0; k = 0; progC = ['C', 'G', 'Am', 'F']
seg = np.zeros(int((tC1 - tC0 + .5) * SR))
while t < tC1:
    r, th, fi = CH[progC[k % 4]]; b = 1.0
    for j in range(4):
        tj = t - tC0 + j * .25
        for n in (r + 12, th + 12, fi + 12): put(seg, piano(note(n), .5, 1.0), tj, .2 if j else .28)
        put(seg, marimba(note(r + 24 + (0, 4, 7, 12)[j])), tj, .22); put(seg, tick(j % 2 == 0), tj + .125, .08)
    put(seg, bassn(note(r - 12), .9), t - tC0, .5)
    t += b; k += 1
seg = seg[:int((tC1 - tC0) * SR)]; seg[-int(.04 * SR):] *= np.linspace(1, 0, int(.04 * SR))
put(music, seg, tC0); put(sfx, scratch(), tC1 - .02, .5)
# ---------------- drone under the confrontation
tD0 = tC1 + .3; tD1 = st['S9a'] - .9
td = tt(tD1 - tD0); dr = (np.sin(2 * np.pi * 55 * td) + .5 * np.sin(2 * np.pi * 82.6 * td + np.sin(td * .7) * 2) + .25 * np.sin(2 * np.pi * 110.5 * td)) * env(len(td), 2.0, .25) * (.5 + .5 * td / td[-1])
put(music, dr, tD0, .2)
# ---------------- music D: sad piano for the reveal + ending
tE0 = st['S9a'] + .15; tEnd = E['end']; progD = ['Am', 'F', 'C', 'G', 'Am', 'F', 'Dm', 'Am']; t = tE0; k = 0; barD = 2.6
while t < tEnd - .3:
    r, th, fi = CH[progD[k % 8]]
    put(music, pad([note(r), note(th), note(fi), note(r + 12)], barD + 1.0), t, .3)
    if t >= st['S10a'] - 1.0:
        seq = [r, fi, r + 12, th + 12, fi + 12, th + 12]; step = barD / 6
        for j, n in enumerate(seq):
            if t + j * step < tEnd - .1: put(music, piano(note(n + 12), 2.6, .75), t + j * step, .4)
    else:
        put(music, piano(note(r), 3.0, .7), t, .42); put(music, piano(note(th + 12), 3.0, .7), t + barD / 2, .3)
    t += barD; k += 1
cutn = int(tEnd * SR); music[cutn - int(.03 * SR):cutn] *= np.linspace(1, 0, int(.03 * SR)); music[cutn:] = 0

# ---------------- sound effects
# --- the hook: ball screams in, snap, dead stop, two clock ticks, then the music kicks in
tf0 = E['snaps'][0]
rz = tt(tf0); riser = np.sin(2 * np.pi * np.cumsum(180 + 900 * (rz / tf0) ** 2) / SR) * (rz / tf0) ** 1.5 * .5
put(sfx, riser * env(len(rz), .01, .01), 0, .7)
wb = whoosh(tf0 + .1, 200, 3500); put(sfx, wb, 0, 1.0)
put(sfx, freeze_fx(), tf0, .5)
for i in range(2): put(dry, tick(i == 0), tf0 + .22 + i * .17, .55)
put(sfx, whoosh(.45, 400, 4000), E['flick'] - .5, .45)            # camera whip as he steps out
put(dry, pop(), E['flick'], .6)
put(dry, marimba(note(84), .6) + marimba(note(91), .6) * .6, E['wink'], .5)
for i, ts in enumerate(E['snaps']):
    put(dry, snap(), ts - .01, .9); put(sfx, freeze_fx(), ts, .55 if i in (0, 1, 5) else .4)
    put(sfx, whoosh(.3, 2000, 8000)[::-1], ts - .3, .25)
for ts in E['unfreeze']:
    put(dry, snap(), ts - .01, .9); put(sfx, unfreeze_fx(), ts - .05, .5); put(sfx, whoosh(.3, 300, 3000), ts + .05, .6); put(dry, bonk(), ts + .24, .6)
for tcut in E['cuts'][1:-1]:
    if tcut < st['S5c'] or tcut >= st['S10a']: put(sfx, whoosh(.26, 500, 5000), tcut - .15, .16)
put(dry, pop(), st['S3b'] + du['S3b'] * .57, .5)
for i in range(3): put(dry, crunch(), st['S3d'] + du['S3d'] * .68 + i * .2, .4)
put(dry, pop(), st['S3d'] + du['S3d'] * .12, .3)
put(dry, alarm(du['S4c'] * .42), st['S4c'], .5)
for i in range(1, 11): put(dry, thud(), st['S4d'] + du['S4d'] * i / 11, .35)
for i in range(4): put(dry, pop(), st['S4a'] + .15 + i * .2, .18 + .04 * i)
put(sfx, noisebed(du['S4e'] + du['S4f'] + .6, 150, 900), st['S4e'], .5)          # lonely wind
put(sfx, cheer(tC1 - tC0 + .4), tC0, .42)
put(sfx, noisebed(st['S8a'] - tC1, 300, 1500, .8), tC1, .1)                      # distant murmur
# heartbeat: starts on the shaking hands, speeds up, stops when he freezes
t = st['S7b']; hb_end = film.pe(30) + .05
while t < hb_end:
    p = (t - st['S7b']) / (hb_end - st['S7b']); put(dry, heart(), t, .5 + .5 * p); t += .78 - .4 * p
t = st['S8a'] + .1
while t < st['S8b'] + .5:
    put(dry, thud(), t, .5); t += .33 / 1.0 * (1 if t < st['S8b'] else 1.6)
put(sfx, whoosh(.5, 300, 4000), st['S8a'] - .2, .5)
put(sfx, impact(), st['S9a'] - .02, 1.0)
put(sfx, impact()[:int(1.5 * SR)] * env(int(1.5 * SR), .005, .6), st['S9b'] - .02, .42); put(sfx, impact()[:int(1.5 * SR)] * env(int(1.5 * SR), .005, .6), st['S9c'] - .02, .42)
# clock: slow tick-tock through the ending, a last tick on black
t = st['S10b']; i = 0
while t < tEnd - .4:
    put(dry, tick(i % 2 == 0), t, .5); put(sfx, tick(i % 2 == 0), t, .25); t += .5; i += 1
last = np.concatenate([tick(True), np.zeros(200)]); put(dry, last, tEnd + .02, 1.3); put(sfx, thud(), tEnd + .02, .5)

# ---------------- reverb + mix
ir_t = tt(1.6); ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 4.2); ir = filt(ir, 200, 6000); ir /= np.sqrt((ir ** 2).sum())
def rev(x, wet): return x + fftconvolve(x, ir)[:len(x)] * wet
music = rev(music, .22); sfx = rev(sfx, .3)
sfx[int((tEnd + 1.0) * SR):] *= 0
w = wave.open("build/vo.wav"); vo = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768; w.close()
vo = filt(vo, 70); v = np.zeros(N); v[:min(N, len(vo))] = vo[:N]
# gentle compression on voice
e = np.sqrt(np.maximum(1e-9, lfilter([1 - .999], [1, -.999], v * v))); g = np.minimum(1.0, (0.16 / np.maximum(e, 1e-4)) ** .4); v = v * g; v /= np.abs(v).max() / .92
# duck music under voice
ve = np.sqrt(lfilter([1 - .9995], [1, -.9995], v * v)); duck = 1 - .45 * np.clip(ve / .08, 0, 1)
def arms(x, m=None):
    m = np.abs(x) > 1e-4 if m is None else m
    return np.sqrt((x[m] ** 2).mean()) if m.any() else 0
vr = arms(v, ve > .03)
mus = music * duck; mus *= (.21 * vr) / arms(mus)           # music about 13.5 dB under the voice
mus[int(tE0 * SR):] *= 1.3
fx = sfx * .55 + dry * .5; pk = np.abs(fx).max(); fx *= min(1.0, .8 / pk)
mix = v + mus + fx
mix = np.tanh(mix * 1.1) * .97
print("voice rms %.3f music rms %.3f fx rms %.3f fx peak %.2f" % (vr, arms(mus), arms(fx), np.abs(fx).max()))
mix = mix[:int(DUR * SR)]
st2 = np.stack([mix, mix], 1)
w = wave.open("build/mix.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st2 * 32767).astype(np.int16).tobytes()); w.close()
print("mix ok", len(mix) / SR, "peak", np.abs(mix).max())
