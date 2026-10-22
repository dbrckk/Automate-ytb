# Mode vidéo complet hors ligne — sans clé API

Ce mode produit un **aperçu vidéo original**, depuis un texte fourni, sans appeler Higgsfield, Hugging Face ou une autre API payante.

## Depuis Android (sans PC)

1. Ouvrir [Actions / One-click offline video preview](https://github.com/dbrckk/Automate-ytb/actions/workflows/one-click-offline-video.yml).
2. Choisir **Run workflow**.
3. Conserver le sujet et le scénario de démonstration pour un premier essai, ou saisir son propre texte. Prévoir **une phrase complète par scène** (ex. 8 phrases pour 60 secondes / 7,5 secondes).
4. Choisir 720p ou 1080p, voix française/anglaise (eSpeak) ou mode silencieux, puis lancer.
5. À la fin du workflow, télécharger l'artefact **automate-ytb-offline-video** : MP4, image de miniature, images des scènes, sous-titres SRT, narration WAV (si choisie), manifestes et rapports.

**Important :** les entrées du workflow d'un dépôt public ne sont pas un espace privé. Ne pas y mettre de mots de passe, secrets, scripts confidentiels ni données personnelles.

## Fonctionnement technique

- Le module de planification d'origine \`scene_plan\` découpe le récit en séquences de durée fixe et exige le texte complet. Il n'invente jamais des faits pour remplir un épisode.
- \`offline_studio\` produit une illustration 16:9 par séquence avec Pillow : personnage original récurrent (hibou cartoon), titre, extrait du récit, symboles, progression et palettes cohérentes. Ce sont des illustrations procédurales **et non** des images cinématiques produites par IA.
- Les illustrations sont importées via \`production.ingest\` avec leur provenance, vérification de format et empreinte SHA-256. Le coût déclaré de génération d'images est **0 USD**.
- eSpeak-NG produit facultativement une piste audio française ou anglaise, découpée et calée à la durée des scènes. Les paroles excessivement longues sont refusées plutôt que coupées brutalement.
- FFmpeg anime légèrement chaque plan, réutilise les segments déjà calculés lorsque rien n'a changé, puis crée le MP4, une ébauche de miniature, un fichier SRT et un rapport JSON.
- Les sous-titres sont alignés **par scène**, pas mot à mot. La voix eSpeak est intelligible mais synthétique : elle ne remplace pas encore Kokoro ou une voix neuronale.

Le projet **n'est pas automatiquement publié sur YouTube** et n'est pas automatiquement déclaré conforme à la monétisation. Les textes, sources, droits de musique, miniature et rendu final nécessitent une revue avant toute mise en ligne.

## Utilisation Python

Installation : Python 3.11+, \`pip install -e .\`, FFmpeg, FFprobe et eSpeak-NG facultatif.

Créer une vidéo exemple de 60 secondes :

~~~bash
python -m automate_ytb.offline_studio \
  --topic "Comment créer une vidéo éducative ?" \
  --script examples/offline_episode_fr.txt \
  --character "Un hibou violet original avec une écharpe dorée" \
  --directory outputs/episode \
  --duration 60 --shot-seconds 7.5 \
  --language fr --resolution 720p
~~~

Sans narration :

~~~bash
python -m automate_ytb.offline_studio \
  --topic "Comment créer une vidéo éducative ?" \
  --script examples/offline_episode_fr.txt \
  --directory outputs/episode-silent --duration 60 \
  --shot-seconds 7.5 --silent
~~~

Si vous changez le sujet, la durée ou le script, utilisez un **nouveau dossier de sortie** ; le programme bloque les incohérences au lieu de remplacer des fichiers de production déjà approuvés.

## Limites explicites

Cette amélioration vise surtout le parcours de bout en bout **sans PC et sans frais de génération IA**. Elle ne rivalise pas encore avec les scènes générées par Higgsfield dans la vidéo de référence. Pour obtenir ce résultat, les prochains travaux porteront sur la cohérence des personnages entre images IA, les prises de vue illustratives pertinentes, une voix neuronale naturelle, une vérification documentaire systématique et des transitions plus expressives.

Le recours aux minutes de GitHub Actions est régi par les quotas et conditions de GitHub. « Sans API payante » ne signifie pas absence absolue de tout coût d'infrastructure.
