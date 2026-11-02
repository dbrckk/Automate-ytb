# Original science cinematic V2: full-height composition

## What changed
* Lightning action view: 1080x1380 visible moving pixels within original
  1080x1920 portrait instead of the former 1080x930 central strip.
* Source artwork remains 1080x930 and renders once per video frame. The
  deterministic source-space camera makes a *uniform* magnification without
  distorting the geometry. Slow push/pull and horizontal tracking differ across
  the five narrative beats; a restrained impact-camera jolt accompanies return.
* The editorial title, chapter/progress indicator and subtitles are composited
  **after** the animated camera, maintaining fixed mobile-safe locations.
* Native 9:16 science dissolves mask the outgoing image to the scene-action
  field. The following shot's own on-video UI is never double-exposed with
  the previous title or subtitles. Full narration/music/SRT timing is unchanged.

## Limits and release gates
This remains deterministic 2.5D science illustration, **not** photorealistic
AI video. CPU-only workflow: no paid API, GPU, credits or extra data sources.
Visual improvements to this single episode do not yet generalize to arbitrary
science topics. All output remains an unreviewed draft, never auto-published.

Validate the real 30 fps H.264/AAC Kokoro English MP4 on the feature-branch
science workflow and the full CI test suite before merging. Inspect original
video frames and narration by ear. Do not assume CI proves aesthetics.
