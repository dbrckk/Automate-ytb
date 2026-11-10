# P5.15 — Source-painted detailed volcano materials, not an isolated edit

## Defect confirmed in actual rendered video
The source volcano remained a large faceted triangular cone with generic
star-like points in its sky; the tiny perfectly elliptical crater also
looked like a primitive icon. Optical grading and 2.5D parallax alone
could not repair the source materials.

## Shared production upgrades
- `rock_surface25d.weathered_rock()` adds cached multiscale coherent
  mineral pigmentation, branching ravines fixed in world coordinates,
  lit edges, strata and subtle internal shade variation. It preserves
  the **exact original alpha** and surface-light geometry, with no
  per-frame texture generation and no downloaded stock photographs.
- The existing physical conical heightfield is more finely tessellated,
  with the shared original weathered rock source applied once before
  actual ash, lava and narrator-directed camera animation.
- Source `science_volcano._base()` no longer injects space stars into
  geological footage. Separate diffuse volcanic ash/haze light replaces
  the point-star noise. The summit opening is now a nonuniform
  original crater silhouette, preserving the actual (540,345) vent
  attachment required by all eruption stages.
- Distinct exterior/cutaway shots retain existing pressure, gas, lava,
  eruption and rock lighting; all still output actual 1080x1920 video.

## Evidence and limits
The new dedicated CI requires actual 1080x1920 original source frames,
SHA256 manifest, an inspectable contact sheet, material/alpha/cache tests,
legacy volcano mesh and action regression, and live MP4 validation through
the general pipeline. This is **authored illustration**, not a physically
complete fluid/geologic simulation, Unreal render or proof of AAA.
No paid assets or external AI credits. Human aesthetic review still needed.
