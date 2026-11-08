# Automate-ytb — Feuille de route de production graphique et animation 2.5D

**Date :** 7 novembre 2026. **Base de l'audit :** `main` à `bf3edcdeeb52115c1c0b3b4017efdec9c125f948`. **Statut : plan de travail, pas fonctionnalités terminées.**

## Objectif et résultat attendu

Transformer la production actuelle (dessin 2D procédural + certaines plaques de parallaxe + animations par sujet) en **mise en scène 2.5D authentique** : chaque plan comporte un espace de profondeur explicite, des calques opaques/transparents, une caméra indépendante, des personnages ou objets articulés, des occultations correctes, des ombres/éclairages liés à l'action et une chronologie cohérente avec la narration. Le résultat doit montrer **des actions et leurs conséquences**, et non simplement faire défiler de jolies images.

Sortie prioritaire : **Shorts 9:16, 1080×1920, 30 images originales/seconde pour la composition 2.5D, H.264/AAC**, voix Kokoro EN/FR et sous-titres calés sur l'audio. Les plans Blender/Cycles restent des moteurs optionnels spécialisés, sans prétendre que leurs images interpolées sont des rendus géométriques natifs 30 i/s. Préserver 16:9 et les montages de rushes réels avec un routeur explicite.

Contraintes : gratuit/open source, exécution reproductible GitHub Actions CPU si raisonnable, utilisation Android sans commandes locales, pas d'assets tiers sans licence, pas de simulation de profondeur inventée à partir d'une image plate, pas de dépendance à une API payante, pas de publication automatique. La fiabilité et le vrai MP4 passent avant les effets décoratifs.

## État réellement inspecté

| Composant actuel | Réutilisation | Lacune pour la nouvelle cible |
| --- | --- | --- |
| `depth_layers.py` et `ground_contact.py` | Premier plan, oscillation, ombre de contact des animaux | Plaques limitées ; pas de scène de profondeur commune ni occultations spatiales générales |
| `joint_motion.py`, `animated_owl.py`, `animated_forest.py` | Poses/appendices et animations des personnages | Les angles restent des expressions déterministes ; **pas de vraie IK** pour pieds/mains/contacts |
| `cinematic_stage.py` et `science_stage_director.py` | Poses caméra, recadrage, impulsions causales | Caméra dépendant des moteurs et sujets ; difficile de déplacer ensemble plusieurs calques à profondeurs différentes |
| `science_lightning_fx.py`, `science_volcano_lighting.py`, `atmospheric_light.py` | Éclairage d'action, reflets, ombres et atmosphères | Solutions locales sans éclairage/relighting multi-calques réutilisable |
| `sprite_supersampling.py`, `science_motion.py` | Antialiasing 2x, dessins originaux à résolution de sortie | Détails et matériaux variables selon scène, rasterisation parfois trop simple |
| `science_audio_cues.py`, `science_portrait.py` | Événements repérés par phrases Kokoro, action + composition Shorts | Les actions restent majoritairement spécifiques au sujet ; pas de contrat de chorégraphie commun |
| `motion_interpolation.py` | Interpolation optique de plaques Blender validée sur des rendus de référence | N'ajoute pas de vraie géométrie ni de nouveaux détails ; artefacts possibles |
| `production.py`, `episode.py`, `qa_bundle.py` | Orchestration, encode FFmpeg, SHA, revues visuelles et validation | Aucun contrat complet de calques 2.5D partagé par cartoons/science |

**Dépendance immédiate :** la PR [#215](https://github.com/dbrckk/Automate-ytb/pull/215) sur l'éclairage spatial des éclairs était **ouverte** lors de l'audit ; vérifier sa fusion/son dernier SHA avant de superposer d'autres modifications aux mêmes fonctions. La PR #213 de synchronisation narration/action est fusionnée.

## Contrat technique cible : une scène 2.5D par plan

Créer un schéma versionné `Scene25D` et un compositeur déterministe **réutilisés par science, cartoons et motion design**. Pas de remplacement massif du moteur vidéo en une seule PR.

```text
narration et timecodes PCM
         │
storyboard (action, personnages, conséquence, angle)
         │
sources originales/licenciées → préparation des couches
         │
Scene25D : caméra, acteurs/rigs, couches Z, masques,
           pivots, matières, lumières, trajectoires, événements
         │
animation paramétrique à l'instant t (frames réellement recalculées)
         │
compositeur 2.5D : occlusion → ombres → lumière → profondeur → color grade
         │
encodeur existant FFmpeg → MP4 + SRT/VTT + QA + livraison Android
```

Schéma minimal à formaliser dans le code : `id`, `source` et `source_sha256`, `license` / propriété, `z`, `transform`, `pivot`, `alpha_mask`, `optional_depth_mask`, `optional_normal_map`, `blend_mode`, `camera`, `actor_id`, `parent_id`, `keyframes`, `start_ms/end_ms`, `animation_clock`, `event_cues`, `render_profile`. Seuls des champs et animations **sur liste blanche** sont autorisés ; jamais d'expressions FFmpeg/Python arbitraires provenant d'un script utilisateur. Les calques facultatifs absents ne doivent pas être simulés silencieusement : garder le moteur d'origine et signaler le fallback.

**Définition précise du 2.5D :** dessin, sprites et effets 2D placés sur différents plans Z avec perspective/parallaxe, occlusion et caméra cohérentes. Ce n'est ni un volume 3D entièrement reconstructible, ni une simple caméra Ken Burns sur une image unique.

## Feuille de route priorisée — une PR complète et mesurable à la fois

| Étape | Priorité | Travail livré dans le code | Gain visible et condition de sortie |
| --- | --- | --- | --- |
| **P0 — Preuves et référence** | Bloquante | Fixer deux films de référence de 30–40 s avec mêmes scénarios/voix avant/après ; captures par plan, traces de rendu, SHA, facture CPU/RAM et défauts observables ; isoler le pilote du code PR #215 | Comparaison honnête, pas de progrès esthétique déclaré sur la seule base de tests |
| **P1 — Véritable compositeur multi-Z** | Très haute | `scene25d.py`, `compositor25d.py` : plans ciel/fond/décor/acteur/avant-plan/FX, transparence prémultipliée, ordre Z, masques et clipping validés, cache des plaques statiques, streaming vers FFmpeg | Au moins 4 plans de profondeur **réellement indépendants** sur le pilote ; passage devant/derrière vérifié, sans contour alpha noir/blanc |
| **P2 — Caméra 2.5D cinématographique** | Très haute | `camera25d.py` : translation/zoom/tilt modéré, trajectoires courbes, easing C1, profondeur parallaxée par Z, focus acteur, garde-fous de cadre vertical et sous-titres | Un travelling rend le déplacement différentiel perceptible ; aucun trou/étirement/acteur coupé sur le MP4 |
| **P3 — Animation d'acteurs crédible** | Très haute | `rig25d.py` : hiérarchie parent/enfant, pivots exacts, animation pose → anticipation → action → retour, IK 2 os si applicable, pieds ancrés, inertie oreilles/ailes/queues, regard et bouche déjà présents réutilisés | Marche : pieds sans glissement pendant appui ; saut : réception physique et ombre changeant avec hauteur ; personnage ne flotte pas |
| **P4 — Lumières, matériaux et atmosphères** | Haute | `lighting25d.py` : ombres propres, lumière directionnelle + locales, normals/depth maps **uniquement si disponibles**, ambient occlusion stylisée, bloom borné, brume Z, réflexion et palette par scène | L'éclair illumine nuage/sol/acteur **au bon instant** ; cohérence jour/nuit ; pas de voile blanc uniforme ou couleurs brûlées |
| **P5 — Interactions causales et FX** | Haute | `effects25d.py` : contacts, poussière/eau/pluie, traînées, impacts, particules, occultation de fumée, effets synchronisés avec la phrase narrée ; durée de vie et densité bornées | On voit cause → contact → réaction → conséquence, pas seulement des particules génériques |
| **P6 — Direction artistique unifiée** | Haute | Bible de couleurs, matériaux et lignes, profils science/cartoon/documentaire/promo, lumière et contraste normalisés, figures nettes, foreground moins répétitif, supersampling sélectif | Continuité visuelle entre 5 plans, sujet lisible sur écran Android ; pas de texture de base évidente |
| **P7 — Intégration multi-genres et livraison** | Moyenne après P1–P6 | Routeur explicite : science 2.5D, cartoon 2.5D, footage documentaire, Blender 3D ; format 9:16 puis cadrage 16:9 natif, Actions, cache/reprise, MP4/SRT et revue | Même contrat de sortie utilisable depuis Android ; un mode non compatible reste fonctionnel sans régression |

### Stratégie d'exécution

**Pilote n°1 :** `The Secret Life of a Lightning Bolt`, 5 scènes, 9:16. Existant : atmosphère, éclairs, terrain, pluie, voix anglaise, sortie MP4 vérifiable. Première transformation : décomposer `science_lightning.py` et `science_lightning_fx.py` en Z distincts sans changer le scénario, puis un travelling et des masques d'occlusion. Cela permettra de juger l'amélioration à images/voix comparables, pas de comparer deux sujets sans rapport.

**Pilote n°2 :** une scène narrative **renard/lapin/chat/chouette** dans un décor existant, avec marche, saut, interaction et premier plan croisant le personnage. C'est le test de généralisation de la 2.5D et du rig/IK, non une illustration statique.

**Pilote n°3 :** une scène scientifique océan/aurore, en conservant le rendu Blender existant lorsqu'il apporte plus de valeur. Le système ne doit pas dégrader les vraies animations 3D.

**Ordre des livraisons :** établir P0 → finir P1 + rendre une vidéo pilote → P2 + rerender → P3 + film personnage → P4 → P5 → P6 → P7. Les PR liées à un même fichier sont séquentielles, avec fusion seulement après vérification de leurs **SHAs exacts**. Éviter les PR géantes transversales et les fonctions factices.

## Profils de rendu et performance

- **Développement interne seulement** : rendu réduit pour déboguer le système ; ne pas le présenter comme vidéo finale.
- **Film livré** : rendu réellement animé à **30 i/s**, 1080×1920, H.264/AAC, narration et sous-titres vérifiés ; on ne qualifie pas une interpolation de photographies d'animation 30 i/s.
- **CPU-first** : Python + Pillow déjà installés, OpenCV/NumPy (extra `[motion]`) lorsque nécessaires, FFmpeg pour l'encodage ; ne pas ajouter un runtime/node/GPU avant une comparaison coût/qualité démontrant un bénéfice.
- **Accélérations** : géométrie/raster statique en cache, régions d'image affectées, flou à résolution inférieure puis upscale, débit de frames streamé sans stocker des milliers de PNG, effets coûteux sélectifs.
- **Objectif de performance proposé, non encore mesuré :** temps de génération sur GitHub Actions au plus ~2× le rendu de référence et mémoire stable, à réévaluer avec mesures exactes de P0. Aucun sacrifice implicite de la résolution ou de la qualité pour respecter cet objectif.

## Qualité et conditions de fusion

Mesures **proposées**, à ajuster après baseline :

| Domaine | Vérification automatisée / humaine |
| --- | --- |
| Couverture 2.5D | Chaque plan pilote possède 4–7 calques visibles indépendants et des Z documentés ; différences de mouvement mesurées dans le MP4 ; absence de remplissage artificiel |
| Contact et occlusion | Aucun masque inversé ; acteurs devant/derrière au bon moment ; points de contact sans dérive visible ; test d'images clés avant/après |
| Mouvement et montage | Génération de frames à intervalles réels ; aucune séquence de plusieurs secondes figée lorsque le script demande un mouvement ; transitions sans sauts visibles ; pas de clignotements |
| Caméra et lisibilité | Sujet dans les limites prévues, titres/captions dans zones sûres, focalisation sans recadrage abusif, profondeur discernable sur écran de téléphone |
| Lumière et couleurs | Exposition cohérente par beat, noirs non bouchés, pas de clipping large dans les éclairs, reflets attachés aux sources/objets |
| Audio et vidéo | MP4 intégral décodable ; FPS/codec/durée/SHA vérifiés ; voix Kokoro PCM, musique autorisée, SRT synchronisés ; règles de non-publication inchangées |
| Fiabilité et coût | Tests pertinents au nouveau moteur + tests d'intégration avant jalon ; workflow réel vert au SHA livré ; aucune régression des autres sujets ; durée/ressources rapportées |
| Revue artistique | 2 planches + MP4 avant/après, visionnage téléphone ; notation séparée de l'image, de l'animation, de la mise en scène, de la voix et de la cohérence scientifique |

Échelle éditoriale suggérée (0–5 par axe) : **qualité de l'illustration, profondeur, fluidité, contacts, éclairage, lisibilité, synchronisation voix/action**. Chaque évaluation doit être accompagnée d'une image/vidéo de preuve, pas d'une note sans inspection. Revue externe des faits scientifiques et des licences avant publication.

## Risques et garde-fous

1. **Fausse 2.5D :** ne jamais présenter une seule image zoomée comme scène 3D ; exiger des couches et des occultations démontrées.
2. **Scintillement et halos alpha :** composition en alpha prémultiplié, contraste/blur bornés, test sur fond sombre et clair.
3. **Coût CPU :** l'effet visuellement discret ne justifie pas un rendu 10× plus long ; utiliser profiler/étalonnage et couper les passes inutiles.
4. **Masques d'image importée :** aucune segmentation automatique aveugle ; si confiance insuffisante, conserver la vidéo existante, signaler la limite et ne pas inventer la géométrie.
5. **Droits et sécurité :** images, depth/normal maps et sons disposent d'une provenance ; scripts d'utilisateurs restent des données validées ; aucune exécution de code via JSON/expressions non contrôlées.
6. **Confusion technique vs artistique :** CI verte vérifie fonctionnement/contrats, pas le niveau « professionnel ». Une inspection des MP4 reste obligatoire.

## Première prochaine PR d'implémentation (après validation de ce plan)

`feat/25d-compositor-layer-contract` :

1. Formaliser `Scene25D` (schéma, contraintes de chemins et licences, Z/alpha, dimension/timecodes) + tests de refus.
2. Implémenter **une seule vraie scène** lightning en couches indépendantes, pipeline caméra + occlusion + rendu natif à 30 i/s ; préserver la narration.
3. Produire MP4 **avant/après du même script**, feuilles de contact et métriques CPU/mémoire, puis inspecter les différences.
4. Fusionner uniquement lorsque les deux rendus sont décodables, que les calques se croisent correctement, que les workflow tests passent et que le gain visuel est constaté.

**Non inclus dans ce commit :** rendu 2.5D nouveau, animations IK, nouvelles images ou qualité artistique déjà démontrée. Ce document définit le contrat d'exécution et ses conditions de preuve.
