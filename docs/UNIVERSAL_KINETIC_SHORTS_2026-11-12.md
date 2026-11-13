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


## Opt-in topic illustration search — Commons CC0 (incremental visual step)

The universal kinetic engine can now optionally search **Wikimedia Commons**
for a photograph depicting a beat. This is a zero-cost, token-free original
media route, not automatic AI-generated artwork:

```bash
automate-ytb-short --topic "How wild forests regenerate" \
  --script-file examples/universal_seed_story.en.txt \
  --language en --voice kokoro --commons-art \
  --width 720 --output build/forest-explainer.mp4
```

- Without `--commons-art`, production remains **fully offline for visual
  assets**. This also preserves deterministic PR smoke behavior.
- A JSON beat may provide `"visualQuery": "pine forest canopy"`; otherwise
  the exact authored beat title is searched. No prompt-generated factual claims
  or invented images are introduced.
- Only an image with both **CC0** metadata and the canonical
  CC0 1.0 rights URL can be considered. The result's URL must be an HTTPS
  Wikimedia Commons thumbnail at `upload.wikimedia.org`; SVG, huge,
  unreadable, malicious and unverifiable candidates are rejected. Only
  JPEG/PNG/WebP raster bytes are decoded, with file-size and pixel limits.
- One accepted picture per eligible concept/sequence beat. Images with
  identical file-page URLs are not duplicated across beats. Numeric
  `measure`/`compare` beats keep their accurate animated measurements,
  rather than letting unrelated photography obscure the values.
- The picture is prepared once then rendered with a smooth camera dolly,
  focused portrait crop, graded lighting and restrained edge treatment.
  This **is a photographic animation, not actual object segmentation or
  semantic 3D/2.5D skeletal motion**.
- Search outage, no CC0 result or invalid media falls back to the **existing
  original local 2.5D grammar**. Network search never gatekeeps an MP4.
- `<video>.json` now records selected `commonsSources`: exact Commons
  file page, search query, metadata-reported rights/creator, thumbnail URL,
  media SHA-256 and `rightsVerifiedByHuman=false`. Publication approval
  always remains false. The editor must verify rights, subject relevance and
  appropriateness of the selected file before release.
- The GitHub Actions **Universal kinetic Short smoke** manual workflow now
  exposes `commons_art`, defaulting to off, alongside topic, original script,
  language and neural voice.

This is intentionally strict. Wikimedia explicitly cautions that license
metadata may be incomplete or outdated and that downstream reusers must
verify restrictions beyond copyright. Restricting to CC0 1.0 is conservative,
but does not guarantee that every topic has imagery.

### Independent quality gates

The shared `tests/test_universal_commons.py` suite feeds local official-API
shaped results and real JPEG bytes to the same code; it verifies CC0
filtering, unsafe redirect/host rejection, invalid raster failures,
source metadata, visually changing frames, and safe offline fallback.
No paid API, account, or token is required to test the feature.


## Optional independent 2.5D foreground from real CC0 media

The `--segment-art` switch builds on `--commons-art` and requires the
optional local CPU dependency:

```bash
python -m pip install -e '.[foreground]'
automate-ytb-short --topic "A seed comes to life" \
  --script-file examples/universal_seed_story.en.txt \
  --language en --voice kokoro \
  --commons-art --segment-art --width 720 \
  --output build/segmented-original.mp4
```

The implementation explicitly uses the **local U2NetP** session through
`rembg`, not its current default image provider or any paid cloud service.
The model is downloaded on first use and cached locally. A segmentation
mask must have plausible nontrivial coverage before it is applied; otherwise
the accepted original CC0 photograph still renders with its camera dolly.
This is a source-image saliency matte, **not proof of accurate anatomy,
a complete 3D reconstruction, physical simulation or human verification**.

With a valid matte, the original subject moves on a separate timed foreground
plane over a differently focused background. Both remain anchored in the same
source image; camera motion is smooth and deterministic. This can improve
perceived depth for a single salient subject but cannot make complex scenes
act out unauthored events.

The `commonsSources` manifest now reports `segmentationRequested`,
`segmentationApplied` and `segmentationModel` per acquired source. The
`rightsVerifiedByHuman` and `publicationApproved` gates remain false.
If the optional Python package is absent, explicitly requesting segmentation
produces an actionable error instead of falsely reporting premium 2.5D.
The Android manual workflow provides a separate `segment_art` toggle and
only installs the open model dependency when it is selected.

**Remaining reference-grade gap:** a generic scene generator must select
correct real foreground/backdrop subjects, generate coherent action rigs,
and preserve visual identity across several cuts. Neither CC0 photographs
nor generic saliency masks accomplish that alone.


## Authored subject motion: original actor rig

The universal story format now supports actual, keyframed motion for separate
original, rights-confirmed transparent PNG/WebP subjects. An optional
`actorTracks` array belongs to an individual concept/sequence beat.
Each entry identifies an existing foreground layer by its `z` depth and has
2–8 keys. Key times go from 0 to 1 (the true PCM-derived beat duration),
positions are bounded offsets in stage fractions, scale is a multiplier,
and rotation uses degrees. All tracks use smooth time-addressable interpolation.

```json
{
  "actorTracks": [
    {"z": 45, "keys": [
      {"at": 0, "x": -0.15, "y": 0, "scale": 0.75, "angle": -12},
      {"at": 0.5, "x": 0, "y": -0.07, "scale": 1.1, "angle": 0},
      {"at": 1, "x": 0.12, "y": 0, "scale": 1.0, "angle": 9}
    ]}
  ],
  "actorLinks": [{"fromZ": 45, "toZ": 78, "at": 0.53}]
}
```

A link pulse represents an explicitly authored visual connection between
two independently animated original subjects; it does not assert an unproven
physical collision. No motion is fabricated from topic keywords.
Backgrounds cannot be rigged; opaque foregrounds, invalid dimensions,
duplicate depths, missing endpoint keys and unsafe transforms are rejected.
The same actor rig works for transparent artwork from any appropriate topic.

To generate and truly encode the repo-owned demonstration:

```bash
python examples/build_original_actor_rig_sample.py --out-dir build/actors
automate-ytb-short --brief build/actors/actor-rig-story.json \
  --output build/actors/actor-demo.mp4 --voice kokoro --width 1080
```

The generator creates original background, body, receiver and articulated antenna layers. GitHub CI separately
encodes and validates a real 720x1280 actor-action MP4 alongside existing
web/nature topics. This improves the **general pipeline** rather than
claiming to create a faithful person, animal, real machine, or scientific
physical simulation from a bare title. Topic-specific articulated motion
synthesis remains an unsolved next step.

### Articulated parts: author-defined hinge pivots

Each original transparent foreground component can now rotate about its own
**fixed hinge**, rather than only around the center of its alpha bounding box.
An optional `pivot` field on an `actorTracks` entry specifies two normalized
coordinates inside the transparent component's bounding box:

```json
{"z": 90, "pivot": [0.5, 0.94], "keys": [
  {"at": 0, "x": 0, "y": 0, "scale": 1, "angle": -20},
  {"at": 0.5, "x": 0, "y": 0, "scale": 1, "angle": 25},
  {"at": 1, "x": 0, "y": 0, "scale": 1, "angle": -10}
]}
```

Here the component rotates around a near-bottom hinge, so an original
antenna, arm, wing, pendulum, mechanical lever or similar **separate original
art layer** can articulate independently from the main subject. The engine
maintains the joint's world position during rotation and rejects invalid
pivot coordinates, including non-finite numbers and booleans. The pivot
must also remain unchanged when the same original subject continues into
the next shot. No automatic human/animal skeletal inference is claimed.

The reproducible actor demonstration now includes a separately illustrated
antenna joint over the existing original spacecraft; dedicated GitHub Actions
renders an actual portrait H.264/AAC film and exercises the hinge tests.


### Attached assemblies: a real parent-to-child transform

A child actor can now reference another approved moving foreground layer
through parentZ and attach, in addition to its own normalized pivot.
The example contains a spacecraft antenna attached to the original body:

    {
      "z": 90,
      "parentZ": 45,
      "attach": [0.5, 0.62],
      "pivot": [0.5, 0.94],
      "keys": [
        {"at": 0, "x": 0, "y": 0, "scale": 1, "angle": -4},
        {"at": 0.5, "x": 0, "y": 0, "scale": 1, "angle": 26},
        {"at": 1, "x": 0, "y": 0, "scale": 1, "angle": -15}
      ]
    }

Unlike copying the body position into every antenna frame, the child now
inherits the parent's translation, camera displacement, scale and angle.
Its hinge follows the selected normalized parent crop anchor. Its separate
local angle rotates the component about its own pivot; local x/y offsets
move along the rotated parent's axes.

Parent layers must be licensed, moving RGBA originals at a lower Z depth.
The hierarchy is an acyclic tree. Missing parents, invalid normalized
anchors, discontinuous joint attachment across shots and excessive inherited
scale are rejected. Nested original parts are supported within the existing
six-actor budget. This is not automatic anatomical or physics simulation.

The dedicated CI verifies three real 720x1280 portrait MP4s, including
two continuous scenes with a truly parented antenna, and validates inherited
joint geometry independently of audio and video encoding.


### Original vector illustrations: full-resolution artwork without PNG files

The universal original-story JSON now supports `visualVectors` in every
`concept` or `sequence` beat, alongside approved `visualLayers`.
It is an **original illustration authoring engine**, not a text-to-image
model: the vector shape descriptions must be supplied by the story
author or a separate, audited scene-describing program.

The vector stage accepts 1–6 independent original transparent layers,
up to 48 shapes per layer, with:

- original multi-segment cubic Bezier outlines, polygons, smooth ellipses,
  rounded rectangles and lines
- bounded 0..1 scene-relative geometry (consistent across resolutions)
- two-stop color gradients, optional strokes and 2× anti-aliasing
- original depth, material lighting and independent 2.5D parallax
- all existing actor animation, attached hinge, Foley and cross-scene rules
- deterministic SHA-256 provenance of the **actual authored shapes**
- no image downloads, SVG/XML parsing, scripts, remote APIs or paid credits

An original vector illustration layer has this declarative format:

    {
      "id": "illustrated-sun",
      "z": 55,
      "parallaxX": 1.0,
      "parallaxY": 0.4,
      "material": "none",
      "rights": "Original illustration authored from scratch in this story.",
      "rightsConfirmed": true,
      "shapes": [
        {"kind": "ellipse", "box": [0.3, 0.2, 0.7, 0.6],
         "fill": ["#FFE5AE", "#F0A66D"],
         "stroke": "#FFF4CC", "strokeWidth": 0.004}
      ]
    }

The layer ID is stable across narrated shots. Transparent layers can be
animated through `actorTracks` by referencing their `z`, just like
licensed PNG/WebP files. For a continued shot, the source ID and geometry
hash must remain identical; the rig's poses and joint attachments must
also be continuous.

To build and encode a complete original, multi-layer illustrated flower
without **any source image file**:

    python examples/build_original_vector_story.py --out-dir build/flower
    automate-ytb-short --brief build/flower/original-vector-story.json --output build/flower/flower.mp4 --voice kokoro --width 1080

The sample contains gradients, hand-authored curved petals, veins,
botanical highlights and a textured background. Leaf and flower
components inherit motion from the stem; the camera follows the subjects
continuously over two narration beats. GitHub Actions runs tests and
encodes a real H.264/AAC portrait video using eSpeak as the fast draft
voice; `kokoro` remains the optional neural voice mode.

**Honest scope:** this is a scalable, free, testable drawing *backend*.
It does **not** magically create a faithful image of an arbitrary real
animal, place, product, scientific mechanism or historical event from
plain text. A semantically grounded scene specification or a separately
validated generative/retrieval model is still required for those use
cases. Source facts and publication require editorial verification.

### Translucent vector material overlays

An original vector shape may optionally declare an opacity between 0.05
and 1.0. The default remains fully opaque for existing stories. Every
primitive is rasterized into its own transparent RGBA plate and alpha-
composited in author-defined order. This preserves the colors and details
under semi-transparent glints, shadows, glass, haze, and highlights rather
than replacing the earlier pixels. Gradients and outlines obey the same
opacity. Non-finite, string, boolean and out-of-range values are rejected.

The original flower fixture includes two separate translucent petal glints
in both continuous shots, demonstrating reusable material layering without
an external image generator or paid provider. This is an authored vector
material tool, not an automatic semantic illustration model.


### Flexible original illustrated parts: deterministic non-rigid motion

The universal actor rig supports an optional bounded deformation on any
already-approved transparent actor image or vector layer:

    {
      "z": 55,
      "parentZ": 35,
      "attach": [0.33, 0.64],
      "pivot": [0.93, 0.57],
      "deform": {
        "kind": "sway",
        "amount": 0.095,
        "cycles": 1.5,
        "offset": 0.15
      },
      "keys": [/* existing at/x/y/scale/angle keyframes */]
    }

The scene engine samples a local horizontal mesh deformation on the cached
RG**B**A source plate. The displacement is **zero at the authored hinge**.
The same plate may independently inherit its parent's translation, rotation
and scale. Source-space motion remains coherent after cutting between shots:
sway reads the group camera clock and the deformation parameters cannot
change across adjacent shots of the same original actor. The warp pads
the source image to prevent a moving edge from being clipped.

Amount is bounded to 0.005–0.12 of the resized original crop width; cycles
to 0.25–3 per continuous camera window; offset to 0–1. Unknown kinds,
extra fields, non-finite values, booleans and unsafe dimensions fail closed.
This is authored flexible motion (e.g. leaves, cloth, antenna), *not*
automatic anatomical inference, physically accurate simulation, or a
general text-to-video image generator.

The original flower example now has two separately deforming leaves in
each of two continuous shots. GitHub's real H.264/AAC smoke verifies four
flexible-actor tracks, while the dedicated unit suite verifies reproducible
pixels, pinned hinges, and rejected discontinuities.

### Object-space vector material shading (engine v11)

Every original vector primitive can now use a bounded `fill` surface gradient:

```json
{
  "colors": ["#FFF4C8", "#E3AA88", "#8B456E", "#273048"],
  "direction": "radial",
  "space": "shape"
}
```

Accepted directions are `vertical`, `horizontal`, `diagonal`, and
`radial`; use `space: "shape"` to shade the local painted silhouette
instead of the whole image, or `space: "stage"` for global atmospheric
lighting. Use two to five explicitly authored `#RRGGBB` stops.
The existing solid and two-stop array fills remain accepted, and arrays
still render as vertical stage-wide gradients for compatibility.

The rasterizer produces a bounded anti-aliased gradient only once per scene.
The object's alpha is applied after painting its color to avoid dark
premultiplied edges. The existing RGBA overlay opacity then composites
reflections correctly over earlier details. The original flower fixture
uses two differently directed petal shaders and a radial multi-stop center,
plus independently rigged flexible parts, in two continuous shots.

This feature improves the **reusable renderer** for any authored object.
It does not claim to invent a semantically correct object from an arbitrary
topic or to replace factual/visual editorial review.

### Cinematic authored-world presentation and local contact cues (v12)

**Why:** previous authored visuals occupied a boxed 51%-height stage beneath
persistent title/progress UI; the event compositor drew a straight beam
between every pair of subjects even when they never touched. Those lines
looked like diagrams rather than genuine moving objects.

**New reusable defaults for original PNG/WebP and vector shots:**

- Composite the original 2.5D scene as an aspect-preserving *full-width*
  portrait world, up to 63% of the frame height. The top/bottom 4.6% of
  that picture fades into an existing generated backdrop. Source art is never
  stretched, cropped, hallucinated or blurred to fake more detail.
- Keep a smaller topic label; replace the persistent big headline and data
  progress bar with a short narrated beat title which fades out after an
  authored shot begins. This is temporal editorial typography, not a slide.
  PCM-derived narration captions remain below the imagery.
- Actor links keep the **exact same authored beat time and Foley cue**.
  For nearby centres, render a brief warm-localized glint at the midpoint.
  For distant actor centres, show two independent subtle local responses
  instead of pretending the subjects are physically connected by a beam.
  There is no universal full-width connector line or orbit circle.
- These changes apply to *every* properly authored art-layer/rigged shot,
  independently of subject matter. Exact numerical diagrams without authored
  artwork retain the older readable data/chart layout.
- Manifest reports `portraitCompositionEngine` and
  `contactVisualEngine`; pixel-level safety and media tests guard both.

**Remaining gaps:** this is not image generation from arbitrary natural
language, and a transient glint is only a visually coherent event marker;
it does not establish factual causality. Still required: object-specific
visual generation, movement/storyboard planning, sound/music aesthetic
evaluation and successful neural Kokoro narration in a complete original
episode. Human editorial approval is still required to publish.

### PCM-synchronized cinematic phrase captions (shared generator v13)

The original Short renderer now paints every authored phrase with exact font
metrics, centred in the portrait safe area (69–89% of frame height). The
short rounded dark matte follows the content instead of permanently
covering the screen with a wide PowerPoint banner. All words remain
visible: one to three lines at a bounded font size, explicitly rejecting
unrenderable strings instead of applying ellipses or discarding lines.

The **same synthesized PCM phrase boundaries** drive both SRT entries and
baked-in caption visibility. A short fade accompanies each phrase's real
start/end frames. There is no fabricated word-level alignment, estimated
karaoke highlight or speech recognition. Offline preview captions are
labelled unaligned and use an authored excerpt.

Caption layouts are validated against the actual 9:16 target resolution
*before* starting expensive free Kokoro inference or FFmpeg; source text and
mobile constraints are checked together. Bounded font/layout caches reuse
measured line breaks over every 30 FPS frame and are returned defensively
to prevent a mutated caller layout from omitting text. Rendering
alpha-composites just the small caption panel, not a full RGBA frame.
The manifest records `captionOverlayEngine`,
`captionLayoutPreflight: passed`, `captionWordsOmitted: 0`, and
`wordLevelAligned: false`. The full-media CI asserts these claims.

This is a **typographic and sync** improvement, not a claim of human-quality
speech. The usual CI smoke intentionally uses eSpeak; a genuine Kokoro run
must separately be verified before natural voice quality is claimed.

### Real neural narration evidence in the universal Short renderer (v14)

The universal CLI accepts `--voice kokoro --voice-name af_heart` and
optionally `--export-narration-wav`, generating the same original 9:16
Short and preserving the source narration as a separate WAV when opted in.

Every produced Short now measures the *actual generated* mono PCM16 before
rendering: sample rate, duration, RMS loudness, peak level, voiced fraction,
and SHA-256. Kokoro is required to produce 24 kHz PCM; silent, truncated,
oversized or wrong-format voices abort production rather than silently
falling back to eSpeak. The measured WAV duration must agree with the
same frame clock that drives visual beats and subtitle cues (±35 ms).

The manifest includes `voiceName`, `voiceEvidence` and optional
`narrationWavFile`. If a WAV is requested, the renderer first validates
the actual mixed video and only then copies the original voice PCM, verifying
the exported SHA-256 exactly matches the pre-render speech samples.
This supports human listening and reproducible comparison between voices
without re-synthesizing model output.

```bash
python -m pip install -e '.[speech]'
automate-ytb-short \
  --brief examples/universal_web_request.json \
  --voice kokoro --voice-name af_heart \
  --output build/my-short.mp4 --width 720 \
  --export-narration-wav
```

A separate fully free CPU-only GitHub Actions workflow,
`.github/workflows/universal-kokoro-verified.yml`, actually invokes
the open Kokoro-82M model, renders **original articulated vector artwork**,
and independently verifies the 24 kHz WAV, hash, bounded speech energy,
real H.264/AAC, synchronized source captions, and 9:16 resolution.
It saves source WAV, MP4, SRT, QA and manifest in the same artifact.

**Accuracy limit:** verified neural synthesis and audible PCM are not proof
that a human finds the voice natural. This audit never auto-approves the
voice, video, facts, artwork or publication. The existing fast CI uses
eSpeak and explicitly reports it as such; it is not relabeled as Kokoro.

### Original subject-specific illustrated Shorts from script text (v15)

A free user-supplied **original** EN/FR script can now select a real,
multi-depth vector subject automatically, *only when its own narration*
contains explicit recognizable source nouns. Supported first families:
botanical scenes (trees/seeds/leaves), orbital/planetary illustrations,
railway locomotives, rain/clouds, ocean waves and password/security
symbols. These are **different original silhouettes**, not just recolored
copies of the old circles and bars.

Each accepted family builds five bounded original painted layers (sky,
environment, recognizable hero, internal detail and moving atmospheric
elements). Per-object multi-stop material shading, translucency, parallax,
4 independent actor trajectories and continuous two-shot camera movement
reuse the already-tested universal 2.5D renderer. Original theme-specific
foreground details are generated deterministically and cached as source
sprites; no per-frame asset re-generation, remotely retrieved copyrighted
photo, AI inference service or fabricated numerical fact is needed.

Example free CLI:
```bash
automate-ytb-short \
  --topic "An illustrated planetary journey" \
  --script-file examples/universal_planet_story.en.txt \
  --language en --voice kokoro --voice-name af_heart \
  --width 720 --output build/planet.mp4
```

**Safety and reliability:** unknown or unrecognized subjects retain the
legacy generic conceptual diagrams rather than inventing an unrelated real
object. A concrete family must be mentioned in the narration; topical words
alone do not qualify, and simple explicit negation is excluded. The
`proceduralVisualFamily` and `proceduralVisualEngine` declarations are
verified against the same source text and exact original shapes/keyframes
before output is trusted. Mutated "automatically generated" vector artwork
is rejected, never silently accepted as certified source provenance.
The final MP4 manifest records the actual generated family and number of
originally illustrated scenes and leaves `publicationApproved: false`.

**Current limitations:** the vocabulary and six procedural silhouette
families are finite. These are **stylized illustrative objects** rather
than documentary footage, historically exact trains, observed planets,
scientifically precise simulations or a general text-to-image AI model.
Mixed or ambiguous subjects may still use a thematic illustration rather
than accurate scene-by-scene visual storytelling; complex source facts,
licensed photorealistic art, detailed storyboarding, interactions and
human editorial judgment still need development. This is an improvement
of the **generic video creation process**, not a one-video asset swap.
