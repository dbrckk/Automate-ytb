# Universal video editorial pipeline — all styles

This improvement targets **every approved-video style**:
original cartoon characters, documentary, cinematic storyboards, scientific
animations, landscape videos and native 9:16 Shorts.

## Existing issues

The earlier montage applied the same hold-frame dissolve between all scene
boundaries. When subjects were visually unrelated, this double-exposed
titles, characters and colored graphics. In generic documentary/cinematic
scenes without a character rig, the FFmpeg camera always performed the same
mechanical, centered zoom, stopping after its zoom cap.

## New all-style default

The editor samples actual outgoing and incoming **decoded MP4 frames**.
Two nearby compositions may keep a soft 320 ms dissolve. Large RGB/luminance
differences and dark-to-bright jumps result in a **clean cut** instead.
Every decision is reported under \`render-report.json.transitions.boundaries\`
with measured RGB/luma differences and the chosen method.

The clean-cut and dissolve paths do not change a scene's duration, the
timing of the narration, subtitles, scene starts, music or audio mastering.
For science Shorts the existing UI-safe dissolve matte remains in place
whenever a dissolve is selected. An explicit user choice of \`cut\` or
\`dissolve\` overrides adaptive decisions and preserves prior behavior.

**Fallback image motion**: approved still images used by documentaries,
cinematic scenes or unrigged cartoons get conservative, shot-directed
camera paths (wide, medium, close-up, macro, low angle, shoulder) with
bounded 2D zoom and slight travel. This replaces the identical centered
camera used for all stills. The engine does **not** misrepresent these
scenes as real articulated animation, real 3D or volumetric parallax.
Animated owl/forest and science rigs retain their existing real internal
motions rather than applying a redundant pan or zoom.

## Access from Android

In **GitHub Actions → One-click YouTube preview (free)**, the default
\`transition\` is now \`adaptive\`; \`cut\` and \`dissolve\` are still options.

Equivalent no-manual-video-edit CLI:

    python -m automate_ytb.episode \
      --plan build/scene-plan.json --output build/video \
      --style cinematic --voice kokoro --language en \
      --transition adaptive --render-profile high

Styles supported: \`cartoon\`, \`documentary\`, \`cinematic\`, \`science\`.
Science 9:16 is still a distinct approved source requirement and cannot
be faked from landscape cards.

## Test contract

- Real decoded source videos decide cuts/fades; no invented AI scene cuts.
- Real FFmpeg 24fps and 30fps clips preserve frame counts and duration.
- No outgoing science title or subtitle is blended into its incoming
  title/caption band.
- The same short real videos can be used across editorial styles; test
  actual rendered previews at least once for each supported family.
- All approvals remain human; the decision report never claims the final
  montage is professionally edited or factually/legally verified.
- No credentials, paid tokens or external video assets are introduced.

## Remaining professional work

Replace documentary/cinematic draft-card visuals with scene-specific
original source assets and real animated subjects. Improve editing by
speech-phrase events and meaningful action beats instead of relying solely
on image dissimilarity. Upgrade source-video media analysis and human
review, and verify portability on long videos with hundreds of scenes.
