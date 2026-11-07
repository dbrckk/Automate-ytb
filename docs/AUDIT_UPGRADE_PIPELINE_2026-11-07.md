# Audit technique et plan d'upgrade — Automate-ytb

**Audit daté du 7 novembre 2026**, base `main` au commit `b12876c361bc6177d6510e047447114a8808fc0e` (PR #207 fusionnée). Ce document distingue le code examiné, les preuves GitHub Actions et les exigences **encore non démontrées**.

## Objectif produit

Créer des vidéos réellement regardables sur TikTok/YouTube Shorts, depuis un Android, en 9:16 H.264/AAC avec narration naturelle FR/EN, sous-titres lisibles, progression visuelle continue et événements correspondant aux phrases. Privilégier les rushes autorisés et les animations originales. Les outils gratuits/open source sont prioritaires. Une revue humaine demeure nécessaire avant toute publication.

## État de référence et preuves vérifiées

| Domaine | Code disponible | Réellement vérifié | Limite actuelle |
| --- | --- | --- | --- |
| Rendu de bout en bout | `production.py`, `episode.py`, `footage.py` | Workflows de validation, réel NASA/Kokoro (#206) et Aurora 3D (#207) réussis sur leurs SHA | Passer les tests ne garantit pas une bonne vidéo |
| Sources réelles et choix des prises | `auto_edit.py`, `source_scheduler.py`, `shot_diversity.py` | Découpage chronologique, diversité optique et activité temporelle à 20/50/80 % | Aucune reconnaissance vérifiée du sujet ou du lien avec la narration |
| Composition 9:16 | `subject_reframe.py`, `footage.py` | Tracking de luminosité/mouvement réel, limitation de vitesse caméra, possibilité de conserver le cadre original | Un mouvement diffus ou un élément lumineux secondaire peut attirer le recadrage et masquer le sujet |
| Animation 3D | `scripts/blender_aurora_stage.py`, `science_blender_aurora.py` | Rendu réel Blender/Cycles de cinq scènes Aurora, géométrie/trajectoires contrôlées, PR #207 fusionnée | 18 poses Cycles par séquence interpolées à 30 i/s ; pas du Blender natif 30 poses/s ; sujet encore schématique |
| Voix/sous-titres | `narration.py`, `voice_preflight.py`, `narration_pacing.py` | Génération Kokoro et master PCM vérifiés avant Blender ; titres incrustés sur rendu NASA | Aucun benchmark d'écoute humain et pas d'alignement phonétique mot-à-mot prouvé |
| QA | `qa_bundle.py`, `media_qa.py`, `professional_review.py`, `shot_diversity.py` | Décodage de vraies images, vérification MP4, rapports et avertissements | Mesures à images espacées et indicateurs optiques non sémantiques |
| Android/livraison | Workflows GitHub Actions, artefacts MP4/ZIP | Artefacts présents dans les runs #42357672254 et #42383500383 | Lien Android direct permanent, upload utilisateur et rétention durable non démontrés |

**Preuves GitHub :** PR #206 (sélection multi-rush avec mouvement) et #207 (60 traceurs 3D); Actions #42357672254 (NASA/Kokoro), #42383500383 (Aurora/Cycles/Kokoro). Leurs validations techniques sont réussies, pas une approbation éditoriale.

## Ordre de travaux — un seul chantier bloquant à la fois

### P0 — Cadrage mobile et confiance visuelle (chantier ouvert immédiatement)

**Problème vérifié :** `track_crop` maximise l'énergie optique d'une fenêtre et l'option `auto` l'applique dès que moins de 50 % des images sont noires ou presque vides. Un ciel, une mer, un texte lumineux ou une agitation répartie peut ainsi déclencher un crop serré injustifié.

**Upgrade :** mesurer la part d'énergie réellement retenue dans la fenêtre suivie, comparée à la zone centrale et à la fraction géométrique attendue d'une scène uniforme; écarter automatiquement le recadrage quand l'activité est trop diffuse pour un suivi raisonnablement fiable. Le mode `follow` demeure disponible comme choix explicite. Publier les fractions mesurées dans le rapport de framing, sans prétendre identifier des personnes/objets.

**Critères :** vidéo synthétique avec sujet lumineux mobile : le cadre le suit; vidéo diffuse : le cadre original est préservé; noir : repli inchangé; filtre FFmpeg généré réellement exportable; anciens tests, MP4 encodé et workflows verts sur le SHA exact. **Impact attendu :** moins de sujets coupés ou recadrés arbitrairement sur Shorts; dépend de la prise de vue et de la revue visuelle.

### P1 — Événements réellement animés

**Avancement technique au 7 novembre :** PR #209 fusionnée (cinq caméras Blender/Cycles dirigées par l'action, rendus et tests vérifiés). Upgrade suivant en branche : éclairage local synchronisé aux impacts électroniques/moléculaires, avec vingt véritables sources Blender animées. Critère de fusion : voir la validation et le vrai MP4 de la PR, puis inspection humaine du scintillement et de la lisibilité. Documentation : `docs/M3_REACTIVE_MOLECULAR_LIGHTING_2026-11-07.md`.

- Passer d'un défilement visuel à des mouvements causaux par shot (entrée, action, interaction, conséquence).
- Benchmark sur 3 types : réel documentaire, 3D scientifique, original narratif.
- Pour la 3D : plan de caméra, éclairage et matériaux cohérents; comparer interpolation existante à davantage de poses **seulement après mesure du coût CPU et de la qualité**.
- Critères : événement visible à différentes fractions du shot dans le MP4 encodé, continuité aux coupes, planche contact et inspection humaine avant/après.

### P2 — Narration et timing

- Synthèse par phrase complète avec PCM mesuré avant rendu lourd; ne pas recréer l'audio après coup.
- Comparaison EN/FR à texte identique des voix Kokoro, mesures de pauses et reprises, écoute sur Android.
- Définir une solution libre d'alignement forcé facultatif avec un repli explicitement marqué « par phrases ».
- Critères : aucun mot perdu dans SRT, cadence cohérente, pas de décalage cumulatif scène/voix.

### P3 — Montage causal et pertinence

- Produire une edit-decision-list de sources approuvées par beat narratif; **ne pas inventer l'alignement sémantique** quand aucun modèle vérifié n'a été exécuté.
- Détecter les répétitions et ruptures par séquence et recadrage, et conserver la chronologie d'origine des rushes.
- Critères : trois genres, absence de sujet perdu, coupes motivées et correspondance action-phrase validée par un humain.

### P4 — Livraison utilisable sur Android

- Manifeste SHA256, taille réelle, codec, audio, durée, droits et provenance, date d'expiration d'artefact.
- Simplifier l'accès à la vidéo MP4 finale depuis la page GitHub Actions, sans prétendre qu'une URL ZIP vaut un lien direct durable.
- Workflow d'upload autorisé et sécurisé seulement lorsque l'interface et l'hébergement sont réellement opérationnels.

### P5 — Publication maîtrisée et amélioration continue

- Validation éditoriale explicite, respect des droits et des règles des plateformes; pas de publication automatique implicite.
- Benchmarks avant/après conservés sur les mêmes contenus, captures début/milieu/fin/coupes, SLO de réussite de rendu et surveillance des régressions.
- Décisions d'évolution appuyées sur le MP4 réellement produit, non sur des scores esthétiques inventés.

## Règles d'intégration

- Ne pas remplacer la version saine de `main` tant que la CI et, si elle touche au montage réel, le workflow de rendu réaliste ne passent pas sur le **SHA de la PR**.
- Les tests unitaires protègent la sûreté, mais la qualité artistique requiert un MP4 et une écoute/inspection humaines.
- Toutes les sources doivent être autorisées; aucun coût d'API payante, modèle fictif ou publication non sollicitée.
