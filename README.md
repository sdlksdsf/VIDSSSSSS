# VIDSSSSSS

Roblox-style animated Short, built from an analysis of five reference videos.

- `docs/01-analysis.md` — what the reference Shorts do and why it works
- `docs/02-script.md` — our original script and shot list (awaiting approval)

## Final video

`render/the-kid-who-could-stop-time.mp4` — 59.0 s, 1080x1920, 24 fps, narration + synthesised music and sound effects.

Rebuild (Python 3.11, `pip install numpy pillow scipy imageio-ffmpeg`):

```
python src/vo.py                         # assemble narration -> build/vo.wav, build/timeline.json
python src/audio.py                      # music + SFX + mix -> build/mix.wav
python src/film.py render 0 1 frames     # render all frames
ffmpeg -framerate 24 -i frames/%05d.jpg -i build/mix.wav -c:v libx264 -crf 19 -pix_fmt yuv420p -c:a aac -shortest render/the-kid-who-could-stop-time.mp4
```

## Short 2: In This Town Nobody Turns Off the Lights

- Video: `render/nobody-turns-off-the-lights.mp4`
- Analysis of the 7 reference Shorts: `docs/04-analysis-round2.md`; script: `docs/05-script-2.md`
- Code: `short2/` (`vo.py` timing, `world.py` lighting, props and sets, `film.py` shots, `audio.py` soundtrack); voice clips in `audio/vo2/`

Rebuild:

```
python short2/vo.py
python short2/audio.py
python short2/film.py render 0 1 /tmp/f2
ffmpeg -framerate 24 -i /tmp/f2/%05d.jpg -i build/s2/mix.wav -c:v libx264 -crf 19 -pix_fmt yuv420p -c:a aac -shortest render/nobody-turns-off-the-lights.mp4
```
