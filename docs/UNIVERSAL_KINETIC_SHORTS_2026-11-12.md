# Universality-first kinetic Shorts (2026-11-12)

## Implemented now — original 9:16 animated format, not a slide generator

`automate_ytb/universal_kinetic.py` introduces an **additional, opt-in production
route**. Existing 2.5D science, animation, narrated video and delivery workflows
are unchanged. The new route reuses the project's native `SpeechEngine`,
`MasterTimeline`, `FoleyEngine`, final audio mix and `shorts_delivery` QA.

A narrative story is an authored JSON object with `schemaVersion: 1`, a
`topic`, `language` (`en` or `fr`) and 2–12 `beats`. Every beat has
`title`, `narration` and one of four visual grammars:

| `kind` | Required visual data | Actual time-dependent graphic |
|---|---|---|
| `measure` | `label`, `value`, `scaleMax`, `unit` | Numeric amount and proportion animated from authored data |
| `compare` | `left`, `right`, `leftValue`, `rightValue`, `unit` | Two bars on the same bounded scale; avoids misleading independent maxima |
| `sequence` | `steps` (2–5 strings) | Causal stages progressively activate along a connected path |
| `concept` | `nodes` (2–5 strings) | Persistent central relationship network with orbital motion |

The topic is **not** used as a keyword switch that invents facts. Narration,
numeric data and labels must be authored or produced and checked by an upstream
research/script generator. Optional `sources` per beat preserve link provenance;
the engine does not claim that URLs prove the text, nor that facts were reviewed.

## Actual command

~~~bash
python -m pip install -e '.[speech]'
sudo apt-get install -y ffmpeg espeak-ng fonts-dejavu-core
automate-ytb-short \
  --brief examples/universal_web_request.json \
  --output build/web-request-short.mp4 \
  --voice kokoro --width 720
~~~

No paid services, proprietary content, remote image API or token are required.
Kokoro needs its downloadable open model once on a machine with Internet.
For a CPU-only fast fallback without model download, use `--voice espeak`
(**draft only, not a premium-sounding voice**). `--width 1080` produces
1080×1920; both 720 and 1080 use 30 fps and H.264/AAC. Output
`<stem>.json` records the actual technical QA and unreviewed editorial status.

## Why it improves the pipeline

- 2–12 authored beats can explain web infrastructure, historical stages,
  processes, economics, or physical measurements using the **same engine**.
- Speech is synthesized **before** picture timing. Scene boundary positions
  come from actual PCM sample counts rather than an assumed TTS speaking speed.
- The same immutable cross-beat timeline drives the on-screen progress indicator
  and sample-indexed causal foley triggers; there is no per-clip counter reset.
- The original procedural bed runs across the full story, not as a scene-reset
  8-second music loop. Voice, bed and foley are mixed through the existing
  limiting, loudness-normalized production audio path.
- Numeric labels and underlying bars share the same input value and
  interpolation. A missing value results in a validation error rather than
  an invented statistic.

## Limitations — not yet reference-grade across all topics

1. The `concept` grammar is still an abstraction: arbitrary animals,
   people, devices, historical locations and complex 2.5D objects require
   original licensed imagery or a rigged asset generator. The new renderer
   does **not** pretend to generate those.
2. A topic title alone does not supply accurate narration or evidence;
   universal subject research/story generation is a separate, currently
   missing module. The included example deliberately marks numeric timings
   as hypothetical.
3. Subtitle segmentation is proportional to a whole beat, **not
   word-aligned**. The manifest explicitly identifies this limitation.
4. A technically accepted MP4 is not a professional subjective quality score.
   Listening/visual A/B review against the privately supplied reference
   remains essential, along with Android safe-area verification.
5. The reference video is private user data. Never publish its audio,
   video frames, or copied assets to GitHub.

## Next production priorities

- **P0:** add an upstream sourced, topic-agnostic StoryGraph and original
  script planner; user enters a topic, the process researches and validates
  facts before rendering. No fabricated citations.
- **P1:** introduce a richer visual object/asset grammar (rigged 2.5D
  characters, maps, physical transformations, complex graphs) and native
  render adapters to the same persistent timeline.
- **P2:** replace approximate subtitle timing with PCM phrase- and eventually
  word-level alignment; attach scene-specific Foley and score motifs.
- **P3:** automated multi-topic batch benchmark with authentic 30-fps motion
  QA, audio loudness, budgeted CPU/RAM and human review gates.

## Reproducible checks

~~~bash
python -m unittest discover -s tests -p test_universal_kinetic.py -v
# Run using GitHub Actions: Universal kinetic Short smoke
~~~

That smoke test uses two original non-science beats and **real local eSpeak,
FFmpeg, AAC and MP4 decoding**; it never tests arbitrary internet research.
