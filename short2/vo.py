"""Assemble the narration: trim pauses, set pacing, and write timeline.json
with start/end times for every phrase and word (used for sync and captions)."""
import wave, json, subprocess, numpy as np, imageio_ffmpeg, os
FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 44100
# (clip, phrases, extra pause AFTER each phrase in seconds [final-speed])
CLIPS = [
 ("01", ["I turned off my bedroom light,", "and the whole town screamed."]),
 ("02", ["Because here,", "nobody has turned off a light in a hundred years.", "Kids sleep in sunglasses.", "Dogs wear flashlights.", "Even the fridge has a night-light."]),
 ("03", ["They say the Dark is alive.", "And whoever it touches,", "disappears."]),
 ("04", ["We'd moved in that morning.", "Nobody told me the rule.", "At school,", "they called me Lights Out.", "But something felt off.", "Everyone here looked so tired."]),
 ("05", ["On Thursday,", "Old Pete's bulb burned out.", "A black shape slid under his door.", "By morning,", "Pete was gone."]),
 ("06", ["You woke it up!", "Tonight,", "you sit in the dark.", "Alone."]),
 ("07", ["They left me in the square,", "and switched off the last lamp.", "Two huge eyes opened above me.", "A giant hand came down,"]),
 ("08", ["and tucked me in.", "The Dark didn't take people.", "It put them to bed.", "Nobody here had slept in a hundred years."]),
 ("09", ["So one by one,", "the lights went out.", "And the mayor?", "He owned the light bulb factory.", "So the Dark tucked him in first."]),
 ("10", ["But I'm not even tired!"]),
]
GAP = 0.13          # default pause between phrases
CLIPGAP = 0.20      # default pause between clips
EXTRA = {
 "I turned off my bedroom light,": 0.30, "and the whole town screamed.": 0.55, "Because here,": 0.08,
 "And whoever it touches,": 0.22, "disappears.": 0.35, "At school,": 0.06, "On Thursday,": 0.08, "By morning,": 0.10,
 "Pete was gone.": 0.35, "Tonight,": 0.08, "you sit in the dark.": 0.22, "Alone.": 0.40,
 "and switched off the last lamp.": 0.55, "Two huge eyes opened above me.": 0.25, "A giant hand came down,": 0.80,
 "and tucked me in.": 0.45, "It put them to bed.": 0.22, "Nobody here had slept in a hundred years.": 0.35,
 "the lights went out.": 0.40, "And the mayor?": 0.18, "He owned the light bulb factory.": 0.25, "So the Dark tucked him in first.": 0.30,
}
START = 0.50
TARGET = float(os.environ.get("TARGET", 59.0))

def load(f):
    w = wave.open(f); n = w.getnframes()
    a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float64) / 32768
    assert w.getframerate() == SR and w.getnchannels() == 1
    return a

def speech_segments(a, minsil=0.13):
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
        a = load(f"audio/vo2/{c}.wav"); segs = speech_segments(a)
        assert len(segs) == len(phrases), (c, len(segs), len(phrases))
        for pi, ((s, e), ph) in enumerate(zip(segs, phrases)):
            pad = int(0.03 * SR); s = max(0, s - pad); e = min(len(a), e + pad)
            x = a[s:e].copy(); f = int(0.012 * SR)
            x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
            last = pi == len(phrases) - 1
            g = EXTRA.get(ph, CLIPGAP if last else GAP)
            if ci == len(CLIPS) - 1 and last: g = 0
            pieces.append([c, ph, x, g]); speech += len(x) / SR; gaps += g
    tempo = float(os.environ.get("TEMPO", 1.14))
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
    os.makedirs("build/s2", exist_ok=True)
    w = wave.open("build/s2/vo_raw.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((y * 32767).astype(np.int16).tobytes()); w.close()
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", "build/s2/vo_raw.wav", "-af", f"atempo={tempo:.4f}", "-ar", str(SR), "build/s2/vo.wav"], check=True)
    end = tl[-1]["t1"]; dur = end + 1.5
    json.dump({"tempo": tempo, "duration": dur, "phrases": tl}, open("build/s2/timeline.json", "w"), indent=1)
    for p in tl: print("%6.2f %6.2f  %s" % (p["t0"], p["t1"], p["text"]))
    print("duration", round(dur, 2))
main()
