# M1 — Documentaire court avec vrais timelapses NASA de l’ISS

Objectif : appliquer **le monteur universel** `automate_ytb.auto_edit` à deux sources vidéo réelles et datées, au lieu de créer de nouveaux schémas illustratifs. Démo d'intégration : `.github/workflows/nasa-real-aurora-short.yml`.

## Sources officielles

- 17 août 2022, aurore australe photographiée depuis l'ISS : https://svs.gsfc.nasa.gov/31281/ — `ISS067_20220817_aurora_1080p25.webm` (1920 × 1080).
- 12 novembre 2025, aurores observées depuis l'ISS : https://svs.gsfc.nasa.gov/31375/ — `ISS_20251112_071350-20251112_073549_1080p30.webm` (1920 × 1080).

Il s'agit de **timelapses constitués de photographies spatiales**, et non de séquences enregistrées en temps réel. La NASA recommande l'attribution, l'absence de toute implication de soutien officiel et une revue des éventuels droits tiers. Crédit : Earth Science and Remote Sensing Unit, NASA Johnson Space Center; traitement/édition Marit Jentoft-Nilsen (Global Science and Technology, Inc.). Voir https://www.nasa.gov/nasa-brand-center/images-and-media/.

## Chaîne réellement utilisée

Téléchargement contrôlé depuis les liens officiels fixes → vérification de taille, codecs, résolution, durée et SHA-256 → texte anglais original factuel → musique originale générée localement → narration Kokoro anglaise `af_heart` → montage multi-sources par `auto_edit` → recadrage 9:16 suivant l'activité visuelle de la source → H.264/AAC → décodage complet, QA sonore, sous-titres SRT/VTT, planches et artifact GitHub pour Android.

Pas de modèle payant, pas d'invention de prises de vue, pas de publication sur les plateformes, pas de prétendue segmentation sémantique des sujets. L'algorithme ne suit que des changements visuels et lumineux, et ne comprend pas géographiquement l'image.

## Critère d'acceptation

La PR doit obtenir un **vrai MP4** et non uniquement valider du YAML : deux fichiers NASA authentiques réellement utilisés, narration anglaise Kokoro, pistes H.264/AAC, 1080×1920 à 30 FPS, sous-titres disponibles, voix audible et crédit fourni. Un échec téléchargeable/vidéo/QA bloque la PR. La revue artistique et le contrôle des licences restent distincts du QA technique.

En cas d'insuffisance de durée des sources, diminuer la durée éditoriale ou choisir d'autres plans officiels pertinents avec preuve, et **ne jamais boucler artificiellement des rushes** pour remplir le temps.

## Limites à corriger ensuite

Le montage à partir de deux timelapses NASA améliore la motion réelle, mais il ne constitue pas encore un moteur générique de recherche sémantique. Le recadrage panoramique vers vertical peut agrandir les détails, et les sous-titres auto restent plutôt des phrases que des mots alignés phonétiquement. Le prochain chantier est une vraie sélection multi-sources par événement, vérifiée humainement sur trois domaines (science, produit, quotidien).
