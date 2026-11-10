# P5.7 — universal 2.5D cinematic lighting, not a one-off video

## Non-negotiable production direction

Every final video uses authored **2.5D image planes** and a real 2.5D
compositor. Blender/Cycles and 3D proof-of-concept scenes are not part of
this new development track. This work improves the reusable rendering
system across science, stories, explainers, advertising and other topics.

## Verified architecture

The current production system already contains:
- `Scene25D` with independent source RGBA planes, Z depth, per-plane
  parallax and material-aware edge relighting.
- `visual_quality25d` with per-layer detail, chroma, silhouette and
  depth-motion diagnostics.
- P5.6 shared open editorial layout, now merged, to avoid static
  slide-like boxed frames across science videos.

## Added in P5.7

`Light25D` is a bounded, immutable local lighting field in **screen-space
2.5D coordinates**, with independently specified warm/cool light color,
radius, intensity and ambient exposure. It is applied by the common
`Scene25D.render(light=...)` stage **after authored material response**
and **before source-over layer compositing**. Each plane responds with
depth attenuation and its camera-shifted position. Original alpha bytes,
masks, source assets and all unlit legacy outputs are preserved.

This is infrastructure for real event-driven flashes, day/night changes,
reflected warm/cool highlights and controlled cinematic transitions in
**any** topic; it does not make flat primitive source assets magically
premium. No new GPU, model API, paid credit, or external texture is needed.

## Promotion and next tasks

1. Green repository tests, including no-regression of unlit output.
2. Connect event-timed lights to the shared video director, not only to
   a specific lightning renderer. Preserve narration and subtitle timings.
3. Upgrade reusable authored asset families: foliage, metal, clouds,
   water, terrain, architecture, characters and atmospheric effects.
4. Add cross-topic **actual rendered MP4** comparisons and mobile-safe
   1080x1920 review. Do not claim cinematic quality from code or metrics.
5. Keep editorial approval separate from machine validation.

P5.7 is a **shared compositing capability**; a visually superior full
Short is not yet claimed.


## P5.8 — Actual pipeline-wide authored-event integration (implemented)

The feature is now connected to both existing render families rather than
only exposed as an unused compositing API:

- `PortraitScienceScene.frame()` forwards its **measured synthesized-speech
  event fraction** from `science_audio_cues.audio_event_fraction` to the
  same shared `finish_world` implementation. This is available across
  science scenes with real action timing (ocean, lightning, volcano, aurora).
  Scenes with no authenticated event receive **no invented lighting cue**.
- `forest25d.frame(story=True, interaction=True)` forwards the existing
  physical paw–flower contact clock to the same light director. Other
  character frames remain visually unchanged by default.
- `event_lighting25d` provides C1 pulse continuity, exact zero at shot
  boundaries, bounded radii and original warm/cool palette from `LOOKS`.
- `finish_world(event_fraction=...)` runs once on the finished moving world,
  **before** the mobile-screen headline and subtitles. Alpha and pixels
  outside the designated world region are unchanged. Layer-level motivated
  lighting remains separately available through `Scene25D.render(light=...)`.
- Regression tests specifically prevent arbitrary flashes, original-image
  mutation, timer errors and clipping, and compare multiple material looks.

This does **not** constitute a claim that source assets are now AAA; high
quality lighting only enhances existing art. A higher-quality shared asset
library and cross-topic video comparison are still required.
