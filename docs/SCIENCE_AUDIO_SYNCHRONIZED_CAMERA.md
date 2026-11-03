# Speech-phrase-synchronized scene-camera events

For volcano and aurora science Shorts, audio-mode Kokoro narration already
produces real **synthesized phrase** start/end timestamps in captionSegments.
This change reuses those existing markers and the scene action classifier:
the first synthesized phrase mentioning the current physical event locates a
temporal visual cue. Its midpoint controls a compact, smooth camera emphasis.

Crucially, this is **not word-level alignment**. An event inside a long phrase
can still lead or lag the precise spoken keyword. The algorithm never claims
sub-120ms accuracy, re-synthesizes audio, reorders scene events, or adds paid
models. The pulse is bounded away from shot edges; absent cues retain the
authored deterministic v2 camera position. Both Android-safe overlays and
caption SRT timings remain unchanged.

See tests/test_science_audio_cues.py for marker/schema/fallback coverage and
tests/test_science_stage_director.py for explicit boundary/crop checks.
