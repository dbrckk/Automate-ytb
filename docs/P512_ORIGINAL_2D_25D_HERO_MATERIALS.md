# P5.12 — Reusable high-detail original 2D/2.5D hero materials

## Visual defect and direction
Even after shared organic clouds and P5.10 light/water/magma ribbons,
large raindrops and the sunlight source were plain filled ellipses
with a handful of highlights. They dominated scenes and still looked
like infographic slides rather than original illustrated objects.

## Change in the VIDEO CREATION PROCESS
- New independent original source-art bank `hero_materials25d.py`
  produces **cached**, deterministic, antialiased, alpha-safe glass and
  luminous solar surfaces, without network, stock images, 3D, paid credits,
  or per-frame random noise.
- Glass uses object-space material shading, approximate Fresnel rim,
  chromatic colored interior, caustic highlight and layered translucency.
  It is qualitative, **not a physically exact ray-tracing calculation**.
- Solar painting uses an emitting disc, soft halo, uneven material texture
  and a directional highlight. Color is an artistic representation.
- **Every** rainbow refraction, internal reflection and emergence video
  draws the same reusable original glass hero, while the solar beat
  reuses the solar source material; both keep the independently animated
  P5.11 atmospheric layers and the previously implemented P5.10 optical
  light trajectories.
- The old public draw-only storyboard interface remains compatible.
  Full native portrait renderer passes the actual RGBA canvas to opt
  in to detailed 2D/2.5D source materials. No single-episode hardcode.

## Validation and honesty
Dedicated tests require bounded input, image determinism/cache identity,
true RGBA interior gradients, untouched alpha outside the sphere,
and actual original 1080x1920 cross-scene generation.
Existing rainbow, organic 2.5D, all-topic and complete H264/AAC video
workflow checks remain in CI. Human visual assessment remains necessary:
these are higher-complexity native illustrations, not photorealism
or an automatic certification of AAA-quality film.

Next: semantic authoring of richer original natural forms and characters
across other scene families, with actual full MP4 comparison at fixed
storyboard/voice/times before aesthetic signoff.
