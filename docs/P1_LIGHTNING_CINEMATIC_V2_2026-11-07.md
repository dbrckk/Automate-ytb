# P1 — Cadrage cinématographique et interface mobile minimale pour les éclairs

Date : 7 novembre 2026. Branche de départ : `main` @ `191bfd55f638789632a15e7d29a0be61e20836df`.

## Audit sur une vraie sortie

Vidéo de référence : `The Secret Life of a Lightning Bolt`, génération PR #211 / run #42392578379, réelle sortie MP4 1080 × 1920, 30 FPS, narration Kokoro anglaise, 36,355 s, cinq séquences, revue technique verte.

Inspection **des images réellement décodées** aux instants 0,8 ; 3,6 ; 7,7 ; 10,9 ; 14,5 ; 18,2 ; 22 ; 26 ; 30 ; 33,8 secondes :

- Les cinq séquences racontent bien des événements différents, mais le **titre de l'épisode se répète à l'identique sur tous les plans**, occupant l'en-tête comme une présentation.
- La caméra logicielle réalisait déjà un léger mouvement horizontal et un zoom, mais son **point de visée vertical restait systématiquement fixé au milieu** du studio (source `cinematic_stage.py`), alors que le leader descend vers le pylône et le retour de courant remonte dans l'autre sens.
- Les sous-titres et la zone d'action sont séparés ; cette séparation doit être préservée. Les scènes restent des animations originales 2D illustratives, pas des prises de vues ni une simulation électromagnétique 3D.

Ces observations éditoriales motivent une correction mesurable de composition, pas une prétention de photoréalisme.

## Upgrade implémenté

1. **Trajectoires 2D verticales dirigées par l'événement :**
   - séparation des charges : plan large progressant doucement ;
   - leader : zoom avant et **suivi descendant** vers le point de connexion ;
   - connexion : cadre concentré sur l'éclair et le pylône ;
   - retour de courant : **suivi montant** inverse ;
   - tonnerre : recul pour découvrir la propagation de l'onde de choc.
2. L'interpolation `smoothstep` existante agit sur X **et Y**, ainsi que sur le zoom. La fenêtre reste à l'intérieur des pixels réels du studio source, sans distorsion, téléportation ni freeze.
3. **Titre affiché une seule fois au début du premier plan** ; les autres secondes affichent une étiquette d'événement compacte et le compteur 01/05 à 05/05. L'en-tête reste fixe et ne saccade pas avec la caméra. Les sous-titres ne changent pas.
4. Le rendu Aurora/Volcano utilise toujours ses interfaces et sa caméra propres ; le changement graphique est volontairement limité aux cinq plans lightning.
5. Déclencheur CI : toute modification de la caméra, de l'interface ou des tests lance le vrai workflow original Lightning + Kokoro, en plus des tests généraux.

## Critères d'acceptation

- Tests couvrant les **210 instants successifs de 30 FPS** de chaque scène : cadrage borné, déplacement caméra progressif, suivi vertical descendant/montant supérieur à 100 pixels source.
- Pas de répétition permanente du titre dans le crop d'en-tête ; étiquette des étapes stable en cours d'action.
- Rendu complet H.264/AAC et analyses QA sur le SHA exact de la PR. Inspecter l'ensemble de la vidéo et comparer des captures avant/après aux mêmes instants.
- **Évaluation visuelle humaine obligatoire** avant d'affirmer une qualité professionnelle. QA technique, même réussie, ne prouve pas la pertinence esthétique.

## Suite du plan

Le problème transversal reste la différence entre animation explicative 2D et scène cinématographique riche : travailler ensuite sur la causalité des interactions visuelles, l'intensité lumineuse des coups de foudre et la cohérence image/voix au-delà des seules mesures de pixels. Ne pas ajouter d'API payante ni publier automatiquement.
