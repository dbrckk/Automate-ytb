# Automate-ytb — Sous-titres vocaux naturels pour TikTok et YouTube Shorts

## Pourquoi cette modification

Le rendu documentaire NOAA précédent possédait une véritable narration anglaise
Kokoro, mais seulement **quatre sous-titres**, affichés en une fois pendant
chaque long plan. Un Short professionnel a besoin de textes plus courts et
synchronisés, sans redevenir un montage de diapositives.

## Fonctionnement réel (gratuit et hors service payant)

1. Chaque ligne du script reste un **beat narratif** et un vrai plan filmé.
2. Les lignes sont découpées en petits **groupes de mots prononçables**
   (48 caractères et 8 mots maximum, ponctuation conservée).
3. Kokoro synthétise chaque groupe; les blancs excessifs de début et de fin
   sont raccourcis sans détruire les pauses intérieures.
4. Le début/la fin de chaque sous-titre provient **du nombre exact d'échantillons
   PCM 24 kHz générés**. Aucun timing proportionnel au nombre de lettres ou
   de mots n'est présenté comme une précision phonétique.
5. Chaque plan conserve sa véritable source NOAA, son recadrage suivi par
   activité et son éclairage. Dans le même encodage FFmpeg, le filtre
   **libass** dessine discrètement les phrases parlées au bas de la
   zone centrale, avec contour lisible, petite entrée/sortie douce et
   marges réservées pour les contrôles mobiles TikTok/Shorts.
6. Le SRT distinct contient les mêmes phrases et les mêmes instants.
   La voix Kokoro et le mixage musical original restent inchangés dans
   leur principe; pas de nouvelle musique sous licence.
7. L'export est revérifié avec `media_qa` et `shorts_delivery` puis
   archivé sur GitHub Actions, **sans publication automatique**.

La durée de la vidéo est maintenant évaluée depuis le **fichier PCM de
narration réel**, et non un nombre fixe de 22,05 secondes : cela évite
les faux échecs lorsque Kokoro prononce plus lentement une phrase.

## Contrôles reproductibles

```bash
python -m unittest discover -s tests -p 'test_short_captions.py' -v
```

Les vérifications couvrent la conservation exacte du texte source,
les modifications malveillantes ou accidentelles de sous-titres,
les chevauchements temporels, la sécurité des expressions ASS,
la génération SRT et **une vraie vidéo H.264 encodée/décodée dont les
pixels affichent le sous-titre aux instants prévus**.

Le workflow `.github/workflows/kokoro-short-voice.yml` génère
également le vrai documentaire NOAA + voix Kokoro EN + MP4 1080×1920
avec contrôle technique complet, en incluant les nouveaux fichiers
dans ses déclencheurs de régression.

## Limites explicites

- **Ce n'est pas un alignement mot à mot** : un groupe de mots prononcé
  naturellement forme une seule unité affichée. Un futur karaoké
  mot par mot nécessitera un véritable alignement phonétique/ASR
  indépendant et une vérification de transcription.
- Synthétiser des groupes plus courts peut modifier la prosodie d'une
  grande phrase; la qualité de voix doit être écoutée humainement.
- Les zones de sécurité diffèrent selon les interfaces réelles des plateformes;
  il faut vérifier le MP4 sur téléphone avant toute publication.
- Un recadrage d'une source 720p panoramique vers une sortie 1080p verticale
  agrandit des pixels; il ne crée pas de détails natifs. La priorité suivante
  reste l'acquisition de sources verticales haute définition autorisées.
- Les contrôles techniques ne constituent ni un contrôle des droits d'auteur,
  ni une évaluation artistique, ni une autorisation de publication.

## Livraison GitHub

Les fichiers attendus dans l'artefact sont :
`deep-sea-short.mp4`, `deep-sea-short.srt`,
`narration.wav`, `narration.json`,
`deep-sea-short.json`, `deep-sea-media-qa.json`,
`platform-shorts-report.json`, **`caption-review.jpg`** (quatre vraies
captures extraites du MP4 final pour une revue rapide sur Android)
et les crédits de source.
