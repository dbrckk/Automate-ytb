# Real 3D Aurora Science Shorts — Blender/Cycles CPU

## Why this is different

The existing northern-lights video used procedural 2D Pillow rigs. This new
**opt-in** path renders original 3D sources in Blender before composing each
Short, without taking paid inference tokens or requiring a PC from the editor.

The five authored scientific action stages are:

1. **Solar wind:** physically lit Sun and Earth spheres, moving curved electron
   pathways and a perspective camera.
2. **Magnetic field:** 3D field-line curves around a shaded globe plus charged
   particle paths.
3. **Atmospheric collisions:** actual spatially separated gas spheres with
   continuous excitation motion.
4. **Emission:** emissive photon geometry, oxygen-green/nitrogen-violet/light-red
   colored sources.
5. **Aurora curtains:** six layered *translucent* emissive, folded 3D surfaces,
   illuminated arctic terrain and real depth-parallax stars.

The imagery is a schematic educational visualization, not an atmospheric
simulation or an accurate spectral/altitude measurement.

## One-click generation

In GitHub **Actions → One-click YouTube preview (free)**:

- style: `science`
- resolution: `shorts`
- topic: a supported aurora/northern-lights topic with explicitly classifiable
  solar-wind, magnetic, collision, emission and curtains narration
- voice: `kokoro`; language: `en`
- `cinematic_3d: true` (optional, never the automatic default)

A dedicated workflow named **Verify real Blender 3D aurora science Short**
renders a fixed 31-second original English episode and invokes full video QA.

The one-click job picks its rendering engine by the authored scientific topic:
Blender ocean for ocean current beats, Blender aurora for aurora beats. Other
topics fail visibly instead of passing a false 3D production claim.

Output artifact includes actual encoded H.264/AAC 1080x1920 30fps MP4,
SRT/VTT, measured voice pacing, EBU R128/true-peak analysis, professional
review report, stills from the encoded MP4, and real Blender aurora contact
sheet + SHA256 manifest. No YouTube upload.

## Render reproducibility

On a Linux PC or GitHub runner with Blender/Cycles installed:

    blender --background --factory-startup -t 2 \
      --python scripts/blender_aurora_stage.py -- \
      --output build/aurora-3d --frames 18 \
      --width 600 --height 750 --samples 8

    python -m automate_ytb.aurora_stage_review \
      --folder build/aurora-3d --out build/aurora-3d/review.jpg

    export AUTOMATE_YTB_AURORA_3D_DIR="$PWD/build/aurora-3d"

The renderer outputs **18 genuinely rendered 3D poses per science action**,
then the video path interpolates between those keyframes at 30 FPS. Motion
still requires human viewing to detect interpolation ghosting; it is *not*
30 independently path-traced Blender images per second.

All 90 PNGs have exact manifest hashes, dimensions and sequence IDs. A
missing, corrupted or misattributed frame fails the job. Blender materials,
lighting, geometry and shot paths are created locally; no cloud AI assets,
passwords or proprietary downloads are involved.

## Professional acceptance

- Test and run on actual GitHub CPU runner, with enough time budget.
- Run existing 500+ safety/regression tests and actual complete MP4 QA.
- Watch the real encoded video and inspect actual image differences.
- Reject if 2D overlay dominance hides 3D, if direct emission blooms
  distractingly, if color/contrast harms text legibility, or if audio quality
  regresses.
- Do not enable globally or publish until human review.

## Latest P0 scene-world upgrade (November 4)

Previously, the visible Blender stage used a flat blue Earth sphere, a low
contrast sine-wave polar floor and isolated moving dots for the collision
sequence. The following changes are authored in the actual 3D source:

- **Planet**: procedural ocean/continent relief shading, polar ice region,
  surface bump and a separate atmospheric grazing-angle scattering shell.
  Landmass patterns are stylized, **not geographic maps**.
- **Landscape**: 64×64 actual 3D ground vertices, a ridged mountain skyline,
  altitude-specific ice/snow/granite material regions and foreground rocks
  placed *on* the ground instead of at approximate floating heights.
- **Atomic animation**: paired diatomic gas molecules with visible bonds,
  incoming charged particles timed to impacts, molecule excitation pulses
  and colored photon trajectories moving away from collisions.
- **Verification**: the renderer's manifest now records actual source-scene
  geometry counts and rejects incomplete landscapes, molecules, photons,
  planet materials and auroral surfaces. The human contact-sheet review
  includes those counts, not a fabricated artistic score.

All improvements use original Blender materials/geometry and GitHub Actions
CPU, with no third-party asset/license or paid inference dependency.
These are explanatory visualizations, not plasma physics simulations.

## Remaining work

Increase true 3D temporal sampling and use physical light-scattering materials
when CPU cost allows; improve geometry, camera ease and realistic night-sky
color management; introduce 3D volcano geology and lightning next.
