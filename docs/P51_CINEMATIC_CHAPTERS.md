# P5.1 — Plans cinématographiques sans bandeau permanent

## Constat

Les chapitres en haut de l'image restaient visibles durant la quasi-totalité
de chaque plan. Bien que la caméra et les éléments 2.5D soient animés, ces
bandeaux fixes donnent encore un aspect présentation.

## Correction implémentée

Le titre principal n'apparaît qu'à l'ouverture de l'épisode, comme avant.
Chaque chapitre est ensuite introduit en fondu de 320 ms et disparaît
progressivement entre 2,45 et 3,15 secondes. La suite du plan de 6 secondes
montre donc le monde en mouvement sans cartouche statique.

Le texte reste dans la zone de sécurité supérieure, sans toucher à la
narration Kokoro, aux sous-titres synchronisés, aux images 2.5D ni aux
commandes de TikTok/Shorts.

## Contrôles

Les tests contrôlent pour les cinq étapes l'apparition initiale, la
transition douce, l'absence complète de cartouche à partir de 3,2 s,
l'intégrité des zones de vidéo et de sous-titres, et l'immuabilité des
plaques graphiques en cache.

Après validation GitHub et fusion, la modification du fichier
`lightning_editorial25d.py` déclenche automatiquement le rendu original
sur `main`, suivi d'une publication MP4 permanente dans GitHub Releases
et de l'ajout à l'historique.
