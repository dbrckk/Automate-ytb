# P5.19 — Continuous environmental 2.5D world, no rectangular ocean card

## Defect observed in real P5.18 frame contact
Although P5.14–P5.18 made currents and material surfaces animate, actual
ocean video frames retained a large purple/blue **rectangular scenic card**
behind the animated gyre. Dynamic ribbons and suspended sediment were
also painted directly onto the overall scene and could continue beyond
the atmospheric card edge, reinforcing a slideshow / visual presentation
appearance.

## General source-compositing correction
`world_volume25d.world_volume_alpha()` introduces a cached, original
smooth environmental light mask that fades organically on all sides.
It works for water, haze or smoke and has a seed-locked irregular
boundary rather than a perfect oval/card. Source lighting remains
specific to the five ocean-story topics and is composed into the existing
underwater atmosphere without full-bleed new images or stock assets.

`science_ocean_depth.lighting_plate` now uses this physical world
transition for all five ocean story topics.

`science_ocean_depth.draw_depth` now draws original moving ribbons,
particle details and highlights in **local source-space 920x890**,
clips their alpha to the same exact environmental volume mask and only
then composites to the real 1080x1920 production canvas. Dynamic
elements can no longer remain as sharp rectangular chart lines where
the source atmosphere has already faded.

The environmental source plane remains cached per story. The animation
uses no per-frame Python pixel loops and avoids allocating a second
full-portrait canvas: original 2.5D motion and captions are preserved.

## Evidence
The dedicated GitHub Actions job verifies edge transparency, substantial
interior material visibility, deterministic source caching, all five
story types, no motion/color leaking into titles and captions, and native
scenes. Three real 1080x1920 ocean narrative frames are provided as PNG,
SHA256 manifest and contact sheet for visual inspection.

This is conceptual original 2.5D scientific imagery, not a numerical
fluid simulation or photorealistic underwater footage.

## Native-frame refinement — last dense-water diagram removed
The first actual P5.19 review sheet exposed another blue rectangular
card in the sinking/polar-water chapter. The same PR now replaces this
real production card with the new shared open-water caustics and
`density_plume25d.sinking_plume_frame`: low-resolution diffuse
volumetric shading behind moving full-resolution cold-water filaments.
The entire material source is clipped to the existing organic world
mask. Surface ripple, coherent deep descent, visible ice and scientific
explanatory arrows remain. Legacy direct-draw access is preserved.
This is original conceptual 2.5D animation, not a fluid solver.
