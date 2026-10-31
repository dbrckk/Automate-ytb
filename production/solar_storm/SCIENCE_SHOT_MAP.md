# Solar Storm — scientific scene-to-footage contract

This is the source-verified storyboard for `render_short.py` (six spoken scenes,
13 shots, English NASA/Kokoro Short). It was revised after inspecting the
**actual previously encoded MP4**, not only the screenplay.

| Spoken scene | Allowed video subjects | Authored source plan |
| --- | --- | --- |
| 1: Sun-to-Earth opening | Solar observational footage | NASA SDO 131 Å, 304 Å |
| 2: Extreme-UV observations | Real solar imagery (false-color) | SDO 171 Å, 131 Å |
| 3: Coronal mass ejection launch | SDO eruption **and NASA Sun-origin CME animation** | SDO 304 Å, NASA CIL `CME.webm` |
| 4: Earth's magnetic shielding | NASA CIL Earth-only magnetosphere animation | Two distinct moments of `H_0219_VC_Animation_Earth_Only.mp4` |
| 5: Aurora and satellite disruptions | Aurora observation and space-technology animation | NASA aurora, impact animations 01 and 02 |
| 6: Solar connection conclusion | Aurora and solar observations | NASA aurora, SDO 171 Å |

## What was wrong in the previous complete output

The original `cme` key pointed to
`H_0219_VC_Animation_Earth_Only.mp4` (NASA SVS 20297). It depicts
Earth's **magnetosphere**, although scene 3's narration and graphic describe
**plasma being launched from the Sun**. The resulting real MP4 showed
Earth's magnetic shield three shots in a row, beginning during the wrong
spoken concept. Technical codec QA could not detect this factual mismatch.

The revised source `cme_launch` is NASA CIL's `CME.webm`
(SVS source page 13029, GSFC/CIL/Krystofer Kim):
https://svs.gsfc.nasa.gov/13029/
The original Earth-only animation is now named `magnetosphere`,
with its genuine role made explicit (SVS 20297):
https://svs.gsfc.nasa.gov/20297/

The `validate_storyboard()` check runs **before any media download or
Kokoro synthesis** and refuses mismatched science roles. A separate
role mapping prevents later renaming from reintroducing the error.
The new NASA solar animation is a **conceptual visualization**, not
real SDO footage or a recording of a single storm event.

The CME animation has an authored horizontal focal crop so that the
Sun's limb and solar ejecta remain visible in native 9:16 portrait;
this framing still requires review using the actual rendered MP4.

## Release verification

After merging, the existing push-triggered Solar Storm GitHub Actions
workflow must produce a new real MP4, `shot_contact_sheet.jpg`,
`shot_review.json`, the 6-scene contact sheet and complete audio QA.
The 13-shot storyboard validator is **not** proof of artistic quality,
synchronization or that every video frame depicts the intended event.

Do not republish the earlier 35.07-second version as the corrected scientific
storyboard. It is visually and technically valid but contains the mismatch
described above. Source credits (NASA SVS 13029, 14536, 20297, 14956,
15077) must remain attached to any release.

## Cinematic camera moves (original FFmpeg, no source retiming)

`camera_motion.py` authors exactly thirteen deterministic camera presets.
The renderer normalizes each input clip to 30 fps **before** scaling,
cropping or zooming. The camera then makes a gentle optical push-in and a
small horizontal/vertical tracking move over the **real NASA video frames**,
without changing the image aspect ratio, clip duration or spoken pacing.

- SDO solar observations: a subtle 9:16 push-in helps resolve visible detail.
- Sun-origin CME conceptual animation: the crop follows the source's Sunward
  focal area, not the center of Earth's magnetosphere.
- Earth field, satellites and aurora: a restrained, centered camera respects
  the original subjects and preserves explanatory context.
- Per-shot `camera` metadata is stored in `production_report.json`, including
  the exact FFmpeg filtergraph used, frame rate and focal subject.

The feature is checked by a **real encoded static-source H.264 test**:
frames sampled at two times must visibly change from the animated camera,
while the MP4 remains 1080×1920, 30 fps and retains its correct duration.
The original NASA videos are not modified. Motion is not a substitute for
full phone playback and editorial examination of the final MP4.
