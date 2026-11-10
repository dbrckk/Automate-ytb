# P5.16 — A single real 2.5D geological conduit source for all magma animations

## Defect
Previously the rock cutaway painted an exactly vertical column. Separately,
the ascent beat used a rounded-rectangle molten region and a second unrelated
straight-line glow. Painting more details on the mountain could not fix this
geometrical disconnection.

## One reusable source-of-truth geometry
- `volcanic_conduit25d.conduit_center_x(y)` is a smooth, deterministic
  source-space centerline with multiple bounded low-frequency bends. It meets
  the exact fixed coordinates of the crater vent at (540,345) and the
  underground chamber attachment at (540,1028).
- `conduit_path()`, `conduit_mask()`, `draw_rock_conduit()`,
  and `active_conduit_path()` all reuse this source, rather than
  inventing independent art/masks/motion curves.
- The existing geological cutaway now paints source-aware shaded walls.
  The ascent beat drives a molten fill, locally centered flowing highlights,
  a soft glow and the origins of three fractures from this exact conduit.
- The magma front moves monotonically upward with the narrated beat,
  never passing beyond its physical cutaway mask or detaching from rock.
  Existing chamber/gas/pressure logic is unchanged.

## Actual verification
The original GitHub Actions source-frame job runs real native 1080x1920
`PortraitScienceScene` at early and late ascent times, captures SHA256
hashes, exports a phone-scale contact sheet and checks original earlier
volcano tests. There is no per-frame random noise, paid AI or 3D.
The art explains the principle; it is not an accurate geological cross
section or a CFD simulation. Human visual review is still required.
