# P5.17 — Original organic volcanic reservoir for 2.5D videos

## Actual short-video source-art defect
The existing geology had a curved vent (P5.16) but it still ended in a
regular colored elliptical chamber. The gas, pressure waves, painterly
magma substrate and dark rock rim all used different ellipses. These
made a prominent underground focal element look like a presentation
graphic even when animated.

## Source material work, shared by every future episode
`volcanic_reservoir25d` now supplies one deterministic, band-limited
organic geological silhouette with cached native RGBA rock and molten
source materials. The exact same contour is used by the rock cutaway,
the liquid and gas clipping mask, the contact rim and circulating
pressure waves. The existing P5.16 conduit still ends inside this
reservoir without moving its summit connection.

The cached source rock has material thickness, staggered sediment
edges, chromatic veins and a recessed magma basin. Cached molten art
has layered low-frequency thermal bands; animated circulating lava
cells now use irregular polygons instead of identical ellipses. The
material is created once per process; only physically linked convection,
gas and pressure evolve per frame.

## Verification
The dedicated workflow runs the original magma, pressure and ascent
regressions, plus new cache, mask, invalid input, and exact native
1080×1920 `PortraitScienceScene` rendering tests. It saves genuine
source-frame PNGs, SHA-256 hashes and a phone-scale contact for manual
assessment. Regular full pipeline/voice/MP4 QA is separate and required
before merge.

The source is original 2.5D science illustration. No paid generation,
stock downloads, 3D renders, claims of a geomechanical solver, or
publication approval.
