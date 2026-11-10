# P5.14 — Reusable, actually moving original 2.5D water eddy materials

## Production problem
The previous Coriolis current storyboard drew an enormous flat ellipse and
three geometric circles. Moving dots did not give its source body material
depth. Although meant to be explanatory, it looked like a slide deck.

## Shared source-art engine
`flow_material25d.py` supplies two public reusable operations:
- `vortex_source()`: cached, bounded translucent source with original
  radial shading, coherent directional texture, natural rim, and three
  tailored ocean/lagoon/storm material palettes.
- `vortex_frame()`: adds independent **per-frame moving spiral filaments**
  over the reused source. The movement is not a rotating flat photograph.
  All highlights are clipped to original fluid alpha, the source is never
  mutated, input dimensions and clocks are bounded, and generated imagery
  does not require third-party assets, 3D or paid services.

## Actual production integration
In `science_storyboards._coriolis()`, real native 1080x1920 videos receive
the moving water while existing explanatory trajectory arrows, stable
title/caption bands, precise audio cue times and a 'schematic/not to scale'
label are retained. Existing external Pillow-draw-only calls remain
backward compatible.

## Verification
`test_flow_material25d.py` verifies source caching, alpha, motion, palette,
time and safety limits, actual storyboards and production 1080x1920 frames.
`scripts/review_flow_material25d.py` renders two genuine source frames and
an inspectable contact sheet into CI artifacts, retaining SHA256 hashes.
Full studio validations still cover FFmpeg output, speech and captions.
A human phone-scale assessment remains necessary. The animation is a
conceptual gyre and must not be presented as geographically correct
hemisphere rotation or a predictive ocean model.
