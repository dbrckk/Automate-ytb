# Automate-ytb — plan qualité professionnelle (4 novembre 2026)

## État réellement vérifié

Base de travail : `main` au commit `e43e5d99a8851a1500d35cf560df219afb54e5d4`.
Le pipeline sait créer un Short original 1080×1920/30 FPS H.264/AAC, sous-titres issus des durées de phrases Kokoro, mix musique/voix, QA FFprobe et rendu scientifique thématique. Les courants océaniques ont une option **vraie 3D Blender/Cycles**, validée par CI. Volcans et aurores utilisent actuellement des scènes surtout 2,5D. La dernière vidéo aurorale n'est donc pas une preuve de 3D généralisée.
PR ouvertes antérieures (dont #174 volcan) laissées intactes.

## Cible produit

Créer des vidéos scientifiques de 30–60 s qui se soutiennent visuellement et auditivement sur smartphone **sans images fixes déguisées en vidéo**, sans voix robotique, sans média sans licence, sans API obligatoire payante, sans intervention PC. Chaque amélioration doit augmenter la valeur perçue **sans dégrader la fiabilité**.

| Rang | Axe | Déficit initial | Livraison et critères quantifiables | État |
|---|---|---|---|---|
| P0 | **Plans 3D réellement animés** | 3D réservée aux courants océaniques ; aurores et autres scènes trop schématiques | Étendre Blender headless aux cinq phases aurorales : modèles spatiaux et atmosphériques, rideaux 3D, lumière émissive, caméra à trajectoire, 10+ poses distinctes par plan ; rendu MP4 réel + contact sheet des cinq scènes | **Première tranche engagée dans cette PR** |
| P0 | **Direction visuelle / cadrage** | Composition répétitive, illustrations plates, manque de lumière et volume | Palette et éclairage propres à chaque cause ; premiers/seconds plans ; caméra motivée ; titres et sous-titres dans les zones sûres ; audit d'images décodées avant/après | À poursuivre après la tranche aurorale |
| P0 | **Voix naturelle** | Synthèse par fragments, rythme parfois découpé malgré Kokoro | Comparaison aveugle des quatre voix sur le même texte ; groupes de phrases respirables, débit conservatif ; choix anglais/français ; vérifier les vrais WAV/MP3, attaques, fins, prononciation | Déjà Kokoro ; améliorations à venir |
| P1 | **Action ↔ son ↔ caméra** | Synchronisation à la phrase plutôt qu'aux mots, actions souvent indépendantes | Cue list stable issue du script et du PCM ; objets réagissant réellement aux événements ; pas d'alignement phonémique revendiqué sans ASR mesuré | À venir |
| P1 | **Sound design & mixage** | Musique de fond générique, peu d'effets causaux | Créer des bruitages originaux libres, ducking limité, loudness intégrée cible -16 LUFS, true peak mesuré, transitions propres | À venir |
| P1 | **Montage cinématographique** | Durées/plans peu variés et cuts parfois prévisibles | Rythme par beat, 3 échelles de plan, raccords de mouvement, animations d'entrée/sortie sans amputer la voix ; test avant/après | À venir |
| P1 | **QA de livraison** | QA technique ≠ qualité artistique, seulement échantillons décodés | Contrôle duration/codec/FPS/audio/SRT, images début-milieu-fin par scène, artefacts visibles, galerie & écoute mobile, rapport + signature de l'absence de validation humaine | Déjà technique ; revue artistique obligatoire |
| P2 | **Rendu haute fidélité** | 10 poses 3D interpolées → ghosting possible | Profil de rendu 3D avec plus de poses natives et de samples après mesure CPU ; budget de temps, mémoire, facture Actions documentés ; ne pas remplacer la prévisualisation rapide | À venir |
| P2 | **Scalabilité et Android** | 3D lente et encore limitée à quelques domaines | Mode `2d` fiable par défaut, `3d` opt-in ; un clic depuis Actions, fichiers MP4 et rapports téléchargeables ; presets reproductibles sans clé payante | En cours |

## Première tranche appliquée : aurores boréales en 3D

1. Ajouter au moteur Blender **cinq scènes distinctes** : vent solaire, champ magnétique, collisions, émission et rideaux auroraux.
2. Générer de vrais maillages 3D animés : courbes de champ, particules, couche atmosphérique, rideaux maillés, horizon et globe éclairé ; caméra mobile par scène.
3. Remplacer **uniquement l'arrière-plan d'illustration** pour les aurores dans le compositeur : protéger les textes, les étapes causales existantes et les sous-titres synchronisés ; pas de régression océan.
4. Pré-calculer les poses par Blender CPU ; SHA256, whitelist des noms et dimensions, cache borné, rejet explicite des corruptions ; aucun faux fallback « 3D ».
5. Créer un workflow dédié de Short anglais Kokoro 1080×1920/30fps et une planche-contact des 5 scènes pour revue.
6. Accepter uniquement si : suite existante verte, vrai rendu Blender terminé, MP4 FFprobe + QA réussis, cinq scènes visuellement distinctes et mobiles, sans occultation des sous-titres.

**Limites honnêtes :** 3D originale stylisée, non photoréalisme ni simulation de magnétosphère ; interpolation des poses 3D, non 30 images Cycles indépendantes par seconde ; évaluation humaine obligatoire pour voix, esthétique et précision scientifique. Aucune publication YouTube automatique.

## Mesures suivies pour chaque rendu

- **Fiabilité** : CI verte, nombre de scènes, artefact MP4 décodable, conformité 1080×1920/30 FPS, SRT non coupés, aucune image manquante.
- **Mouvement** : poses 3D réellement différentes, zéro séquence figée détectée par l'échantillonnage ; ne pas transformer le taux de pixels modifiés en « score artistique ».
- **Voix** : échantillons comparatifs réels, contrôle des silences, loudness, consonnes/intonation à l'écoute.
- **Visuel** : profondeur, cohérence lumière, contraste des titres/sous-titres, palette et variété des plans sur une planche-contact.
- **Coût** : poids des artefacts et durée GitHub Actions observés, sans promettre la gratuité illimitée des runners.

## Critère de fin de version professionnelle

Les critères techniques sont nécessaires mais insuffisants. Le produit ne pourra être présenté comme **niveau professionnel** qu'après examen visuel et sonore de plusieurs vidéos sur différents sujets et résolution des défauts constatés ; les CI vertes ne constituent pas une certification artistique.
