# P5.5 — Extreme 2.5D is a product-wide video pipeline, not a one-off storm

**Product-owner direction (2026-11-09): ALL future native artwork is 2.5D
only. Improving a single episode is not a substitute for upgrading the
reusable video-creation process.**

PR #249 (experimental Blender motion) closed without merge; published
Shorts remain accessible. P5.3's historical standalone Blender pilot
stays inert as evidence; it is not promoted to video production.

## Current architecture and the real failure mode

PortraitScienceScene.frame is the shared portrait renderer for lightning,
volcano, aurora, rainbow, Earth/orbit and ocean science. Scene25D is shared
by lightning and animated forest character worlds. The one-click workflow
turns authored scenes into real AAC/H264 and already runs voice/caption and
MP4 QA. **The bottleneck is source art detail and material depth**, not
another pile of transitions.

## Integrated as reusable code (not a single video)

1. automate_ytb/finish25d.py: shared, free, deterministic finishing on
   WORLD pixels: edge definition, local contrast, authored color balances
   and bounded diffuse light. World-only bounds preserve existing mobile
   title/subtitle safe zones. Used by every native science family and
   fox/rabbit/cat 2.5D moving-character scenes. No AI upscale.
2. automate_ytb/surface25d.py and Layer25D.material: common alpha-derived
   rim light and interior contour shadow for cloud, foliage, metal,
   fabric, mineral and water. Applied to storm cloud/terrain AND forest
   actors/landscapes. Z depth, transparent masks and original parallax
   stay intact. Default material='none' preserves the old compositor.
3. review_board.py: diagnostics on actual MP4-decoded scenes (portrait
   or landscape), exposing flat geometry, low local detail and weak
   palette separation in visual-review.json for ANY video genre.
   Signals are advisory, not automatic aesthetic approval.
4. one-click-preview.yml: explicitly rejects 3D before any costly speech
   or Blender installation; only original 2.5D is allowed. Both new unit
   test groups run before Kokoro.
5. H264/AAC delivery, FR/EN narrator, audio-aligned SRT/VTT, provenance,
   timecodes and editorial approval rules remain unchanged.

## What this stage DOES NOT claim

A look/lighting pass cannot transform simple source shapes into extremely
detailed art by itself. It does not invent new clothing seams, biome
geometry, complex cloud silhouettes or new animations. Authoring
material-rich source assets is the next major task.

## Validation gates

- New modules and existing full production test suite must pass.
- Render at least two independent topics, compare real decoded MP4 frames
  against pre-P5.5 frames, not posters or promised file paths.
- No title/caption changes, audio drift, flicker, alpha loss, wraparound
  edges or excessive CPU render cost.
- Stable download link only after real MP4 encode, tech QA, anonymous
  HTTPS download and original file checksum match.
- Human review still required for visuals, scientific claims and posting.

## Global roadmap toward genuinely extreme 2.5D

P5.6: **semantic authored asset construction** across ALL native genres:
multiscale silhouettes, paintable material textures, atmospheric depth
planes, water/foliage/architecture/character/electric VFX material maps
and reproducible cached RGBA assets, not single flat backdrops.

P5.7: **reusable motion engine**: material-aware deformation,
wind/fluid movement, motivated character contact shadows, foreground
occlusion, action-reactive lighting, continuous temporal motion.

P5.8: **real encoded video QA**: multiple topics at 1080x1920 30fps,
palette/depth/detail/motion evidence, prior-video comparisons, CPU budget,
anomaly warnings and manual art review.

P5.9: production reliability, multi-genre scene recipes, caching,
regression suites, permanent release links and editorial signoff;
no paid media credits, unlicensed artwork or claims of false AAA quality.

## P5.5 quality QA correction from actual encoded film

A real 30.04-second 1080x1920 Kokoro ocean-currents preview passed H264,
AAC, timing and old 'flat asset' numerical signals, **but still looked like
five infographic slides**. Its huge left/right panel borders are present in
each decoded beat. The generic visual QA now reports paired dominant panel
rails separately from color and edge complexity and requests visual review.
This is an honest diagnostic, not an invented replacement for the flat
assets. It is calibrated against this ocean preview, the rendered 2.5D
forest video and the submitted lightning video; the panel detector is
**advisory only** because genuine architecture can contain rectangles.
