"""Short 6 soundtrack: bouncy pizzicato bed + story sfx mixed with narration -> build/s6/mix.wav"""
import numpy as np, wave, sys
from scipy.signal import fftconvolve, butter, lfilter
sys.path.insert(0, 'short6')
import film
SR = 44100; E = film.events(); DUR = E['dur']; N = int(DUR * SR) + SR
rng = np.random.default_rng(61)
src = open('src/audio.py').read()
exec(src[src.index('def tt('):src.index('music = np.zeros(N)')])
music = np.zeros(N); sfx = np.zeros(N); dry = np.zeros(N)
def ding(f=1568, d=.8):
    t = tt(d); return (np.sin(2 * np.pi * f * t) + .4 * np.sin(2 * np.pi * f * 2.01 * t)) * np.exp(-t * 6)
def sparkle(f=2637, d=.5):
    t = tt(d); return (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * pi_f(f) * t)) * np.exp(-t * 10)
def pi_f(f): return f * 1.5
# bed: bouncy pizzicato, 112 bpm, C major, playful - starts right after the rule lands
beat = 60 / 112; t = E['rule'] + 1.2; k = 0
chords = [(48, 55, 64), (45, 52, 60), (41, 48, 57), (43, 50, 59)]
while t < E['end'] - .3:
    c = chords[(k // 4) % 4]
    if k % 4 == 0:
        put(music, pad([note(n) for n in c], beat * 4 + .5), t, .32); put(music, bassn(note(c[0] - 12), .9), t, .38)
    put(music, marimba(note(c[k % 3] + 12), .35), t, .3)
    put(music, marimba(note(c[(k + 2) % 3] + 24), .28), t + beat / 2, .18)
    if k % 2 == 1: put(music, tick(True), t + beat * .75, .10)
    if k % 8 == 5: put(music, sparkle(), t + beat * .5, .14)
    t += beat; k += 1
# sfx
put(sfx, ding(1319, 1.0), E['rule'] + .1, .35)                     # rule lands
for c in E['cuts']: put(sfx, whoosh(.28, 500, 4000), c - .18, .2)
put(dry, pop(), E['smudge'], .6); put(sfx, whoosh(.4, 300, 1800), E['smudge'] - .2, .3)
put(dry, impact(), E['roof'], 1.0); put(dry, crunch(), E['roof'] + .05, .8); put(sfx, whoosh(1.0, 150, 1200), E['roof'] - .1, .4)
for x in (E['shout1'], E['shout2'], E['shout3']):
    put(dry, pop(), x, .7); put(sfx, whoosh(.3, 600, 2500), x - .08, .25)
put(dry, pop(), E['laugh'], .5)
put(sfx, whoosh(.8, 800, 3000), E['flashback'] - .15, .35)
put(dry, impact(), E['dexclear'], .8); put(dry, ding(2093, .9), E['dexclear'] + .05, .5)
put(sfx, whoosh(.6, 400, 3000), E['dexclear'] - .1, .3)
put(dry, ding(1760, .7), E['punch'], .5); put(dry, pop(), E['punch'] + .15, .6)
put(sfx, cheer(1.2), E['chase'] + 1.0, .4)
ir_t = tt(1.2); ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 6); ir = filt(ir, 200, 6000); ir /= np.sqrt((ir ** 2).sum())
def rev(x, wet): return x + fftconvolve(x, ir)[:len(x)] * wet
music = rev(music, .25); sfx = rev(sfx, .2)
cutn = int((E['end'] + .03) * SR); music[cutn:] = 0; sfx[cutn:] = 0; dry[cutn:] = 0
w = wave.open("build/s6/vo.wav"); vo = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768; w.close()
vo = filt(vo, 70); v = np.zeros(N); v[:min(N, len(vo))] = vo[:N]
e = np.sqrt(np.maximum(1e-9, lfilter([1 - .999], [1, -.999], v * v))); g = np.minimum(1.0, (0.16 / np.maximum(e, 1e-4)) ** .4); v = v * g; v /= np.abs(v).max() / .92
ve = np.sqrt(lfilter([1 - .9995], [1, -.9995], v * v)); duck = 1 - .4 * np.clip(ve / .08, 0, 1)
def arms(x, m=None):
    m = np.abs(x) > 1e-4 if m is None else m
    return np.sqrt((x[m] ** 2).mean()) if m.any() else 0
vr = arms(v, ve > .03); mus = music * duck; mus *= (.2 * vr) / arms(mus)
fx = (sfx * .55 + dry * .5) * (1 - .35 * np.clip(ve / .08, 0, 1)); fx *= min(1.0, .55 / np.abs(fx).max())
mix = (np.tanh((v + mus + fx) * 1.1) * .97)[:int(DUR * SR)]
w = wave.open("build/s6/mix.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([mix, mix], 1) * 32767).astype(np.int16).tobytes()); w.close()
print("mix ok", len(mix) / SR)
