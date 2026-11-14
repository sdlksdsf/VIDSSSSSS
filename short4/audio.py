"""Short 4 soundtrack: pulse bed + map sfx mixed with narration -> build/s4/mix.wav"""
import numpy as np, wave, sys
from scipy.signal import fftconvolve, butter, lfilter
sys.path.insert(0, 'short4')
import film
SR = 44100; E = film.events(); DUR = E['dur']; N = int(DUR * SR) + SR
rng = np.random.default_rng(31)
src = open('src/audio.py').read()
exec(src[src.index('def tt('):src.index('music = np.zeros(N)')])
music = np.zeros(N); sfx = np.zeros(N); dry = np.zeros(N)
def slide(f0, f1, d=.5):
    t = tt(d); return np.sin(2 * np.pi * np.cumsum(f0 + (f1 - f0) * t / d) / SR) * env(len(t), .01, .08)
def ding(f=1568, d=1.0):
    t = tt(d); return (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.01 * t)) * np.exp(-t * 5)
def buzz():
    t = tt(.45); return filt(np.sign(np.sin(2 * np.pi * 110 * t)) + np.sign(np.sin(2 * np.pi * 116 * t)), 150, 2500) * env(len(t), .005, .05) * .5
def hit(d=.9): n = int(d * SR); return impact()[:n] * env(n, .003, d * .5)
def blip(f): t = tt(.07); return np.sin(2 * np.pi * f * t) * np.exp(-t * 45)
# bed: minor-key pulse, 120 bpm, tension rises toward the reveal
beat = .5; t = 0.0; k = 0; roots = [45, 45, 41, 43]
while t < E['reveal'] - .3:
    r = roots[(k // 8) % 4]
    put(music, bassn(note(r - 12), .4), t, .5)
    if k % 2 == 1: put(music, tick(k % 4 == 1), t + .25, .2)
    for j, n in enumerate((r + 12, r + 19, r + 24, r + 19)): put(music, marimba(note(n), .3), t + j * beat / 4, .22 if j else .3)
    if k % 8 == 0: put(music, pad([note(r), note(r + 7), note(r + 15 if r != 41 else r + 16)], beat * 8 + .6), t, .32)
    if t > E['sea'] - .2 and k % 2 == 0: put(music, thud(), t, .35)
    t += beat; k += 1
for n, g in ((57, .5), (64, .45), (69, .45), (73, .5)): put(music, piano(note(n), 2.4, 1.2), E['reveal'], g * .7)
put(music, pad([note(45), note(52), note(61)], E['end'] - E['reveal'] + .3), E['reveal'], .4)
# sfx
put(sfx, whoosh(1.0, 200, 3000), 0.0, .5); put(dry, hit(), .02, .5)
for i in range(4): put(dry, pop(), E['n'] + i * .14, .5); put(dry, blip(880 + i * 150), E['n'] + i * .14, .3)
for c in E['cuts']: put(sfx, whoosh(.3, 500, 5000), c - .2, .35)
for x in (E['x1'], E['x2']): put(dry, hit(.6), x, .9); put(dry, buzz(), x, .45)
n = 33
for i in range(n): put(dry, blip(700 + i * 22), E['isl0'] + i * (E['isl1'] - E['isl0']) / n, .28)
put(sfx, whoosh(.4, 300, 3000), E['india'] - .3, .5); put(dry, thud(), E['india'] + .3, .8)
put(sfx, slide(300, 900, 1.0), E['merge'], .2); put(dry, pop(), E['merge'] + 1.1, .6); put(dry, ding(1568, .6), E['nyc'] + .1, .3)
put(dry, hit(.6), E['split'], .6); put(dry, hit(.7), E['y1995'], .8)
put(sfx, slide(200, 700, .9), E['move'], .3); put(sfx, whoosh(.9, 300, 4000), E['move'], .4); put(dry, thud(), E['move'] + .9, .7)
put(sfx, whoosh(1.6, 400, 6000), E['sun'], .35); put(dry, ding(2093, .8), E['utc'], .3)
put(sfx, noisebed(E['reveal'] - E['sea'], 300, 1800, 1.2), E['sea'], .22); put(sfx, slide(120, 60, 2.0), E['rise'] + .1, .4)
put(sfx, slide(200, 1200, .5), E['reveal'] - .5, .3); put(dry, hit(1.2), E['reveal'], 1.0)
put(dry, scratch(), E['strike'] - .05, .6); put(dry, buzz(), E['strike'] + .05, .5)
put(dry, ding(1319, .9), E['right'], .45); put(dry, ding(1976, .9), E['right'] + .12, .4); put(dry, pop(), E['right'], .6)
ir_t = tt(1.4); ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 5); ir = filt(ir, 200, 6000); ir /= np.sqrt((ir ** 2).sum())
def rev(x, wet): return x + fftconvolve(x, ir)[:len(x)] * wet
music = rev(music, .22); sfx = rev(sfx, .25)
cutn = int((E['end'] + .03) * SR); music[cutn:] = 0; sfx[cutn:] = 0; dry[cutn:] = 0
w = wave.open("build/s4/vo.wav"); vo = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768; w.close()
vo = filt(vo, 70); v = np.zeros(N); v[:min(N, len(vo))] = vo[:N]
e = np.sqrt(np.maximum(1e-9, lfilter([1 - .999], [1, -.999], v * v))); g = np.minimum(1.0, (0.16 / np.maximum(e, 1e-4)) ** .4); v = v * g; v /= np.abs(v).max() / .92
ve = np.sqrt(lfilter([1 - .9995], [1, -.9995], v * v)); duck = 1 - .4 * np.clip(ve / .08, 0, 1)
def arms(x, m=None):
    m = np.abs(x) > 1e-4 if m is None else m
    return np.sqrt((x[m] ** 2).mean()) if m.any() else 0
vr = arms(v, ve > .03); mus = music * duck; mus *= (.24 * vr) / arms(mus)
fx = (sfx * .55 + dry * .5) * (1 - .35 * np.clip(ve / .08, 0, 1)); fx *= min(1.0, .6 / np.abs(fx).max())
mix = (np.tanh((v + mus + fx) * 1.1) * .97)[:int(DUR * SR)]
print("voice %.3f music %.3f fx %.3f" % (vr, arms(mus), arms(fx)))
w = wave.open("build/s4/mix.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([mix, mix], 1) * 32767).astype(np.int16).tobytes()); w.close()
print("mix ok", len(mix) / SR)
