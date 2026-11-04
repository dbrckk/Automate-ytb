# World-space moving camera for the volcano eruption

**Implemented:** The eruption's source mountain is a true cached 3D
heightfield, reprojected *every video frame* instead of using a single
pre-rasterized rock plate. The renderer evaluates 3D vertices, face normals
and face visibility from a continuously orbiting camera, then paints the
depth-sorted triangles. The summit remains fixed at the ash/lava vent, so
pre-existing cinematic plume/ejecta/shadow VFX do not jump away from their
physical origin.

- World-space yaw varies smoothly over 19.5 degrees across the full eruption
  shot; a shallow per-depth foreshortening adds near/far parallax.
- The rock uses deterministic lithologic variation, roughness and normal-based
  Lambert lighting already established by `science_volcano_mesh`.
- The source remains 1080×1380; no new inference, paid service, Blender runtime
  or GPU. The original 9:16 editorial and Kokoro voice timing stay unchanged.
- The 3D mesh is drawn *between the original environment and crater/foreground*
  and then the existing causal eruption effects, avoiding a duplicated flat
  mountain behind the moving geometry.
- Only the eruption hero shot receives the new animated mesh initially. The
  cutaway scenes retain their stable, cached baseline, and lava stays
  rock-guided on its existing fixed geography.
- Stage artwork and generated-video fingerprints change so old 2.5D clips
  cannot be silently reused as the new 3D camera output.

**Not claimed:** physically correct ray tracing, Blender/PBR, measured 3D
occlusion, physically accurate volcanic turbulence, photorealism or AAA-level
assets. This renderer uses an orthographic-style camera, face-depth painter
ordering and approximate depth foreshortening to stay practical on free
GitHub Actions CPU runners. Editorial human inspection of full decoded
H.264 still decides acceptance.

## Acceptance
`python -m unittest discover -s tests -p 'test_science_volcano_3d_camera.py'`
and the full GitHub Actions CI plus 34-second real English Kokoro volcano
workflow. Validate dynamic camera geometry and crop boundaries as distinct
from inherited 2D camera pulses.
