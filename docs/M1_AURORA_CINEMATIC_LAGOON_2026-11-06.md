# M1 — Premier plan 3D cinématographique : aurores et lac glaciaire

Date : 6 novembre 2026. Dépôt : `dbrckk/Automate-ytb`.

## Problème réellement observé

La planche du rendu Aurora Alive précédemment validé (artefact Actions
`13506316346`, run `42224706598`) présente cinq scénarios Blender :
vent solaire, champ magnétique, collisions, émission et rideaux d'aurore.
La dernière séquence possède des rideaux 3D, mais un sol rocheux trop
simple et aucun élément de premier plan reflétant leurs couleurs. La
source Blender était rendue à **600 × 750**, puis agrandie pour la vidéo
verticale. La conformité H.264 ne garantit pas la qualité d'image.

## Correction : vraies scènes, pas une nouvelle diapositive

- Sur la séquence `curtains` seulement : création d'un lac glaciaire
  **maillé en 68 × 32 sommets** avec berge progressivement resserrée.
- Shader Blender Cycles Physically Based : matériau sombre, faible
  rugosité, couche métallique limitée, bruit de micro-relief et bump.
  Les reflets du rideau passent par le moteur Cycles, pas par une image
  dupliquée en arrière-plan.
- Surface modifiée à chaque pose source avec deux systèmes d'ondes
  continues, de vitesses et longueurs d'onde différentes.
- 11 petits blocs de glace en vrais volumes 3D animés par flottement
  léger, positions stables et illumination existante.
- Caméra dédiée au dernier plan : distance et focale adaptées pour
  révéler le lac et garder le mouvement des rideaux.
- Source améliorée de 600 × 750 / 8 samples à **800 × 1020 / 10 samples**,
  sans augmenter artificiellement la résolution native à 1080.
- Matériau et géométrie limités au plan qui en bénéficie; les quatre
  autres scènes conservent leur direction scientifique.
- Le manifeste Blender expose la vraie métrique
  `lagoonSurfaceVertices` pour chaque scène. Le chargeur la contrôle
  **si elle existe**, refuse les lacs absents/mal placés et continue
  de lire les anciens manifests sans lac.

## Vérifications obligatoires avant fusion

1. `python -m unittest discover -s tests -v` réussit.
2. Le workflow `aurora-blender3d-release-candidate.yml` rend réellement
   ses cinq plans en Cycles, génère la voix Kokoro, les sous-titres,
   le MP4 H.264/AAC 1080 × 1920, les QA et la planche de scène.
3. Le manifeste nouvellement créé prouve au moins 2000 sommets pour
   le lac du plan `curtains` et zéro ailleurs.
4. Le rendu doit rester visuellement animé avec un mouvement non figé
   et pas de scènes noires. Inspecter réellement le plan sur smartphone,
   sans inventer une validation esthétique.
5. Garder le rendu précédent pour comparaison visuelle à scénario
   identique; ne pas déclarer la nouvelle version meilleure uniquement
   sur la base d'une augmentation de pixels ou de polygones.

## Coûts et limites

Le coût CPU Blender/Cycles augmente (plus de pixels, de samples et
réflexions). Aucune API d'image, aucune musique ou scène sous licence
payante ne sont ajoutées. Le rendu source final reste une séquence
**d'images clés 3D interpolées**, et non une simulation 3D recalculée à
30 FPS : ne pas déformer cette distinction dans le produit.

Cette amélioration M1 est le premier **plan premium validable**, non
l'annonce que tous les styles et toutes les scènes sont déjà premium.
Les prochaines étapes devront réutiliser la méthode de comparaison
des MP4 de référence pour les documentaires et vidéos de produits.
