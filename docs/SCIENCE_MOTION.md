# Mode scientifique animé (expérimental, gratuit)

Ce mode utilise des illustrations **originales**, produites localement par Pillow et assemblées en vidéo H.264 par FFmpeg. Il crée des plans réellement animés à **30 images/seconde**, avec les mêmes contrôles d’intégrité des ressources, de voix, d’audio et de sous-titres que le moteur courant.

## Périmètre réel

- **Sujets pris en charge :** phénomènes liés à la Terre, à ses océans et à l’atmosphère, évoqués explicitement dans le **titre**. L’illustration de la sphère est schématique ; ni une carte exacte ni une simulation physique.
- **Plans disponibles :** rotation/orbite schématique, circulation atmosphérique, vagues océaniques, éclairage jour/nuit ; ils sont sélectionnés à partir des phrases françaises ou anglaises du script.
- **Formats :** sortie encodée en 720p ou 1080p, toujours en 30 fps dans ce mode. Les scènes animées en 1080p sont désormais dessinées **directement à 1920×1080** : ciel, étoiles, globe calculé à 612 px, contours, annotations et typographie vectorielle. La miniature d'approbation statique reste en 1280×720 (ce n'est pas la résolution de la vidéo exportée).
- **Inexactitudes possibles :** chiffres scientifiques, géographie, mouvements astronomiques et contenu du script doivent être revus indépendamment. L’IA ne recherche ni ne vérifie les faits en générant ces images.
- **Licence/coûts :** pas de médias externes importés et pas de modèle graphique payant. Kokoro est facultatif et peut nécessiter un téléchargement lors de la première utilisation. Les quotas GitHub Actions habituels restent applicables.
- **Publication :** aucune mise en ligne automatique ni approbation éditoriale implicite.

## Android — prévisualisation

1. Ouvrir **Actions → One-click YouTube preview → Run workflow** sur GitHub.
2. Choisir **style = science**, un titre explicite sur la Terre ou les océans, un script original avec suffisamment de phrases et un personnage de type **Original astronomy graphics**.
3. Sélectionner **1080p** et, pour la qualité d'encodage, **render_profile = high**. Choisir **voice = kokoro** pour la synthèse neuronale si le runner dispose des ressources nécessaires.
4. Lire la vidéo MP4 et écouter le fichier `voice-sample.mp3` de l'artefact, contrôler la lisibilité des chiffres et corriger toute erreur factuelle avant publication.

En ligne de commande, utiliser `python -m automate_ytb.episode --style science --render-profile high --resolution 1080p --voice kokoro --plan scene-plan.json --output out` après avoir généré un plan avec `python -m automate_ytb.scene_plan`.

## Shorts 9:16 (1080×1920 natif)

Le choix **resolution = shorts** dans **Actions → One-click YouTube preview** est réservé au style `science`. Il produit une vidéo originale 1080×1920 à **30 images/seconde** : ce n'est ni le recadrage ni l'agrandissement d'une vidéo 16:9. Le moteur dispose d'une composition verticale indépendante, avec globe ou phénomènes atmosphériques et océaniques adaptés à l'écran mobile. Les titres et **sous-titres visibles phrase par phrase** sont placés dans des zones séparées, pensées pour les principales interfaces de Shorts/TikTok/Reels. Les mêmes séquences temporelles sont utilisées pour le texte incrusté dans la vidéo et le SRT : si `voice = kokoro` ou `espeak` et `caption_timing = audio`, les changements de phrase suivent les débuts de fragments de voix synthétisés. Les temps ne sont pas vérifiés mot par mot ; sans voix ou en mode `estimated`, ils sont calculés proportionnellement au texte. La revue visuelle et l'écoute sur l'application cible restent indispensables.

Le poster d'approbation reste en 1280×720 : sa géométrie diffère donc volontairement du film vertical. Le contrôle final doit porter sur le **MP4 généré**, pas uniquement sur le poster. Les scripts restent originaux, les légendes complètes sont exportées en SRT/VTT, la narration Kokoro est facultative et l'export ne publie rien automatiquement. Les sujets non liés à la Terre ou aux océans ne sont pas représentés par une fausse animation.

Pour Android : sélectionner `style = science`, `resolution = shorts`, `render_profile = high` et, si souhaité, `voice = kokoro`. Les vérifications du pipeline et `tests/test_science_shorts.py` contrôlent la taille exacte, le mouvement entre les images, les limitations d'entrée et le vrai codec H.264.

## Revue visuelle native 9:16 sur Android

Le workflow **One-click YouTube preview** extrait maintenant les planches de contrôle directement du MP4 final en conservant son ratio d’image. Pour une vidéo verticale 1080×1920, chaque échantillon est décodé en **360×640** (format 9:16) et inséré dans un aperçu portrait de **quatre scènes par page**, sans découpage 16:9. Les bandes des titres et les sous-titres restent entièrement visibles pour une vérification sur smartphone. Les vidéos horizontales conservent leurs huit scènes par page et leur rendu habituel. Le rapport `review/visual-review.json` expose l'orientation, les dimensions des images et le nombre de scènes par planche.

Les scènes approuvées avec le rig `original-science-v1` et le style `science` sont aussi soumises à la détection d’animations figées sur **deux images réellement décodées du MP4**. Une animation scientifique complètement immobile déclenche une erreur technique ; les plans documentaires volontairement fixes restent autorisés. L'échantillonnage demeure limité et ne certifie ni la qualité cinématographique ni l'exactitude des faits.

## Intégrité des planches de contrôle

La validation technique finale ne se contente plus d’un rapport JSON affirmant que les captures du MP4 sont correctes. Le générateur de planches enregistre l'empreinte **SHA-256 de chaque JPEG** réellement produit. La consolidation `qa_bundle` exige ensuite que toutes les planches annoncées existent, soient des JPEG décodables en **1120×2030**, aient exactement les empreintes annoncées et présentent une orientation et un nombre de pages cohérents avec les dimensions du MP4. Une capture manquante, déplacée, altérée, tronquée ou substituée empêche la mention `technicalPreviewReady`. Les anciens rapports en schéma v2 restent lisibles, sans revendiquer cette vérification supplémentaire. Ce contrôle ne prouve pas la qualité artistique ni l’absence de zones masquées : l'approbation éditoriale demeure humaine.

## Typographie mobile sans perte de texte

Les titres et les sous-titres incrustés en mode `shorts` sont désormais mis en lignes en tenant compte de leur largeur réelle : le moteur adapte la taille des glyphes dans les limites de lisibilité, répartit aussi les termes techniques trop longs et évite les points de suspension qui supprimaient parfois des mots. Tous les textes des phrases sont contrôlés avant l'encodage des images. Un titre ou un fragment incompatible avec la zone réservée provoque une erreur explicite : il doit être raccourci ou découpé dans le script, sans supprimer silencieusement du contenu. Le SRT exporté conserve son contenu intégral. Les vidéos précédemment mises en cache sont invalidées pour le rendu portrait. Cette sécurité typographique ne remplace pas l'inspection du film sur téléphone.

## Rendu 1080p natif

Le choix `resolution=1080p` alloue un canevas 1920×1080 et calcule directement les images originales à cette résolution avant encodage H.264. Contrairement à l'ancienne version, le rendu n'agrandit plus une image 720p en fin de processus. Il conserve la même composition graphique, avec des épaisseurs de trait, rayons, glyphes et éclairages adaptés. L'option 720p reste inchangée et moins coûteuse en calcul. Les images de présentation/validation sont toujours générées en 720p ; cette différence est volontaire et documentée.

## Continuité et coût de rendu

La rotation schématique de la Terre reste active au-delà de la cinquième seconde d'un plan. Les différentes orientations sont calculées seulement lorsqu'elles sont visibles, puis conservées dans un cache mémoire borné à huit poses. Les scènes d'océan et d'atmosphère ne chargent aucune sphère terrestre inutile. Cela réduit les calculs superflus et évite le gel visuel de l'ancien moteur, sans prétendre reproduire fidèlement la vitesse réelle de rotation de la Terre.

## Courants océaniques multicouches (Shorts 9:16)

Les scènes de mode `ocean` combinent désormais quatre couches de vagues animées avec **trois courants d'eau indépendants**, des particules à traînée lumineuse et deux tourbillons dont l'orientation évolue continûment à **30 images/seconde**. Les lignes de courant et leurs vitesses restent différentes selon la profondeur. Ce sont des graphiques originaux générés localement, et non une carte physique des courants ou une simulation hydrodynamique. Les éléments sont positionnés dans la bande visuelle centrale afin de préserver les titres, les légendes et les contrôles de l’interface mobile. La cache des clips portrait a été invalidée pour que les vidéos précédentes ne masquent pas cette évolution.

Les régressions vérifient des images distinctes d'une frame à l'autre, un rendu reproductible, l’activité des trois courants, l’absence de globe chargé dans le mode océan et les sous-titres inchangés. Une revue éditoriale du MP4 reste nécessaire, en particulier pour les sujets scientifiques spécifiques où ces courants schématiques ne doivent pas être interprétés comme une représentation exacte.

## Rotation continue pour les Shorts (9:16)

Les plans verticaux animés interpolent maintenant les deux orientations calculées les plus proches du globe à chaque image (30 fps). Cela limite les saccades de la carte terrestre visibles auparavant toutes les 0,4 seconde, sans exécuter la coûteuse projection complète de la sphère à chaque nouvelle image. Le cache conserve au maximum six poses, avec des clés distinctes selon l'orientation et la résolution. Cette interpolation visuelle ne constitue pas une simulation physique ; une revue du film exporté demeure indispensable. Le rendu horizontal et les vidéos documentaires NASA restent inchangés.

## Optimisation CPU du globe

Le moteur réutilise maintenant, entre les différentes orientations de la Terre, son atlas original de continents et son halo pré-calculé par résolution. Les calculs dépendant uniquement de la latitude (échantillonnage vertical, nuages et glace polaire) sont effectués une fois par ligne plutôt que pour chaque pixel. Les images rendues conservent leur résolution réelle et les mêmes formules de couleur, sans ajouter de dépendance ni consommer de crédits de génération. Le nombre d’orientations stockées par scène reste borné. Les tests vérifient des couleurs de pixels contre les équations de référence, la stabilité des résultats et l’absence de mutation des ressources mises en cache. Aucun gain chiffré n’est affirmé sans mesure sur un environnement de production.

## Vérifications de sortie

Les régressions `tests/test_science_motion.py` couvrent les quatre modes visuels, les images successives distinctes, l’empreinte des ressources de la narration et un vrai H.264 à 30 fps. La CI doit réussir l'ensemble de la chaîne avant fusion, et une revue humaine doit contrôler le film complet. Des animations multisciences généralisables, une direction artistique native 1080p et l'alignement mot à mot fiable restent des objectifs futurs.
