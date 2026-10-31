# Mode scientifique animé (expérimental, gratuit)

Ce mode utilise des illustrations **originales**, produites localement par Pillow et assemblées en vidéo H.264 par FFmpeg. Il crée des plans réellement animés à **30 images/seconde**, avec les mêmes contrôles d’intégrité des ressources, de voix, d’audio et de sous-titres que le moteur courant.

## Périmètre réel

- **Sujets pris en charge :** phénomènes liés à la Terre, à ses océans et à l’atmosphère, ainsi que les **arcs-en-ciel en format Shorts 9:16**, évoqués explicitement dans le **titre**. L’illustration de la sphère est schématique ; ni une carte exacte ni une simulation physique.
- **Plans disponibles :** rotation/orbite schématique, circulation atmosphérique, vagues océaniques, éclairage jour/nuit ; cinq schémas spécifiques d'optique pour la formation d'arcs-en-ciel en format vertical. Ils sont sélectionnés à partir des phrases françaises ou anglaises du script.
- **Formats :** sortie encodée en 720p ou 1080p, toujours en 30 fps dans ce mode. Les scènes animées en 1080p sont désormais dessinées **directement à 1920×1080** : ciel, étoiles, globe calculé à 612 px, contours, annotations et typographie vectorielle. La miniature d'approbation statique reste en 1280×720 (ce n'est pas la résolution de la vidéo exportée).
- **Inexactitudes possibles :** chiffres scientifiques, géographie, mouvements astronomiques et contenu du script doivent être revus indépendamment. L’IA ne recherche ni ne vérifie les faits en générant ces images.
- **Licence/coûts :** pas de médias externes importés et pas de modèle graphique payant. Kokoro est facultatif et peut nécessiter un téléchargement lors de la première utilisation. Les quotas GitHub Actions habituels restent applicables.
- **Publication :** aucune mise en ligne automatique ni approbation éditoriale implicite.

## Android — prévisualisation

1. Ouvrir **Actions → One-click YouTube preview → Run workflow** sur GitHub.
2. Choisir **style = science**, un titre explicite sur la Terre ou les océans (ou sur les arcs-en-ciel avec `resolution = shorts`), un script original avec suffisamment de phrases et un personnage de type **Original astronomy graphics**.
3. Sélectionner **1080p** et, pour la qualité d'encodage, **render_profile = high**. Choisir **voice = kokoro** pour la synthèse neuronale si le runner dispose des ressources nécessaires.
4. Lire la vidéo MP4 et écouter le fichier `voice-sample.mp3` de l'artefact, contrôler la lisibilité des chiffres et corriger toute erreur factuelle avant publication.

En ligne de commande, utiliser `python -m automate_ytb.episode --style science --render-profile high --resolution 1080p --voice kokoro --plan scene-plan.json --output out` après avoir généré un plan avec `python -m automate_ytb.scene_plan`.

## Shorts 9:16 (1080×1920 natif)

Le choix **resolution = shorts** dans **Actions → One-click YouTube preview** est réservé au style `science`. Il produit une vidéo originale 1080×1920 à **30 images/seconde** : ce n'est ni le recadrage ni l'agrandissement d'une vidéo 16:9. Le moteur dispose d'une composition verticale indépendante, avec globe ou phénomènes atmosphériques et océaniques adaptés à l'écran mobile. Les titres et **sous-titres visibles phrase par phrase** sont placés dans des zones séparées, pensées pour les principales interfaces de Shorts/TikTok/Reels. Les mêmes séquences temporelles sont utilisées pour le texte incrusté dans la vidéo et le SRT : si `voice = kokoro` ou `espeak` et `caption_timing = audio`, les changements de phrase suivent les débuts de fragments de voix synthétisés. Les temps ne sont pas vérifiés mot par mot ; sans voix ou en mode `estimated`, ils sont calculés proportionnellement au texte. La revue visuelle et l'écoute sur l'application cible restent indispensables.

Le poster d'approbation reste en 1280×720 : sa géométrie diffère donc volontairement du film vertical. Le contrôle final doit porter sur le **MP4 généré**, pas uniquement sur le poster. Les scripts restent originaux, les légendes complètes sont exportées en SRT/VTT, la narration Kokoro est facultative et l'export ne publie rien automatiquement. Les sujets sans moteur explicatif pris en charge sont refusés, y compris les sujets hors Terre/océans/arcs-en-ciel. Les arcs-en-ciel ne sont actuellement rendus qu'en format Shorts 9:16, pas en sortie horizontale.

Pour Android : sélectionner `style = science`, `resolution = shorts`, `render_profile = high` et, si souhaité, `voice = kokoro`. Les vérifications du pipeline et `tests/test_science_shorts.py` contrôlent la taille exacte, le mouvement entre les images, les limitations d'entrée et le vrai codec H.264.

## Optique atmosphérique : vraie production originale d'arcs-en-ciel

Le rendu **natif 9:16** accepte désormais un second sujet scientifique explicitement pris en charge : **« How Do Rainbows Form? »**, ou un titre équivalent contenant « rainbow » / « arc-en-ciel ». Cinq notions sont dessinées directement par Pillow à **1080×1920** : lumière solaire blanche et composantes colorées, première réfraction à l'entrée d'une **goutte sphérique**, réflexion partielle à sa face arrière, seconde réfraction à la sortie, puis arc coloré vu par un observateur. Les raies colorées portent des marqueurs qui se déplacent continûment selon l'horloge du plan à 30 images par seconde ; la composition finale comporte un fond atmosphérique de jour indépendant des cartes océaniques. Le contenu ne prétend pas réaliser un calcul de ray tracing exact ni localiser le « bout » d'un arc-en-ciel.

Le moteur classe les phrases originales selon les notions optiques ; une narration vague ou non reconnue est **refusée explicitement**, plutôt que représentée avec un faux globe terrestre. Les sujets hors Terre/océans/arcs-en-ciel restent également refusés. Les cinq animations d'optique ne sont disponibles que pour `style=science` et `resolution=shorts` ; les versions horizontales non conçues pour ce sujet sont refusées avant la production coûteuse des images ou de la voix. Une véritable vignette d'approbation **16:9** est extraite de l'illustration originale 9:16, sans simuler une prise de vue sur une autre planète. Cela ne change jamais le format de la vidéo finale.

Le workflow `rainbow-science-release-candidate.yml` génère automatiquement un scénario anglais original de cinq scènes, la voix naturelle Kokoro `af_heart`, la musique d'ambiance locale, le SRT/VTT, le MP4 H.264 et les planches d'inspection **directement décodées** du fichier final. Le même contrôle strict de durée PCM (30s avec tolérance de 600ms), les mêmes vérifications visuelles et sonores, la protection des crédits, et l'obligation d'une approbation humaine restent actifs. En cas d'échec, les rapports PCM sont archivés pour diagnostiquer la durée du scénario sans couper la voix ou halluciner des faits. Les nouveaux tests valident les cinq scènes, leur mouvement, la déterminisme, les sous-titres, la taille portrait, la vignette et le refus de sujets non pris en charge.

## Revue visuelle native 9:16 sur Android

Le workflow **One-click YouTube preview** extrait maintenant les planches de contrôle directement du MP4 final en conservant son ratio d’image. Pour une vidéo verticale 1080×1920, chaque échantillon est décodé en **360×640** (format 9:16) et inséré dans un aperçu portrait de **quatre scènes par page**, sans découpage 16:9. Les bandes des titres et les sous-titres restent entièrement visibles pour une vérification sur smartphone. Les vidéos horizontales conservent leurs huit scènes par page et leur rendu habituel. Le rapport `review/visual-review.json` expose l'orientation, les dimensions des images et le nombre de scènes par planche.

Les scènes approuvées avec le rig `original-science-v1` et le style `science` sont aussi soumises à la détection d’animations figées sur **deux images réellement décodées du MP4**. Une animation scientifique complètement immobile déclenche une erreur technique ; les plans documentaires volontairement fixes restent autorisés. L'échantillonnage demeure limité et ne certifie ni la qualité cinématographique ni l'exactitude des faits.

## Intégrité des planches de contrôle

La validation technique finale ne se contente plus d’un rapport JSON affirmant que les captures du MP4 sont correctes. Le générateur de planches enregistre l'empreinte **SHA-256 de chaque JPEG** réellement produit. La consolidation `qa_bundle` exige ensuite que toutes les planches annoncées existent, soient des JPEG décodables en **1120×2030**, aient exactement les empreintes annoncées et présentent une orientation et un nombre de pages cohérents avec les dimensions du MP4. Une capture manquante, déplacée, altérée, tronquée ou substituée empêche la mention `technicalPreviewReady`. Les anciens rapports en schéma v2 restent lisibles, sans revendiquer cette vérification supplémentaire. Ce contrôle ne prouve pas la qualité artistique ni l’absence de zones masquées : l'approbation éditoriale demeure humaine.

## Typographie mobile sans perte de texte

Les titres et les sous-titres incrustés en mode `shorts` sont désormais mis en lignes en tenant compte de leur largeur réelle : le moteur adapte la taille des glyphes dans les limites de lisibilité, répartit aussi les termes techniques trop longs et évite les points de suspension qui supprimaient parfois des mots. Tous les textes des phrases sont contrôlés avant l'encodage des images. Un titre ou un fragment incompatible avec la zone réservée provoque une erreur explicite : il doit être raccourci ou découpé dans le script, sans supprimer silencieusement du contenu. Le SRT exporté conserve son contenu intégral. Les vidéos précédemment mises en cache sont invalidées pour le rendu portrait. Cette sécurité typographique ne remplace pas l'inspection du film sur téléphone.

## Rendu 1080p natif

Le choix `resolution=1080p` alloue un canevas 1920×1080 et calcule directement les images originales à cette résolution avant encodage H.264. Contrairement à l'ancienne version, le rendu n'agrandit plus une image 720p en fin de processus. Il conserve la même composition graphique, avec des épaisseurs de trait, rayons, glyphes et éclairages adaptés. L'option 720p reste inchangée et moins coûteuse en calcul. Les images de présentation/validation sont toujours générées en 720p ; cette différence est volontaire et documentée.

## Continuité et coût de rendu

La rotation schématique de la Terre reste active au-delà de la cinquième seconde d'un plan. Les différentes orientations sont calculées seulement lorsqu'elles sont visibles, puis conservées dans un cache mémoire borné à huit poses. Les scènes d'océan et d'atmosphère ne chargent aucune sphère terrestre inutile. Cela réduit les calculs superflus et évite le gel visuel de l'ancien moteur, sans prétendre reproduire fidèlement la vitesse réelle de rotation de la Terre.

## Courants océaniques multicouches (Shorts 9:16)

Les scènes de mode `ocean` combinent désormais quatre couches de vagues animées avec **trois courants d'eau indépendants**, des particules à traînée lumineuse et deux tourbillons dont l'orientation évolue continûment à **30 images/seconde**. Les lignes de courant et leurs vitesses restent différentes selon la profondeur. Ce sont des graphiques originaux générés localement, et non une carte physique des courants ou une simulation hydrodynamique. Les éléments sont positionnés dans la bande visuelle centrale afin de préserver les titres, les légendes et les contrôles de l’interface mobile. La cache des clips portrait a été invalidée pour que les vidéos précédentes ne masquent pas cette évolution.

Les régressions vérifient des images distinctes d'une frame à l'autre, un rendu reproductible, l’activité des trois courants, l’absence de globe chargé dans le mode océan et les sous-titres inchangés. Une revue éditoriale du MP4 reste nécessaire, en particulier pour les sujets scientifiques spécifiques où ces courants schématiques ne doivent pas être interprétés comme une représentation exacte.

## Rotation continue pour les Shorts (9:16)

Les plans verticaux animés interpolent maintenant les deux orientations calculées les plus proches du globe à chaque image (30 fps). Cela limite les saccades de la carte terrestre visibles auparavant toutes les 0,4 seconde, sans exécuter la coûteuse projection complète de la sphère à chaque nouvelle image. Le cache conserve au maximum six poses, avec des clés distinctes selon l'orientation et la résolution. Cette interpolation visuelle ne constitue pas une simulation physique ; une revue du film exporté demeure indispensable. Le rendu horizontal et les vidéos documentaires NASA restent inchangés.

## Optimisation CPU du globe

Le moteur réutilise maintenant, entre les différentes orientations de la Terre, son atlas original de continents et son halo pré-calculé par résolution. Les calculs dépendant uniquement de la latitude (échantillonnage vertical, nuages et glace polaire) sont effectués une fois par ligne plutôt que pour chaque pixel. Les images rendues conservent leur résolution réelle et les mêmes formules de couleur, sans ajouter de dépendance ni consommer de crédits de génération. Le nombre d’orientations stockées par scène reste borné. Les tests vérifient des couleurs de pixels contre les équations de référence, la stabilité des résultats et l’absence de mutation des ressources mises en cache. Aucun gain chiffré n’est affirmé sans mesure sur un environnement de production.

## Release candidate : statut fondé sur le vrai MP4

L'action **Verify full 9:16 science Shorts release candidate** appelle directement le workflow de production existant comme **workflow réutilisable GitHub Actions**. Une simple demande de déclenchement d'un deuxième workflow ne peut plus être considérée comme une validation réussie. Le statut de release devient **rouge** si la synthèse Kokoro, le rendu H.264 1080×1920 à 30 fps, les sous-titres, l'audio, les planches de contrôle ou la consolidation des rapports échouent. L'artefact `automate-ytb-free-preview` est associé à la **même exécution de release** ; il contient le MP4, l'échantillon vocal, les légendes, les images et les rapports disponibles. Un job de confirmation ne s'exécute qu'après la réussite de la production.

Depuis Android, ouvrir **Actions → Verify full 9:16 science Shorts release candidate → Run workflow**. Si l'exécution est verte, télécharger son artefact et vérifier la **présence effective de `preview.mp4` et `qa-summary.json`**. La configuration de référence vise 30 secondes, Kokoro anglais `af_heart`, musique originale, synchronisation audio des phrases et profil `high`. Le workflow conserve les limites de temps et quotas habituels des runners GitHub ; il ne consomme pas de crédits d'API de génération. La validation technique n'atteste pas la précision scientifique, le naturel subjectif de la voix, l'originalité artistique ni l'autorisation de publier.

## Garde-fou sur les silences de narration — mesure PCM

Pour les vidéos scientifiques natives `shorts` complètes avec Kokoro et sous-titres calculés sur l'audio, la production mesure **la quantité exacte de silence numérique ajoutée en fin de chaque scène** après synthèse. Elle enregistre `narration-pacing.json` dans l'artefact GitHub, même lorsque le contrôle échoue avant l'encodage. Une scène dépassant 1 500 ms de remplissage, ou plus de 20 % de remplissage sur la vidéo sélectionnée, entraîne un échec explicite : le script original doit être étoffé avec des faits vérifiables, ou la durée demandée adaptée. Les autres types de vidéo conservent un diagnostic consultatif afin de préserver la compatibilité.

Ces chiffres proviennent des durées des échantillons PCM, pas d'un calcul de mots par minute. Le contrôle ne coupe pas la voix, n'accélère pas le modèle, ne fabrique pas de texte scientifique et ne remplace pas une écoute humaine. Les pauses naturelles intérieures à une prise ne sont pas classées comme du remplissage. Le rapport indique scène par scène l'audio produit, la durée retenue et le silence ajouté. Une voix techniquement complète n'est pas nécessairement naturelle.

Le premier export complet de 30 secondes comptait environ 44 mots et 13,6 secondes de remplissage silencieux ; la recette de référence utilise désormais cinq phrases originales plus informatives. Sa durée et sa fluidité définitives doivent être validées sur le véritable export Kokoro après intégration.

## Vérifications de sortie

## Durée cible mesurée sur la vraie narration Kokoro

Le moteur vérifie maintenant **deux** critères indépendants avant l'encodage coûteux d'un Short scientifique entièrement narré : la quantité de silence PCM ajoutée à chaque scène et **l'écart entre la durée originale demandée et la durée obtenue après la synthèse Kokoro**. La source de vérité est l'audio PCM assemblé, et non une estimation du nombre de mots. Le rapport `narration-pacing.json` inclut `requestedDurationMs`, `totalSceneDurationMs`, `durationDriftMs` et le seuil maximal de **600 ms** pour les Shorts stricts. Un dépassement empêche que le workflow de publication technique affiche un statut vert, même si l'encodage H.264 serait valide.

L'ancien Short de référence réclamait 30 secondes mais durait **31,555 secondes dans son plan PCM** (31,599 secondes dans le conteneur MP4), soit un dépassement de 1,555 seconde. Il est désormais rejeté avant la création d'un autre MP4. Le scénario exemple a été légèrement raccourci sans supprimer de mécanisme scientifique ; seul un nouveau rendu du vrai moteur peut confirmer sa durée. Le code ne tronque jamais les phrases, ne change pas automatiquement la vitesse Kokoro, et ne fabrique pas d'informations supplémentaires. Les options sont de réécrire le scénario original ou de choisir consciemment une autre durée. Les rendus non stricts continuent de produire un avertissement diagnostique au lieu d'échouer.

## Storyboard narratif en trois étapes et contraste des notions

L'inspection des images **réellement décodées** du Short de référence a montré que les mentions « WARM » et « COOL » étaient pratiquement invisibles : elles utilisaient exactement les mêmes couleurs que les réservoirs qu'elles étaient censées expliquer. Les noms utilisent désormais une encre bleu nuit sur les fonds orange et bleu, avec un contraste calculé supérieur à 7:1 pour chacune des deux cartes, tout en conservant le codage chaud/froid.

Les cinq diagrammes de courants océaniques gagnent un indicateur temporel **cause → mécanisme → conséquence**. Chaque scène propose trois descriptions scientifiques fixes en anglais et en français, pré-écrites pour cette explication et sélectionnées selon le temps réellement écoulé dans la scène. Une barre de progression évolue de manière continue avec les images, à 30 images par seconde, sans masquer les sous-titres ni demander de synthèse vocale additionnelle. Les temps sont normalisés par la durée effective de la scène (qui peut varier légèrement après synthèse Kokoro), et non par une hypothèse de six secondes fixes. Le code ne crée pas de nouvelle allégation factuelle ou de simulation géophysique.

Le bandeau de progression utilise la zone native 1080×1920 entre l'étiquette de sujet et le diagramme, distincte de la zone des sous-titres. Les régressions exigent trois états réellement distincts dans des images produites par Pillow, un mouvement continu de la progression, la conservation des glyphes de sous-titres, des textes lisibles dans les réservoirs colorés, et le rejet d'horloges invalides. Comme précédemment, l'approbation éditoriale reste obligatoire avant toute publication.

## Lisibilité native sur téléphone

Le contrôle de la première vidéo encodée avec les cinq nouveaux schémas a révélé des libellés internes trop petits dans un aperçu mobile, malgré une exportation 1080×1920 correcte. Les textes principaux des schémas ont donc été agrandis (environ 34 à 44 px natifs selon leur rôle), le titre de concept passe de 30 à 36 px, et les sous-titres visent 40 px au lieu de 31 px. Les cas de sous-titres exceptionnellement longs conservent l'adaptation existante sans coupure des mots. La grille conserve les zones sûres, et la mention **« schématique, non à l'échelle »** remplace la formule plus ambiguë « science illustrée ». Les tests vérifient la largeur réelle des glyphes, trois lignes maximum et l'absence de débordement de la zone de sous-titres sur les cinq phrases de référence.

## Storyboards scientifiques originaux et spécifiques à la narration

Pour le sujet **courants océaniques**, le moteur de Shorts reconnaît maintenant cinq notions scientifiques dans le texte original, sans décider à partir d'un simple numéro de plan : **chauffage solaire différentiel**, **vents et courants de surface**, **déviation/gyres liée à l'effet Coriolis**, **plongée des eaux denses**, **redistribution de chaleur**. Chaque notion possède une composition 1080 × 1920 indépendante et des flèches, particules ou chemins recalculés à chaque instant de la scène. Les textes du graphique basculent entre anglais et français lorsque la langue est identifiable.

Le rendu conserve les zones sûres du titre et des sous-titres, les minutages issus de la synthèse audio et l'interdiction d'inventer automatiquement des faits. Les graphiques ne prétendent **ni reconstituer une carte réelle de courants, ni être une simulation du système climatique** : les légendes restent qualitatives et le dessin signale son caractère illustratif. Les sujets pour lesquels les concepts ne peuvent pas être détectés conservent le moteur historique au lieu de recevoir un faux schéma. Aucun téléchargement de texture, modèle ou service payant n'est nécessaire.

La CI couvre la détection du concept, les cinq images différentes, les changements réels de pixels entre images, la reproductibilité, la conservation des zones UI, l'absence de projection planétaire coûteuse dans les nouveaux schémas et la rétrocompatibilité avec un sujet sans correspondance. Une nouvelle exécution du **vrai workflow Kokoro 9:16** est demandée automatiquement lorsque le moteur de scènes scientifiques change. Cette production restera une **prévisualisation technique**, nécessitant une revue scientifique, artistique et sonore avant toute diffusion.

Les régressions `tests/test_science_motion.py` couvrent les quatre modes visuels, les images successives distinctes, l’empreinte des ressources de la narration et un vrai H.264 à 30 fps. La CI doit réussir l'ensemble de la chaîne avant fusion, et une revue humaine doit contrôler le film complet. Des animations multisciences généralisables, une direction artistique native 1080p et l'alignement mot à mot fiable restent des objectifs futurs.
