# Solar Storm — real-video visual review

The production workflow `.github/workflows/solar-storm-documentary.yml` renders
an original **English 1080×1920, 30 fps H.264** science Short with **Kokoro**
narration and properly attributed NASA SVS video.

## Final downloadable artifact

On Android, open **Actions → Produce Solar Storm short — NASA + Kokoro**.
The successful run uploads `solar-storm-english-short` including:

- `Solar_Storm_Short_EN_1080x1920.mp4`: the encoded release candidate.
- `subtitles_en.srt`: actual recorded narration aligned through Whisper;
  unmatched words remain explicitly flagged in `word_timestamps.json`.
- `contact_sheet.jpg`: six real decoded MP4 frames sampled at the middle of
  each spoken scene, **outside** the published video.
- `review_frames.json`: frame positions, darkness/contrast statistics,
  and possible visual duplication warnings, including nonadjacent scenes.
- `qa.json`: technical stream checks and the visual review result.
- `publication.txt`: source attribution and limitations.

The pipeline **fails** when it cannot decode any sampled MP4 scene or encounters
an entirely black sampled frame. Similar-looking scenes are warnings because
different NASA shots may legitimately share the same solar imagery.

The contact sheet is for rapid mobile review. It does **not** establish that
scientific narration matches every shot or that subjective production quality
is adequate. Check the entire MP4 with sound before publishing. Technical QA
and a green workflow do **not** mean editorial approval:
`editorial_approved: false` is retained deliberately.

### No changes to the finished viewer experience

The contact sheet and diagnostic labels are separate files. They never add
frame numbers, internal counters, slides, a watermark, or telemetry to the
published Short. External NASA media remain credited in the accompanying
publication description; production is local/open source apart from licensed
NASA source retrieval, and does not invoke paid AI image APIs.
