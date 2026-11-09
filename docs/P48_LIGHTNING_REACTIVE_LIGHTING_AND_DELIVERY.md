# P4.8 — Éclairage réactif des orages et livraison fiable

État : code et contrôles proposés pour le Short original
« Can Lightning Travel Upward From a Tower? ».

## Problème observé dans le MP4 de référence

Sur le rendu réel de 30 secondes du 9 novembre 2026, le canal principal est
très lumineux, tandis que les bancs de nuages, la pluie et le sol restent
visuellement sombres. Les cinq événements électriques sont distincts, mais
la lumière ne relie pas suffisamment le phénomène à son environnement.

Un autre problème confirmé : la livraison scientifique démarrait aussi
après un push quelconque du workflow, puis tentait de récupérer l'artefact
expiré de l'ancien run `41286036076`. Ce chemin créait un échec sans
rapport avec le vrai MP4 et rappelait le problème « File not found ».

## Modification du moteur

- Deux masques originaux spatialement variables, mis en cache, séparent
  l'illumination des nuages et les réflexions du sol humide.
- La puissance est dérivée de `_flash_intensity`, identique à celle du
  véritable canal électrique. Aucune impulsion supplémentaire n'est créée.
- L'illumination est ajoutée **dans le graphe de profondeur** après le
  terrain et avant le canal, pour que les plans nuages/sol réagissent sans
  recouvrir le cœur blanc de l'éclair.
- Les reflets sont centrés autour de l'ancrage physique de l'antenne,
  et suivent la même dynamique électrique.
- Les séquences sans éclair ne créent aucun éclairage parasite.
- Tests sur les pixels, la transparence, les différentes temporalités,
  les dimensions, les erreurs et le déterminisme.

Il s'agit d'un modèle illustratif en 2.5D, pas d'un solveur physique de
diffusion atmosphérique ni d'une vidéo photographique.

## Livraison sans lien expiré

Le workflow de release scientifique n'est plus déclenché par un simple push
de sa propre configuration. Il démarre uniquement sur la réussite d'un vrai
rendu reconnu ou une invocation manuelle avec run ID. La validation du MP4,
l'accès HTTPS anonyme, la comparaison octet par octet et la mise à jour de
l'historique GitHub restent requis.

Le workflow du Short ascendant se relance à présent quand le moteur
`science_lightning.py`, les effets `science_lightning_fx.py` ou leurs
tests évoluent, pour produire la version effectivement modifiée.

## Critères de réussite

1. Les tests complets sont verts, notamment le nouveau contrôle de lumière.
2. Un vrai MP4 1080x1920, 30 FPS avec Kokoro EN est rendu sur `main`.
3. Les pixels nuages et sol changent pendant l'impact sans créer un flash
   plein écran ou perdre les détails et les textes lisibles.
4. La nouvelle GitHub Release est téléchargée anonymement et vérifiée,
   puis ajoutée à `docs/video-history.json`.
5. La publication TikTok / YouTube reste bloquée avant validation humaine.
