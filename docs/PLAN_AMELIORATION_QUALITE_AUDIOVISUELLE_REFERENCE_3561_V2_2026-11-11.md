# Automate-ytb — plan directeur V2 : atteindre une réalisation audiovisuelle de référence

**Date :** 11 novembre 2026  
**Statut :** cahier des charges d'amélioration / architecture cible — les évolutions décrites ne sont pas présumées implémentées.  
**Dépôt :** dbrckk/Automate-ytb  
**Source de référence privée :** 3561.mp4 fourni par l'utilisateur. Ne jamais committer la vidéo, ses images, son audio ou une reproduction de ses créations dans le dépôt.  
**Objectif :** améliorer durablement la **chaîne de génération de toutes les futures vidéos**, et non seulement reproduire une vidéo ou un style de dessin.  
**Plans antérieurs :** docs/PLAN_QUALITE_AUDIOVISUELLE_REFERENCE_3561_2026-11-11.md et docs/REFERENCE_GRADE_MOTION_SOUND_MASTER_PLAN_2026-11-11.md. Ce document V2 précise la conception, les contrats entre modules, les lots de travail et les critères d'acceptation. En cas de divergence sur l'ordre, ce plan V2 fait autorité.

---

## 0. Politique de développement : règles de qualité non négociables

1. **Fiabilité > fonctionnement réel > sécurité/provenance > architecture > performances > esthétique > fonctions secondaires.** Une fonction qui ne produit pas de MP4 vérifiable n'est pas livrée.
2. Exécuter les travaux **dans le dépôt existant**, sur une branche dédiée, par PRs atomiques. Aucun redémarrage du projet à zéro.
3. Protéger les sorties existantes : titres, voix, sous-titres, effets de causalité, encodage, validation QA, liens GitHub Releases et historique.
4. Gratuit/open source et exécutable sur les runners Linux GitHub Actions sans crédits d'API ; refuser la dépendance obligatoire à un service distant, à un GPU onéreux ou à des secrets.
5. Traiter la vidéo de référence comme un **benchmark de finition**, jamais comme un contenu à reproduire image par image, son par son, texte par texte. Produire nos propres scripts, illustrations, effets et musiques.
6. **Qualité technique ≠ qualité artistique.** Une vidéo encodée et correctement synchronisée peut être visuellement pauvre. Les deux familles de contrôles doivent rester distinctes.
7. Préférer la finalisation d'un composant testé à l'ouverture simultanée de plusieurs modules inachevés.
8. Préserver la reproductibilité : même script, configuration, versions, graine et assets -> mêmes événements et images, modulo tolérances explicites des encodeurs.
9. Rester honnête : pas de note attribuée à la voix, aux bruitages ou à la musique sans écoute humaine ; pas de promesse de qualité « AAA » fondée uniquement sur des pourcentages.
10. Les sorties sont des **prévisualisations non approuvées éditorialement** tant que l'utilisateur n'a pas contrôlé le fond et la forme ; aucune publication YouTube/TikTok automatisée dans ce chantier.

## 1. Benchmark : ce que 3561.mp4 démontre réellement

### 1.1 Données de fichier reproductibles

Les chiffres ci-dessous proviennent de l'analyse locale de la vidéo source et de la dernière sortie réelle Ocean Heat Engine ; la mesure de mouvement est réalisée sur 144 × 256 pixels, à 4 images/s, en comptant la part des pixels dont la luminance change de plus de 8/255 entre deux échantillons consécutifs.

| Propriété | Vidéo de référence 3561.mp4 | Ocean Heat Engine |
|---|---:|---:|
| Durée | 30,800 s | 34,433 s |
| Image | 576 × 1024 | 1080 × 1920 |
| Cadence | 30 fps | 30 fps |
| Conteneur vidéo | H.264 | H.264 |
| Audio | AAC stéréo, 44,1 kHz, ~32 kb/s | AAC stéréo, 48 kHz, ~242 kb/s |
| Mouvement visuel médian, 250 ms | 9,30 % | 3,33 % |
| Mouvement visuel moyen, 250 ms | 11,33 % | 4,47 % |
| Volume intégré mesuré EBU R128 | -14,8 LUFS | -16,1 LUFS |
| Plage de loudness, LRA | 2,5 LU | 2,5 LU |
| Pic vrai mesuré | +0,5 dBTP | -1,5 dBTP |

**Interprétation :** le fichier de référence n'est pas meilleur grâce à une résolution supérieure ; au contraire sa résolution native est inférieure. Le mouvement par pixel ne mesure ni l'intelligence des animations ni le montage. Il est utile pour repérer l'immobilité, **pas** comme un objectif aveugle : une caméra qui tremble artificiellement peut augmenter ce chiffre en dégradant la vidéo. Le pic vrai positif de la référence est **un point de vigilance**, et surtout pas une cible de mastering.

### 1.2 Déconstruction des images : une idée persistante, une progression

Observation de 15 images clés, environ toutes les deux secondes :

| Temps indicatif | Élément narratif | Mécanique visuelle à retenir |
|---|---|---|
| 0–3 s | Question initiale, premiers pliages, épaisseur | Titre stable, jauge persistante, valeur et unité immédiatement compréhensibles |
| 3–8 s | Comparaisons familières (tasse, animal, personnage, maison) | La **même grandeur** avance ; le comparateur change d'échelle avec elle |
| 8–13 s | Tour et relief de plus en plus grands | Caméra, cadrage, profondeur et objets de référence s'adaptent à la progression |
| 13–20 s | Atmosphère, espace, Terre et Lune | Transition d'échelle spectaculaire sans perdre la valeur suivie |
| 20–23 s | Résolution de la question initiale | Cible visuelle claire, compteur qui aboutit, récompense narrative |
| 23–30 s | Extension surprenante vers des distances plus grandes | Seconde révélation, expansion du monde, clôture mémorable |

Le fond sombre, les touches menthe/or, l'espace négatif, le trait lumineux et les éléments de comparaison sont **des choix de composition**, pas des ressources à cloner. Ce qui doit être réutilisé est la grammaire : **question -> grandeur suivie -> transformations physiques -> repères successifs -> changement d'échelle -> révélation**.

Ne pas imiter littéralement la mise en page ou les icônes de la source. Le style de notre moteur doit pouvoir être sobre, illustratif, scientifique, cinématique ou organique selon le sujet.

### 1.3 Analyse sonore : observé / non vérifié

- Observé techniquement : flux AAC stéréo 44,1 kHz ; -14,8 LUFS intégré ; LRA 2,5 LU ; pic vrai +0,5 dBTP. Ce dernier révèle un risque d'overs réels, non une excellence à copier.
- Non démontré par ces mesures seules : qualité du timbre vocal, présence exacte et qualité de bruitages, richesse musicale, construction harmonique, équilibre esthétique, réverbération, émotion, nature des instruments.
- Toute comparaison « meilleure voix / meilleure musique » nécessitera une **écoute A/B réelle** sur le MP4 complet, sur haut-parleur Android et au casque. Les métriques techniques sont des garde-fous, pas une substitution à l'écoute.

### 1.4 Problème majeur à corriger

La référence exploite un **monde narratif continu**. Le moteur actuel découpe principalement le propos en clips/scènes successifs, même si chaque clip comporte de beaux effets. Nous devons remplacer la logique « cinq tableaux avec mouvement décoratif » par « une ou plusieurs actions qui évoluent à travers l'épisode ». **C'est la priorité absolue.**

## 2. Audit d'architecture du code existant : conserver, modifier, ne pas dupliquer

| Composant existant | Réalité constatée | Décision pour V2 |
|---|---|---|
| automate_ytb/scene_plan.py | Segmente le script en phrases/scènes avec startMs/endMs et paramètres de direction | Conserver la compatibilité, ajouter un contrat de StoryGraph et d'objets persistants |
| automate_ytb/action_timeline.py | Gestes locaux par scène, phases issues des phrases synthétisées ou d'estimations | Réutiliser les phases comme adaptateur, ne pas les confondre avec une horloge absolue multi-scènes |
| automate_ytb/science_audio_cues.py | Événement visuel corrélé à une phrase prononcée | Réemployer ses marqueurs, étendre vers une couche d'événements sonore/visuelle commune |
| automate_ytb/scene25d.py | Composition jusqu'à 16 calques RGBA, Z, relief, parallaxe et éclairage | Étendre par des transforms d'objets persistants et coordonnées de monde, sans casser l'API |
| automate_ytb/science_portrait.py | Rendu natif 1080 × 1920 de plusieurs domaines, typographie et captions | Ajouter un adaptateur de MasterTimeline, garder les renderers de domaines en fallback |
| automate_ytb/science_storyboards.py | Cinq actions océaniques sémantiques | Transformer progressivement les primitives en composants réutilisables, pas réécrire le domaine entier |
| automate_ytb/transitions.py | Coupe et transition entre clips successifs | Introduire continuité inter-scènes et raccords motivés, conserver le mode legacy |
| automate_ytb/narration.py | Kokoro 24 kHz, EN/FR, vraie synthèse audio, durée mesurée | Préserver le TTS, ajouter auditions, prosodie éditoriale et éventuelle précision mot par mot |
| automate_ytb/episode.py | Orchestration et contrôle de pacing ; audio de synthèse avant encodage | Brancher les modules V2 ici derrière un choix de moteur, sans modifier arbitrairement la durée parlée |
| automate_ytb/soundtrack.py | Musique synthétique par boucle de 8 s à 16 kHz mono et fondus de scène | Remplacer **progressivement** par score musical continu 48 kHz stéréo + stems ; conserver ancien mode |
| automate_ytb/production.py | Assemblage vidéo/audio, mastering et rapport | Réutiliser, ajouter pistes séparées et événements vérifiés, ajuster le manifeste et les tests |
| automate_ytb/media_qa.py | Loudness, pic vrai, audio, sous-titres, décodage de médias | Étendre aux métriques de synchronisation des SFX et à la détection de ruptures |
| automate_ytb/quality.py et qa_bundle.py | QA technique source et MP4 final, contact sheets, SHA-256 | Ne jamais contourner ; intégrer les nouveaux rapports comme contrôles supplémentaires |
| .github/workflows/one-click-preview.yml | Rendu réel H.264/AAC, Kokoro et QA | Ajouter un profil V2 optionnel, limiter la consommation CPU, maintenir les workflows actuels |
| .github/workflows/science-preview-download.yml | Pré-release avec URL MP4 directe et vérification du téléchargement public | Conserver strictement le gate : main réussi, MP4 décodable, checksum, URL réellement lisible |
| docs/video-history.json | Historique durable par assets GitHub Releases | Ajouter la version de moteur/QA sans casser les entrées historiques |
| tests/ et .github/workflows/validate.yml | Grand ensemble de tests et CI | Ajouter des tests ciblés rapides à chaque PR, préserver l'exécution globale avant fusion sensible |

**Diagnostic honnête :** le dépôt n'est pas vide. Il dispose de beaucoup de fondations utiles. Le manque n'est pas « davantage de scripts graphiques » : c'est **l'architecture de récit, d'état, de synchronisation multimodale et de direction artistique**. Il faudra également réduire le coût du parcours CI quand les tests lourds ne changent pas.

## 3. Contrat de qualité de la future chaîne

### 3.1 Définition d'une vidéo réussie

Une vidéo V2 doit remplir ces exigences *simultanément* :

1. **Compréhension :** la question initiale est visible ou dite immédiatement ; chaque animation explique réellement une idée.
2. **Cause et effet :** au moins un système visuel change parce qu'une donnée/un événement change, pas parce que le temps passe.
3. **Continuité :** identité et état d'au moins un objet central conservés sur plusieurs beats, y compris pendant un raccord.
4. **Progression :** la révélation finale découle visuellement de ce qui a été montré auparavant.
5. **Composition :** sujet, profondeur, couleurs, contrastes et typographie dirigent l'attention.
6. **Animation :** accélérations, décélérations, suivi de caméra et déformations lisibles, non saccadées.
7. **Voix :** naturelle, prononciation exacte, pauses et accentuation adaptées, sans silence mort ni voix tronquée.
8. **Musique :** originale, structurée autour de l'arc dramatique, pas une boucle qui recommence à chaque scène.
9. **Bruitages :** originaux/licenciés et cohérents, alignés sur les événements visibles, sans saturation ni surcharge.
10. **Finalisation :** MP4 compatible mobile, sous-titres fiables, audio équilibré, livraison vérifiée et reproductible.

### 3.2 Barre de validation

- **Automatique bloquant :** fichier décodable, 9:16/1080p/30 fps pour release finale, durée, absence de silence/absence de voix non prévus, absence de frames noires, sous-titres corrects, intégrité des sources, droits, niveaux audio, absence de reset involontaire des objets persistants.
- **Automatique diagnostique (non score esthétique) :** motion salience, quantité de coupes, changements d'échelle, densité de texte, temps de réponse aux événements, indicateurs de tremblement, densité de bruitages.
- **Humain bloquant pour déclaration « qualité référence atteinte » :** au moins **4/5 dans chacun** des axes lisibilité, animation, direction artistique, musique, bruitages, voix, mixage et dramaturgie ; aucune note globale ne peut cacher un 2/5 sur la voix ou les visuels.
- La grille de 4/5 est **une cible future**, et non une note mesurée aujourd'hui. Consigner les désaccords humains plutôt que modifier la note a posteriori.

## 4. Architecture cible : une MasterTimeline unique et des composants substituables

~~~text
Brief de sujet / faits vérifiés / langue / format
  -> StoryDirector
       -> StoryGraph : concepts, unités, causalité, comparaisons, climax
       -> VisualBible : style, palette, objets récurrents, composition
  -> VoiceDirector : Kokoro -> WAV PCM -> timestamps réels de phrases
  -> TimelineCompiler :
       MasterTimeline{frameClock, events, actorIDs, cameras, worldState}
  -> RenderCoordinator
       |-> KineticMotionRenderer (vecteurs, typographie, visualisation)
       |-> Cinematic25DRenderer (profondeur, matières, atmosphère)
       |-> HybridRenderer (combinaison guidée par plan, pas slideshow)
       |-> AudioEventEngine (foley, transitions, ambience)
       |-> ScoreComposer (composition musicale structurelle)
       |-> VoiceProcessor (stem narration)
  -> AudioMixer : voice/music/foley/ambience -> mastering
  -> Encoder FFmpeg : H.264/AAC, SRT/VTT
  -> TechnicalQA + EditorialReview
  -> GitHub Release MP4 + manifest + history
~~~

### 4.1 Horloge unique et précision

- Horloge primaire rationnelle en **frames**, avec 30 fps en sortie finale ; timestamps absolus en **entiers** et unités explicites. Éviter l'accumulation d'erreurs liée à des floats 29.999…
- Une vidéo de N frames a exactement N états échantillonnables : state_at(frameIndex). L'audio est indexé en samples à 48 kHz ; conversion déterministe frame -> sample.
- Séparer : (a) intervalle éditorial (beats), (b) événement sémantique (cause), (c) animation continue (courbe), (d) narration prononcée (phrase PCM), (e) audio synthétisé/déclenché.
- Intégrer des marqueurs de synchronisation **mesurés**, avec provenance ; les intervalles au mot ne sont **pas inventés** lorsqu'on ne dispose que de timestamps par phrase.
- Les modèles d'événements sont immuables après compilation ; animations et audio lisent les mêmes données, et ne modifient pas leur propre horloge.

### 4.2 Exemple de contrat déclaratif (proposition V2, non implémentée)

~~~json
{
  "schemaVersion": 2,
  "episode": {
    "id": "original-growth-demo-001",
    "language": "en",
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "seed": 12507
  },
  "objects": [
    {"id": "value", "type": "measured-quantity", "unit": "m", "source": "fact-reviewed"},
    {"id": "main-visual", "type": "rigged-object", "persistent": true, "z": 20},
    {"id": "comparison-a", "type": "comparison-prop", "persistent": false, "z": 30},
    {"id": "camera", "type": "camera25d", "persistent": true}
  ],
  "events": [
    {
      "id": "growth-001",
      "type": "quantity.change",
      "atFrame": 90,
      "durationFrames": 24,
      "actor": "value",
      "from": {"value": 1, "unit": "m"},
      "to": {"value": 8, "unit": "m"},
      "easing": "cubic-in-out",
      "causes": ["main-visual.height", "camera.follow", "sfx.growth"]
    },
    {
      "id": "compare-001",
      "type": "comparison.reveal",
      "atFrame": 114,
      "durationFrames": 21,
      "actor": "comparison-a",
      "dependsOn": ["growth-001"],
      "sfx": {"family": "reveal", "gainDb": -15, "preRollMs": 25}
    }
  ]
}
~~~

Ce contrat illustre **la même information pilotant plusieurs canaux**. La version finale doit imposer schéma, types, plages admissibles, limite d'événements, rejets de références circulaires, rejet des valeurs non finies, IDs sûrs, unités cohérentes et contrôle de complexité CPU avant rendu. Aucune expression Python arbitraire/eval provenant d'un brief ou de données externes.

### 4.3 API Python attendue

- **StoryGraph** : concepts, relations de cause, preuves, unités et provenance ; aucune animation liée à une chaîne de caractères du titre.
- **ObjectRegistry** : ID stable, propriétés d'animation et cycle de vie ; vérification des collisions de noms et de Z.
- **QuantityTrack** : valeurs exactes, unités, conversions, affichage, animation continue, transitions de changement d'ordre de grandeur.
- **CameraTrack** : pose monde, point suivi, zoom, framing safe area, profondeur et easing.
- **MasterTimeline** : compilation triée des événements, dépendances sans cycles et échantillonnage stateless state_at(frame).
- **VisualRenderer** : adapter.render(state, style), sans effet de bord ; même entrée -> même frame.
- **AudioCuePlanner** : conversion de événements sémantiques vers SFX/music marks, sans générer de sons arbitraires.
- **ScoreComposer** et **FoleyEngine** : sorties WAV/stems + manifest des marqueurs.
- **FinalMix** : mixage des stems, traitement de voix et loudness mesuré après AAC.
- **QaEvidence** : journal versionné, règles appliquées, artefacts et digest.

**Emplacement proposé (à adapter à la meilleure architecture constatée lors de l'implémentation) :**

~~~text
automate_ytb/
  story_graph.py
  master_timeline.py
  timeline_schema.py
  quantity_track.py
  cinematic_direction.py
  renderer_router.py
  kinetic25d.py
  audio_event_engine.py
  score_composer.py
  mixdown.py
  audiovisual_qa.py
scripts/
  benchmark_reference_offline.py
  compare_av_render.py
tests/
  test_master_timeline.py
  test_quantity_track.py
  test_audio_event_engine.py
  test_score_composer.py
  test_audiovisual_qa.py
~~~

Ne pas créer tous ces fichiers d'un coup. Ils constituent **une carte de responsabilités**, et peuvent être regroupés si cela réduit réellement la complexité. Les modules existants priment sur toute duplication.

## 5. Réalisation narrative : de la phrase à l'événement filmable

### 5.1 Séquencement

Une structure conseillée pour un Short de 25–45 secondes (les proportions s'adaptent au texte et non l'inverse) :

- **Hook / anomalie** : poser le problème au premier mouvement ou à la première image.
- **Modèle de départ** : présenter une grandeur, un mécanisme, un protagoniste ou un état initial.
- **Progression dirigée** : montrer 3–6 transformations en conservant une référence visuelle.
- **Changement d'échelle / complication** : le monde se recadre autour de la nouvelle grandeur.
- **Climax / réponse** : révéler le résultat lorsque l'état suivi y parvient.
- **Épilogue bref** : démontrer une conséquence inattendue ou conclure avec une image claire.

Les phases ne sont pas obligatoirement six scènes : plusieurs événements peuvent se succéder dans **une scène continue**. Les coupes doivent avoir une motivation (cause, changement de point de vue, rapport d'échelle), pas simplement correspondre à une fin de phrase.

### 5.2 StoryGraph et vérification factuelle

Pour chaque phrase :
- Détecter **ce qui change** (valeur, objet, relation, danger, point de vue).
- Définir **ce qu'on doit voir** avant, pendant et après (états A -> B).
- Définir les éléments persistants ; préférer réutiliser un objet plutôt qu'en recréer un semblable.
- Exprimer les relations physiques avec les unités et les hypothèses. L'exponentiel est calculé exactement, puis affiché avec arrondis contrôlés ; aucune valeur « spectaculaire » inventée.
- Conserver les sources et le statut de validation des comparateurs (masse, distance, hauteur, température).
- Si le sujet ne se prête pas à une action honnête, choisir un schéma explicatif approprié plutôt qu'inventer une simulation trompeuse.
- Demander une revue scientifique ou marquer la séquence comme illustrative lorsque le phénomène n'est pas fidèlement simulé.

### 5.3 Stratégie par type de sujet

| Sujet | Grandeur/objet persistant | Animation motivée | Risque à contrôler |
|---|---|---|---|
| Mathématiques / exponentiel | Quantité et compteur | Croissance, changement d'échelle, comparaison | Débordements, données fausses, faux effet de zoom |
| Océan / climat | Parcelle d'eau et flux de chaleur | Advection, rotation, plongée, transfert | Ne pas faire passer schéma pour simulation réelle |
| Volcan / géologie | Réservoir, pression, flux | Compression, ascension, éruption, dépôt | Géométrie/chronologie géophysique trompeuses |
| Électricité / orage | Différence de potentiel et leader | Propagation, connexion, retour lumineux | Temps physique mal interprété |
| Histoire | Carte, lieu ou objet historique | Trajectoire, frise, évolution documentée | Anachronismes et droits des images |
| Économie | Valeur et unités monétaires | Barres liées à données, comparaisons | Échelles biaisées, inflation ou conversions fausses |
| Produits / objets | Pièce et assemblage | Décomposition, rotation, montage, usage | Fausse représentation du produit |
| Nature / biologie | Organisme ou processus | Croissance organique, interaction, cycle | Exagération morphologique et scientifique |

## 6. Moteur d'animation : continuité, profondeur et rythme

### 6.1 Objets persistants et état temporel

- Un objet reçoit un ID stable et un espace de coordonnées monde, quel que soit le chapitre.
- state_at(t) calcule position, taille, rotation, opacité, déformation, éclairage et propriétés scientifiques, sans conserver un état mutable uniquement dans la mémoire d'un renderer.
- Un objet n'est jamais réinitialisé à 0 lors d'une coupe ; le nouveau plan réutilise son dernier état, ou indique explicitement un changement de contexte.
- Gestion du cycle de vie : introduction / visible / sortie / masqué / réutilisé. L'absence d'objet est un état explicite.
- Les points d'ancrage de comparateurs doivent suivre la grandeur, sans décalage lors de la caméra ou de l'échelle.
- Pour toute interpolation, documenter les unités, bornes, dérivées et comportements aux extrémités.

### 6.2 Cinématique

- Courbes C1/C2 lorsque appropriées, sans accélérations infinies, gigue aléatoire par frame ni overshoot intempestif.
- **Anticipation** (quelques frames), **action**, **suivi secondaire**, **settle** ; ces mouvements ne doivent pas masquer la donnée.
- Caméra : déplacement dolly, cadrage suivi, zoom d'échelle graduelle, profondeur et vitesse adaptés à la lisibilité du texte.
- Parallaxe : couches distinctes avec Z réel/illustratif, occlusion testée et ombres de contact ; ne pas tricher avec un seul fond étiré.
- Transitions d'échelle : il faut conserver un repère (ligne d'horizon, axe, objet principal, compteur ou unité) et annoncer le changement d'ordre de grandeur.
- Simuler un **motion blur léger optionnel**, basé sur déplacement réel, sans détérioration des chiffres/labels.
- Éviter tremblement subpixel, aliasing de traits fins, particules sans causalité et effets continus décoratifs trop bruyants.

### 6.3 Mathématiques, unités et échelle

- Calculs exacts avec int/Decimal/Fraction selon cas, puis conversion vers espace écran **après** calcul des quantités réelles ; contrôle des unités.
- Repères physiques stockés comme données versionnées : label, quantité, unité, source, incertitude, statut vérification.
- Zoom logarithmique quand nécessaire, mais indiquer les discontinuités d'échelle pour éviter les comparaisons trompeuses.
- Les nombres animés doivent suivre la quantité réellement dessinée ; pas d'incrémentation indépendante du visuel.
- Définir stratégie pour les très grands nombres (notation scientifique), zéros, valeurs négatives, infinis, erreurs de calcul et localisations EN/FR.
- Synchroniser compteur, progression visuelle, caméra, label et bruitage sur une **même transition**.

### 6.4 Continuité aux raccords

Pour chaque frontière entre deux plans :
- Vérifier state_before et state_after à ±1 frame ; différencier coupe volontaire et saut d'état non volontaire.
- Tracer ID, objet/valeur, coordonnées monde et cadrage.
- Éviter le reset de la boucle musicale et des enveloppes de bruitage à chaque fin de plan.
- Préférer transition de caméra, raccord de mouvement ou occlusion réelle quand cela améliore la compréhension.
- Garder le mode transitions.py historique comme solution de repli, mais ne pas le confondre avec un moteur de continuité.

## 7. Direction artistique : deux profils professionnels, pas un thème unique

### 7.1 Profil A — kinetic editorial

- Quantité suivie, compteur, courbe, repère, trace lumineuse **liés à la donnée**.
- Palette restreinte cohérente par sujet, fond de profondeur qui ne concurrence pas le contenu.
- Traits Bézier, formes organiques si pertinentes, ombres douces, glow parcimonieux et petites particules causales.
- Typographie hiérarchique : une question, un chiffre dominant, une unité, un comparateur ; éviter les phrases trop nombreuses dans l'image.
- Échelle, détail et contexte évoluent avec la caméra ; le spectateur doit comprendre ce qu'il regarde sans arrêt sur image.
- Les choix de la référence servent à comprendre la **hiérarchie**, non à imposer une copie du vert menthe/or ou du style de son créateur.

### 7.2 Profil B — cinematic 2.5D

- Décor hiérarchique : arrière-plan, milieu, sujet, avant-plan, lumière volumique, atmosphère, ombres et relief.
- Matériaux cohérents (eau, pierre, tissu, peau, nuage, métal) avec normalité visuelle, microrelief et réponse à l'éclairage.
- Animations organiques : déformations riggées, articulation, contact, turbulence contrôlée, poussière et propagation du flux.
- Profondeur construite par occlusion et différentiel de mouvement, pas par une seule transformation affine du canvas.
- Préserver une **direction de lumière principale** et une continuité de couleurs lors des coupes.
- Éviter d'ajouter systématiquement des objets complexes : le détail doit renforcer le sujet et le contraste focal.

### 7.3 Profil C — hybride, uniquement quand justifié

Un graphique peut apparaître **dans** un monde 2.5D (overlay en coordonnées monde, repères rattachés à un objet) ; les deux ne doivent pas être deux compositions indépendantes collées ensemble.

### 7.4 Bibliothèque de composants à industrialiser

1. Progression sur une échelle physique avec mise à jour de valeur/unité.
2. Repères de comparaison dont l'entrée et la sortie sont animées.
3. Compteur typographique à échelles diverses (avec séparateurs de milliers).
4. Caméra centrée sur un acteur avec suivi et changement d'ordre de grandeur.
5. Objet déformable / extensible piloté par grandeur.
6. Flèches/flux advectés suivant un champ de vitesse.
7. Traces et particules avec émission, trajectoire et durée de vie.
8. Révélation par lueur/occlusion/échelle, reliée à un événement.
9. Système d'ombres et lumière motivée par l'action.
10. Zones éditoriales et sous-titres qui s'adaptent sans masquer l'action.

### 7.5 Choix des technologies et critères de migration

**Décision initiale :** conserver Python + Pillow, les composants 2.5D existants et FFmpeg. Ajouter du calcul vectoriel antialiasé et des caches ciblés lorsque nécessaire. Une migration de moteur est **un benchmark, pas une obligation**.

Candidats éventuels :
- Motion Canvas : animation vectorielle TypeScript orientée explications synchronisées à la voix. Tester exporter headless, installation CI, consommation RAM, reproductibilité et intégration des frames dans FFmpeg.
- Manim Community : moteur libre MIT utile aux mathématiques ; comparer uniquement sur le même storyboard et le même budget CPU, sans recopier les assets de ses projets d'exemple.
- Blender/Godot : réserver aux scènes pour lesquelles géométrie, lumière ou rig ne sont pas suffisamment réalistes avec Pillow ; éviter le coût 3D sur un graphe simple.

**Critères de décision de l'essai** : qualité visuelle à storyboard identique, capacité à l'animer par données externes, temps CPU réel, mémoire max, nombre de dépendances, licence, stabilité dans Actions, coût de maintenance et compatibilité Android pour la récupération. Mesurer et documenter ; ne pas ajouter trois moteurs concurrents simultanément.

## 8. Sound design : un moteur Foley déclenché par les causes visibles

### 8.1 Taxonomie d'événements et signatures acoustiques

| Famille | Déclencheur visuel réel | Construction originale suggérée | Règle |
|---|---|---|---|
| tick/count | Changement discret de compteur | Impulsion douce, partiels courts, pitch contrôlé | Pas de clic aigu répétitif fatigant |
| growth/rise | Allongement, accumulation, expansion | Sweep harmonique et bruit filtré | Courbe d'énergie suit la grandeur |
| fold/contact | Contact physique, compression, froissement | Bruit granulaire filtré + petit impact | Son plausible, non identité sonore copiée |
| whoosh/camera | Déplacement rapide de la caméra ou du sujet | Bruit large bande filtré selon la vitesse | Uniquement si mouvement significatif |
| reveal | Apparition de résultat ou de comparateur | Attaque contrôlée + texture tonale | Réserver un contraste au climax |
| water/air | Écoulement, jet ou turbulence | Bruit coloré et enveloppes turbulentes | Événement lié au flux |
| electrical | Connexion/flash d'un leader | Transitoire bref et traîne spatiale | Sécurité des pics, pas de surprise excessive |
| scale-transition | Passage d'un ordre de grandeur | Modulation/filtrage du signal de transition | Synchroniser le changement d'échelle |
| ambience | Environnement continu | Couche basse discrète, non loop de 8 s | Ne pas masquer la parole |

### 8.2 Contrat audio événementiel

Chaque événement possède :
- ID de l'événement source, scène/objet associé, temps absolu en sample index ou microsecondes, durée, type, intensité, seed, pitch, enveloppe ADSR, pan, gain, éventuel pre-roll, priorité et licence.
- Paramètres dérivés de l'animation : vitesse angulaire, profondeur, variation de grandeur, impact, visibilité et état d'occlusion.
- Garde-fous : polyphonie max, espacement min pour répétitions, seuil de gain, budget CPU, évitement de pics collectifs, absence de coupure par limite de plan.
- Un manifeste de provenance et d'événements pour inspecter pourquoi un son a été produit.

### 8.3 Génération et bibliothèques sonores

**Version de démarrage recommandée :** NumPy/SciPy si nécessaire + fonctions DSP en Python ou FFmpeg (oscillateurs, bruit, filtres, envelopes), sans achat. Rendre les stems PCM float32 48 kHz stéréo, les encoder seulement au mix final.

Les samples CC0/CC-BY éventuels nécessitent : source explicite, URL ou hash, preuve de licence, auteur et attribution dans un fichier de crédits. Ne jamais récupérer automatiquement la piste ou les effets de la vidéo de référence.

### 8.4 Synchronisation et mix

- Les SFX sont alignés à la date **de l'événement visuel effectif**, et non au milieu arbitraire du segment narratif.
- Cible instrumentale : écart onset audio / début visible **≤ 80 ms**, ou pré-roll documenté si la mise en scène le motive.
- Le bruitage ne doit pas devancer une révélation d'une manière qui l'explique prématurément.
- Priorité des stems : voix > effet causant/confirmant l'action > musique > ambiance ; exceptions éditoriales motivées.
- Diminuer les sons de compteur répétés, conserver la variation de timbre et éviter une impression de jeu d'arcade générique.
- Garder une version A/B **sans SFX** afin de confirmer que chaque bruitage apporte quelque chose.

## 9. Musique : ScoreComposer véritablement continu et narratif

### 9.1 Pourquoi remplacer le mode actuel

Aujourd'hui soundtrack.py crée des motifs simples sur des cycles de 8 s à 16 kHz mono et applique des fondus de scène. Le résultat est techniquement utilisable comme **musique d'attente**, mais manque de continuité dramatique, spatialisation, relief fréquentiel et orchestration.

### 9.2 Plan musical

- Composer à partir d'un **arc global** : curiosité initiale -> pulsation/discovery -> montée de tension -> rupture ou suspension -> reveal -> résolution.
- Pas de mélodie existante ni de « musique dans le style exact de [artiste] » ; thèmes originaux, motifs générés à partir de règles musicales.
- Une grille de temps musical peut guider les coupes, mais la phrase parlée et la compréhension restent prioritaires.
- Choisir tempo, pulsation, gamme/harmonie et texture une seule fois par épisode ; adapter la densité à chaque acte.
- Introduire des variations mélodiques/métriques contrôlées, des couches rythmiques et des transitions harmoniques, plutôt qu'une répétition identique du même accord.
- Structure des stems : pad / bass / pulse / arpeggio / percussion légère / transition / reveal hit. Version simple possible pour les sujets sobres.
- Garder une enveloppe d'intensité non monotone : la montée doit comporter une respiration avant la révélation.
- Supporter modes « discret / documentaire / mystérieux / énergique », indépendants de la langue de narration.
- Établir un contrat de durée : musique commence et finit avec le récit, pas avec le dernier beat de huit secondes.

### 9.3 Mixage et mastering

- PCM mix à **48 kHz stéréo**, voix Kokoro 24 kHz correctement rééchantillonnée ; garder l'original PCM pour alignement.
- Ducking sous la voix avec enveloppes attack/release, pas de pompage audible ; éviter l'effet de « musique qui s'éteint puis repart » à chaque phrase.
- EQ correctif minimal, contrôle des sifflantes seulement en présence d'un problème confirmé, compression modérée et limiteur true-peak final.
- **Cible finale proposée** : -16 LUFS ±1 (programme narré), true peak ≤ -1,5 dBTP, aucune perte d'intelligibilité ; contrôler **après** encodage AAC, et non seulement sur les stems.
- La référence présente +0,5 dBTP : **ne pas copier ce défaut**. Conserver la marge de sécurité existante.
- Audio mobile : audition petit haut-parleur (voix prioritaire), casque (stéréo et bruitages), à faible volume (consonnes intelligibles).
- Rendre également stems et manifest pour l'analyse, sans imposer l'écoute d'un ZIP à l'utilisateur final.

## 10. Voix, alignement et sous-titres

### 10.1 Conserver le fonctionnement réel déjà acquis

- Kokoro EN/FR et audios PCM véritables : oui.
- Frontières mesurées des phrases synthétisées : oui.
- Alignement **des mots**/phonèmes vérifié : **non** dans l'implémentation actuelle. Ne pas le présenter comme existant.
- Système de validation du pacing : oui ; il a déjà évité un export 33 s lorsque la narration exigeait plus de durée. Garder cette sécurité.

### 10.2 Direction vocale

1. Préparer le script pour être lu à voix haute : phrases courtes, verbes concrets, pauses logiques, chiffres exprimés oralement de façon naturelle.
2. Choisir la voix par audition A/B sur le **même script** ; Kokoro af_heart/bella/nicole/sarah/michael selon langue autorisée.
3. Conserver l'expressivité à petite dose : pas de pitch/tempo exagérés ni de ralentissement artificiel d'un enregistrement.
4. Gérer noms propres, unités et nombres difficiles avec prononciation contrôlée et lexique de substitution affichage ≠ lecture.
5. Prévoir une durée de respiration avant un impact/révélation ; ajuster **le script et le storyboard**, pas couper la voix.
6. Séparer voix source, voix traitée et mix final pour audition et régression.

### 10.3 Alignement plus fin : lot optionnel et réaliste

- D'abord utiliser les marqueurs **PCM par phrase** pour synchroniser beats, SFX et principaux mouvements.
- Ensuite, si l'on démontre un besoin de déclencher les chiffres mot par mot, étudier un aligneur local spécialisé ; évaluer sa précision EN/FR, sa RAM/CPU et les licences, avec garde de confiance et repli à la phrase.
- Ne jamais « fabriquer » des timestamps exacts à partir de la longueur des mots : étiqueter chaque marqueur comme measured / estimated / human-reviewed.
- Exiger la cohérence mot prononcé -> sous-titre -> apparition du nombre ; si la précision est insuffisante, déclencher au niveau de la phrase et ne pas prétendre au mot.

### 10.4 Sous-titres mobiles

- SRT et VTT issus du même plan audio ; pas d'ellipse supprimant les mots du script.
- Typographie stable, haut contraste, 1–3 lignes, zones sûres pour interfaces TikTok et YouTube (évaluées à chaque changement de layout).
- Lorsqu'une action occupe le bas de l'image, repositionnement contrôlé ou ajustement du cadrage, pas de masquage.
- Vérifier la cohérence entre sous-titre incrusté et sous-titre exporté, et la latence observable sur l'encodeur final.

## 11. QA : mesurer le rendu réel, mais ne pas optimiser les mauvais indicateurs

### 11.1 Contrôles visuels

- Vérifier les vraies images encodées à divers temps, y compris **avant/après chaque cut** ; pas seulement les images dessinées avant FFmpeg.
- Vérifier 9:16 et zones sûres, lisibilité à **360 pixels de largeur**, pas d'objets hors écran ou de texte tronqué.
- Mesurer mouvement inter-frames, détecter les périodes de gel et distinguer objet voulu immobile vs scène qui devait s'animer.
- Détecter sauts de position/zoom non autorisés, disparition d'un acteur persistant, contradiction valeur affichée / valeur calculée.
- Vérifier densité de contours et couleurs pour éviter bruit visuel, mais jamais les transformer en score esthétique absolu.
- Vérifier artefacts d'aliasing, scintillement de sous-pixel, ombres incohérentes et variations brutales d'éclairage non motivées.

### 11.2 Contrôles audio

- FFmpeg ebur128 avec true peak sur la piste AAC **finale** ; LUFS, LRA, peak et récap des pistes.
- Détection de coupures, saturation, clics, longs silences inattendus, niveau voix insuffisant et bruitages dominants.
- Vérifier les événements audio/vidéo à partir d'une seule timeline, avec marge ≤80 ms pour les événements synchrones.
- Ne pas choisir un score musical par analyse du spectre ou par loudness ; validation humaine nécessaire.
- Soumettre un extrait d'audition voix seule, musique seule et mix final, sans imposer leur téléchargement à un spectateur.

### 11.3 Contrôles de narration et contenu

- Les grandeurs illustrées ont des unités, source et incertitude quand utile.
- Aucun faux comparateur, aucun nombre inventé, aucune imitation de voix ou de musique protégée.
- Les effets sonores ne représentent pas une certitude scientifique lorsqu'ils sont simplement illustratifs.
- Vérifier EN/FR et sous-titres correspondants, prononciation des nombres et noms propres.
- Conserver statut factChecked=false tant qu'une revue fiable n'est pas effectuée.

### 11.4 Grille de revue humaine indépendante

| Axe | 1/5 | 3/5 | 5/5 |
|---|---|---|---|
| Clarté | Compréhension difficile | Compréhensible avec effort | Immédiate même sur Android |
| Storytelling | Idées séparées | Progression correcte | Chaque étape prépare la révélation |
| Graphismes | Simples et génériques | Cohérents | Direction artistique aboutie |
| Animation | Cartes qui bougent | Actions pertinentes mais disjointes | Transformation continue et précise |
| Caméra / profondeur | Plan fixe | Mouvements acceptables | Cadrage narratif maîtrisé |
| Musique | Fond répétitif | Ambiance adaptée | Progression dramaturgique convaincante |
| Bruitages | Absents/gênants | Synchronisés | Expressifs, naturels, sobres |
| Voix | Robotique/inintelligible | Correcte | Naturelle, bien articulée et dirigée |
| Mixage | Voix masquée / clipping | Niveau stable | Parfaitement équilibré sur mobile et casque |
| Finition | Défauts visibles | Utilisable | Aucun défaut perturbant |

L'utilisateur peut noter chaque axe ; la cible de passage est **≥4/5 sur chaque axe critique**, pas seulement une moyenne. En cas d'échec, ouvrir une issue pointant vers un défaut observable, un timecode et une preuve.

## 12. Stratégie de tests, budgets CI et exploitation gratuite

### 12.1 Pyramide de validation

**Niveau A : tests unitaires rapides**
- Validation du schéma, unités, IDs, ordre temporel, dépendances circulaires, valeurs non finies, timestamps et comportement des interpolateurs.
- state_at(frame) doit être **pur et déterministe** ; vérification hash de frames synthétiques (ou métriques robustes lorsque l'anti-aliasing varie selon plateforme).
- Faux événements et données invalides doivent échouer **avant** TTS/encodage coûteux.

**Niveau B : intégration courte**
- Rendu de 3–6 secondes à 540 × 960, 15–30 fps selon le test ; continuité entre deux beats, 2 SFX synchrones, une phrase audio réelle si disponible dans le cache.
- Tests de synchronisation audio/vidéo, mappage unité->taille, caméra, captions, lumière et opacité.

**Niveau C : release candidate**
- 25–45 s, 1080 × 1920, 30 fps, H.264/AAC, qualité haute, vrais sous-titres, soundtrack continu, contrôle QA complet et lien vérifié.
- Ne pas employer d'assets/mocks dans ce niveau : des tests unitaires avec synthèse fictive peuvent exister **en dessous**, mais la validation finale nécessite une vraie vidéo.

### 12.2 Budget de rendu

- Exploiter d'abord les actions/caches et CPU GitHub Actions déjà configurés.
- Cacher **les assets immuables** et voix/parties du rendu par checksum script/version, jamais un « preview.mp4 » réutilisé hors de son hash source.
- Générer frames en flux/batches, ne pas conserver toutes les frames 1080p brutes en mémoire.
- Éviter N² sur les particules ; nombre de calques, objets, particules et trajectoires bornés avant rendu.
- Profiler temps par frame, temps de TTS, composition, mixage, encodage, RAM max et taille des artefacts.
- Si un moteur optionnel ralentit trop la CI sans gain visible sur la **même scène**, le rejeter.
- Les limites concrètes CPU/RAM/durée sont fixées après baseline mesurée, pas inventées ici.

### 12.3 Sécurité

- Tout brief, source ou texte externe est une donnée **non fiable** : schema strict, chemins sous répertoires dédiés, limites taille/temps, IDs, décodage de médias sécurisé, aucune commande shell construite par concaténation non validée.
- Pas de téléchargement automatique de fichiers exécutables, pas de désérialisation arbitraire de modèles ou d'assets.
- Respecter droits audio/visuels ; stocker licences et SHA de toute entrée ; refuser les échantillons sans preuve.
- Aucun média privé utilisateur ou secret ne doit apparaître dans les releases publiques, logs Actions ou commits.
- Pinner ou borner les dépendances et contrôler les changements de versions (FFmpeg, Kokoro, Python).

### 12.4 Fiabilité et liens directs

- Le seul lien communiqué comme « vidéo terminée » doit pointer vers un vrai **MP4** publié et téléchargé intégralement lors du test de release.
- Ne pas exposer un ZIP Actions comme téléchargement direct de vidéo.
- Les échecs doivent produire logs exploitables et manifests de diagnostic ; conserver des artefacts de preuve avec TTL, mais pas les traiter comme livraison définitive.
- Historiser les releases dans docs/video-history.json : sujet, version moteur, durée, taille, sha, codec, date, scorecard et statut humain.
- Versionner les schémas et maintenir une conversion backward compatible pour les anciens plans.

## 13. Démonstration de polyvalence : trois vidéos pilotes, trois défis distincts

| Pilote | Objectif | Composants partagés obligatoires | Échec interdit |
|---|---|---|---|
| A — Grandeur et comparaison **originales** (autre idée que le pliage vers la Lune) | Prouver animation d'une quantité et changement d'échelle dans le mode kinetic editorial | QuantityTrack, CameraTrack, repères, audio cues, ScoreComposer | Compteur désynchronisé ou copie de la référence |
| B — Circulation océanique réécrite | Prouver un phénomène causal continu en mode scientifique 2.5D | StoryGraph, flow field, acteurs persistants, caméra, Foley, QA | 5 cartes indépendantes ou simulation présentée comme exacte |
| C — Éruption volcanique ou autre sujet organique | Prouver changement d'état, matériaux, éclairage et physique illustrative | Renderer 2.5D, lumière, impacts, ambiences, mixage | Réemploi mécaniquement identique des assets du pilote A |

Chaque pilote : script inédit, storyboard et fait vérifiables, génération réelle, contact sheet, film MP4 et SRT/VTT, stems audio, rapport QA et **écoute humaine**. Une réussite sur un seul sujet ne prouve pas que le moteur est générique.

**Exécution du lot 0 :** [outil de mesure, baseline réelle, tests et éléments restants](LOT0_BENCHMARK_AV_REFERENCE_3561_2026-11-11.md). Les fonctionnalités futures restent définies comme non implémentées jusqu'à preuve sur MP4.

## 14. Plan d'exécution par lots avec dépendances et critères de sortie

### Lot 0 — Instrumenter et protéger la baseline (priorité P0)

**Actions**
- [ ] L0.1 Rendre reproductible la comparaison 3561.mp4 / Ocean : même pas de 250 ms, même redimensionnement, extraction FFprobe/EBU R128.
- [ ] L0.2 Écrire un script benchmark local qui produit **seulement des métriques et des contact sheets temporaires**, sans committer la référence privée.
- [ ] L0.3 Rassembler état actuel des tests, CI, QA et version de l'épisode livré.
- [ ] L0.4 Figer deux séquences maison comme baselines : motion graphique + phénomène 2.5D.
- [ ] L0.5 Ajouter un profil de benchmark (durée, cadence, RAM, taille, spectre, clips) et un rapport JSON versionné.

**Definition of Done** : les deux rendus maison se rejouent de manière mesurable ; aucune donnée de référence protégée ne part sur GitHub. Aucune régression de l'ancien workflow.

**Première tranche de réalisation :** [moteur pur, tests, preuve audiovisuelle et limitations](LOT1_MASTER_TIMELINE_PERSISTANTE_V1_2026-11-11.md). Le raccordement aux Shorts narrés demeure dans le backlog.

### Lot 1 — MasterTimeline et schéma d'événements (priorité P0, bloquant)

**Actions**
- [ ] L1.1 Spécifier schéma V2 et validation stricte (types, unités, IDs, horloge, limites).
- [ ] L1.2 Implémenter state_at(frame) déterministe et ObjectRegistry.
- [ ] L1.3 Compiler dépendances entre événements, rejeter cycles et chevauchements contradictoires.
- [ ] L1.4 Brancher l'adaptateur des cues PCM réels sans inventer de timecodes mot à mot.
- [ ] L1.5 Implémenter un acteur persistant sur au moins trois beats.
- [ ] L1.6 Implémenter une caméra et un événement audio liés au même événement source.
- [ ] L1.7 Ajouter tests robustes de valeurs, continuité, invalidités et determinisme.

**Definition of Done** : une vraie séquence interne à 30 fps montre un même objet modifié par trois événements distincts ; aucun saut ni reset ; les événements son/visuel partagent le même timecode ; tests unitaires et intégration réussis.

### Lot 2 — Transformation de grandeurs et animation des comparateurs (P0/P1)

**Actions**
- [ ] L2.1 QuantityTrack exact, conversion d'unités et édition des formats EN/FR.
- [ ] L2.2 Moteur de référence à seuil et équivalence physique, avec sources.
- [ ] L2.3 Caméra monde persistante et changements de grandeur perceptibles.
- [ ] L2.4 Déformation/extension de rigs 2D/2.5D et entrées/sorties de repères.
- [ ] L2.5 Anti-aliasing, interpolation subpixel et transition logarithmique contrôlée.
- [ ] L2.6 Export d'un pilote original 25–40 s ; revue frame/caméra/valeur.

**Definition of Done** : au moins 6 changements de repères ou de grandeur intelligibles, sans mensonge d'unité ni reset de compteur ; aucun élément tronqué en portrait. Un pilote complet est encodé et inspecté.

**Première liaison codée (CI à confirmer) :** [Foley causal dans le véritable AAC final, mixage avec narration et musique, tests d'intégrité](LOT3_FOLEY_CAUSAL_FINAL_AAC_V1_2026-11-11.md).

### Lot 3 — FoleyEngine et AudioEventTimeline (P1)

**Actions**
- [ ] L3.1 Définir les familles SFX et le contrat d'événement audio.
- [ ] L3.2 Générer 5 familles de SFX originaux 48 kHz avec enveloppes et variations déterministes.
- [ ] L3.3 Associer tous les SFX à un événement physique visible via ID et temps absolu.
- [ ] L3.4 Créer stems, manifestes de licence, mutes/solo A/B et rapport onset.
- [ ] L3.5 Limiter polyphonie, gain, transitoires et événements répétitifs.
- [ ] L3.6 Vérifier offset de synchronisation cible ≤80 ms et écoute A/B smartphone/casque.

**Definition of Done** : au moins 5 impacts/transformations correctement sonorisés sur la vidéo pilote ; sans clipping ni clic ; le système fonctionne également pour l'océan.

### Lot 4 — ScoreComposer musical continu et mastering (P1)

**Actions**
- [ ] L4.1 Profil musical global de 25–45 s, indépendant du nombre de scènes.
- [ ] L4.2 Générer motifs, harmonies, pads, basses, pulsation et reveal impact originaux à 48 kHz stéréo.
- [ ] L4.3 Alignement de la montée musicale à la narration/aux événements de la MasterTimeline.
- [ ] L4.4 Remplacer les fondus à silence inter-scènes, conserver une résolution harmonique d'épisode.
- [ ] L4.5 Ajouter mixage stems narration/music/foley/ambience et ducking sans pompage.
- [ ] L4.6 Recontrôler LUFS/true peak **après** AAC et ouvrir audit d'écoute.

**Definition of Done** : musique qui suit l'arc du film, aucun reset de boucle à chaque changement de scène, voix toujours intelligible, -16 LUFS ±1 et true peak ≤-1,5 dBTP sur l'export ; audio noté humainement.

### Lot 5 — Production visuelle premium et routeur de rendu (P1)

**Actions**
- [ ] L5.1 Formaliser VisualBible et deux presets kinetic-editorial/cinematic-2.5D.
- [ ] L5.2 Créer banque de composants, palette, typographie, matériaux et éclairage.
- [ ] L5.3 Transformer les éléments persistants selon le même state_at(frame).
- [ ] L5.4 Tester concrètement qualité/cout CPU des vecteurs Python vs un unique prototype moteur alternatif.
- [ ] L5.5 Vérifier la cohérence des coupes, composition, lumière, profondeur et répétitions.
- [ ] L5.6 Intégrer fallback vers les scènes historiques pour les thèmes non pris en charge.

**Definition of Done** : au moins deux genres différents exploitent des composants communs, avec composition lisible, action évolutive, zéro défaut de layout, et un film final non constitué de cartes répétées.

### Lot 6 — Direction de voix et alignement approfondi (P1/P2)

**Actions**
- [ ] L6.1 Construire un banc d'audition de voix avec même texte et niveau normalisé.
- [ ] L6.2 Traiter la prosodie à partir de script/ponctuation authentiques, sans time-stretch destructeur.
- [ ] L6.3 Ajouter dictionnaires de prononciation des nombres, unités et noms techniques.
- [ ] L6.4 Évaluer un aligneur local optionnel **uniquement** si nécessaire ; rapporter confiance et disponibilité.
- [ ] L6.5 Ajuster les animations à la parole réelle, en particulier nombre et révélation.
- [ ] L6.6 Écoute EN/FR sur le pilote et sous-titres synchronisés.

**Definition of Done** : script audible sans coupure, diction et rythme validés par écoute, captions sans omission, statut de précision des marqueurs honnête ; aucune régression de Kokoro.

### Lot 7 — QA audiovisuelle et publication de previews (P0 avant toute livraison finale)

**Actions**
- [ ] L7.1 Ajouter diagnostics de continuité d'objet et de caméra.
- [ ] L7.2 Ajouter contrôle de cohérence valeur réelle/valeur écran/unité.
- [ ] L7.3 Ajouter rapport de synchronisation audio/visuel et détection de clipping/clics.
- [ ] L7.4 Étendre manifest QA avec paramètres moteur, seeds, stems, versions et checksums.
- [ ] L7.5 Préserver les tests qualité existants, la sécurité du workflow de release et l'historique.
- [ ] L7.6 Vérifier le téléchargement HTTP public des octets complets du MP4, et l'expérience Android.
- [ ] L7.7 Construire la grille de revue humaine séparée des succès techniques.

**Definition of Done** : les trois pilotes possèdent un vrai fichier MP4, SRT/VTT, QA et lien public vérifié ; aucun statut « approuvé » automatique sans revue.

### Lot 8 — Industrialiser, profiler et stabiliser (P2)

**Actions**
- [ ] L8.1 Benchmarker CPU, RAM, I/O, encodeur, coût Actions par minute de film.
- [ ] L8.2 Introduire caching content-addressed sans contamination entre épisodes.
- [ ] L8.3 Tester reprise sur erreurs TTS/média/encodage ; retries bornés et idempotence du release.
- [ ] L8.4 Étendre la couverture à trois formats narratifs différents, avec mêmes garanties.
- [ ] L8.5 Documenter migration de schéma, CLI et procédure Android minimale.
- [ ] L8.6 Stabiliser un profil « production premium » unique et reproductible.

**Definition of Done** : déploiement/relance reproductibles, aucun faux lien, pas de dépendance payante, temps/ressources mesurés, documentation et tests à jour.

### Chemin critique

L0 -> L1 -> L2 -> L3 -> L4 -> L5 -> L6 -> L7 -> L8.  
Un sous-travail audio non dépendant peut être exploré parallèlement **seulement** si cela ne retarde pas la livraison complète de L1. Les lots sont des **dépendances techniques**, pas une promesse de calendrier inventé.

## 15. Backlog précis à découper en Issues GitHub

| Issue proposée | Domaine | Priorité | Preuve de fermeture |
|---|---|---|---|
| REF-01 | Baseline audiovisuelle reproductible | P0 | benchmark.json + protocole et exemples maison |
| REF-02 | Schéma MasterTimeline V2 et validation stricte | P0 | Tests parsing, types, cycles, horloge |
| REF-03 | ObjectRegistry et world state purs | P0 | state_at(frames) identique, scène continue |
| REF-04 | Source unique des événements audio/visuels | P0 | Cues synchrones identifiés et tracés |
| REF-05 | QuantityTrack, unités et comparateurs | P0 | Calculs vérifiés + six changements d'échelle |
| REF-06 | Caméra persistante et raccords | P1 | Tests aux frontières + preuve vidéo |
| REF-07 | Rig et micro-animation cinétique premium | P1 | Courbes/deformation non saccadées |
| REF-08 | FoleyEngine original avec stems | P1 | 5 classes SFX, true peak sécurisé |
| REF-09 | ScoreComposer continu 48 kHz | P1 | Musique dramaturgique et A/B sans loop 8s |
| REF-10 | Mixdown 4 pistes + sidechain | P1 | -16 LUFS ±1, TP≤-1,5 dBTP |
| REF-11 | VisualBible / kinetic editorial | P1 | Revue comparative sur 3 segments |
| REF-12 | Cinematic25D state adapter | P1 | Occlusion et continuité validées |
| REF-13 | Voix/lexique/alignement fiable | P1 | Auditions, pacing et markers honnêtes |
| REF-14 | QA intermodal et scorecard | P0 | Fail-closed sur défauts techniques |
| REF-15 | 3 films pilotes/benchmark multi-genres | P0 | Liens MP4 + SRT + scorecards |
| REF-16 | Performance/caches/histoire/provenance | P2 | Profil CPU/RAM et releases idempotentes |

**Pour chaque issue :** indiquer contexte, fichiers touchés, interfaces modifiées, tests attendus, capture vidéo ou extrait audio, risques, rollback possible, statut « implémenté/testé/validé humainement ». Ne fermer que lorsque les critères sont remplis sur un artefact réel.

## 16. Risques et parades

| Risque | Impact | Détection / mesure | Parade |
|---|---|---|---|
| Refactor détruisant les renderers historiques | Élevé | Tests et MP4 anciens cassés | Adapter branché par feature flag, migration progressive |
| Timeline audio et images désynchronisées | Critique | Diff événements horodatés, écoute finale | Une horloge maître, conversions frames/samples contrôlées |
| Mouvement artificiel créé pour augmenter la métrique | Élevé | Révision d'images, mauvaise lisibilité | Pas de quota pixel, validation narrative |
| Images trop chargées malgré plus de détails | Élevé | Densité contours/texte, test Android 360px | Direction artistique focalisée et contraste |
| SFX répétitifs ou clips | Élevé | Piques, écoute A/B, répétitions | Variation contrôlée, polyphonie, limiter |
| Musique concurrente de la voix | Critique | Ratio voix/bed, diction faible volume | Stems, ducking, mixage contrôlé |
| Prononciation erronée ou discours trop rapide | Élevé | Pacing et écoute de nombres propres | Lexique, réécriture, audition voix |
| Moteur alternatif imposant GPU/longues CI | Élevé | Profil RAM/CPU/temps | Spike comparatif, fallback Pillow |
| Licence non prouvée pour un son ou une texture | Critique | Manifest de provenance manquant | Refus de l'asset, synthèse originale |
| Erreur de mesure scientifique | Critique | Contrôle unités et source | StoryGraph factuel + revue scientifique |
| Liens temporaires ou MP4 absent | Critique | GET complet, SHA/ffmpeg | GitHub Release, QA fail-closed |
| Fuite du média source privé | Critique | Audit artefacts/logs/git status | Travail local, stocker uniquement mesures |
| Résultat joli sur un seul sujet | Élevé | Pilotes A/B/C | Contrat multi-genres et composants communs |
| Tests trop longs sur Actions | Élevé | Temps de jobs, erreurs infra | Pyramide tests, caching borné, smoke ciblé |
| Faux « qualité validée » par métriques | Élevé | Score humain absent | Double statut QA technique / éditorial |

## 17. Ordre du premier sprint de construction après adoption

1. **Avant code :** figer état des workflows principaux, notamment les dernières validations, et les invariants de MP4 direct existant.
2. Implémenter le **contrat événementiel minimal** avec une grandeur, un acteur, une caméra et un SFX ; le tester sans vidéo complète.
3. Rendre une **séquence de 4 à 6 secondes** où la grandeur et l'objet évoluent ensemble, et auditer au moins 3 frames temporelles réelles.
4. Réutiliser cette séquence dans deux autres beats successifs : confirmer la persistance de l'objet et du cadrage.
5. Ajouter un **son causal** puis une seconde classe de Foley, tous deux depuis le même event ID ; enregistrer les écarts.
6. Générer un premier film inédit 25–40 secondes **sans copier la référence** ; encoder, auditer, écouter et publier un MP4 **preview** vérifié.
7. Ne passer au ScoreComposer complexe qu'une fois ce premier cycle mouvement + événement sonore réellement robuste.

**Le premier gain attendu** est l'abandon des tableaux visuellement déconnectés, pas la multiplication des textures. **Le second gain** est la causalité du son, puis la composition musicale sophistiquée. L'ordre peut être ajusté sur preuves d'échec observées, et non sur préférence esthétique abstraite.

## 18. Matrice de décision Go / No-Go

| Porte | Go si… | No-Go si… |
|---|---|---|
| G0 Base intacte | Builds et fonctions historiques validés | QA actuelle contournée |
| G1 Timeline | Horloge stricte, unités et IDs, aucun reset | Mouvement uniquement décoratif |
| G2 Images | Caméra, comparateurs et objets continus | Cartes indépendantes déguisées en vidéo |
| G3 SFX | Stems causaux, onset mesurés et écoute | Sons placés arbitrairement |
| G4 Musique | Arc complet original, mix lisible, TP sûr | Boucle de 8 s simplement amplifiée |
| G5 Voix | Durée réelle et diction revues | Accélération/troncature pour remplir le clip |
| G6 QA | Vraies images, vrai MP4, vrai audio, checksums | Tests uniquement sur mocks / source avant encodage |
| G7 Livraison | Lien MP4 testé en entier, historique, statut clair | ZIP temporaire, lien hypothétique |
| G8 Référence | 3 sujets notés humainement ≥4/5 par axe critique | Une seule belle démo ou comparaison sans écoute |

## 19. Documents et technologies de référence

**Dépôt inspecté (main, 11 novembre 2026) :** les fichiers nommés en section 2 ; docs/QUALITY_ROADMAP.md ; docs/ROADMAP_RENDER_PREMIUM_2_5D_2026-11-07.md ; docs/PLAN_QUALITE_AUDIOVISUELLE_REFERENCE_3561_2026-11-11.md ; tests/test_audio_mastering.py ; .github/workflows/validate.yml.

**Outils officiels à évaluer, sans obligation de migration :**
- FFmpeg (loudnorm, ebur128, sidechaincompress, dynaudnorm, alimiter) : https://www.ffmpeg.org/ffmpeg-filters.html
- Motion Canvas (animations programmées avec synchronisation voix et export) : https://motioncanvas.io/docs/
- Manim Community (animation mathématique, MIT) : https://docs.manim.community/en/stable/
- Kokoro-82M (modèle speech local Apache-2.0, licence et limitations à respecter) : https://huggingface.co/hexgrad/Kokoro-82M

**Portée de cet engagement :** ce document décrit précisément **quoi construire, dans quel ordre, comment le vérifier et ce qui constituerait un échec**. Il ne prétend ni que les lots sont déjà codés ni que la musique/voix de la référence ont été subjectivement évaluées. Les futurs commits, tests et liens vidéo devront démontrer l'implémentation effective.

---
**Principe cardinal : une action, un état cohérent, une horloge, des images et des sons synchronisés — puis validation réelle.**
