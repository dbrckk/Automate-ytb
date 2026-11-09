# P4.9 — Cinéma vertical : caméra physique et habillage allégé

**9 novembre 2026 — Automate-ytb**. Reprise du dernier MP4 réel
« Can Lightning Travel Upward From a Tower? » après P4.8.

## Audit de l'ancien export

Le storyboard prouve que cinq scènes différentes sont animées : charges,
canal descendant, décharges ascendantes, retour lumineux, tonnerre.
Cependant, le **titre complet est redessiné dans chacune des cinq scènes**,
en concurrence avec la zone de visualisation. Dans l'ancien moteur, la
caméra se déplace et zoome essentiellement horizontalement ; son axe vertical
reste contraint autour du centre alors que l'éclair descend puis remonte.
Le rendu ressemble encore trop à un enchaînement de diapositives scientifiques.

## Correctifs réalisés

- **Accroche unique** : le titre principal n'apparaît que dans le premier
  plan, avec révélation puis fondu de sortie progressifs. Le titre ne revient
  pas à chaque changement de scène.
- **Cartouches de chapitre** : les cinq séquences reçoivent un intitulé court,
  leur numéro et une très fine ligne de progression. L'habillage passe
  entièrement dans la zone supérieure y=112–300, hors animation et sous-titres.
- **Économie CPU** : les plaques typographiques originales sont mises en cache.
  Seule leur opacité varie à chaque frame ; aucun service payant, aucune
  image de banque, aucun nouveau rendu de texte à chaque image.
- **Caméra cinématique physique** : le cadrage suit effectivement l'axe Y :
  le `leader` descend dans le nuage ; le `return stroke` remonte vers le
  ciel ; le tonnerre revient à un cadrage plus large. Les positions sont
  interpolées et limitées par le crop 1080×930 → 1080×1380 pour ne montrer
  ni bord noir ni étirement de l'image.
- **Compatibilité** : l'habillage Aurora et Volcano reste inchangé ; les
  pistes Kokoro, le sous-titrage lié au PCM et la lumière P4.8 sont conservés.

## Contrôles de production

Les tests de caméra vérifient la direction réelle des déplacements sur
chaque plan, la continuité à 30 FPS, les limites de cadrage et la validité
des paramètres. Les tests d'habillage vérifient la transition de l'accroche,
l'absence de répétition, l'immobilité des en-têtes de chapitres,
l'intégrité des couches du film et des sous-titres, les cinq intitulés
EN/FR et la stabilité du cache.

Les workflows de Shorts Lightning et Upward-Lightning sont reliés aux
nouveaux fichiers : chaque modification génère un MP4 H.264/AAC avec voix
Kokoro sur GitHub Actions. Sur `main`, les résultats réussis passent par
le **système de livraison GitHub Releases** à lien direct et empreinte
SHA-256, puis l'historique `docs/video-history.json`.

**Important :** une validation technique ne remplace pas le contrôle humain
de l'artistique, de l'écoute et de la rigueur scientifique avant publication
sur TikTok/YouTube.
