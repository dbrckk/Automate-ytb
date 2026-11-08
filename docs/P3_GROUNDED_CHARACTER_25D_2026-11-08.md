# P3 — animation 2.5D des personnages : rig à deux os et appui au sol

**Date :** 8 novembre 2026. **Base :** `main` `2e511a72e93f9b53114e0928676ea20912580306`. **Statut : prototype intégrable avec workflow réel, qualité de rendu soumise à inspection.**

## Problème vérifié dans le dépôt

Les animaux originaux utilisent des sprites Pillow indépendants de la tête, des oreilles, du corps, de la queue et des pattes ; la production cartoon historique déplace les jambes par expressions FFmpeg dans `choreography.py`. Même si une phase d'appui bloque déjà certaines coordonnées, **le genou n'est pas géométriquement recalculé** à partir de la position du bassin et du pied. Cela limite les interactions et peut produire un membre visuellement déconnecté lors de mouvements longs.

## Fonctionnalité ajoutée

- `automate_ytb/rig25d.py` : vrai solveur géométrique IK analytique à **deux os de longueur constante**. Pour chaque patte, l'articulation du genou découle des coordonnées du bassin et du point d'appui, avec sélection de sens de flexion et refus des positions impossibles.
- Marcher sans glisser : pour 62 % du cycle, la patte reste **fixe en coordonnées monde** pendant que le corps avance. Pendant le retour, le pied rejoint l'appui suivant selon une trajectoire en arc, continuellement raccordée et à vitesse nulle aux limites du mouvement. Les deux pattes ont un déphasage d'une demi-période.
- `automate_ytb/forest25d.py` : **réutilise les sprites originaux** du renard (corps, oreille gauche/droite, queue) et les compose avec les membres IK dans le vrai moteur `Scene25D` déjà fusionné. Décor procédural original à plusieurs profondeurs : ciel, nuages, crêtes, arbres, prairie, ombre de contact, renard IK, impacts au sol et herbes de premier plan. Les plans de végétation se déplacent avec une parallaxe Z différenciée.
- `scripts/render_25d_character_pilot.py` : production **7,2 s / 216 frames réellement composées en 1080×1920 à 30 fps**, encodées H.264/AAC par FFmpeg ; soundtrack PCM original, sans média tiers. Trois images de contrôle, SHA du MP4, décodage intégral, mesure des longueurs des os et de la dérive des pieds au sol.
- `tests/test_rig25d.py` : longueur exacte des os, appui fixe malgré déplacement du corps, cadence alternée, continuité des pas, images réellement différentes et refus des données dangereuses.
- `.github/workflows/p3-25d-character-pilot.yml` : rendition autonome sur GitHub Actions gratuit, contrôle des pieds et mise à disposition de l'artefact MP4.

## Limites délibérées

- Cette vidéo constitue **un pilote d'animation**, pas un épisode narré professionnel : pas de voix Kokoro, ni de synchronisation labiale dans ce pilote ; ne pas la présenter comme une vidéo finale TikTok.
- Les mouvements restent dessinés en 2D, calculés dans un espace 2.5D avec parallaxe ; pas de géométrie 3D réelle ni de simulation musculaire.
- L'ancienne pipeline de rig FFmpeg continue de fonctionner **sans modification**. La migration de ses quatre animaux vers `rig25d` sera progressive après confirmation du MP4 pilote ; ne pas la considérer terminée.
- L'analyse des pieds garantit une stabilité numérique pour les phases d'appui ; **la sensation visuelle** de poids, la qualité du décor et le contact réel nécessitent toujours une revue vidéo humaine.

## Critères de sortie P3

1. Test de solveur IK : écart de longueur des os inférieur à 0,001 pixel, refus des cibles inaccessibles, et point d'appui fixe pendant toute une phase de soutien.
2. Vérification sur **vrai MP4** : 1080×1920, 30 FPS, 216 frames, H.264 + audio AAC, audio et vidéo entièrement décodables, hash SHA256, trois captures temporelles différentes.
3. Test visuel mobile : aucun glissement de pied visible, genoux qui plient réellement avec le déplacement du buste, jambes qui restent connectées, ombre sous le renard, vegetation d'avant-plan distincte.
4. Budget rendu GitHub Actions vérifié ; pas d'échec de tests du dépôt ni de dégradation des autres modes de production.
5. Les résultats mesurés sont enregistrés dans `pilot-qa.json` plutôt que déclarés sans preuve.

**Après réussite :** P3.1 généralise le rig aux lapins/chats/chouettes quand la géométrie corporelle s'y prête, intègre la vraie narration PCM aux séquences multi-genres et ajoute les contacts avec objets.
