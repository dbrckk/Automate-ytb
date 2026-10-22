# Référence vidéo complète — Ithielix / Automate-ytb

**Vidéo fournie :** `2933.mp4`, 13 min 16 s, 640×360, H.264, 60 i/s, AAC stéréo. **Décodage vidéo et audio complets vérifiés.** Cette version remplace le fichier `2929.mp4` tronqué à ~68 s.

## Relevé chronologique visuel

| Horodatage approximatif | Ce qui est observable |
|---|---|
| 00:00–03:10 | Présentation de la chaîne éducative Murph, de ses histoires illustrées, miniatures et chiffres affichés dans YouTube Studio/NexLev. Ces chiffres ne permettent pas de vérifier les revenus réels ni d'attribuer avec certitude le panneau privé à Murph. |
| 03:10–04:35 | Démonstration d'une vidéo de référence, puis construction du Google Doc intitulé **MASTER AUTOMATION PROMPT**. Le texte visible demande un **original AI-image slideshow story video**, avec Higgsfield, et expose `REFERENCE VIDEO` et `TARGET_DURATION` comme paramètres. Il évoque l'analyse de référence, recherche, écriture, voix, génération et montage jusqu'au MP4. |
| 04:35–05:45 | Interface de **Codex** et discussion de préparation d'assets, de style et du recours à Higgsfield. Ce passage montre l'orchestration par prompts ; il ne démontre pas une automatisation totalement sans intervention. |
| 05:45–07:45 | Aperçu d'une vidéo 3D illustrée à personnages cohérents. L'interface Codex affiche un livrable annoncé **15:07, 1080p, 150 scènes principalement fixes**, avec miniatures, manifeste d'images, prompts et scénario. Les éléments sont présentés à l'écran ; leur complétude technique n'a pas été auditée. |
| 07:45–10:05 | Relecture des scènes de l'épisode, des miniatures, et comparaison avec des vidéos explicatives illustrées. |
| 10:05–13:16 | Discussion des outils de codage, du fonctionnement de la méthode et de la stratégie YouTube ; nouveaux écrans d'analytics. Ce sont des démonstrations/affirmations, pas une garantie de monétisation. |

Analyse fondée sur les images de la vidéo intégralement décodable, **pas sur une transcription mot à mot des propos anglais**. Les passages trop petits ou masqués ne sont pas reconstitués.

## Correction d'architecture par rapport au premier fichier

La priorité n'est **pas** de recréer immédiatement un dessin animé avec rigs 2D et animation sophistiquée. Dans la démonstration, la méthode visible repose avant tout sur des **images IA cohérentes, une narration et un assemblage cinématique**. Les mouvements de caméra, transitions et microanimations peuvent venir ensuite.

### Chaîne de production cible

1. Sujet original, durée, public cible et vidéo de référence à analyser, sans copier les créations d'autrui.
2. Recherche factuelle, scénario complet, références HTTPS et validation des affirmations.
3. **Bible graphique permanente** : mascotte originale, proportions, expressions, costumes, lieux, palette, lumière.
4. **Plan de scènes** : environ 6 secondes par plan, narrative beat par image, même personnage et même style, variations de cadrages, liste des assets.
5. **Génération d'illustrations** via un fournisseur interchangeable, avec gestion des coûts et droits de modèles/poids.
6. **Contrôle de cohérence** des personnages et erreurs d'images, validation explicite des licences des médias.
7. **Voix naturelle et sous-titres alignés** sur l'enregistrement final, et non seulement sur des durées approximatives.
8. **Montage FFmpeg**, léger mouvement Ken Burns, transitions mesurées, mixage audio, export MP4 1080p 16:9.
9. **Trois miniatures**, description et chapitres ; contrôle qualité et publication YouTube d'abord privée avec consentement.
10. Boucle de mesure via l'API officielle YouTube/Analytics, sans inventer de revenus ou automatiser du contenu répétitif.

## Ressources de Star List à prioriser

Le scan antérieur examine **1 062 dépôts et 27 sites web**, sans exclure les dépôts `indexed`. Pour ce résultat précis, l'ordre recommandé est :

- **FFmpeg** : montage, synchronisation audio, transcodage, rendu et QA ; déjà utilisé par la V1.
- **Kokoro / VoxCPM** : piste de narration plus naturelle que eSpeak, sous réserve de licences et coûts des poids.
- **Whisper** : transcription et contrôle des sous-titres.
- **StoryDiffusion / Toonflow-app / modèles d'image via Hugging Face** : caractère cohérent et prompts pour des séries d'images.
- **Higgsfield Skills** : éventuellement connecter un moteur hébergé après examen des tarifs, quotas et droits.
- **MoneyPrinterTurbo** : référence d'orchestration, mais aucune dépendance importée sans audit.
- **Motion Canvas** : ajouter plus tard des mouvements d'image/de caméra. Il n'est plus le prérequis de la V2.
- **FastH3 Omni / LTX-Video** : options gourmandes ou hébergées, non indispensables au flux de plans fixes.

Une licence de code dans Star List ne certifie jamais la licence des modèles, des voix, des images ou du contenu généré.

## Première implémentation de ce pivot

Le module `automate_ytb/scene_plan.py` produit un manifeste JSON en lecture/écriture locale **sans appels aux modèles ni publication**. Il enregistre une bible de style et de personnage, la durée, les consignes d'image de chaque plan et les timecodes. Toutes les images sont marquées non approuvées par défaut.

```sh
python -m automate_ytb.scene_plan \
  --topic "Pourquoi un œuf peut-il avoir deux jaunes ?" \
  --script mon-scenario-original.txt \
  --character "Une mascotte originale, poussin orange avec des bottes vertes" \
  --duration 900 --shot-seconds 6 --output plan-scenes.json
```

Pour une vidéo de 900 secondes avec plans de six secondes, **150 unités narratives distinctes sont nécessaires**. Si le scénario est trop court, le programme signale le manque au lieu de fabriquer un récit pour remplir artificiellement la durée.

**À développer :** connecteur images, génération réellement automatisée et contrôlée, audio naturel, export MP4 depuis `scene-plan.json`, vérification réelle du rendu, visualisation Android et reprise après interruption. Le module livré est un planificateur, **pas un générateur vidéo IA complet**.
