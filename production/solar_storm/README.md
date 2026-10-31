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
- `shot_contact_sheet.jpg`: each of the **13 actual edited NASA shots** sampled
  from the final encoded Short; label text appears **only on the review sheet**.
- `shot_review.json`: source key, narration scene, extracted timestamps,
  black frame checks and possible repeated frames for all edited shots.
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

The shot-level reviewer checks the encoded 13-shot timeline against the final
video duration, requires six narration scenes and rejects corrupt or fully
black sampled frames. It also compares actual RGB thumbnails before flagging
lookalikes, avoiding misleading similarity warnings from false-color NASA
footage that has different color palettes. These are still technical checks;
full-motion continuity and factual framing require human approval.

## Télécharger une nouvelle vidéo vérifiée depuis Android

1. Dans [Actions → Produce Solar Storm short — NASA + Kokoro](../../.github/workflows/solar-storm-documentary.yml), lancer la production depuis `main` et vérifier que son workflow termine avec succès.
2. Ouvrir [Actions → Publish verified Solar Storm MP4 — selected run](../../.github/workflows/publish-solar-storm-video.yml) → **Run workflow**. Laisser `source_run_id` vide pour choisir **la production la plus récente de `main`**. Si cette dernière a échoué ou n'est pas terminée, la publication échoue au lieu de récupérer silencieusement une ancienne vidéo. Facultatif : renseigner l'identifiant exact d'une production réussie.
3. Récupérer l'URL directe du MP4 dans le résumé du workflow de publication. Chaque exécution validée possède un tag et un lien GitHub Release **distinct**, sans remplacement d'une autre vidéo.

Le workflow de publication vérifie l'origine GitHub Actions, le commit source, le MP4 réel (H.264 1080×1920 à 30 fps et audio AAC 48 kHz), le rapport QA, les six scènes et les treize plans décodés avant d'exposer les fichiers. Il fournit également un manifeste `release-provenance.json` avec l'empreinte SHA-256 du MP4. Les anciens artefacts de GitHub Actions expirent : si les fichiers source n'existent plus, la publication refuse de continuer.

Il s'agit d'un **téléchargement public demandé explicitement**, pas d'une publication YouTube. Le drapeau `editorial_approved=false` est conservé ; l'exactitude scientifique, la voix, le montage et les droits doivent être contrôlés humainement. L'ancien lien daté de 2026 n'est pas automatiquement remplacé et ne doit pas être présenté comme « dernière version ».
