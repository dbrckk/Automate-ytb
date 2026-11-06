# M0 — Validation réelle de la voix Kokoro avant Blender 3D

## Défaut constaté le 6 novembre 2026

Deux exécutions de **Aurora Alive** (PR #196) ont effectué le rendu CPU
Blender puis installé Kokoro, avant d'être rejetées à l'étape narration.

- Run #42219660878 : cible **35 s**, plus de **21 %** de silence de
  fin de scène, dont une scène ayant **2,28 s** de silence ajouté.
- Run #42220584936 : cible **32 s**, vraie durée PCM **32,68 s**,
  dépassement de **680 ms** face à une tolérance de **600 ms**.

Le problème n'était pas un MP4 illisible : la durée audio définitive était
connue **après** le coût Blender. Le fichier
\`docs/PLAN_PIPELINE_VIDEO_PRO_2026-11-06.md\` désigne cette erreur M0.

## Correction

Pour le workflow \`one-click-preview.yml\` avec \`cinematic_3d=true\`,
\`voice=kokoro\` et \`caption_timing=audio\` :

1. Décomposer/valider le storyboard et ses actions scientifiques.
2. Installer le moteur Kokoro, puis **synthétiser une fois** toutes les
   phrases, avec leur vrai débit et leurs pauses.
3. Produire \`build/voice-preflight/narration.wav\`,
   \`plan.json\` (horaires réellement mesurés),
   \`narration-pacing.json\` et \`manifest.json\`.
4. Rejeter immédiatement les silences de queue excessifs ou une durée
   hors contrat. Le script ne doit **pas** être automatiquement remplacé,
   étiré, compressé ni tronqué.
5. Seulement après la validation PCM, lancer les calculs Blender.
6. Lors de l'assemblage final, \`episode.build_preview\` charge le WAV
   validé, la même timeline et les données de voix **sans exécuter Kokoro
   une deuxième fois**. Un hash SHA256 protège chaque pièce du bundle
   contre des modifications entre les deux étapes.
7. Exécuter ensuite FFmpeg, décoder le MP4, contrôler la qualité,
   les légendes et les artefacts comme auparavant.

En cas de script invalide, le workflow conserve un rapport diagnostique
dans l'artefact \`automate-ytb-free-preview\`. Le rapport n'est pas
une vidéo réussie; aucune annonce de livraison n'est faite sans MP4.

## Compatibilité

Les appels existants \`episode\` restent inchangés si
\`--voice-preflight\` est absent. Les voix eSpeak, le mode silencieux,
les exports non-Blender et l'usage normal de Kokoro continuent de suivre
le chemin existant.

La nouvelle option n'accepte que la voix \`kokoro\`, les sous-titres
\`audio\` et un épisode entier, afin d'éviter de réutiliser une piste
dont les frontières ne correspondent pas aux scènes.

## Vérifications

\`\`\`bash
python -m unittest discover -s tests -p 'test_voice_preflight.py' -v
\`\`\`

Tests : maintien du script original, vrai WAV PCM, empreintes de la
timeline et de l'audio, refus en amont de la 3D si le discours
est trop court, refus des modifications et mauvaises configurations,
preuve que l'assemblage final **ne rappelle pas** le moteur de synthèse.

Le vrai rendu GitHub Actions \`aurora-blender3d-release-candidate.yml\`
reste la preuve requise pour approuver l'intégration globale, accompagnée
de la suite \`validate.yml\` sur le même commit.

## Limites

Une voix peut passer la durée tout en restant artificielle ou mal
prononcer un mot. Les sous-titres PCM sont alignés sur des *groupes de
paroles effectivement synthétisées*, non sur des phonèmes. Une écoute
et un visionnage restent obligatoires avant publication.

Le coût initial de téléchargement du modèle Kokoro reste nécessaire,
mais évite les calculs Blender perdus et la répétition de la synthèse.
