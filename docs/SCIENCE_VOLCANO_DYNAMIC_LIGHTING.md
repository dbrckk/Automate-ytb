# Volcano lighting after real triangulated 3D terrain

Magma's former bloom is an unmasked overlay: it brightens the air even when
a face of the volcano should receive the light. New local emissive shading
tracks the actual eruption crater and the moving tips of both lava flows,
using the silhouette/alpha of the triangulated terrain as a light receiver.

This changes the **mountain facets themselves** rather than repainting the
whole background. Emitters are deterministic and finite, using low-resolution
Pillow Gaussian fields plus cached 3D material masks; the overlay does not
touch titles, subtitles, sky, people or third-party footage.

This is still approximate 2.5D emissive light, not path-traced physically
based rendering. Validate the exported English narrated 1080x1920 full MP4,
all five scenes, before merging. No automatic YouTube publication.
