# Automate-ytb — Plan opérationnel pour une pipeline vidéo professionnelle

> Établi le 6 novembre 2026 d'après l'inspection effective de \`main\` (\`e32ec907d44303193e169d7db0a0a406394c62c0\`), des workflows, des plans antérieurs et des PR ouvertes.
>
> **Statut : plan, pas implémentation.** Les objectifs et seuils ci-dessous sont des critères d'acceptation proposés, pas des résultats déjà atteints.

## Objectif produit

Depuis un smartphone Android, fournir un sujet ou un script, ou charger plusieurs vidéos déjà autorisées, choisir FR/EN, style, durée et format, puis récupérer **un vrai MP4 complet** et des fichiers de publication : SRT/VTT, couverture, titre/description, crédits/licences, rapport d'assurance qualité et source des assets. Les moteurs principaux doivent rester **gratuits et open source**, avec rendu CPU/GitHub Actions lorsque viable. Aucune publication automatique sans permission explicite et contrôles adéquats.

La qualité cible n'est pas « un MP4 qui passe FFprobe » : il faut du mouvement réel continu, une direction d'acteurs/objets cohérente, une image de qualité, une voix naturelle et une progression visuelle qui montre ce que raconte le script. **Pas de faux timelapse obtenu par zoom sur des images fixes, pas de cartons de diapositives et pas de voix eSpeak présentée comme voix premium.**

Formats de référence : TikTok/Shorts **9:16 1080×1920 30 fps**, H.264/AAC; versions 16:9 et éventuellement 1:1 à partir du même plan éditorial, avec cadrages distincts, pas un recadrage aveugle.

## Audit de départ et preuves

### Ce qui existe réellement sur \`main\`

- Narration Kokoro FR/EN, variantes d'expression/débit, audio PCM et sous-titres par **phrases mesurées** dans les moteurs qui en disposent : \`narration.py\`, \`narration_pacing.py\`, \`short_voice.py\`, \`captions.py\`.
- Pipeline multi-sources vidéo, allocation, normalisation, recadrage dynamique limité par l'activité de l'image : \`auto_edit.py\`, \`footage.py\`, \`subject_reframe.py\`, \`production.py\`.
- Animations spécifiques science, personnage et effets, rendus Blender aurora/ocean en option : \`science_motion.py\`, \`science_blender_aurora.py\`, \`science_blender_3d.py\`, \`scripts/blender_aurora_stage.py\`.
- Quality gates médias/sous-titres, inspections de vraies images décodées et planches : \`media_qa.py\`, \`shorts_delivery.py\`, \`visual_preflight.py\`, \`qa_bundle.py\`, \`professional_review.py\`.
- Workflows \`one-click-preview.yml\`, \`kokoro-short-voice.yml\`, \`validate.yml\`, \`aurora-blender3d-release-candidate.yml\`, \`science-shorts-release-candidate.yml\`.

### Bloqueurs observés

1. **Rendu Aurora Alive, PR #196, premier run #42219660878 : échec** après préparation Blender, au moment de \`Plan scenes, graphics and narration\`, car la durée PCM Kokoro ne concordait pas avec la cible. La correction sur branche attend son rendu/QA définitif : ne pas considérer la PR prête sans confirmation.
2. **PR #195** (sous-titres parlés incrustés) encore ouverte pendant cet audit : les versions intermédiaires ont connu des rendus annulés/échecs; ne pas assimiler le statut d'une ancienne exécution à celui du dernier SHA. Préserver le découpage PCM et écouter la prosodie : de trop petits fragments peuvent provoquer une voix hachée.
3. Les vidéos scientifiques sont souvent **illustratives** : animations 2D/2,5D ou Blender rendu à faible nombre d'images de référence; la sortie 1080p ne signifie pas que les images sources ont cette précision ni qu'une animation 3D est entièrement animée à 30 images originales par seconde.
4. Les inspections visuelles restent **échantillonnées**, donc une vidéo techniquement correcte peut être répétitive, peu naturelle, mal synchronisée ou mal cadrée sur téléphone.
5. Les artefacts GitHub Actions ont une durée de vie limitée et les liens temporaires peuvent échouer côté Android; il manque un mécanisme de livraison direct, durable et vérifié. Aucun upload web Android autonome prêt à produire n'a été vérifié.

## Politique de priorité

Ordre d'exécution : **fiabilité d'abord**, puis **impact visuel réel**, **mouvement**, **voix et synchronisation**, **rythme**, **finitions audio**, **livraison Android**. Ne pas disperser l'effort sur des dizaines de petits effets décoratifs. Chaque phase a un résultat vidéo de référence et une décision explicite « accepté / à corriger ».

Pour comparer les rendus, constituer un jeu de référence commun contenant :
- un sujet scientifique visuel (aurores, physique, phénomènes naturels);
- un montage documentaire avec **plusieurs rushes réels autorisés**;
- un montage promotionnel ou narratif avec des interactions visibles entre sujets et environnement.

Pour chaque genre, produire systématiquement **une vidéo avant / après** à scénario comparable. Ne pas fusionner une amélioration artistique parce que seul son code passe les tests.

## Phase 0 — Réparer la chaîne de rendu et de livraison (bloquante)

**Problème :** un long calcul Blender peut finir par échouer seulement après le chargement de Kokoro, et un artefact peut être inaccessible sur Android.

**Travaux concrets :**
1. Résoudre les PR #195/#196 en inspectant le dernier SHA, les logs et la couverture effective, sans fusion aveugle. Corriger les régressions en place avant d'empiler un autre générateur.
2. Distinguer la **durée cible éditoriale** de la **durée réelle PCM**. Utiliser une préflight voix : planifier les textes et déterminer les limites avant le rendu 3D final. Si un script dépasse le budget, demander une reformulation automatique **affichée pour validation**, ajuster la durée dans une plage autorisée ou échouer avant les calculs lourds. Ne pas couper/accélérer la voix silencieusement.
3. Exécuter chaque tâche avec identifiant, empreinte SHA-256 des entrées, état, relance idempotente et cache de scènes. Les anciennes versions de PR annulées ne doivent pas consommer le quota.
4. Séparer \`preview\` basse résolution et \`final\` : réutiliser les scènes et l'audio exacts une fois acceptés. Ne pas annoncer 1080p natif lorsque la source est agrandie.
5. Après tout rendu : décodage intégral FFmpeg, FFprobe des pistes, comparaison audio/SRT et contrôle des fichiers réellement archivés. Produire un manifeste \`delivery.json\` avec hashes, tailles, durée, source SHA, artefact/lien et date d'expiration. Le lien mobile doit être **testé**, avec un secours ZIP/MP4 et sans URL inventée.

**Sortie P0 :** trois créations consécutives sur des scripts différents produisent un MP4 complet, les contrôles sont verts sur le SHA exact, une archive téléchargeable est présente et chaque panne déclare clairement son stade. Aucun faux succès de vidéo non générée.

## Phase 1 — Image premium : routeur de sources et storyboard visuel (gain visible majeur)

**Problème :** les contenus sont souvent constitués de diagrammes ou de déplacements artificiels sur une image. Le moteur doit choisir le **bon type de séquence pour le genre**.

**Travaux concrets :**
1. Créer un routeur \`genre + shot + source\` : footage réel quand disponible/licencié; rendu 3D original quand la scène exige volume et interactions; motion design/vectoriel pour les concepts abstraits; prises de vue de produits réelles pour la promotion. Ne jamais appeler photoréaliste un schéma 2D.
2. Plan structuré par scène : \`subject\`, \`action\`, \`environment\`, \`camera\`, \`motion\`, \`start/end event\`, \`source_id\`, \`license\`, \`narration_beat\`, \`confidence\`.
3. Banque de rushes gratuite **avec droits vérifiés** : NASA/NOAA/Wikimedia selon conditions particulières, rushes personnels, assets open source issus d'une revue de \`star-list\`. Vérifier attribution, modifications, date et droit d'usage **par fichier**, conserver URL officielle, SHA-256 et crédit affichable; ne jamais supposer qu'une image trouvée peut être réutilisée.
4. Dérushage : détecter coupes, netteté, luminosité, mouvements dominants, plans doublons, qualité technique et lisibilité en 9:16; conserver un *confidence score*. Les sélections sémantiques avancées sont optionnelles et locales; en cas d'incertitude, s'abstenir plutôt que présenter un choix erroné.
5. Conserver des sources **verticales 1080p ou mieux** si possible. Écarter les plans qu'il faut trop agrandir ou qui perdent le sujet au recadrage; garder \`contain + moving background\` en secours avec qualité explicitement inférieure.

**Sortie P1 :** sur chaque benchmark, aucune séquence ne cache le sujet, ne recycle le même plan sans justification ou ne s'annonce « vraie vidéo » si elle est un simple fond panoramique. Toute source est identifiée, vérifiée et visuellement inspectable.

## Phase 2 — Animation, physique lisible, lumières et caméra (gain visible majeur)

**Problème :** succession de poses illustrées, mouvements limités et effets « slide ».

**Travaux concrets :**
1. Repenser les scènes comme des **actions continues** : anticipation → action → interaction → réaction → reprise, avec positions/vitesses temporellement cohérentes.
2. Pour Blender : éclairage multi-source cohérent, shaders et matériaux adaptés, profondeur, particules réactives, géométrie crédible, profondeur de champ limitée, trajectoires de caméra conçues pour l'histoire. Les images 3D précédentes ne doivent pas simplement boucler un petit nombre de poses visibles.
3. Établir un budget par plan : image de référence rapide, simulation/rendu final seulement sur plans acceptés. Adapter Blender Eevee/Cycles selon test objectif de coût et qualité plutôt que choisir l'outil « le plus cher ».
4. Créer un langage de plans filmés (plan large → moyen → détails, suivi d'objet, panoramique, transitions motivées). Détecter et empêcher les recadrages qui coupent un sujet important ou provoquent un mouvement artificiel.
5. Les personnages doivent avoir articulation cohérente, poids, contacts/occlusion, expression/lipsync uniquement si une scène contient **un personnage qui parle à l'image**. Pour les vidéos documentaires, ne pas créer artificiellement une personne qui n'existe pas dans les sources.

**Sortie P2 :** au moins un événement/mouvement **observable dans la scène** toutes les quelques secondes sur les Shorts de référence, sans imposer un montage hyperactif; revue comparative avant/après montrant une amélioration nette de lisibilité, fluidité, éclairage et continuité. Vidéo décompressée inspectée sur au moins début/milieu/fin **et** aux coupes.

## Phase 3 — Voix de narrateur naturelle et synchronisation fiable

**Problème :** Kokoro fonctionne, mais peut prononcer des fragments isolés de façon hachée, avec pauses non naturelles; timing des sous-titres pas phonétique.

**Travaux concrets :**
1. Définir des profils FR/EN par genre (documentaire, éducatif, produit, fiction). Audition contrôlée des voix existantes \`af_heart\`, \`af_bella\`, \`af_nicole\`, \`am_michael\`, \`ff_siwis\`; décider à l'écoute et vérifier la licence/modèle. Réduire les variations de débit artificielles.
2. Synthétiser des phrases **sémantiquement complètes** pour conserver la prosodie; ne pas hacher la voix uniquement pour calculer les sous-titres. Nettoyer les silences de début/fin de façon conservatrice, préserver les respirations/pauses naturelles.
3. Produire le **master WAV entier** avant le plan de scènes final. Calculer la durée réelle, découper ensuite le montage autour des événements vocaux. Interdire tout changement de durée de voix sans recalcul du montage.
4. Sous-titrage par phrases réellement mesurées; pour le **mot à mot**, brancher un alignement local vérifié (par exemple WhisperX/faster-whisper selon compatibilité) et rapporter couverture/erreur; si non fiable, rester en sous-titres par groupes et l'indiquer.
5. Qualité linguistique et dictionnaire de prononciation FR/EN, noms propres, ponctuation. Révision du texte factuel avant synthèse, deux voix ou styles comparables sur un extrait identique.

**Sortie P3 :** comparaison en aveugle sur cinq extraits FR et cinq EN, même texte, avec appréciation humaine de clarté, respiration, accent, diction et naturel. Aucune revendication « voix réaliste validée » sans écoute. Pas de mots absents/inventés dans le SRT.

## Phase 4 — Monteur éditorial intelligent et relation image–voix

**Travaux concrets :**
- Monter à partir d'une timeline d'**événements causaux**, pas de durées identiques obligatoires par slide.
- Chaque phrase du script possède un ou plusieurs plans avec mouvement démontrant ce qu'elle explique. Contrôler la cohérence chronologique, l'apparition des sujets, les axes de caméra et la stabilité couleur/lumière.
- Couper aux événements/respirations/accents musicaux pertinents, sans flash ou transition répétitive. Pour un Short, démarrer par l'action la plus forte; titres très courts et avec une vraie visualisation derrière.
- Introduire du rythme variable : un plan peut durer longtemps **si quelque chose y évolue**. Éviter les transitions décoratives non motivées.
- Sorties \`edit-decision-list.json\` et \`shot-evidence.json\` avec cause de sélection, début/fin source, score de confiance et hash source.

**Sortie P4 :** revue sur trois genres : les scènes correspondent au sens de la voix; aucune coupe ne masque une action, ne désynchronise une phrase ou n'utilise des rushes hors sujet. Les changements sont mesurés sur vidéos réelles.

## Phase 5 — Sound design, sous-titres et finition

**Travaux concrets :**
- Rendre les effets sonores originaux/autorisé **événementiels** (vent, impact, ambiance, mouvement), pas des sons en boucle sans lien.
- Fond musical original ou avec droits documentés, ducking réel sous la voix, fade cohérent, contrôle EBU R128 LUFS/true peak, écoute sur haut-parleur Android.
- Sous-titres incrustés, typographie de lecture rapide, contrastes, taille et zones sûres, **pas d'effets qui masquent le sujet**; SRT/VTT indépendants; animation par phrase synchronisée.
- Colorimétrie cohérente interplans, sortie mobile, thumbnail et A/B de couverture.
- Contrôles automatisés de texte débordant, zones UI, noir/blanc anormal, silences intempestifs, doublons et coupures brutales.

**Sortie P5 :** rendu audible et lisible sur smartphone sans devoir régler le volume; aucune voix couverte par musique; mêmes paroles dans la narration et le sous-titre.

## Phase 6 — Produit utilisable sur Android et livraison durable

**Travaux concrets :**
1. Workflow GitHub Actions **un bouton** avec sujet/script, type, médias autorisés, langue, voix, durée et format; validation immédiate des entrées.
2. Téléversement navigateur multi-fichiers avec authentification, budgets de taille, reprise d'upload, quotas et effacement des sources; **ne pas présenter comme existant** tant que non déployé/testé. Comparer les options gratuites sans supposer qu'un hébergement gratuit stocke durablement des vidéos volumineuses.
3. Orchestration de tâches idempotentes, cache par SHA, relance par étape, réservations de CPU raisonnables, limites de taille/mémoire; watchdog sur rendu bloqué.
4. Livraison \`MP4 + ZIP + SRT + cover + texte de publication + sources/licences + QA\`, manifeste de checksums, **lien vérifié** depuis Android. En complément d'artefacts Actions expirables, étudier les GitHub Releases ou un stockage utilisateur déjà autorisé pour les vidéos validées.
5. Mode revue → publier uniquement sur ordre explicite, via APIs autorisées et OAuth; jamais intégrer secrètement des identifiants ni supposer une intégration TikTok/YouTube déjà active.

**Sortie P6 :** utilisateur Android obtient la vidéo finie en un flux réplicable, avec liens fonctionnels et message d'erreur compréhensible si panne, sans terminal ni paiement externe obligatoire.

## QA de sortie — non négociable

Les niveaux d'approbation sont distincts :

| Niveau | Contrôles obligatoires | Ce que ce niveau **ne** prouve **pas** |
| --- | --- | --- |
| A — technique | MP4 décodable entièrement; conteneur, profil, durée, pistes, audio, sous-titres, fichiers et checksums | Qualité artistique |
| B — visuel | Captures issues du MP4, mesures de mouvement/coupes/lumière, vérification cadrage mobile | Réalisme de chaque scène |
| C — éditorial | Écoute de la voix, correspondance audio/image, cohérence et véracité des faits, crédits/licences | Permission automatique de publication |
| D — diffusion | Accord explicite, metadata, spécifications actuelles de la plateforme, lien final vérifié | Garanties de vues/rétention |

Établir une grille de comparaison humaine **sur 100**, réservée aux vidéos passées aux gates A/B :
- Images et matières : 30 points;
- Mouvement/animation et interactions : 25;
- Naturel de la voix : 20;
- Scénario et synchro : 15;
- Sound design/sous-titres : 10.

Ne pas calculer une « note professionnelle » inventée sur l'état actuel du dépôt. Mesurer sur des sorties réelles, à script comparable, avec au moins une écoute et un visionnage humain. Les gains sont présentés avant/après, avec limites.

## Ordre précis des travaux / PR à ouvrir

| Séquence | Modification unique | Dépend de | Preuve de fin |
| --- | --- | --- | --- |
| M0 | Réparer/terminer PR #195 et #196 sur dernier SHA et préserver 1 Short exploitable | aucun | MP4/audio et QA verts, artefact effectivement récupéré |
| M1 | Préflight audio PCM et adaptation de la durée **avant** tout Blender lourd | M0 | Aucun run ne rend les scènes 3D avant de découvrir un problème de durée voix |
| M2 | Routeur de sources et vrai dérushage 9:16 à confiance explicite | M1 | Benchmark footage vs infographie : sujet toujours visible et sources traçables |
| M3 | Plan-clé premium : vrai mouvement 3D/footage, matériaux, lumière, caméra, événements | M2 | Deux exports identiques de référence avant/après et choix artistique validé |
| M4 | Voix en phrases complètes, prosodie, sous-titres et horodatage fiables | M3 | Master WAV contrôlé, transcription intègre, test d'écoute FR/EN |
| M5 | Monteur causal + cut dynamique et audio événementiel | M4 | Aucun plan hors sujet, dynamique liée à une action et voix audible |
| M6 | Export multi-format, manifeste et téléchargement Android durable | M5 | Liens MP4/ZIP vérifiés après livraison, sans intervention PC |

**Pas de refonte totale :** les modules existants restent propriétaires de leur fonction. Chaque PR termine une capacité, mesure une vraie vidéo, et conserve les anciens formats et entrées.

## Ressources et coûts

- Pile locale gratuite : Python, FFmpeg/FFprobe, Pillow, Blender, Kokoro. Optionnels selon benchmarks/licences : PySceneDetect, OpenCV, Whisper/faster-whisper, alignement phonétique libre.
- External assets : \`dbrckk/star-list\` est une **source de candidats**, pas un catalogue automatiquement licencié. Vérification de version/licence/usage avant intégration.
- Respecter les quotas GitHub Actions, les contraintes de stockage, la durée des artefacts et les licences des modèles. Ne jamais prétendre qu'une solution gratuite est illimitée.
- Prioriser le cache et une prévisualisation peu coûteuse; payer un calcul final uniquement après validation de l'idée du plan.

## Critère global « pipeline professionnelle »

Une production est acceptable quand un utilisateur peut fournir un script ou ses rushes autorisés, lancer le rendu **sans console**, écouter une voix réellement naturelle, voir des scènes continuellement animées et liées au propos, récupérer un MP4 vérifié avec SRT/crédits et, sur Android, retrouver ses fichiers sans « file not found ». Aucune de ces propriétés ne doit être annoncée comme acquise sans la démonstration correspondante.
