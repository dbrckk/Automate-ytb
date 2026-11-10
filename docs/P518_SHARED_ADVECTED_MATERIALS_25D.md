# P5.18 — Cached original animated water and magma surface materials

## Problem confirmed from actual 1080x1920 source frames
P5.14 introduced moving ocean ribbons; P5.17 added irregular molten
material plates. Both still relied on static underlying source colors.
This limited surface depth, making motion look like symbols over slides.

## General reusable material engine
`dynamic_material25d.moving_material(size,seconds,material,seed)` uses
three authored coherent multi-scale *cached source planes* shifted at
different speeds, then shades the combined physical field with tailored
water or magma palettes. The result is a spatially continuous animated
source texture; every timeline frame reads the same reusable source.
No per-frame RNG or Python per-pixel loops; motion is a small number of
Pillow shifts, blends and one resize. No GPU, external assets, neural
tokens or paid rendering infrastructure.

The water eddy `flow_material25d.vortex_frame` clips this animation to
the exact original water silhouette before drawing independent moving
filaments. The rock-reservoir `science_volcano_magma._molten_plate`
clips the shared heat layer to the exact P5.17 chamber mask, underneath
its existing irregular floating crust and convection accents. This
*changes the creation engine across two subject families*, not a
single finished video.

## Verification
A dedicated CI pipeline validates inputs and caches, coherent timeline
motion, alpha clipping, unchanged original source assets, original
volcano/ocean animation regressions and genuine 1080x1920 frames.
`scripts/review_dynamic_material25d.py` renders early/late samples for
both actual video topics with SHA256 manifest and a phone-scale sheet.
Full audio and MP4 production validation is still required before main.

This is stylized time-advection, not measured ocean physics, lava CFD,
3D rasterization or automatically editorially approved photorealism.
