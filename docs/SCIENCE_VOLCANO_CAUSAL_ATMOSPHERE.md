# Causal volcanic ash lighting and atmosphere

This update makes the ash column interact with the pre-existing geometrically
projected rock mesh in the **eruption** shot. Previously the volcanic plume
moved in front of the mountain but the mountain received no ash-driven shadow.

`science_volcano_atmosphere.cast_plume_shadow` creates a moving, expanding
shadow field based on the existing summit origin. The field is multiplied by
the real projected terrain's alpha mask; neither the open sky nor the 9:16
caption bands are darkened. The source-local incandescent crater illumination
is then composed *after* the ash shadow, preserving the dramatic color
contrast between the hot vent and cooled rock.

`draw_windborne_ash` adds a small independent near-field pass with
deterministic emission times, updraft, horizontal wind and quadratic settling.
This is distinct from the already implemented high-altitude plume and sharp
ballistic rock fragments. It does not rely on a static photograph, stock
texture, API call, or paid GPU inference.

The two fields are computed at 270×345 and rescaled once. The original
continuous 30 FPS video timing, English Kokoro voice, phrase-based camera
emphasis, captions and human-only YouTube publication are unchanged. Science
art and clip-cache versions are incremented to invalidate old results.

**Validation contract:** real full volcano MP4 through GitHub Actions,
deterministic masked terrain shading and ash motion checked, review images
and English audio listened to before any quality claim. The effect remains
stylized 2.5D, not volumetric CFD or PBR ray tracing.
