# Automate-ytb — P0 voix, graphismes, interactions (4 novembre 2026)

## Base de référence
Dépôt `dbrckk/Automate-ytb`, main initial `3fd6c4e800899804effb68803c9f1ebf9013b534`.
Le pipeline existant possède déjà : Kokoro FR/EN, narration anglaise native, 1080×1920 H.264/AAC 30 FPS, storyboards différents selon les domaines, sous-titres basés sur les fragments PCM et QA media. Ce **n'est pas** un moteur photoréaliste : ses scènes sciences restent essentiellement des illustrations 2,5D. Les PR ouvertes d'autres auteurs (notamment volcan VFX) sont volontairement laissées intactes.

## Priorités et état

| Priorité | Chantier | Action / livraison | Vérification requise |
| --- | --- | --- | --- |
| P0 | Voix à comparer | `voice_audition.py` synthétise le **même extrait de texte fourni** avec `af_heart`, `af_bella`, `af_nicole`, `am_michael`. Vrais MP3 avec manifeste et SHA256, aucun service facturé | Écouter les quatre MP3, choisir la voix gagnante sur timbre, accent, prononciation et naturel |
| P0 | Expression | Nouveau profil optionnel `expressive`, variation très modérée du débit selon les événements/contrastes/interrogations | Écoute avec et sans profil sur le même texte ; un débit plus variable n'est **pas** une émotion synthétisée |
| P0 | Interactions | `science_causal_vfx.py` relie source → trajet → réaction d'arrivée pour 5 scènes de courants océaniques | Décoder images avant, pendant, après l'événement ; l'arrivée ne doit pas précéder la cause |
| P0 | Synchronisation | Les phases océan utilisent désormais les bornes de **phrases PCM effectivement générées** dans `captionSegments` | Comparer la réaction visuelle avec l'audio, sans prétendre à l'alignement phonétique |
| P0 | Cache | Versionnement science-art / MP4 actualisé | Régénération effective des images et des clips ; aucun rendu obsolète |
| P1 | Vérification | Régressions du moteur, validateur historique et Short scientifique réel | Tests, FFprobe, médias, sous-titres, revue humaine avant fusion |
| P1 | Volume / lumière | Étudier une passe Blender headless sur des plans clés avec retour au backend CPU actuel | Mesurer coût, mémoire et vraie qualité visuelle sur un plan avant extension |
| P1 | Animation | Étendre les trajectoires causales aux arcs-en-ciel, éclairs, aurores et autres univers | Mesurer cohérence, continuité interplans et lisibilité sur mobile |
| P2 | Voix | Rendre facultatif un alignement audio de type Whisper avec couverture et écart rapportés | Aucune affirmation de synchronisation mot à mot sans mesure réelle |
| P2 | Sound design | Ajouter ambiances et événements originaux liés aux changements visuels, avec ducking | Mix LUFS/true peak et écoute sur smartphone |

## Mode d'emploi Android

- Lancer `One-click YouTube preview (free)` dans GitHub Actions, sélectionner `science`, `en`, `kokoro`, `expressive`, `shorts`, `high` et fournir un scénario original dont les 5 scènes sont sémantiquement prises en charge par le moteur.
- Télécharger l'artefact `automate-ytb-free-preview`. Il contient le MP4, WAV, SRT/VTT, rapports QA et, pour une vidéo Kokoro anglaise, `voice-auditions/` avec quatre MP3 et `audition-report.json`.
- Comparer la qualité audible des voix. Aucun score automatique ne peut décider que l'une est « meilleure » pour tout script.
- Le nouveau trajet causal ne s'applique qu'aux cinq beats des courants océaniques ; les univers volcan/aurore/éclair conservent leur direction spécifique. Le rendu final garde les annotations « schéma » et ne prétend ni aux fluides simulés ni à une scène 3D.

## Critères d'acceptation

1. Les tests préexistants et nouveaux passent sans régression ; la prévisualisation H.264/AAC est lisible.
2. Les voix anglaises disponibles sont effectivement synthétisées au moins une fois sur runner Kokoro, et les quatre fichiers MP3 sont consultables sans clé payante ; une audition facultative qui échoue ne masque pas l'état de QA du MP4 principal.
3. Les marqueurs narratifs proviennent des limites de phrases audio réelles ; aucun timestamp mot/phonème inventé.
4. Les nouvelles interactions apparaissent au moment prévu et restent dans la zone de l'illustration.
5. L'artefact final inclut `quality-report.json`, `media-report.json`, `qa-summary.json` et `review/visual-review.json`.
6. **Aucune publication automatique.** Une vraie lecture humaine est requise pour le ton de la voix, les éventuels défauts de script et le rendu artistique.

## Risques et réserves

- Des phrases très courtes synthétisées individuellement peuvent encore paraître artificielles ; le profil expressif réduit certaines monotonies, mais ne résout pas le caractère haché de toutes les prises.
- Les trajectoires sont des **illustrations causales stylisées**, non une simulation océanographique fidèle.
- Le téléchargement initial de Kokoro et l'encodage 1080×1920 utilisent du CPU et les quotas gratuits GitHub Actions ; pas de coût d'API par requête.
- Aucun travail sur cette branche ne doit être annoncé comme fusionné, publié ou validé tant que les contrôles CI et le visionnage ne sont pas faits.
