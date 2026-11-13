"""Assemble the narration: trim pauses, set pacing, and write timeline.json
with start/end times for every phrase and word (used for sync and captions)."""
import wave, json, subprocess, numpy as np, imageio_ffmpeg, os
FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 44100
# (clip, phrases, extra pause AFTER each phrase in seconds [final-speed])
CLIPS = [
 ("01", ["Ever since Eli was a kid,", "he could stop time."]),
 ("02", ["One snap of his fingers,", "and the whole world froze.", "Birds hung in the air.", "Raindrops stopped falling.", "Even his mom froze mid-sentence."]),
 ("03", ["At first,", "he thought it was the best power in the world.", "He finished every test.", "He dodged every dodgeball.", "He always got the last slice of pizza."]),
 ("04", ["As he got older,", "he used it for everything.", "An extra hour of sleep.", "An extra day to study.", "Sometimes", "he stayed in the frozen world for weeks,", "just because it was quiet."]),
 ("05", ["Then one morning,", "at his graduation,", "his best friend walked up to him", "and stopped smiling.", "He just stared."]),
 ("06", ["Eli...", "what happened to you?"]),
 ("07", ["Eli laughed it off.", "But his hands were shaking.", "His stomach dropped."]),
 ("08", ["He ran inside and looked in the mirror.", "And he froze."]),
 ("09", ["Gray hair.", "Tired eyes.", "A face he didn't recognize."]),
 ("10", ["Every time he snapped,", "the world stopped.", "But he never did.", "Eli hadn't been stopping time.", "He'd been spending his."]),
]
GAP = 0.20          # default pause between phrases
CLIPGAP = 0.30      # default pause between clips
EXTRA = {  # phrase text -> pause after it (overrides)
 "he could stop time.": 0.40, "Sometimes": 0.12, "At first,": 0.12,
 "just because it was quiet.": 0.75, "He just stared.": 0.55, "Eli...": 0.35,
 "what happened to you?": 0.60, "His stomach dropped.": 0.45,
 "He ran inside and looked in the mirror.": 0.50, "And he froze.": 0.80,
 "Gray hair.": 0.32, "Tired eyes.": 0.32, "A face he didn't recognize.": 0.60,
 "But he never did.": 0.70, "Eli hadn't been stopping time.": 0.45,
}
START = 0.20
TARGET = float(os.environ.get("TARGET", 59.0))

def load(f):
    w = wave.open(f); n = w.getnframes()
    a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64) / 32768
    assert w.getframerate() == SR and w.getnchannels() == 1
    return a

def speech_segments(a, minsil=0.18):
    win = int(SR * 0.02)
    e = np.sqrt(np.convolve(a * a, np.ones(win) / win, 'same')); th = e.max() * 0.03
    loud = e >= th; segs = []; i = 0; n = len(a)
    while i < n:
        if loud[i]:
            j = i
            while j < n:
                if not loud[j]:
                    k = j
                    while k < n and not loud[k]: k += 1
                    if (k - j) / SR > minsil or k >= n: break
                    j = k
                else: j += 1
            segs.append((i, j)); i = j
        else: i += 1
    return segs

def main():
    pieces = []; speech = 0; gaps = START
    for ci, (c, phrases) in enumerate(CLIPS):
        a = load(f"audio/vo/{c}.wav"); segs = speech_segments(a)
        assert len(segs) == len(phrases), (c, len(segs), len(phrases))
        for pi, ((s, e), ph) in enumerate(zip(segs, phrases)):
            pad = int(0.03 * SR); s = max(0, s - pad); e = min(len(a), e + pad)
            x = a[s:e].copy(); f = int(0.012 * SR)
            x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
            last = pi == len(phrases) - 1
            g = EXTRA.get(ph, CLIPGAP if last else GAP)
            if ci == len(CLIPS) - 1 and last: g = 0
            pieces.append([c, ph, x, g]); speech += len(x) / SR; gaps += g
    tempo = max(1.0, min(1.12, speech / (TARGET - gaps - 0.9)))
    print("speech %.2f gaps %.2f tempo %.3f" % (speech, gaps, tempo))
    out = [np.zeros(int(START * tempo * SR))]; t = START * tempo; tl = []
    for c, ph, x, g in pieces:
        t0 = t; out.append(x); t += len(x) / SR
        out.append(np.zeros(int(g * tempo * SR))); t1 = t; t += int(g * tempo * SR) / SR
        words = ph.split(); wts = [len(w) + 1.5 for w in words]; tot = sum(wts); acc = 0; ws = []
        for w, wt in zip(words, wts):
            ws.append({"w": w, "t0": (t0 + (t1 - t0) * acc / tot) / tempo, "t1": (t0 + (t1 - t0) * (acc + wt) / tot) / tempo}); acc += wt
        tl.append({"clip": c, "text": ph, "t0": t0 / tempo, "t1": t1 / tempo, "words": ws})
    y = np.concatenate(out); y = y / np.abs(y).max() * 0.9
    os.makedirs("build", exist_ok=True)
    w = wave.open("build/vo_raw.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((y * 32767).astype(np.int16).tobytes()); w.close()
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", "build/vo_raw.wav", "-af", f"atempo={tempo:.4f}", "-ar", str(SR), "build/vo.wav"], check=True)
    end = tl[-1]["t1"]; dur = end + 0.9
    json.dump({"tempo": tempo, "duration": dur, "phrases": tl}, open("build/timeline.json", "w"), indent=1)
    for p in tl: print("%6.2f %6.2f  %s" % (p["t0"], p["t1"], p["text"]))
    print("duration", round(dur, 2))
main()
