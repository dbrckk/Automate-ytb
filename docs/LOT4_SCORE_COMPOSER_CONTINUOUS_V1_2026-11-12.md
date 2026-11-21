# ScoreComposer V1 — partition continue originale (lot 4)

**Date :** 12 novembre 2026. **État :** implémentation opt-in sur la branche de développement ; validation CI et évaluation esthétique humaine requises avant déclaration de qualité finale.

## Modification du processus de production

Le soundtrack historique `ambient` génère une boucle de huit secondes à 16 kHz mono et redémarre les notes/fondus sur chaque scène. Le nouveau mode `score` compose un accompagnement **pour l'épisode entier** sur une seule horloge, à **48 kHz stéréo**, sans remise à zéro entre les scènes. Il ne remplace pas le rendu existant par défaut.

- Profils : `discreet`, `documentary` (par défaut), `mysterious`, `energetic`.
- Harmonie : gamme pentatonique originale, quatre voicings, basse, pad stéréo à légers écarts de fréquence, motif d'arpège, pulsation et accents dramatiques.
- Arc narratif global : progression, respiration, révélation et résolution, modulées selon la durée réelle du script audio. Une révélation *explicitement déclarée* dans `masterTimeline.soundCues` guide le pivot musical et marque l'échantillon de l'accent correspondant ; à défaut, le moteur utilise un pivot dramaturgique heuristique déclaré comme tel, jamais présenté comme un alignement de mot.
- Aucune musique téléchargée, aucun sample pack, aucune API, aucun abonnement, pas de copie de mélodies existantes. Synthèse par blocs PCM bornés en mémoire et rythme déterministe.
- Les scripts à voix naturelle restent prioritaires : l'actuel mix FFmpeg compression de la musique sous la narration, limitation et loudnorm est conservé ; la vidéo finale H.264/AAC et la chaîne Foley restent inchangées.
- Limite sûre de la première tranche : épisodes complets de 12 à 180 secondes. Le mode `score` refuse `--limit` au lieu de prétendre posséder un arc musical complet depuis un simple extrait. Le rendu n'est pas activé rétroactivement pour d'anciens plans.

## Choisir le nouveau moteur

Depuis Android : GitHub Actions → **One-click YouTube preview (free)** → option `soundtrack: score`. Dans l'interface native, le profil musical est `documentary`.

En ligne de commande :

```bash
python -m automate_ytb.episode --plan build/scene-plan.json --output build/video --style science --resolution shorts --voice kokoro --caption-timing audio --soundtrack score --score-mode documentary
python -m automate_ytb.quality --plan build/scene-plan.json --output build/video --expect-voice kokoro --expect-soundtrack score
```

Les prérequis Kokoro restent ceux du pipeline existant. Il faut un plan et des assets originaux approuvés. La commande n'invente pas des événements visuels ou une vidéo.

## Preuves de production

- `background-original.wav` : PCM 16-bit stéréo 48 kHz avec durée exacte arrondie au sample.
- `score-report.json` : profil, tempo, durée, mode de continuité, source des événements, marqueurs exacts (`atSample`), SHA-256 du WAV, provenance originale et état de revue humaine.
- `episode-report.json` : manifeste de l'étape musicale et son moteur, `publicationApproved: false`.
- `quality.check` : rejette un WAV absent/altéré, un rapport manquant/altéré, une fréquence/durée inexacte et une composition non attestée. L'AAC exporté passe en plus les contrôles techniques médias déjà en place.
- `tests/test_score_composer.py` : même SHA après deux compositions, horloge continue aux frontières des scènes, stéréo non-identique, événements visuels réels, entrée invalide, MP4/AAC réellement encodé, altération du WAV détectée.
- Workflow dédié `.github/workflows/original-score-composer.yml` et contrôles de régression `test_soundtrack.py` et `test_foley_engine.py`.

## Limites ouvertes

Le moteur produit une **musique synthétique structurée**, non une orchestration acoustique de niveau studio. Le pivot hors MasterTimeline est heuristique. L'écoute humaine à faible volume sur téléphone et au casque, l'A/B face aux vidéos déjà sorties, les tests Kokoro + score + Foley sur un même Short inédit et le contrôle EBU R128 **après** AAC restent obligatoires. Le score final ne vaut pas autorisation de publication. L'accompagnement musical d'anciennes vidéos reste en `ambient` tant qu'il n'est pas explicitement changé.

**Suite :** évaluer un Short multi-scènes de 30–45 secondes avec voix Kokoro et accents visuels ; enrichir le timbre et la progression après écoute. Ne pas confondre conformité technique et qualité artistique.
