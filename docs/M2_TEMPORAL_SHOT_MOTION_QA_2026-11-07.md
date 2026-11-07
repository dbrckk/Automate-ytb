# M2 — Contrôle temporel des plans du MP4 réel (7 novembre 2026)

## Problème vérifié

Le contrôle précédent de `shot_diversity.py` décodait uniquement une image au milieu de chaque scène du Short effectivement encodé. Cela permet de constater les variations **entre** plans, mais pas de détecter un long plan presque immobile, un gel d'image ou un effet de diapositive malgré un fichier vidéo parfaitement valide.

## Évolution implémentée

La commande reste inchangée :

```bash
python -m automate_ytb.shot_diversity \
  --video build/nasa-short/render/preview-captioned.mp4 \
  --plan build/nasa-short/scene-plan.json \
  --edit-report build/nasa-short/auto-edit-report.json \
  --out build/nasa-short/render/shot-diversity-qa.json
```

- Pour **chaque** scène : décodage de vrais pixels du MP4 à 20 %, 50 % et 80 % de sa durée (au lieu d'un seul point).
- Mesure de la variation moyenne absolue des pixels en niveaux de gris entre les trois images, limitée aux 75 % supérieurs de l'image pour réduire les faux mouvements causés par les sous-titres en bas.
- Identification des plans optiquement quasi statiques lorsque les deux différences sont inférieures à 1,5 niveau de gris. Le seuil génère un **avertissement**, pas une décision de publication ni un refus automatique, faute de référence artistique fiable.
- Rapports JSON : `temporalMotionAudited`, `temporalSamplesPerScene`, `temporalAuditedSceneCount`, `nearStaticSceneCount`, `temporalSampleSeconds` et `temporalPixelActivity` par scène.
- Workflow NASA : vérifie la présence de **trois vraies mesures par scène** sur le MP4 1080×1920 avec Kokoro et sous-titres déjà incrustés, tout en conservant ses contrôles de provenance, de voix et de diversité des rushes.
- Interface historique `analyze_frames(frames, source_names=...)` conservée : les appels sans échantillons temporels fonctionnent toujours.

## Limites explicites

Ce n'est **pas** une estimation de mouvement physique ni une compréhension de scène. Un panoramique de caméra, un zoom sur une photographie, un changement de luminosité ou une incrustation haute peuvent augmenter les différences sans aucune animation de personnage/objet. Trois points de mesure ne garantissent pas qu'aucun gel bref n'existe entre les échantillons. Les cinéastes doivent toujours vérifier le mouvement visible, la relation narration-image et l'intérêt éditorial.

## Validation attendue

1. Tests de non-régression : scènes statiques repérées, variation réelle mesurée, zone de sous-titres ignorée, données invalides rejetées.
2. Pipeline général vert sur la branche exacte.
3. Rendu NASA réel sur la branche exacte avec rapport temporel complet; toujours non publié.
4. Révision visuelle/sonore humaine avant diffusion.

**Amélioration suivante après ce jalon :** exploiter les avertissements comme rétroaction de montage **avant** le rendu final, en recherchant des fenêtres de source plus vivantes ou en modifiant le plan, sans boucle, duplication ou pseudo-animation trompeuse.
