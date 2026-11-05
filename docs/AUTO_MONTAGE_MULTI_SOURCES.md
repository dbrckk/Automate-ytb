# Montage automatique de plusieurs vidéos originales — P1

## Ce qui fonctionne

Le moteur Python/FFmpeg combine automatiquement plusieurs **vidéos locales
que l'utilisateur possède ou peut légalement éditer** en un MP4 final, sans
sélection manuelle de chaque extrait. Les scènes peuvent provenir de vidéos
différentes, conservées dans l'ordre indiqué, **sans répétition ni gel de
quelques images** pour combler une durée impossible.

Il fonctionne pour les projets documentaires, produits, fitness, gaming,
voyage, éducatifs, personnels ou cinématiques. Le genre choisi est un
libellé éditorial, pas une analyse sémantique automatique.

## Commande complète (Linux, Windows avec Python/FFmpeg)

Créer un fichier texte `script.txt` contenant une phrase originale par
séquence (5 phrases pour 30 secondes à 6 secondes/plan), puis :

    python -m pip install -e .
    python -m automate_ytb.auto_edit \
      --script script.txt \
      --topic "A journey through the city" \
      --videos original-01.mp4 original-02.mov original-03.mp4 \
      --genre documentary \
      --duration 30 --shot-seconds 6 \
      --resolution shorts --fps 30 \
      --rights-note "I recorded these videos and own their editing rights." \
      --confirm-rights \
      --output finished-video

Pour un plan existant validé par le planificateur, remplacer
`--script script.txt --topic ...` par `--plan scene-plan.json`.
Si une narration enregistrée ou une musique originale est disponible,
ajouter `--audio narration.wav` ou `--music music.wav`.
Par défaut, la vidéo est silencieuse sans `--audio` ni `--voice-engine`.
Le son des caméras est volontairement supprimé.

### Narration automatique gratuite (EN/FR)

Pour produire une vidéo **avec voix naturelle en anglais** sur la même
commande, installer Kokoro localement sur une machine disposant de Python,
FFmpeg et des ressources nécessaires :

    python -m pip install -e '.[speech]'
    python -m automate_ytb.auto_edit \
      --script script.txt --topic "Original documentary" \
      --videos original-01.mp4 original-02.mp4 original-03.mp4 \
      --duration 30 --shot-seconds 6 --genre documentary \
      --voice-engine kokoro --language en --voice-name af_bella \
      --narration-style expressive --resolution shorts \
      --rights-note "I recorded these videos and own their editing rights." \
      --confirm-rights --output english-narrated-video

Pour le français, utiliser `--language fr --voice-name ff_siwis`.
Omettre `--voice-name` choisit la voix par défaut de la langue.
Les styles disponibles sont `natural`, `gentle`, `lively` et
`expressive`; ils modulent raisonnablement le débit, pas les émotions
par clonage. Le téléchargement initial du modèle Kokoro est gratuit mais
nécessite un accès réseau et consomme des ressources locales. Le brouillon
`--voice-engine espeak` (avec eSpeak installé) fournit un repli technique
plus robotique, **non recommandé comme voix finale**. Aucun appel à
une API de synthèse payante n'est effectué.

La synthèse utilise le scénario d'origine de **chaque scène** et produit
`narration.wav` ainsi que `voice-report.json`. Les durées réelles du
signal PCM sont mesurées et peuvent allonger les plans : l'algorithme
revalide alors la capacité des rushes. Si elle est insuffisante, le montage
échoue proprement plutôt que d'accélérer artificiellement la voix,
de tronquer la phrase ou de répéter les images. Les sous-titres sont
horodatés par phrases synthétisées, **pas alignés au phonème/mot**.

`--audio` et `--voice-engine kokoro/espeak` sont mutuellement exclusifs.
Le modèle et les voix ne sont chargés que lorsque la synthèse est activée.
La revue humaine des prononciations, du rythme et de la cohérence
des extraits reste obligatoire.

## Résultats

- `finished-video/render/preview.mp4` : H.264, 9:16 1080×1920 par défaut;
  options `--resolution 720p` ou `1080p` pour 16:9.
- `finished-video/render/draft-captions.srt` : sous-titres séparés, estimés
  à partir du texte; ils ne sont pas intégrés à l'image.
- `finished-video/scene-plan.json` : scènes et preuves de droits,
  empreintes SHA-256 des MP4 normalisés et images.
- `finished-video/assets/` : vrais extraits vidéo normalisés et vignettes.
- `finished-video/narration.wav` et `voice-report.json` : seulement lorsque
  la synthèse vocale locale est choisie, avec preuves de durée.
- `finished-video/auto-edit-report.json` : provenance, allocation,
  timecodes de chaque extrait, diagnostics d'exposition, contraste et
  mouvement, avertissements de revue.
- `finished-video/render/visual-preflight.json` et
  `render-report.json` : contrôle technique et métadonnées d'encodage.

Le projet est préparé dans un dossier temporaire puis publié uniquement
une fois le MP4 intégral produit. Si le montage échoue, aucun dossier final
incomplet n'est publié. Un dossier existant n'est jamais écrasé.

## Comment les extraits sont choisis

1. Tous les fichiers sont inspectés avec FFprobe : type, durée, codec,
   résolution et capacité de découpage; toute vidéo insuffisante ou
   illisible échoue avec une explication.
2. Le plan est réparti entre les sources dans leur ordre; l'algorithme
   privilégie plusieurs fichiers distincts pour varier les images.
3. Le temps disponible est réparti sans chevauchement. Quand un fichier
   comporte des marges, FFmpeg évalue quelques fenêtres candidates en
   96×54 pixels : luminosité, contraste et changement entre images.
4. Le programme sélectionne l'extrait qui évite les noirs, sur/sous-
   expositions flagrantes et plans très plats, puis conserve les
   diagnostics et les empreintes dans le rapport.
5. Les extraits sont réellement découpés et encodés localement; le
   montage final conserve timecodes, voix enregistrée et musique facultative.

**Limite essentielle :** ces mesures ne reconnaissent ni les personnes,
ni les événements, ni la pertinence de l'image par rapport au scénario.
Ce n'est pas encore un dérushage sémantique assisté par IA, ni un
montage professionnel certifié. Un visionnage humain reste requis.

## Garanties de sécurité et d'utilisation

- Pas de téléchargement externe, de liens Web arbitraires ou d'injection
  dans un shell : tous les programmes reçoivent une liste d'arguments.
- Les sources respectent les limitations de l'import vidéo : fichiers
  MP4/MOV/MKV/WEBM locaux, max 250 Mio/source, source vidéo validée.
- 1 à 32 fichiers; une même source ne peut pas apparaître deux fois.
- Déclaration explicite des droits pour tous les fichiers et pas de
  publication YouTube automatique.
- Sources et extraits vérifiés par SHA-256; pas de sortie « réussie » si
  l'un des encodages ou contrôles échoue.
- Mémoire et échantillonnage bornés; rendu complet via les moteurs
  FFmpeg déjà présents; aucun modèle payant ou jeton requis.

## Restant après P1

Uploader plusieurs vidéos directement depuis Android sans commande,
comprendre le contenu réel des scènes, relier clips/narration de manière
sémantique, rendre la voix Kokoro plus naturelle après écoute et améliorer
les transitions/graphismes par genre. Ces chantiers relèvent des phases
P2–P10 du plan directeur.
