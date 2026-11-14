"""Short 3 dialogue assembler. Cuts each line out of the voice clips using the forced-alignment
word times in audio/vo3/align.json, sets per-speaker pace, writes build/s3/vo.wav + timeline.json."""
import wave, json, subprocess, numpy as np, imageio_ffmpeg, os
FF = imageio_ffmpeg.get_ffmpeg_exe(); SR = 44100
TEMPO = dict(R=float(os.environ.get("TR", 1.25)), K=1.15, M=1.10, C=1.08)
# speaker, clip, first word, last word, caption ("_" joins two spoken words into one caption word), pause after
L = [
 ("R", "r1", 0, 7, "I picked a wallet up off the sidewalk,", .10),
 ("R", "r1", 8, 15, "and some guy grabbed my arm and screamed,", .10),
 ("K", "k1", 0, 0, "THIEF!", .22),
 ("K", "k1", 1, 4, "He stole my wallet!", .30),
 ("R", "r1", 18, 23, "Sir, it was on the ground!", .16),
 ("K", "k1", 5, 11, "There was a thousand dollars in there!", .14),
 ("K", "k1", 12, 18, "Pay up, or I call the cops.", .22),
 ("R", "r2", 3, 5, "A thousand dollars?", .14),
 ("R", "r2", 6, 10, "Bro, there's a bus ticket", .06),
 ("R", "r2", 11, 16, "and a coupon for free fries.", .28),
 ("R", "r2", 17, 20, "A moth flew out.", .12),
 ("R", "r2", 21, 24, "Even he looked broke.", .45),
 ("K", "k1", 19, 23, "Because you already took it!", .16),
 ("R", "r3", 0, 2, "In four seconds?", .14),
 ("R", "r3", 8, 10, "I'm a kid,", .06),
 ("R", "r3", 11, 13, "not a magician.", .40),
 ("R", "r3", 19, 24, "And the second they showed up,", .08),
 ("R", "r3", 25, 27, "he started crying.", .18),
 ("K", "k2", 0, 4, "Officer, this kid robbed me!", .30),
 ("R", "r4", 0, 4, "That's when I noticed the", .0),
 ("R", "r4", 5, 5, "I", .0),
 ("R", "r4", 6, 6, "D", .0),
 ("R", "r4", 7, 7, "inside.", .26),
 ("R", "r4", 8, 8, "Sir.", .10),
 ("R", "r4", 9, 11, "What's your name?", .30),
 ("K", "k2", 5, 5, "Kevin.", .30),
 ("R", "r4", 12, 12, "Weird.", .16),
 ("R", "r4", 13, 18, "Because this wallet belongs to Margaret.", .16),
 ("R", "r4", 19, 22, "And she's seventy-_four.", .40),
 ("K", "k2", 6, 9, "That's an old photo.", .22),
 ("R", "r4", 23, 25, "You're wearing pearls.", .30),
 ("K", "k2", 10, 13, "It was a phase.", .30),
 ("M", "m1", 0, 2, "That's my wallet!", .10),
 ("M", "m1", 3, 9, "He snatched it at the bus stop!", .18),
 ("K", "k3", 0, 14, "I didn't run three blocks with that thing just to lose it to a kid!", .60),
 ("C", "c1", 0, 6, "You have the right to remain silent.", .30),
 ("C", "c1", 7, 9, "I'd start now.", .45),
 ("R", "r5", 0, 4, "Margaret gave me the coupon.", .14),
 ("R", "r5", 5, 9, "Best fries I ever had.", .30),
 ("K", "k3", 15, 19, "Can I get one fry?", .28),
 ("M", "m1", 10, 10, "No.", 0),
]
START = 0.12
def load(c):
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", f"audio/vo3/{c}.wav", "-ar", str(SR), "-ac", "1", f"build/s3/_{c}.wav"], check=True)
    w = wave.open(f"build/s3/_{c}.wav"); return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
def stretch(x, k, name):
    w = wave.open("build/s3/_p.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes()); w.close()
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", "build/s3/_p.wav", "-af", f"atempo={k:.4f}", "-ar", str(SR), "build/s3/_q.wav"], check=True)
    w = wave.open("build/s3/_q.wav"); return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
def main():
    os.makedirs("build/s3", exist_ok=True)
    A = json.load(open("audio/vo3/align.json")); raw = {}; out = [np.zeros(int(START * SR))]; t = START; tl = []
    for spk, c, i0, i1, text, gap in L:
        if c not in raw:
            a = load(c); raw[c] = a / np.abs(a).max()
        a = raw[c]; W = A[c]; n = len(a)
        s = W[i0][1] - .05; s = max(s, (W[i0 - 1][2] + W[i0][1]) / 2 if i0 else 0)
        e = W[i1][2] + .30; e = min(e, (W[i1 + 1][1] - .02) if i1 + 1 < len(W) else n / SR)
        s = max(0, int(s * SR)); e = min(n, int(e * SR)); x = a[s:e].copy()
        win = int(SR * .02); en = np.sqrt(np.convolve(x * x, np.ones(win) / win, 'same')); idx = np.flatnonzero(en > en.max() * .04)
        a0 = max(0, idx[0] - int(.02 * SR)); a1 = min(len(x), idx[-1] + int(.04 * SR)); x = x[a0:a1]; off = (s + a0) / SR
        f = int(.008 * SR); x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
        k = TEMPO[spk]; y = stretch(x, k, c); y = y / max(.2, np.abs(y).max()) * (.9 if spk != 'R' else .85)
        d = len(y) / SR; caps = text.split(); al = W[i0:i1 + 1]; ws = []; j = 0
        for cw in caps:
            m = cw.count('_') + 1; w0 = (al[j][1] - off) / k; w1 = (al[j + m - 1][2] - off) / k; j += m
            ws.append({"w": cw.replace('_', ''), "t0": t + clamp(w0, d), "t1": t + clamp(w1, d)})
        assert j == len(al), (text, j, len(al))
        ws[0]["t0"] = t; ws[-1]["t1"] = t + d
        tl.append({"spk": spk, "text": text.replace('_', ''), "t0": t, "t1": t + d, "words": ws})
        out.append(y); out.append(np.zeros(int(gap * SR))); t += d + int(gap * SR) / SR
    y = np.concatenate(out + [np.zeros(SR * 2)])
    w = wave.open("build/s3/vo.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    dur = tl[-1]["t1"] + 0.9
    json.dump({"duration": dur, "phrases": tl}, open("build/s3/timeline.json", "w"), indent=1)
    for i, p in enumerate(tl): print("%2d %s %6.2f %6.2f  %s" % (i, p["spk"], p["t0"], p["t1"], p["text"]))
    print("duration", round(dur, 2))
def clamp(v, d): return max(0.0, min(d, v))
main()
