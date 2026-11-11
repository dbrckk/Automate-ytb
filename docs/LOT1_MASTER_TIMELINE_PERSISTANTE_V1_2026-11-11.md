# V2 — Lot 1 : MasterTimeline persistante (première tranche exécutable)

**État :** premier moteur et script d'encodage implémentés, tests CI spécialisés déclenchés mais succès final **non encore établi**. Le rendu narré Automate-ytb historique reste inchangé : l'intégration généralisée aux Shorts et le moteur de musique sont les étapes suivantes.

## But

Remplacer progressivement la juxtaposition d'illustrations/chapitres indépendants par un état de monde unique. Un objet conserve ses propriétés physiques (valeur, position, échelle, opacité, orientation) au cours de plusieurs séquences, pendant que la caméra et les événements acoustiques utilisent la même horloge absolue.

## Fichiers

- [automate_ytb/master_timeline.py](../automate_ytb/master_timeline.py) — moteur pur, validation stricte, événements d'animation, beats, registre d'objets, ancrages de sons aux événements sources.
- [scripts/render_master_timeline_pilot.py](../scripts/render_master_timeline_pilot.py) — **pilote ingénierie original** de 6 secondes, 9:16, 30 fps, H.264/AAC, quatre effets sonores synthétiques réellement audibles, aucun téléchargement ni média tiers.
- [tests/test_master_timeline.py](../tests/test_master_timeline.py) — tests de conservation d'état, absence de reset aux frontières, tolérances, valeurs impossibles, entrées dangereuses et adaptation du plan de scènes existant.
- [tests/test_master_timeline_pilot.py](../tests/test_master_timeline_pilot.py) — tests sur fichier réellement encodé : vidéo animée et audio non nul aux événements.
- [.github/workflows/master-timeline-v1.yml](../.github/workflows/master-timeline-v1.yml) — CI gratuite, pilote H.264/AAC et rapport de mouvement/EBU R128 sur le **MP4 final**.

## Contrats du moteur

- **Objet** : ID stable limité et contrôlé, propriétés initiales validées, valeur avec unité explicite, entrée copiée et figée.
- **Beat** : intervalle continu [start_frame, end_frame] ; les beats contigus couvrent toute la vidéo, sans remise à zéro de l'état.
- **PropertyEvent** : ID, objet, propriété, frames absolues, from/to, easing (linear/smoothstep/smootherstep). Même propriété : pas de chevauchement ni de saut de valeur non motivé.
- **SoundCue** : fait référence à l'ID d'un **vrai événement visuel** et reçoit un onset précis en **échantillons PCM**, pas une estimation de mot prononcé.
- **MasterTimeline.state_at(frame)** : état complet purement dérivé de la frame demandée, indépendamment de l'ordre d'appel, des coupes ou du nombre de frames déjà rendues.
- **MasterTimeline.from_scene_plan(...)** : convertit les vrais startMs/endMs d'un fichier \`scene-plan.json\` V1 en intervalles de frames, sans remplacer son schéma ou modifier ses données.
- **Compatibilité Kokoro confirmée localement :** les plans réels de production ont une durée décimale dérivée du PCM. Le cas océan à 34,42 s, cinq scènes et 34 420 ms est converti en 1 033 frames à 30 fps, avec les bornes exactes [0,204,408,612,816,1033]. Les valeurs incohérentes, booléennes et non finies sont rejetées.
- **Preuve indépendante :** un pilote local de 6 s à 30 fps avec quatre sons causaux a été encodé H.264/AAC, décodé entièrement et audité EBU R128. Cela ne remplace pas la validation du rendu du script GitHub, qui reste attendue en CI.
- **MasterTimeline.audio_events()** : manifeste détachable de cues non mutables pour le moteur Foley/mixage futur.
- Horloge du pilote : 30 fps, audio PCM 48 kHz, **1 frame = 1600 samples**, sans dérive.

## Reproductibilité / commande manuelle facultative

~~~bash
python -m pip install -e .
python -m unittest discover -s tests -p 'test_master_timeline*.py' -v
python scripts/render_master_timeline_pilot.py \
  --output build/master-timeline/timeline-original.mp4 \
  --width 360 --height 640
python scripts/benchmark_audiovisual.py \
  --video build/master-timeline/timeline-original.mp4 \
  --label timeline-engineering-pilot \
  --output build/master-timeline/av-baseline.json
~~~

La CI exécute cette démonstration sans action utilisateur, conserve le MP4 réel et ses rapports en artifact temporaire. **Ne pas confondre ce pilote technique avec une vidéo professionnelle prête à publier.** Il n'inclut ni voix Kokoro ni musique structurée et ne doit jamais être présenté comme une nouvelle sortie publiable.

## Sécurité et limites

1. Pas de code exécuté depuis les scripts utilisateurs, pas de prompt chargé en tant qu'instruction.
2. Validation des identifiants, types exacts (booleans rejetés), valeurs finies, unités, limites de frames, d'objets, d'événements et de cues.
3. Refus des sources sonores inconnues, des onsets négatifs et hors-durée, des ID dupliqués et des mouvements contradictoires.
4. Les effets de bruitages proviennent d'oscillateurs originaux dans le pilote ; pas de pistes téléchargées.
5. Aucune voix ou timestamp **au mot** n'est revendiqué : les positions temporelles du noyau sont des frames et les segments PCM par phrase existants pourront être adaptés explicitement lors du raccordement.
6. L'ancien moteur \`action_timeline.py\` reste fonctionnel. Les créateurs de Shorts existants ne changent pas de comportements tant que le raccordement n'est pas validé.

## Definition of Done : tranche 1

- [x] WorldObject / Beat / PropertyEvent / SoundCue validés et reproductibles.
- [x] Conserver un objet et une caméra à travers trois beats **dans la même horloge**.
- [x] Refuser les chevauchements, sauts de valeur, IDs/temps non valides et sources audio inexistantes.
- [x] Ancrer les sons en échantillons 48 kHz depuis les vrais événements visuels.
- [ ] Confirmer sur un véritable MP4 que le script produit les images originales et les SFX au bon moment (CI en attente).
- [ ] Confirmer la CI complète et le pilote MP4 final sur GitHub Actions, puis renseigner le run et l'empreinte.
- [ ] Brancher ce monde persistant dans \`episode.py\` / \`science_portrait.py\` par une option réversible, sur une narration Kokoro réelle.
- [ ] Raccorder les stems Foley à \`production.render\` et vérifier volume/mix/sous-titres.
- [ ] Réaliser deux vidéos inédites sur **des sujets distincts** exploitant effectivement cette API.

Les trois derniers points appartiennent aux étapes suivantes du lot 1 / lots 2 à 4 et ne sont **pas implicitement terminés** par ce pilote.

## Travail suivant le plus utile

1. Adaptateur \`scene-plan V1 -> StoryGraph / objets / événements / MasterTimeline\` qui ne repose pas sur les mots du titre et n'invente pas de faits physiques.
2. Raccordement au moteur de rendu science par feature flag avec fallback des anciens épisodes.
3. FoleyEngine réutilisable et mixage contrôlé (ducking, LUFS, pic vrai).
4. Première vidéo originale narrée Kokoro avec un acteur persistant, musique et SFX, suivie d'un audit visuel/sonore réel.

**Principe de fermeture** : la tranche d'infrastructure peut être fusionnée après tests. La qualité audiovisuelle cible reste non atteinte tant qu'elle n'est pas démontrée par des films complets et une écoute humaine.
