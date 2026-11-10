# P5.23 — Global graphics motion engine, not a one-off video

## Production defects from source audit
The shared science world finish already adds color, contrast, sharpening
and sparse event lighting, but it treats **author-painted surfaces as
rigid pixels** between 30fps animation frames. Water, heat haze, auroral
glow and fast atmosphere never refract surrounding original pigments.
The multi-depth `Scene25D` compositor also rounds every parallax
translation to integer pixels; at typical camera rates this makes
fine particles, clouds, character hair and foreground masks **judder**
in 1px steps rather than move continuously.

## Reusable original 2.5D sources (all future videos)
`optical_motion25d` is one bounded CPU-only generator:
- `refract_source` moves original scene RGB through a regular coarse
  64px source-space optical mesh. Vertex displacement is analytical,
  low-amplitude, deterministic and continuously dependent on *actual*
  narrated frame clock. Warp vertices are shared across cells to
  prevent spatial seams. All source crop borders remain pinned.
  Every output pixel is sampled from **existing original video art**,
  never synthetic/stock stills, per-frame random grain or generic
  photo zoom. Distinct subdued original direction presets for
  ocean water, volcanic heat, auroral atmospheric light, storm air,
  and forest foliage. Precise rainbow optics, daylight diagrams and
  neutral sources are intentionally unwarped.
- `translate_subpixel` resamples existing transparent 2.5D depth
  planes with Pillow's *premultiplied* RGBa interpolation. This
  preserves smooth foreground motion, avoids alpha-black halos and
  prevents severe integer-coordinate snapping. True integer-offset
  scenes keep the existing fast path unchanged.

`finish25d.finish_world` invokes original source refraction BEFORE
focal light and final source-region feathering, but AFTER authored
graphics. It is the same common code path for lightning, volcano,
ocean, aurora, rainbow, and Earth source frames, with original
mobile title and caption overlays rendered later without distortion.
All original RGBA alpha and world crop edges are retained.
`scene25d.Scene25D.render` uses subpixel per-layer transformations
for any authored depth, material, source mask or camera path, while
keeping cached low-frequency authored light positions rounded for
performance and strict integer identity where applicable.

## Verification and scope
The targeted CI generates genuine 1080×1920 source frames for **three
different stories** (ocean, volcano, aurora), each comparing the same
timestamp with the new optical engine enabled vs disabled. It enforces
actual pixel differences inside original art, byte-exact unchanged
title/caption areas, deterministic frames, sensible source bounds,
premultiplied edge safety, safety rejection and old 2.5D/lighting
regressions. Images, SHA256 manifest and real contact are saved.

Full narrated Kokoro, SRT and H.264/AAC production QA remains mandatory
before merging. No commercial credits, image inference, 3D renders,
new licensed assets, fake measured optical physics or automated approval.

The general source engine improves **continuous movement and optical
depth**. It cannot magically turn primitive object geometry into
detailed art; complex source-assets remain a separate core priority.

## Regression fixed using real Actions evidence
The initial Actions tests discovered a previous P5.8 general finishing
invariant: identical input at shot start/end must stay byte-identical
when there is no authored event light. Independent optical movement
violated this. A smooth `sin(pi*t/duration)^2` **C1 boundary
envelope** now gives exact original pixels at both ends, while leaving
all mid-scene source-space motion continuous. Tests sample a genuine
nontransparent cloud pixel and preserve the historical event-light
contract, without relaxing its checks.

## Production release gate permanently expanded
The audit uncovered a coverage gap: modifying `finish25d` or
`scene25d` previously triggered PNG/scene tests but did not reliably
start the real narrated `science-shorts-release-candidate` workflow.
This PR changes the **permanent on.pull_request and on.push path
filters** for the existing reusable 30s English Kokoro 1080x1920,
30fps H.264/AAC production job to include `optical_motion25d`,
`finish25d` and `scene25d`. Any future change to these common
graphics modules must then pass real TTS, MP4 decode, captions, media
QA and contact sheets; a dedicated test enforces this wiring.
It is not a request to publish a new video publicly.

## General 9:16 narrated release-gate regression repaired
The first full narrated science preview on this branch reached its
art-direction gate and reported one P5.8 legacy assertion treating
**identical source images at two different times** as mandatory.
P5.23 deliberately adds original moving water/heat/auroral optical
materials; static equality at 1.2 s and 3.7 s would prohibit the
requested real motion, despite an absence of random flicker.
The shared test is now updated to require deterministic *same-time*
rendering, a smaller pixel-level difference across 10 milliseconds
than across 2.5 seconds, and **exactly equal** start/end images
with the C1 shot-boundary envelope. The dedicated shared graphics
workflow now executes that test as well; existing general preflight
and narrated release QA remain mandatory.
