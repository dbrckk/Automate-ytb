# M3 — Particules chargées véritablement animées dans l'espace 3D

Date : 7 novembre 2026. Statut : changement proposé, soumis aux vérifications GitHub du commit exact et à une revue visuelle humaine.

## Constat

L'animation Blender Aurora utilise cinq séquences causales (vent solaire, champ magnétique, collisions, émission, rideaux). Dans les deux premières, les trajectoires reposaient surtout sur des splines ondulantes. Les courbes seules ne montrent pas assez le déplacement de particules en 3D.

## Changement

- 36 traceurs lumineux indépendants dans solar_wind et 24 dans magnetic_field. Ce sont des maillages 3D émissifs Blender Cycles, ni des sprites 2D ni des textures glissantes.
- Chaque traceur suit les coordonnées XYZ interpolées d'une spline réellement animée, avec quatre déphasages par trajectoire, vitesse continue, pulsation et occultation aux jonctions de boucle.
- Les zones de collision et émission conservent leurs molécules, électrons et photons. Les nouveaux traceurs se limitent aux deux premières scènes.
- Le module Python aurora_tracer_motion permet la vérification du trajet, de l'interpolation 3D et des valeurs invalides, sans API payante.
- Le renderer mesure avant Cycles combien de traceurs ont réellement avancé d'au moins 0,28 unité Blender entre q=0 et q=.43. Le manifeste donne movingTracerParticles et animatedTracerParticles.
- Le chargeur contrôle ces données lorsqu'elles sont déclarées, rejette les valeurs impossibles et reste compatible avec les manifests 3D antérieurs.

## Critères d'acceptation

1. CI générale verte et tests de mouvement 3D et de robustesse.
2. Véritable workflow Blender/Cycles Aurora + narration Kokoro anglaise + MP4 H.264/AAC + contrôle qualité réussi sur le dernier SHA de la PR.
3. Inspection humaine du MP4 et de la planche de contacts pour juger la visibilité, le mouvement, les raccords et la synchronisation.

## Limites

Ces traceurs sont une visualisation pédagogique et non une simulation scientifique du plasma. Les 18 poses Blender par scène sont interpolées jusqu'à 30fps; le risque d'artefacts subsiste. Les mesures de géométrie ne constituent pas un jugement artistique. Aucune publication automatique.
