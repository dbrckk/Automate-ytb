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
