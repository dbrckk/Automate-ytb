# Historique permanent des vidéos — Automate-ytb

## Source de vérité

Toutes les vidéos réellement exportées et distribuées sont archivées dans les
[GitHub Releases](https://github.com/dbrckk/Automate-ytb/releases), avec des
liens HTTPS MP4 accessibles sur Android ou PC.

Le catalogue machine est **[video-history.json](video-history.json)**.
Il est synchronisé automatiquement après chaque livraison réussie des pipelines
**science** et **forêt 2.5D** par `scripts/update_video_history.py`.
Il est généré depuis les assets MP4 effectivement publiés : aucune vidéo
hypothétique ou simple idée n'est comptabilisée.

Chaque entrée contient le sujet, le type, la date de publication technique,
le tag de release, la taille, le lien MP4, le lien GitHub Release et l'empreinte
SHA-256 lorsqu'elle est disponible.

**Important :** le statut `technical-preview-unreviewed` signifie que les
tests automatisés sont passés, mais pas que la vidéo a été approuvée ou publiée
sur YouTube ou TikTok.

## Nouvelle vidéo inédite

**Can Lightning Travel Upward From a Tower?**

Une vidéo originale expliquant cinq étapes physiques d'un éclair associé à
une tour : séparation des charges, canal précurseur, décharges ascendantes,
éclair de retour et tonnerre. La vidéo utilise le rendu 2.5D original,
une narration anglaise Kokoro et une bande sonore générée localement.
Le fichier ne sera inscrit dans le catalogue qu'une fois réellement produit,
contrôlé et distribué par une GitHub Release vérifiée.

## Prévenir « File not found »

Les liens temporaires `sandbox:` et les artefacts GitHub Actions ne doivent
jamais servir de liens finaux. La livraison passe par une release publique,
un téléchargement HTTPS intégral sans authentification et une comparaison
octet par octet avant d'annoncer le MP4.
