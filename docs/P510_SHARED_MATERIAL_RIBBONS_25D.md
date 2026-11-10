# P5.10 — Shared original 2.5D material strokes for every video subject

## Purpose

Fix the creation **process**, never just a lightning or ocean example.
Original authored curves now have a reusable screen-space material-aware
appearance and deterministic visible direction-of-flow. Only 2.5D images,
Pillow/vector paths and local CPU calculations; no external downloaded
art, GPU, 3D renderer, or paid token.

## Integrated into real video generators

- Original rainbows: light refraction/emergence beams stay **strictly
  straight**, with spatially cohesive scattering, a warm/cool colored
  luminous core and a photon impulse travelling along real arc-length.
- Ocean circulation: original moving water paths retain their authored
  waveform, now with depth-color underside, fine cool rim and a moving
  in-curve highlight, not just a static single-pixel wave.
- Volcanic lava: advancing physical routes receive the same layer-aware
  material renderer but in incandescent magma colors. An unstarted
  zero-length flow at t=0 is explicitly NOT rendered as a fictitious bolt.

All three call `automate_ytb.material_ribbons25d.draw_material_ribbon`,
so changes to finish quality and dynamic material parameters immediately
propagate to existing videos and future topics.

## Safety & quality gates

- Validate finite world-space coordinates, authored material choices, frame
  time/progress, non-degenerate visible paths, alpha range, and determinism.
- Tracer position is arc-length weighted, not a vertex-index jump.
- Test actual existing domain renderers at two different timestamps,
  including a zero-flow start for lava; verify no full-stage freeze.
- Render actual original 1080x1920 `PortraitScienceScene` images for
  rainbow refraction, ocean wind and volcano lava. Provide inspectable
  RGB PNGs, screenshot sheet, SHA256 manifest and CI green.
- Do not conflate technical verification with human aesthetic approval,
  do not publish automatically, and keep the full Kokoro release pipeline
  completely unchanged.

This **adds spatial material structure and animated visual traces**, but
does not replace all primitive shapes. The next art pass should target the
large source heroes (sun, water droplet, rock summit, cities, animals) and
genuinely more sophisticated depth, silhouette, occlusion and art direction.
