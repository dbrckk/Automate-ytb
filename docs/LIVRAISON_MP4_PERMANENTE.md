# Livraison fiable des vidéos — règle de production permanente

## Pourquoi les liens « File not found » revenaient

Les fichiers `sandbox:/mnt/data/...` appartiennent à une session de ChatGPT :
ils ne constituent pas un hébergement durable. Les ZIP stockés dans les
artefacts GitHub Actions expirent également (ici après 7 jours), et sur
Android ils demandent souvent plusieurs manipulations.

**Interdiction dans nos livraisons finales :** envoyer un lien sandbox,
un lien vers un artefact Actions ou une URL devinée comme s'il s'agissait
d'un lien de téléchargement permanent.

## Solution retenue : GitHub Releases (gratuit sur notre dépôt public)

1. Le moteur produit un MP4 réel avec une voix ou de l'audio AAC.
2. Les tests et le manifeste QA attestent SHA-256, résolution, cadence,
   durée, codecs et contrôle de décodage intégral.
3. Un workflow **sans secret externe** récupère exactement les octets
   issus de ce rendu et les republie en **GitHub Release de prévisualisation**.
4. Un téléchargement HTTP public **sans connexion** est effectué ; son
   SHA-256 doit correspondre au SHA-256 avant upload.
5. **Seulement après ce contrôle**, communiquer l'URL directe :

   `https://github.com/dbrckk/Automate-ytb/releases/download/<tag>/<video>.mp4`

Les GitHub Releases n'ont pas la date d'expiration des artefacts Actions.
Le téléchargement reste accessible tant que le dépôt public, la release et
le fichier existent. GitHub documente actuellement une limite inférieure
à 2 Gio **par fichier**, 1 000 fichiers par release, et aucune limite
de bande passante ni de taille totale annoncée :
https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases

## Implémentation actuelle

| Type de rendu | Distribution publique | Déclenchement |
| --- | --- | --- |
| Forest Discovery 2.5D / Kokoro | `.github/workflows/forest-stable-video-download.yml` | Automatique quand le rendu sur `main` réussit |
| Vidéos scientifiques du pipeline établi | `.github/workflows/science-preview-download.yml` | Automatique après un rendu scientifique `main` validé |
| Solar Storm | `.github/workflows/publish-solar-storm-video.yml` | Sélection explicite d'un rendu validé |
| Nouveau type ou nouveau sujet de Short | **Obligation d'intégrer cette étape avant de le dire « livré »** | À raccorder au workflow de sa catégorie |

Le distributeur forêt accepte uniquement une exécution GitHub de
`Verify narrated 2.5D forest short with real Kokoro PCM` terminée
avec succès, issue du dépôt et de la branche `main`. Une exception
explicite et limitée à l'exécution P4.7 #42593121306 permet d'archiver
le MP4 déjà rendu et validé avant la mise en place de cette règle.

Les exécutions de PR non fusionnées **ne sont pas publiées automatiquement**.

**Important :** une Release publique est un aperçu technique consultable ;
elle n'autorise pas la mise en ligne automatique sur TikTok ou YouTube.
Les commentaires, la qualité artistique, la voix et la conformité éditoriale
restent à contrôler séparément. Aucun MP4 confidentiel ne doit être versé
dans les Releases de ce dépôt public.

## Récupérer la vidéo depuis Android

Ouvrir directement le lien `.mp4` communiqué après la vérification, ou :

1. Ouvrir `https://github.com/dbrckk/Automate-ytb/releases`.
2. Choisir la release de la vidéo (avec un tag propre à son rendu).
3. Appuyer sur le fichier `.mp4` dans « Assets ».

**Il n'est pas nécessaire de connecter Stripe, de payer un service vidéo,
d'installer un outil sur Android ou de télécharger un ZIP Actions.**

Pour une relivraison ponctuelle d'un rendu forêt déjà terminé, GitHub >
Actions > « Stable permanent MP4 downloads for validated forest Shorts »
> « Run workflow » > renseigner l'ID de l'exécution source et lancer.
Le workflow refuse les exécutions invalides, expirées ou non validées.

## Règles anti-régression pour toutes les prochaines vidéos

- Un asset de Release possède un tag unique par exécution : **ne pas écraser**
  la vidéo précédente si un nouveau rendu est généré.
- Conserver avec le MP4 un manifeste contenant son SHA-256 et les preuves
  de validité du format, pour pouvoir le contrôler indépendamment.
- Vérifier un **GET HTTP anonyme intégral**, et non simplement la présence
  de la Release dans l'API GitHub.
- En cas de code HTTP non-2xx, de SHA différent, de vidéo corrompue ou de
  Release absente : marquer la livraison comme **échouée** et ne pas
  communiquer le lien comme fonctionnel.
- Dans les réponses ChatGPT, préférer le **lien GitHub Release réel**,
  copié depuis la sortie du workflow réussi. Ne pas inventer de `sandbox:`.
- Pour chaque nouveau moteur de vidéo, prévoir systématiquement la branche
  de distribution (déjà faite pour science et forêt), avant de déclarer
  une fonctionnalité vidéo terminée.

Ce mécanisme supprime la dépendance au stockage temporaire de ChatGPT.
Il ne peut garantir la disponibilité à vie en cas de suppression du dépôt
ou de changement de conditions de GitHub.
