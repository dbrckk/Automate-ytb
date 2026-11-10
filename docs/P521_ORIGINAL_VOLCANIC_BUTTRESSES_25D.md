# P5.21 — Geometric volcanic buttresses: break the uniform pyramid

## Defect in actual P5.20 production frames
Even after the molten jet became a real moving 2.5D source, the exterior
mountain still read like a nearly triangular pyramid with broad regular
faces. Painting more colors onto the same geometry cannot correct that
major source-art defect.

## Correct source heightfield, source mask and illuminated faces together
`science_volcano_mesh` now uses an original erosion-based sampled ridge
silhouette, derived once from geologically motivated hand-shaped
shoulders. The canonical vent and summit anchors are unchanged and the
lower mountain joins the original ground. No detached screen-space
decorations or fake parallax substitute for geometry.

The source geometry itself gains world-space radial buttresses, rock
stratification benches and eroded slope channels. Heights and projected
ring radii vary coherently with radius/azimuth; disturbances taper to
zero at the real source rim and foothills. The fixed mesh still receives
face-normal lighting, original weathered mineral materials, actual
lava-source illumination, soot, magma flow, and moving camera direction.
The geometry is *cached once* and reused across every video frame;
per-frame billow and magma/moving material engines are unchanged.

## Evidence and limitations
Independent GitHub Actions tests validate the crater depression, masked
alpha, seeded deterministic geometry, source anchoring, stable 9:16
eruption/lava frames and compatibility with old mesh/lighting tests.
A review artifact contains two actual 1080x1920 original frames,
SHA-256 manifest and a phone-scale contact sheet. Full voice/MP4
production CI must pass before merge.

This is original mathematically projected **2.5D** science scenery.
It is not terrain data from a real volcano, a physical landslide solver,
or automatic proof of photorealism or a cinematic AAA standard.
