# Episode science original — Comment se forment les éclairs ?

**Usage :** première production 9:16 *distincte* de la vidéo de référence « Terre à l'arrêt ». Le film référent n'est jamais importé, copié, converti ou répété dans ces cinq plans.

## Storyboard et mouvements réels

| Plan | Narration pédagogique | Action calculée par image |
| --- | --- | --- |
| 1 | Collisions gouttes / cristaux et séparation des charges | Hydrométéores, marqueurs opposés et transferts mobiles dans les nuages |
| 2 | Canal ionisé progressant vers le sol | Déploiement progressif et ramifié d'un leader descendant |
| 3 | Décharges ascendantes et jonction | Streamer remontant d'un relief vers un leader préexistant |
| 4 | Décharge lumineuse | Propagation du trait lumineux dans l'autre sens, du sol vers le nuage |
| 5 | Tonnerre | Ondes sonores concentriques qui se déplacent depuis le canal chauffé |

**Important :** le processus électrique est représenté au ralenti **à titre explicatif**. La formation du canal et le retour lumineux se produisent réellement en fractions de seconde. Le storyboard illustre une décharge nuage-sol typique, pas tous les types d'éclairs ni une prévision de trajectoire.

## Références scientifiques

- NOAA JetStream, étapes du leader, streamer ascendant, retour lumineux et temporalité :
  https://www.noaa.gov/jetstream/lightning/how-lightning-is-created/jetstream-max-lightning-process-keeping-in-step
- National Weather Service, nature du courant et propagation du retour :
  https://www.weather.gov/safety/lightning-science-return-stroke
- NOAA NESDIS, phénomènes à l'origine du tonnerre :
  https://www.nesdis.noaa.gov/about/k-12-education/severe-weather/what-causes-lightning-and-thunder

## Production

Le workflow `.github/workflows/lightning-science-release-candidate.yml` appelle directement le moteur existant de vidéo. Il exige l'export MP4 H.264 natif 1080×1920 à 30 i/s, la synthèse vocale Kokoro française (`ff_siwis`), une musique originale, le SRT et la QA des plans. Aucune image stock du film de référence, aucune clé de service payant.

Le workflow `.github/workflows/science-preview-download.yml` livre un fichier direct *uniquement si* le rendu a réussi sur `main`, après validation de SHA, du décodage et du SRT. Il n'active **jamais** la publication YouTube.

La vidéo demeure un **aperçu technique** tant que sa clarté, les informations scientifiques, la voix française et le rythme ne sont pas validés éditorialement.
