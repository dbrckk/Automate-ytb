# Analyse de la référence Murph et sélection complète Star List

**Date :** 22 octobre 2026 · **Source fournie :** `2929.mp4` · **Lien d'origine :** https://x.com/Ithielix/status/2112780512548823426

## 1. Qualité du média et périmètre réellement analysé

Le MP4 annonce 796,47 secondes (13 min 16 s), H.264 1920×1080 / 60 i/s, audio AAC stéréo. Il ne contient physiquement qu'environ 68 secondes récupérables : FFmpeg signale `partial file`, `Invalid NAL unit size`, et 4 081 images décodées contre 47 786 annoncées. L'audio récupéré dure 68,01 secondes. Impossible de reconstituer la suite à partir de ces octets.

**Ne pas présenter la suite comme visionnée.** Ni les outils employés, ni les prompts, ni le coût d'une chaîne totalement automatisée ne sont démontrés par les seules 68 secondes présentes. Le pipeline ci-dessous est une **reconstruction de conception**, non le procédé exact du créateur.

### Repères visuels récupérés

| Temps | Observation vérifiable | Interprétation prudente |
|---|---|---|
| 00:00–00:08 | Chaîne **Murph**, @Murph-b5y, environ 15 000 abonnés et 49 vidéos sur la page affichée. Illustrations 2D colorées, personnages aux expressions fortes, miniatures à grosses lettres jaunes, thèmes « pourquoi ». | Viser des vidéos explicatives originales en 2D avec mascottes récurrentes et identité visuelle maîtrisée. |
| 00:09–00:17 | Panneau NexLev : 3 563 281 vues et 9 158 $ indiqués sur 30 jours. | Un tableau de bord tiers ne prouve pas des revenus effectivement encaissés. |
| 00:18–00:56 | YouTube Studio : 7 127 649 vues sur 90 jours, 432 300 heures, +65 800 abonnés, 14 453,36 $ de revenus **estimés**, écran du compte flouté. | Impossible d'attribuer avec certitude ce tableau à la même chaîne Murph. |
| 00:57–01:08 | Retour à la page Murph et aux miniatures/cartes d'épisodes. | Aucune séquence de production détaillée n'apparaît dans l'extrait récupérable. |

**Attention :** la page publique de Murph affiche ~15 000 abonnés, tandis que le panneau privé non identifiable affiche 65 996 abonnés. Les valeurs ne doivent pas être fusionnées ni prises pour des preuves de rentabilité.

### Style de référence à traduire en création originale

- **Format principal :** épisodes explicatifs 16:9 de plusieurs minutes, Shorts dérivés dans un second temps. Une miniature comporte une durée affichée de 34:07.
- **Concept :** curiosités du quotidien, animaux, science accessible, questions intrigantes.
- **Identité :** mascotte et personnages expressifs, décor cartoon 2D, traits lisibles, couleurs saturées, typographie forte, compositions simplifiées.
- **Réalisation :** illustrations originales et animations explicatives. S'inspirer du langage visuel **sans copier les personnages, les miniatures ou des scènes de Murph**.
- **Rétention :** mise en place rapide d'une question, progression narrative, démonstrations visuelles, renouvellement des cadrages, conclusion claire et factuelle.

## 2. Audit de l'ensemble du catalogue Star List

Snapshot examiné de `dbrckk/star-list` : **1 062 dépôts GitHub, 27 sites web**, sans exclusion de la catégorie `indexed`. Neuf thèmes de recherche ont été couverts : niches, scénario, voix, illustration, animation, montage, miniature, orchestration et analytics.

Le moteur présente 403 entrées nécessitant une vérification de métadonnées ou d'état, dont 131 licences non résolues et 347 informations d'auto-hébergement non vérifiées. Ces groupes se recoupent. **Zéro entrée dans l'ancienne file `audit` ne signifie pas zéro vérification à faire.**

Les suggestions suivantes ont été reclassées **manuellement selon le besoin précis de ce projet** : une ressource recommandée pour la génération d'images n'est pas automatiquement pertinente pour écrire un scénario ni pour publier sur YouTube. Les notes /5 mesurent la **priorité d'examen pour Automate-ytb**, pas la qualité absolue des dépôts.

| Priorité | Ressource référencée dans Star List | Score /5 | Usage pressenti et réserve |
|---|---|---:|---|
| P0 | [motion-canvas/motion-canvas](https://github.com/motion-canvas/motion-canvas) | 5,0 | Moteur TypeScript d'animation vectorielle/2D reproductible, MIT indiqué dans le catalogue. Première piste pour éliminer les diapositives statiques. |
| P0 | [FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) | 5,0 | Assemblage vidéo/audio, transitions, effets, export, contrôles techniques. Déjà présent dans la V1. Licence indiquée NOASSERTION dans Star List : examiner les conditions LGPL/GPL et la distribution réelle. |
| P0 | [JohnHeibel/ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase) | 4,8 | Approche animations de personnages dessinés avec p5.js/p5.brush et émotions. Référence de technique, pas d'assets à recopier. |
| P0 | [hexgrad/kokoro](https://github.com/hexgrad/kokoro) | 4,8 | TTS naturel et multilingue, sous réserve des modèles/voix et conditions de déploiement. Remplacer eSpeak comme voix principale. |
| P0 | [openai/whisper](https://github.com/openai/whisper) | 4,7 | Transcription et base d'alignement des sous-titres. Synchronisation fine à vérifier selon modèle et langue. |
| P1 | [HBAI-Ltd/Toonflow-app](https://github.com/HBAI-Ltd/Toonflow-app) | 4,7 | Référence d'architecture pour scénario, storyboard, personnages et production de motion comics. Licence MIT indiquée, dépendances/modèles à examiner. |
| P1 | [kaomei/stickman-video-director](https://github.com/kaomei/stickman-video-director) | 4,6 | Inspiration pour découpage de scènes et prompts d'animation de personnages simples. Ne pas adopter les directives externes sans examen. |
| P1 | [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | 4,6 | Organisation du flux de production ; réutiliser des idées techniques vérifiées, pas du contenu préfabriqué non original. |
| P1 | [Asad-Ismail/MoneyPrinterTurbo-Extended](https://github.com/Asad-Ismail/MoneyPrinterTurbo-Extended) | 4,5 | Sous-titres mot-à-mot, TTS et recherche d'extraits pertinents décrits dans README ; vérifier implémentation, services et droits des médias. |
| P1 | [HVision-NKU/StoryDiffusion](https://github.com/HVision-NKU/StoryDiffusion) | 4,5 | Cohérence de personnages dans des séquences d'images / génération illustrée. Ressources GPU, poids et licences des modèles à vérifier. |
| P1 | [ATH-MaaS/Pixelle-Video](https://github.com/ATH-MaaS/Pixelle-Video) | 4,3 | Moteur de génération de courtes vidéos automatisées, à évaluer pour des modules indépendants. |
| P1 | [OpenBMB/VoxCPM](https://github.com/OpenBMB/VoxCPM) | 4,3 | Moteur audio/voix alternatif, selon résultat d'écoute et coût de calcul. |
| P2 | [higgsfield-ai/skills](https://github.com/higgsfield-ai/skills) | 4,4 | Interface de compétences pour génération visuelle et marketing ; **services externes** pouvant nécessiter authentification/crédits. Licence du code ≠ droit gratuit de génération. |
| P2 | [Lightricks/LTX-Video](https://github.com/Lightricks/LTX-Video) | 4,1 | Animation/génération de plans avancés, mais forte charge GPU et vérification des poids. Ne doit pas bloquer une V2 qui fonctionne sans GPU. |
| P2 | [Anil-matcha/AI-Youtube-Shorts-Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) | 4,0 | Découpage de longs épisodes en Shorts 9:16 avec recadrage et transcription, après stabilisation du format long. |
| P2 | [OpenCut-app/OpenCut](https://github.com/OpenCut-app/OpenCut) | 4,0 | Référence d'interface et de montage manuel/visuel ; éviter d'empiler plusieurs éditeurs. |
| Option | [n8n-io/n8n](https://github.com/n8n-io/n8n) | 3,9 | Orchestration facultative. Licence **Sustainable Use License** : vérifier la compatibilité avant redistribution/service. Un orchestrateur Python simple peut suffire initialement. |
| Option | [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | 4,2 | Alternative React à Motion Canvas pour montage programmatique. Conditions commerciales et licence à vérifier ; éviter deux moteurs concurrents en V2. |
| Option | [calesthio/OpenMontage](https://github.com/calesthio/OpenMontage) | 3,8 | Référence d'édition/génération, avec contraintes AGPL-3.0. |
| Option | [comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI) | 3,9 | Workflows reproductibles d'images. GPU / dépendances importants ; privilégier des fournisseurs interchangeables plutôt qu'imposer ComfyUI. |

### Références web examinées parmi les 27

| Site | Utilité réelle pour Automate-ytb |
|---|---|
| [Hugging Face](https://huggingface.co/) | Comparer et versionner TTS, illustration, diffusion et vision. Catalogue de modèles, **pas** garantie d'inférence gratuite. |
| [FLUX.3 Image Klein GGUF](https://huggingface.co/AtomicChat/FLUX-3-Image-Klein-GGUF) | Piste d'illustrations locales si le matériel, les poids et les droits sont adaptés. |
| [FastH3 Omni](https://huggingface.co/collections/FastVideo/fasth3-omni) | Collection à examiner pour génération vidéo, non un moteur prêt à être intégré. |
| [Viggle PINOC MCP](https://viggle.ai/pinoc/mcp) | Essais de transfert/mouvement de personnages, dépendance au fournisseur et aux prix. |
| [Skill Issue](https://skill-issue.in/) | Recherche de compétences d'agents. Toute instruction ou commande externe doit être contrôlée avant usage. |
| [60fps.design](https://60fps.design/) | Références de mouvement et rythme visuel, pas composant de rendu. |
| [SoPilot](https://sopilot.net/) | Marketing et distribution, secondaire par rapport à la qualité du contenu. |

Les autres sites du catalogue (NPC pour jeux, design d'interfaces, création de jeux, etc.) restent disponibles mais ne doivent pas être installés par défaut : ils ne résolvent pas le problème de l'animation explicative YouTube.

## 3. État actuel du dépôt Automate-ytb

Les modules existants comprennent `automate_ytb/studio.py`, `automate_ytb/youtube.py`, CLI et workflows GitHub Actions. La V1 sait réaliser des brouillons, créer des images Pillow, des pistes eSpeak ou fournies, composer des MP4 via FFmpeg, générer SRT et miniatures, et consulter des données publiques de niches via YouTube Data API.

**Écart principal par rapport à la référence visuelle :** rendu largement fondé sur des scènes fixes ; pas de mascottes originales animées de manière continue, pas de charte graphique multi-épisodes avec rig réutilisable, TTS eSpeak peu naturel, ni contrôle robuste du rythme narratif sur des épisodes longs.

## 4. Architecture proposée : une chaîne complète mais modulaire

**Entrée :** sujet, langue, durée, audience, préférence visuelle, sources. **Sortie :** MP4 16:9 original, miniature(s), SRT, description, preuves de sources, manifest de droits, brouillon de publication.

1. **Recherche :** API YouTube officielle pour les performances observables + collecte documentaire citée ; séparer idées de concurrents et réutilisation non autorisée de médias.
2. **Scénario :** générer une question, un hook, un plan narratif, des affirmations sourcées et une chronologie de scènes ; vérification des faits et distinction entre information et hypothèse.
3. **Style bible :** construire une mascotte **originale**, sa fiche de poses et d'expressions, une palette, des décors, des règles de typographie et une graine visuelle cohérente par épisode.
4. **SceneSpec :** fichier JSON par scène avec durée, texte narré, sujet, personnages, expression, animation, mouvement caméra, effets et preuves de propriété des médias.
5. **Voix :** Kokoro comme moteur candidat, fournisseur TTS alternatif, prononciation, pauses, variation d'intonation ; Whisper pour alignement et vérification.
6. **Images et animation :** Motion Canvas pour l'animation reproductible 2D ; génération d'images optionnelle et contrôlée ; génération vidéo GPU uniquement pour les plans justifiant ce coût.
7. **Montage :** FFmpeg, timecodes fiables, transitions motivées, musique légalement utilisable, effets et contrôle du niveau sonore ; reprise de travail sans tout régénérer.
8. **Miniatures et publication :** trois créations distinctes, revue visuelle, métadonnées, contrôle des droits, upload OAuth d'abord **privé** puis publication autorisée.
9. **Boucle d'apprentissage :** analytics de la chaîne connectée (durée moyenne, visionnage, vues, CTR quand disponible), comparaison des vidéos et révision des futurs scénarios, sans chiffres inventés.

## 5. Priorités d'implémentation

**P0 / prochaine itération :** ajouter `SceneSpec`, créer une mascotte originale et un renderer 2D Motion Canvas configurable ; conserver l'éditeur FFmpeg existant ; produire un épisode d'essai **réellement animé**, pas un diaporama.

**P1 :** ajouter un TTS naturel derrière une interface de fournisseur interchangeable et synchroniser précisément les sous-titres avec l'audio final.

**P2 :** exporter automatiquement un storyboard contrôlable, des images cohérentes et une charte graphique persistante. Empêcher les pertes de continuité entre les scènes et les épisodes.

**P3 :** rendre le pipeline reprenable et consultable sur Android : étapes, statut, prévisualisation, journal, coût estimé des fournisseurs, téléchargement des artefacts GitHub Actions.

**P4 :** niche/scénario sourcé, qualité éditoriale, analytics officiels, titres/miniatures et publication par OAuth avec consentement explicite.

### Critères d'acceptation avant de qualifier la V2 de stable

- Vidéo d'essai de 2 à 3 minutes avec scénario original vérifiable, **animations continues**, personnage reconnaissable, plusieurs décors et voix intelligible.
- Export MP4 16:9, SRT correctement synchronisé, miniature exploitable, son propre et absence de coupures/audio manquant.
- Modes gratuit/CPU et fournisseurs GPU/hosted clairement séparés ; toute erreur fournisseur doit laisser un projet reprenable.
- Ne jamais déduire un droit d'exploitation d'une simple étiquette de licence dans Star List. Vérifier code, poids, médias, dépendances et conditions commerciales.
- Respecter la politique YouTube sur le contenu original et la production en masse. Source : https://support.google.com/youtube/answer/1311392
- Upload YouTube via API : https://developers.google.com/youtube/data/reference/rest/v3/videos/insert . `privacyStatus` doit être défini explicitement à `private` par défaut.

**Limite de preuve :** pour une analyse réellement minute par minute de 01:08 à 13:16, il faut remplacer le fichier par sa version complète non tronquée. En aucun cas ce document ne prétend avoir visionné la séquence manquante.
