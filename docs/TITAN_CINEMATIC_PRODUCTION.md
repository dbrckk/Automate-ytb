# Titan documentary — cinematic production workflow

This workflow builds a ~29-second vertical science short in **English**, using licensed/public-domain NASA scientific visualizations and Kokoro-82M narration. Its production target is **1080 × 1920 / 30 fps / H.264 / AAC**.

## Why this production route

The original procedural scenery and eSpeak voice were not suitable for social distribution. The revised pipeline uses **animated 4K NASA source footage** instead of synthetic still cards, and **Kokoro neural speech** rather than robotic TTS. It does not infer these animations are recorded Titan surface footage. No paid generation credits are used.

## Architecture and exact build

1. `production/titan/render_short.py` downloads authorized NASA SVS 20403 videos, creates Kokoro English narration and timestamps, selects six shots and exports the factual base video.
2. `production/titan/finish_short.py` burns short, sentence-synchronized English subtitles into the MP4 via ASS/libass; shows four scene-relevant overlays (Titan identity, lake composition, methane cycle, temperature); builds a subtle original atmospheric track; applies limited image sharpening; exports `Titan_Documentary_Enhanced_EN.mp4`.
3. Both stages use `ffmpeg -f null` to verify full decode of the video. The enhanced stage produces separate subtitle and QA files.
4. GitHub Actions `.github/workflows/titan-documentary.yml` runs both stages and uploads the finished MP4 and supporting assets as `titan-nasa-kokoro-english` for 14 days.

**Android:** [Actions → Produce Titan documentary](https://github.com/dbrckk/Automate-ytb/actions/workflows/titan-documentary.yml) → completed successful run → **Artifacts** → `titan-nasa-kokoro-english`.

Do **not** distribute the raw NASA/Kokoro base as the final short: use `enhanced/Titan_Documentary_Enhanced_EN.mp4` from the artifact.

## Presentation rules

- The spoken English narration is authoritative; graphics must support it rather than interrupt it.
- No slides, “01/08” labels, progress counters, intro cards, unrelated facts or watermarks.
- Subtitle zone stays above bottom-platform UI; subtitles use no more than a short clause at once, white sans-serif with outline, softly faded.
- Factual callouts appear only at the appropriate moment in the narration.
- Never stretch 16:9 science images. Use moving 4K sources and smart vertical framing.
- Keep full copyright and media attributions in the published description. Scientific visualizations are *illustrative*, not documentary camera footage.
- Verify actual pronunciation/listening manually before publishing, particularly place and chemical names.

## Limitations worth addressing before claiming premium quality

- Subtitle timing is **phrase-estimated** within the real Kokoro sentence boundaries, not forced word-level alignment. Do not describe it as word-perfect.
- The field of view from 16:9 NASA animations is cropped for a vertical phone. Review framing of small moons, rings and molecular models on the actual output.
- A coherent visual story and aesthetically pleasing natural voice remain editorial judgements; passing the automated technical QA alone does not prove them.
- Automated posting is not enabled; YouTube/TikTok/Instagram upload and license review must be completed independently.

## Next improvements, in order

1. Forced alignment of actual narration speech to subtitle timestamps; check with Whisper/phoneme alignment where available without paid APIs.
2. A shot-by-shot inspector to choose crop focal points rather than fixed center framing; maintain 3D continuity and avoid black, empty frames.
3. Replace minimal atmospheric sound design with a professionally mastered original score when the proper licensed assets are available.
4. Add only evidence-backed visualization layers (methane rain, freeze temperature or rings), not decorative HUD elements.
