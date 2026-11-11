# Audit P5.27/P5.28 — Rainbow Chase (11 novembre 2026)

## Périmètre réellement vérifié

Vidéo originale: **Why Can't You Reach the End of a Rainbow?**
- Source du MP4 complet et historique : [GitHub Release vérifiée](https://github.com/dbrckk/Automate-ytb/releases/tag/science-preview-rainbow-chase-42918834320)
- SHA256 vérifié : `2856c795b76ef149742a1a66519d68cdf12bcd6162dc50c8ad0239279f6df097`
- Source de l'évaluation visuelle : 6 images **décodées du MP4 réel** à 3,0 / 9,5 / 16,0 / 22,9 / 28,0 / 31,5 s ; 5 images de scènes archivées dans `video/review/storyboard-01.jpg` et `storyboard-02.jpg` de l'artifact de production (Actions run 42918834320).
- Rapports examinés: `narration-pacing.json`, `media-report.json`, `qa-summary.json`, `professional-review.json`, `voice-auditions/audition-report.json`.
- **Limite critique : pas d'écoute humaine indépendante de la voix dans cet audit**. Il ne faut pas transformer les mesures acoustiques ou la tonalité du modèle en jugement subjectif validé.

## Notes initiales / 10 (avis de production à confirmer)

| Axe | Note | Base et limite |
| --- | ---: | --- |
| Graphismes / direction artistique | **6,5** | Décodage et inspection visuelle, palette propre et scènes lisibles mais encore schématiques |
| Qualité des animations et action | **5,5** | 5 paires de scènes en mouvement, mais trois gouttes cadrées identiquement et action narrative finale absente |
| Composition / storytelling | **6** | Les cinq phases optiques sont correctes qualitativement, mais le moteur ne met pas l'observateur en mouvement dans le payoff |
| Voix : naturel humain **provisoire** | **≈7** | Kokoro af_heart, prosodie mesurée non monotone ; **pas d'écoute directe**. Ne pas présenter comme un score d'écoute |
| Audio : qualité technique | **8,5** | `-16,1 LUFS`, `-1,5 dBTP`, AAC stéréo 48 kHz ~243 kb/s, pas d'erreur QA |
| Vidéo : spécifications techniques | **9** | 1080×1920, 30 fps H.264 High, 33,10 s, décodage complet et SHA256 cohérent ; pas une validation artistique |

Faits de montage : 80 mots anglais, 29,44 s de voix réelle, 33,09 s de plan, 3,65 s de silence de fin de plans (**11,03 %**). Silences par scène : 0,72 / 0,87 / **1,23** / 0,35 / 0,48 s. Sous-titres : 10 cues, délimitations approximatives **non alignées mot par mot**. 0 scène gelée détectée sur 5 paires d'images ; taux moyen de variation luminance sur paires : 21,83 %, ce qui n'établit pas la qualité du mouvement. L'audio vocal a une hauteur médiane autour de 197 Hz sur les portions énergétiques, mais cette donnée n'établit pas le naturel du timbre ni la prononciation.

## Défauts observables et causes techniques

1. **L'objet optique reste une fiche pédagogique**. Plans 2, 3 et 4: quasi-même cadrage et grande goutte translucide fixe; seuls les rayons changent. Causes : `automate_ytb/science_rainbow.py` (`_refraction`, `_reflection`, `_emergence`), absence de trajectoire de caméra propre au domaine « rainbow » dans `science_stage_director.py`. Le 2.5D `Scene25D` existe mais n'est pas exploité pleinement pour ces éléments.
2. **Le « pourquoi ne peut-on atteindre le bout » n'est pas montré**. Dans la scène `_arc` de `science_rainbow.py`, la personne et l'arc gardent des coordonnées fixes, tandis que la narration décrit un observateur se déplaçant. Les petites particules et les nuages bougent, pas la cause centrale.
3. **L'action décisive arrive très tard**. L'explication propre au titre vient à la cinquième scène (26,49–33,09 s), après quatre plans surtout consacrés au mécanisme général d'un arc-en-ciel déjà traité dans une vidéo antérieure. Les 2 premières secondes doivent contextualiser la question.
4. **Sous-titres peu synchrones au mot** : le SRT a seulement 10 blocs sur 33 s, avec segmentation par portions de scène et non alignement direct sur la parole. Les bandeaux occupent beaucoup d'espace vertical malgré un grand sujet au centre.
5. **Naturalité vocale non mesurée perceptuellement**. `voice_pacing.py` propose des profils fixes (`natural=0.94`, `gentle=0.88`, `expressive=0.95`, `lively=1.04`) et quelques variations limitées en mode expressive. L'audition du build fournit déjà `af_heart`, `af_bella`, `af_nicole`, `am_michael` sur le même texte. **Ne pas remplacer automatiquement** la voix ni ajouter de modèle payant sans test.
6. **Texture/éclairage et profondeur insuffisamment « cinéma »** : nuages génératifs et éléments optiques corrects pour une explication, mais silhouettes, surfaces et mise en scène sans les détails, changements d'échelle et occultations d'une animation narrative professionnelle.

## Plan ordonné — finir une amélioration avant d'en ouvrir plusieurs

### P0 · P5.27 — Mettre en scène la causalité physique (priorité numéro 1)

**Fichiers visés** : `automate_ytb/science_rainbow.py`, `automate_ytb/science_stage_director.py`, `automate_ytb/science_portrait.py`, `tests/test_science_rainbow.py`, nouveaux tests vidéo.

- Pour la scène finale, faire marcher l'observateur dans l'espace 2.5D **et recalculer l'ensemble des gouttes contribuant à la couleur vue**. Ne pas déplacer simplement l'arc en tant qu'objet physique : ce serait scientifiquement trompeur. Montrer deux points de vue / trajets lumineux de gouttes différentes avec une perspective qui suit la caméra.
- Faire varier les plans au sein des scènes : extérieur avec pluie/sun, gros plan volumétrique de goutte, caméra intérieure sur la réflexion, recul sur plusieurs gouttes + personne. Profondeurs Z distinctes et occultation réelle via `Scene25D` ; éviter le simple zoom d'une image aplatie.
- `cause → action → conséquence` déclenché selon la narration, avec source de temps continue : on doit voir ce qui change quand l'explication change.
- **Critère** : 5 scènes distinctes à 1080×1920 ; au moins 4 scènes ont une action sémantique démontrable au-delà du déplacement des nuages. Dans le dernier plan, la silhouette de l'observateur change réellement de position et les trajets de lumière correspondants se recomposent ; légendes/captions restent dans leur zone. Test visuel avant/après et vérification de continuité sur plusieurs timestamps.
- **Réutilisation obligatoire** : étendre le contrat d'action à au moins un autre moteur (océan ou volcan) sans scénarios codés uniquement pour « Rainbow Chase ».

### P0 · P5.28 — Voix plus humaine, par tests comparatifs et prosodie

**Fichiers visés** : `automate_ytb/voice_pacing.py`, `automate_ytb/episode.py`, `automate_ytb/voice_audition.py`, `tests/test_voice_improvements.py` + tests audio.

- Écouter **à l'aveugle** les quatre voix déjà produites sur le **même texte**, puis sur une phrase interrogative et un passage explicatif. Critères humains : timbre, rythme, intonation, articulation, absence de ruptures robotiques. Mesures acoustiques en complément seulement.
- Garder Kokoro en première option gratuite/CPU. Expérimenter pauses justifiées aux frontières de sens, questionnement, variations modestes de débit et du placement d'emphase. **Ne pas altérer la voix en accélérant les segments pour masquer un débordement**.
- Réduire la répétition et l'attente en fin de plan avec une durée cible adaptée à la durée de la voix ; pour cette vidéo, viser `tailPaddingFraction <= 0.08` et `maxSceneTailPaddingMs <= 800` sans forcer la voix ni les scènes, tant que la lisibilité le permet.
- Ajouter, si techniquement viable sans coût payant, un **alignement automatique mot/phonème→audio** indépendant de l'estimation à partir des fractions du texte. Mesurer le décalage moyen et le p95 sur un jeu annoté manuellement.
- Conserver audio `-16 ± 1 LUFS`, true peak `<= -1 dBTP`, AAC, pas de clipping et voix intelligible quand musique présente.
- **Critère humain** : la meilleure voix doit obtenir **au moins 8/10** en écoute comparative par un évaluateur réel, avec appréciation distincte de la naturalité et de l'intelligibilité. En son absence, marquer « non validé » et ne pas inventer la réussite.

### P1 · P5.29 — Direction artistique 2.5D partagée, pas de filtres cosmétiques

- Améliorer les **sources** : gouttes détaillées (Fresnel stylisé, indices de réfraction symboliques corrects, lumières et caustiques), pluie à densité variable, occlusion, profondeur atmosphérique, reflets et turbulence cohérents ; pas de grandes formes primitives non travaillées.
- Palette / contraste distincts par scène, détails lisibles sur un vrai écran Android, transitions visuellement motivées par l'action. Texte bref, jamais par-dessus le sujet.
- Fournir un moteur partagé de couches et d'actions réutilisable sur aurore, volcan, océan et optique ; conserver le CPU gratuit.
- **Critère** : galerie native complète avant/après, 5 plans visuellement différenciables, contrôles d'alpha/mouvements, absence de jitter/seams, 2 sujets science sans montage spécifique. Objectif indicatif **graphismes >= 8/10** après revue humaine, sans prétendre qu'un test pixel le certifie.

### P1 · P5.30 — Porte de sortie éditoriale de production

- Nouvelle vidéo **inédite** générée depuis le moteur amélioré : anglais Kokoro, 9:16 / 1080×1920 / 30 fps / H.264 + AAC, vraies animations, scènes non répétitives, paroles, SRT/VTT.
- Comparaison source/décodage : contact-sheet avant/après, échantillon de 6 timestamps minimum, mesure **motion du sujet** séparée du mouvement du fond, contrôle de lisibilité et d'absence de jitter à 30 fps.
- Tests unitaires + QA complète + décodage du MP4 + audio RMS/LUFS/pics + ratio de silence + contrôle sécurité des assets, licences et faits scientifiques. **Revue humaine avant toute publication**.
- Publier uniquement une **GitHub Release preview non approuvée**, re-télécharger anonymement en HTTPS, égalité des bytes/SHA256, ajouter dans `docs/video-history.json`. Jamais « File not found », jamais de liens inventés.
- Vérifier que le coût API externe reste **0** et que le temps CPU/mémoire ne régressent pas fortement par rapport au rendu original.

## Principes de validation

- Priorité globale : **fiabilité > MP4 réellement fonctionnel > sécurité > cohérence du moteur > graphismes/voix > effets secondaires**.
- Chaque étape = PR dédiée, tests adaptés et sortie vidéo réellement encodée avant fusion. Aucun « P5.27 livré » tant que les actions ne sont pas **dans le MP4**.
- Les scores cibles sont des **objectifs éditoriaux**, pas des promesses, et la note de voix actuelle est provisoire sans écoute humaine.
- Les scènes ne doivent jamais simuler des phénomènes scientifiques trompeurs juste pour un effet « AAA ».
