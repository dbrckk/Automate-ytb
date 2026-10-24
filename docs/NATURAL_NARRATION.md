# Narration neuronale locale : Kokoro-82M

Automate-ytb peut maintenant synthétiser les narrations originales de scènes
en français et en anglais avec Kokoro. Le mode eSpeak reste par défaut pour
les brouillons rapides et entièrement reproductibles.

## Android, sans PC

1. Ouvrir le workflow [One-click YouTube preview](https://github.com/dbrckk/Automate-ytb/actions/workflows/one-click-preview.yml).
2. Choisir Run workflow, saisir un scénario original et sélectionner Voice = kokoro.
3. Sélectionner le français ou l'anglais, et télécharger l'artefact produit.
4. Vérifier la piste narration.wav, la vidéo preview.mp4 et les sous-titres SRT.

Le workflow n'appelle pas de service TTS facturé à la requête. En revanche,
le modèle et le moteur PyTorch CPU sont téléchargés à la première exécution :
cela consomme du temps de calcul GitHub Actions, soumis aux quotas du compte.

## Installation locale

Python 3.12, FFmpeg et espeak-ng sont recommandés. Pour un serveur CPU :

    python -m pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.3,<3"
    python -m pip install -e '.[speech]'

Puis, avec un scene-plan.json déjà créé :

    python -m automate_ytb.episode --plan project/scene-plan.json --output project/video --style cartoon --language fr --voice kokoro

Voix disponibles : ff_siwis (français, défaut), af_heart (anglais, défaut),
af_bella et am_michael (anglais). Le paramètre --voice-name accepte ces choix
selon la langue. Aucun clonage ou imitation de voix d'une personne réelle.

Le modèle [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) est publié sous
Apache-2.0 ; il convient de vérifier les informations relatives aux voix et
aux attributions des données avant la distribution commerciale.

## Synchronisation et limites

Le modèle est chargé une fois par épisode. Chaque scène reçoit son audio PCM,
assemblé dans un WAV mono avec de légères respirations. Les scènes trop courtes
sont prolongées en fonction de la durée réelle de la narration ; l'audio
n'est jamais tronqué pour tenir artificiellement en six secondes. Les
sous-titres restent alignés sur les scènes, pas mot par mot.

Le résultat doit être écouté avant publication : prononciation, pauses,
intensité et rythme ne sont pas garantis professionnels.

## Contrôles effectivement exécutés

- 46 tests locaux réussis sans exclusion, avec eSpeak disponible.
- Véritable synthèse française Kokoro 0.9.4 en Python 3.12 sur CPU, WAV 24 kHz.
- Intégration MP4 sur deux scènes originales à 1280 x 720, durée 12 secondes,
  avec flux vidéo et audio vérifiés par FFprobe.
- Tests du format moderne Kokoro Result.audio, des paramètres de voix,
  des fichiers audio invalides, de la continuité des scènes et du refus de
  modifier le plan après un échec.

Les vidéos longues de 150 scènes en voix Kokoro restent à valider en conditions
réelles. Il n'y a pas encore d'alignement mot par mot, de lip-sync automatique,
de publication YouTube ni de génération éditoriale factuellement garantie.

## Sous-titres pilotés par la durée de synthèse (mode `audio`)

Dans **One-click YouTube preview (free)**, l'option **Caption timing** propose
désormais `audio` (par défaut) ou `estimated` (ancien comportement).
En mode `audio`, eSpeak ou Kokoro synthétise séparément chaque fragment
correspondant à un bloc de sous-titres. Le programme enregistre les
échantillons PCM produits et les débuts réels de chaque fragment, avec une
courte pause contrôlée entre eux. Ces mesures alimentent directement les
timecodes des SRT et WebVTT. Aucun service d'alignement distant n'est appelé.

Le mode `estimated` conserve la synthèse complète de chaque scène et les
durées proportionnelles au nombre de mots ; il peut être plus rapide et
produire une prosodie plus continue, surtout avec de longues narrations.
En local : `python -m automate_ytb.episode --plan build/scene-plan.json --output build/video --voice kokoro --caption-timing audio`.

**Limites importantes :** le mode audio n'est pas de l'ASR, ne reconnaît pas
les mots réellement prononcés et n'effectue pas d'alignement phonétique.
Les phrases synthétisées séparément peuvent paraître moins fluides.
Le dernier sous-titre de chaque scène reste affiché jusqu'à la fin du plan,
y compris pendant un éventuel silence final. La qualité du rendu doit être
écoutée et examinée avant diffusion ; le programme n'autorise pas la publication.
