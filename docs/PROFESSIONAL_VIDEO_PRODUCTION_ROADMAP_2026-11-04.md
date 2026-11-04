# Automate-ytb — Professional Video Production Roadmap (2026-11-04)

## Product objective

Produce distinctive **original** English/French 9:16 science videos, with cinematic
motion, clear science communication, natural narration and reliable, reproducible
CPU-first rendering. Never confuse a successful encode with a professional-quality
production. The creator approves all final videos and rights.

## Baseline actually inspected

- Working 1080×1920 H.264 / AAC high-quality export at 30 fps, EBU R128 and
  true-peak measurements, subtitles synchronized to synthesized phrase boundaries.
- Kokoro speakers, expressive speed profile and optional comparative voice samples.
- Science illustration rigs (ocean, aurora, volcano, lightning, rainbow, Earth).
- Optional real Blender Cycles 3D ocean scenes: ten rendered keyframes per beat,
  interpolated to 30 fps; other science domains are still predominantly 2D.
- Technical QA samples two frames per scene and checks motion, banded portrait
  composition, near-black frames, duplicates, hash-bound contact sheets.
- Human listening and editorial quality are NOT certified by these checks.

## Delivery sequence (finish each gate before the next)

| Stage | Priority | Engineering deliverable | Acceptance |
| --- | --- | --- | --- |
| 1. Evidence-based production review | P0 | Actionable `professional-review.json` generated from **real encoded** QA; voice, motion, composition, lighting and sound ranked | CI runs on a complete actual MP4; defects are traceable; no made-up premium score |
| 2. Cinematic asset language | P0 | Reusable Blender procedural scene kits for aurora, volcano, Earth, lighting; distinct foreground/midground/background, surface roughness and color management | At least 5 visibly different shots per topic, native vertical safe areas, comparison against 2D baseline |
| 3. True animation continuity | P0 | Increase true 3D temporal samples or render with optical flow/motion vectors; avoid ghosting from crossfading 10 Blender frames | Scrub full MP4 at 30fps, no double edges, motion is causal rather than arbitrary camera shaking |
| 4. Voice direction | P0 | Speaker audition and authored phrase pacing; pronunciation dictionary, consistent breath and emphasis, no synthetic truncation | Human blind listening comparison; measured PCM duration/padding and EBU R128; intelligible with phone speakers |
| 5. Sound & mix | P1 | Scene-specific licensed/original ambience and meaningful effects, adaptive ducking, true-peak limiting | No masking of speech, true peak <= -1 dBTP, stable integrated loudness near target |
| 6. Editorial montage | P1 | Hook, five distinct causal scenes, intentional transitions, animated explanatory typography and end payoff | Human review for clarity, novelty and mobile legibility; subtitles follow real audio |
| 7. Mobile one-click release gate | P1 | Android-friendly GitHub Actions input; automatically generated MP4, scorecard, contact sheet, source/licensing report | Reproducible successful workflow on main, artifact retrievable and manually approved |

## Stage 1 implemented in this branch

- `automate_ytb/professional_review.py` reads already verified
  `qa-summary.json`, `visual-review.json`, `media-report.json`, and optional
  `narration-pacing.json` after video encoding and QA.
- Creates a prioritised list of specific issues (P0/P1) and their evidence,
  plus motion/luminance/loudness measurements. Adds **no** expensive decode,
  model inference, paid API, or ungrounded 10/10 visual quality claim.
- A technically successful preview still needs editorial review.
- New report is included in the existing one-click GitHub Actions artifact.
- Unit-level regression coverage for malformed evidence, audio defects,
  low motion, duplicated visuals and approval invariants.

## Performance and constraints

- Keep the 2D science renderer as the stable fallback. New Blender domains are
  opt-in until visual comparison and full runner QA pass.
- Prefer procedural original assets, Blender, Pillow, FFmpeg and Kokoro, without
  API keys, per-video credits or external licensed media.
- Render times and hosted runner quotas are measured, not assumed free/unlimited.
- Any scientific diagrams are illustrative, not claimed to be CFD/photogrammetry.
- No automatic upload to YouTube and no fabricated fact-check or rights clearance.

## Current release gates

1. `python -m unittest discover -s tests` on the PR head.
2. Run at least one complete English Kokoro science workflow on the same head,
   verifying real MP4, actual 30fps audio/video, subtitle and visual QA.
3. Inspect `professional-review.json`, review contact sheets, listen to MP4.
4. Only then merge; do not activate a new rendering mode by default merely
   because its code passes tests.
