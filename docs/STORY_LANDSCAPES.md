# Décors originaux guidés par le scénario

Le moteur **cartoon** produit maintenant quatre compositions de paysages
dessinées localement avec Pillow, sans téléchargement d’assets et sans API
payante : forêt (par défaut), rivière, village et prairie.

La narration française et anglaise peut mentionner un changement de lieu.
Le décor persiste automatiquement au fil des scènes tant qu’un nouvel endroit
n’est pas explicitement mentionné. Ainsi : « Le renard suit la rivière »,
puis « Il observe une fleur » gardent le décor de rivière ; « Il arrive
au village » fait apparaître les maisons. Aucune mention explicite ne
signifie pas que le modèle invente un lieu.

Les paysages sont intégrés **aux images approuvées et aux clips MP4
encodés** : leurs paramètres sont liés à l’empreinte créative du plan,
et les anciens rendus ne sont pas silencieusement réutilisés après
modification du scénario. Le rapport `render-report.json` expose
`landscapes.byScene` et les types de décors utilisés.

Les environnements sont des dessins **2D procéduraux stylisés** avec
formes variées (ruisseaux, passerelles, maisons, chemins, fleurs et
papillons). Ce ne sont pas des environnements 3D, ni des images
génératives haut de gamme. La profondeur et le sens artistique
demandent encore une relecture humaine, en particulier pour les
nuances et les accessoires mis en avant.

L’utilisateur Android conserve exactement le même workflow
`One-click YouTube preview`, sans réglage obligatoire.
