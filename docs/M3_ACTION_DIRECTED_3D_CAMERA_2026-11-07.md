# M3 — Caméras de plans dirigées par l'action (Aurora 3D)

Date : 7 novembre 2026. Base : PR #208 fusionnée, commit a952e10d90577086d254dd34c3dc8523671c9ebc.

## Problème confirmé

Dans le rendu original Blender/Cycles, les cinq étapes scientifiques utilisaient auparavant un mouvement de caméra quasiment identique : légère oscillation latérale et courte avancée, avec un point de visée quasiment figé. La caméra ne suivait pas spécifiquement l'action de chaque séquence (vent solaire, champ magnétique, collisions, émission, rideaux d'aurore).

## Amélioration implémentée

- Cinq trajectoires 3D originales, chacune composée de trois poses auteur : exposition large, démonstration de l'action, conséquence/révélation.
- Interpolation cubique Hermite **continûment différentiable (C1)** des positions et points de visée; départ/arrivée adoucis, sans saut de position lors du beat central.
- Le mouvement modifie la **véritable caméra Blender avant le rendu Cycles**. Il ne s'agit pas d'un panoramique de carte 2D.
- Déplacement du regard dans l'espace : du Soleil vers la Terre, autour de la magnétosphère, vers les collisions moléculaires, en accompagnement des photons, puis progression au-dessus du lac sous les rideaux.
- Trajectoires bornées pour éviter les écarts extrêmes et le mouvement de caméra agressif en 9:16; objectif narratif, pas caméra agitée.
- Le manifeste fournit des métriques entières issues des chemins de caméra auteur : trois points, 31 échantillons, distance cumulée de la caméra et du point de regard (en millièmes d'unités Blender).
- À chaque rendu, le script vérifie que les positions exécutées par l'objet caméra correspondent aux poses auteur à t=0 et t=1. Les manifests anciens restent compatibles; les nouveaux champs incomplets ou incohérents échouent.
- Tests hors Blender : cinq mouvements distincts, continuité C1, distance minimale, limites de cadrage et rejet des entrées invalides.

## Critères de validation et publication

1. Tests généraux de production verts sur le **dernier commit de la PR**.
2. Workflow Aurora réel Blender/Cycles : cinq scènes rendues, voix Kokoro anglaise, sortie MP4 H.264/AAC, sous-titres et contrôles QA réussis.
3. Revue humaine du MP4 sur téléphone : point d'action visible, champ/contrechamp cohérents, pas de fond qui domine le sujet, pas de coupure de mouvement ni d'artefacts d'interpolation. **Aucune appréciation artistique automatique ne vaut ce contrôle.**

## Limites et suite

Les trajectoires sont auteur et illustratives, pas obtenues par détection sémantique du sujet. Les séquences utilisent encore 18 véritables poses Cycles par action avec génération d'intermédiaires; elles ne sont pas rendues en 3D native à 30 images par seconde. Après validation de la caméra : comparer des poses additionnelles et une interpolation optique limitée, sur le MP4 réel, en fonction du temps CPU. Les autres genres (cartoon, documentaire, produit) demandent leurs propres scènes/grammaires de plans, pas un copier-coller de ces cinq caméras.
