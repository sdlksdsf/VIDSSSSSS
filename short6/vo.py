"""Short 6 (remake) narration: forced-align each clip, padded edges, set pace -> build/s6b/vo.wav + timeline.json"""
import wave, json, subprocess, numpy as np, imageio_ffmpeg, os, re
FF = imageio_ffmpeg.get_ffmpeg_exe(); SR = 44100; TEMPO = float(os.environ.get("TEMPO", 1.0)); MAXGAP = .26; CLIPGAP = .30
# clip, speaker, sentences (caption text). "_" joins spoken words into one caption word.
S = [
 ("c1", "R", ["In this town, when you forget someone's name, their face goes blurry.", "And they can't hear you until you say it again.", "Last week, Jake forgot the baker's name.", "Now he buys bread from a smudge."]),
 ("c2", "R", ["Me? I never forget a name.", "I remember everyone at school.", "Everyone, except my best friend.", "Eight years I've called him _buddy_."]),
 ("c3", "R", ["I never said his real name out loud.", "So when I looked at him, I just saw a blur.", "Then the school roof caved in."]),
 ("c4", "R", ["The fire chief said they couldn't dig, too much rubble.", "But I knew he was under there.", "And a blur can't hear you.", "Buddy! Dude! Best friend! Nothing."]),
 ("c5", "G", ["You forgot your best friend's name? That's brutal."]),
 ("c6", "R", ["I didn't care.", "I climbed onto the rubble, and then I remembered the first day we met."]),
 ("c7", "D", ["I'm Dex. What's yours?"]),
 ("c8", "R", ["Dex! I screamed.", "His face snapped back, clear as day.", "He looked up through the dust, grinned, and said,"]),
 ("c9", "D", ["I knew you'd remember."]),
 ("c10", "R", ["Now I've said his name a thousand times.", "He's hiding from me.", "His face is fine. Mine isn't."]),
]
SHOW = {}
def rd(f):
    w = wave.open(f); return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
def align(c, words):
    try:
        from pocketsphinx import Decoder
        d = Decoder(samprate=16000, logfn='/dev/null'); d.set_align_text(' '.join({'hemispheres': 'hemisphere', 'kiribas': 'kiribati'}.get(w, w) for w in words)); d.start_utt(); d.process_raw(open(f'build/s6b/_{c}.raw', 'rb').read(), full_utt=True); d.end_utt()
        r = [(s.start_frame / 100, (s.end_frame + 1) / 100) for s in d.seg() if s.word not in ('<sil>', '(NULL)', '<s>', '</s>')]
        if len(r) == len(words): return r
    except Exception as e: print("align fallback", c, e)
    return None
def main():
    out = [np.zeros(int(.10 * SR))]; t = .10; lines = []
    for c, spk, sents in S:
        a = rd(f'build/s6b/_{c}.wav'); a = a / np.abs(a).max()
        caps = [w for s in sents for w in s.split()]; spoken = []
        for w in caps:
            for p in w.split('_'): spoken += [x for x in re.sub(r"[^a-z' -]", '', p.lower().replace('?', '')).replace('-', ' ').split() if x]
        al = align(c, spoken)
        win = int(SR * .02); en = np.sqrt(np.convolve(a * a, np.ones(win) / win, 'same')); idx = np.flatnonzero(en > en.max() * .04)
        s0, s1 = max(0, idx[0] / SR - .08), min(len(a) / SR, idx[-1] / SR + .10)   # padded so no word is clipped
        if al is None:      # proportional word times between detected speech start and end
            wts = np.cumsum([0] + [len(w) + 1.5 for w in spoken]); al = [(s0 + (s1 - s0) * wts[i] / wts[-1], s0 + (s1 - s0) * wts[i + 1] / wts[-1]) for i in range(len(spoken))]
            segs = [(s0, s1)]
        else:
            segs = []; cur = [max(0, al[0][0] - .05), al[0][1]]
            for (b, e) in al[1:]:
                if b - cur[1] > MAXGAP: segs.append((cur[0], cur[1] + .06)); cur = [b - .05, e]
                else: cur[1] = e
            segs.append((cur[0], min(len(a) / SR, cur[1] + .14)))
        # build audio + time map
        tm = []; local = 0.0; buf = []
        for i, (b, e) in enumerate(segs):
            x = a[int(b * SR):int(e * SR)].copy(); f = int(.006 * SR); x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
            tm.append((b, e, local)); buf.append(x); local += len(x) / SR
            if i < len(segs) - 1: g = int(MAXGAP * .8 * SR); buf.append(np.zeros(g)); local += g / SR
        def mp(x):
            for b, e, l in tm:
                if x <= e: return l + max(0, x - b)
            return local
        j = 0
        for s in sents:
            ws = []
            for cw in s.split():
                n = len([x for p in cw.split('_') for x in re.sub(r"[^a-z' -]", '', p.lower().replace('?', '')).replace('-', ' ').split() if x])
                key = cw.replace('_', ''); ws.append({"w": SHOW.get(key, SHOW.get(key.rstrip('.,'), key)), "t0": (t + mp(al[j][0])) / TEMPO, "t1": (t + mp(al[j + n - 1][1])) / TEMPO}); j += n
            lines.append({"spk": spk, "text": s.replace('_', ''), "t0": ws[0]["t0"], "t1": ws[-1]["t1"], "words": ws})
        out += buf + [np.zeros(int(CLIPGAP * SR))]; t += local + CLIPGAP
    y = np.concatenate(out + [np.zeros(SR)]); y = y / np.abs(y).max() * .9
    w = wave.open("build/s6b/vo_raw.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((y * 32767).astype(np.int16).tobytes()); w.close()
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", "build/s6b/vo_raw.wav", "-af", f"atempo={TEMPO:.4f}", "-ar", str(SR), "build/s6b/vo.wav"], check=True)
    json.dump({"lines": lines}, open("build/s6b/timeline.json", "w"), indent=1)
    for i, l in enumerate(lines): print("%2d %s %6.2f %6.2f  %s" % (i, l["spk"], l["t0"], l["t1"], ' '.join(w['w'] for w in l['words'])))
    print("duration", round(lines[-1]["t1"] + .8, 2))
main()
