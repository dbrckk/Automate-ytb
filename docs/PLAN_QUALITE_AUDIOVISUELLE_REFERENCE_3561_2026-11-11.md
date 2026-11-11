# Automate-ytb — feuille de route vers une réalisation audiovisuelle de référence

Date : 2026-11-11. Statut : plan de production, **pas** une fonctionnalité implémentée. Objet : améliorer le **pipeline réutilisable**, jamais seulement une vidéo.

## Objectif

Produire automatiquement des Shorts originaux 9:16 associant narration naturelle, motion design élégant, animation continue motivée par le propos, musique composée selon l'arc narratif, bruitages synchronisés et rendu professionnel. La référence 3561.mp4 (utilisateur) sert de cible de **niveau de finition**, pas de source à copier, intégrer ou republier (images, musique, identité, narration et assets restent exclus). Le moteur ne doit pas se limiter à un sujet mathématique : deux modes artistiques partagent une même horloge et une même chaîne QA : (a) motion graphics cinétiques, (b) cinéma 2.5D avec décors, matières et profondeur.

## Référence et mesure reproductible

| | Vidéo de référence | Automate-ytb, Ocean Heat Engine |
|---|---:|---:|
| Durée | 30,8 s | 34,433 s |
| Définition native du fichier | 576 x 1024 | 1080 x 1920 |
| Images par seconde | 30 | 30 |
| Surface médiane modifiée à 250 ms, différence de luminance > 8/255 sur image ramenée à 144 x 256 | 9,3 % | 3,3 % |
| Densité médiane de bords Canny à 144 x 256 | 4,7 % | 7,2 % |
| Volume intégré mesuré FFmpeg EBU R128 | -14,8 LUFS | -16,1 LUFS |
| Pic vrai mesuré FFmpeg | +0,5 dBTP | -1,5 dBTP |
| Audio export | AAC stéréo 44,1 kHz ~32 kb/s | AAC stéréo 48 kHz ~242 kb/s |

Ces chiffres sont des observations **du fichier**, pas des scores d'esthétique ni des preuves d'une écoute humaine. Le pic vrai positif de la référence n'est **pas** une cible : éviter l'écrêtage. Le pourcentage de pixels modifiés est un proxy dépendant du contenu, pas un quota de mouvement. Les extraits vidéo de référence ne sont pas enregistrés dans le dépôt public.

### Différence de conception

- Référence : **une métaphore physique continue** (épaisseur d'une feuille pliée qui croît), échelle persistante, étapes visibles et objets de comparaison, palette nocturne retenue, vert menthe et or chauds, hiérarchie typographique très nette, grands espaces négatifs et événements qui transforment réellement la géométrie du monde. Chaque progrès est visualisé plutôt que présenté sous forme de tableau.
- Pipeline actuel : cinq scènes océaniques successives, titres et badges largement répétés, flèches et formes explicatives indépendantes. Le débit d'informations graphique est élevé et l'action visuelle évolue plus faiblement, malgré une définition de fichier supérieure.
- Audio actuel : automate_ytb/soundtrack.py synthétise quatre thèmes sur des **boucles de 8 s mono à 16 kHz**, avec fondus vers zéro à chaque scène ; automate_ytb/episode.py accepte seulement musique ambient/none ; aucun moteur générique de bruitages narratifs n'est raccordé à l'épisode science. Le pipeline Kokoro dispose déjà de marqueurs PCM par phrase dans automate_ytb/episode.py ; les conserver.
- Mécanique visuelle actuelle : automate_ytb/science_portrait.py choisit des sujets et dessins par domaine, automate_ytb/scene25d.py assemble jusqu'à 16 plans avec parallaxe, automate_ytb/transitions.py traite les scènes comme des clips successifs avec coupe/fondu. L'animation de transformation inter-scènes d'objets persistants n'est pas une abstraction de premier ordre.

## Architecture cible — une seule horloge pour le visible et l'audible

Script original et validation scientifique -> StoryDirector -> StoryGraph (objets, actions, analogies, continuité et impacts) -> VoiceDirector (Kokoro, PCM, prosodie, marqueurs de phrases) -> MasterTimeline (temps absolu, état persistent, caméra, courbes et événements) -> VisualRenderer (kinetic vectors ou cinématique 2.5D) + ScoreComposer (musique originale) + FoleyEngine (bruitages originaux, stems) -> AudioMixer -> FFmpeg H.264/AAC -> QA technique + revue humaine -> Release MP4 stable et historique GitHub.

Tout objet (échelle, position, épaisseur, opacité, couleur, lumière, source de bruitage) doit être dérivable de la même position temporelle absolue ; une ré-exécution à graine égale reproduit les mêmes images et sons. Ne jamais produire une illustration de fond figée en la qualifiant d'animation.

## Ordre de réalisation (une étape complètement terminée avant la suivante)

### P0 — Instrumentation, référence et garde-fous (fondation)

1. Scripts d'audit hors ligne : ffprobe, frames contact sheet, frame-to-frame motion salience, luminosité/contraste/couverture du texte, ebur128/true peak et vérification des sous-titres. Mémoriser des **métriques**, pas le média de référence privé.
2. Baseline immuable et test sur **deux sujets originaux distincts** : le Short Ocean Heat Engine et un nouvel épisode à croissance d'échelle (nouvelle idée et nouvelles illustrations, sans copier le texte de la référence). Sorties : `benchmark.json`, `storyboard.jpg`, `audio-report.json` et run GitHub public.
3. Conserver tous les tests et chemins de livraison existants ; séparer QA technique et validation humaine.
**Critère de fin** : mesure reproductible automatisée sur deux fichiers ; aucun changement des fichiers originaux ni rupture des Release MP4.

### P1 — MasterTimeline et actions visuelles continues (priorité #1)

1. Ajouter un plan d'action déclaratif validé (`BeatAction`: actor, cause, precondition, start/end cue, easing, from/to, spatial units, scene scope, collision/occlusion), pas des scripts spécialisés uniquement dans un Short.
2. Introduire des identifiants d'objets persistants et des caméras coordonnées monde pour traverser les chapitres sans réinitialiser décor, échelle ni position. Déplacer, déformer, allonger et comparer des éléments au fil d'une phrase.
3. Courbes cubic/spring contrôlées, animation incrémentale à 30 fps, suivi de caméra, trajectoires, incréments lisibles, transitions de monde et mini-révélations ; éviter 5 planches fixes séparées par des fondus.
4. Aligner les événements sur les **marqueurs PCM existants** (précision à la phrase, pas à chaque phonème), avec offset explicite ; aucune invention d'horodatages mot par mot.
**Critère de fin** : dans un prototype 30-40 s, au moins un objet conserve son identité sur >= 3 beats, 3 changements d'échelle intégrés à la même prise en scène, jamais de rupture visuelle involontaire ; inspecter frames 1/5/10/20/30 et la continuité aux frontières.

### P2 — Direction artistique et moteur d'animation graphique premium

1. Créer un profil `kinetic-infographic` (palette limitée, contraste contrôlé, matière emissive originale, lueurs douces, micro-particules sobres, atmosphère, ombres de contact, guide visuel de profondeur) séparé de `cinematic-2p5d` (matériaux riches, éclairage, perspective, occlusion). La référence implique **moins de traits**, pas plus de bruit de texture.
2. Remplacer le bandeau d'explication permanent par une hiérarchie épisodique : question/hook, progression, analogie à échelle commune, preuve visuelle et conclusion. Texte à l'écran réservé aux chiffres, noms d'échelle et phrases fortes ; les sous-titres suivent la voix.
3. Vecteurs anti-crénelés, formes Bezier, morphing, échelles logarithmiques / exponentielles, unités réellement calculées, compositing glow HDR simulé et sous-pixel sans tremblement. Réutiliser `scene25d.py`, `lightfield25d.py` et `optical_motion25d.py` lorsqu'ils conviennent.
4. Pilote moteur : d'abord étendre Pillow/FFmpeg ; comparer sur une **scène identique** un prototype Motion Canvas (éditeur/moteur vectoriel TypeScript) ou Manim CE (Python/MIТ) ; n'adopter de dépendance supplémentaire que si rendu, automatisation headless, robustesse et temps de CI sont meilleurs.
**Critère de fin** : storyboard avec composition hiérarchisée, zéro titre masquant l'action, aucune forme géométrique de substitution, zéro gel inattendu, zéro élément tronqué, rendu 1080x1920/30fps soutenu sur GitHub Actions.

### P3 — Réalisateur musical + bruitages événementiels (priorité #1 avec P1)

1. Remplacer le bed unique 16 kHz/8 s par un `ScoreComposer` original **48 kHz stéréo** : motifs et timbres modulaires, basse/pulse, nappes, arpège, textures, crescendo, relâchements, passage entre scènes sans fondu au silence systématique. Structure globale `hook -> développement -> révélation -> résolution` déterminée par la même MasterTimeline.
2. Nouveau `FoleyEngine` génératif : plis, froissements, swoosh de montée, pops de comparaison, impulsions, transitions d'échelle, chutes, impacts, eau/air/électricité selon le sujet ; création synthétique originale (oscillateurs, bruit filtré, enveloppes, couches) ou éléments audio tiers uniquement si licence compatible vérifiée et provenance enregistrée.
3. Créer des événements audio à t absolu (onset en millisecondes, pré-roll éventuel, durée, vélocité, scène, volume, pan, famille), déclenchés **par l'action visible**, pas selon un nombre arbitraire de bruitages par seconde.
4. Mixer en pistes distinctes narration/musique/foley via FFmpeg, égalisation légère, panoramique prudent, sidechain/ducking sous les mots et limiter de pic vrai. Piste finale cible -16 LUFS ±1, **true peak <= -1,5 dBTP** ; éviter clics, bruitages dominants et fatigue. Garder le mix d'origine disponible pour A/B.
**Critère de fin** : au moins 5 événements démontrés image/son dans le pilote, écart de synchronisation <= 80 ms au niveau des événements datés, transitions de volume sans clic, analyse EBU R128 complète, écoute A/B humaine obligatoire pour caractère musical et choix des bruitages.

### P4 — Voix naturelle et montage expressif

1. Conserver Kokoro local et les vrais timestamps PCM. Évaluer les voix anglaises déjà prises en charge (`af_heart`, `af_bella`, `af_nicole`, `af_sarah`, `am_michael`) par des extraits d'audition sur **même texte**, sans annoncer une voix meilleure sans l'avoir écoutée.
2. Revoir l'écriture pour respiration et accentuation : phrases courtes, pauses après une révélation, un seul nombre frappant par beat, variation de rythme, éviter superposition musique/voix sur une donnée décisive.
3. Ajouter chaîne de post-traitement non destructive : niveau de parole homogène, réduction des sifflantes et résonances après revue, compression douce, contrôle de consonnes ; ne jamais accélérer ou tronquer la voix pour remplir une durée.
4. Réglage d'edit : mouvements et effets avant/pendant/après la phrase correspondante, cuts au sens et à la musique, visual payoff dans les dernières secondes, hook lisible dès les premières images.
**Critère de fin** : écoute humaine sur mobile et casque, aucune phrase coupée, aucune prononciation critique incorrecte, diction et musique notées séparément ; timings subtitles PCM exacts, scènes non silencieuses inutilement.

### P5 — Orchestration polyvalente et sélection automatique des plans

1. Un `StoryGraph` de concepts (physique, quantité, acteur, causalité, comparaison) propose des actions filmables. Refuser les concepts sans visualisation intelligible plutôt que générer cinq cartes informatives.
2. Routeur de rendu selon l'intention : science/math/logarithme -> motion graphics ; nature/produit/histoire -> 2.5D cinématique ; les deux partagent voix, musique, SFX, contrôle qualité et livraison.
3. Banque de composants **originaux** (règle d'échelle, trajectoire, halo, compteur, caméra, surface volumique, occlusion, révélation, transformation), indépendante de l'épisode et dotée de tests de non-régression.
**Critère de fin** : deux sujets non apparentés réutilisent le moteur sans fonctions conditionnelles codées en dur selon le titre ; nouvelles vidéos créées uniquement à partir de script + storyboard de paramètres.

### P6 — QA de production, revue comparative et livraison

1. CI rapide à 540x960/720x1280, évaluation d'extraits clés ; rendu final GitHub Actions en 1080x1920 30fps, H.264/AAC stéréo 48k ; reproductibilité par version de moteur, seed, source hash et manifest de timing.
2. Contrôles bloquants : frames manquantes, gel d'action, texte hors safe-zone, silence/clic imprévu, débit de voix, désynchronisation >80 ms, clipping, narrateur absent, média altéré, autorisations d'actifs, erreurs FFmpeg, absence de MP4 téléchargeable.
3. Barème d'écoute/vision **humain** (mobile puis casque) séparé par axes : lisibilité, conception des scènes, qualité de mouvement, graphismes, musique, bruitages, voix, équilibre du mix, storytelling. Objectif >=8/10 sur **chacun** des axes critiques pour les deux sujets, sans maquiller les scores par des moyennes ; A/B aveugle quand possible.
4. Les métriques de mouvement n'optimisent pas une agitation artificielle : pour le **pilote cinétique seulement**, viser une médiane indicative de 7-12 % des pixels changés dans l'échantillonnage de cette référence, puis examiner humainement toutes les scènes (texte et éléments stables ne doivent pas bouger inutilement).
5. Publier uniquement les prévisualisations passées par `quality.py`, `media_qa.py`, `qa_bundle.py` et la vérification complète du fichier HTTPS dans `science-preview-download.yml`, préserver `docs/video-history.json` et la mention **UNREVIEWED** jusqu'à validation éditoriale.
**Critère de fin** : deux MP4 originaux techniquement validés, liens directs fonctionnels sur Android, journal de tests GitHub, scorecard humain explicite, et aucun changement cassant du pipeline précédent.

## Séquence d'exécution immédiate après acceptation

1. P0 : figer les rapports, créer test de non-régression des deux références techniques, documenter l'audio existant.
2. P1 : livrer une seule scène test de croissance d'échelle avec caméra persistante, calée sur un vrai fichier voix ; vérifier frames et fluidité ; **ne pas démarrer plusieurs moteurs à moitié finis**.
3. P3 : ajouter deux bruitages originaux synchronisés + une vraie phrase musicale sur cette même scène, puis étendre aux cinq beats.
4. P2 : polir la palette, la lumière, le texte et la profondeur une fois le mouvement causal correct.
5. P4 -> P6 : compléter le mix, auditions, exporter les deux vidéos, QA et collecte de scores ; seulement ensuite généraliser P5.

## Périmètre et contraintes non négociables

- 100 % gratuit/open source lorsque suffisant, sans clé payante ni quota de modèle distant obligatoire.
- Revue humaine de l'audio et de l'esthétique : les métriques de fichier seules ne permettent **pas** d'affirmer la qualité musicale, l'émotion de la voix ou l'efficacité du montage.
- Aucun média de la référence fourni par l'utilisateur n'est copié dans GitHub, repris tel quel, intégré à une sortie ou revendiqué comme une création originale.
- Fiabilité > fonctionnement réel > sécurité et provenance des assets > architecture > performance > interface. Chaque étape a ses tests avant d'être dite terminée.

## Documents externes examinés

- Motion Canvas : https://motioncanvas.io/docs/ (moteur vectoriel synchronisable avec voix).
- Manim CE : https://docs.manim.community/en/stable/ (moteur libre d'animation mathématique).
- FFmpeg loudnorm / sidechaincompress : https://www.ffmpeg.org/ffmpeg-filters.html (normalisation EBU R128 et mixage).

