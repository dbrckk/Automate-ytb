# V2 — activation automatique d'un acteur visuel persistant dans les Shorts scientifiques

**Statut :** générateur original facultatif, à valider sur la CI et par revue humaine. Il **ne transforme pas** encore la musique et n'insère **aucun bruitage dans le mix final** ; les événements sonores sont des données auteur prêtes pour l'étape Foley.

## Pourquoi

Un projet capable de recevoir manuellement une \`masterTimeline\` a besoin d'un véritable *auteur de scènes* pour fonctionner sur de nouveaux épisodes. Ce générateur fournit cette première passerelle, sans toucher au moteur de production existant tant que le mode facultatif n'est pas activé.

## Usage direct par workflow GitHub Actions

Ouvrir **Actions → One-click YouTube preview (free) → Run workflow** et choisir :

- \`style: science\`, \`resolution: shorts\`, \`voice: kokoro\`, \`language: en\`, \`render_profile: high\`.
- \`continuous_world: true\` pour activer l'acteur persistant et la caméra illustratifs dans tous les plans.
- Fournir un script original de cinq phrases avec une suite de causalités reconnues. Le moteur refuse d'inventer une transition si les cinq étapes sont ambiguës.

Les appels existants à la workflow réutilisable restent inchangés : le nouvel input \`continuous_world\` est **facultatif** et vaut \`false\` par défaut. Les autres genres restent en mode historique tant qu'un routeur multi-genres n'est pas réellement validé.

## Script local

~~~bash
python -m automate_ytb.scene_plan \
  --topic "How ocean currents move heat" \
  --script original-script.txt --character "An original science illustration" \
  --duration 30 --shot-seconds 6 --output build/scene-plan.json

python -m automate_ytb.science_world_preset --plan build/scene-plan.json
~~~

La commande lit et valide le plan original, **génère un objet original** \`concept-marker\`, ses déplacements x/y, une caméra globale et cinq événements audio documentés, vérifie l'ensemble via \`MasterTimeline\`, puis sauvegarde le plan atomiquement. Pas de remplacement si une timeline originale existe déjà. Pas de média tiers, pas de modèle IA distant, pas de fichier privé ajouté à GitHub.

## Cinq suites sémantiques prises en charge

| Sujet | Étapes reconnues | Élément |
|---|---|---|
| Courants océaniques | solar → wind → coriolis → sinking → heat | Marqueur conceptuel de circulation |
| Arc-en-ciel | sunlight → refraction → reflection → emergence → arc | Repère d'évolution d'un rayon |
| Éclair | charge → leader → connection → return → thunder | Repère conceptuel de décharge |
| Aurore | solar_wind → magnetic_field → collisions → emission → curtains | Repère d'évolution de particule |
| Volcan | magma → pressure → ascent → eruption → lava | Repère de matière en transformation |

Les trajectoires sont **illustratives**, et non des simulations physiques exactes. Aucun chiffre ni quantité physique n'est généré arbitrairement. Une direction artistique détaillée et une vérification scientifique restent nécessaires. Le moteur existant dessine ses scènes 2.5D réelles ; \`master_timeline_art.py\` ajoute l'acteur continu sous les textes mobiles.

## Contrat temporel

- Chaque mouvement est ancré à \`scene-NNN/fraction\`, **pas** à une durée fixe en secondes.
- Après synthèse vocale Kokoro, les scènes peuvent durer 34,42 s au lieu de 30 s ; l'adaptateur recalcule les frames d'après les vraies limites en millisecondes.
- Les propriétés \`x,y,scale\` et la caméra restent continues aux frontières des cinq scènes et partagent la même horloge de frames.
- Les cinq cues acoustiques référencent les événements visuels, mais **le mix final ne les utilise pas encore** ; cette limitation est explicitement déclarée dans les manifests.

## Validation / clôture

- [ ] Les tests spécialisés couvrent cinq sujets, vraies durées fractionnaires et refus des scripts non reconnus.
- [ ] Le workflow One-click avec \`continuous_world: true\` génère un MP4 narré réel.
- [ ] Le QA du MP4, les captions et le lien GitHub Release fonctionnent sans régression.
- [ ] Revue humaine des raccords, de la hiérarchie des plans et de la qualité visuelle sur smartphone.
- [ ] Le FoleyEngine mixe effectivement les cues en audio pour les vidéos futures.
- [ ] Un rendu multi-genres hors science est démontré.

**Objectif de cette tranche :** passer de « moteur utilisable uniquement par programmation » à « générateur activable depuis la production existante ». Ne pas confondre ce résultat avec une certification de qualité finale équivalente à la référence utilisateur.
