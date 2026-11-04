# Universal video quality upgrade — 2026-11-04

## Scope: every supported format, without misleading 3D claims

The original repository has specialised science animation, cartoon character
rigs and opt-in Cycles 3D, but ordinary documentary, cinematic, photo,
product and illustration scenes still used the same central Ken Burns
zoom regardless of storyboard direction.

This upgrade targets the shared fallback renderer:

1. Shot-specific cinematography: wide, medium, closeup, macro, low and
   shoulder now define different crops, framing and eased pans. Authored
   idle, rest, walk, run, fly, jump, talk and surprise actions affect pacing.
   Camera settles at both ends and crop bounds prevent black borders.
2. Real FFmpeg rendering: photo scenes are encoded into H.264 through the
   existing production path, with no external AI model. Regression tests
   decode the MP4 and verify frame count, motion and absence of blank frames.
3. Long-form QA: episodes longer than 36 seconds retain the same 18-second
   decode budget but inspect six distributed 3-second windows instead of
   three 6-second windows. Short videos retain existing inspection.
4. Cache invalidation: shared renderer version and per-clip fingerprint
   change so existing still clips are rebuilt with the new camera direction.

## Limitations

- Camera movement on a still image is not real character animation,
  volumetric 3D, motion tracking or object segmentation.
- Visual preflight is objective defect detection, not aesthetic approval.
- Dedicated science/cartoon/Blender engines remain unchanged.
- No automatic YouTube publishing, paid inference or external media service.

## Next cross-genre priorities

1. Explicit source-media router distinguishing video footage, photos,
   infographics and real 3D, with accurate format capabilities.
2. Local subject-aware camera placement that protects faces, products and
   titles across aspect ratios.
3. Original-footage editing: real cuts, event-aware reframing, musical beat
   alignment and context-appropriate sound design.
4. Genre-aware voice direction, pronunciation dictionaries and natural
   expressive pauses; listening tests in addition to LUFS measurements.
5. Genre/duration quality budgets and real encoded MP4 before/after
   comparison with human editorial review.

## Acceptance

Run repository regression tests and actual documentary rendering, plus
existing science, cartoon and Blender production gates. Inspect the real
encoded MP4 and reports; do not merge on code-only assumptions.
