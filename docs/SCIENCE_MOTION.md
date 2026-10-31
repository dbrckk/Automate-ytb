# Mode scientifique animé (expérimental, gratuit)

Ce mode utilise des illustrations **originales**, produites localement par Pillow et assemblées en vidéo H.264 par FFmpeg. Il crée des plans réellement animés à **30 images/seconde**, avec les mêmes contrôles d’intégrité des ressources, de voix, d’audio et de sous-titres que le moteur courant.

## Périmètre réel

- **Sujets pris en charge :** phénomènes liés à la Terre, à ses océans et à l’atmosphère, évoqués explicitement dans le **titre**. L’illustration de la sphère est schématique ; ni une carte exacte ni une simulation physique.
- **Plans disponibles :** rotation/orbite schématique, circulation atmosphérique, vagues océaniques, éclairage jour/nuit ; ils sont sélectionnés à partir des phrases françaises ou anglaises du script.
- **Formats :** sortie encodée en 720p ou 1080p, toujours en 30 fps dans ce mode. Les illustrations de base sont tracées à 1280×720 ; la sortie 1080p est agrandie, **ce n’est pas de l’art natif 1080p**.
- **Inexactitudes possibles :** chiffres scientifiques, géographie, mouvements astronomiques et contenu du script doivent être revus indépendamment. L’IA ne recherche ni ne vérifie les faits en générant ces images.
- **Licence/coûts :** pas de médias externes importés et pas de modèle graphique payant. Kokoro est facultatif et peut nécessiter un téléchargement lors de la première utilisation. Les quotas GitHub Actions habituels restent applicables.
- **Publication :** aucune mise en ligne automatique ni approbation éditoriale implicite.

## Android — prévisualisation

1. Ouvrir **Actions → One-click YouTube preview → Run workflow** sur GitHub.
2. Choisir **style = science**, un titre explicite sur la Terre ou les océans, un script original avec suffisamment de phrases et un personnage de type **Original astronomy graphics**.
3. Sélectionner **1080p** et, pour la qualité d'encodage, **render_profile = high**. Choisir **voice = kokoro** pour la synthèse neuronale si le runner dispose des ressources nécessaires.
4. Lire la vidéo MP4 et écouter le fichier `voice-sample.mp3` de l'artefact, contrôler la lisibilité des chiffres et corriger toute erreur factuelle avant publication.

En ligne de commande, utiliser `python -m automate_ytb.episode --style science --render-profile high --resolution 1080p --voice kokoro --plan scene-plan.json --output out` après avoir généré un plan avec `python -m automate_ytb.scene_plan`.

## Vérifications de sortie

Les régressions `tests/test_science_motion.py` couvrent les quatre modes visuels, les images successives distinctes, l’empreinte des ressources de la narration et un vrai H.264 à 30 fps. La CI doit réussir l'ensemble de la chaîne avant fusion, et une revue humaine doit contrôler le film complet. Des animations multisciences généralisables, une direction artistique native 1080p et l'alignement mot à mot fiable restent des objectifs futurs.
