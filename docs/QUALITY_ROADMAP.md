# Plan de travail — Automate-ytb V2 : qualité professionnelle

État examiné : 30 octobre 2026 ; branche main au commit 96328b15350ae055ecbe8d66623e13b3130cd812 (PR #102).

## Objectif

Produire des vidéos originales et fonctionnelles, montées automatiquement avec narration naturelle, véritables mouvements, sous-titres, audio cohérent et médias autorisés, pilotables depuis Android. Priorité aux méthodes gratuites et open source : Python, Pillow et FFmpeg. Le projet utilise déjà des rigs 2D pour chouette/renard/lapin/chat, décors, météo, caméra, rendu MP4 H.264, narration et contrôles éditoriaux. Ce ne sont pas des rigs 3D ou un niveau AAA certifié.

## Ordre des chantiers avec critères de sortie

| Phase | Problème principal | Travail | Critère de sortie |
| --- | --- | --- | --- |
| P0 — fiabilité | Le contrôle visuel inspecte seulement les premières 18 secondes | Échantillonner début, milieu, fin ; inspecter des MP4 réels ; conserver les rapports | Fin noire détectée dans une vidéo longue, diagnostic horodaté, tests FFmpeg/FFprobe et CI réussis |
| P1 — animation | Rigs 2D articulés encore limités | Affiner poses, anticipation, appui, récupération, orientation et transitions | Comparer des images vidéo décodées pour chaque action, préserver les timecodes, pas de régression |
| P2 — graphismes | Décors et personnages moins détaillés que le niveau cible | Bible artistique, éclairage, matériaux, cohérence des plans, lisibilité mobile | Galeries jour/nuit/biomes et revue humaine de vrais exports, provenance des assets vérifiable |
| P3 — voix et montage | La synthèse et la synchronisation peuvent manquer de naturel | Vérification Kokoro, débit, pauses, niveaux EBU R128, alignement par phrases | MP4 avec voix et musique écoutées, durée vérifiée, sous-titres et niveaux mesurés |
| P4 — narration et scènes | Risque de scènes répétitives et storyboard trop générique | Sélection de plans/actions motivée par la narration, contrôle de diversité, transitions cohérentes | Aucune intrigue inventée, détection des répétitions, droit des médias documenté |
| P5 — exploitation Android | L'exécution doit rester simple sans PC | Actions manuelles reproductibles, exports accessibles, bons diagnostics | Artefacts vidéo, son, galerie et rapports disponibles avec documentation exploitable |

## Méthode de développement

1. Inspecter main et les PR avant chaque modification ; corriger tout blocage existant.
2. Livrer une fonctionnalité cohérente, complète et testable par PR, sans empiler des ébauches.
3. Avant toute fusion, exécuter les tests d'intégration pertinents et les contrôles réels MP4/audio ; CI verte exigée.
4. Mesurer le coût et le temps des rendus, la cohérence des images, la fluidité, la sortie audio et la reproductibilité.
5. Préserver narration, timecodes, droits, métadonnées, empreintes SHA-256, cache et publication avec contrôle humain.
6. Examiner les candidats dbrckk/star-list sans importer de médias ou instructions tiers non licenciés ou non vérifiés.
7. Distinguer ce qui est réalisé, mesuré et validé de ce qui reste esthétique et nécessite une revue humaine.

## Première livraison : contrôle visuel sur l'ensemble de la chronologie

Le contrôle historique décodait uniquement les 18 premières secondes. La stratégie P0 inspecte jusqu'à 18 secondes au total, réparties en trois fenêtres de six secondes au début, au milieu et à la fin des vidéos longues. Chaque fenêtre est analysée séparément : les coupes entre fenêtres ne provoquent pas de faux flashs. Les rapports indiquent les temps réellement échantillonnés et gardent les compteurs historiques.

Cela **ne certifie pas** les intervalles non échantillonnés. La validation humaine de la vidéo reste nécessaire.

## Sources de référence

Les ressources de star-list utiles à la suite incluent PoseMy.Art pour l'étude de poses, SHOT.CAFE pour le cadrage et Sakugabooru pour le rythme de l'animation. Elles sont des références, pas des licences de réutilisation. Blender pourrait fournir des poses ou assets originaux, sous réserve d'intégration, de budget et de compatibilité réels.
