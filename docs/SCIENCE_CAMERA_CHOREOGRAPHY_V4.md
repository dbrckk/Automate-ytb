# Caméra scientifique : phases causales et synchronisation vocale

**Statut :** branche de développement. Ne pas considérer ce changement comme une validation artistique du film.

## Ce que fait réellement le rendu

Les dix plans 2,5D existants des domaines `volcano` et `aurora` conservent les mêmes images, cadrages d'entrée/sortie, durée, résolution et paramètres FFmpeg. Le déplacement continu de la caméra n'utilise plus un seul smoothstep générique :

1. **Mise en place** : déplacement discret pour donner le temps de comprendre l'espace et l'objet.
2. **Action physique** : accélération contrôlée pendant la montée de magma, la décharge, l'impact ou l'émission.
3. **Résolution** : approche progressive du cadrage final, sans saut à un point-clé.

Les courbes par plan sont définies dans `science_stage_director.EVENT_PROGRESS` et évaluées par `camera_progress`. Elles sont **monotones, bornées et C1 continues** aux points-clés ; chaque recadrage reste dans les dimensions de l'image originale. Les petites impulsions de caméra associées à la narration Kokoro, déjà synchronisées aux *phrases audio synthétisées*, sont conservées indépendamment.

**Limite importante :** la vitesse principale de caméra est structurée selon des phases visuelles écrites à la main ; seule l'impulsion locale utilise la position mesurée de la phrase de narration. Il ne s'agit ni de véritable mouvement de caméra en 3D, ni d'un alignement audio mot à mot. Une nouvelle géométrie/occlusion, des matériaux et des voix plus expressives constituent les prochains chantiers majeurs.

## Validations et répétabilité

- Le test `tests/test_science_stage_director.py` vérifie bornes, croissance monotone, absence de saut de progression, déplacements réguliers à 30 FPS, constance des débuts/fins de plans et impulsions audio.
- `automate_ytb/science_motion.SCIENCE_VERSION` est révisé : la validation des illustrations reconnait un changement du moteur et ne réutilise pas une ancienne approbation de manière silencieuse.
- `automate_ytb/production.py` utilise une nouvelle `portraitMotionVersion`, donc les fichiers `.clip-cache` précédents ne sont pas considérés équivalents.
- Le workflow GitHub **Validate production pipeline** doit réussir après ouverture de la PR et encoder réellement la vidéo d'exemple. Le test technique n'évalue pas la beauté, les textures, ni la voix à l'écoute.

La prochaine vidéo volcan complète doit être comparée aux rendus précédents avec 3 images + fragments décodés par plan, la piste audio écoutée en anglais, et un lien MP4 GitHub vérifié avant validation humaine. **Aucune publication automatique sur YouTube.**
