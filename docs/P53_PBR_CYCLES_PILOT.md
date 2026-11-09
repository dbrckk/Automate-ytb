# P5.3 / P5.4 — voie vers un rendu graphique premium

## Situation, vérifiée sur la vidéo source

P5.1/P5.2 : narration Kokoro, sous-titres et animations fluides fonctionnent.
Le défaut principal est le matériau : nuages plats, métal sans éclat réaliste,
profondeur atmosphérique presque absente et éclair trop régulier. Améliorer
les couleurs du pipeline 2.5D seul ne suffit plus.

## P5.3 (implémenté comme pilote isolé)

Nouvel outil `scripts/blender_lightning_pilot.py` :

- Scène **réellement en 3D** créée avec les primitives Blender, Cycles CPU,
  caméra perspective, éclairages d'aire et colorimétrie froide/chaude.
- Immeubles industriels en volumes, fenêtres émissives, métal Principled
  avec roughness/metallic/bump procédural, sol humide à microrelief.
- Pylône construit en dizaines de barres et contreventements 3D ; l'éclair
  est une spline 3D à ramifications lumineuses.
- **3 nuages-meshes fusionnés à partir de 42 lobes implicites** irréguliers, disposés dans trois profondeurs
  spatiales, éclairés par les mêmes sources que le terrain.
- Image PNG originale 540 × 690, manifeste SHA256 et métriques d'objets.
  Aucun modèle ni texture importés, aucun service payant.
- Workflow de preuve GitHub `storm-blender-pbr-pilot.yml` installe Blender
  et produit vraiment l'image, pas une simulation en test.
- Porte de qualité : cohérence du manifeste Cycles, détection de corruption,
  comptage des vrais meshes, écart-type des couleurs pour éviter le faux
  rendu monochrome, limites de coût et ressources.

**P5.3 ne change pas le moteur du Short tant que l'image pilote n'est pas
réellement rendue, examinée et comparée à P5.2.** Une image de démonstration
ne doit pas être présentée comme une vidéo terminée.

## P5.4 — après validation du pilote

1. Rendre les cinq séquences physiques de l'orage en vraies compositions
   3D synchronisées sur les mêmes cinq narrations anglaises.
2. Définir des poses de caméra animées en Blender et un champ lumineux
   déclenché par la progression du canal conducteur (non un flash aléatoire).
3. Évaluer l'épaisseur des nuages : meshes éclairés contre volumes Cycles
   plus coûteux, avec contrôle des coûts CPU.
4. Définir cinq familles de plans distinctes et matériaux réutilisables,
   sans répétition de fonds ni titres permanents.
5. Mettre des contrôles automatiques de contraste, animation,
   cohérence physique, lisibilité mobile et décodage MP4 dans GitHub Actions.
6. Basculer progressivement via une option explicite, jamais en détruisant
   les exports 2.5D stables. Test complet H264/AAC 1080 × 1920, Kokoro
   anglais, SRT audio, reproductibilité et livraison GitHub Release.

## Objectifs mesurables avant activation 3D

- Premier PNG Cycles PBR calculé et hashé **réellement** en CI.
- Détails de silhouette et étendue de couleurs mesurables et visiblement
  supérieurs aux simples rectangles et ellipses de P5.1.
- Rendu CPU dans un budget GitHub Actions fixé ; aucun crédit IA payant.
- Transition vers le MP4 autorisée uniquement après vérification de l'artefact
  physique, coût, profondeur et acceptation visuelle.
