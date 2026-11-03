# Volcano VFX — emitted ash, stratified plume and ballistic ejecta

The **volcanic eruption** shot now has an original continuously emitted ash
column rather than soft gray disks placed at arbitrary coordinates. Crater
origin is fixed at stage (540, 345). 162 stable emitters produce quantized,
reusable shaded billows with coherent upward drift, expansion, fade-in and
fade-out, and wind advection. 210 independent fine-ash motes share the same
volcanic source. Billows are composed at 270×345 and upsampled once per 1080×1380
stage; there is no large full-resolution per-frame Gaussian filtering.

135 tephra emitters have source-anchored birth times, signed lateral velocity,
vertical initial speed, downward gravitational acceleration and glowing trails.
All smoke and ejecta parameters have deterministic clocks and hard bounds.
There are no textures, paid services, models, or external asset licenses.

An original crater light still modifies the actual projected rock faces,
not the sky. The original English Kokoro narration, source facts, real captions
and soundtrack remain unchanged. Stable GitHub Release deliverables are
still an explicitly **unreviewed preview**, not an automatic YouTube upload.

**Limitations:** Stylized 2.5D ash, not physically calibrated fluid dynamics or
true ray-marched volumetrics. Quality and visual performance must be inspected
on decoded frames from the real MP4, not inferred from passing unit tests.
