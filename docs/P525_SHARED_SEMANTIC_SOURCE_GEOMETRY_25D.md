# P5.25 — Original semantic geometry for every future 2.5D video

## Source-asset problem (not a finishing/FX problem)
Inspecting the real 1080×1920 P5.24 science source contact sheet showed
flat, repeated bright circles and uniform filled polygons — particularly
auroral plasma graphics. A global sharpening, saturation, glow, or screen-space
relief shader cannot add semantic object geometry. This change operates
BEFORE the global finishing pipeline and is not limited to one video.

## Reusable original source generator
`automate_ytb/semantic_geometry25d.py` defines a single deterministic,
bounded `render_material_sheet` contract. The output is a transparent RGBA
source plane with multiple asymmetrical **real curved silhouette contours**,
overlapping depth bands and source-following illumination/occlusion folds.
It supports **three distinct authored material families**:

- **Plasma:** a changing double-contour emissive curtain with many fine
  longitudinal folds, thin conductive striations and an occluded underside.
  `science_aurora._curtains` now draws six independently animated source
  planes through the common generator, rather than solid smooth polygons.
- **Water:** a thinner wave crest plus refractive translucent inner bands,
  integrated into `science_ocean_depth.draw_depth` *behind* existing
  physical source-guided ocean tracers. It preserves source masks and their
  feathering into the surrounding sea.
- **Volcanic ash:** broader asymmetric, darker diffuse bands, used **only
  in the active eruption beat** behind an existing crater-origin plume,
  rocks and ejecta, with progressively increasing opacity. Calm beats
  do not gain fake ash.

Every shape is generated from fixed seeded spatial harmonics and continuously
varying physical scene clock; **no random per-frame noise, unlicensed image,
GPU, online model, paid service, image-to-depth hallucination, or 3D**.
The generator returns a 2.5D source plane, not a composited title card.
All overlays, moving cameras, Kokoro audio, caption timing, SRT, H264/AAC and
production release handling remain owned by the existing pipeline.

## Verification protocol
- New unit tests validate source alpha, silhouette asymmetry, material
  uniqueness, deterministic same-time rendering and negative inputs.
- Tests render **three distinct real source frames** (aurora, ocean, volcano),
  before and after disabling only the new geometry. Compare the same timestamp
  at real 1080×1920 without modifying narration. Verify title/caption regions
  are byte-identical.
- `scripts/review_semantic_geometry25d.py` saves six native-resolution PNGs,
  a contact sheet, and individual SHA256 hashes in a GitHub Actions artifact.
  A human must examine the result: mechanical passing tests cannot certify
  beauty, originality, physics, or factual accuracy.
- The permanent narrated English Kokoro 1080×1920 release-candidate
  workflow now tracks changes to the new shared engine as well as all three
  subject consumers. CI includes previous aurora, ocean and volcano suites.

## Performance and scope limitations
This is an incremental shared **geometry** pass, not an assertion that all
scenes now look AAA. CPU cost increases because each animated transparent
sheet is rasterized per frame. Compare genuine video render durations in CI
before merging. This stage adds no neural asset synthesis or full 3D geometry.
It does not replace P5.24 source-derived microrelief. Richer object anatomy,
temporal coherence metrics, foreground occlusion, material-driven deformation
and human visual review remain separate follow-on steps.

Merge only after P5.24 is integrated and P5.25 passes targeted visual-source
checks, full production tests, and narrated H264/AAC export. Keep public
publishing disabled pending editorial approval.
