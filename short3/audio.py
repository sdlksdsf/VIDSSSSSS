"""Short 3 soundtrack: synthesised music + sound effects mixed with the dialogue -> build/s3/mix.wav"""
import numpy as np, wave, sys
from scipy.signal import fftconvolve, butter, lfilter
sys.path.insert(0, 'short3')
import film
SR = 44100; E = film.events(); DUR = E['dur']; N = int(DUR * SR) + SR
rng = np.random.default_rng(23)
src = open('src/audio.py').read()                      # reuse the instrument / sfx synths of short 1
exec(src[src.index('def tt('):src.index('music = np.zeros(N)')])
st, ps, pe = E['st'], film.ps, film.pe
music = np.zeros(N); sfx = np.zeros(N); dry = np.zeros(N)
CH = {'C': (48, 52, 55), 'Am': (45, 48, 52), 'F': (41, 45, 48), 'G': (43, 47, 50), 'Em': (40, 43, 47), 'Dm': (38, 41, 45)}
def slide(f0, f1, d=.5):
    t = tt(d); return np.sin(2 * np.pi * np.cumsum(f0 + (f1 - f0) * t / d) / SR) * env(len(t), .01, .08)
def click():
    t = tt(.07); return filt(rng.standard_normal(len(t)), 1800, 7000) * np.exp(-t * 200) * 1.6 + np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 160) * .8
def ratchet():
    return np.concatenate([np.pad(click(), (0, int(.035 * SR))) * (.5 + .1 * i) for i in range(5)] + [click() * 1.6])
def coin():
    t = tt(.5); return (np.sin(2 * np.pi * 1976 * t) * (t < .08) + np.sin(2 * np.pi * 2637 * t) * (t >= .08)) * np.exp(-np.clip(t - .08, 0, None) * 9) * .6
def ding(f=1568):
    t = tt(1.0); return (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.01 * t)) * np.exp(-t * 5)
def flutter(d=1.2):
    t = tt(d); return filt(rng.standard_normal(len(t)), 900, 5000) * (np.sin(2 * np.pi * 26 * t) > .2) * env(len(t), .05, .2) * .5
def laugh(d=1.3, n=9):
    t = tt(d); x = np.zeros(len(t))
    for i in range(n):
        f0 = rng.uniform(190, 520); rate = rng.uniform(5.5, 8); ph0 = rng.uniform(0, 1); on = rng.uniform(0, .25)
        g = np.clip(np.sin(2 * np.pi * (rate * t + ph0)), 0, 1) ** 1.5 * np.clip((t - on) / .05, 0, 1) * np.exp(-np.clip(t - d * .5, 0, None) * 3)
        f = f0 * (1 - .12 * t / d) * (1 + .05 * np.sin(2 * np.pi * rate * t)); ph = 2 * np.pi * np.cumsum(f) / SR
        v = np.sin(ph) + .5 * np.sin(2 * ph) + .3 * np.sin(3 * ph); fc = rng.uniform(700, 1500); x += filt(v, fc * .6, fc * 1.8) * g
    return x / n * 2.2
def gasp(d=.55):
    t = tt(d); return filt(rng.standard_normal(len(t)), 700, 3500) * (t / d) ** 2 * env(len(t), .01, .03) * 1.2
def siren(d):
    t = tt(d); f = 760 + 280 * np.sin(2 * np.pi * 1.6 * t); x = np.sin(2 * np.pi * np.cumsum(f) / SR); x = x + .3 * np.sign(x)
    return filt(x, 400, 3500) * env(len(t), .3, .5) * np.linspace(.4, 1, len(t)) * .5
def wah(d=1.6):
    t = tt(d); f = 520 - 150 * (t / d) + 60 * np.sin(2 * np.pi * 6.5 * t); ph = 2 * np.pi * np.cumsum(f) / SR
    return filt(np.sin(ph) + .4 * np.sign(np.sin(ph)), 300, 2400) * env(len(t), .05, .3) * (.6 + .4 * np.sin(2 * np.pi * 3 * t)) * .5
def gulp():
    t = tt(.22); return np.sin(2 * np.pi * np.cumsum(180 + 500 * (t / .22) ** 2) / SR) * env(len(t), .01, .03)
def bark():
    t = tt(.16); return filt(np.sign(np.sin(2 * np.pi * np.cumsum(520 - 900 * t) / SR)), 400, 2600) * env(len(t), .005, .06)
def groove(t0, t1, gain=1.0, bar=1.44, prog=('C', 'F', 'G', 'C', 'Am', 'F', 'G', 'G'), bass=True):
    t = t0; k = 0
    while t < t1 - .1:
        r, th, fi = CH[prog[k % len(prog)]]; pat = [r, fi, th + 12, fi, r + 12, fi, th + 12, r + 12]; s = bar / 8
        for j, n in enumerate(pat):
            if t + j * s < t1 - .04:
                put(music, marimba(note(n + 12)), t + j * s, (.36 if j % 2 == 0 else .25) * gain)
                if j % 2 == 1: put(music, tick(j % 4 == 1), t + j * s, .14 * gain)
                if j % 4 == 0: put(music, thud(), t + j * s, .18 * gain)
                if j % 4 == 2: put(music, snap(), t + j * s, .12 * gain)
        if bass: put(music, bassn(note(r - 12), .6), t, .5 * gain); put(music, bassn(note(fi - 12), .35), t + bar * .5, .36 * gain); put(music, bassn(note(r - 12), .3), t + bar * .75, .3 * gain)
        t += bar; k += 1
def sneak(t0, t1, g=.5):
    seq = [48, 51, 54, 51, 48, 51, 54, 57]; t = t0; i = 0
    while t < t1 - .05: put(music, bassn(note(seq[i % 8]), .3) + marimba(note(seq[i % 8] + 12), .3) * .5, t, g); t += .24; i += 1
def cutpop(n, g=.4): put(dry, pop(), st[n] + .02, g); put(sfx, whoosh(.22, 600, 5000), st[n] - .13, .2)

# ---- 0-6 s hook: stroll -> grab -> THIEF!
groove(0.0, E['grab'] - .05, .8, bass=False)
put(sfx, whoosh(.5, 300, 4000), E['grab'] - .45, .8); put(dry, impact()[:int(.7 * SR)] * env(int(.7 * SR), .003, .3), E['grab'], .9); put(dry, scratch(), E['grab'] - .05, .5)
put(dry, impact()[:int(.9 * SR)] * env(int(.9 * SR), .003, .4), E['thief'] - .03, 1.0); put(sfx, slide(300, 900, .25), E['thief'] - .28, .3)
put(sfx, gasp(), st['D'] + .05, .7); put(dry, bonk(), E['ball'] + .45, .5); put(dry, bark(), E['ball'] + .1, .4); put(dry, bark(), E['ball'] + .34, .35)
# ---- the argument
groove(st['E_'], st['Hs'] - .05, .85, prog=('Am', 'F', 'C', 'G'))
cutpop('E_'); cutpop('Fk'); put(dry, coin(), ps(5) + .45, .5); put(dry, thud(), E['pay'], .6); cutpop('G')
put(sfx, whoosh(.3, 500, 5000), st['Hs'] - .1, .4); put(dry, pop(), E['ticket'], .7); put(dry, pop(), E['coupon'], .7); put(dry, marimba(note(84), .4), E['ticket'], .4); put(dry, marimba(note(88), .4), E['coupon'], .4)
put(dry, slide(500, 180, .5), E['coupon'] + .45, .3)                                    # sad trombone-ish
put(sfx, flutter(1.25), E['moth'], .6); put(dry, pop(), E['laugh1'] + .25, .4)
put(sfx, laugh(1.6), E['laugh1'], .8)
groove(E['laugh1'], st['L_'] - .05, .9, prog=('C', 'G', 'F', 'G'))
cutpop('J'); cutpop('K_'); put(dry, ding(2093), ps(15) + .25, .3); put(sfx, laugh(1.2), E['laugh2'], .75)
# ---- cops
put(sfx, siren(2.4), E['siren'] - .1, .7); put(dry, slide(160, 60, .4), E['siren'] + .9, .4)
put(sfx, wah(1.3), E['cry'], .5)
tm = st['L_']; k = 0
while tm < st['N'] - .1:
    put(music, thud(), tm, .6); put(music, bassn(note(36 if k % 4 < 2 else 34), .4), tm, .55)
    if k % 2: put(music, tick(True), tm + .2, .2)
    tm += .4; k += 1
put(sfx, wah(1.0), st['M'] + .1, .3); put(dry, gulp(), E['gulp'], .6)
# ---- that's when I noticed
put(dry, ding(1568), E['notice'], .45); put(dry, ding(2349), E['notice'] + .18, .35)
sneak(st['N'] + .9, E['idpop'] - .15)
put(dry, scratch(), E['idpop'] - .2, .5); put(dry, impact()[:int(1.0 * SR)] * env(int(1.0 * SR), .003, .5), E['idpop'], .9); put(sfx, gasp(), E['idpop'] + .15, .7)
put(dry, thud(), E['age'], .8); put(dry, ding(1047), E['age'], .3)
groove(st['R'], E['cover'] - 3.0, .7, prog=('Dm', 'G', 'C', 'Am'))
cutpop('R'); put(sfx, laugh(1.1), E['laugh3'], .7)
put(sfx, whoosh(.5, 300, 3000), E['marg'], .5); put(dry, thud(), E['marg'] + .8, .5)
tm = st['T_']; k = 0
while tm < E['cover'] - .05:
    put(music, thud(), tm, .7); put(music, bassn(note(36 + k // 2), .3), tm, .6); tm += .3; k += 1
put(dry, scratch(), E['cover'] - .08, .6); put(sfx, gasp(.5), E['cover'] + .08, .9); put(dry, pop(), E['cover'] + .5, .3)
put(dry, ratchet(), E['cuff'] - .2, .9); put(sfx, laugh(1.1), E['laugh4'], .7)
# ---- fries
put(sfx, siren(1.2), st['V_'] - 1.0, .25)
groove(st['V_'], E['no'] - .2, .85, prog=('C', 'F', 'G', 'C'))
for i in range(4): put(dry, crunch(), st['V_'] + .5 + i * .62, .25)
put(dry, thud(), E['no'], .9); put(dry, pop(), E['no'] + .02, .6)

ir_t = tt(1.2); ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 5.5); ir = filt(ir, 200, 6000); ir /= np.sqrt((ir ** 2).sum())
def rev(x, wet): return x + fftconvolve(x, ir)[:len(x)] * wet
music = rev(music, .15); sfx = rev(sfx, .22)
tEnd = E['end']; cutn = int((tEnd + .03) * SR); music[cutn:] = 0; sfx[cutn:] = 0; dry[cutn:] = 0
w = wave.open("build/s3/vo.wav"); vo = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768; w.close()
vo = filt(vo, 70); v = np.zeros(N); v[:min(N, len(vo))] = vo[:N]
e = np.sqrt(np.maximum(1e-9, lfilter([1 - .999], [1, -.999], v * v))); g = np.minimum(1.0, (0.16 / np.maximum(e, 1e-4)) ** .4); v = v * g; v /= np.abs(v).max() / .92
ve = np.sqrt(lfilter([1 - .9995], [1, -.9995], v * v)); duck = 1 - .45 * np.clip(ve / .08, 0, 1)
def arms(x, m=None):
    m = np.abs(x) > 1e-4 if m is None else m
    return np.sqrt((x[m] ** 2).mean()) if m.any() else 0
vr = arms(v, ve > .03)
mus = music * duck; mus *= (.22 * vr) / arms(mus)
fx = (sfx * .55 + dry * .5) * (1 - .35 * np.clip(ve / .08, 0, 1)); pk = np.abs(fx).max(); fx *= min(1.0, .75 / pk)
mix = np.tanh((v + mus + fx) * 1.1) * .97
print("voice rms %.3f music rms %.3f fx rms %.3f fx peak %.2f" % (vr, arms(mus), arms(fx), np.abs(fx).max()))
mix = mix[:int(DUR * SR)]
w = wave.open("build/s3/mix.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([mix, mix], 1) * 32767).astype(np.int16).tobytes()); w.close()
print("mix ok", len(mix) / SR, "peak", np.abs(mix).max())
