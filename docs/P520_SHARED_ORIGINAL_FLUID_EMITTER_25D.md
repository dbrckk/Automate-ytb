# P5.20 — One original causal 2.5D fluid emitter for magma and spray

## Actual source-art defect
The P5.19 geological frames still painted the erupting molten fountain as
three straight vertical lines with fixed widths. The wind-driven ocean
scene used large teaching arrows without matching physical water spray.
More static material noise cannot solve missing source motion complexity.

## Shared CPU-only moving-material engine
`fluid_emitter25d.emitter_frame` generates connected coherent *bundles*
of moving tapering source paths with soft sub-surface scattering, dark
under-ridges, heat/light highlights and time-advected source flecks.
The same bounded original function supports magma fountains and
wind-driven surface spray with distinct source directions and palettes.
An anchored emission origin is provided by `emitter_anchor`.

Volcano `_explosion` now attaches the fountain source exactly to the
existing (540,345) crater and keeps original source-space ash billows
and ballistic fragments above the material. Ocean `_wind` now layers
spray on the existing underwater environment, behind scientific
arrows and captions, with its own continuous motion.

It renders only small native-space RGBA source patches, ~300×280 for
fountains and 690×190 for spray; glow is computed at quarter size, with
no per-frame RNG, downloaded art, GPU, paid model or 3D dependency.
The direction and palette of source forces differ, but the renderer,
validation, temporally coherent path logic and moving flecks are shared.

## Verifiable acceptance
Targeted unit tests cover edge transparency, emitter origin, continuous
change between timestamps, seek reproducibility, absence of a lava jet
before eruption, input safety and actual native 1080×1920 scene frames.
A new independent GitHub Actions CI renders four authentic original
science frames for magma/spray at two times, exports SHA256 records and
a phone-scale review contact. Existing volcano ash/ejecta, ocean
storyboard, full-pipeline audio, accessibility and MP4 gates must pass
on the exact final head before merging.

Illustrated fluid trajectories are educational; these source visuals
do **not** claim physically simulated lava or windborne water, 3D
rasterization, or automatic aesthetic approval.
