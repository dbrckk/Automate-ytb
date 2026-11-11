# Automate-ytb V2 — Foley causal audible dans les MP4 finaux

**Date :** 11 novembre 2026. **Statut :** implémentation proposée, résultats CI à confirmer après PR. Le moteur musical ScoreComposer n'est **pas** encore livré ; la voix Kokoro et les musiques existantes restent préservées.

## Défaut réparé

La première tranche MasterTimeline produisait déjà des événements audio structurés et des animations persistantes, mais **les événements sonores n'étaient pas mélangés à l'export H.264/AAC final**. Seul le pilote d'ingénierie possédait réellement ces bruitages.

La nouvelle liaison produit des bruitages *à partir du temps absolu des événements visuels*, puis les mixe dans la vidéo effectivement livrée. Les vidéos historiques non configurées restent rigoureusement sur leur ancien chemin de production.

## Architecture implémentée

1. Plan V1 avec objet optionnel \`masterTimeline\` contenant événements, acteurs et \`soundCues\`, validé par \`master_timeline_adapter.py\`.
2. \`MasterTimeline.audio_events()\` donne l'identité de l'événement visuel source, la famille Foley, \`atFrame\` et \`atSample\` (48 kHz), calculés à partir des scènes **réellement recadencées après la synthèse Kokoro**, et non de timestamps de mots inventés.
3. \`foley_engine.create_causal_foley()\` produit un **WAV original PCM 48 kHz 16-bit stéréo** avec une enveloppe par type de son (count, growth, contact, whoosh, reveal, water, electrical, scale-transition). La synthèse est déterministe et générée par blocs, sans modèle, sample pack, téléchargement ou clé d'API.
4. \`foley-report.json\` enregistre la version du synthétiseur, la famille et l'ID source de chaque son, les marqueurs en frames/samples, les niveaux, le SHA-256 du vrai WAV, la fréquence, la durée, la provenance originale et le statut de revue humaine.
5. \`production.render\` ne génère la piste que si des sons sont **explicitement** déclarés et si le rendu comporte déjà narration ou musique. Les prévisualisations silencieuses restent vidéo seules, pour conserver les contrats des gates QA historiques.
6. \`foley_engine.mix_causal_foley()\` transforme la vidéo **déjà encodée** en MP4 H.264/AAC final, voix/musique/Foley séparées, compression de la musique sous la voix (sidechain), égalisation élémentaire, limitation de crête et normalisation EBU R128. Trois configurations réelles prises en charge :
   - Narration + musique + Foley, cible -16 LUFS ;
   - Narration + Foley, cible -16 LUFS ;
   - Musique + Foley, cible -24 LUFS.
7. \`quality.check()\` valide le choix du mode de mixage, la présence du WAV original, sa provenance, les timestamps événements, le rapport, l'empreinte SHA-256 et la confirmation d'intégration ; ne dispense jamais des vérifications MP4, SRT, droits ou revue humaine habituelles.

## Propriétés de synchronisation

- À 30 fps et 48 kHz : **1 frame = 1 600 échantillons**. L'événement et le bruitage utilisent le *même* \`atSample\`.
- Les débuts Foley sont attachés à un événement visualisable et non placés aléatoirement par seconde ou titre de sujet.
- Un événement hors de la durée PCM réellement mesurée est refusé.
- Les sons peuvent dépasser leur fin de scène sans redémarrer, car la piste audio couvre l'épisode complet.
- Limites de ressources : 64 cues et 180 secondes pour cette première étape ; rejet explicite plutôt qu'export incomplet.
- Des effets ne sont pas ajoutés automatiquement aux anciens sujets : une action doit être explicitement déclarée par un storyboard réel validé.
- L'audio 48 kHz n'est pas une preuve de qualité de composition, et le volume est ajusté au mix ; le timbre, l'émotion et la dramaturgie nécessitent encore écoute humaine.

## Tests et validation

\`tests/test_foley_engine.py\` :
- WAV réel, deux événements visuels horodatés, silence avant l'événement, énergie audible à l'onset, canal gauche/droite distinct, SHA identique sur deux générations ;
- rejet des durées invalides et des cues fictifs ;
- vrai encodage **H.264/AAC** à partir d'une vidéo H.264 silencieuse et de vrais WAV synthétiques, avec mixage voix+musique+Foley, voix+Foley et musique+Foley ;
- FFprobe : dimensions/codec, AAC 48 kHz stéréo et durée ; EBU R128 : loudness et vrai pic ;
- régression sur \`tests/test_soundtrack.py\`, conservation des 924+ tests existants dans la CI complète.

CI spécialisée : \`.github/workflows/causal-foley-final-mix.yml\`. Aucun crédit payant ou GPU nécessaire.

### Commande minimale pour les tests

~~~bash
python -m pip install -e .
python -m unittest discover -s tests -p test_foley_engine.py -v
~~~

## Critères de fin de cette tranche

- [x] Moteur Foley original 48 kHz, stéréo, borné, déclaratif et source-timé.
- [x] Raccordement effectif au code \`production.render\` pour les trois modes audio existants.
- [x] QA fermée : rejet d'un stem absent, non authentifié ou incompatible avec le storyboard.
- [x] Tests réels écrits sur WAV et MP4 avec vérification EBU R128.
- [ ] Tests et CI GitHub complets réussis sur le commit final.
- [ ] Réaliser un **Short inédit avec vraie voix Kokoro** et un \`masterTimeline.soundCues\` approuvé ; inspecter à l'oreille les événements dans l'AAC final.
- [ ] Évaluer et améliorer le timbre des bruitages et leur mix par écoute A/B sur Android et casque.
- [ ] ScoreComposer original continu (lot musical distinct).

**Important :** les moteurs de synthèse Foley et de mixage sont des avancées techniques réelles, **pas** une promesse que le niveau esthétique du fichier utilisateur 3561.mp4 est déjà atteint. Cela demandera aussi MasterTimeline sur des vidéos inédites, le moteur graphique premium et le ScoreComposer.

## Repli

Supprimer la clé \`masterTimeline\` du plan (ou les \`soundCues\`) ramène l'épisode au même chemin de rendu/mixage historique sans Foley. Pas de modification des CLI ni d'actifs tiers. Cette compatibilité doit rester vraie dans toute PR ultérieure.
