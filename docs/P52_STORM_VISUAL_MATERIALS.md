# P5.2 — Remplacement des assets simplifiés de la tempête

## Diagnostic du MP4 P5.1 réellement examiné

Le modèle visuel ne souffre pas principalement d'un manque de transitions :
les nuages étaient des ellipses monochromes floutées, la décharge une
sinusoïde régulière, le pylône quelques lignes et les bâtiments des
rectangles sans matière. La profondeur géométrique existante était peu
lisible à l'écran.

## Améliorations intégrées

- **Matières orageuses originales** : silhouette convective irrégulière,
  quatre octaves de texture procédurale à graine fixe, contraste des faces
  et des creux, liserés de lumière argentée et notes plus chaudes.
- **Profondeur** : trois familles de nuages de dimensions, opacités et teintes
  distinctes, toujours animées à des vitesses différentes par le moteur
  2.5D existant. Les quatre bords des sprites sont fondus pour supprimer
  les raccords rectangulaires.
- **Pylône/ville** : charpente métallique triangulée avec diagonales,
  reflets et haubans, immeubles à façades orientées, ouvertures lumineuses
  et sols humides à reflets mouvants. La pointe du pylône reste
  strictement à la coordonnée du raccord de foudre (700, 695).
- **Décharge** : remplace la ligne sinusoïdale par un canal irrégulier
  multi-échelle reproductible et des ramifications secondaires. Même
  chemin conducteur partagé par descente, connexion et retour lumineux.
- **Fiabilité** : aucun asset payant, aucune image stock ni service distant,
  pas d'aléatoire instable d'une image à l'autre. Les tests contrôlent
  l'opacité des raccords, les variations de matière, les coordonnées
  physiques et le déterminisme.

## Conditions de validation

La suite de tests générale, le contrôle de matériaux et le moteur de
rendu Kokoro sur le workflow GitHub doivent réussir avant une fusion.
Après fusion, les deux épisodes orage doivent être réellement rendus
et les liens MP4 permanents vérifiés par le workflow de livraison.

## Limite de qualité restant à traiter

Ceci est une amélioration du rendu **illustratif procédural** Pillow/2.5D,
pas un résultat 3D photoréaliste. Pour dépasser ce plafond de qualité,
la prochaine étape sera de tester des assets de scène réellement
tridimensionnels (Blender Eevee/Cycles si les quotas CPU le permettent),
avec matériaux PBR, nuages volumétriques, composition dynamique et
tests de coût/temps d'encodage. Aucun niveau « AAA » n'est revendiqué
sur la base de cette seule itération.
