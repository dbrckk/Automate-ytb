# P5.5 — 2.5D extreme quality, across the video production pipeline

## Production policy

The main video renderer remains **2.5D only**. Experimental Blender 3D
animation must not replace the narrated Shorts engine. This is a change to
the reusable creation process, not a one-off enhancement to lightning.

## Reusable first step shipped

Every `Scene25D` now exposes `quality_report()` for independently
authored layered RGBA visuals, irrespective of video topic, language or
orientation. It measures actual visible texture/detail energy, silhouette
edge complexity, warm/cool chroma separation, three-or-more depth planes,
distinct parallax motion profiles and resulting frame-to-frame displacement.

The report is **diagnostic**, not a cinematic-quality certificate:
intentional minimalism, fades, stylization and low-light scenes may be
flagged. It never modifies source images, rejects videos automatically,
claims factual review or authorizes social publication.

## Next reusable upgrades, in order

1. **Asset contracts:** require detailed foreground, middle and background
   layers with metadata for texture source, scale, lighting direction,
   edge quality and intended movement. Keep originals and rights evidence.
2. **Reusable 2.5D material library:** procedural or originally authored
   roughness, patina, foliage, cloth, stone, cloud, water and metal; avoid
   repeating simple geometry across topics.
3. **Lighting graph:** depth-aware rim lights, physically motivated local
   flashes, occlusion, warm/cool contrast, wet-surface highlights and
   color-script transitions driven by the scene's semantic events.
4. **Animation grammar:** animated masks, independent near/mid/far motion,
   subtle deformations, particles and camera trajectories with a meaningful
   event, rather than static images panned across a screen.
5. **Automated quality evidence:** run reports on all scenes, export
   per-scene before/after metrics and contact sheets for human inspection;
   preserve existing MP4/voice/SRT and public-release verification.
6. **Promotion gate:** compare actual rendered MP4 clips and reject
   regressions in technical decoding, pacing and caption legibility.
   A numeric score alone never proves aesthetic improvement.

## Non-goals

No new Blender dependency in production. No paid image credits. No
unlicensed stock footage. No one-topic hardcoded "premium" score.
No claim that this first diagnostic change alone delivers extreme visuals.
