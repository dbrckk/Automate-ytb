# P5.11 — Native continuous atmospheric parallax across future 2.5D video topics

This is a production-engine change, **not** a new isolated episode.

## Previous limitation
The cached original cloud silhouettes introduced in P5.9 had coherent source texture and real alpha, but they never moved within a narrated shot. Camera post-processing and moving diagram tracers cannot fix static source atmosphere.

## Implemented shared engine
- `drifting_cloud_bank()` reuses the exact original organic texture/alpha from the cached `cloud_bank()`, with a slightly overscanned source and **full-resolution bilinear subpixel translation**. No regenerated per-frame noise, no wraps, black edges or paid calls.
- Two independent parallax speeds now animate the upper and lower cloud planes in **every native rainbow scene**. Sky gradient and diffuse haze remain cached, and physically explained optical rays are painted after the environment.
- All volcanic beats now receive a separate moving upper-sky cloud plane between the cached distant rock/sky and the actual magma/plume/VFX. Ash and lava timing are not rewritten.
- Strict time/seed/material bounds and true no-op transparent off-cloud zones protect long-lived 1080×1920 Short scenes. 1920-wide assets gracefully disable camera drift instead of sampling beyond the original source.

## QA and limitations
- Regression tests exercise deterministic motion, cached-source immutability, unsafe inputs, mobile title/subtitle preservation and actual rainbow and volcanic scenes.
- Existing science/rainbow/volcano/organic workflow suites validate compatibility on the PR branch. The main release gate validates fully encoded MP4 and speech.
- Atmospheric parallax is deliberate 2.5D layered illustration, not actual fluid simulation or neural video. This change improves scene continuity but **does not by itself solve primitive hero silhouettes** (droplet, sun, summit) or certify extreme visual quality.
- Next target: detailed reusable heroic object silhouettes/material maps, cross-genre renders and human inspection of full encoded MP4s before publication.
