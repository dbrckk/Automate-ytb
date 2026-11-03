# Shaded geometric volcano terrain (science video)

The original volcano film previously used a manually authored triangular 2D
silhouette with a few decorative facets. The real source has been replaced in
both exterior and geological-cutaway scenes by a cached **triangulated 3D
heightfield**: 21 radial rings × 72 segments, concave summit crater, irregular
erosion channels, cross-product normal lighting, subtle lithologic strata,
forward-facing triangle culling, and a safe polygon mask.

This is deliberately **not** Blender/Cycles, photogrammetry, true PBR or
photorealistic video. It is a substantial, dependency-free geometric upgrade
that works in CPU-only GitHub Actions and without paid credits. The darker
underlying cone seals the cutaway to avoid holes. The independent causal lava,
pressure, rising magma, explosions, camera and fixed readable typography
continue to render as before.

Validation gates: geometric deterministic/cached-mesh tests, main pipeline
unit and FFmpeg tests, and a real 1080x1920 English Kokoro volcano episode QA
with decoded storyboard. Review the new decoded frames alongside baseline
release \`science-preview-volcano-eruption-41658232278\` for visual judgment.
Do not claim the studio-grade Blender milestone is complete until its
full 3D-material backend renders an actual complete movie.
