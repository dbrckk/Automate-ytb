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

Ce passage décrit le précédent système d'images fixes. Depuis le rig v1 ci-dessous, la chouette est animée par calques mobiles ; il ne s'agit toujours ni de vidéo générée par IA, ni d'animation 3D. Pour d'autres personnages ou styles, le moteur conserve les cartes graphiques précédentes afin de ne pas représenter un personnage erroné. Les images ne reprennent pas la mascotte d'une chaîne tierce.

Les futurs ajouts devront prévoir un catalogue de personnages originaux, des gestes/expressions contrôlés par le storyboard et une validation de cohérence visuelle entre les scènes.

## Animation 2D de la chouette (rig v1)

Le mode cartoon avec une description contenant owl, chouette ou hibou
ne se limite plus à une illustration fixe. Notre chouette originale est composée
de calques transparents (ailes gauche/droite, corps, clignements)
animés indépendamment grâce à FFmpeg. Les ailes battent,
le corps oscille et les yeux clignent ; l'arrière-plan reste cohérent pendant le
plan. Les variations de décor et de narration sont conservées à chaque scène.

**Réutilisation :** le moteur associe au visuel approuvé l'empreinte
du sujet, du texte, du personnage et du style. Si le contenu est modifié après
la préparation des images, le rendu refuse d'exploiter les anciens médias sans
nouvelle validation. Le cache des clips est également invalidé si l'image,
la durée, le nombre d'images par seconde ou le moteur de rendu change.

L'aperçu reste gratuit sans compte IA, sans image copiée, sans génération distante
ni publication YouTube. **Limites :** l'animation procédurale ne couvre encore
que la chouette ; ce n'est ni de la vidéo générée par IA, ni une animation 3D
complexe ; la voix eSpeak est provisoire. Pour les autres personnages, le
moteur conserve ses propres cartes graphiques au lieu de dessiner une chouette
qui ne correspondrait pas au scénario.

Les tests comparent des images réellement décodées du MP4 à différents
instants : ils vérifient que le personnage bouge tandis que le décor reste
stable. Ils vérifient aussi la reproductibilité des visuels et le refus
des anciennes images si le scénario change.
