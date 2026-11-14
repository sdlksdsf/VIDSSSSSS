"""Short 5 soundtrack: soft bed + body sfx mixed with narration -> build/s5/mix.wav"""
import numpy as np, wave, sys
from scipy.signal import fftconvolve, butter, lfilter
sys.path.insert(0, 'short5')
import film
SR = 44100; E = film.events(); DUR = E['dur']; N = int(DUR * SR) + SR
rng = np.random.default_rng(51)
src = open('src/audio.py').read()
exec(src[src.index('def tt('):src.index('music = np.zeros(N)')])
music = np.zeros(N); sfx = np.zeros(N); dry = np.zeros(N)
def squelch(d=.5):
    t = tt(d); n = filt(rng.standard_normal(len(t)), 200, 1400); return n * (0.5 + 0.5 * np.sin(2 * np.pi * (9 + 14 * t / d) * t)) * env(len(t), .02, d * .5)
def ding(f=1568, d=.8):
    t = tt(d); return (np.sin(2 * np.pi * f * t) + .4 * np.sin(2 * np.pi * f * 2.01 * t)) * np.exp(-t * 6)
# bed: calm marimba pattern, 100 bpm, C major-ish, starts after the hit
beat = .6; t = E['smack'] + .5; k = 0; ch = [(48, 55, 64), (45, 52, 60), (41, 48, 57), (43, 50, 59)]
while t < E['end'] - .2:
    c = ch[(k // 4) % 4]
    if k % 4 == 0: put(music, pad([note(n) for n in c], beat * 4 + .5), t, .4); put(music, bassn(note(c[0] - 12), .9), t, .4)
    put(music, marimba(note(c[k % 3] + 12), .4), t, .3); put(music, marimba(note(c[(k + 1) % 3] + 24), .3), t + beat / 2, .16)
    t += beat; k += 1
# sfx
put(sfx, whoosh(.5, 300, 3000), E['smack'] - .45, .4); put(dry, impact(), E['smack'], 1.0); put(dry, thud(), E['smack'], .9)
for c in E['cuts']: put(sfx, whoosh(.3, 500, 4000), c - .2, .22)
for i in range(4): put(dry, pop(), E['pop'] + i * .16, .6)
put(sfx, squelch(1.2), E['pop'] + .1, .5)
put(sfx, whoosh(.9, 200, 1500), E['blue'], .25)
put(sfx, squelch(1.4), E['cells'], .35); put(sfx, squelch(1.0), E['eat'] + .1, .5)
for x, f in ((E['green'], 1175), (E['yellow'], 1319), (E['gone'], 1760)): put(dry, ding(f), x, .3)
put(dry, ding(2093, 1.0), E['last'] + .3, .2)
ir_t = tt(1.2); ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 6); ir = filt(ir, 200, 6000); ir /= np.sqrt((ir ** 2).sum())
def rev(x, wet): return x + fftconvolve(x, ir)[:len(x)] * wet
music = rev(music, .25); sfx = rev(sfx, .2)
cutn = int((E['end'] + .03) * SR); music[cutn:] = 0; sfx[cutn:] = 0; dry[cutn:] = 0
w = wave.open("build/s5/vo.wav"); vo = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768; w.close()
vo = filt(vo, 70); v = np.zeros(N); v[:min(N, len(vo))] = vo[:N]
e = np.sqrt(np.maximum(1e-9, lfilter([1 - .999], [1, -.999], v * v))); g = np.minimum(1.0, (0.16 / np.maximum(e, 1e-4)) ** .4); v = v * g; v /= np.abs(v).max() / .92
ve = np.sqrt(lfilter([1 - .9995], [1, -.9995], v * v)); duck = 1 - .4 * np.clip(ve / .08, 0, 1)
def arms(x, m=None):
    m = np.abs(x) > 1e-4 if m is None else m
    return np.sqrt((x[m] ** 2).mean()) if m.any() else 0
vr = arms(v, ve > .03); mus = music * duck; mus *= (.2 * vr) / arms(mus)
fx = (sfx * .55 + dry * .5) * (1 - .35 * np.clip(ve / .08, 0, 1)); fx *= min(1.0, .55 / np.abs(fx).max())
mix = (np.tanh((v + mus + fx) * 1.1) * .97)[:int(DUR * SR)]
w = wave.open("build/s5/mix.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([mix, mix], 1) * 32767).astype(np.int16).tobytes()); w.close()
print("mix ok", len(mix) / SR)
