# Universal video editorial pipeline — all styles

This improvement targets **every approved-video style**:
original cartoon characters, documentary, cinematic storyboards, scientific
animations, landscape videos and native 9:16 Shorts.

## Existing issues

The previous montage applied the same hold-frame dissolve between all scene
boundaries. When subjects were visually unrelated, this double-exposed
titles, characters and colored graphics. The current production renderer
already has genre-aware safe camera paths (`camera_motion.py`); this release
does not replace that working engine or pretend to invent 3D animation.

## Adaptive mode in mobile and multi-source production

When `adaptive` is selected, the editor samples actual outgoing and incoming **decoded MP4 frames**.
Two nearby compositions may keep a soft 320 ms dissolve. Large RGB/luminance
differences and dark-to-bright jumps result in a **clean cut** instead.
Every decision is reported under `render-report.json.transitions.boundaries`
with measured RGB/luma differences and the chosen method.

The clean-cut and dissolve paths do not change a scene's duration, the
timing of the narration, subtitles, scene starts, music or audio mastering.
For science Shorts the existing UI-safe dissolve matte remains in place
whenever a dissolve is selected. An explicit user choice of `cut` or
`dissolve` overrides adaptive decisions and preserves prior behavior.

**Still-image scenes**: the existing `automate_ytb/camera_motion.py`
already handles bounded directed zoom and camera travel for licensed images,
whereas the original forest, owl and science rigs contain real authored
internal movement. This PR leaves those pathways untouched. Real footage is
never mislabelled as generative AI or new 3D art.

## Access from Android

In **GitHub Actions → One-click YouTube preview (free)**, the default
`transition` is now `adaptive`; `cut` and `dissolve` are still options.

Equivalent no-manual-video-edit CLI:

    python -m automate_ytb.episode \
      --plan build/scene-plan.json --output build/video \
      --style cinematic --voice kokoro --language en \
      --transition adaptive --render-profile high

Styles supported: `cartoon`, `documentary`, `cinematic`, `science`.
The low-level Python `render()` keeps `dissolve` as its backward-compatible default;
Android's one-click workflow, the episode CLI, and the multi-video auto-editor
select `adaptive` by default.
Science 9:16 is still a distinct approved source requirement and cannot
be faked from landscape cards.

## Test contract

- Real decoded source videos decide cuts/fades; no invented AI scene cuts.
- Real FFmpeg 24fps and 30fps clips preserve frame counts and duration.
- No outgoing science title or subtitle is blended into its incoming
  title/caption band.
- Validate with real H.264 FFmpeg red/blue hard-cut and visually similar dissolve.
- Verify actual end-to-end cartoon, documentary and cinematic previews
  with the independent release candidate workflow.
- All approvals remain human; the decision report never claims the final
  montage is professionally edited or factually/legally verified.
- No credentials, paid tokens or external video assets are introduced.

## Remaining professional work

Replace documentary/cinematic draft-card visuals with scene-specific
original source assets and real animated subjects. Improve editing by
speech-phrase events and meaningful action beats instead of relying solely
on image dissimilarity. Upgrade source-video media analysis and human
review, and verify portability on long videos with hundreds of scenes.
