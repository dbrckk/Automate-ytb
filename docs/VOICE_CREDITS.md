# Crédits et précautions — voix naturelles Kokoro

**Moteur et modèle :** Kokoro-82M v1.0, développé par hexgrad et contributeurs ;
modèle fourni sous licence **Apache-2.0**.

Modèle officiel : https://huggingface.co/hexgrad/Kokoro-82M

**Voix française par défaut :** `ff_siwis`, voix féminine issue du jeu
de données vocales SIWIS (langue française). La fiche officielle
`VOICES.md` mentionne cette source dans sa colonne **CC BY**.

Crédit SIWIS : SIWIS French Speech Synthesis Database, University of
Edinburgh, Centre for Speech Technology Research (2017),
https://doi.org/10.7488/ds/1705 (jeu de données CC BY 4.0).

Pour les vidéos distribuées, conserver les crédits du modèle et de la source
vocale lorsque requis ; vérifier également les licences des versions
exactes des composants utilisés. Ces crédits n'autorisent ni l'imitation
de la voix d'une personne sans consentement, ni l'emploi de contenus
protégés d'une tierce partie.

**Fonctionnement :** le modèle est téléchargé sur le runner GitHub Actions
lorsqu'une prévisualisation utilise Kokoro. Aucun appel à une API vocale
payante n'est nécessaire, mais le calcul du runner et le téléchargement
peuvent être longs. La qualité, la prononciation et le ton doivent être
écoutés avant toute publication ; le modèle français ne comprend qu'une
voix dédiée dans son catalogue officiel.

**Styles :** `natural` (0,94x), `gentle` (0,88x) et `lively` (1,04x)
modifient le **débit de génération natif**, pas l'identité du locuteur.
Des pauses ponctuées sont ajoutées uniquement entre phrases et
incluses dans les repères audio des sous-titres.

**Locuteurs proposés par le formulaire Android :** `auto` (voix par défaut
selon la langue), `af_heart` et `af_bella` (anglais, voix féminines),
`am_michael` (anglais, voix masculine) et `ff_siwis` (français).
La validation des langues interdit toute sélection incompatible. Le même
modèle Kokoro local est utilisé et aucun crédit API n'est ajouté.
Les crédits de chaque voix et les conditions de ses sources vocales doivent
être vérifiés dans la version du catalogue Kokoro effectivement distribuée ;
la prise en charge technique n'est pas une approbation commerciale automatique.
