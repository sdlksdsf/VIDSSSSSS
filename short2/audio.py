"""Short 2 soundtrack: synthesised music + sound effects, mixed with the narration -> build/s2/mix.wav"""
import numpy as np, wave, sys
from scipy.signal import fftconvolve, butter, lfilter
sys.path.insert(0, 'short2')
import film
SR = 44100; E = film.events(); DUR = E['dur']; N = int(DUR * SR) + SR
rng = np.random.default_rng(11)
src = open('src/audio.py').read()                      # reuse the instrument / sfx synths of short 1
exec(src[src.index('def tt('):src.index('music = np.zeros(N)')])
st, du, ps, pe = E['st'], E['du'], film.ps, film.pe
music = np.zeros(N); sfx = np.zeros(N); dry = np.zeros(N)
CH = {'C': (48, 52, 55), 'Am': (45, 48, 52), 'F': (41, 45, 48), 'G': (43, 47, 50), 'Em': (40, 43, 47), 'Dm': (38, 41, 45)}

def glass():
    d = 1.1; t = tt(d); x = filt(rng.standard_normal(len(t)), 2500) * np.exp(-t * 9)
    for i in range(22):
        f = rng.uniform(2500, 9000); t0 = rng.uniform(0, .35); tk = np.clip(t - t0, 0, None)
        x += .25 * np.sin(2 * np.pi * f * tk) * np.exp(-tk * rng.uniform(14, 40)) * (t >= t0)
    return x * .6 + thud()[0] * 0 + np.pad(thud(), (0, len(t) - len(thud()))) * 1.2
def scream(d=1.9):
    t = tt(d); x = np.zeros(len(t))
    for i in range(16):
        f0 = rng.uniform(420, 980); vib = 1 + .03 * np.sin(2 * np.pi * rng.uniform(5, 8) * t + rng.uniform(0, 6)); gl = 1 + .25 * np.exp(-t * rng.uniform(2, 6))
        ph = 2 * np.pi * np.cumsum(f0 * vib * gl) / SR; v = np.sign(np.sin(ph)) * .5 + np.sin(ph)
        fc = rng.uniform(900, 2600); v = filt(v, fc * .7, fc * 1.5)
        on = rng.uniform(0, .18); x += v * np.clip((t - on) / .05, 0, 1) * np.exp(-np.clip(t - d * .55, 0, None) * 3)
    return x / 5 + filt(rng.standard_normal(len(t)), 800, 3000) * .12 * env(len(t), .05, d * .5)
def clunk(f=110):
    t = tt(.3); return np.sin(2 * np.pi * (f + 90 * np.exp(-t * 60)) * t) * np.exp(-t * 16) + filt(rng.standard_normal(len(t)), 1500, 5000) * np.exp(-t * 90) * .7
def click():
    t = tt(.07); return (filt(rng.standard_normal(len(t)), 1800, 7000) * np.exp(-t * 200) * 1.6 + np.sin(2 * np.pi * 1700 * t) * np.exp(-t * 160) * .8) + np.pad(tick(False) * .8, (int(.035 * SR), 0))[:len(t)]
def hum(d, f=120):
    t = tt(d); return (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * 2 * f * t) + .3 * np.sin(2 * np.pi * 3 * f * t) + .2 * np.sign(np.sin(2 * np.pi * f * t))) * env(len(t), .05, .02) * .3
def buzz(d):
    t = tt(d); g = (np.sin(2 * np.pi * 9 * t) + np.sin(2 * np.pi * 14.3 * t + 1) > .2); return filt(np.sign(np.sin(2 * np.pi * 100 * t)) * g, 400, 5000) * env(len(t), .01, .02) * .4
def zap():
    t = tt(.35); return filt(rng.standard_normal(len(t)), 1500, 9000) * np.exp(-t * 16) * (1 + np.sign(np.sin(2 * np.pi * 60 * t))) * .7 + pop()[0] * 0
def snore(d=1.15):
    t = tt(d); a = np.sin(np.pi * t / d) ** 1.5
    x = filt(rng.standard_normal(len(t)), 150, 900) * (.6 + .4 * np.sign(np.sin(2 * np.pi * 27 * t))) * a + np.sign(np.sin(2 * np.pi * 78 * t)) * a * .25 * (.5 + .5 * np.sin(2 * np.pi * 27 * t))
    w = tt(.55); wh = np.sin(2 * np.pi * np.cumsum(1250 - 500 * w / .55) / SR) * np.sin(np.pi * w / .55) * .35
    return np.concatenate([filt(x, None, 1400), wh])
def yawn():
    d = .9; t = tt(d); f = 330 + 240 * np.sin(np.pi * t / d) - 120 * t / d; return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) * .5
def slide(f0, f1, d=.5):
    t = tt(d); return np.sin(2 * np.pi * np.cumsum(f0 + (f1 - f0) * t / d) / SR) * env(len(t), .01, .08)
def rumble(d):
    t = tt(d); return (filt(rng.standard_normal(len(t)), None, 120) * 3 + np.sin(2 * np.pi * 41 * t) * .8) * env(len(t), d * .3, d * .3)
def mbox(f, d=1.6):
    t = tt(d); return (np.sin(2 * np.pi * f * t) * np.exp(-t * 3.2) + .4 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 9) + .2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 16)) * env(len(t), .002, .05)

def playful(t0, t1, gain=1.0, bar=1.6, prog=('C', 'F', 'G', 'C', 'Am', 'F', 'G', 'G')):
    t = t0; k = 0
    while t < t1 - .1:
        r, th, fi = CH[prog[k % len(prog)]]; pat = [r, fi, th + 12, fi, r + 12, fi, th + 12, fi]; s = bar / 8
        for j, n in enumerate(pat):
            if t + j * s < t1 - .04:
                put(music, marimba(note(n + 12)), t + j * s, (.36 if j % 2 == 0 else .25) * gain)
                if j % 2 == 1: put(music, tick(j % 4 == 1), t + j * s, .12 * gain)
                if j % 4 == 0: put(music, thud(), t + j * s, .16 * gain)
        put(music, bassn(note(r - 12), .7), t, .5 * gain); put(music, bassn(note(fi - 12), .4), t + bar / 2, .36 * gain)
        t += bar; k += 1
def drone(t0, t1, g=.22, f=55):
    td = tt(t1 - t0); x = (np.sin(2 * np.pi * f * td) + .5 * np.sin(2 * np.pi * f * 1.5 * td + np.sin(td * .7) * 2) + .25 * np.sin(2 * np.pi * f * 2.01 * td)) * env(len(td), min(.8, (t1 - t0) * .3), .25)
    put(music, x, t0, g)

# ---------------- hook: hum of a hundred lamps -> CLICK -> silence -> the town screams -> glass
tc = E['click']
put(sfx, hum(tc), 0, .55); put(music, marimba(note(72)) + marimba(note(76)) * .7, .05, .4); put(music, marimba(note(79)), .30, .4); put(music, marimba(note(84)), .55, .4)
put(dry, click(), tc - .01, 1.4); put(sfx, slide(700, 90, .5), tc + .02, .35)
put(dry, pop(), st['A2'] + .12, .5); put(dry, marimba(note(96), .4), st['A2'] + .12, .4)        # the "!"
put(sfx, scream(st['B'] - st['A3'] - .1), st['A3'], .95)
put(sfx, whoosh(.5, 400, 5000), E['hit'] - .5, .7); put(dry, glass(), E['hit'], 1.0); put(sfx, glass(), E['hit'], .5)
# ---------------- the rule + gags
playful(st['B'], st['F'] - .05)
put(sfx, hum(st['C'] - st['B'], 100), st['B'], .22)
for n in ('C', 'D', 'E_'): put(dry, pop(), st[n] + .02, .55); put(sfx, whoosh(.24, 600, 5000), st[n] - .14, .22)
put(dry, bonk(), st['D'] + du['D'] * .5, .0)
put(dry, marimba(note(91), .5) + marimba(note(96), .5) * .7, st['E_'] + du['E_'] * .55, .35)
# ---------------- the legend
drone(st['F'], st['G'] - .05, .30); put(sfx, buzz(E['f_out'] - st['F']), st['F'], .42)
put(sfx, whoosh(.9, 150, 1500), E['f_out'] - .8, .6); put(dry, zap(), E['f_out'], .7); put(sfx, impact()[:int(1.2 * SR)] * env(int(1.2 * SR), .005, .5), E['f_out'], .5)
put(dry, slide(900, 200, .35), E['f_out'] + .05, .3)
# ---------------- moving in, school, tired
playful(st['G'], st['I'] - .05, .9, prog=('F', 'C', 'G', 'C'))
put(dry, thud(), st['G'] + .1, .5)
bell = sum(np.sin(2 * np.pi * f * tt(.7)) * np.exp(-tt(.7) * 5) * (1 + .5 * np.sin(2 * np.pi * 22 * tt(.7))) for f in (1568, 2093, 3136)); put(sfx, bell, st['Hs'], .16)
put(sfx, cheer(du['Hs']) * .0 + noisebed(du['Hs'], 500, 2000, 3), st['Hs'], .12)
tI = st['I']
for i, n in enumerate((60, 57, 53, 50)): put(music, piano(note(n), 1.6, .7), tI + i * du['I'] / 4.4, .4); put(music, bassn(note(n - 12), .9), tI + i * du['I'] / 4.4, .35)
for i in range(3): put(dry, yawn(), tI + .15 + i * du['I'] / 3.4, .45)
# ---------------- Pete
drone(st['J'], st['L_'] - .05, .30, 49)
put(sfx, hum(E['j_pop'] - st['J'], 110), st['J'], .25); put(sfx, buzz(.75), E['j_pop'] - .75, .45)
put(dry, zap(), E['j_pop'], .9); put(dry, pop(), E['j_pop'], .8); put(sfx, glass()[:int(.5 * SR)], E['j_pop'], .3)
put(sfx, whoosh(du['K'] * .9, 100, 900), st['K'], .8); put(sfx, rumble(du['K']), st['K'], .3); put(sfx, slide(160, 60, .5), st['K'] + du['K'] * .8, .5)
for i, n in enumerate((57, 52)): put(music, piano(note(n), 2.0, .7), st['L_'] + .1 + i * .8, .45)
# ---------------- the mayor
tm = st['M']; k = 0
while tm < E['m_close'] - .1:
    put(music, thud(), tm, .7); put(music, bassn(note(33), .5), tm, .6)
    if k % 2: put(music, thud(), tm + .21, .45)
    tm += .42; k += 1
put(sfx, noisebed(du['M'], 300, 1500, 2), st['M'], .14); put(dry, pop(), st['M'] + .05, .4)
put(sfx, impact(), E['m_close'] - .02, .8)
# ---------------- alone: lamps die one by one, then the eyes
drone(st['N'], st['O'], .22, 46)
nl = 6
for i in range(nl):
    tt_ = E['n_off0'] + (E['n_dark'] - E['n_off0']) * (i + 1) / nl
    put(dry, clunk(150 - i * 14), tt_ - .02, .6 + .08 * i); put(sfx, clunk(150 - i * 14), tt_ - .02, .4)
put(sfx, rumble(du['O'] + .4), st['O'] - .1, .7); put(sfx, impact(), st['O'] + .25, .7); put(dry, slide(180, 520, .5), st['O'] + .2, .25)
t = E['n_dark'] + .15; hb_end = st['Q'] - .2
while t < hb_end:
    p = (t - E['n_dark']) / (hb_end - E['n_dark']); put(dry, heart(), t, .5 + .5 * p); t += .72 - .36 * p
drone(st['P_'], st['Q'] - .2, .30, 41); put(sfx, whoosh(du['P_'] * .8, 100, 1200), st['P_'] + .1, .7)
td = tt(du['P_'] - .4); put(sfx, np.sin(2 * np.pi * np.cumsum(200 + 500 * (td / td[-1]) ** 2) / SR) * (td / td[-1]) ** 2 * env(len(td), .01, .02), st['P_'], .22)
# ---------------- the lullaby (music box) from the tuck to the end of the lights going out
tq = st['Q'] + .12; put(dry, slide(500, 900, .25), st['Q'] + .25, .22)
mel = [76, 76, 79, None, 76, 76, 79, None, 76, 79, 84, 83, 81, 81, 79, None, 74, 76, 77, 74, 74, 76, 77, None, 74, 77, 83, 81, 79, 83, 84, None]
step = .30; i = 0; t = tq; tl_end = st['U'] - .25
chords = ['C', 'C', 'G', 'G', 'G', 'G', 'C', 'C']
while t < tl_end:
    n = mel[i % len(mel)]
    if n: put(music, mbox(note(n)), t, .42)
    if i % 4 == 0:
        r, th, fi = CH[chords[(i // 4) % 8]]; put(music, mbox(note(r + 12), 2.2), t, .22); put(music, pad([note(r), note(fi), note(th + 12)], step * 4 + .8), t, .30)
    t += step; i += 1
put(dry, marimba(note(88), .8) + marimba(note(95), .8) * .6, st['R'] + .1, .35)
for i in range(3): put(dry, yawn(), st['S_'] + .05 + i * .5, .4); put(dry, thud(), st['S_'] + .25 + i * .5 + .42, .5)
nT = 9
for i in range(nT): put(dry, click(), st['T_'] + .3 + (du['T_'] - 1.0) * i / (nT - 1), .5); put(sfx, clunk(120 - 6 * i), st['T_'] + .3 + (du['T_'] - 1.0) * i / (nT - 1), .18)
# ---------------- the mayor's secret
put(sfx, scratch(), st['U'] - .22, .6)
tu = st['U'] + .1; sneak = [48, 51, 54, 51, 48, 51, 54, 57]
for i, n in enumerate(sneak):
    if tu + i * .2 < E['u_rev'] - .05: put(music, bassn(note(n), .3) + marimba(note(n + 12), .3) * .5, tu + i * .2, .5)
for n, g in ((60, .5), (64, .45), (67, .45), (72, .5)): put(music, piano(note(n), 1.6, 1.2) + marimba(note(n + 12), 1.6) * .6, E['u_rev'], g * .6)
put(dry, thud(), E['u_rev'], .7); put(sfx, whoosh(.3, 500, 5000), E['u_rev'] - .25, .4)
playful(E['u_rev'] + .45, E['v_sleep'] - .05, .75, prog=('C', 'G', 'F', 'G'))
put(sfx, whoosh(.9, 120, 1500), st['V_'] + .1, .7); put(dry, bonk(), E['v_tuck'], .6); put(dry, pop(), E['v_tuck'], .6)
put(dry, slide(700, 200, .3), E['v_sleep'], .3); put(dry, thud(), E['v_sleep'] + .28, .8)
put(dry, snore(), E['v_sleep'] + .32, .9)
tEnd = E['end']; put(sfx, buzz(.4), tEnd - .45, .3); put(dry, click(), tEnd - .02, 1.5)

# ---------------- reverb + mix
ir_t = tt(1.6); ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 4.2); ir = filt(ir, 200, 6000); ir /= np.sqrt((ir ** 2).sum())
def rev(x, wet): return x + fftconvolve(x, ir)[:len(x)] * wet
music = rev(music, .2); sfx = rev(sfx, .28)
cutn = int((tEnd + .05) * SR); music[cutn:] = 0; sfx[cutn:] = 0; dry[cutn + int(.1 * SR):] = 0
w = wave.open("build/s2/vo.wav"); vo = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768; w.close()
vo = filt(vo, 70); v = np.zeros(N); v[:min(N, len(vo))] = vo[:N]
e = np.sqrt(np.maximum(1e-9, lfilter([1 - .999], [1, -.999], v * v))); g = np.minimum(1.0, (0.16 / np.maximum(e, 1e-4)) ** .4); v = v * g; v /= np.abs(v).max() / .92
ve = np.sqrt(lfilter([1 - .9995], [1, -.9995], v * v)); duck = 1 - .45 * np.clip(ve / .08, 0, 1)
def arms(x, m=None):
    m = np.abs(x) > 1e-4 if m is None else m
    return np.sqrt((x[m] ** 2).mean()) if m.any() else 0
vr = arms(v, ve > .03)
mus = music * duck; mus *= (.24 * vr) / arms(mus)
fx = (sfx * .55 + dry * .5) * (1 - .25 * np.clip(ve / .08, 0, 1)); pk = np.abs(fx).max(); fx *= min(1.0, .8 / pk)
mix = np.tanh((v + mus + fx) * 1.1) * .97
print("voice rms %.3f music rms %.3f fx rms %.3f fx peak %.2f" % (vr, arms(mus), arms(fx), np.abs(fx).max()))
mix = mix[:int(DUR * SR)]
w = wave.open("build/s2/mix.wav", "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([mix, mix], 1) * 32767).astype(np.int16).tobytes()); w.close()
print("mix ok", len(mix) / SR, "peak", np.abs(mix).max())
