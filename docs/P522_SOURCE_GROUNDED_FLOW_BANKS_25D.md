# P5.22 — Original source-based lava channels and moving water banks

## Identified in real P5.20–P5.21 review
Two lava rivers advanced with a **uniform-thickness painter's line**
ending in a circular orange cap. Detachable bright speckles and parallel
tube walls made the new mountain look like a diagram. Ocean surface
current lines also retained a simple uniform-width renderer.

## Shared 2.5D physical source geometry
`flow_banks25d` now handles original connected rock/water source paths,
their *independent* irregular left and right banks, dark cooling edges,
a hot center, time-advected polygonal cooling plates and water shear.
Variations are keyed to cumulative distance from the **original path
origin**, not to the current number of visible vertices. The upstream
rock banks therefore **do not morph or jump** as the lava head advances.

`advancing_path(path,progress)` moves the magma front by actual arc
length, correcting unequal-speed segment-index animation. Physically
anchored noses taper at the current channel end; no artificial circular
lava-cap sprite or drifting sky flecks remain.

`science_volcano._lava_track(side)` caches both original authored
rock drainage paths ONCE for reuse across hundreds of frames. Flow
lighting is still masked to the real 2.5D terrain. 
`science_storyboards._wind` uses the same bank geometry for three water
current bands, with the actual variable narrated duration, not a
hard-coded episode length. Existing optical and general ribbons stay
untouched for backward compatibility.

Only local native Pillow polygons are rasterized. No new full-portrait
intermediate, no per-frame random noise, paid API, 3D or external bitmap.

## Acceptance
Targeted tests verify geometric continuity, unequal banks, stable
source-clock playback, monotone arc-length head, original anchoring,
alpha safety, long-duration narration, and old physical/semantic
scene regressions. A CI workflow produces actual 1080×1920
volcano/ocean source frames at two time points and SHA256 evidence.

Full production, Kokoro voice and MP4 release gates remain mandatory
before merge. This is a sophisticated original 2.5D science aesthetic,
not a physical numerical simulation or an AAA/photorealistic claim.
