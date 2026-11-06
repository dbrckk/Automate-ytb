# M1 — Sous-titres brûlés et vérifiés pour Shorts NASA (6 novembre 2026)

## Problème vérifié sur un MP4 réel

Le Short NASA de 35 s contient de vraies séquences filmées en timelapse depuis l'ISS, une piste Kokoro et des sous-titres SRT distincts. Mais la vidéo seule n'affiche aucun texte sur un lecteur mobile qui ignore les fichiers SRT externes.

La première expérience de sous-titres intégrés a échoué visuellement alors que FFmpeg s'était terminé sans erreur : des paramètres ASS `FontSize=30,MarginV=440` plaçaient le texte **hors champ** avec le PlayRes implicite de libass. Le fichier MP4 était techniquement valide mais **aucun sous-titre n'était visible**. Une correction à `FontSize=11,MarginV=78` a été vérifiée par comparaison directe des images encodées.

## Livrables implémentés

- `automate_ytb/mobile_subtitles.py` : traite exclusivement des SRT présents sur disque, lit les phrases temporellement mesurées, et crée des sous-groupes adaptés à l'écran mobile (43 caractères, 8 mots maximum), tout en préservant **tous** les mots et les bornes de chaque phrase d'origine.
- Les sous-groupes reçoivent des durées **approximatives proportionnelles au texte** ; il ne s'agit pas de timestamps réellement alignés sur les phonèmes ou les mots. Cette limite est indiquée dans `mobile-captions-qa.json`.
- Le master original `preview.mp4` n'est jamais modifié. `preview-captioned.mp4` est recréé avec libass/FFmpeg, H.264 en 1080 × 1920, et `-c:a copy` pour préserver exactement le flux narrateur/musique AAC.
- Les styles privilégient des textes blancs contrastés, contour noir, position stable dans la zone centrale-basse, sans image de fond ou diapositive textuelle.
- Après encodage, le module **décode la vidéo complète**, vérifie H.264/AAC 9:16 et échantillonne les pixels de la zone réservée au texte. Au moins 500 pixels fortement différents (>35/255) par rapport au master sont requis à un horodatage contenant une phrase. Un rendu dont le texte a disparu hors champ **échoue**.
- Le workflow NASA produit les deux versions et livre MP4 master + MP4 incrusté, SRT original + SRT compact, crédits et diagnostics. La revue éditoriale humaine, le contrôle des sources, des licences et la publication restent distincts.

## Première preuve locale

Source : artefact GitHub déjà produit via run #42274760867, PR #200 ; rendu de contrôle local sur ce master.
- SRT original : 10 cues ; SRT mobile : 15 cues, aucune suppression ni modification de mot.
- MP4 sous-titré : **35,000 s ; 1080 × 1920 ; 30 FPS ; H.264/AAC** ; décodage FFmpeg intégral OK.
- À 1 seconde, **4 261 pixels** modifiés d'au moins 35 niveaux de gris dans la zone 270 × 150 de l'écran échantillonné : preuve de texte visible, pas seulement de métadonnées.
- Hash du flux AAC original : `17bb062f960c65e37938c2bb28f933f1f4910818a2912eb058a67fc92afbafc8`.
- Hash du flux AAC incrusté : **identique**. La voix et la musique originales ont été copiées et non resynthétisées.
- Les 2 versions sont comparables sur le même plan, en conservant les mêmes rushes.
- Il faut encore attendre les vérifications CI sur le commit exact avant fusion.

## CI plus fiable

Le workflow `validate.yml` n'exécute plus systématiquement un `apt-get update` qui avait épuisé 20 minutes avant même le premier test. Il teste les binaires du runner, puis limite explicitement les délais d'installation si un paquet manque. La limite totale de job de 30 min empêche le signal « succès » sans tests.

## Limites et prochain chantier

Le routage de sources NASA prouve qu'un monteur peut produire un Short à partir de vidéos réelles autorisées, mais ne démontre pas une recherche sémantique générale. Les 15 sous-titres courts sont lisibles, pas alignés phonétiquement. M2 : améliorer la segmentation audio réellement mesurée au niveau mot et vérifier les zones sûres des interfaces TikTok/YouTube sur plusieurs formats de source.
