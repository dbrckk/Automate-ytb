# Profondeur de champ cinématique — décors originaux

**Statut :** effet optique 2D stylisé, intégré au rendu PNG approuvé et aux scènes animées FFmpeg. Ce n'est ni un ray tracing ni une mise au point physique sur un personnage 3D.

## Règle de mise au point

La distance de mise au point est déterminée exclusivement par le cadrage validé par le réalisateur automatique. Les décors lointains sont filtrés une seule fois avec Pillow avant le montage, sans flou calculé à chaque image vidéo. La silhouette, les yeux, les membres, les objets tenus, les particules proches et les légendes restent nets.

| Cadrage | Flou décor, rayon source 720p | Flou particules lointaines |
| --- | ---: | ---: |
| wide | 0 px | 0 px |
| medium | 1,2 px | 0,9 px |
| closeup | 3,6 px | 2,7 px |
| macro | 7,2 px | 5,4 px |
| low | 2 px | 1,5 px |
| shoulder | 2,8 px | 2,1 px |

Les quatre biomes originaux et les rigs chouette, renard, lapin et chat utilisent les mêmes réglages, sans téléchargement externe ni API payante.

## Protection qualité

- Plan large strictement inchangé (aucun réencodage de l'image de fond).
- Les calques **background** et **ambient_far** sont les seuls adoucis.
- Les éléments animés, les accessoires et le premier plan restent nets.
- Empreintes des illustrations et version de rendu modifiées : pas de réutilisation de vieilles scènes floues.
- Les métadonnées de cadrage exposent le rayon et la version du système.
- Tests de réduction du détail, transparence et préservation du personnage, encodage MP4 réel et contrôle du codec.

## Limites et prochaines évolutions

Le système est une profondeur de champ **fixe par plan**, pas un rack focus qui suit le regard. Pour les scènes à plusieurs personnages, des masques de profondeur et un système de mise au point explicite dans le storyboard seront nécessaires. Un réglage trop fort peut supprimer des éléments narratifs situés au fond ; garder les illustrations approuvées et les visuels de contrôle accessibles avant publication.

Sur Android : l'effet est automatique dans le workflow de prévisualisation, aucun autre logiciel requis.
