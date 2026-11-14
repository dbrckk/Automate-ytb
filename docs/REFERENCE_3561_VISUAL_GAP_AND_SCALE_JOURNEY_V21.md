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


## v22 — Global camera + original landmark artwork (14 Nov 2026)

The v21 source-authenticated length sequence was real but visually static:
its background stayed fixed, its glowing column stretched in a scene-local
composition, and contextual objects were small line icons. This was not
comparable to the reference's continuous visual escalation.

The new, reusable renderer
\`automate_ytb/universal_scale_camera.py\` adds a genuine global moving
*illustrative* world, not per-shot Ken Burns animations. An absolute camera
pose is derived only from the continuously interpolated base-10 scale
coordinate. The camera center, lens scale and gentle horizontal pan are
mathematically identical at consecutive scene boundaries. Once a sourced
landmark becomes visible, it occupies a fixed world coordinate and
automatically moves down-screen as the camera climbs. Earlier landmarks
remain part of the same world until outside the crop. Stars and particles
have independently moving depth planes tied to that global progress.

The artwork is procedurally authored inside the repository: seven original
detailed object silhouettes (metal ruler, articulated person, textured
tree, perspective-windowed tower, multi-plane snow mountain, latitude-
marked Earth and cratered Moon). Their **icon sizes are explicitly
illustrative** and do not purport to be physically calibrated. A visible
label confirms that they are not to scale. The actual comparison numbers
and visible labeled milestones remain verified against exact source spans.
The source-authored numerical ruler and animated central beam continue
across cuts and cannot fabricate intermediate measured numbers. Numeric
text crossfades between the two actually authored adjacent quantities.

Compatibility: new original-text stories with an eligible numeric
sequence store
\`proceduralScaleCameraEngine=source-scale-continuous-world-camera-landmarks-v22\`.
Saved v21 JSON stories without that field retain the original renderer
pixel-for-pixel. Invalid version markers, unsupported camera-only claims,
forged scale values and unsourced artwork are rejected by the JSON reader.
Other 2.5D subject, collision and authored JSON routes remain unchanged.

Reproduce locally with free dependencies:

\`\`\`bash
python -m unittest discover -s tests -p test_universal_scale_camera.py -v
automate-ytb-short --topic "What if a glowing thread kept growing?" \
  --script-file examples/universal_scale_journey_story.en.txt \
  --language en --voice espeak --width 720 \
  --output build/universal/continuous-scale-original.mp4
python -m automate_ytb.shorts_delivery \
  --video build/universal/continuous-scale-original.mp4 --require-audio
\`\`\`

The GitHub Actions universal video workflow performs actual 720×1280
H.264/AAC encoding and checks the source-derived six-waypoint camera
manifest. The full production tests and real CPU Kokoro neural narration
CI must also pass at the same commit SHA before merge.

**Still to improve:** reference-like composition, sophisticated motion of
real comparable objects, shot-level timing by spoken words (not just PCM
phrase boundaries), richer lighting/material depth, music dramaturgy and
cross-genre narrative planning. Technical CI success cannot validate
artistic likeness or audio naturalness.


## v23 — Synchronisation audiovisuelle fondée sur le PCM réel

### Problème corrigé

En v22 les repères chiffrés et les silhouettes étaient déclenchés à des
**fractions arbitraires de la scène** (par ex. 12–39 %), même lorsqu'un
narrateur ne prononçait le nombre ou le nom de l'objet que bien plus tard.
Les effets sonores tombaient au début des scènes, séparément de ces
apparitions. Cela produisait un décalage perceptible avec la référence
3561.mp4, malgré une bonne synchronisation des sous-titres.

### Moteur v23

- Nouveau fichier : \`automate_ytb/universal_scale_speech.py\`.
- Marqueur de provenance distinct :
  \`proceduralScaleSpeechEngine=source-scale-real-pcm-phrase-choreography-v23\`.
- Le générateur produit **d'abord** le véritable WAV mono du narrateur
  (Kokoro ou eSpeak) et collecte les débuts/fins de chaque phrase via le
  nombre exact d'échantillons PCM écrits dans le WAV.
- Le compilateur recoupe chaque valeur de mesure \`sourceSpan\` avec
  **une seule phrase réellement synthétisée** de la scène. L'illustration
  est associée à la première phrase qui nomme réellement sa famille de
  sujet. En l'absence d'un nom explicite, le repère géométrique reste
  une illustration générique et réutilise le début mesuré du nombre.
- Avant la phrase chiffrée, le moteur conserve la dernière mesure
  explicitement annoncée ; ensuite, la nouvelle mesure apparaît et la
  caméra commence sa progression. Pas de nouvelle mesure inventée.
- L'icône, éventuellement citée dans une phrase différente, apparaît
  au début **mesuré** de cette phrase et reste dans le même monde animé.
- Les accents Foley 48 kHz « scale-transition » et « reveal » sont liés à
  des \`PropertyEvent\` du MasterTimeline aux mêmes frames que leurs
  mouvements visuels. Ils ne reposent ni sur une durée calculée d'après
  la longueur des mots, ni sur des échantillons externes.
- Le rapport MP4 archive les phrases, frames, types d'événements et
  nombres de sons réellement associés. Les scènes non numériques et les
  histoires v22 déjà sauvegardées conservent leur ancien comportement.
- Les événements et la liste de phrases sont validés avant l'encodage.
  Une phrase manquante, falsifiée, non ordonnée, sans la mesure source,
  ou un prétendu alignement mot à mot sont refusés.

### Limite essentielle

**Il s'agit d'une synchronisation exacte à l'échelle de la phrase
synthétisée, PAS à l'échelle du mot.** Le nombre lui-même peut être prononcé
après le début de la phrase sélectionnée. Le rapport indique donc
\`wordLevelAligned=false\` et la méthode
\`measured-synthesized-pcm-phrase-onsets-not-word-aligned\`. Sans
reconnaissance acoustique ou alignement forcé supplémentaire (par
exemple une voie locale optionnelle Whisper avec contrôle de confiance),
prétendre à une précision phonème/mot serait inexact.

Cette évolution est une amélioration du pipeline réutilisable pour les
**explications quantitatives source-authentifiées**, et non une nouvelle
vidéo optimisée spécifiquement pour le benchmark.

### Tests et reproduction

\`\`\`bash
python -m unittest discover -s tests -p test_universal_scale_speech.py -v
automate-ytb-short \
  --topic "How a glowing thread changes scale" \
  --script-file examples/universal_pcm_phrase_scale_story.en.txt \
  --language en --voice espeak --width 720 \
  --output build/universal/pcm-phrase-scale-original.mp4
python -m automate_ytb.shorts_delivery \
  --video build/universal/pcm-phrase-scale-original.mp4 --require-audio
\`\`\`

Le workflow GitHub encode un MP4 720×1280 H.264/AAC avec **quatre phrases
de nombre et quatre phrases d'objet** distinctes. Le contrôle vérifie
leurs décalages réels, leur conservation dans le rapport et les huit
effets sonores correspondants. Les tests du repo entier et le vrai rendu
neural Kokoro restent des portes de validation séparées avant toute fusion.

### Étape suivante

L'alignement acoustique mot à mot optionnel, avec couverture/confidence
vérifiables, devra compléter — et non remplacer mensongèrement — ces
ancrages de phrases. Ensuite, améliorer l'élasticité des mouvements,
la direction visuelle et la dramaturgie musicale et sonore pour réduire
l'écart encore considérable avec 3561.mp4.
