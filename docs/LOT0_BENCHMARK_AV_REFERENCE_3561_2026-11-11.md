# Lot 0 (V2) — baseline audiovisuelle reproductible, sans médias privés

**État :** outil et premier rapport implémentés. Ce lot **n'est pas déclaré entièrement terminé** : les baselines de deux styles originaux (kinetic et 2.5D) et l'intégration complète au cycle QA demeurent à réaliser.

## Livrables réels

- [scripts/benchmark_audiovisual.py](../scripts/benchmark_audiovisual.py) : analyse des **vrais fichiers encodés** via FFprobe/FFmpeg ; sans dépendance Python externe.
- [av-reference-baseline-2026-11-11.json](av-reference-baseline-2026-11-11.json) : première mesure figée de la référence **privée** et du MP4 océan **publié**, avec empreintes SHA-256.
- [tests/test_av_reference_baseline.py](../tests/test_av_reference_baseline.py) : validation des métriques, labels, confidentialité et test sur un H.264/AAC généré par FFmpeg.

Aucune image, piste audio ou copie de \`3561.mp4\` n'est envoyée au dépôt. Le rapport conserve uniquement les données techniques et empreintes, sans chemin absolu.

## Rejouer la mesure (PC Linux / runner)

Prérequis gratuits : Python ≥3.11, FFmpeg, FFprobe. La référence peut rester **hors du dépôt**, dans un dossier privé.

~~~bash
python scripts/benchmark_audiovisual.py \
  --video /chemin/prive/3561.mp4 --label reference-private \
  --video /chemin/local/ocean-heat-engine.mp4 --label ocean-baseline \
  --output /tmp/av-baseline.json
python -m unittest discover -s tests -p test_av_reference_baseline.py -v
~~~

Pour analyser uniquement une nouvelle sortie :

~~~bash
python scripts/benchmark_audiovisual.py \
  --video build/video/preview.mp4 --label new-episode \
  --output build/video/av-baseline.json
~~~

**Éviter de placer le média privé dans un artifact GitHub Actions.** L'exécution distante de la commande doit viser uniquement des clips autorisés à être lus sur le runner.

## Algorithme exact et interprétation

1. FFprobe collecte durée, dimensions, fps, codec, sample rate/canaux/débit audio.
2. FFmpeg décode les images en niveaux de gris 144×256, **4 images/s** ; pour chaque paire successive, le mouvement est le pourcentage de pixels avec changement absolu de luminance >8/255.
3. Le rapport calcule la médiane, moyenne, 90e percentile, échantillons quasi noirs et plus longue séquence de paires quasi immobiles.
4. FFmpeg \`ebur128=peak=true\` mesure **sur l'audio encodé** : LUFS intégré, LRA, true peak.
5. SHA-256 du fichier et taille binaire identifient exactement le média analysé.
6. Pour une vidéo >120 s, l'échantillonnage visuel est limité aux **120 premières secondes** et le champ \`motionWindowTruncated\` devient \`true\`; la mesure audio porte toujours sur la piste entière.

## Baseline mesurée (11 novembre 2026)

| Signal | 3561.mp4 (référence privée) | Ocean Heat Engine |
|---|---:|---:|
| Durée | 30,800 s | 34,433 s |
| Dimensions | 576×1024 | 1080×1920 |
| Médiane pixels modifiés | 9,298 % | 3,334 % |
| Moyenne pixels modifiés | 11,328 % | 4,474 % |
| LUFS intégré | −14,8 | −16,1 |
| LRA | 2,5 LU | 2,5 LU |
| Pic vrai | **+0,5 dBTP** | −1,5 dBTP |

La référence a un pic vrai élevé ; **ne pas viser +0,5 dBTP**. La nouvelle baseline ne prescrit pas 9,298 % comme quota de mouvement : les coupes, zooms arbitraires et tremblements artificiels gonflent ce score sans apporter de valeur narrative.

## Portée et limites de confiance

- **Ce que prouve l'outil :** caractéristiques de fichier, variations de luminance temporelles et mesures audio objectives.
- **Ce qu'il ne prouve pas :** qualité d'illustration, pertinence de mouvements, fluidité subjective, présence et beauté de la musique, qualité du timbre de voix, synchronisation réelle de bruitages, exactitude scientifique.
- Le rendu océan livré **avant** le nouveau plan n'implémente pas les composants futurs MasterTimeline/ScoreComposer/FoleyEngine. Ne jamais le présenter comme ayant validé ces modules.
- La mesure d'images étant échantillonnée à 250 ms, elle **ne suffit pas** à prouver une animation fluide à 30 fps ; de futurs tests complémentaires examineront chaque frame et les raccords.

## Critères avant clôture complète du lot 0

- [x] Benchmark original/private sur les mêmes règles de comparaison.
- [x] Rapport JSON versionné et tests sur MP4 réellement encodé.
- [x] Vérification du mode de confidentialité et de l'absence de média privé dans Git.
- [ ] Baseline **kinetic editorial originale** livrée en plus de l'océan 2.5D.
- [ ] Mesure CPU/RAM du rendu d'origine sur GitHub Actions.
- [ ] Revue visuelle et écoute humaine documentées, indépendamment des métriques.
- [ ] Raccordement optionnel des nouvelles mesures au rapport QA de production, sans briser l'ancien gate.

**Suite :** réaliser MasterTimeline V2 après que les critères de fondation indispensables sont couverts ; privilégier des composants réutilisables à tout type de vidéo.
