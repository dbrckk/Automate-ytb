# Quality previews: neural voice and chapter-level premium art direction

## User-visible defect and fix (14 November 2026)

The old "visual review" artifact delivered eSpeak even though the permanent
premium pipeline already supported real Kokoro; users understandably heard
a crude robotic voice. The renderer also selected exactly one three-choice
topic-hash color palette for the entire episode and reused one cached
background, so every chapter inherited almost the same blue-green look.

### Implemented in this branch

- **Real voice for qualitative previews:** the maglev review pipeline now
  installs free CPU Kokoro and uses `af_heart` with the expressive delivery
  profile; retains the original WAV as a QA artifact. The complete five-beat
  original script is now rendered rather than a two-beat excerpt, so every
  palette can be heard and seen. Any purely technical eSpeak checks elsewhere
  remain explicitly technical. Neither one proves subjective naturalness
  without listening.
- **Phrasing and pacing:** original source words are unchanged. Narration
  uses the already maintained voice-pacing module's bounded phrase-rate
  and punctuation pauses, with frame boundaries derived from generated PCM.
  `--voice-style natural|gentle|lively|expressive` is available to the same
  actual universal video CLI; the source and exact style are recorded.
- **Six reusable editorial lighting looks:** copper, amber, violet, cobalt,
  rose and emerald. The illustrated maglev story changes scene lighting and
  color accents through its authored actions. Other concrete illustration
  families use deterministic multi-chapter sequences instead of one hue
  for the whole video.
- **Performance:** atmosphere and light reflections are graded once for
  each vector art layer at source-load time. Video uses cached per-chapter
  full-resolution backgrounds rather than new gradients on every frame.
  Reflective coloring protects original geometry, window details, RGB
  source data, alpha, actor positions and recorded rights.
- **Inspectable provenance:** final render manifest includes
  `proceduralVisualPaletteEngine`,
  `proceduralVisualChapterPalettes`, and `voiceStyle`.
  Pre-existing authored JSON without the original finishing marker keeps
  its original palette behavior.

## Star-list resource review

The user-maintained catalog `dbrckk/star-list`, plus this project's
`docs/REFERENCE_VIDEO_STARLIST_AUDIT.md`, identifies:
- [hexgrad/kokoro](https://github.com/hexgrad/kokoro): already integrated
  locally; usable without paid APIs; **selected** for quality previews.
- [motion-canvas/motion-canvas](https://github.com/motion-canvas/motion-canvas):
  promising expressive 2D TypeScript motion design; **not integrated
  this increment**, as replacing the live Python actor renderer would
  add an entirely new runtime and break existing delivery.
- [FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg): already used and
  retained for real-time audio/video encoding and full decoder validation.
- [OpenBMB/VoxCPM](https://github.com/OpenBMB/VoxCPM): additional
  local TTS research candidate, not presumed free to run on GitHub CPU
  or subjectively superior without benchmark listening samples.

No external image or commercial service is automatically downloaded. No
paid generation credits were used or are required by the new features.

## Quality acceptance

1. Existing test suite and genuine H264/AAC encoded and full-decoded
   maglev video must pass in GitHub Actions.
2. Output manifest must contain two different chapter palettes from the
   genuine two-beat maglev source and `voiceEngine=kokoro`,
   `voiceName=af_heart`, `voiceStyle=expressive`.
3. The exported WAV must be actual 24 kHz mono Kokoro PCM, not a
   synthesized label over eSpeak; it must remain independently inspectable.
4. Tests must verify that at least five chapter palettes have distinct
   values, cached raster artwork changes per chapter and old unmarked
   authored stories remain accepted.
5. Human listening and visual comparison to `3561.mp4` are still
   required. These technical checks are **not** a claim of 20/20 aesthetics.

## Remaining technical-artistic debt

A small built-in illustration grammar and deterministic vector art remain
insufficient to reliably illustrate *arbitrary* topics at premium studio
quality. Better subject object geometry, asset-specific art-direction packs,
scene-editing grammar, camera choreography and human visual evaluation are
still necessary. Changing color and speaker alone does not close that gap.

## Persistent Android-friendly preview delivery

After all unit and real media checks pass, a **main-branch push** runs the
full Kokoro audiovisual review and creates an immutable GitHub prerelease
with the real MP4, captions, full-decode report, contact sheet and SHA256
ledger. The workflow performs an anonymous HTTP download and compares
SHA256 bytes before reporting a success or a permanent direct link. The
source narration WAV remains a time-limited GitHub Actions artifact for
focused human listening and is not passed off as the public final video.

A pull request never publishes a release, and no preliminary release URL
should be given to a user until the actual anonymous GET succeeds.
