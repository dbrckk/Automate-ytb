# Reference gap — 3561.mp4 / continuous motion design (13 Nov 2026)

## Empirical reference audit

The user-supplied benchmark \`3561.mp4\` was examined **frame by frame**,
not inferred from a thumbnail or a generic style label.

- Source media: **576×1024, portrait 9:16, 30 fps, 30.8 s**, H.264 + stereo AAC.
- The video's structure is a coherent **quantitative scale journey**, not a
  chain of separately illustrated scenes: a continuously growing gold/orange
  luminous spire, a cyan progress ruler and numeric updates at the top, and
  source-relevant scale-comparison line art that changes as the scale grows.
- Repeated framing establishes a stable measuring world. Numeric values,
  reference objects, current distance and the global narrative all work
  together. Physical examples become increasingly expansive.
- Negative space, restrained colors, glowing contour art and legible
  typography do more of the visual work than dense textures would.
- Progression spans micro → objects → human → architecture → Earth → space
  and is the source of the viewer's sense of escalation. The benchmarks'
  watermark, author branding, exact scripts, images and music are NOT reused.
- Automated image sampling (every 3rd frame at reduced resolution) found
  average luminance ~26.5/255 and nontrivial motion; this is an approximate
  descriptive statistic, not a perceptual aesthetic score.
- The encoded audio contains stereo AAC. **Voice naturalness, music quality
  and sound-design likeness cannot be certified from metadata or stills**;
  independent human listening is still needed.

## Comparison with Automate-ytb v20

The 13 Nov coastal-storm Short rendered successfully at 1080×1920 and
~40.87 s, real neural Kokoro + H.264/AAC; that is technical readiness, NOT
visual equivalence. Its illustration path yields isolated two-object
animations, a separate scene title and several independently grounded shots.
It lacks an underlying quantitative world state, meaningful numeric-scale
motion and long-range visual escalation. Merely adding more polygons, particle
systems or photorealism would not repair this missing **motion grammar**.

## v21 implemented: general-purpose source-only quantitative journey

Modules:
- \`automate_ytb/universal_scale_journey.py\`
- \`automate_ytb/universal_script.py\`
- \`automate_ytb/universal_kinetic.py\`

An original-script Short automatically uses this route when **all 3–12
source beats** contain exactly one unambiguous, monotonically increasing
length statement. Unit normalization uses standard exact metre, centimetre,
millimetre, kilometre, foot, inch, mile and Julian light-year multipliers.
Contradictory, ambiguous, missing, unbounded or unrelated data falls back to
the existing genre renderer rather than guessing numbers.

The v21 image engine adds:
1. One stable original graphic **world** across editorial beat boundaries
2. One log-scaled measuring axis shared across the entire episode
3. A source-number progress position with differentiable easing at cuts
4. A glowing height marker with bounded blur, parallax-like horizon and
   continuous moving particles
5. Source-only landmark outlines (human, tree, skyscraper, mountain, Earth,
   Moon or ruler), without external assets or copied reference graphics
6. A hierarchy for one topic title, one authored quantity and an
   accumulated history of previous authored numerical measurements
7. Existing PCM-timed complete subtitles, free speech engines and
   original soundtrack; no invented word alignment or physics

Numbered progress *positions* are interpolated, but no intermediate
numeric fact is invented or displayed as a real observation. Every printed
quantity must occur literally in the corresponding narration; source text,
unit conversion, icon selection, exact waypoint sequence and provenance are
recomputed on the read path. Tampered or stripped declarations fail closed.
Legacy v15–v20 stories with no eligible quantity sequence follow unchanged
render paths.

Reproduce a new ORIGINAL demo (not a copy of the benchmark):

\`\`\`bash
python -m unittest discover -s tests -p test_universal_scale_journey.py -v
automate-ytb-short \
  --topic "What if a glowing thread kept growing?" \
  --script-file examples/universal_scale_journey_story.en.txt \
  --language en --voice espeak --width 720 \
  --output build/universal/continuous-scale-original.mp4
python -m automate_ytb.shorts_delivery \
  --video build/universal/continuous-scale-original.mp4 --require-audio
\`\`\`

The same route supports English/French text when the source units are
recognized. Use \`--voice kokoro\` for the regular natural-voice output.

## Remaining work for the quality target

This v21 update is a **foundational** motion-graphics improvement only; not
general cinematic visual generation nor a claim of parity with 3561.mp4.

Priority 1 — **Content/storyboard planning**: add source-reviewed numeric
and causal narrative planning, clarify which story is best represented by a
single continuous physical model versus independent scenes. This must avoid
hallucinated quantities and unjustified benchmarks.

Priority 2 — **Landmark quality + camera choreography**: detailed original
vector/raster layers, genuine scene-to-scene size comparisons, type-on,
smooth reveal and persistent camera movement; support larger catalog of
visual examples without low-detail primitive representations.

Priority 3 — **Precise audio/animation alignment**: align words (not just
phrases) to measured PCM using an offline alignment tool; trigger every
reveal/glint/camera beat at corresponding narration words. Bespoke Foley
families must refer to real authored visual events.

Priority 4 — **Original sonic identity**: integrate dynamic music motifs
and environmental sound loops with transitions; use in-context blind
listening to compare English Kokoro voices. Music and voice should not be
judged from bitrate or a "verified real voice" metadata flag.

Priority 5 — **Repeatable subjective audiovisual QA**: extract comparable
frames/audio, storyboard-to-output consistency metrics and independent
human review of composition, readability, motion, story, voice, music,
effects and pacing; record per-domain evaluation and publish changes only
after feedback.

Priority 6 — **Generalization**: build separate grammars for numeric
comparisons, mechanisms, geography, events and character interactions.
Never describe one narrow genre grammar as being able to animate "any topic".

## Success criteria

- Quantitative source script is deterministically recognized and rendered
  with an always-persistent scale instead of independent diagram slides.
- Numeric claims and units can be traced to original beat wording, including
  when mixed SI units are converted. A forged scale is refused.
- Original shapes and actual RGB pixels change across frames while world
  progress remains continuous at every editorial scene transition.
- A complete 9:16 H.264/AAC MP4 is rendered and technical media QA passes.
- Source and generated story, video, manifest, subtitles, voice proof and
  creation history remain auditable. No automatic TikTok posting or
  unsupported subjective quality claim.
