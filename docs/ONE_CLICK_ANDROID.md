# Une vidéo YouTube depuis Android — sans PC ni appel API payant

La prévisualisation peut conserver un décor de **forêt, rivière, village ou prairie** en fonction du scénario. Voir [Décors originaux guidés par le scénario](STORY_LANDSCAPES.md).

## Lancer un aperçu complet

1. Ouvrir [Actions](https://github.com/dbrckk/Automate-ytb/actions) dans le dépôt.
2. Sélectionner **One-click YouTube preview (free)**, puis **Run workflow**.
3. Renseigner le sujet, un **scénario original**, une description de personnage original, la durée, la langue et le style. Le scénario doit avoir **au moins une phrase par scène** ; par exemple 30 secondes / 6 secondes = 5 phrases.
4. Sélectionner **kokoro** pour une voix neuronale naturelle (français : ff_siwis ; anglais : af_heart), **espeak** pour un brouillon plus léger, ou **none** pour un aperçu silencieux. Kokoro télécharge un modèle local sur GitHub Actions et peut consommer beaucoup de temps de calcul. Aucun service TTS payant n'est appelé.
5. Dans **Soundtrack**, choisir **ambient** pour une musique instrumentale
   originale créée gratuitement dans le workflow, ou **none** pour un rendu
   sans musique. Si une narration est présente, FFmpeg réduit le fond sonore
   pendant les paroles. Le mastering comprend une limitation des pics, mais
   il faut encore écouter le résultat pour juger de la qualité.
6. À la fin du run, télécharger l'artefact **automate-ytb-free-preview** dans la rubrique **Artifacts**. Il contient MP4, narration WAV, sous-titres SRT, trois miniatures, scénario, JSON de scènes et compte rendu.

Ce workflow crée **sans API d'inférence payante des illustrations procédurales de brouillon**, pas des images IA photoréalistes. La chouette originale dispose d'un moteur d'animation 2D. Il produit une narration **eSpeak provisoire** ou, sur demande, une voix **Kokoro neuronale** dont la prononciation doit être écoutée et validée. Le résultat est un **brouillon à revoir**, sans publication automatique.

### Précautions

- Sur un **dépôt GitHub public**, les entrées d'un workflow et les artefacts ne doivent pas être considérés comme privés. Ne pas coller de scénario confidentiel, identifiants ou données personnelles.
- Le lancement nécessite les permissions GitHub pour exécuter des workflows sur le dépôt. Le rendu peut prendre du temps sur des projets comportant beaucoup de scènes.
- Aucune facture d'inférence n'est générée par ce workflow (GitHub Actions peut néanmoins être soumis aux règles de quotas de ton compte).
- Les sujets, affirmations, illustrations, voix et métadonnées doivent être vérifiés avant publication. Ce n'est pas un moteur d'information automatiquement sourcée.
- Le système adapte la durée des scènes à une narration eSpeak trop longue : il **ne tronque pas la voix**. Les sous-titres sont synchronisés **à l'échelle de chaque scène**, pas au mot.
- Limites configurées dans l'action : 30–900 secondes au départ, 3–20 secondes par scène, 150 scènes maximum. Pour dépasser ces seuils, prévoir une orchestration plus avancée avec reprise.

### Génération IA optionnelle

Le module [Hugging Face](HUGGINGFACE_IMAGE_PROVIDER.md) sait demander de véritables images à un fournisseur compatible. Il utilise le **client officiel InferenceClient** et se configure séparément avec :

~~~bash
python -m pip install -e '.[images]'
python -m automate_ytb.image_provider --plan project/scene-plan.json --limit 1
~~~

Par défaut, il affiche le budget estimé **sans envoyer la moindre requête**. La génération réelle nécessite un jeton privé \`HF_TOKEN\`, l'option \`--execute\`, un consentement de droits et un montant estimé suffisamment élevé. Les tarifs réellement facturés ne peuvent pas être garantis par le programme : définir les limites directement chez le fournisseur.

**Le workflow gratuit et le fournisseur IA restent distincts.** Ainsi, une commande Android ne peut pas déclencher une dépense externe par accident.

## Architecture et étapes suivantes

L'Action existante prépare le plan de scènes, notre moteur crée les images de brouillon, eSpeak fabrique une piste PCM dont les segments sont calés sur le planning, FFmpeg produit les clips puis le MP4, et trois miniatures sont exportées.

Les prochaines améliorations qualitatives les plus importantes sont : des gestes guidés par le storyboard, des univers et personnages originaux supplémentaires, la qualité artistique des images, une génération IA à coût contrôlé et une synchronisation mot-à-mot. Kokoro constitue désormais une option de TTS naturel, sans garantir automatiquement une narration professionnelle. Ces fonctions ne sont **pas** promises par le workflow gratuit de cette version.

## Personnage animé : illustration originale améliorée

En style **cartoon**, si la description du personnage contient `owl`, `chouette` ou `hibou`, le système produit maintenant une **chouette originale dessinée** avec lunettes turquoise, foulard doré, expressions, poses et décors variant selon les scènes. Les rendus sont déterministes pour permettre la reprise et la comparaison visuelle.

Ce passage décrit le précédent système d'images fixes. Depuis le rig v1 ci-dessous, la chouette est animée par calques mobiles ; il ne s'agit toujours ni de vidéo générée par IA, ni d'animation 3D. Pour d'autres personnages ou styles, le moteur conserve les cartes graphiques précédentes afin de ne pas représenter un personnage erroné. Les images ne reprennent pas la mascotte d'une chaîne tierce.

Les futurs ajouts devront prévoir un catalogue de personnages originaux, des gestes/expressions contrôlés par le storyboard et une validation de cohérence visuelle entre les scènes.

## Animation 2D de la chouette (rig v1)

Le mode cartoon avec une description contenant owl, chouette ou hibou
ne se limite plus à une illustration fixe. Notre chouette originale est composée
de calques transparents (ailes gauche/droite, corps, clignements)
animés indépendamment grâce à FFmpeg. Les ailes battent,
le corps oscille et les yeux clignent ; l'arrière-plan reste cohérent pendant le
plan. Les variations de décor et de narration sont conservées à chaque scène.

**Réutilisation :** le moteur associe au visuel approuvé l'empreinte
du sujet, du texte, du personnage et du style. Si le contenu est modifié après
la préparation des images, le rendu refuse d'exploiter les anciens médias sans
nouvelle validation. Le cache des clips est également invalidé si l'image,
la durée, le nombre d'images par seconde ou le moteur de rendu change.

L'aperçu reste gratuit sans compte IA, sans image copiée, sans génération distante
ni publication YouTube. **Limites :** l'animation procédurale ne couvre encore
que la chouette ; ce n'est ni de la vidéo générée par IA, ni une animation 3D
complexe ; la voix eSpeak est provisoire. Pour les autres personnages, le
moteur conserve ses propres cartes graphiques au lieu de dessiner une chouette
qui ne correspondrait pas au scénario.

Les tests comparent des images réellement décodées du MP4 à différents
instants : ils vérifient que le personnage bouge tandis que le décor reste
stable. Ils vérifient aussi la reproductibilité des visuels et le refus
des anciennes images si le scénario change.


## Voix neuronale optionnelle (Kokoro)

Le workflow gratuit conserve **espeak** par défaut. Sélectionner **kokoro** dans GitHub Actions active l'installation CPU et le téléchargement du modèle public au premier lancement. Le modèle [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) est décrit sous licence Apache-2.0 ; vérifier les informations relatives aux voix et attributions amont pour la distribution. Les voix permises sont ff_siwis en français, af_heart, af_bella et am_michael en anglais. Le workflow sélectionne automatiquement ff_siwis en français et af_heart en anglais.

Localement, installer les dépendances de voix, puis lancer :

    python -m pip install -e '.[speech]'
    python -m automate_ytb.episode --plan build/scene-plan.json --output build/video --voice kokoro --language fr

Le moteur instancie Kokoro une seule fois par épisode, génère l'audio des scènes, ajoute une respiration entre les fragments et prolonge les scènes trop courtes. Aucune phrase n'est tronquée pour rentrer artificiellement dans six secondes. Les sous-titres restent alignés à la scène et non mot par mot. La génération peut échouer si le téléchargement, la mémoire ou le moteur CPU ne sont pas disponibles. GitHub Actions peut appliquer ses quotas habituels.

Le mode Kokoro ne déclenche ni API TTS payante ni publication YouTube.

## Direction artistique contextuelle (nouveauté)

Les nouvelles scènes analysent **uniquement la narration rédigée par l'utilisateur** pour
identifier des indications visuelles simples et explicites :

- **Météo et lumière :** pluie, orage, nuit, soleil/matin, nuages, vent.
  En l'absence d'une nouvelle indication, l'ambiance est conservée depuis
  la scène précédente, afin d'éviter les sauts arbitraires.
- **Actions :** vol (ailes plus amples et corps plus mobile), marche,
  parole, surprise ou repos.
- **Expressions :** curiosité, sourire, inquiétude et étonnement.
- **Cadrage :** le storyboard prévoit plusieurs plans (large, moyen,
  rapproché, macro et contre-plongée), avec de légères variations de zoom.

Ces indications sont enregistrées dans le JSON de production sous
\`scenes[*].direction\`, avec quatre propriétés validées :
\`weather\`, \`action\`, \`emotion\`, \`shot\`.
Le rendu FFmpeg ajoute des couches de pluie, vent ou nuages animées lorsque
le texte le justifie. Les illustrations et les mouvements restent **originaux,
locaux et gratuits** dans le workflow standard.

### Transparence et limites

Le système repose sur un dictionnaire de mots clés français/anglais,
**pas sur une compréhension sémantique complète**. Il peut se tromper si
plusieurs événements météorologiques opposés sont décrits dans une seule
phrase, ou avec une négation. Corriger alors la propriété \`direction\`
dans le plan avant génération de l'image. Toute modification des indications
après validation d'un visuel doit déclencher une nouvelle approbation
au lieu de réutiliser automatiquement une image devenue incohérente.

Le contenu raconté et les horodatages ne sont jamais réécrits par cette
étape. Les anciens plans sans indications \`direction\` continuent à utiliser
le rendu historique. Kokoro reste une voix optionnelle et la synchronisation
des sous-titres demeure au niveau des scènes, pas des mots.

## Bande sonore originale et sous-titres plus lisibles

La nouvelle option **ambient** fabrique une musique d'ambiance minimaliste
par synthèse locale à partir de sons purs, sans télécharger d'extraits tiers,
sans bibliothèque musicale et sans API payante. Le thème tonal varie suivant
les indications déjà présentes dans le storyboard (jour, nuit, pluie et
émotions simples). Les raccords entre scènes sont adoucis pour éviter les
clics. Cette bande sonore est une création technique **provisoire**, pas une
musique de qualité commerciale garantie.

Lorsque **espeak** ou **kokoro** est activé, le moteur mélange la narration
et la musique en atténuant automatiquement cette dernière pendant la parole ;
un limiteur réduit le risque de saturation. Le dossier exporté contient
dorénavant aussi le fichier WAV original de la bande sonore.

Les sous-titres SRT sont segmentés en **petites phrases de deux lignes
environ**, avec des durées estimées proportionnellement au texte de chaque
scène. Cela améliore la lisibilité mais **ne correspond pas à un alignement
phonétique réel au mot**. Vérifier les timecodes en relisant la vidéo.

Le réglage de base de l'outil local reste **sans musique** pour préserver le
comportement des projets existants. L'action Android propose **ambient** par
défaut et permet de le désactiver. La génération sonore n'utilise aucune
donnée ni voix de tiers non autorisée.

## Contrôle qualité automatique du MP4

Le workflow Android vérifie maintenant, avant de signaler une exécution réussie :

- la durée, la résolution H.264 et le décodage d'images au début et à la fin du MP4 ;
- les pistes AAC réellement présentes : voix eSpeak/Kokoro et/ou musique d'ambiance ;
- la concordance entre le mode audio demandé sur Android et le mixage effectué ;
- le scénario, l'empreinte SHA-256 du MP4 et l'intégrité des rapports ;
- la continuité chronologique des sous-titres jusqu'à la fin de l'épisode ;
- l'absence d'approbation automatique de publication YouTube.

Le fichier quality-report.json est conservé avec le MP4. Un échec signale
exactement ce qui manque ou ne correspond pas. Ce contrôle ne garantit ni
la qualité artistique, ni la véracité des faits, ni le droit de publication.

Le choix soundtrack est correctement transmis depuis Android : ambient
ajoute la musique originale sous la narration ; none désactive cette piste.


## Contrôle technique avant publication

Le workflow gratuit génère aussi deux nouveaux livrables :
- **draft-captions.vtt** : sous-titres WebVTT réutilisables depuis YouTube Studio ;
- **quality-report.json** : vérification FFprobe de la durée, de la résolution,
  des flux vidéo/audio, de la présence de la narration et des bornes des sous-titres.

Le rapport inclut le pic numérique de la piste audio pour identifier un volume
anormalement faible ou proche de la saturation. Il ne mesure pas les LUFS et
ne vérifie pas par écoute la qualité du français. Les sous-titres restent
synchronisés par scène (pas au mot). Le rapport ne valide ni les faits, ni les
droits, ni l'autorisation de publier.


## Rapports qualité séparés (mise à jour)

Le workflow conserve maintenant **trois rapports distincts** dans l'artefact :

- `quality-report.json` : contrôle structurel du MP4, du scénario, des pistes audio demandées et du nombre de sous-titres.
- `media-report.json` : deuxième vérification de la durée, des flux audio/vidéo, du volume maximal et des sous-titres.
- `qa-summary.json` : synthèse des deux contrôles, empreintes SHA-256 du MP4 et des fichiers SRT/VTT, et décision de validité **technique** du brouillon.

Le workflow échoue si une vérification critique ne passe pas. Ces rapports ne
certifient ni la véracité des faits, ni les licences, ni la qualité artistique, et
n'autorisent aucune mise en ligne automatiquement. Les deux fichiers d'origine
ne s'écrasent plus mutuellement.


## Contrôle audio et mastering automatique

Les vidéos produites avec une voix (eSpeak ou Kokoro) reçoivent une
**normalisation EBU R128** visant environ **–16 LUFS** et un plafond
de pic réel à **–1,5 dBTP**. Si la vidéo ne contient qu'une musique
ambiante originale, la cible plus discrète est **–24 LUFS**.
Le mix voix + musique conserve son ducking avant la normalisation.

Le fichier téléchargeable `media-report.json` expose désormais :
- le niveau intégré LUFS réellement mesuré sur le MP4 ;
- le véritable pic inter-échantillons (dBTP) et le pic numérique (dBFS) ;
- la cible utilisée et les avertissements éventuels.

`qa-summary.json` conserve ces mesures dans un seul compte rendu.
Des niveaux aberrants sont signalés ou refusés par le contrôle qualité ;
aucune publication automatique n'est autorisée.

**Limites :** la normalisation est en une passe, et non un mastering
artistique professionnel. Le niveau mesuré dépend du contenu :
un court passage silencieux ou une voix défectueuse peut toujours
nécessiter une correction et une écoute humaine. La plate-forme YouTube
peut effectuer sa propre normalisation ; les cibles citées sont des
objectifs du projet, pas des exigences officielles de YouTube.


## Relecture visuelle rapide sur Android

Le workflow gratuit exporte maintenant, à partir du **MP4 réellement encodé**,
une planche illustrée nommée storyboard-01.jpg (et des pages supplémentaires
si nécessaire). Chaque page présente des images extraites au milieu de scènes
réparties sur la vidéo, leur numéro, l'horodatage et un court extrait
de la narration. Les pages JPEG sont adaptées à une ouverture directe
et au zoom sur smartphone après extraction de l'artefact GitHub Actions.

Le fichier visual-review.json conserve l'empreinte SHA-256 du MP4 contrôlé,
les scènes échantillonnées, leurs niveaux de luminance et les alertes possibles
(images illisibles, majoritairement noires, cadrages répétés). L'analyse est
intégrée à qa-summary.json : un échec bloquant empêche de déclarer l'aperçu
techniquement prêt. Aucune vidéo n'est approuvée pour publication.

Les prélèvements sont **limités à 12 scènes** dans le workflow pour préserver
le temps de traitement. Les scènes sombres ou visuellement répétitives
peuvent être intentionnelles : les alertes doivent être examinées avant
d'en tirer une conclusion. Une planche de quelques images ne remplace pas la
lecture complète du MP4. Aucune image de la vidéo d'un concurrent n'est utilisée.

### Décors plein écran et plans de caméra

Pour les scènes du personnage **chouette originale** en style `cartoon`,
l'export affiche maintenant un paysage procédural 2D sans grand panneau
opaque de narration sur la droite. Les textes complets restent disponibles
en fichiers de sous-titres `SRT` et `WebVTT`. Le rendu module les six plans
validés par le storyboard : large, moyen, rapproché, macro, bas et épaule.
Les plans hors large comportent un mouvement de caméra léger et déterministe.

L'amélioration se voit dans `preview.mp4` et dans la planche JPEG de relecture
extraite du MP4. Les anciens PNG de la chouette doivent être régénérés et
réapprouvés, car le moteur refuse la réutilisation d'un asset dont la version
artistique ne correspond plus à l'empreinte de validation.

Ce mode est original, gratuit et sans IA vidéo distante, mais demeure
une animation stylisée 2D. Les décors et placements doivent être revus avant
la mise en ligne ; l'exécution réussie d'Actions ne constitue pas un accord
éditorial ou juridique.

### Transitions fluides entre les scènes

Le champ `Transition` du workflow propose `dissolve` (défaut) ou `cut`.
En mode `dissolve`, la dernière image de chaque scène se fond dans les
premières images de la scène suivante sur environ 320 ms. Ce procédé
n'enlève ni ne recouvre les temps de narration : il conserve les durées
et les horodatages SRT/VTT d'origine. Le procédé encode de nouveau la
partie concernée, puis réutilise les clips de transition mis en cache.

Le fichier `render-report.json` et le contrôle qualité structurel
documentent les transitions et vérifient que le décalage du montage vidéo
est nul. Ces fondus sont visuels uniquement ; une vraie transition de
scènes animées ou un montage artistique reste à perfectionner.

### Nouvelles ambiances automatiques

Les scènes `cartoon` de la chouette, du renard, du lapin et du chat
intègrent désormais des particules de pollen en journée et des lucioles
la nuit. Les particules sont animées localement dans FFmpeg, uniquement
au premier plan : le ciel et les étoiles restent stables. Le contenu du
scénario, la voix, les sous-titres et le calendrier des scènes sont
inchangés. Pour vérifier l'effet, ouvrir `preview.mp4` et les planches
de relecture présentes dans l'artefact GitHub Actions.

Aucune banque de vidéos ni API payante n'est utilisée ; les effets sont
stylistiques et nécessitent une relecture avant publication.

### Actions et mimiques automatiques

Le scénario choisi dans One-click preview peut maintenant déclencher
des mouvements plus différenciés pour la chouette, le renard, le lapin
et le chat : marche, course, saut, vol, parole, surprise et repos.
Le moteur ajoute une bouche qui s'ouvre périodiquement pendant les
scènes de dialogue, sans perturber le clignement des yeux. Les mêmes
ambiances de jour/nuit, la météo, les plans de caméra et les transitions
`dissolve` continuent de fonctionner.

Ces gestes proviennent exclusivement des indices présents dans le
scénario ; ce ne sont pas des animations 3D ni du lip-sync au mot.
Le rendu reste un brouillon à examiner sur ton téléphone.

### Marche, course et saut : pattes séparées

Le personnage choisi automatiquement (`renard`, `lapin` ou `chat`)
possède deux pattes dessinées sur des calques indépendants, qui
alternent pendant la marche et la course, et se replient ensemble
pendant les sauts. Les mouvements sont sélectionnés depuis le
scénario. Aucune option payante ou manipulation Android n'est requise.
Ils demeurent des mouvements procéduraux stylisés 2D et ne remplacent
pas la relecture de `preview.mp4`.

### Objets simples et gestes visuels automatiques

Dans les prévisualisations `cartoon`, un personnage original peut
désormais inspecter, ramasser ou sauter par-dessus certains objets si
le scénario mentionne **explicitement** une action et une pomme, une
fleur, un livre ou une pierre. Les illustrations sont gratuites et
produites localement. Aucun mot n'est ajouté à la narration.

Pour essayer depuis Android, indiquer par exemple dans le scénario :
« Le renard ramasse une pomme rouge. » ou « Le lapin saute par-dessus
une pierre. ». Le fichier `preview.mp4` permet d'examiner les gestes
en mouvement. Ce sont des animations 2D procédurales et non une
simulation physique du ramassage.

### Objets ramassés conservés entre plusieurs scènes

Dans une histoire `cartoon` avec une chouette, un renard, un lapin ou
un chat, une pomme, un livre ou une fleur explicitement ramassés peuvent
maintenant rester visibles près du personnage lors des plans suivants.
La narration n'a pas besoin de répéter le nom de l'objet. Une mention
explicite indiquant qu'il est déposé ou consommé met fin à ce suivi.

La mémoire des objets est limitée à un objet à la fois, et se reconstruit
depuis les scènes du script, sans service payant. Regarder les scènes
successives dans `preview.mp4` et vérifier le rapport
`render-report.json` (champ `propContinuity`) avant publication.

### Gestes successifs dans un même plan

Pour une scène `cartoon` avec un personnage original, écrire plusieurs
actions successives dans la narration (« Le renard marche, puis saute,
puis parle. ») déclenche jusqu'à trois phases de mouvement. Les raccords
de pose sont légèrement lissés. L'audio et les sous-titres ne sont pas
redécoupés : le moment exact des gestes est estimé à partir du texte et
doit être revu dans `preview.mp4`. Le champ `actionTimeline` du
`render-report.json` permet de contrôler les phases prévues.

### Regards des personnages

Les personnages originaux `cartoon` regardent désormais vers les objets
qu'ils inspectent, ramassent ou franchissent. Un objet porté d'une scène
précédente produit une pose d'yeux légèrement orientée vers le bas.
Aucun réglage supplémentaire n'est nécessaire sur Android.
Vérifier les poses dans `preview.mp4` et dans `objectGaze` du rapport :
ce sont des orientations 2D fixes, et non un suivi permanent de l'objet.

### Gestes mieux synchronisés avec la voix

Sélectionner une voix `espeak` ou `kokoro`, puis
`Caption timing = audio`. Lorsqu'une phrase de sous-titres réellement
synthétisée décrit un geste distinct, le dessin déclenche désormais
ce geste à **son début audio mesuré**. Le champ `audioAnchored` du
`render-report.json` indique les scènes ayant bénéficié de ce réglage.

Cela n'invente pas de synchronisation mot à mot : plusieurs gestes
prononcés dans la même phrase restent placés proportionnellement
au texte. Les anciens modes, la qualité audio et les sous-titres
ne changent pas. Le MP4 doit toujours être visionné avant publication.

### Regard et bouche animés plus naturellement

Les yeux des personnages `cartoon` rejoignent désormais leur cible
en environ 420 ms au lieu d'être figés dans une orientation dès la
première image. Les clignements restent présents.

Avec `Voice = espeak` ou `kokoro`, la voix WAV créée pour la
prévisualisation peut aussi fermer la bouche pendant les silences,
**uniquement si le personnage parle dans le scénario**. Le moteur
utilise une mesure de volume toutes les 80 ms ; ce n'est pas encore
une synchronisation précise des lèvres sur les phonèmes.

Le rapport `render-report.json` contient `speechMouth` :
nombre de scènes analysées et d'intervalles de voix. Aucun service
payant, réglage manuel ou publication automatique n'est nécessaire.

### Contrôle des animations et des images figées

Le workflow GitHub `One-click YouTube preview` examine maintenant
**deux images réelles par scène échantillonnée** dans le MP4 encodé.
Il bloque la validation technique lorsqu'un personnage attendu comme
animé semble totalement figé, sans pénaliser les documents ou photos
volontairement statiques.

Dans l'artefact du workflow, ouvrir
`review/visual-review.json` pour consulter les champs
`motionPairsCompared`, `frozenAnimatedSceneCount` et les
mesures `frames[].motion`. Les planches
`review/storyboard-*.jpg` restent disponibles pour une
inspection manuelle directement sur ton téléphone.

Ce contrôle est limité à un échantillonnage et ne dispense jamais
d'écouter ni de visionner l'épisode avant publication.
