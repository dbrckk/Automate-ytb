# Automate-ytb — studio de vidéos YouTube originales

Première version fonctionnelle inspirée des **étapes** de la démonstration vidéo : étudier une niche, définir un concept, écrire une narration, composer des scènes, produire une voix, assembler une vidéo, créer des miniatures et préparer sa diffusion. Ce dépôt **ne copie pas** les vidéos ni les personnages de Murph.

## Ce que fait la V1

- **Recherche de niches** : analyse en lecture seule des résultats de l’API officielle YouTube, avec vues, ancienneté et abonnés visibles. Ces indicateurs ne prouvent ni les revenus ni la saturation réelle d’une niche.
- **Création de brouillons** : à partir d’un sujet, d’un angle, d'un script personnel facultatif et de faits accompagnés de leurs sources HTTPS.
- **Storyboard** : scènes et illustrations originales générées localement avec Pillow. Des images détenues ou licenciées peuvent être placées dans `assets/scene-01.png`, etc.
- **Montage** : assemblage FFmpeg des scènes avec transitions simples, audio narratif fourni ou TTS eSpeak, sous-titres SRT, et trois miniatures.
- **Livrables** : projet JSON, narration, plan de montage, vidéo MP4, miniatures, métadonnées YouTube et liste de contrôles éditoriaux.
- **Depuis Android** : lancer les workflows `Actions` sur GitHub puis récupérer l’artefact téléchargeable. Aucun PC personnel obligatoire.

La V1 **n’inclut pas** de génération cinématique IA photoréaliste, de clone de voix, de recherche factuelle IA sans vérification, de montage identique à la vidéo de référence ni de publication automatique YouTube. Les visuels locaux sont des cartes graphiques originales qui servent de base au montage. Pour des images et animations plus sophistiquées, utiliser des fournisseurs avec droits d’utilisation vérifiés et injecter les médias approuvés dans le storyboard.

## Nouvelle action Android : vidéo complète de brouillon

**[One-click YouTube preview (free)](https://github.com/dbrckk/Automate-ytb/actions)** permet désormais de préparer des scènes originales depuis un scénario fourni, de générer des illustrations procédurales sans coût d'API, d'enregistrer une voix provisoire eSpeak, de monter un MP4 (720p ou 1080p), de produire les sous-titres et trois miniatures. Le tout est téléchargeable comme artefact GitHub Actions, sans PC personnel.

**Important :** les cartes illustrées sont des **brouillons graphiques** ; ce n'est pas encore une vidéo IA à la qualité de Murph. Aucun contenu n'est publié sur YouTube. Ne pas transmettre de texte confidentiel aux entrées Actions d'un dépôt public.

Guide : [Production Android en un workflow](docs/ONE_CLICK_ANDROID.md).

## Formats YouTube 16:9 et Shorts 9:16

Le workflow Android gratuit exporte désormais aussi un **clip vertical 720×1280**
à partir du MP4 horizontal, avec fond flouté, audio conservé et sous-titres
SRT recalés sur l'extrait. Pour l'instant, il prend les 30 premières
secondes, sans prétendre sélectionner les meilleurs moments.
Voir le [guide Android](docs/ONE_CLICK_ANDROID.md).

## Guide rapide sur GitHub / Android

1. Ouvrir l’onglet **Actions** du dépôt puis **Generate YouTube draft**.
2. Choisir **Run workflow**, renseigner le sujet, la langue, le style et la durée. On peut également fournir son propre texte.
3. Ouvrir le run terminé, télécharger l’artefact `automate-ytb-video-draft` dans la rubrique **Artifacts**.
4. Vérifier les sources, les images, la prononciation, les droits des médias, les métadonnées et la qualité de la vidéo **avant toute publication manuelle**.

Pour découvrir des niches, définir un secret de dépôt nommé `YOUTUBE_API_KEY` (clé personnelle Google Cloud autorisée à utiliser YouTube Data API v3), puis lancer **Discover YouTube niches**. Ne pas placer de clé dans les fichiers ou les logs.

## Production multi-scènes : nouveauté

Le pipeline peut désormais planifier **150 plans pour un épisode de 15 minutes** et
exporter un lot de prompts image compatibles avec des fournisseurs interchangeables.
Chaque image importée est contrôlée (source/droits déclarés, empreinte SHA-256, coût),
puis les scènes prêtes peuvent être assemblées en **MP4 avec léger mouvement de caméra**
par FFmpeg. Le rendu reprend les segments déjà préparés après une interruption.

Depuis Android, ouvrir **Actions → Prepare original image-scene batch** pour obtenir
un kit de production sans payer d'API. Les images ne sont **pas générées par ce workflow** ;
l'intégration au fournisseur d'images sera une étape distincte et soumise au budget.

Voir [le guide de production scène par scène](docs/IMAGE_SCENE_PIPELINE.md).


Python 3.11+, FFmpeg, éventuellement `espeak-ng`, et :

```bash
python -m pip install -e .
python -m automate_ytb create \
  --topic "Pourquoi la lune change-t-elle de forme ?" \
  --angle "Une explication pédagogique et visuelle" \
  --style cartoon --language fr --duration 90 \
  --output outputs
```

Pour uniquement produire le storyboard et les fichiers de plan :

```bash
python -m automate_ytb create --topic "Une question originale" --plan-only
```

Pour la recherche officielle YouTube :

```bash
export YOUTUBE_API_KEY="VOTRE_CLE"
python -m automate_ytb discover --queries "science animation" "historical facts" \
  --min-views 20000 --max-subscribers 100000
```

Tests :

```bash
python -m unittest discover -s tests -v
```

## Repères tirés de la vidéo fournie

La vidéo montre une chaîne d'animation explicative (Murph), des indicateurs YouTube Studio, des exemples de contenu illustré, des instructions textuelles dans Codex et un outil de génération de séquences vidéo. Nous avons transposé **l’organisation de la production**, pas les créations tierces ni les chiffres présentés.

## Intégration à Star List

`dbrckk/star-list` reste le catalogue de ressources à évaluer pour les évolutions. Les familles intéressantes sont : **FFmpeg** et outils de montage, **Kokoro** ou autres solutions de voix autorisées, **StoryDiffusion** et outils visuels, **MoneyPrinterTurbo** pour l'orchestration, et les outils de génération d'assets 3D. Ces dépôts sont des **candidats**, non des dépendances intégrées dans la V1. Examiner licences, droits commerciaux, exigences de calcul et API avant adoption.

## Contrôles de qualité

- Aucune promesse de revenus YouTube ou de monétisation.
- Aucune récupération automatique de vidéos/images de chaînes concurrentes.
- Les faits importés ont une provenance explicite ; la présence d’une URL ne suffit pas à les vérifier.
- L'utilisateur reste responsable des droits de voix, musique, images, titres et clips.
- Toute mise en ligne passe par une validation explicite ; le système produit des brouillons, non des publications autonomes.

### Narration neuronale optionnelle

La création de brouillons propose maintenant une voix **Kokoro-82M** en français
ou anglais, activée uniquement si voice=kokoro est sélectionné dans GitHub Actions.
La voix eSpeak reste le choix le plus léger par défaut. La durée réelle des
enregistrements ajuste les scènes afin de ne pas couper la narration.
Les sous-titres ne sont pas encore alignés mot par mot. Kokoro télécharge
ses poids et demande davantage de calcul sur le runner.

Voir le [guide de narration neuronale](docs/NATURAL_NARRATION.md).

### Réalisation contextuelle des scènes

Le storyboard peut désormais inférer des **consignes visuelles non factuelles**
depuis le scénario original : jour/nuit, pluie, vent, nuages, action des ailes,
expressions et types de plans. Elles pilotent les décors et les calques animés
dans le workflow gratuit et sont attachées aux images approuvées pour éviter
la réutilisation de scènes obsolètes. Ce moteur est fondé sur des mots-clés,
pas sur un modèle de compréhension complète. Voir
[le guide Android](docs/ONE_CLICK_ANDROID.md).

### Animation procédurale originale

Le workflow Android gratuit inclut désormais une **chouette 2D articulée**
(ailes indépendantes, oscillation du corps, clignements) lorsque la description
du personnage contient owl, chouette ou hibou, en style cartoon.
La vidéo est calculée à partir de calques originaux avec FFmpeg, sans API payante.
Les autres personnages restent pour l'instant sur des visuels de brouillon.
Cette animation est plus vivante qu'un diaporama, mais n'atteint pas encore
la qualité visuelle de la référence ni une animation universelle des personnages.

## Nouveau : aperçu vidéo complet depuis Android, sans API payante

Le workflow **[One-click offline video preview](https://github.com/dbrckk/Automate-ytb/actions/workflows/one-click-offline-video.yml)** transforme un scénario original en MP4 16:9, illustrations 2D originales cohérentes, voix eSpeak optionnelle, sous-titres SRT, couverture et rapports de production. Il fonctionne dans GitHub Actions, même sans PC, et ne demande aucune clé d'un service de génération d'images.

Ce mode utilise des **dessins procéduraux** et une **voix synthétique** : ce n'est pas encore la qualité visuelle ni la voix neuronale des outils IA montrés dans la vidéo de référence. Il ne recherche pas de faits automatiquement et ne publie rien sur YouTube. Pour les détails, voir [le guide Android](docs/ONE_CLICK_OFFLINE_EPISODE.md).
