# P5.9 — Original organic 2.5D asset bank for the actual video pipeline

## Product constraint

The *process* must improve across future videos, not only the storm. All
new deliverables use authentic, animated, multilayer **2.5D**, no Blender
or external 3D models. Keep Kokoro phrase timing, the proven 1080×1920
pipeline, mobile subtitle margins and freely accessible GitHub artifacts.

## Verified current limitations

Cross-topic previews in GitHub Actions (P5.6/P5.8) still showed
simplistic rainbow diagram boxes, repetitive sawtooth terrain around the
volcano and broad geometric ocean depth bands. Lighting alone cannot
invent genuine source-asset detail.

## Implemented in shared module

`automate_ytb/organic_environment25d.py` is a reusable local CPU asset
bank, not a per-video hand-painted still:

- **Cloud banks:** coherent multiscale internal density, weathered irregular
  silhouette, colored material shading and true soft alpha. No circles
  scattered along a baseline as isolated cloud sprites.
- **Rock/terrain:** four independent eroded horizontal profiles with
  multiscale nonrepeating ridges, rock sediment bands and depth-dependent
  color/transparency. Works on land and underwater geology.
- **Water optics:** perspective-separated caustic light paths following
  spatially smooth water folds, with a bounded reflected bloom and
  separate sharp optical threads.
- **Safety:** deterministic seed, strict size/palette bounds, cached source
  assets rather than per-frame noise, authored RGBA outputs and no
  network/dependencies beyond installed Pillow.

## Wired into actual videos

1. `science_rainbow.daylight_background()`: two distinct translucent
   cloud banks in the original daytime sky. `draw_rainbow` no longer
   frames optics in a large opaque rounded rectangular chart and grid;
   semantic ray paths remain unchanged.
2. `science_volcano._base()`: distant original rock strata and an
   atmospheric bank behind the physical summit. The five real volcanic
   actions and camera trajectories remain intact.
3. `science_ocean_depth.lighting_plate()`: replace the two plain
   five-point seafloor polygons with shared eroded sediment bodies and
   multiple water-caustic paths. Actual currents are still animated
   separately on their existing physical clock.

These original environment materials are **cacheable art primitives** that
future wildlife, commercial, documentary, atmospheric and underwater
renderers can use without changing the generator or paying for images.

## Acceptance

CI runs bounded deterministic geometry tests plus all existing
domain-specific regressions. It renders actual 1080×1920 science source
frames for rainbow, volcano and ocean and uploads inspectable full PNGs,
a contact sheet and original SHA256 records. Human inspection is needed;
no claim of photographic or AAA quality just from a passing test.

This resolves *some* visual primitiveness, not all of it. A further
round should introduce reusable organic hero silhouettes, believable
cloud scattering, nuanced mineral facets, more advanced water refraction,
material-responsive event illumination and a full narrated MP4 comparison.
It must not become an isolated special-effects patch.
