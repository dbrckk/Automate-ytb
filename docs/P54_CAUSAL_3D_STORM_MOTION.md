# P5.4 — Five-shot 3D storm motion, bounded production feasibility

The P5.3 Blender pilot is real Cycles/PBR (CI passed) but its recovered
540×690 frame exposed large simplifications: cloud lobes read as cotton
balls, industrial facades as extruded boxes, and water pools as black disks.
Do not prematurely call that render cinematic, photographic or AAA.

## Implemented

- Five causally ordered shots from **the same real 3D scene**:
  charge separation, branching descending leader, upward attachment, bright
  return stroke and expanding thunder wave.
- Five perspective camera plans, continuously varied during each shot.
- Shared 3D channel curve whose visible extent follows scene action;
  side forks and lighting strength change with the conductive event.
- Added correlated colored noise on actual PBR cloud shaders, additional
  geometry deformation, facade ribs, metallic details and less circular
  reflective water patches.
- Exact original frame SHA256 and 3D provenance tracked in manifest;
  duplicate/frozen animation, corrupted pixels, bad beat order, blank
  render, unsafe dimensions, truncated MP4 and mismatch of number of
  decoded H264 frames all block delivery.
- Free Blender Cycles on CPU, free FFmpeg, no imported model or image,
  no AI rendering credits or third-party assets.

## Explicitly NOT claimed

This is a **2.5s silent 320×400, 8fps visual animatic**, not a 30fps,
1080×1920, fully narrated Shorts candidate. Its job is a bounded rendering
experiment and real image-to-image comparison with P5.2, avoiding a
disruptive replacement of the working Kokoro release pipeline.

## Progression gate

1. Run GitHub CI to actually raytrace each time step and inspect its
   20 decoded PNG frames and actual H264 file.
2. If practical, review the sequence for harsh jumps between beats,
   cloud materials, urban geometry, highlight contrast and actual motion.
3. On passing main CI, permanent prerelease MP4 HTTPS link is downloaded
   anonymously and compared byte-for-byte to the encoded original.
4. Integrate the 3D renderer into full episodes only if the actual
   improvements and CPU budget are convincing. The stable 2.5D path
   remains the default until then.

## Next 3D visual changes required for premium level

Real animated cloud density (smoke/volumes instead of broad spheres),
physically defined cloud-light scattering, higher-quality industrial
environment assets with nonrepetitive windows and realistic material aging,
a lightning VFX system with stronger secondary forks and momentary atmospheric
illumination, true 30fps temporal animation, final grading and audio alignment.
P5.4 is the evidence-gathering step, not the finish line.
