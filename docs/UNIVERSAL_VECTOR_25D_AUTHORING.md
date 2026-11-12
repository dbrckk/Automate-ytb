# Universal 2.5D vector storyboard — original Shorts

## Capability delivered

The reusable vertical-video engine now accepts two complementary, explicitly
authored visual media types per narrated beat:

- visualLayers: original or rights-approved PNG/WebP images with parallax;
- visualVectors: original editable Bézier paths, polygons and ellipses, painted
  locally in 2× antialiased resolution with gradients, highlights and glow.

Both paths feed Scene25D, the original actor keyframes, continuous cross-beat
camera and real PCM-derived narration/sound events. Vectors need no PNG files,
image API key, SVG interpreter or online media provider.

## Working local example

    python examples/build_vector_botany.py --out build/vector/story.json
    automate-ytb-short --brief build/vector/story.json --output build/vector/botany.mp4 --voice espeak --width 720

For the optional free neural voice, install the project's speech extra and use
--voice kokoro instead. The deterministic GitHub Actions video tests use
eSpeak and do not claim natural-human narration quality.

The example creates original multi-depth seed/soil/root/leaf/water drawings,
then grows/reveals independently moving actors through two continuous beats.

## Vector source contract

Each visualVectors layer requires: name, z, parallaxX, parallaxY, material,
shapes. Layer z (0..100) must be unique across all vector and PNG layers.
There can be 1–6 vector layers, at most 48 shapes per layer and at most
120 shapes total. Supported shape types: path, ellipse, polygon.

Each shape requires: type, geometry, fill, stroke, strokeWidth, opacity, glow.
Fill can be a 6-digit hexadecimal RGB or an exact top/bottom color gradient;
stroke is a 6-digit hex RGB or null, and strokeWidth is 0..0.04 stage width.
Source opacity is in 0.02..1 and glow radius in 0..0.06 stage width.
Geometry coordinates must be finite and between -0.15 and 1.15.

- Ellipse geometry: [x0, y0, x1, y1].
- Polygon geometry: a list of 3–64 [x,y] points.
- Path geometry: a list of 2–60 M/L/C/Z commands. Cubic C uses c1, c2, p;
  M and L use p; Z closes the final path. Filled paths must close.

Optional actorTracks are the same as for approved transparent PNG layers.
Every actor key has at, x, y, scale and angle, plus optional opacity (0..1).
An opacity transition lets a sprout, object, label or light appear gradually
instead of abruptly popping into place.

Two adjacent beats with identical original source geometry use cached
raster artwork and a shared camera. Mismatched final/initial actor poses
(including opacity) are rejected. Explicit actorLinks receive causal Foley.

## Editorial, safety and performance

- Inline vectors cannot embed SVG/XML, CSS, URLs, font files or scripts.
- Bounded file, layer, path, color, size and motion validation protects
  renderer complexity; source illustration is cached across adjacent beats.
- Normalized coordinates define shapes, not scientific or anatomical truth.
  Script-only generation still uses existing abstract kinetic visuals unless
  author-reviewed subject art is provided.
- The output manifest records original-vector SHA256 fingerprints and sets
  rightsManuallyConfirmedByAuthor=false for vector geometry. Copyright and
  editorial approval must be confirmed separately. publicationApproved=false.
- The wide cinematic stage now occupies about 68.5% of the 9:16 phone frame
  with a soft transparent caption veil instead of a large empty footer panel.

## Remaining roadmap, ordered

1. Automatic per-topic original assets, validated against facts and rights.
2. Fully articulated causal motions (jointed roots/limbs, deformation,
   mechanical interaction, object-specific kinematics).
3. Stronger scene direction: more composition variety, camera perspective,
   physical continuity, lighting and richness without repetitive diagrams.
4. Actual Kokoro audio evaluations, natural delivery and word-level timing.
5. Multi-topic independent QA, visual review and mobile Shorts safe zones.

This source-renderer milestone does not yet match the artistic level of the
private reference 3561.mp4. A motion percentage is not an aesthetic score.
