# Cinematic stage director (shared original 9:16 science)

The new scientific stage camera is **shared** by volcanic and aurora episodes,
not a movie-specific sequence of static slides. Each narrative beat gets its
own smooth 30 FPS pose: close underground chamber shots, upwards follow of
magma, ash-plume framing and wide lava. Northern Lights scenes move around the
Sun, magnetic field, excited oxygen/nitrogen, and flowing curtains. The same
source-space magnification is used on both axes, and all source coordinates
remain within each original frame. No stretched sprites or transparent borders.

This is an **art-direction improvement**, not photorealistic 3D or neural
video. The expensive 1080×1380 frame is painted once per movie frame, then
reframed with a single Pillow affine resample. Headline/progress/subtitles are
composited later at fixed native-portrait coordinates. Original English Kokoro,
music, timings and SRT timestamps are untouched. All existing licensing and
unreviewed GitHub release checks remain required. CPU-only and no paid APIs.

Release checks: science-stage-director camera crop/continuity tests, volcano
and aurora native-frame regressions, and real English Kokoro MP4 renders on
Actions. The checks confirm reproducibility and decoder validity, not audience
retention or professional cinematic appearance.
