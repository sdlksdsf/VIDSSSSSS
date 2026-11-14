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

## Short 3 - He Said I Stole His Wallet
```
python short3/vo.py        # dialogue -> build/s3/vo.wav + timeline.json
python short3/audio.py     # music + sfx mix -> build/s3/mix.wav
python short3/film.py render 0 1 /tmp/f3
ffmpeg -framerate 24 -i /tmp/f3/%05d.jpg -i build/s3/mix.wav -c:v libx264 -crf 19 -pix_fmt yuv420p -c:a aac -shortest render/he-said-i-stole-his-wallet.mp4
```

## Short 4 - Only One Country Is In All 4 Hemispheres (map animation)
```
python short4/vo.py && python short4/audio.py
python short4/film.py render 0 1 /tmp/f4
ffmpeg -framerate 24 -i /tmp/f4/%05d.jpg -i build/s4/mix.wav -c:v libx264 -crf 19 -pix_fmt yuv420p -c:a aac -shortest render/only-one-country-4-hemispheres.mp4
```
Map outlines: Natural Earth (public domain), `short4/data/`.

## Short 5 - How A Bruise Changes Colour (realistic 3D-style explainer)
```
python short5/vo.py && python short5/audio.py
python short5/film.py render 0 1 /tmp/f5
ffmpeg -framerate 24 -i /tmp/f5/%05d.jpg -i build/s5/mix.wav -c:v libx264 -crf 19 -pix_fmt yuv420p -c:a aac -shortest render/how-a-bruise-changes-colour.mp4
```
Shot images are AI-generated (`short5/img/`); the purple / green / yellow stages are derived from them in `short5/film.py`.
