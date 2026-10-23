# Une vidéo YouTube depuis Android — sans PC ni appel API payant

## Lancer un aperçu complet

1. Ouvrir [Actions](https://github.com/dbrckk/Automate-ytb/actions) dans le dépôt.
2. Sélectionner **One-click YouTube preview (free)**, puis **Run workflow**.
3. Renseigner le sujet, un **scénario original**, une description de personnage original, la durée, la langue et le style. Le scénario doit avoir **au moins une phrase par scène** ; par exemple 30 secondes / 6 secondes = 5 phrases.
4. Laisser la voix **espeak** pour une première démonstration avec narration, ou **none** pour un aperçu silencieux.
5. À la fin du run, télécharger l'artefact **automate-ytb-free-preview** dans la rubrique **Artifacts**. Il contient MP4, narration WAV, sous-titres SRT, trois miniatures, scénario, JSON de scènes et compte rendu.

Ce workflow crée **gratuitement des illustrations procédurales de brouillon**, pas des images IA photoréalistes ni une animation comparable à Murph. Il produit une piste de narration **eSpeak de qualité provisoire**, pas une voix professionnelle. Le résultat est un **brouillon à revoir**, sans publication automatique.

### Précautions

- Sur un **dépôt GitHub public**, les entrées d'un workflow et les artefacts ne doivent pas être considérés comme privés. Ne pas coller de scénario confidentiel, identifiants ou données personnelles.
- Le lancement nécessite les permissions GitHub pour exécuter des workflows sur le dépôt. Le rendu peut prendre du temps sur des projets comportant beaucoup de scènes.
- Aucune facture d'inférence n'est générée par ce workflow (GitHub Actions peut néanmoins être soumis aux règles de quotas de ton compte).
- Les sujets, affirmations, illustrations, voix et métadonnées doivent être vérifiés avant publication. Ce n'est pas un moteur d'information automatiquement sourcée.
- Le système adapte la durée des scènes à une narration eSpeak trop longue : il **ne tronque pas la voix**. Les sous-titres sont synchronisés **à l'échelle de chaque scène**, pas au mot.
- Limites configurées dans l'action : 30–900 secondes au départ, 3–20 secondes par scène, 150 scènes maximum. Pour dépasser ces seuils, prévoir une orchestration plus avancée avec reprise.

### Génération IA optionnelle

Le module [Hugging Face](HUGGINGFACE_IMAGE_PROVIDER.md) sait demander de véritables images à un fournisseur compatible. Il utilise le **client officiel InferenceClient** et se configure séparément avec :

~~~bash
python -m pip install -e '.[images]'
python -m automate_ytb.image_provider --plan project/scene-plan.json --limit 1
~~~

Par défaut, il affiche le budget estimé **sans envoyer la moindre requête**. La génération réelle nécessite un jeton privé \`HF_TOKEN\`, l'option \`--execute\`, un consentement de droits et un montant estimé suffisamment élevé. Les tarifs réellement facturés ne peuvent pas être garantis par le programme : définir les limites directement chez le fournisseur.

**Le workflow gratuit et le fournisseur IA restent distincts.** Ainsi, une commande Android ne peut pas déclencher une dépense externe par accident.

## Architecture et étapes suivantes

L'Action existante prépare le plan de scènes, notre moteur crée les images de brouillon, eSpeak fabrique une piste PCM dont les segments sont calés sur le planning, FFmpeg produit les clips puis le MP4, et trois miniatures sont exportées.

Les prochaines améliorations qualitatives les plus importantes sont : une charte graphique originale avec personnage réellement visible et cohérent, une API ou un modèle TTS naturel, une génération IA à coût contrôlé et une synchronisation mot-à-mot. Ces fonctions ne sont **pas** promises par le workflow gratuit de cette version.

## Personnage animé : illustration originale améliorée

En style **cartoon**, si la description du personnage contient `owl`, `chouette` ou `hibou`, le système produit maintenant une **chouette originale dessinée** avec lunettes turquoise, foulard doré, expressions, poses et décors variant selon les scènes. Les rendus sont déterministes pour permettre la reprise et la comparaison visuelle.

Il s'agit d'illustrations procédurales fixes, animées au montage par un léger mouvement de caméra, **pas** d'animation squelettique ni de vidéo générée par IA. Pour d'autres personnages ou styles, le moteur conserve les cartes graphiques précédentes afin de ne pas représenter un personnage erroné. Les images ne reprennent pas la mascotte d'une chaîne tierce.

Les futurs ajouts devront prévoir un catalogue de personnages originaux, des gestes/expressions contrôlés par le storyboard et une validation de cohérence visuelle entre les scènes.
