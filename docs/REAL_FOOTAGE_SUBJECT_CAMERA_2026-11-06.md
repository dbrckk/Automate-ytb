# Filmage réel + narration naturelle : recadrage intelligent Shorts

## Ce qui change par rapport à la vidéo « diaporama »

Le rendu documentaire NOAA/Kokoro ne recadre plus la vidéo panoramique sur
une coordonnée horizontale fixe. Chaque séquence cherche sa **zone d'activité
visuelle** dans les vraies images décodées, génère un chemin de caméra
progressif puis applique un crop 9:16 *image par image* dans FFmpeg.

- 2 échantillons gris 160×90/s, calcul borné (maximum 72 images/plan).
- Énergie de contraste et de mouvement sur la zone utile, avec exclusion
  relative des bandes de sous-titres et du bord supérieur.
- Choix d'une fenêtre verticale privilégiant l'activité détectée.
- Pénalité contre les changements de cible injustifiés, inertie et limite
  de vitesse pour empêcher les panoramiques brusques.
- Fallback centré si une scène est sombre ou dépourvue de détails.
- Interpolation linéaire avec `crop` FFmpeg sur les *images réelles*
  ; aucun déplacement fictif ou répétition d'un fond statique.
- Les quatre anciens gros titres incrustés, qui imitaient des slides et
  risquaient de gêner l'interface TikTok, ont été supprimés. Les
  sous-titres SRT alignés sur les segments de voix restent disponibles.

La timeline des plans est dictée par les **durées PCM réelles de Kokoro**.
L'audio est mixé sous la voix, sans prise de son du bateau NOAA.
Sortie : H.264 + AAC, 1080×1920, 30 FPS, extrait original sans publication.

## Critères techniques de livraison

L'exécution du workflow `kokoro-short-voice.yml` valide :
1. Origines NOAA identiques aux références SHA256 autorisées.
2. Échantillonnage de vraies images et chemin de caméra borné pour 4 plans.
3. Absence de titres diapositives dans le montage principal.
4. Décodage entier du MP4 et correspondance durée/piste audio Kokoro.
5. Qualité sonore mesurée; SRT livré, pas de publication automatisée.

Un test d'intégration encode localement une scène avec une vraie forme en
mouvement, compare le déplacement du recadrage et décode réellement un
nouvel MP4 vertical.

## Limites à ne pas masquer

Ce n'est pas un algorithme de reconnaissance des animaux. Des particules
brillantes peuvent être sélectionnées à la place des méduses, et les
sources panoramiques 720p ne créent pas de vrais détails verticaux 1080p.
Les séquences choisies et le suivi de mouvement demandent un visionnage
humain intégral sur smartphone.

La narration anglaise Kokoro peut comporter des défauts de prononciation
et ne doit pas être qualifiée de parfaite sans écoute.

L'absence de gros titres incrustés évite un effet PowerPoint, mais les
**sous-titres sociaux dynamiques mot à mot** restent un chantier distinct.
Ils nécessitent un alignement à partir de l'audio plutôt que d'extrapoler
des durées mot par mot.

## Commande de vérification

```bash
python -m unittest tests.test_subject_reframe -v
```

Le workflow produit le MP4 et son rapport JSON de `portraitTracking`;
ce rapport ne constitue pas une validation artistique ni un accord de
publication TikTok/YouTube.
