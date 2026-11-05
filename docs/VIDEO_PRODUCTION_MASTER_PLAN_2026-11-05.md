# Automate-ytb — plan directeur de production vidéo 2026–2027

État audité le 5 novembre 2026 : main `8c07708b14069272fc3a544ed730a7d9fc777b7a`.
Ce document remplace les annonces génériques de qualité « AAA » par des
contrats vérifiables et une progression priorisée pour **tous les genres**.

## Objectif produit

Un utilisateur sur Android charge ses vidéos/images, fournit un sujet ou un
script (FR/EN), choisit une durée et un format, puis obtient automatiquement
une vidéo H.264 avec montage cohérent, transitions, voix naturelle optionnelle,
musique autorisée, sous-titres, miniatures et rapport de contrôle. Les médias
et leur provenance restent inspectables. Le résultat n'est **jamais publié**
sans vérification humaine explicite.

## État réel et lacunes

| Capacité | État sur main | Limite actuelle |
| --- | --- | --- |
| MP4 horizontal 720p/1080p et Short vertical 1080×1920 | Fonctionne | Rendu CPU coûteux sur longues vidéos |
| Images autorisées, mouvements de caméra guidés par scène | Fonctionne | Une image en mouvement n'est pas une animation 3D |
| Vidéos personnelles MP4/MOV/MKV/WEBM avec droits | Fonctionne | Un import manuel par scène |
| Rendu voix anglaise/française Kokoro en workflows dédiés | Fonctionne avec revue | Prononciations, accents et alignement nécessitent écoute |
| Vidéos scientifiques et séquences Blender | Fonctionne en opt-in | Couverture limitée aux sujets codés, pose 3D non continue |
| Sous-titres et mixage audio | Fonctionne | Alignement phonétique non garanti |
| Contrôles vidéo et audio | Fonctionne | Échantillonnage partiel, validation esthétique humaine |
| Upload web Android, multi-fichiers et stockage | Non livré | Pas de service de transfert établi |
| Sélection de plans, dérushage automatisé | Partiel | Pas encore de route multi-source en une commande |
| Personnages IA parlant face caméra et lipsync phonétique | Non livré | Rendu et droits de voix/visages à traiter |

## Plan priorisé, un chantier terminé à la fois

| Ordre | Chantier | Livrable et test de sortie |
| --- | --- | --- |
| P0 | Robustesse des entrées, reprise et qualité | Détecter vidéos illisibles, doublons, segments impossibles, droits non confirmés, hash corrompu; tests FFmpeg sur vrais MP4 |
| **P1 — première livraison en cours** | **Auto-montage de plusieurs vidéos** | **Une commande** avec script/plan + vidéos; allocation chronologique sans chevauchement, recherche de passages correctement exposés et nets, rapport des choix, création des assets et vrai MP4 9:16 ou 16:9; échec sans livrable partiel |
| P2 | Transfert Android sans logiciel lourd | Upload multi-fichiers authentifié, reprise des transferts, quotas, suppression sécurisée, suivi de tâches, stockage borné; test réel sur navigateur mobile et serveur gratuit viable |
| P3 | Analyse sémantique du dérushage | Transcription locale facultative, segmentation des plans, événements visuels, alignement avec narration; abstention quand faible confiance; test contre vidéos annotées |
| P4 | Montage visible et dynamique | Sélection de plans variée, rythmes liés aux événements/voix/musique, coupes J/L si audio autorisé, effets qui servent le récit; comparaison réelle des exports |
| P5 — intégration en cours | Voix multilingue naturelle | Kokoro EN/FR directement disponible en option du montage multi-sources, durées PCM et sous-titres par phrases; dictionnaire de prononciation, tests d’écoute et alignement plus fin encore à développer |
| P6 | Graphismes et animation premium | Typographies mobiles, titrages natifs, effets de profondeur, motion design original, plus de poses Blender quand utile; grilles de captures et contrôle de lisibilité |
| P7 | Montage audio et son | Musique libre ou originale avec preuve de droits, ducking cohérent, LUFS/true peak, ambiance et sound design, aucun audio parasite |
| P8 | Formats et diffusion | Shorts 9:16, paysage 16:9, carré 1:1, 24/30fps, profils CPU, export prêt YouTube/TikTok/Instagram, SEO et métadonnées sous validation |
| P9 | Production autonome et fiabilité | Jobs idempotents, cache fondé sur hashes, budgets de calcul, contrôle des coûts/quota, observabilité, audit sécurité, sauvegarde et rétention |
| P10 | Vérification éditoriale finale | Visionnage intégral, droits/risques/qualité de narration, source des faits, export de preuves, publication volontaire seulement |

## P1 — contrat du montage multi-sources

1. Modes : `--plan plan.json` **ou** `--script texte.txt --topic ...`.
2. Entrées : 1 à 32 vidéos *locales déjà détenues*, sans URL distante,
   fichiers autorisés par l'utilisateur et ordre conservé.
3. Les scènes sont assignées à des fichiers dans cet ordre; aucune portion
   n'est réutilisée ou bouclée pour remplir artificiellement le montage.
4. Fenêtres candidates évaluées par FFmpeg en faible résolution :
   luminosité, contraste et changement entre images. **Ce ne sont pas des
   scores esthétiques, une compréhension du scénario, ni de l'IA sémantique.**
5. Préflight complet avant encodage : fichiers, codecs, tailles, durée totale,
   faisabilité des découpages, droits explicites.
6. Préparation dans un dossier temporaire : plan, MP4 normalisés, vignettes
   issues des médias, hashes, rapport des choix, rendu final.
7. Le dossier utilisateur est publié uniquement après réussite complète.
   Aucun écrasement d'un montage existant et pas de publication YouTube.
8. Tests d'intégration avec deux/trois MP4 réellement encodés (dont audio
   source), diagnostic en cas de capacité insuffisante, corruption des médias,
   ordre et chevauchement, sortie FFprobe H.264, sous-titres et audit.

## Définition de « terminé »

- Fonction réellement exécutable dans les dépendances installées.
- Résultat vérifié sur un MP4 produit par le code, pas une image de maquette.
- Tests, échec attendu, sécurité, hash, droits et durée conformes.
- Workflows GitHub Actions du dépôt verts sur l'exact commit de PR.
- Différences/limitations documentées sans note de qualité inventée.
- Pas de déploiement ou publication implicite.

## Architecture cible (progressive)

Import autorisé → validation et analyse sources → plan éditorial →
allocation/choix clips → normalisation vidéo et images → voix et audio
optionnels → montage 9:16/16:9 → FFmpeg H.264/AAC + SRT →
rapport QA et revue humaine → export et éventuelle publication autorisée.

Le noyau reste Python/FFmpeg/Pillow avec Blender/Kokoro disponibles par
option; préférer les moteurs gratuits et éviter l'inférence payante.

## Livraison de consolidation P1 → P5 (5 novembre 2026)

- Le montage automatique de rushes originaux est fusionné dans `main`
  via PR #187, commit `52f0f531d1fc12e2b1040382ec15ebb49c98577a`.
  Les 542 tests CI et l'export de démonstration ont réussi sur la PR.
- La branche `feat/multivideo-natural-narration-20261105` relie
  volontairement le moteur multi-sources au narrateur déjà existant :
  voix Kokoro EN/FR en option, voix de brouillon eSpeak et sous-titres
  fondés sur les durées réelles de synthèse PCM.
- Les clips sont alloués **après** la mesure effective des paroles.
  Si la durée dépasse les rushes disponibles, aucune sortie finale
  partielle ne doit être publiée.
- Critères de fusion : contrôle CI sur le commit exact, vrai export
  MP4 avec AAC narré, voix/horodatage de sous-titres vérifiés,
  mode silencieux préservé, pas d'audio caméra, pas de publication.
- Les modèles ne sont ni téléchargés ni exécutés sans activation.
  La narration française et anglaise doit être écoutée avant toute
  affirmation de qualité professionnelle; ces contrôles ne valent
  ni alignement phonétique, ni dérushage sémantique.
