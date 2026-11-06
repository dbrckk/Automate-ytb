# P4/P6 — vrais plans verticaux avec suivi optique dans tous les montages

## Changement livrable

L'outil automatique **multi-source** (`automate-ytb-autoedit`) dispose
désormais d'un recadrage intelligent pour **tous les genres documentaires,
fitness, voyage, produit, éducation, gaming et vidéos personnelles**.

Avant : convertir un plan horizontal en Short utilisait principalement
une petite image panoramique centrée, avec du flou du même plan autour.
Cette technique préserve le contexte mais peut évoquer un diaporama.

Après : lorsque les images contiennent suffisamment d'information, le
moteur suit **l'activité visuelle réelle décodée** à l'intérieur d'un
recadrage 9:16 plein cadre. La caméra est limitée en vitesse et en
accélération (même moteur que les rendus sous-marins NOAA).

L'analyse est hors ligne, déterministe et gratuite :
FFmpeg + Python standard, sans GPU, modèle téléchargé, crédits IA
ou service propriétaire.

## Comportement du paramètre

| Option | Fonction | Utilisation |
| --- | --- | --- |
| `--portrait-framing auto` | Recadrage suivi sur plan horizontal actif; préservation si trop sombre, plan déjà portrait ou géométrie inadaptée | **Par défaut dans l'auto-montage** |
| `--portrait-framing follow` | Force la caméra suivie quand les dimensions le permettent | Pour les rushes dont on sait que le sujet reste identifiable |
| `--portrait-framing preserve` | Conserve l'intégralité du cadre au centre avec un fond animé flouté si nécessaire | Texte essentiel ou action répartie sur toute la largeur |

Pour les appels historiques du moteur `production.render`, le défaut
reste **preserve**, afin de ne modifier aucun ancien rendu implicitement.

Les images réellement utilisées sont les clips normalisés,
**SHA256 vérifié avant le rendu**, sans audio caméra.
Les mouvements ne réécrivent pas la narration, les sous-titres
ou le timing des scènes.

Exemple :

```bash
automate-ytb-autoedit \
  --videos prise-1.mp4 prise-2.mp4 \
  --script narration.txt \
  --topic "Deep ocean" --genre documentary \
  --resolution shorts --fps 30 \
  --portrait-framing auto \
  --voice-engine kokoro --language en \
  --rights-note "Original footage owned by the user, cleared for editing" \
  --confirm-rights --output sortie
```

Kokoro nécessite l'installation locale des dépendances facultatives
`.[speech]` et de son modèle libre. Le moteur n'utilise pas eSpeak comme
substitut caché et ne publie rien.

## Preuves inspectables

Le rendu comporte `realFootageFraming` dans `render-report.json`, et
la sortie multi-sources le répercute dans `auto-edit-report.json` :

- Nombre de scènes **follow** et **preserve**.
- Pour chaque plan : mode demandé, mode appliqué, raison du choix.
- Quand le suivi s'applique : images décodées, chemin de caméra,
  résolution des sources et limites de confiance.
- Statut `humanReviewRequired` toujours vrai.

Les tests d'intégration encodent et décodent de véritables fichiers :
vidéo H.264 mobile, absence d'audio caméra, caméra recadrée, fallback
sur une vidéo noire et rejets des paramètres non autorisés.

## Limites

- Détection d'activité **≠ compréhension sémantique** :
  le moteur ne sait pas automatiquement distinguer un animal, visage,
  prix, titre ou objet utile d'un élément brillant.
- Le recadrage enlève les parties gauche et droite du rush.
  Pour des démonstrations où tout le cadre compte, préférer
  `preserve` ou enregistrer nativement en portrait.
- Le fallback se déclenche sur faible information visuelle,
  **pas** sur une qualité artistique jugée par IA.
- Au-delà de 60 s par plan, le mode `auto` conserve le cadre ;
  `follow` refuse ce cas.
- Les fichiers source trop faibles restent trop faibles en 1080p
  même après mise à l'échelle.
- L'export Shorts doit être visionné sur téléphone avant publication.
  L'accord de diffusion, les droits et la précision de la narration
  ne sont pas certifiés automatiquement.

## Définition de terminé

La PR est fusionnable uniquement lorsque le workflow de production est
vert **sur le SHA exact**, avec de vrais MP4 de sortie, sans substitution
de simples images ou simulations. Aucun upload TikTok/YouTube automatique.
