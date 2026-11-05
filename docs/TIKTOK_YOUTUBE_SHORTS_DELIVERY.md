# TikTok + YouTube Shorts — export commun, contrôles et publication

## Contrat réel de livraison

Objectif : **un seul MP4 original** vertical utilisable dans les deux
applications sans retouche de proportions. Profil privilégié : **1080×1920,
9:16, 30 FPS, H.264, AAC 48 kHz stéréo, 8–60 secondes**, mobile first.

Le validateur accepte aussi 720×1280, 24–60 FPS et jusqu'à 180 secondes pour
respecter le plafond YouTube Shorts; ces dimensions/durées alternatives
peuvent déclencher des conseils éditoriaux. Les limites TikTok varient
selon le type de compte, le mode de publication et les règles applicables.
Un export techniquement compatible n'est jamais une preuve d'acceptation
ou de publication par TikTok/YouTube.

## Commande (PC, serveur, ou workflow Android)

```bash
python -m automate_ytb.shorts_delivery \
  --video build/video/preview.mp4 \
  --require-audio \
  --report build/video/platform-shorts-report.json
```

Le fichier JSON inclut les dimensions et codecs **lus dans le MP4 réel**,
la durée, la fréquence moyenne, les avertissements et les contrôles manuels.
En cas d'erreur, la commande retourne le code 2.

Le workflow GitHub **One-click YouTube preview (free)** exécute désormais
cette vérification avant de livrer les exports de résolution `shorts`.
Les autres formats ne sont pas présentés comme des Shorts.

## Règles créatives permanentes

- **0–2 s :** sujet vivant immédiatement, accroche compréhensible sans
  voix. Éviter les fades noirs et diapositives.
- **2–20 s :** actions réelles image par image, animation interne aux sujets,
  au moins un événement visuel significatif, plans variés qui servent
  l'histoire. Un panoramique d'image fixe ne suffit pas.
- **Textes :** courts, au centre de la zone lisible; éviter coins/haut,
  boutons de droite et panneau de description bas. Examiner
  **sur TikTok et Shorts** les vrais recouvrements avant publication.
- **Son :** musique originale/autoriséе; narration anglais/français
  naturelle avec Kokoro quand demandée, revue d'écoute et mesure LUFS.
  Pas de remplacement silencieux de la voix par une synthèse robotique.
- **Fin :** conclusion visuelle et retour fluide au début si possible,
  sans obligation de tromperie ou de clickbait.
- **Production :** export 9:16, thumbnail adaptée, titre, description,
  hashtags contextuels, déclarations honnêtes (2D, animation, 3D,
  footage réel ou non).
- **Publication :** jamais déclenchée sans authentification appropriée,
  droits validés et consentement explicite. Des contrôles techniques ne
  confirment pas les droits musicaux ou l'acceptation de la plateforme.

## Sources officielles (consultées le 5 novembre 2026)

- YouTube Help, Shorts jusqu'à 3 minutes :
  https://support.google.com/youtube/answer/15424877
- Guide TikTok for Business sur la production 9:16, haute résolution et
  zones de sécurité :
  https://ads.tiktok.com/business/library/Creative_Codes_One_Pager.pdf
- Les spécifications publicitaires TikTok ne sont **pas** des garanties
  pour toutes les publications organiques.

## Limitations techniques vérifiées

Le validateur utilise ffprobe et la **fréquence d'images moyenne**.
Il ne prouve pas à lui seul qu'il n'y a aucune image gelée, artefact,
dérive audio ou problème de composition. L'assurance qualité complète
exige des contrôles séparés et un visionnage humain.
