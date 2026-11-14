# P0 — First reusable premium 2.5D visual rebuild

## Diagnosis grounded in 3561.mp4 (supplied reference)

The 30.8-second, 576×1024, 30-fps source combines one coherent dark
environment with a fixed, highly legible typographic hierarchy, green progress
line, glowing warm growth column, persistent comparison landmarks, and a
continuous scale journey culminating in a space reveal. The perceived quality
comes from **art-directed silhouettes and motion**, not frame dimensions.
The cinematic-scale renderer already has a related numerical treatment.
General topic output, however, previously selected a six-family low-detail
illustrator or a generic circle-and-label diagram. A working H.264/AAC export
was mistakenly treated as a premium visual success.

### Changes in this first P0 increment

1. **Specific source-grounded maglev family.** Original illustrative scene
   made from five 2.5D planes: deep sky, detailed guideway, aerodynamic
   modern carriage with multiple windows and nose contour, undercarriage and
   bounded stylized electromagnetic cues, and motion-light foreground. It
   never substitutes a toy steam engine or depicts wheels/smoke as the main
   hero object. The lines represent a visual explanation, **not** verified
   electromagnetic simulation.
2. **Continuous semantic identity.** If the narration specifies "maglev",
   later generic mentions of "train" keep the same maglev art and actor
   family rather than changing vehicles between spoken beats. Maglev and
   rail are not composited as two independent objects.
3. **Shared optical finish.** For freshly compiled, source-provenanced
   illustrated episodes, hero layers 40–100 receive a cached colored
   emission plate computed once per vector layer (downscaled Gaussian
   blur). Dark world layers stay unchanged; no full-frame per-fps blur.
4. **Serialized episode compatibility.** The new
   `proceduralVisualFinishEngine` marker is validated by the renderer.
   Older generated JSON without this marker keeps its prior treatment.
   Falsified markers and altered generated geometry fail validation.
5. **Fail-closed premium gate.** New public premium requests lacking
   authored/grounded visual vectors for one or more beats (and lacking a
   continuous source-grounded scale world) now fail before installing
   heavyweight speech models. It is better to refuse an under-illustrated
   premium job than publish generic rings as a successful production.
6. **Real regression harness.** The PR workflow encodes an actual 720×1280
   original maglev video (two authentic source beats) with free eSpeak **for visual verification only**,
   checks all decoded frames/audio, verifies full artwork provenance, and
   uploads five JPG frames, a contact sheet, SRT, manifest and MP4.
   This is not a neural premium release or a TikTok publication.

## Measurable acceptance conditions

- `proceduralVisualFamily == "maglev"` for the actual failed request.
- At least 85 original vector primitives across exactly five depth planes,
  reused across the five narrated beats with actor continuity.
- Every narrated scene must have actual original generated artwork; a
  generic circle fallback is a **blocking release failure**.
- QA must confirm H.264 video, audio and complete decode, and the image
  contact sheet must be reviewable as a human visual quality checkpoint.
- No invented quantitative facts, copyrighted media, video publication,
  or artistic-quality score implied by technical validation.

## Remaining work to approach the reference

This is **the first visual system upgrade, not 20/20 quality**. A finite
vector library cannot visually represent arbitrary real subjects. Next
priorities, in descending order: add more source-grounded packs for
previously unsupported content; richer object geometry and handcrafted
optical depth; continuous cinematographic transitions and on-beat reveal
timing for non-scale stories; real assets or generated illustrations with
verified rights for unknown topics; automatic sampled-frame defect metrics;
human review of the audio, graphic richness and visual comparison to
3561.mp4 before any public release.

The premium gate intentionally does not claim to solve unknown subjects.
It prevents an honest but visually poor fallback from being mislabelled
premium. No paid service, cloud inference token, or external media asset
is required by this incremental rebuild.
