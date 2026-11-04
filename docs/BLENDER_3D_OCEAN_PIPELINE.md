# Original Blender 3D Ocean Stage — production notes (2026-11-04)

## Delivery contract

A separate **optional** real-3D visual track, entirely open-source and offline:
Blender renders original animated 3D seabed geometry, wave meshes, flowing
curve geometry, ice/thermal/solar props, moving perspective camera, lights and
Cycles physically based surface shaders. The existing reliable Pillow path
remains the default. No paid inference, remote asset service, API credentials,
proprietary characters, or YouTube publishing is involved.

- Select **Actions → One-click YouTube preview (free) → Run workflow**,
  set style=science, resolution=shorts, an authored ocean-current topic,
  and **cinematic_3d=true**. English + Kokoro + expressive remains supported.
- Run **Verify real Blender 3D ocean science Short** to obtain a fixed,
  reproducible English narrated 30-second full-production release candidate.
- Artifacts include MP4, subtitles, voice comparisons, QA reports, a five-panel
  real-3D contact sheet and the verified Blender manifest.
- No action publishes the video. Human listening and frame review are mandatory.

## Rendering boundaries

- A **Cycles CPU** pass makes ten actual Blender camera poses per semantic beat
  (solar, wind, coriolis, sinking, heat), 600×580 samples, 8 Cycles
  samples. The animated 3D frames are time-blended behind the existing
  explanatory diagrams for smooth **30 fps video export**; this is NOT
  30 distinct physically path-traced 3D frames per second. Fast motion can
  ghost between camera samples. Increase scene samples/resolution only after
  measuring runner latency and artifact size.
- The normal non-3D mode never installs Blender. In 3D mode, missing,
  tampered, wrong-sized or incomplete frame sets **fail**, never quietly
  fall back to 2D while claiming 3D.
- The 3D environment remains a **stylized scientific illustration**:
  it is not photogrammetry, a geospatial map, fluid CFD or calibrated
  atmosphere. Existing captions explicitly say schematic/not to scale.
- The 3D visuals sit within the 920×890 scene band (x=80..1000,
  y=600..1490); title, speech captions and mobile-safe controls are never
  replaced by rendered geometry. Meaningful interaction effects still
  follow synthesized caption-*phrase* boundaries, not invented word times.
- Blender is CPU-heavy; GitHub-hosted runner availability, Debian package
  version and work limits must be checked through actual CI, not assumed.

## Reproduce locally

Requires Blender with bundled Cycles, Python 3.11+, Pillow and FFmpeg.

    blender --background --factory-startup -t 2 \
      --python scripts/blender_ocean_stage.py -- \
      --output build/ocean-3d --frames 10 \
      --width 600 --height 580 --samples 8

    python -m automate_ytb.blender_stage_review \
      --folder build/ocean-3d --out build/ocean-3d/review.jpg

    export AUTOMATE_YTB_OCEAN_3D_DIR="$PWD/build/ocean-3d"
    # Run normal episode CLI, with a 9:16 science ocean-currents scene plan.

The manifest stores exact SHA256 for every PNG and a narrow whitelist of
five beat directories; no external paths or weak provenance fallback.

## Accept / reject

1. GitHub CI: existing 500+ tests plus dedicated Blender full MP4 + Kokoro +
   FFmpeg QA complete successfully on the *current* PR head.
2. Five Blender scene poses demonstrably change; real frames and manifest are
   present; no duplicate/frozen imagery.
3. Listen to narration, review actual MP4 frames and verify that ocean labels
   remain legible against 3D scenery.
4. Compare visuals against prior 2.5D baseline. If the 3D pass reduces
   clarity or runner resources are excessive, do not enable by default.

## Next genuine improvements

- Move from sample-frame interpolation to motion-vector-based resampling or a
  render farm for higher true 3D temporal sampling.
- More detailed volumetric lighting, bathymetric structures, underwater flora
  and material authoring, while preserving source rights and visual meaning.
- Speech-driven camera choreography and sound design keyed to real narration.
- Art direction and subjective voice listening; numerical QA cannot certify
  premium appearance or a human-like voice.
