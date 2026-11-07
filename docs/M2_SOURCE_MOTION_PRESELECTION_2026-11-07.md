# M2 — Pré-sélection des plans selon le mouvement réel (7 novembre 2026)

## Objectif

Le contrôle final (PR #205) repère les plans figés après leur encodage. Le choix des extraits ne doit plus reposer uniquement sur un très court prélèvement central : le monteur recherche une variation visible dans la durée de chaque plan proposé, avant les rendus coûteux.

## Mise en œuvre

- Un décodage FFmpeg borné échantillonne trois images réelles à environ 20 %, 50 % et 80 % de la fenêtre source. Lorsque les horodatages WebM/variables empêchent de récupérer les trois images, trois recherches temporelles précises sont utilisées en secours (sans duplication d'image).
- Les variations de pixels dans les 75 % supérieurs sont mesurées avec le seuil optique de 1,5 niveau de gris de l'audit du MP4 final.
- Un candidat quasi immobile reçoit une pénalité de 0,35 dans son score de sélection. Un passage réellement plus vivant est donc favorisé à exposition et contraste comparables, sous réserve de la chronologie, de la capacité et de l'absence de réutilisation des rushes.
- Lorsque toutes les fenêtres restent statiques, la vidéo reste produisible mais le rapport signale cette limite : aucune fausse animation n'est inventée.
- Les rapports exportent temporalSourcePixelDeltas, temporalNearStaticSource, temporalSelectionPenalty, temporalMotionAwareSelection et nearStaticSelectedSceneCount.
- Le workflow NASA exige ces informations sur les vraies séquences vidéo montées et conserve la vérification après rendu des sous-titres, de la voix et des fichiers.

## Limites

Ce sont seulement trois mesures temporelles approximatives, pas un suivi optique continu. Une translation de caméra ou un éclairage changeant peut produire des différences de pixels sans animation du sujet. Ni reconnaissance d'objets ni correspondance voix-image ne sont revendiquées.

## Validation

Le test FFmpeg crée un rush statique et un rush mouvant; les tests de sélection vérifient la préférence pour le mouvement et l'interdiction du chevauchement temporel. Avant fusion : CI générale et rendu réel NASA/Kokoro sur le SHA exact. Une écoute et un visionnage restent nécessaires avant publication.
