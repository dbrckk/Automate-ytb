# Automate-ytb — studio de vidéos YouTube originales

Première version fonctionnelle inspirée des **étapes** de la démonstration vidéo : étudier une niche, définir un concept, écrire une narration, composer des scènes, produire une voix, assembler une vidéo, créer des miniatures et préparer sa diffusion. Ce dépôt **ne copie pas** les vidéos ni les personnages de Murph.

Voir aussi [les décors originaux guidés par le scénario](docs/STORY_LANDSCAPES.md), avec paysages persistants en mode cartoon.

## Ce que fait la V1

- **Recherche de niches** : analyse en lecture seule des résultats de l’API officielle YouTube, avec vues, ancienneté et abonnés visibles. Ces indicateurs ne prouvent ni les revenus ni la saturation réelle d’une niche.
- **Création de brouillons** : à partir d’un sujet, d’un angle, d'un script personnel facultatif et de faits accompagnés de leurs sources HTTPS.
- **Storyboard** : scènes et illustrations originales générées localement avec Pillow. Des images détenues ou licenciées peuvent être placées dans `assets/scene-01.png`, etc.
- **Montage** : assemblage FFmpeg des scènes avec transitions simples, audio narratif fourni ou TTS eSpeak, sous-titres SRT, et trois miniatures.
- **Livrables** : projet JSON, narration, plan de montage, vidéo MP4, miniatures, métadonnées YouTube et liste de contrôles éditoriaux.
- **Depuis Android** : lancer les workflows `Actions` sur GitHub puis récupérer l’artefact téléchargeable. Aucun PC personnel obligatoire.

La V1 **n’inclut pas** de génération cinématique IA photoréaliste, de clone de voix, de recherche factuelle IA sans vérification, de montage identique à la vidéo de référence ni de publication automatique YouTube. Les visuels locaux sont des cartes graphiques originales qui servent de base au montage. Pour des images et animations plus sophistiquées, utiliser des fournisseurs avec droits d’utilisation vérifiés et injecter les médias approuvés dans le storyboard.

## Nouvelle action Android : vidéo complète de brouillon

**[One-click YouTube preview (free)](https://github.com/dbrckk/Automate-ytb/actions)** permet désormais de préparer des scènes originales depuis un scénario fourni, de générer des illustrations procédurales sans coût d'API, d'enregistrer une voix provisoire eSpeak, de monter un MP4 (720p ou 1080p), de produire les sous-titres et trois miniatures. Le tout est téléchargeable comme artefact GitHub Actions, sans PC personnel.

**Important :** les cartes illustrées sont des **brouillons graphiques** ; ce n'est pas encore une vidéo IA à la qualité de Murph. Aucun contenu n'est publié sur YouTube. Ne pas transmettre de texte confidentiel aux entrées Actions d'un dépôt public.

Guide : [Production Android en un workflow](docs/ONE_CLICK_ANDROID.md).

## Guide rapide sur GitHub / Android

1. Ouvrir l’onglet **Actions** du dépôt puis **Generate YouTube draft**.
2. Choisir **Run workflow**, renseigner le sujet, la langue, le style et la durée. On peut également fournir son propre texte.
3. Ouvrir le run terminé, télécharger l’artefact `automate-ytb-video-draft` dans la rubrique **Artifacts**.
4. Vérifier les sources, les images, la prononciation, les droits des médias, les métadonnées et la qualité de la vidéo **avant toute publication manuelle**.

Pour découvrir des niches, définir un secret de dépôt nommé `YOUTUBE_API_KEY` (clé personnelle Google Cloud autorisée à utiliser YouTube Data API v3), puis lancer **Discover YouTube niches**. Ne pas placer de clé dans les fichiers ou les logs.

## Production multi-scènes : nouveauté

Le pipeline peut désormais planifier **150 plans pour un épisode de 15 minutes** et
exporter un lot de prompts image compatibles avec des fournisseurs interchangeables.
Chaque image importée est contrôlée (source/droits déclarés, empreinte SHA-256, coût),
puis les scènes prêtes peuvent être assemblées en **MP4 avec léger mouvement de caméra**
par FFmpeg. Le rendu reprend les segments déjà préparés après une interruption.

Depuis Android, ouvrir **Actions → Prepare original image-scene batch** pour obtenir
un kit de production sans payer d'API. Les images ne sont **pas générées par ce workflow** ;
l'intégration au fournisseur d'images sera une étape distincte et soumise au budget.

Voir [le guide de production scène par scène](docs/IMAGE_SCENE_PIPELINE.md).


Python 3.11+, FFmpeg, éventuellement `espeak-ng`, et :

```bash
python -m pip install -e .
python -m automate_ytb create \
  --topic "Pourquoi la lune change-t-elle de forme ?" \
  --angle "Une explication pédagogique et visuelle" \
  --style cartoon --language fr --duration 90 \
  --output outputs
```

Pour uniquement produire le storyboard et les fichiers de plan :

```bash
python -m automate_ytb create --topic "Une question originale" --plan-only
```

Pour la recherche officielle YouTube :

```bash
export YOUTUBE_API_KEY="VOTRE_CLE"
python -m automate_ytb discover --queries "science animation" "historical facts" \
  --min-views 20000 --max-subscribers 100000
```

Tests :

```bash
python -m unittest discover -s tests -v
```

### Son, narration et sous-titres

Le workflow Android gratuit peut désormais produire une **musique de fond
originale par synthèse locale**, dont l'intensité est réduite pendant la voix
Kokoro ou eSpeak. Un limiteur protège contre les pics du mixage, et les
sous-titres SRT sont segmentés en phrases plus courtes. Les durées de ces
phrases restent des estimations, **pas** une synchronisation mot par mot.

Sur Android, choisir **Soundtrack: ambient** ou **none** dans l'action.
En local :

~~~bash
python -m automate_ytb.episode --plan build/scene-plan.json \
  --output build/video --voice espeak --soundtrack ambient
~~~

La musique synthétique est une bande provisoire : elle doit être écoutée et
validée avant publication.

## Repères tirés de la vidéo fournie

La vidéo montre une chaîne d'animation explicative (Murph), des indicateurs YouTube Studio, des exemples de contenu illustré, des instructions textuelles dans Codex et un outil de génération de séquences vidéo. Nous avons transposé **l’organisation de la production**, pas les créations tierces ni les chiffres présentés.

## Intégration à Star List

`dbrckk/star-list` reste le catalogue de ressources à évaluer pour les évolutions. Les familles intéressantes sont : **FFmpeg** et outils de montage, **Kokoro** ou autres solutions de voix autorisées, **StoryDiffusion** et outils visuels, **MoneyPrinterTurbo** pour l'orchestration, et les outils de génération d'assets 3D. Ces dépôts sont des **candidats**, non des dépendances intégrées dans la V1. Examiner licences, droits commerciaux, exigences de calcul et API avant adoption.

### Mastering audio automatique et contrôles EBU R128

Le MP4 de prévisualisation utilise maintenant une normalisation
**EBU R128** : environ **–16 LUFS** avec narration, **–24 LUFS** pour
l'ambiance seule, et un plafond cible de **–1,5 dBTP**.
Les niveaux réellement mesurés sur le MP4 final (LUFS intégrés,
pic réel et pic numérique) sont inclus dans `media-report.json` et
`qa-summary.json`. Le contrôle Android signale les écarts
importants ; aucun fichier n'est publié automatiquement.

Il s'agit d'un réglage technique et non d'un mastering artistique.
Les valeurs sont des choix internes au projet, pas des obligations
officielles de YouTube. L'écoute humaine reste nécessaire.

### Storyboard visuel vérifié sur MP4

L'action Android produit maintenant une **planche JPEG de relecture**,
assemblée depuis les images du MP4 effectivement encodé : aperçu rapide
sur téléphone des scènes, cadrages et transitions de l'épisode.
Le fichier visual-review.json signale les images impossibles à décoder
ou majoritairement noires ; qa-summary.json vérifie que cette analyse
correspond exactement au MP4 présent. Les erreurs bloquantes n'autorisent
pas à considérer le brouillon comme techniquement prêt. Voir
[le guide Android](docs/ONE_CLICK_ANDROID.md).

## Contrôles de qualité

- Aucune promesse de revenus YouTube ou de monétisation.
- Aucune récupération automatique de vidéos/images de chaînes concurrentes.
- Les faits importés ont une provenance explicite ; la présence d’une URL ne suffit pas à les vérifier.
- L'utilisateur reste responsable des droits de voix, musique, images, titres et clips.
- Toute mise en ligne passe par une validation explicite ; le système produit des brouillons, non des publications autonomes.

### Narration neuronale optionnelle

La création de brouillons propose maintenant une voix **Kokoro-82M** en français
ou anglais, activée uniquement si voice=kokoro est sélectionné dans GitHub Actions.
La voix eSpeak reste le choix le plus léger par défaut. La durée réelle des
enregistrements ajuste les scènes afin de ne pas couper la narration.
Les sous-titres ne sont pas encore alignés mot par mot. Kokoro télécharge
ses poids et demande davantage de calcul sur le runner.

Voir le [guide de narration neuronale](docs/NATURAL_NARRATION.md).

### Réalisation contextuelle des scènes

Le storyboard peut désormais inférer des **consignes visuelles non factuelles**
depuis le scénario original : jour/nuit, pluie, vent, nuages, action des ailes,
expressions et types de plans. Elles pilotent les décors et les calques animés
dans le workflow gratuit et sont attachées aux images approuvées pour éviter
la réutilisation de scènes obsolètes. Ce moteur est fondé sur des mots-clés,
pas sur un modèle de compréhension complète. Voir
[le guide Android](docs/ONE_CLICK_ANDROID.md).

### Animation procédurale originale

Le workflow Android gratuit inclut désormais une **chouette 2D articulée**
(ailes indépendantes, oscillation du corps, clignements) lorsque la description
du personnage contient owl, chouette ou hibou, en style cartoon.
La vidéo est calculée à partir de calques originaux avec FFmpeg, sans API payante.
Les autres personnages restent pour l'instant sur des visuels de brouillon.
Cette animation est plus vivante qu'un diaporama, mais n'atteint pas encore
la qualité visuelle de la référence ni une animation universelle des personnages.

## Nouveau : aperçu vidéo complet depuis Android, sans API payante

Le workflow **[One-click offline video preview](https://github.com/dbrckk/Automate-ytb/actions/workflows/one-click-offline-video.yml)** transforme un scénario original en MP4 16:9, illustrations 2D originales cohérentes, voix eSpeak optionnelle, sous-titres SRT, couverture et rapports de production. Il fonctionne dans GitHub Actions, même sans PC, et ne demande aucune clé d'un service de génération d'images.

Ce mode utilise des **dessins procéduraux** et une **voix synthétique** : ce n'est pas encore la qualité visuelle ni la voix neuronale des outils IA montrés dans la vidéo de référence. Il ne recherche pas de faits automatiquement et ne publie rien sur YouTube. Pour les détails, voir [le guide Android](docs/ONE_CLICK_OFFLINE_EPISODE.md).

## Contrôle technique des aperçus vidéo

Le workflow Android valide le vrai MP4 avec FFprobe/FFmpeg avant d'annoncer
une réussite. Il compare les pistes de narration/musique présentes, les durées,
les sous-titres et les rapports aux options sélectionnées. Chaque aperçu
contient un fichier quality-report.json avec mesures et avertissements.
Cette validation technique ne remplace pas une revue éditoriale humaine.

### Contrôle qualité du MP4

Le workflow Android exporte également les sous-titres WebVTT et le rapport
`quality-report.json` (flux vidéo/audio, durée, résolution, pic audio,
cohérence des timecodes). La vérification est technique et ne remplace pas la
révision de la voix, des faits et des droits.


### Contrôles techniques cumulés

Les artefacts Android contiennent désormais deux rapports indépendants
(`quality-report.json` et `media-report.json`) et une synthèse
(`qa-summary.json`). Le second contrôle ne remplace plus les mesures du premier.
Le résultat reste un **brouillon** : l'analyse automatique ne valide pas la
qualité éditoriale ni la publication sur YouTube.

### Sous-titres synchronisés sur la synthèse vocale

L'action Android **One-click YouTube preview (free)** accepte maintenant
**Caption timing = audio** (défaut) pour utiliser les durées PCM réellement
synthétisées de chaque fragment de texte, ou **estimated** pour préserver le
mode rapide avec voix prononcée d'un seul tenant par scène. Les sous-titres
SRT/VTT suivent ainsi plus précisément les transitions entre phrases de la
voix de synthèse, au prix de plusieurs appels locaux au moteur TTS.
Ce n'est ni de la reconnaissance vocale ni un alignement au mot. Le son,
la ponctuation et les pauses nécessitent toujours une réécoute humaine.
Voir [narration naturelle](docs/NATURAL_NARRATION.md).

### Finitions de narration audio

En mode `Caption timing = audio`, l'outil retire maintenant une partie des
longs silences placés **avant ou après** les fragments vocaux synthétisés
(eSpeak/Kokoro), en conservant les pauses internes et en limitant les clics
aux raccords. Les sous-titres restent synchronisés avec la durée du PCM
réellement monté. `episode-report.json` indique la durée totale retirée.
Un fragment totalement silencieux est rejeté. Le mode `estimated` conserve
le comportement historique sans ce traitement. Cela améliore les raccords
techniques, pas nécessairement la prosodie ; écouter avant toute diffusion.

### Décors narratifs et mouvements de caméra (cartoon chouette)

Les scènes de la chouette originale en mode **cartoon** ne sont plus
principalement des fiches avec un grand encadré de narration. La vidéo place
le personnage dans un **paysage 2D dessiné localement** : profondeur par plans
de collines, arbres, feuillage, touches de lumière, météo et ombre au sol.
Le scénario conserve ses sous-titres SRT/WebVTT : le texte complet n'est plus
gravé sur la moitié des images.

Six cadrages sont désormais différenciés : large (stable), moyen, rapproché,
macro, contre-plongée et épaule. Les cinq derniers intègrent un léger mouvement
de caméra de type panoramique, calculé image par image par FFmpeg à partir de
paramètres validés. Les rendus restent déterministes et compatibles 720p/1080p.
La version du moteur est incluse dans l'empreinte des visuels : un ancien
visuel approuvé ne peut pas être réutilisé silencieusement après ce changement.

**Limites :** ce sont des illustrations procédurales stylisées en 2D, pas des
scènes photoréalistes, des modèles 3D ou des vidéos générées par IA.
L'animation universelle des autres personnages reste à réaliser. Les
nouveaux cadrages et compositions demandent une relecture visuelle avant
toute publication.

### Nouveaux personnages 2D animés : renard, lapin et chat

Le mode **cartoon** sélectionne désormais automatiquement un personnage
original animé lorsque la description indique explicitement *renard / fox*,
*lapin / rabbit / bunny* ou *chat / cat*. Chaque animal dispose d'un dessin
différent (museau, oreilles, couleur, queue), d'un mouvement de corps, d'une
queue animée et d'un clignement. Les scènes partagent les décors naturels,
la météo, les six cadrages et les mouvements de caméra de la chouette.

La sélection reste **conservatrice** : les descriptions non reconnues
continuent d'utiliser le générateur de cartes 2D existant ; aucun personnage
inconnu n'est remplacé arbitrairement par un animal. Les illustrations sont
fabriquées localement avec Pillow et la vidéo avec FFmpeg, sans utiliser de
banque d'images, d'API payante, de modèles 3D ni d'images tierces.

Chaque scène enregistre son moteur `original-forest-fox-v1`,
`original-forest-rabbit-v1` ou `original-forest-cat-v1`. Les empreintes
des illustrations incluent la version du moteur, la description du personnage,
le script et les choix du réalisateur. Modifier l'animal ou l'art exige une
nouvelle validation, et non la réutilisation silencieuse des assets.
`render-report.json` indique le nombre de scènes concernées dans
`animatedForestScenes`.

**Limite :** style cartoon 2D procédural, sans animation squelettique 3D,
lip-sync réaliste ni garantie d'une direction artistique professionnelle.
Écouter et visionner le MP4 avant toute publication.

### Transitions cinématiques sans décaler la narration

Le rendu vidéo ajoute désormais une transition **dissolve** entre deux scènes :
la dernière image de la scène précédente s'estompe pendant environ 0,32 s
au début de la scène suivante. Ce montage est purement visuel. Chaque scène
conserve **exactement son nombre d'images** ; la voix, la musique, les
horodatages SRT/WebVTT et la durée finale du MP4 ne sont pas raccourcis.

Dans le workflow Android **One-click YouTube preview**, choisir
`Transition = dissolve` (par défaut), ou `cut` pour des coupes franches.
L'opération est réalisée localement par FFmpeg avec les plans originaux déjà
approuvés, sans téléchargement, API facturée ni publication automatique.
Le rapport `render-report.json` précise le mode, le nombre de transitions,
la durée de fondu et le décalage temporel (toujours 0 ms).

La transition est un **fondu de l'image finale figée** vers la nouvelle
scène, et non un morphing ou un fondu entre deux scènes animées en temps
réel. Une scène initiale unique n'a pas de transition. L'effet est léger,
réversible et peut ajouter du temps de calcul FFmpeg au premier rendu ;
le résultat doit être revu avant publication.

### Atmosphères 2D vivantes de jour et de nuit

Les décors **cartoon** des chouettes, renards, lapins et chats disposent
maintenant de deux ambiances supplémentaires : des lucioles lumineuses au
premier plan des scènes de **nuit** et de fines particules de pollen
flottantes dans les scènes de **jour**. Les effets sont produits localement
avec Pillow puis déplacés image par image dans FFmpeg. Le ciel, la lune
et les étoiles restent fixes pour éviter les mouvements incohérents.

Le choix d'ambiance continue de respecter la météo déterminée à partir
des mots du scénario, sans inventer de nouveaux événements. Les effets
existants de pluie, de vent, d'orage et de nuages sont conservés.
Les versions des deux moteurs visuels et du cache MP4 ont été modifiées
pour empêcher la réutilisation trompeuse des anciens rendus.

Ces effets restent **des illustrations 2D procédurales**. Ils n'impliquent
ni vidéo générée par IA ni effets de particules photoréalistes.

### Expressions et actions animées (cartoon)

Les quatre personnages originaux en mode `cartoon` (chouette, renard, lapin,
chat) ont désormais une **chorégraphie distincte** lorsque le scénario
mentionne la marche, la course, le saut, le vol, la parole, la surprise ou
le repos. Le réalisateur extrait ces indications du texte français ou
anglais sans le modifier. Les déplacements utilisent des oscillations
déterministes différentes pour la silhouette et les ailes/queues, avec une
petite réaction amortie lors des surprises.

Les scènes de dialogue intègrent une **bouche animée indépendante** des
clignements d'yeux : son ouverture est rythmique, non alignée sur chaque
phonème et non fondée sur une analyse du son. Cela évite de présenter à
tort un véritable `lip-sync`. Les animations continuent d'utiliser les
dessins originaux Pillow, les cadrages FFmpeg, les ambiances et les
transitions sans services tiers ni frais d'API.

Les empreintes d'approbation des illustrations et la version du moteur
sont modifiées : les clips et poses anciens ne peuvent pas être repris
silencieusement après ces changements. Les tests inspectent des images
réellement encodées pour le saut du lapin, la queue du renard en course
et la bouche de la chouette en dialogue.

Le rendu reste une **animation 2D stylisée**, pas de l'animation osseuse
3D ou une synchronisation labiale vérifiée. Écouter et revoir les
résultats avant toute publication.

### Pattes articulées indépendantes (renard, lapin, chat)

Les mammifères originaux en mode `cartoon` possèdent maintenant **deux
calques de pattes indépendants** au lieu de pieds peints dans le torse.
Le rendu FFmpeg applique une trajectoire propre à chaque patte : les
appuis gauche/droite s'alternent pendant la marche et la course ; les
pattes se regroupent pendant un saut. Les scènes de repos limitent
fortement le déplacement des pieds.

Les pattes, les yeux, la bouche, la queue et le corps restent des
illustrations locales originales dessinées avec Pillow et animées via
FFmpeg. Les décors, transitions, météo, voix et SRT/VTT sont inchangés.
Les empreintes d'approbation et le cache de clips évoluent afin que les
anciennes poses ne soient pas utilisées pour une nouvelle animation.

Ces trajectoires sont encore de la **cinématique 2D procédurale**, pas
de la capture de mouvements, des articulations 3D, un IK réaliste ou
une simulation physique du sol. Contrôler le MP4 avant publication.

### Interactions d'objets guidées par le scénario (illustrations originales)

Lorsque **le scénario mentionne explicitement** un objet pris en charge
(*pomme*, *fleur*, *livre* ou *pierre*) et une action pertinente, les scènes
`cartoon` de la chouette, du renard, du lapin et du chat peuvent maintenant
faire apparaître l'objet dans le décor. Trois interactions sont possibles :
**inspection** (objet animé légèrement sur place), **ramassage** (geste de
patte/aile et déplacement de l'objet vers le personnage) et **obstacle**
(pierre restant au sol lorsque le personnage saute).

L'analyse s'effectue uniquement dans le texte narratif original, avec
un vocabulaire français/anglais limité. Elle n'invente pas d'objets absents
du récit ; une simple mention sans action ne déclenche pas de mise en scène.
Tous les PNG sont dessinés localement par Pillow, puis intégrés à la
vidéo réelle par des calques FFmpeg. Les poses, décors, météo, voix,
sous-titres et fondus restent compatibles. Les hash d'approbation et le
cache MP4 changent avec cette révision.

**Limites :** il s'agit de gestes stylisés en 2D, pas de saisie réaliste
à cinématique inverse ni de suivi du regard. Les objets ne sont pas
persistants entre plusieurs scènes ; la détection de mots-clés peut
manquer certains synonymes ou gestes. Toute publication requiert
une vérification visuelle et éditoriale.

### Continuité des objets d'une scène à l'autre

Les personnages originaux `cartoon` conservent désormais visuellement
une **pomme, une fleur ou un livre** ramassé dans une scène antérieure.
Le moteur parcourt les scènes **dans l'ordre du scénario original**, en
mémorisant au plus un objet tenu. Cet objet apparaît près de la patte/aile
pendant les scènes suivantes, y compris lorsque la narration ne répète pas
son nom. Une **nouvelle prise remplace l'ancien objet** ; une phrase disant
explicitement que l'objet est posé, abandonné ou consommé l'efface à partir
de la scène correspondante. Si le personnage examine un autre objet, celui-ci
occupe momentanément le premier plan sans supprimer l'inventaire.

La continuité est calculée **uniquement à partir du texte**, sans API,
sans modification de la narration et sans enregistrer d'état caché entre
les exécutions. Les empreintes d'approbation des images tiennent compte de
l'objet porté : un changement de ramassage dans une scène précédente rend
les visuels suivants obsolètes et impose une nouvelle approbation.
Le rapport `render-report.json` expose `propContinuity`, notamment
`carriedScenes`, `carriedByScene` et `timelineShiftMs=0`.

**Limites :** un seul objet suivi, uniquement les mots-clés et verbes
pris en charge, sans permanence des personnages, physique réaliste, suivi
des regards ou planification multi-objets. La détection d'un dépôt exige
un verbe pertinent et le nom explicite de l'objet. L'effet est une
animation 2D stylisée, soumise à relecture avant publication.

### Plusieurs actions dans un seul plan animé

Lorsqu'une seule scène `cartoon` contient **plusieurs gestes distincts et
explicitement écrits**, séparés par de la ponctuation ou « puis » / « then »,
les personnages originaux peuvent maintenant enchaîner des poses au cours
du même MP4. Par exemple : « Le renard marche, puis saute, puis parle ».
Les trajectoires du corps, des pattes et des ailes/queues évoluent selon
l'action. Un raccord interpolé de 240 ms atténue le saut de pose, tandis
que la bouche s'active pendant le segment de parole.

Le nombre de phases est volontairement plafonné à **trois** par scène.
Une scène trop courte, une action unique ou un texte non explicite conserve
l'ancien mouvement. Les frontières de phases sont estimées à partir de
la longueur relative des propositions : **il ne s'agit pas d'un alignement
sur le son**, d'ASR ou de synchronisation mot par mot. Le rapport de
rendu inclut `actionTimeline` et les phases temporelles observables.
Le scénario, la piste audio, les SRT/VTT, les transitions et les autorisations
de publication restent inchangés.

Tous les gestes sont produits localement à partir de poses 2D originales
et d'expressions FFmpeg à vocabulaire contrôlé. Cela reste une mise en
scène procédurale, **sans IK, physique ni lip-sync réaliste**.

### Regard dirigé vers les objets du récit

Dans les scènes `cartoon` du renard, du lapin, du chat et de la chouette,
les pupilles sont maintenant positionnées en fonction d'un objet
**explicitement observé, ramassé, transporté ou franchi** dans le scénario.
Les personnages dirigent le regard vers la droite lorsqu'un objet apparaît
dans le décor, ou légèrement vers le bas et la droite lorsqu'ils en portent
un depuis une scène précédente. Sans interaction explicite, la pose
initiale des yeux est conservée ; les clignements et expressions restent
compatibles.

Les poses sont dessinées localement avec Pillow et sont intégrées aux
illustrations approuvées et aux MP4. Le rapport `render-report.json`
contient un `objectGaze` par scène pour relecture. Le moteur et les
empreintes d'art évoluent pour empêcher la réutilisation d'anciens visuels
qui ne respectent plus la direction des yeux.

**Limite importante :** il s'agit d'une **orientation statique du regard
par scène**, et non d'un mouvement oculaire continu, d'un suivi 3D de
l'objet ou d'une compréhension visuelle réelle du décor. Le visage reste
une illustration 2D stylisée.

### Synchronisation des gestes sur les débuts des phrases synthétisées

En mode `caption_timing=audio`, le moteur ne se contente plus d'estimer
tous les changements de geste d'après la longueur du texte. Lorsqu'une
**phrase audio synthétisée distincte** correspond clairement à un geste
(« marche », puis « saute », puis « parle »), le mouvement démarre
désormais à l'horodatage mesuré dans le PCM de cette phrase.

Le système reste conservateur : si plusieurs actions se trouvent dans
une seule phrase audio, si les repères ne sont pas valides ou si les
durées des phases sont trop courtes, il conserve l'ancien placement des
gestes basé sur le texte. Aucun mot n'est supposé avoir été aligné par
ASR ou par reconnaissance phonétique.

Le rapport `render-report.json` indique, dans `actionTimeline.scenes`,
les intervalles des actions et `audioAnchored` pour distinguer les
débuts **mesurés** des débuts **estimés**. Le cache vidéo inclut les repères
de sous-titres audio pour éviter de réutiliser des gestes synchronisés
sur un ancien enregistrement.

Les scènes `cartoon` de la chouette, du renard, du lapin et du chat
sont concernées. Les voix, SRT/VTT, ambiances, transitions, durées et
restrictions de publication restent inchangés. Pour activer ce mode
sur Android, sélectionner `Caption timing: audio` et une voix de
synthèse disponible.

### Regard progressif et animation de bouche sensible à la voix

En `cartoon`, les personnages originaux (chouette, renard, lapin et
chat) passent maintenant **progressivement** du regard neutre au regard
dirigé vers un objet observé ou tenu. Les deux poses originales sont
superposées avec un fondu alpha de 420 ms après le début de la scène.
Les clignements restent prioritaires ; les personnages sans objet
conservent le regard neutre. La pose utilisée dans l'illustration
approuvée reste la pose finale du mouvement.

Quand une voix WAV mono PCM 16 bits accompagne la vidéo, le moteur
analyse localement son énergie par fenêtres de **80 ms**. Dans les
scènes dont le scénario indique explicitement que le personnage parle,
les gestes de bouche se ferment désormais pendant les silences et ne
s'ouvrent qu'aux instants où la piste vocale présente une activité.
La voix et les sous-titres restent inchangés : seule l'animation
réagit à l'audio existant. Les pistes audio non prises en charge
et les vidéos sans voix conservent l'ancienne animation rythmique.

Le rapport `render-report.json` inclut `speechMouth` et ses
statistiques d'analyse. Le cache MP4 prend en compte les intervalles
audio détectés ; les empreintes des illustrations ont changé avec le
nouveau rendu du regard.

**Limites :** les yeux effectuent un déplacement 2D interpolé, pas un
suivi oculaire 3D. Les mouvements de bouche sont déclenchés par
l'énergie sonore ; ce n'est ni du lip-sync aux phonèmes ni une analyse
de l'identité du locuteur. Une voix off ne devient pas automatiquement
un personnage parlant : le scénario doit indiquer la parole.

### Contrôle qualité du mouvement sur les vidéos réellement encodées

Le contrôle visuel de la prévisualisation YouTube ne se limite plus à
une image par scène échantillonnée. Il extrait **deux images à des
instants différents dans le MP4 final**, puis mesure leur différence
réelle en niveaux de gris à petite résolution. Le rapport
`review/visual-review.json` documente désormais, pour chaque scène
examinée, la différence moyenne de luminance, la proportion de pixels
ayant changé et l'éventuel manque de mouvement.

Lorsqu'un plan déclare explicitement utiliser le rig animé original
de la chouette, du renard, du lapin ou du chat, **deux images
pratiquement identiques signalent un rendu figé**, et le contrôle
qualité bloque sa validation technique. Les scènes documentaires
volontairement statiques sont exemptées de ce blocage. Les cadres
presque noirs restent signalés ; si la majorité des scènes
échantillonnées est presque entièrement noire, le contrôle échoue.

Le rapport global `qa-summary.json` inclut
`visualMotionPairs` et `frozenAnimatedScenes`, refuse un rapport
visuel incomplet et conserve toujours
`humanEditorialReviewRequired=true` et
`publicationApproved=false`. Les planches JPEG existantes sont
maintenues et utilisables depuis un smartphone Android.

**Limites :** au plus 24 scènes, échantillonnées à deux instants
chacune ; ce n'est ni un contrôle de chaque image, ni un jugement
artistique, un détecteur d'erreur d'animation 3D ou une autorisation
de publier. Des poses très proches peuvent être prises pour un gel ;
une vidéo mobile peut comporter d'autres défauts entre les instants
vérifiés. Une relecture humaine reste obligatoire.

### Précontrôle éditorial automatique du scénario

`One-click YouTube preview` exécute désormais une **analyse locale du
texte original**, sans service payant ni modification silencieuse du
scénario. Elle signale les narrations exactement répétées (même si
elles ne sont pas consécutives), les scènes voisines dont les mots de
contenu sont presque identiques, et les plans dont la densité de mots
semble trop lente ou trop rapide au regard de leur durée.

Le fichier **`story-preflight.json`**, inclus dans l'artefact Android,
contient les numéros de scènes concernées, les indicateurs et une
empreinte du plan réellement analysé. Le rapport
`qa-summary.json` reprend les principaux décomptes et distingue
`technicalPreviewReady` de `editorialRevisionRecommended`.

Les répétitions systématiques déclenchent un signal
`needs-editorial-revision`, **pas un refus de produire une
prévisualisation** : une répétition peut être volontaire et seul
l'auteur peut juger la pertinence narrative. Le système ne prétend
pas détecter toutes les incohérences d'intrigue, vérifier les faits,
mesurer le plaisir du spectateur ni autoriser la publication.

Exécution locale facultative :
`python -m automate_ytb.story_preflight --plan build/scene-plan.json --report story-preflight.json`.

### Voix neuronale par défaut — Kokoro

Le workflow Android `One-click YouTube preview` sélectionne
désormais **Kokoro** par défaut (voix française `ff_siwis` ou anglaise
`af_heart`), en remplacement de la voix eSpeak plus mécanique.
La voix de synthèse est produite sur GitHub Actions, sans API payante,
avec débit `natural` de 0,94x par défaut. Deux autres styles sont
proposés : `gentle` (0,88x) et `lively` (1,04x).

En mode `caption_timing=audio`, les pauses entre phrases suivent
modérément leur ponctuation : courtes pour une virgule, plus longues
pour un point ou des points de suspension. Elles sont réellement
insérées dans le PCM et intégrées aux horodatages SRT/VTT. Le WAV
complet reste disponible, ainsi qu'un nouveau `voice-sample.mp3`
de 12 secondes pour écouter la voix sur Android.

Kokoro doit télécharger et initialiser un modèle local sur le runner,
ce qui peut rallonger fortement la première exécution ; `espeak` ou
`none` restent des choix manuels. Le français dispose d'une
**seule voix Kokoro dédiée** dans le catalogue officiel ; le débit
ne change pas sa personnalité et ne crée pas une voix masculine.
Ces optimisations ne garantissent pas la qualité esthétique ni la
prononciation. Voir [crédits et licences](docs/VOICE_CREDITS.md).

### V2 — fluidité cinématique des plans animés

Les plans originaux de la chouette, du renard, du lapin et du chat disposent
désormais d'un mouvement caméra à accélération et décélération douces
(**smoothstep**), avec une vitesse nulle au début et à la fin de chaque plan.
Le mouvement alterne de sens entre les scènes successives pour limiter
l'effet mécanique. Il reste borné par les cadrages autorisés et ne change ni
la durée, ni les voix, ni les sous-titres ; le plan large conserve sa vue fixe.
Tous les calculs sont intégrés au vrai rendu FFmpeg, et les anciens clips
animés ne sont pas réutilisés.

Cela améliore la **fluidité de cadrage**, mais ne remplace pas une caméra
3D ou un système de parallaxe complet. Les personnages et décors restent
des illustrations 2D originales.

### V2 — profondeur visuelle et premier plan animé

Les scènes `cartoon` originales disposent désormais d'un **premier plan
translucide distinct** du personnage et de son décor. Selon le lieu,
il dessine localement des feuilles, graminées, roseaux ou petits
éléments végétaux, avec un lent mouvement autonome.
Le calque est ajouté après les personnages et la météo puis avant
le cadrage caméra : un effet de profondeur **2,5D stylisé** sans
déplacer la narration, les sous-titres ou le montage.

Les silhouettes restent sur les bords pour préserver la lisibilité des
personnages. Les images approuvées incluent les mêmes assets, et les
empreintes de rendus changent pour empêcher le réemploi des anciennes
vidéos. Il ne s'agit pas de géométrie 3D réelle.

### V2 — éclairage d'ambiance par calque

Les personnages originaux disposent maintenant d'une **lumière atmosphérique
indépendante**, adaptée aux scènes de jour, de nuit et aux temps couverts.
Les villages nocturnes reçoivent de subtils halos chaleureux, tandis que
les scènes de jour utilisent un éclairage solaire diffus. Les couches
transparentes sont composées dans le poster approuvé et dans le véritable
MP4, avant le cadrage caméra.

Ces halos sont des illustrations 2D floutées, non des lumières 3D physiques,
et leur faible opacité vise à préserver la lisibilité des personnages.

### V2 — mouvement organique et ressources d'animation

Les déplacements des personnages originalement dessinés utilisent maintenant de légères harmoniques secondaires : respiration non parfaitement cyclique et suivi des ailes et queues avec deux fréquences déterministes. Les poses restent des illustrations 2D, pas de l'IK, du mocap ou des squelettes 3D ; la voix et la durée des scènes ne changent pas.

**Audit ciblé de star-list :** Sakugabooru (références de timing uniquement, aucun extrait réutilisé), SHOT.CAFE (éclairage et cadrage, inspiration uniquement), PoseMy.Art (études de pose avec droits d'export à examiner) sont pertinents immédiatement. PINOC/Viggle, Blender, Three.js et Scenario Labs 3D peuvent ouvrir une future filière de modèles/mouvements, **mais aucune source n'est installée ou importée automatiquement** sans vérification de licence, format, budget GPU et compatibilité FFmpeg. Cette évolution privilégie les améliorations testables et gratuites sur le moteur existant.

### V2 : sauts avec anticipation et réception

Les sauts d'animaux dessinés disposent désormais d'une courte phase d'accroupissement, d'une ascension interpolée, d'une descente et d'un amortissement au sol. Les deux pieds suivent le même temps de vol. Ces changements restent entièrement procéduraux, gratuits et déterministes, et ne modifient pas la narration ni les fichiers audio. La création d'un véritable rig articulé et de rotations de membres indépendantes constitue encore une étape distincte.

### V2 — contact au sol et profondeur des mouvements

Les quatre animaux originaux utilisent désormais une **ombre douce au sol** sous leurs calques corporels. Elle suit la position horizontale de l'animal sans monter avec lui lors des sauts : la séparation entre ombre et personnage rend la hauteur de saut ou de vol plus lisible. L'ombre est générée localement avec Pillow, floutée et atténuée suivant la météo ; elle figure aussi sur l'image fixe d'approbation.

La composition préserve la narration, les sous-titres, le montage et les images originales. Il s'agit d'un repère spatial 2D stylisé, pas de simulation physique, de ray tracing ou d'un rig squelettique.

### V2 — marche et course avec appui au sol

La marche et la course emploient maintenant deux phases distinctes pour chaque patte : une phase d'appui au sol sans soulèvement artificiel, puis une phase de retour avec une levée adoucie (vitesse verticale nulle au début et à la fin). Les pattes gauche et droite sont déphasées d'un demi-cycle. Ce mécanisme s'applique aux personnages 2D originaux sans service externe. Les sauts conservent leur animation d'anticipation et de réception.

### V2 — expressions naturelles et détails des personnages

Les animaux originaux `cartoon` (renard, lapin, chat, chouette) reçoivent
désormais des touches de finition translucides déterministes : accents de
pelage, joues, reflets du visage et petites plumes. Les effets sont appliqués
aux poses ouvertes/fermées, sans remplacer les yeux, la bouche, le
sous-titrage, les images approuvées ou les assets de scène.

Les clignements ne se répètent plus toutes les quatre secondes à
l'identique : leur intervalle et leur décalage dépendent de l'action et de
l'index de scène. La surprise comporte deux clignements rapprochés, tandis
que le repos est plus lent. Ces gestes restent de l'animation 2D :
aucun tracking oculaire réel, simulation capillaire ni mocap n'est revendiqué.

### V2 : articulations solidaires et détails faciaux préservés

Les ailes de la chouette et les queues du renard, du lapin et du chat
suivent désormais les coordonnées mobiles du torse, même pendant les
sauts, la course et les transitions d'action. Des rotations indépendantes
et limitées sont appliquées aux ailes, à la queue et aux pattes dans des
cadres transparents élargis afin de ne pas rogner les silhouettes. Les
détails de pelage, de plumage et les clignements expressifs de la version
précédente sont conservés.

Il s'agit de **sprites articulés en 2D**, et non de capture de mouvement,
de cinématique inverse ou de modèles 3D. L'ensemble fonctionne hors ligne
avec Pillow et FFmpeg, y compris via les workflows GitHub sur Android.
Les tests comprennent l'encodage et le décodage complet de véritables MP4
illustrant un renard en course et une chouette en vol.

### V2 — oreilles articulées, émotions réactives

Les oreilles des renards, lapins et chats sont extraites de l'illustration du
torse en **deux sprites originaux autonomes**. Leur géométrie et leurs couleurs
restent celles du personnage de référence. Les oreilles gauche et droite
pivotent de manière symétrique selon l'action : repos calme, marche, course,
saut ou brève réaction de surprise dont l'amplitude s'estompe. La tête et les
traits du visage restent préservés ; il s'agit d'articulations de sprites 2D,
pas de simulation 3D ni d'animation osseuse.

La prévisualisation approuvée recombine les mêmes calques, et les empreintes
des rendus sont renouvelées pour éviter la réutilisation des anciennes scènes.
Les essais gratuits vérifient également le fichier MP4 H.264 complet.

### V2 — rendu illustré plus volumétrique et contrôle visuel

Le moteur original produit maintenant des **matériaux 2D ombrés** pour les
corps, ailes, oreilles, pattes et queues : dégradés directionnels, zones
d'ombre douce, léger reflet de contour et diffuseur de lumière elliptique.
Les modifications sont écrêtées à la silhouette transparente exacte du sprite,
afin de ne pas créer de bord opaque ou de scintillement entre les expressions.
Les accents de visage (yeux, plumage et petites mèches de fourrure) restent
dessinés au-dessus du traitement de matière.

Les décors reçoivent un **halo solaire ou lunaire peint**, quelques rayons
diffus à la lumière du jour et une brume de profondeur entre montagnes et
arbres. Tout est déterministe, local, gratuit et original ; il ne s'agit
pas de ray tracing, de textures PBR ou de modèles 3D. Le rendu amélioré
s'applique autant aux posters validés qu'aux clips FFmpeg, et un nouveau
numéro de version force le rafraîchissement des anciens médias en cache.

**Contrôle graphique réel, sans PC :** le workflow
[Premium visual gallery](.github/workflows/visual-gallery.yml) produit
automatiquement après une modification visuelle fusionnée, ou sur exécution
manuelle, une planche PNG 2560 × 1440 de quatre véritables posters
(renard/forêt, lapin/prairie, chat/village de nuit, chouette/rivière).
Dans l'onglet *Actions* de GitHub, ouvrir le dernier run
*Premium visual gallery*, puis l'artefact `original-premium-gallery`.
Une critique humaine du résultat reste indispensable : ces tests valident
la génération, pas un niveau visuel AAA.

### V2 — rendu haute qualité des personnages

Les formes originales des quatre animaux (chouette, renard, lapin, chat)
sont maintenant **peintes à 2× leur résolution native**, puis
reconstruites par filtre Lanczos. Cette opération antialiase réellement
les courbes, diagonales, ailes, oreilles, yeux, pattes et détails fins :
ce n'est pas un agrandissement du PNG déjà pixelisé, ni un simple filtre
de flou. La finition de volume/lumière et les accents de visage
s'appliquent ensuite au sprite final, comme auparavant.

Le procédé reste **entièrement local, déterministe, sans GPU payant**.
Les vidéos et illustrations gardent les mêmes coordonnées, durées,
droits et sous-titres. Cette amélioration de rasterisation ne transforme
pas le moteur 2D en animation 3D ou en cinéma photoréaliste.

### V2 — biomes vivants et mouvement à plusieurs profondeurs

Les quatre décors originaux (forêt, rivière, prairie, village) ne sont
plus entièrement figés autour des personnages. Deux calques transparents
dessinés localement à **2× puis reconstruits avec Lanczos** introduisent
un mouvement lent et différencié :

- **Lointain** : nuages délicats, silhouettes d'oiseaux quand la météo
  le permet, quelques petites étoiles les nuits sombres.
- **Proximité** : feuillages flottants en forêt, papillons en prairie,
  reflets et libellules près des rivières, poussière ou lucioles au village.

Chaque plan se déplace à une vitesse propre dans le montage FFmpeg, avec
un mouvement plus marqué en cas de vent. Les éléments restent à droite
de la composition, à distance du visage des personnages et de la zone des
sous-titres. Les images de validation incluent les mêmes dessins que les
vidéos, et les anciennes images/vidéos en cache sont invalidées.

Ces détails sont de **l'ambiance originale et non une affirmation sur
les faits racontés**. Aucun asset externe, service payant ou GPU n'est requis.
Le procédé crée du mouvement 2,5D, pas des scènes 3D physiques.

### V2 — caméra réactive aux mouvements réels

Outre les travellings déjà interpolés, les scènes originales profitent
désormais d'un **suivi très léger de l'action** : les plans moyens et serrés
accompagnent le balancement horizontal d'une course et la montée / descente
d'un saut. Ce suivi utilise les mêmes cycles temporels fiables que les
animations de personnages, reste à l'intérieur des marges de cadrage, et
s'efface progressivement à chaque frontière de scène pour éviter les à-coups.

Les plans larges ne changent pas, afin de conserver une vue lisible des
paysages. Le rendu demeure une caméra virtuelle 2D/2,5D et non un suivi de
mouvement par vision artificielle. Aucun modèle externe, abonnement ou GPU
n'est nécessaire.

### Profondeur de champ cinématique de la V2

Les nouveaux plans moyens, rapprochés, macro et épaules appliquent une **mise au point sélective** : le décor et les détails atmosphériques lointains deviennent doucement flous tandis que les animaux, accessoires et éléments proches restent nets. Le plan large conserve exactement ses images antérieures. Le flou est calculé **une seule fois par image de décor** en local, et non à chaque image vidéo ; aucune API ou ressource externe n'est utilisée. L'image approuvée correspond à la vidéo. Voir [la table des focales et les limites](docs/DEPTH_OF_FIELD.md).

### V2 — inertie des articulations à la réception

Après la phase de saut, les oreilles, les ailes, les pattes et les queues
réagissent brièvement au contact avec le sol : une oscillation amortie démarre
au temps de réception déjà défini par la chorégraphie (1,39 s sur un cycle de
1,75 s), puis s'éteint. L'effet est léger, déterministe, sans nouveau service
ni ressource téléchargée, et fonctionne dans les véritables rendus FFmpeg
des animaux originaux. La narration, la durée des scènes et le son restent
inchangés. Il s'agit de *follow-through* dessiné en 2D, non d'une simulation
biomécanique ou d'une animation 3D.

### V2 — scènes originales avec deux animaux

Lorsque la narration fait explicitement intervenir ensemble **deux espèces**
parmi le renard, le lapin et le chat, le moteur peut afficher un deuxième
personnage original, plus petit, dans la partie droite de l'image. Son
silhouette complète combine la tête, les oreilles, les pattes et la queue
existantes, avec un très léger mouvement de respiration. Le personnage
principal conserve toute sa chorégraphie, sa bouche et ses accessoires.

La sélection reste prudente : une simple mention isolée d'un autre animal
ne suffit pas à inventer une rencontre ; un maximum d'un compagnon est
ajouté. Cette première version ne fait pas encore parler ni marcher le
second personnage, et n'étend pas le système aux scènes où la chouette est
l'animatrice principale. Les images approuvées et les vrais MP4 utilisent
le même nouveau personnage, sans service payant ni asset externe.


### Démonstration animée V2 — premier véritable MP4 des quatre animaux

Le nouveau workflow **[First animated V2 showcase (free)](.github/workflows/animation-showcase.yml)**
crée automatiquement une courte vidéo 720p H.264 avec le moteur de personnages
du projet, et non un diaporama de posters. Il présente un renard qui saute,
un lapin qui court, un chat qui parle et une chouette qui vole dans les biomes
correspondants. Musique instrumentale locale originale, sous-titres français
intégrés et contrôle technique de décodage sont inclus.

Sur Android : Actions → *First animated V2 showcase (free)* →
*Run workflow* → artefact `automate-ytb-v2-animated-first-video` →
`showcase.mp4`. Fonctionne sans GPU, téléchargement de modèle, API payante
ou publication YouTube. Il s'agit d'une **bande de démonstration d'environ 17 s
sans voix parlée**, non d'un épisode narratif final : le style est procédural 2D.

## Nouveau moteur : infographies scientifiques animées (V2)

Le mode **science** cible les vidéos éducatives avec style spatial/planétaire,
schémas animés, lumière sur la sphère et panneaux explicatifs. Depuis Android :
**Actions → One-click YouTube preview → style = science**, résolution **1080p**
et voix **Kokoro**. Le montage se déroule à **30 images/seconde** en science,
avec les contrôles de droits, d'audio et de sous-titres existants. Les images
sont **originales et schématiques**, sans ressources copiées depuis la vidéo
de référence. La fidélité géographique et l'exactitude scientifique ne sont
pas garanties. Voir [benchmark et écarts](docs/SCIENCE_REFERENCE_TARGET.md).
