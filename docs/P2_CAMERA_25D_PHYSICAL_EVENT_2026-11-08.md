# P2 — caméra 2.5D dirigée par l'événement et le sujet

**Base :** `main` `a7ad1455433b4fb68cccf1fb6b7f7a76bef573e7` (P1 validé). Ce jalon ne modifie ni la narration Kokoro, ni les sous-titres, ni la résolution et l'encodage. Il fait évoluer la cinématographie du Short sur les éclairs sans réécrire les autres moteurs.

## Travaux réalisés dans cette branche

- `automate_ytb/camera25d.py` : mouvements événementiels à accélération/décélération C1, bornés, propres aux cinq scènes (séparation de charges, leader, connexion, retour, tonnerre). Le pic du travelling suit la **phrase réellement synthétisée** lorsqu'une position est connue, sinon un timing explicitement défini dans le moteur.
- Trajectoires des personnages/objets : focalisation sur des **points physiques originaux** déjà présents dans le dessin de l'éclair (`LEADER_CHANNEL`, `UPWARD_STREAMER`, `CONNECTED_CHANNEL`), avec interpolation intra-segment sans interpolation d'images.
- Parallaxe : les plaques des nuages far/middle/near ont des coefficients distincts ; au maximum du plan « leader », la différence de déplacement entre les nuages proches et éloignés est **d'environ 58 pixels dans l'espace source** (objectif géométrique calculé, non mesure visuelle publiée).
- `cinematic_stage.py` : cadrage optionnel sur le sujet sous contraintes explicites, tout en gardant **strictement les mêmes paramètres par défaut** pour les appels historiques. Les limites du recadrage préviennent les marges hors-scène et les étirements.
- À l'entrée et à la sortie du plan, la contribution 2.5D est nulle et sa vitesse tend vers zéro : aucun saut induit par le nouveau travelling, même lors d'une coupe entre deux mécanismes.
- Les nuages et la pluie conservent leur chronologie temporelle indépendante. Le film de sortie conserve **30 compositions d'images indépendantes par seconde**; aucune fausse « 3D native 30 FPS » n'est revendiquée.
- Tests : continuité des poses, données invalides, orientation du mouvement selon la narration, trajectoires physiques, différence de profondeur, intégrité des limites du cadre.

## Vérifications nécessaires avant fusion

1. `python -m unittest discover -s tests -v` et validation du MP4 d'exemple via le workflow `Validate production pipeline`.
2. `Verify original lightning-storm science Shorts` : génère le **vrai MP4 1080×1920 à 30 fps** avec voix Kokoro `af_heart`, musique, SRT, feuilles de contact, SHA256, vérifications de décodage et de scènes figées.
3. Inspection visuelle avant/après de la **même narration** : profondeur perceptible des plans nuageux, absence de poursuite saccadée du canal, mouvement non exagéré sur écran mobile, pas de sujets coupés, lisibilité des captions.
4. Évaluer le coût CPU contre P1 et revenir au cadrage original s'il y a régression de temps, de sujet visible ou de fluidité.

**Limite :** cette contribution améliore une scène 2.5D en profondeur et caméra ; elle n'ajoute pas de simulation 3D, d'IK personnage ni de nouveaux modèles graphiques. La phase P3 traitera ensuite les articulations et interactions.
