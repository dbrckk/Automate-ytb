# Objectif de référence — infographies scientifiques animées

Le fichier de référence fourni par l'utilisateur (`3182.mp4`) a été inspecté **localement**, sans téléverser ni republier ses images ou sa bande sonore dans le dépôt.

## Mesures de la référence

- 32 secondes, 1920 × 1080, 30 images/seconde, H.264.
- Son stéréo AAC, voix et bande sonore intégrées dans la référence.
- Plans explicatifs distincts : planète éclairée, villes et atmosphère, vagues océaniques, comparatif jour/nuit, chiffres et libellés.
- Direction artistique cohérente : bleu nuit, cyan, accents dorés, typographie hiérarchisée, légendes à fort contraste.
- Animation à plusieurs niveaux : mouvement des éléments, courbes et particules, croissance de schémas et transitions de composition.

Ce benchmark décrit des **objectifs visuels**, pas une autorisation de copier les assets, le script ou l'audio.

## Première intégration : style `science`

Sélectionnez **One-click YouTube preview (free)** → **style : science** → **résolution : 1080p** → **voix : kokoro** → **musique : ambient**. Fournir une narration personnelle en français ou anglais, avec une idée par plan (par exemple cinq phrases pour 30 secondes / six secondes par plan).

Le nouveau moteur `automate_ytb/science_motion.py` dessine un globe original **schématique**, des courbes orbitales, des panneaux d'air et d'océan et un comparatif éclairage/obscurité. Les mots du script déterminent les modes de composition. Les valeurs scientifiques doivent provenir du scénario vérifié, jamais être inventées par les visuels.

- Génération de scènes image par image à **30 i/s**, avec encodage H.264 via FFmpeg et adaptation 720p ou 1080p.
- Aucun asset tiers, abonnement, synthèse IA d'image ni matériel WebGL n'est nécessaire pour ce premier mode.
- Le pipeline existant conserve les narrations Kokoro/eSpeak, la musique originale, les sous-titres et les contrôles QA.
- Contrôle d'intégrité par empreinte de l'art et cache de rendu invalidé lors des révisions.

## Écarts non résolus vers la qualité cible

1. **Cartographie et matières** : la planète est une illustration sphérique originale simplifiée, sans nuages volumétriques ni texture géographique fidèle.
2. **Grammaire visuelle** : seuls quatre types de plans scientifiques sont disponibles ; il faut des schémas adaptés à chaque notion.
3. **Cinématique** : le mouvement continu est réel, mais le moteur ne reproduit pas encore des caméras 3D cinématographiques, de la simulation physique ou des rotations WebGL.
4. **Typographie** : un court extrait animé habille chaque plan ; le texte complet reste disponible dans les SRT/VTT, sans synchronisation phonème par phonème.
5. **Direction sonore** : une voix naturelle et une bande-son cohérente nécessitent un contrôle d'écoute humain ; les tests techniques ne suffisent pas à garantir le rendu perçu.
6. **Exactitude** : le modèle d'illustration terrestre ne constitue pas une simulation scientifique. Toute affirmation ou valeur est à sourcer avant publication.

**Portée réelle :** première base exploitable pour les scénarios astronomiques et géophysiques centrés sur la Terre, pas un moteur universel capable de traiter fidèlement n'importe quel sujet. Ne pas promettre une équivalence esthétique acquise sans évaluation qualitative du MP4 final.

## Prochaines priorités

- Planification **sémantique** des objets visuels à partir de chaque phrase sourcée, avec diagrammes par thème.
- Assets spatiaux authentiques ou générés sous licence explicite (NASA/ESA, par image et licence), isolés du premier moteur original.
- Courbes d'accélération harmonisées et contrôle de la densité visuelle sur l'ensemble des plans.
- Harmonisation musique, transitions, sous-titres et voix, puis audit vidéo A/B à partir de captures.
