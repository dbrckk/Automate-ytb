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

## Direct entry from any **original script** — no storyboard JSON to write

The second input route derives descriptive concepts and optional sequential
steps from the **exact original narration**. It never fabricates a measured
value, historical date, physical unit or citation. Each paragraph becomes
a narrated beat; a single paragraph with multiple sentences is also supported.
This is a useful cross-topic fallback, not a semantic scene generator that
can draw an authentic animal or city from scratch.

~~~bash
automate-ytb-short \
  --topic "A seed comes to life" \
  --script-file examples/universal_seed_story.en.txt \
  --language en --voice kokoro --width 1080 \
  --output build/seed-short.mp4
~~~

A `build/seed-short.story.json` file records the compiled editable storyboard,
followed by `build/seed-short.json` for the video production report.

For Android without local rendering: open
[Universal kinetic Short smoke](../.github/workflows/universal-kinetic-smoke.yml)
in GitHub Actions, choose **Run workflow**, and enter **both** `topic`
and `original_script`, with each narrative paragraph separated by a blank
line. Choose `voice=kokoro` for a free neural narrator (optional one-time
download and CPU dependencies, no paid API token) or `voice=espeak` for a
fast robotic draft. Automated PR smoke tests always use eSpeak to keep
CI lightweight; manually dispatched runs with original scripts can select
Kokoro. The command above is the same neural-voice engine. An empty
`topic`/`original_script` pair runs the repository-owned regression
examples. A topic alone deliberately fails: factual narration must not be
invented without evidence.

The workflow produces two original unrelated subjects (an infrastructure
explanation and a nature story), runs real FFprobe preflight, and saves a
side-by-side quantitative motion/loudness report. It does not copy or
rehost the private reference media. Videos and metadata are downloadable
from its Actions artifact for 14 days; this is **not** an archival permanent
release link.

## Verified multi-topic media and visual-quality gap

A real GitHub Actions run has encoded original 720×1280, 30-fps H.264/AAC
videos for a network explainer (37.600 s) and a nature process (13.967 s).
Audio includes real eSpeak narration, a procedural bed, and original
event-triggered SFX. The measured output of this cross-topic smoke was:

| Encoded sample | Median changed pixels, 250-ms window | Mean | EBU R128 loudness | True peak |
|---|---:|---:|---:|---:|
| Web request | 1.481 % | 1.926 % | −16.1 LUFS | −1.5 dBTP |
| Seed story | 1.099 % | 1.230 % | −16.1 LUFS | −1.5 dBTP |
| User-private reference baseline | 9.298 % | 11.328 % | −14.8 LUFS | **+0.5 dBTP** |

The output is still **too diagram-like** and nowhere near the reference's
quality of subject animation. No scalar motion target alone proves quality.
The private reference has a higher-than-desirable true peak; do not copy it.
The benchmark was calculated from the **real encoded media**. It is
included in the downloadable workflow artifact, not inferred from story JSON.

## New reusable premium-art path: real original 2.5D layers

`universal_art25d.py` brings **existing material-aware Scene25D** into the
topic-neutral renderer. Each beat may optionally contain 1–6 independently
authored RGBA PNG/WebP layers. A layered visual scene moves through one
smooth camera trajectory while each authored depth plane reacts to it at its
own parallax factor. Foreground alpha and native object proportions are
preserved. Material rim-lighting is computed once per asset rather than every
frame.

This **does not generate an animal, landscape or object from a topic title**.
It provides the cross-topic scene-compositor integration needed when an
original local illustration is ready; text-only fallback remains a simple
kinetic educational diagram.

Example for a `concept` or `sequence` beat (do not use it on numeric
`measure` or `compare` beats, which must keep numeric graphics visible):

~~~json
{
  "visualLayers": [
    {
      "file": "owned/backdrop.png",
      "z": 5,
      "parallaxX": 0.15,
      "parallaxY": 0.1,
      "material": "none",
      "rights": "Original hand-authored illustration; original rights confirmed.",
      "rightsConfirmed": true
    },
    {
      "file": "owned/foreground.webp",
      "z": 45,
      "parallaxX": 1.1,
      "parallaxY": 0.6,
      "material": "foliage",
      "rights": "Original artwork created and owned by the video author.",
      "rightsConfirmed": true
    }
  ]
}
~~~

Files must be physically located under the storyboard directory, must be
actual bounded PNG/WebP, and cannot escape it with `..`, absolute paths or
URLs. Missing files, unsupported media, unconfirmed rights, invalid materials,
nonfinite camera values and duplicate Z depths fail before rendering. The
manifest contains asset SHA-256 hashes, file basenames and author-claimed
license provenance for audit. Such author claims **are not independent
copyright verification**; humans must check rights and factual claims.

The independent art pipeline is covered by `tests/test_universal_art25d.py`:
actual newly drawn RGBA assets, material-aware parallax, path/rights rejection
and an **encoded original 9:16 MP4 with narration**. It stays generic:
no science-specific, forest-specific or product-specific renderer is imported.

### Unfinished for full subject universality

- Automated, factually grounded script research and source verification
  from a **single topic prompt** remain unimplemented; the user currently
  provides original narration or a structured evidence-backed storyboard.
- Broad original asset acquisition/generation with verified licensing,
  consistent identities and separate transparent depth layers is **not yet
  automated**. Current script-only visuals are not reference-grade.
- Motion studies must include meaningful physical change and actor
  transformations, not just adding camera noise or decorative particles.
- Replace approximate subtitle timing with exact recorded phrase alignment
  and verify natural Kokoro narration by ear. eSpeak is CI-only.
