# P5.0 — Caméra cinématique continue pour les Shorts d'orage

## Objectif

Rendre les mouvements de caméra plus fluides et supprimer l'effet de
tremblement artificiel lors du retour de l'éclair. Préserver les cinq
séquences physiques, la profondeur 2.5D, le cadrage mobile, la narration
Kokoro et les sous-titres synchronisés.

## Modification

- Suppression de la vibration de caméra à fréquence élevée
  (`sin(t*27)`) au moment du retour lumineux.
- Ajout d'une dérive optique de très faible amplitude, liée au temps
  continu de chaque plan. Les dérivées de position s'annulent aux coupes.
- Différenciation des mouvements de contact, retour et tonnerre, sans
  déplacer le trajet physique de l'éclair.
- Aucun changement de format, de voix, de texte ou de publication.

## Contrôles

- Test de l'accélération du cadrage à 30 FPS, des mouvements aux limites
  des plans et de l'absence de saccade synthétique.
- Réutilisation des contrôles existants de recadrage sans bandes noires,
  de suivi de l'action, de parallaxe, et de rendu 1080×1920.
- Le workflow `upward-lightning-original-short.yml` écoute déjà les
  modifications de `cinematic_stage.py` et teste `test_camera25d.py`.
  Une fusion sur `main` doit donc déclencher un vrai nouveau rendu
  Kokoro, puis la livraison GitHub Release et l'historique.

**Critère de fusion :** tests de production verts. Après fusion,
vérifier le vrai MP4 H.264/AAC, son téléchargement public et
l'enregistrement de son URL dans `docs/video-history.json`.
