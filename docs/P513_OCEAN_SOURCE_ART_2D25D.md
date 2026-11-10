# P5.13 — Improved original 2D/2.5D illustration sources for future ocean films

This modifies the **video creation pipeline**, not an individual episode.
Previously the sun, temperature reservoirs, wind material and polar ice in
ocean science remained flat circles, cards and four-point polygons.

The reusable `hero_materials25d.py` now contains deterministic, cached
`thermal_pool` sources for warm/cool media and a translucent multi-facet
`ice_floe` above/below the schematic waterline. Full native
`science_storyboards.py` scene rendering reuses the already authored
`solar_disc` (previously integrated into rainbows) and shared
`organic_environment25d.water_caustics` in wind. The solar region
uses three original painted material pools. Heat transport uses two
high-contrast source-painted reservoirs; dark labels remain readable.

This affects the actual solar, wind, sinking and heat episodes.
Coriolis remains a deliberately schematic vector explanation;
no geographic/CFD precision or false 3D representation is claimed.
The old draw-only API remains compatible. The source art stays cached
between native 30fps frames, with no paid services, remote imagery,
external stock, per-frame random noise or retiming of Kokoro narration.

CI checks real multi-topic source images, deterministic alpha safety,
original audio/subtitle timings and full encoded MP4 regression.
The figures remain explanatory illustrations, **not** proof of an
ultra-realistic look; human phone-scale MP4 inspection is required.
