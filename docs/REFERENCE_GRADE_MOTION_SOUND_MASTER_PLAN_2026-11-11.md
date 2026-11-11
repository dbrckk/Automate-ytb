# Objectif de qualité : animation scientifique de référence (2026-11-11)

## Source et limites de l'analyse

Référence fournie par l'utilisateur : `3561.mp4`, 30,8 s, 576×1024, 30 fps, H.264/AAC, environ 2 Mo. Thème : nombre de plis d'une feuille pour atteindre la Lune. Analyse de dix échantillons vidéo espacés de trois secondes. Le son n'a pas fait l'objet d'une écoute humaine comparative : aucune note de musicalité, timbre, rythme sonore ou naturel vocal n'est revendiquée. Ne pas copier les images, la bande-son, le script, les logos ou les assets du créateur.

Observations vérifiées : fond sombre stable ; une seule jauge de progression continue ; compteur de plis et épaisseur qui évoluent ; changements d'échelle avec repères physiques (objet, personne, tour, montagne, Terre, Lune, étoiles) ; effets lumineux parcimonieux ; un même phénomène causal conservé d'un plan au suivant ; révélation finale. **L'excellence perçue vient de la direction d'animation et du timing, pas de la quantité de détails ni de la résolution.**

## État du dépôt à l'audit

- `automate_ytb/scene_plan.py` : planifie des segments narratifs ; n'exprime pas encore une représentation continue d'une même grandeur ni une transition d'échelle vérifiable.
- `automate_ytb/science_portrait.py` : images 1080×1920, effets 2.5D, narration et sous-titres ; beaucoup de rendus sont composés par chapitre et non à partir d'un état persistant.
- `automate_ytb/science_audio_cues.py` : synchronisation **par phrase** mesurée ; pas d'alignement mot/phonème ni de partition d'effets audio sur une chronologie commune.
- `automate_ytb/science_storyboards.py` : scènes océaniques spécifiques ; pas de grammaire d'animation de données universelle.
- `.github/workflows/one-click-preview.yml` : rendu narré et validation technique automatisée.
- Livraison GitHub Releases MP4 et historique fonctionnels ; épisode océan 34,43 s, 1080×1920, H.264/AAC, vérifié sur le run 43064804190 et livré sur la release science-preview-ocean-heat-engine-43064804190.
- L'amélioration P5.27 de l'action causale est intégrée au moteur. **Aucun résultat visuel n'est qualifié de « qualité référence » sans revue sur un nouveau rendu.**

## Définition de réussite

Créer des vidéos originales sur plusieurs thèmes dont l'image, le son et la narration évoluent ensemble de façon continue. Le rendu final doit être explicatif, dynamique, lisible sur smartphone et cinématographiquement dirigé ; pas un diaporama décoré. Architecture réutilisable, locale, gratuite/open source, déterministe pour les tests et capable de produire un MP4 téléchargeable sans manipulation utilisateur.

### P0 — Moteur de narration visuelle persistante (premier chantier)

**Livrable** : `NarrativeTimeline` à état continu, piloté par des événements (concept, quantité, comparaison, révélation) ; `VisualState` persistant entre les plans ; caméra et objets animés depuis les mêmes données temporelles. Le compteur, l'échelle, le sujet et les repères ne doivent pas se réinitialiser à chaque phrase.

- Une valeur réelle et son unité pilotent directement les transformations d'objets et le compteur. Pour les quantités exponentielles : `value = base * 2**n`, calcul sans dépassement ou conversion float aveugle.
- Échelles linéaires, logarithmiques et catégories physiques (centimètre → bâtiment → planète) ; transitions calibrées, pas de téléportation non signalée.
- Système de repères de comparaison avec provenance et contrôles des unités ; l'objet de référence apparaît au moment où la grandeur l'atteint.
- Caméra continue (position, zoom, profondeur, easing), anticipation/overshoot légers, suivi d'objet ; aucune coupe gratuite.
- Le moteur doit pouvoir illustrer au moins trois sujets non apparentés, sans code graphique codé en dur pour chaque narration.

**Acceptation** : prototype vertical de 25–35 s, 3 sujets distincts, au moins 6 transitions de grandeur/repère par vidéo, zéro retour de compteur involontaire, trajectoires continues à 30 fps ; tests de monotonie, de coordonnées et de conservation des unités. Revue manuelle de lisibilité sur Android.

### P1 — Direction artistique et graphismes 2.5D premium

**Livrable** : scène hiérarchique par calques avec profondeur, occlusion, ombres portées, lumière motivée, matières différenciées, particules à vie finie et une palette pilotée par sujet. Illustrations et objets originaux, SVG/Blender/Godot/Pillow selon le coût CPU et la maintenabilité ; aucun service payant requis.

- Ne pas imposer de photoréalisme : reproduire la *qualité de direction artistique*, y compris en infographie minimaliste.
- Introduire typographie cinétique, éclairage adaptatif et contrastes guidant le regard, sans cadres de type PowerPoint.
- Garder les titres/sous-titres dans les zones sûres TikTok/Shorts ; contraste lisible en mouvement.
- Établir des règles de continuité chromatique, de lumière et d'échelle d'un plan à l'autre.

**Acceptation** : comparaisons de 12 images clés + 3 courtes séquences par thème, tests d'occlusion, de cohérence du layout et de scintillement, vérification humaine de la lisibilité à 360 px de large. Aucun asset de la référence copié.

### P2 — Sound design événementiel et mixage musical

**Livrable** : piste `AudioEventTimeline` utilisant les **mêmes événements temporels que les animations** : pliage, impact, croissance, zoom, transition d'échelle, apparition de repère, révélation. Synthèse DSP/échantillons CC0 vérifiés ; métadonnées de licence et attribution si nécessaire.

- Déclenchement des effets sur événements physiques, enveloppes attack/decay, spatialisation stéréo discrète, transitoires propres ; éviter un « whoosh » sur chaque coupe.
- Musique originale ou à licence compatible, structurée en introduction, montée, tension, révélation, sortie ; ducking sous la voix et cohérence harmonique.
- Pipeline séparant voix, musique, ambiance et effets ; sidechain/ducking, limiteur true peak et contrôles de silence/clipping.
- Pas de copie ni de reproduction de la musique/du sound design de la vidéo de référence.

**Acceptation** : au moins 5 classes d'événements audibles et alignées sur les images (tolérance cible ≤ 80 ms mesurée), pas de clipping, mesure LUFS/true peak documentée, écoute comparative au casque et haut-parleur de smartphone. Aucun « score audio » sans écoute.

### P3 — Narration, sous-titres et montage au mot

**Livrable** : alignement temporel au mot/phonème lorsque disponible en local ; repli explicite aux frontières de phrases réelles. Narration naturelle EN/FR avec choix de voix et rythme par épisode ; pauses, emphase et transitions musicales dirigées par la timeline.

- Évaluer Kokoro sur articulation, pauses et accent ; benchmark d'alternatives gratuites sur les **mêmes textes** plutôt que changer de voix à l'aveugle.
- Synchroniser l'apparition de chiffres, repères et bruitages au moment où ils sont prononcés.
- Garder des sous-titres courts, exacts, sans coupure ni retard ; montage de réaction à la voix et non inversement.

**Acceptation** : sous-titres sans débordement, métrique d'écart entre événement visuel et mot prononcé, absence de fin audio tronquée ; panel d'écoute humaine pour sélectionner les voix.

### P4 — Grammaire de réalisation multi-genres

**Livrable** : directeur `hook → question → progression → changement d'échelle → surprise → résolution`, avec variations par sujet (science, histoire, économie, objets, données) ; continuité d'objets et de caméra, rythme et contrastes sans modèle « cinq cartes identiques ».

**Acceptation** : trois vidéos inédites, chacune avec au moins une transformation réellement continue, une montée sonore et une révélation visuelle, sans répétition d'assets ou d'effets identiques.

### P5 — Validation automatique et livraison

- Validation structurelle : plan, données/unités, licences, provenance des médias, déterminisme.
- Validation technique : décodage complet H.264/AAC, 9:16, fps, synchronisation voix/sous-titres, loudness, true peak, pas de coupure ni de frame noire prolongée.
- Validation du mouvement : différences inter-images significatives **et** continuité de trajectoire ; un score de pixels différents ne suffit pas.
- Validation éditoriale : grille humaine de 1 à 5 pour lisibilité, cohérence des animations, qualité de voix, pertinence musicale, finesse des bruitages et satisfaction de la révélation finale.
- Livrer un MP4 direct via GitHub Releases **seulement après** succès de tous les contrôles automatiques ; historiser version, moteur, seed, sources, scores et empreinte SHA-256.

## Ordre d'exécution et dépendances

| Lot | Dépendance | Livrable démontrable | Priorité |
| --- | --- | --- | --- |
| 1 | Aucune | Schéma d'événements + prototype de grandeur persistante | Bloquant |
| 2 | Lot 1 | Caméra/repères 2.5D continus et rig d'animation | Haute |
| 3 | Lot 1 | Bruitages synchronisés, stems et mixage | Haute |
| 4 | Lots 1–3 | Alignement vocal plus précis et musique dramaturgique | Haute |
| 5 | Lots 1–4 | 3 sujets originaux de validation + comparaison | Haute |
| 6 | Lot 5 | CI, QA éditoriale, GitHub Releases et historique | Obligatoire |

**Règle d'exécution** : terminer et tester un lot avant d'empiler le suivant. L'objectif n'est pas un seul « joli » épisode : toute amélioration doit vivre dans la pipeline et être réutilisable. L'atteinte de la qualité cible ne sera revendiquée qu'après revue réelle de vidéos complètes, son compris.
