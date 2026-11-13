# Pilote : l’éveil d’une fleur imaginaire

Le pilote français montre une ouverture de cinq pétales indépendants, suivie
d’un amortissement. Il s’agit d’une illustration fictive, pas d’une simulation
botanique. Les moteurs existants de dessin vectoriel, articulations, caméra,
narration PCM, Foley et encodage sont réutilisés.

## Production locale

Installer FFmpeg, eSpeak NG et les dépendances Python du projet. Pour la voix
neuronale, installer PyTorch CPU puis `pip install -e '.[speech]'`.
Kokoro télécharge son modèle ouvert au premier lancement ; aucun service
payant ni clé API n’est nécessaire.

```bash
python examples/build_articulated_flower_pilot.py --out-dir outputs/flower
automate-ytb-short --brief outputs/flower/articulated-flower.story.json \
  --output outputs/flower/flower-pilot.mp4 --voice kokoro --width 1080
python scripts/prepare_flower_delivery.py \
  --video outputs/flower/flower-pilot.mp4 --output outputs/flower/delivered --release
```

La voix française par défaut est `ff_siwis`. Pour un brouillon de test,
utiliser `--voice espeak --width 720` et omettre `--release` lors de la
préparation. Un brouillon eSpeak est explicitement refusé par le contrôle
de livraison neuronale, même s’il est techniquement valide en 1080p.

Le kit contient le MP4 original, le SRT, le rapport de production, une planche
de six images extraites du MP4 et un manifeste avec leurs SHA-256. La QA
redécode intégralement les flux, vérifie les sous-titres, recherche les
intervalles presque noirs et mesure le mix AAC final. Cible : −16 LUFS,
plafond −1,5 dBTP ; tolérances de contrôle : ±1 LU et +0,2 dB après AAC.
La musique et le mix sont stéréo 48 kHz.

## Comparaison et tests

```bash
python examples/build_articulated_flower_pilot.py --out-dir outputs/flower --baseline
automate-ytb-short --brief outputs/flower/baseline-flower.story.json \
  --output outputs/flower/baseline.mp4 --voice espeak --width 720
python -m unittest discover -s tests -p test_articulated_flower.py -v
python -m unittest discover -s tests -p test_flower_delivery.py -v
python -m unittest discover -s tests -p 'test_universal*.py' -v
```

La baseline garde l’ancienne fleur rigide et emploie le même texte français
pour faciliter la comparaison aux mêmes moments. Elle démontre précisément
le défaut corrigé : la narration annonçait une ouverture que le sujet entier
simulait par rotation et changement d’échelle. Ce fichier est un comparateur,
pas un candidat à une publication.

### Mesures locales du 13 novembre 2026

Trois vrais MP4 ont été encodés : baseline 720p, pilote 720p et pilote 1080p,
avec eSpeak en français. Tous durent 25,267 s à 30 fps ; leurs sous-titres
et frontières de narration sont identiques. Les deux pilotes passent le
décodage intégral, le contrôle des sous-titres et la détection d’intervalles
presque noirs. Le mix final est stéréo 48 kHz, à −16,3 LUFS et −1,5 dBTP.
Les [mesures brutes](flower-pilot-benchmark-2026-11-13.json) contiennent les
SHA-256 des médias réellement examinés.

La part médiane de pixels modifiés passe de 2,580 % sur la baseline à
1,065 % sur le pilote 720p : elle n’est pas utilisée comme note de qualité.
La correction vérifiée porte sur l’ouverture indépendante des pétales et
l’ancrage du sujet, avec des phases d’attente et de stabilisation assumées.

Kokoro a été installé dans l’environnement de développement, mais l’accès
à son modèle sur Hugging Face a renvoyé HTTP 403. Aucun rendu Kokoro ni
aucune écoute neuronale ne sont donc attestés par ces mesures locales.
Le workflow prévoit cette production sur un runner disposant de l’accès
au modèle ; aucune URL de Release n’est déclarée vérifiée à ce stade.

Les tests vérifient les cinq mouvements relativement au cœur, l’ancrage au
sol, les silhouettes dans le cadre, les poses aux raccords, la reproductibilité,
les limites de complexité et l’identité entre propriétés animées et événements
audio. Un test encode réellement un pilote court avec eSpeak, puis vérifie
le décodage complet, le mix, les sous-titres et le refus de livraison neuronale.

## Android et téléchargement durable

Dans **Universal kinetic Short — real MP4/audio smoke**, lancer manuellement
`flower_pilot=true`, `voice=kokoro` depuis `main`. Le pilote français est
prédéfini : aucun sujet ou scénario n’est nécessaire. Les autres exemples
restent présents pour tester les régressions.

Après réussite complète, **Stable direct MP4 download for articulated flower**
accepte uniquement un rendu manuel réussi du même dépôt sur `main`. Il
contrôle les empreintes du kit, refait la QA et crée une pré-release unique
par exécution. Le lien direct n’est annoncé qu’après téléchargement anonyme
intégral et comparaison octet par octet. Les PR et brouillons eSpeak ne
déclenchent aucune publication. Les assets Actions demeurent temporaires.

## Limites de validation

La qualité artistique reste à écouter et à regarder sur téléphone et au
casque. Aucun score esthétique n’est déduit du nombre de pixels animés.
La référence n’est considérée atteinte qu’après une revue humaine à au moins
4/5 dans chacun des axes de la grille du plan directeur V2. Les rapports
gardent `humanReviewed=false` et `publicationApproved=false`.

Le moteur ne génère pas encore automatiquement une anatomie ou un scénario
sourcé depuis un simple titre. Cette livraison améliore une capacité
réutilisable de mise en scène et de synchronisation, illustrée par le pilote.
