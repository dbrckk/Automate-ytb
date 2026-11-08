# P3.2 — Premier contact réel personnage–décor dans le moteur 2.5D

**Base vérifiée :** PR #220 fusionnée sur `main` au commit `18aae93ae609b631c7a13ee2f7ff28d300d5833a`.

## Livrable de cette PR

- La fleur originale est attachée à la **coordonnée monde du prochain appui de la patte droite**, calculée avec le moteur IK analytique existant `walking_leg`. Le moment d'impact vaut exactement `1.5 * PERIOD`, sans détection d'objet simulée ou collision inventée.
- Lorsqu'un appui valide a eu lieu, la tige se courbe, se comprime, rebondit et revient progressivement vers sa pose de repos. **Avant ce contact : aucune compression, aucun pétale détaché ni son d'impact.**
- Les pétales suivent 11 trajectoires originales indépendantes (direction, vitesse, gravité, traînée temporelle) et sont composés dans leur couche Z de premier plan. La fleur est placée derrière l'animal pour conserver l'occultation réelle par le corps et la patte.
- Les oreilles, la queue et un clignement des yeux suivent une courbe de réaction causale de courte durée, pour les **trois espèces** déjà intégrées.
- Le son d'impact est **synthétisé localement en PCM 48 kHz** à partir de `IMPACT_TIME`, puis encodé en AAC avec le MP4 par FFmpeg, sans fichier musical tiers ni service payant.
- Le mode `--interaction` est opt-in. Les appels existants, sans cette option, ne changent pas et gardent la marche validée auparavant.
- Le manifeste QA ajoute l'instant et les coordonnées de l'appui, le chemin des couches et l'indicateur d'absence de publication. L'intégrité des os, la fixation au sol, le profil vidéo 1080×1920/30 fps et le décodage MP4 sont toujours testés.

### Reproduction

```sh
python -m unittest discover -s tests -p test_forest_contact25d.py -v
python scripts/render_25d_character_pilot.py --animal fox --interaction --output out/p3-fox-25d/fox-flower-contact.mp4
python scripts/render_25d_character_pilot.py --animal rabbit --interaction --output out/p3-rabbit-25d/rabbit-flower-contact.mp4
python scripts/render_25d_character_pilot.py --animal cat --interaction --output out/p3-cat-25d/cat-flower-contact.mp4
```

Le workflow `p3-25d-character-pilot.yml` exécute **trois vrais rendus et contrôles indépendants**, dépose leurs MP4 + captures + QA dans GitHub Actions et ne considère pas le prototype comme publiable. La suite générale `Validate production pipeline` est également requise avant fusion.

### Limites et prochain chantier

Il s'agit d'une réaction déterministe **réalisée graphiquement**, pas d'une simulation universelle de collisions. Les mouvements et couleurs sont des dessins 2D à profondeur 2.5D, pas un modèle 3D. **Ce n'est pas encore un Short narré : aucune voix Kokoro dans ce pilote**, et aucune validation esthétique humaine n'est revendiquée.

La prochaine étape doit intégrer de tels événements à une scène structurée *action → conséquence → réaction*, avec narration naturelle, sans changer les événements après synthèse de la voix.
