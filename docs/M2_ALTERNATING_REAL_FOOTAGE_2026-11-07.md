# M2 — Alternance réelle de sources, sans répétition de rushes

## Constat sur le rendu NASA validé après PR #203

Rapport de montage réel : **5 scènes**, sources utilisées dans l'ordre `2022, 2022, 2025, 2025, 2025`. Il n'y a qu'**un seul changement de source**, même si l'audit des blocs spatiaux n'indique aucun quasi-doublon. Les fichiers officiels NASA ont une durée mesurée de **49,560 s** (2022) et **88,033 s** (2025). Les 5 phrases du Short durent 7 s chacune.

Cette évolution s'attaque au manque de variété des prises de vue, **sans inventer de source**.

## Nouvelle option du monteur universel

`python -m automate_ytb.auto_edit ... --source-order interleave`

- `automate_ytb/source_scheduler.py` planifie le fichier de chaque scène avec une recherche bornée et déterministe (`beam_width <= 128`). Il favorise les changements de source et l'utilisation d'un ensemble diversifié de rushes réellement disponibles, tout en respectant la durée totale propre à chaque enregistrement.
- `auto_edit.select_interleaved_excerpts` attribue les fenêtres temporelles *dans chaque source* en préservant l'ordre chronologique de cette source et en interdisant le réemploi d'une plage déjà consommée. Les candidats restent évalués à partir d'images FFmpeg réellement décodées (exposition, mouvement, composition).
- Le mode historique `--source-order chronological` reste le **défaut**, sans modification des projets existants.
- Le rapport contient `sourceOrderingStrategy`, `sourceSchedule`, `sourceChronologyPreserved` et `sourceSegmentsNonoverlapping`.
- Le workflow NASA utilise désormais le mode intercalé et bloque si le MP4 fini n'alterne pas suffisamment les deux prises de vue ou si un rush a été réutilisé.
- Des tests d'ordonnancement, de capacité, d'absence de doublon temporel et de rendu réel FFmpeg multi-source accompagnent la modification.

**Important :** l'algorithme n'identifie pas la signification des images. L'alternance de prises de vue améliore potentiellement le rythme et la variation visuelle, mais ne prouve pas que chaque plan correspond au texte prononcé. Aucune intégration payante, vidéo fabriquée ni traitement de voix supplémentaire.

## Critères de validation

Le test GitHub NASA doit produire et décoder un **nouveau** MP4 1080×1920, H.264/AAC, Kokoro anglais, sous-titres incrustés, 5 scènes et 2 sources, avec **au moins 3 changements de source sur 4 raccords**, tout en maintenant les contrôles pré/post-montage et l'absence de publication automatique. Ne pas fusionner cette PR si le rendu réel ou la validation générale échoue.
