# Audit de production Automate-ytb — 31 octobre 2026

## Périmètre et niveau de preuve

Inspection des fichiers `automate_ytb/science_portrait.py`, `automate_ytb/narration.py`, `automate_ytb/episode.py`, `automate_ytb/review_board.py`, `automate_ytb/qa_bundle.py`, des workflows GitHub Actions de prévisualisation/validation et de la configuration `pyproject.toml`. Le rapport évalue le **code et les contrats de validation** ; il ne prétend pas avoir visionné et écouté une release finale. Une CI qui passe avec eSpeak n'est pas une preuve de naturel du timbre Kokoro.

## État constaté

| Domaine | État vérifié dans le code | Limite importante |
|---|---|---|
| Export natif | Moteur original 1080×1920, H.264/30 fps, rendu local Pillow et FFmpeg | Style schématique, ne garantit pas une direction artistique premium |
| Animation | Terre interpolée, vagues/courants et tourbillons temporels, cache borné | Richesse et variété insuffisamment démontrées par des vidéos complètes |
| Narration | Kokoro en français/anglais, plusieurs voix anglaises, styles de débit, audio par phrases | Naturel et prononciation à vérifier sur `voice-sample.mp3` ; alignement non phonétique |
| Captions | Texte complet en zones mobiles, temps de phrases issus du PCM si `caption_timing=audio` | Ne constitue pas un alignement mot par mot |
| Intégrité | Rapports média, empreintes du MP4 et des planches JPEG, détection de plans noirs/figés | Échantillonnage borné, ne détecte pas toutes les erreurs du film |
| Livraison Android | Workflow lançable manuellement, artefact contenant MP4, voix, SRT/VTT et rapports | Dépend des quotas et du temps CPU GitHub Actions ; pas de publication automatique |
| Validation de release | **Avant cet audit :** un workflow lançait un autre workflow avec `gh workflow run`, puis terminait avec un succès | **Défaut majeur :** le succès du premier job ne prouvait pas la réussite du rendu ni des QA du second |

## Corrections apportées dans cette itération

1. La production réelle `one-click-preview.yml` devient un **workflow réutilisable** via `workflow_call`, sans retirer `workflow_dispatch` ni ses 15 paramètres Android.
2. La release `science-shorts-release-candidate.yml` utilise le workflow de production comme **job dépendant**. Un échec Kokoro, FFmpeg, media QA ou consolidation rend donc la release rouge : plus de « succès » lié seulement à l'envoi d'un événement.
3. L'artefact de la production est rattaché à **la même exécution de release**. Le job final ne produit son résumé de réussite qu'après la réussite effective du rendu.
4. L'autorisation `actions: write` nécessaire à la télécommande GitHub est supprimée. La release fonctionne avec `contents: read`.
5. Un test de contrat vérifie les paramètres de la réutilisation, la présence des contrôles réellement exécutés et l'absence de dispatch détaché.

**Limite restante :** une release réussie certifie uniquement que les contrôles techniques automatiques se sont exécutés avec succès. Elle ne certifie ni l'intérêt éditorial, ni les faits scientifiques, ni la qualité de la voix perçue à l'écoute. La release candidate entière doit encore être générée et écoutée.

## Backlog priorisé (sans dispersion)

| Priorité | Travail | Critère d'acceptation factuel |
|---|---|---|
| P0 | Valider la réutilisation du workflow sur GitHub | CI verte pour la PR, puis release GitHub Actions terminée avec MP4, `voice-sample.mp3` et `qa-summary.json` dans le même run |
| P0 | Traiter tout échec d'export natif Kokoro/1080×1920 | La release retourne `failure` en cas d'erreur et fournit logs et fichiers de diagnostic |
| P1 | Revoir l'enregistrement vocal réel en anglais et en français | Écoute humaine, absence de coupures et de longues pauses robotiques, diction/niveaux validés |
| P1 | Auditer visuellement un vrai MP4 complet | Plans narratifs compréhensibles, pas d'étirement/cadrage masqué, 30 fps, aucun sous-titre coupé |
| P1 | Enrichir les visuels à partir de chaque phrase | Rendu et transitions spécifiques au sujet, davantage de variation de plans sans duplication artificielle |
| P2 | Élargir le moteur 9:16 à d'autres sciences | Les sujets hors Terre/océan obtiennent une scène pertinente au lieu d'être rejetés, sans simulation inventée |
| P2 | Mesurer les coûts de calcul et durées GitHub Actions | Durée et consommation constatées sur une release complète avant toute optimisation |
| P3 | Publication sociale | Action explicitement validée par un humain et droits des médias vérifiés ; jamais déclenchée par une CI seule |

## Exploitation depuis Android

Ouvrir **Actions → Verify full 9:16 science Shorts release candidate** puis **Run workflow**. Le job de production intégré doit terminer toutes ses vérifications. Une exécution verte permet ensuite de récupérer l'artefact `automate-ytb-free-preview` dans **cette même exécution**, de contrôler le MP4 et d'écouter l'audio. Ne pas publier sur la seule base d'un indicateur vert.

## Contraintes préservées

Aucun jeton ni API payante, aucune suppression des contrôles d'intégrité, aucun accès en écriture aux ressources GitHub dans la release, aucun changement de la cadence de rendu du moteur ni des sous-titres, aucune publication automatique. Les quotas GitHub Actions restent applicables.
