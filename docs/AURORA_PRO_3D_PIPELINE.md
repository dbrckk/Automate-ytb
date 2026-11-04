# Aurora 3D — rendu cinématique original, hors ligne

## Périmètre livré

La branche `feat/pro-aurora-3d-20261104` ajoute une seconde filière 3D
optionnelle à `Automate-ytb`, sans toucher au rendu océan. La 3D aurorale
s'applique seulement aux scripts scientifiques dont le sujet relève des
aurores boréales et dont chaque scène correspond à une des cinq phases
narratives : **vent solaire, champ magnétique, collisions, émission lumineuse,
rideaux auroraux**.

Le Blender officiel tourne sur les runners GitHub et produit des maillages
originaux à éclairage physique : Soleil et globe, champs sous forme de
courbes 3D, atomes et charges, rideaux auroraux réellement maillés et
déformés dans l'espace, horizon de relief et étoiles à différentes distances.
La caméra se déplace entre les poses.

## Production sur Android

1. Sur GitHub, ouvrir **Actions > One-click YouTube preview (free) > Run workflow**.
2. Fournir un sujet et un script de type aurores, puis sélectionner
   `style=science`, `resolution=shorts`, `voice=kokoro`,
   `language=en` (ou `fr`), `voice_style=expressive`,
   `render_profile=high`, et **`cinematic_aurora_3d=true`**.
3. Laisser `cinematic_3d=false` (option océan distincte). Les deux modes
   sont exclusifs. La durée doit respecter la narration mesurée.
4. Télécharger l'artefact `automate-ytb-free-preview`. Il contient MP4,
   SRT/VTT, rapport audio/vidéo, revue animée, preuves Blender et planche-contact.
5. Le workflow dédié **Produce professional aurora 3D science Short**
   utilise un scénario original sur les couleurs et la voix anglaise Bella
   déjà validée sur la vidéo 2,5D de référence.

## Ressources / intégrité

- Génération locale : 5 phases × 10 poses 3D Cycles CPU en 600×768,
  8 samples, puis interpolation à 30 FPS. **30 FPS MP4 ≠ 30 poses
  Cycles calculées indépendamment par seconde.**
- Les images PNG sont enregistrées avec leur SHA-256 dans
  `build/aurora-3d/manifest.json`, et validées en intégralité avant montage.
- Toute corruption, absence de phase ou erreur de ratio fait échouer
  la production. Le mode 2,5D reste par défaut mais ne remplace pas
  silencieusement la 3D demandée.
- Le rendu 3D remplace le plateau scénique dans la bande 1080×1380 ;
  les surimpressions pédagogiques, le titre et les sous-titres restent
  liés aux séquences PCM synthétisées.
- Pas d'assets tiers, de clés API, de droit d'auteur non établi,
  ni de publication automatique YouTube.

## Lancer Blender localement (ordinateur ou runner Linux)

    blender --background --factory-startup -t 2 \
      --python scripts/blender_aurora_stage.py -- \
      --output build/aurora-3d --frames 10 \
      --width 600 --height 768 --samples 8

    python -m automate_ytb.blender_aurora_review \
      --folder build/aurora-3d --out build/aurora-3d/review.jpg

    export AUTOMATE_YTB_AURORA_3D_DIR="$PWD/build/aurora-3d"

Puis lancer la commande normale du pipeline en mode `science/shorts`
sur un scénario d'aurores pris en charge.

## Vérifications avant intégration

- CI générale existante et tests spécifiques verts.
- Vraie exécution Blender et cinq ensembles distincts de poses en mouvement.
- Vidéo complète anglaise 1080×1920, H.264/AAC et sous-titres, sans scène
  statique non désirée ni erreur de cache.
- Inspection des images exportées et écoute audio ; absence de validation
  artistique implicite.

**Limites scientifiques :** la 3D est une représentation stylisée de
phénomènes physiques, pas une simulation de particules ou une photographie.
L'évaluation de l'intonation et de la qualité cinématographique reste humaine.
