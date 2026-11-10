# P5.24 — Shared original-material relief generator across ALL video subjects

## Source-engine defect
Color saturation, contrast sharpening and optical refraction cannot alone
reveal the existing authored small ridges of rocks, water and atmospheric
clouds. Without local directional light response, source material looks
flat even when the underlying art has useful surface details.
A universal arbitrary noise filter would introduce false geometry,
temporal flicker and unwanted flat-silhouette texture.

## New reusable CPU-only source step
`material_relief25d.sculpt_authored_material` turns actual existing
**luminance variation** into a deterministic 1/3-resolution
directional light-and-shadow proxy. Raking warm/cool palettes respond
to the current authored scene look (water, mineral heat, atmospheric
plasma, storm, forest). It does not invent source geometry:
- Solid-color fields are bitwise unchanged. Daylight, neutral and
  precise rainbow optics bypass the shader by design.
- The same pixel input yields the same source relief at every timestamp:
  no RNG, non-reproducible image synthesis, new texture atlas,
  graphics model, downloads, paid credits or mesh rendering.
- The common `finish25d.finish_world` applies source detail **after**
  continuous P5.23 optical movement, but before existing event lighting,
  safe edge feathering, final title and spoken-caption overlays.
- Native Pillow bands are computed at approximately one third
  source resolution, then blended on actual painted RGB without
  introducing extra 1080×1920 stage buffers.

## Evidence
Real audio-synchronized 1080×1920 original source frames from ocean,
volcano and aurora are compared at precisely the same timestamp with
the material relief pass enabled/disabled. Dedicated independent
Actions tests verify source preservation, flat-color identity,
source variation, deterministic re-render, exact alpha and text-safe
regions, and legacy finish/optical contracts. PNGs, SHA256 and
the contact sheet are retained for inspection.

This is **material lighting**, not automatically created complex
geometric assets, simulated surface normals, 3D, AAA cinema, source
fact-checking or editorial approval. Source complexity and stronger
semantic visual planning remain the following development priorities.

## Dependency and merge policy
This PR is intentionally stacked on **P5.23** continuous optics.
Do not merge into `main` until P5.23 passes general production
and narrated Shorts QA; then rebase P5.24 on that exact main,
verify isolated changed files and require full production QA on the
combined head.
