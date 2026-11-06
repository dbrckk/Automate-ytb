# M2 — Diversité optique pendant la sélection des extraits

Le moteur `auto_edit.select_excerpts` comparait auparavant seulement exposition, contraste et mouvement. Deux plans consécutifs pouvaient donc obtenir un bon score technique tout en présentant pratiquement la même composition.

Cette évolution réutilise les pixels **réellement décodés** des candidats FFmpeg (sans second passage) pour calculer une signature spatiale 8×6. Un candidat trop proche du plan précédent reçoit une pénalité optique de 0,22 point, en conservant la qualité technique comme critère principal. Les positions candidates restent dans la capacité temporelle de leur source, avec ordre chronologique et **sans chevauchement**.

La pénalité est indiquée dans `technicalReview.diversitySelectionPenalty` et la comparaison dans `adjacentOpticalComparison`. Le rapport d'édition expose `opticalDiversityAwareSelection=true`. Le contrôle M2 final `shot_diversity.py` reste indépendant : il mesure les images après recadrage, transitions et sous-titres.

**Limites** : ce calcul est optique, non sémantique ; il ne reconnaît ni objets, ni événements, ni correspondance narration-image. Une forte différence de couleur n'est pas une preuve de diversité éditoriale. Si une seule prise est utilisable, le pipeline ne fabrique pas de nouvelles images.

Les tests couvrent le choix d'une alternative visuellement distincte même avec un score technique légèrement inférieur, et le maintien des bornes chronologiques. La CI existante contrôle les montages réels FFmpeg et le rendu NASA avec Kokoro.
