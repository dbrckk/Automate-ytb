# Visual quality bar — original storybook videos

This is a development acceptance checklist, not a claim that current output
already meets a commercial animation studio's finish. Every image is authored
locally; third-party inspiration and model/catalog availability are not rights.

## Visual baseline to review on mobile

For each supported actor (fox, rabbit, cat, owl), compare:
- Full-body wide, medium conversational shot and face close-up;
- Day and night lighting, forest and another narration-grounded biome;
- Neutral/happy/worried/surprised emotions, blink and spoken mouth cue;
- At least one walking, jumping and resting clip at 24 fps;
- Readability of original title, eye glints, ears, toe shapes and contacts.

## Priority order and measurable shipping gates

1. **Raster fidelity** — actual high-resolution drawing, downsample before
   materials, unchanged source dimensions and subpixel edge alpha; see
   `tests/test_sprite_supersampling.py` and encoded MP4 suite.
2. **Distinct characters** — original fox V muzzle, rabbit puffy cheeks and
   feline temple/tabby motifs in every authored facial pose; see
   `tests/test_species_anatomy.py`. Do not change pupils when blinking or
   place opaque decals over the speech overlay.
3. **Performance budget** — keep free/offline Pillow and FFmpeg with bounded
   memory, no runtime downloads or unlicensed model dependencies. Test real
   720p/1080p clips and output frame counts.
4. **Acting and posing** — next: physically plausible timing, head turns,
   independent head/neck, landings, eye direction aligned with movement and
   shape-consistent limb pivots. Current system remains 2D, not IK.
5. **Environment art** — next: distinct foreground, midground and background
   color palettes and nuanced framing; avoid piling distracting glow effects.
6. **Editorial fidelity** — never replace story meaning, skip human rights
   approval, modify audio timing, or interfere with readable SRT/VTT.

## Review decision

A green unit suite is **necessary but not sufficient** to label a scene
premium. A human should inspect the actual CI-video on Android at normal speed
and compare face shapes, motion jitter, silhouettes, color and staging. Record
specific frame/timecode failures, then fix rendering code and revalidate.
