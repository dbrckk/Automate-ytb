# Automate-ytb — Plan d'action directeur pour des vidéos premium

Audit réalisé le **3 novembre 2026** sur `main` à `974dc7cf7e620ff243532e5f808581fea8ec5968`.
Périmètre : génération scientifique en anglais en priorité, puis mutualisation avec les scènes cartoon et les autres formats. Aucun moteur n'est déclaré « AAA » par sa simple présence.

## 1. État réellement vérifié

Rendus GitHub Actions **sur le commit audité** :

| Sujet | Workflow | Durée MP4 | Audio | Silence explicite de fin de scène | QA |
| --- | --- | ---: | --- | ---: | --- |
| Volcan | 41658232278 | 34,000 s | Kokoro EN, musique, -16,1 LUFS | 9,82 %, scène 5 : 1 460 ms | passée |
| Aurores | 41658232499 | 31,333 s | Kokoro EN, musique, -16,2 LUFS | 11,17 %, scène 3 : 1 130 ms | passée |
| Éclairs | 41658232418 | 36,433 s | Kokoro EN, musique, -16,1 LUFS | 10,27 %, scène 2 : 1 070 ms | passée |

Les trois vidéos ont une sortie **1080×1920, 30 FPS, H.264/AAC**, un rapport QA technique réussi, 0 scène animée gelée détectée sur les échantillons, 5 séquences distinctes et des SRT/VTT.

**Réserve capitale : QA ≠ qualité artistique.** Lecture des 6 planches décodées depuis les MP4 : compositions schématiques, objets facettés simples, géométrie/staging répétitifs, zones fixes titre/sous-titres dominantes, effet « infographie animée » plus que « film d'animation ». Les rapports ne vérifient ni photoréalisme, ni qualité de lumière, ni prononciation ni synchronisation exacte mot à mot.

Défauts de conception confirmés :
- `automate_ytb/scene_plan.py` segmente le script à un nombre de scènes égal et attribue des caméras cycliques, sans planification événementielle.
- Dans les trois plans inspectés, `scene.direction.action` vaut `idle` et `emotion` vaut `neutral` pour chacune des **15 scènes**, même pour éruptions, impacts et décharges.
- `automate_ytb/science_stage_director.py` agrandit/cadre la même image 2,5D ; cela ne crée ni une vraie caméra 3D ni de nouvelles surfaces et occlusions.
- `automate_ytb/science_portrait.py` garde le grand titre, chapitre et sous-titrage fixe dans les images finales.
- `automate_ytb/narration.py` propose Kokoro et quelques locuteurs, mais pas de lexique phonétique ni de direction expressive par événement.
- `automate_ytb/episode.py` cadence les sous-titres avec des segments synthétisés, pas par véritable alignement de chaque mot.
- `automate_ytb/soundtrack.py` utilise une ambiance synthétique à 16 kHz avec un motif de 8 secondes ; il manque un véritable sound design événementiel.
- `automate_ytb/review_board.py` compare essentiellement deux images par scène et quelques détails. Un mouvement en boucle peut passer sans posséder de valeur narrative.

## 2. Définition du résultat final

Produire un Short scientifique **original en anglais, 30–45 s, 1080×1920 à 30 FPS**, raconté avec une voix expressive, plans visuellement différenciés, lumières/matériaux et effets cohérents, édition musicale et SFX intégrée, sous-titres accessibles. Une vidéo est « prête » uniquement après décodage, écoute, inspection visuelle et validation du contenu. Publication YouTube toujours conditionnée à une approbation explicite.

Principes non négociables : fiabilité > fonctionnement réel > sécurité > architecture > performances > esthétique. Aucun service payant obligatoire ; pas de contenu stock contrefait ; licences et provenance de tous les assets enregistrées ; Android = récupération directe du MP4 sans poste de travail local.

### Critères quantifiés (cibles, non résultats actuels)

1. **Voix** : silence explicite de fin de scène inférieur à **5 %** de l'épisode ; aucune syllabe coupée ; prononciations difficiles vérifiées ; comparaison d'au moins deux rendus narratifs sur le même texte.
2. **Synchronisation** : sous-titres idéalement mot à mot, écart médian visé < **120 ms** sur un lot audité manuellement, sans affirmer cette précision avant mesure ; effets/mouvements déclenchés aux événements narrés.
3. **Image** : cinq scènes visuellement et sémantiquement distinctes ; au moins trois cadrages **réellement composés** et pas seulement des zooms sur la même image ; silhouettes/volumes/matériaux cohérents ; aucune texture de base exposée comme rendu final.
4. **Animation** : action causale par plan (état initial → transformation → effet → état final) ; pas d'objet qui traverse un autre, de flash orphelin ou de particules qui ignorent la source. 0 frame noire, gel involontaire ou bord transparent.
5. **Audio technique** : cible intégrée -16 LUFS ±1 LU, true peak <= -1 dBTP ; pas de clic, pompage excessif ni musique masquant la parole.
6. **Livraison** : MP4 complet + SRT/VTT + plan horodaté + échantillons décodés + rapport de qualité + manifeste SHA-256 et origine/licences + URL stable GitHub après CI. Temps de calcul et mémoire **mesurés**, pas inventés.

## 3. Séquence d'exécution : une livraison complète à la fois

### Chantier 0 — Baseline et contrats (P0, préalable court)

**Actions :** conserver les trois MP4 et leurs rapports comme références immuables ; créer une grille de 10 critères visuels (matériaux, cadrage, lumière, VFX, profondeur, lisibilité, cohérence, mouvement, SFX, voix) ; instrumenter temps CPU/mémoire par scène ; capturer des frames initiale/médiane/finale, plus de la dernière seconde et des frontières entre scènes.

**Sortie vérifiable :** un rapport comparatif avant/après, reproductible localement et en CI. Le score éditorial reste distinct du statut technique.

### Chantier 1 — Refonte graphique majeure du film volcan (P0, premier chantier de production)

**Architecture :** introduire un backend **hybride** `RenderBackend` (Pillow/FFmpeg actuel = secours fiable ; Blender headless = matière 3D premium sur les plans importants ; Manim facultatif pour les diagrammes précis). Ne pas remplacer tout le pipeline existant.

**Actions :** créer un volcan 3D géométriquement travaillé (cratère, strates, roche érodée, reliefs), matériaux PBR / normal / roughness, éclairage chaud dynamique, ombres, vapeur/fumée volumétrique à coût contrôlé, lave continue et éclaboussures liées au cratère, atmosphère avec profondeur ; développer un vrai mouvement de caméra entre géométries et plans de coupe, avec continuité temporelle. Des caches d'assets et de passes rendent les reprises rapides.

**Stratégie ressources :** mesurer un shot représentatif ; privilégier assets originaux/CC0 et prérendus réutilisables ; CPU local/Actions comme minimum, GPU distant optionnel si explicitement disponible. Si le rendu Blender de l'ensemble n'est pas soutenable, utiliser 3D pour les plans « hero », compositor et animation Pillow pour le reste ; conserver le 1080p final réel. Blender permet l'exécution headless et le rendu CPU, mais ce mode peut être coûteux.

**Critère de fin :** **un nouveau film volcan complet** (pas une scène de démonstration présentée comme version finale), comparé sur les mêmes textes/voix à `science-preview-volcano-eruption-41658232278`. Cinq actions complètes, vraie profondeur/éclairage, aucune répétition évidente de plan et audio intact. N'intégrer à `main` qu'après résultat et contrôle.

### Chantier 2 — Narration visuelle et animation pilotées par événements (P0)

**Actions :** un `NarrativeEventGraph` structuré et validé : `event_id`, concept scientifique, acteur/objet, état avant/après, action, point d'intérêt, cadrage, couleur/intensité, `startMs/endMs`, `audioCue`, sources et risques de justesse. Le réalisateur n'emploie plus `idle/neutral` par défaut pour les scènes à action explicite. Conserver les scènes inconnues en erreur explicite plutôt que montrer des images hors sujet.

**Moteur d'animation :** courbes d'accélération, collisions/cohérence, émission de particules, fluide stylisé déterministe, fumée directionnelle, propagation de lumière, déformation et occlusion ; mouvements de caméra contrôlés par les causes et non par un cycle d'angles.

**Critère de fin :** pour les cinq scènes du volcan, un observateur peut comprendre le phénomène **en coupant le son** ; les événements sont repérables dans un journal de temps et dans le MP4, avec raccords causaux.

### Chantier 3 — Voix anglaise et sound design synchronisé (P1)

**Actions :** conserver Kokoro `af_heart` comme contrôle stable, ajouter lexique de prononciation, passages narratifs avec prosodie (danger, découverte, explication), contrôle des longues pauses, respiration et accents. Comparer par écoute aveugle Kokoro au meilleur candidat open source expressif (Chatterbox uniquement si coût, licence, stabilité et matériel conviennent). Utiliser un véritable **alignement sur l'audio de la voix produite** ; essayer WhisperX sur une voie facultative, ou un aligneur moins coûteux, ne pas assimiler les limites de phrases à des temps mot à mot.

**Son :** événements SFX originaux/licenciés (grondement, pluie, craquement, décharge, éclaboussures), spatialisation discrète, side-chain de la musique à la parole. Auditer les PR existantes **#83** (stéréo 48 kHz) et **#85** (QA audio) après rebase et comparaison de tests, ne pas les fusionner aveuglément.

**Critère de fin :** courte écoute A/B conservée en artefact ; moins de 5 % de silences artificiels ; sous-titres testés mot à mot ; l'épisode reste parfaitement intelligible sur smartphone.

### Chantier 4 — Montage premium et UI mobile (P1)

**Actions :** revoir title-safe, supprimer les grands panneaux persistants, passer à une typographie d'introduction et d'accentuation synchronisée, sous-titres dynamiques contrastés et reflow sans perte, prises de vue plus variées, transitions entre **couches visuelles** avant texte, rythme et accélération compatibles avec les événements (hook dès les premières secondes ; conclusion identifiable). L'audio ne doit pas être rogné par les transitions.

**Critère de fin :** 0 recouvrement de texte ou transition fantôme au début, au milieu et à la fin ; contenu principal lisible en portrait sur Android ; aucune impression de diaporama à 5 panneaux fixes.

### Chantier 5 — QA éditoriale, coût et généralisation (P1 puis P2)

**Actions :** intégrer le contrôle visuel de la PR **#90** après audit de compatibilité ; détection de bord vide, luminosité incohérente, scintillement, doubles textes, motifs répétitifs, SFX mal placés, mot/sous-titre déphasé, plans trop semblables, et comparaison de « vraie action » plutôt que seulement pixels changés. Le QA automatisé ne doit pas prétendre garantir la beauté d'une vidéo. Captures critiques + audio mini-samples accessibles via GitHub Android.

**Généralisation :** seulement lorsque le film volcan est accepté, transformer les auteurs actuels `science_volcano`, `science_aurora`, `science_lightning`, etc., en plugins de séquences avec contrats homogènes et assets mis en cache. Tester ensuite **un nouvel épisode original** de sujet différent ; pas de nouveau sujet si son moteur ne sait dessiner qu'un globe/infographie générique.

**Critère de fin :** deux sujets différents de qualité comparable, intégration complète reproductible, redémarrage/reprise après échec, licence/attribution sûre, coûts gratuits maîtrisés, URL MP4 vérifiée.

## 4. Architecture cible

```
Script original et vérification des faits
  → NarrativeEventGraph (causes / chronologie / intentions)
  → ShotPlan validé + bible visuelle + asset registry/licences
  → Backend graphique par plan (Blender 3D | Pillow 2.5D | Manim)
  → Passes images (couleur, lumière, profondeur, particules, masques)
  → Montage / typographie / caméra / transitions par événements
  ↕ Kokoro + dictionnaire + alignement audio + SFX + musique
  → FFmpeg 1080×1920 / H.264 / AAC / SRT/VTT
  → QA technique + audit comparatif visuel/son + manifest SHA
  → Release GitHub non publiée sur YouTube
```

**Modules existants à conserver** : `science_portrait`, `science_stage_director` (migration graduelle), `narration`, `episode`, `production`, `transitions`, `review_board`, `media_qa`, `qa_bundle`, `science-preview-download.yml`.

**Modules à créer lorsque leur chantier est engagé :** `narrative_graph.py`, `render_backends/`, `asset_registry.py`, `semantic_animation.py`, `word_alignment.py`, `audio_event_mixer.py`, `editorial_visual_qa.py`. Ce sont des cibles de conception, **pas des modules déjà livrés**.

## 5. Ressources gratuites examinées

- **Blender** : programme 3D open source, exécution `-b` et moteur Cycles CPU documentés ; standard principal proposé pour la géométrie/ombrage.
  https://docs.blender.org/manual/en/4.5/advanced/command_line/arguments.html
- **Manim Community** : animation explicative précise des schémas, alternative à l'écriture répétitive de formes Pillow.
  https://docs.manim.community/en/stable/
- **WhisperX** : alignement mot à mot à évaluer en sortie vocale ; modèles et ressources à mesurer.
  https://github.com/m-bain/whisperX
- **Chatterbox** : TTS expressif libre à comparer avec Kokoro, mais **jamais** obligatoire sans benchmarking et examen de la licence du modèle choisi.
  https://github.com/resemble-ai/chatterbox
- **dbrckk/star-list** : références Three.js, Blender MCP, Scenario 3D collection, PINOC et sites d'animation. Blender MCP exécute du Python puissant : **ne pas exposer son port sur Internet**, préférer des scripts Blender confinés/relus en CI. Les datasets ne fournissent pas d'autorisation universelle de republication.
  https://github.com/dbrckk/star-list/blob/main/WEB_RESOURCES.md
  https://github.com/dbrckk/star-list/blob/main/MCP_HERMES_RESOURCES.md

## 6. Règle de progression

**Ne jamais disperser les efforts sur dix petites améliorations.** L'ordre est : chantier 0 → film volcan intégral (chantier 1 + actions causales chantier 2) → voix/son synchronisés (3) → montage/UI (4) → QA et généralisation (5). Les phases de développement restent privées jusqu'à leur critère de sortie ; aucun état de préparation, test vert, screenshot ou promesse ne vaut vidéo jugée professionnelle.

Pendant les travaux : garder `main` publiable, apporter chaque chantier sur une branche dédiée, utiliser les tests lourds **avant** les étapes importantes, mesurer la performance de rendu, et conserver une possibilité de revenir aux exports précédents.
