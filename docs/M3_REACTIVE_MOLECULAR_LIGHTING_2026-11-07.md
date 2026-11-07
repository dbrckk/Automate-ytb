# M3 — Impacts moléculaires et éclairage local réellement interactif

Date : 7 novembre 2026. Évolution après fusion de la PR #209 (caméras 3D dirigées par l'action).

## Problème inspecté

Le renderer `scripts/blender_aurora_stage.py` possède déjà 18 molécules, dix électrons et dix photons, ainsi que des collisions temporellement déphasées. Les molécules gonflent à l'impact; néanmoins, les deux sources lumineuses principales (key/rim) demeurent fixes. Le spectateur peut voir les particules se déplacer, mais il manque une conséquence lumineuse locale immédiatement lisible.

## Amélioration implémentée

- **20 véritables lumières ponctuelles Cycles** : dix dans la scène `collisions` et dix dans `emission`. Elles ne sont pas des superpositions 2D.
- Chaque source est positionnée au milieu des deux atomes mobiles de sa molécule cible. À chaque pose, la position de la vraie lampe bpy suit la molécule.
- L'énergie reste **nulle avant l'arrivée de l'électron**, atteint un maximum à l'instant d'impact déjà défini pour l'électron et décroît ensuite de façon exponentielle. Le motif explique l'énergie libérée et accompagne le photon émis.
- Les impulsions sont colorées différemment selon collision et émission (bleu/violet, vert/violet/rouge) avec puissance bornée; ces couleurs demeurent illustratives, pas une simulation de raies spectrales.
- Les autres scènes ne reçoivent pas de lumières d'impact.
- `aurora_impact_lighting.py` contient la logique déterministe gratuite, testable sans Blender.

## Preuve et assurance qualité

Dans le **vrai objet bpy de chaque scène**, avant les rendus Cycles coûteux :

1. vérifier que chaque lampe est éteinte au début;
2. placer l'animation au temps exact de l'impact et vérifier une intensité élevée **ainsi que la position exacte au milieu des atomes animés**;
3. déplacer le temps de 0,25 de la séquence et vérifier la décroissance de l'éclairage.

Le manifeste `sceneDetails` expose `localImpactLights` et `reactiveImpactLightEvents`, vérifiés par `BlenderAuroraStage`. Les anciennes vidéos 3D restent lisibles; les nouveaux champs incomplets, incohérents ou déclarés dans une mauvaise scène sont refusés. Les tests incluent les vingt impacts temporels, la décroissance et les preuves invalides.

**Condition de fusion :** CI générale verte **et** workflow complet Aurora original 3D Blender/Cycles, narration Kokoro anglaise, sortie MP4 9:16 H.264/AAC et QA réussis **sur le dernier SHA**. Voir les artefacts du workflow pour juger la visibilité réelle sur Android; une exécution technique réussie ne vaut pas appréciation esthétique ni autorisation de publication.

## Prochaines étapes

- Visionner MP4 avant/après et vérifier absence de scintillement gênant ou surexposition.
- Ajuster les puissances et matériaux uniquement sur la base du rendu Cycles inspecté.
- Continuer à améliorer les interactions éclairage–environnement, les transitions causales et la cadence effective en images 3D originales si le coût CPU le permet.
