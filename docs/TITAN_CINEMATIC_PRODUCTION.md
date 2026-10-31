# Titan documentary — cinematic production workflow

This workflow builds a ~33-second vertical science short in **English**, using licensed/public-domain NASA scientific visualizations and Kokoro-82M narration. Its production target is **1080 × 1920 / 30 fps / H.264 / AAC**.

## Why this production route

The original procedural scenery and eSpeak voice were not suitable for social distribution. The revised pipeline uses **animated 4K NASA source footage** instead of synthetic still cards, and **Kokoro neural speech** rather than robotic TTS. It does not infer these animations are recorded Titan surface footage. No paid generation credits are used.

## Architecture and exact build

1. `production/titan/render_short.py` downloads authorized NASA SVS 20403 videos, creates Kokoro English narration and timestamps, selects six shots and exports the factual base video.
2. `production/titan/word_align.py` checks the English script against the actual Kokoro WAV using CPU Faster-Whisper and stores acoustic word timings with match/interpolation provenance; `production/titan/finish_short.py` burns short, word-highlighted English subtitles into the MP4 via ASS/libass; shows four scene-relevant overlays (Titan identity, lake composition, methane cycle, temperature); builds a subtle original atmospheric track; applies limited image sharpening; exports `Titan_Documentary_Enhanced_EN.mp4`.
3. Both stages use `ffmpeg -f null` to verify full decode of the video. The enhanced stage produces separate subtitle and QA files.
4. GitHub Actions `.github/workflows/titan-documentary.yml` runs the alignment and finishing stages and uploads the finished MP4, SRT, voice WAV, word timing audit, and supporting assets as `titan-nasa-kokoro-english` for 14 days.

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

- Subtitle timing is now **measured from the voice waveform**, with a verified recognition fraction in `enhanced/word_timestamps.json`. Unrecognized words are visibly marked as interpolated in the report. The build fails on poor matching; this is NOT guaranteed perfect phoneme alignment.
- The field of view from 16:9 NASA animations is cropped for a vertical phone. Review framing of small moons, rings and molecular models on the actual output.
- A coherent visual story and aesthetically pleasing natural voice remain editorial judgements; passing the automated technical QA alone does not prove them.
- Automated posting is not enabled; YouTube/TikTok/Instagram upload and license review must be completed independently.

## Next improvements, in order

1. Inspect the acoustic word-alignment QA and manually audition scientific names before publication. Enhance with a CTC phoneme forced aligner only if the verified Whisper result warrants it.
2. A shot-by-shot inspector to choose crop focal points rather than fixed center framing; maintain 3D continuity and avoid black, empty frames.
3. Replace minimal atmospheric sound design with a professionally mastered original score when the proper licensed assets are available.
4. Add only evidence-backed visualization layers (methane rain, freeze temperature or rings), not decorative HUD elements.

## Documentary shot direction — October 31 revision

The renderer defines `SHOT_PLAN`: six factual narration scenes are now edited into **12 separate shots**. This is an edit of moving NASA animation frames, not a slideshow or crop of still images. The cut fractions remain inside each sentence and cover its complete spoken duration. Source offsets avoid long periods of empty sky, and all source shots use FFmpeg at 1080×1920 / 30 fps.

The first run of this plan exposed two pale-blue sky shots unsuitable for the described orange Titan atmosphere. Those source selections were explicitly corrected before delivery. Editorial QA should still reject misleading color/planet depictions and verify NASA sources are visualizations, not surface photography.

The subtitle compositor now **starts new groups at scene boundaries** and terminates groups at sentence punctuation so captions cannot show words from the next spoken scene. Mobile readability uses a larger outlined sans-serif face with a bottom safety margin, while the acoustic aligner still distinguishes directly recognized words from interpolated numerical expressions.

This upgrade intentionally does **not** claim photorealism or a cinematic-grade human narrator. The next major quality task should be to curate more diverse professionally animated source material with verified physics and stronger storytelling, rather than apply more filters.

## Climate-model upgrade and source attribution

The updated movie adds a separate NASA Scientific Visualization Studio **Titan Atmospheric Model** animation from [SVS 5530](https://svs.gsfc.nasa.gov/5530/) showing methane cloud circulation. The existing lakes, rainfall and chemistry sequences remain NASA [SVS 20403](https://svs.gsfc.nasa.gov/20403/).

The documentary script now follows a short clear chain: unfamiliar shoreline → Saturn/Titan → frozen hydrocarbon seas → methane cloud circulation → methane rain → alien chemistry. All animations are **simulations / artist visualizations**, not historical video of Titan's surface.

Voice performance uses small scene-specific pace changes via `VOICE_SPEEDS`, with Kokoro `af_heart`; no paid speech API is required. The subtitle timing is still validated against actual WAV audio with word-level flags. The scientific callouts are aligned to the revised scene indexes and ambient rain is attached to the rain segment only.

The first exported new cut revealed two blue-hued landscape angles inconsistent with the surrounding orange atmospheric shots. Those angles were removed from `SHOT_PLAN` in a subsequent build. This is an editorial correction, not a claim that Titan’s real light or colors can be reproduced exactly from these animations.

**Release gate:** require success of source download, narrator render, acoustic caption QA, AAC 48kHz, FFmpeg full decode, and a manual contact-sheet inspection for color continuity. Do not publish merely because the CI workflow exits successfully.
