<p align="center"><img src="identite/phoebe-logo.svg" alt="Phoebe" width="320"></p>

# Phoebe

**[Site du projet et maquette 3D](https://guillaumegodet.github.io/phoebe/)** · [Identité graphique](https://guillaumegodet.github.io/phoebe/identite/) · [Participer](https://guillaumegodet.github.io/phoebe/#participer)

Véhicule amphibie léger : un trike couché à assistance électrique qui roule, flotte et vole sur foils.

Le nom vient de la titanide Phoebé, fille d'Ouranos et de Gaïa : « je vais en Phoebe » = amphibie.

**État : étude de concept.** Rien ici n'est calculé ni validé par essai. Les cotes, épaisseurs et sections sont des choix de départ.

## Contenu

| Dossier | Contenu |
|---|---|
| `cad/phoebe_cad.py` | Modèle paramétrique CadQuery : coque, squelette, interfaces |
| `cad/out/` | Fichiers générés : assemblage STEP, gabarits DXF à l'échelle 1, aperçu, bilan |
| `CLAUDE.md` | Mémoire du projet : décisions, chiffres de référence, points ouverts |
| `maquette/index.html` | Maquette 3D interactive (three.js), à ouvrir dans un navigateur |

## Régénérer les fichiers

```bash
pip install cadquery shapely ezdxf matplotlib
python3 cad/phoebe_cad.py cad/out
```

Tous les réglages sont dans le bloc `Params` en tête du script. Unités : millimètres. Repère : X vers l'avant, Y vers bâbord, Z vers le haut, Z = 0 au sol en mode route.

## Architecture

- Coque de 2,58 m en lattes d'épicéa et toile tendue (technique skin-on-frame), sur un squelette en contreplaqué : poutre de quille en caisson, 13 couples, étrave et tableau arrière pleins.
- Roue avant directrice relevable devant l'étrave, deux roues arrière motrices sur bras relevables.
- Deux foils avant repliables sur le plat-bord, un foil arrière orientable qui porte le moteur immergé.
- Moteur de pédalier 250 W pour la route, moteur immergé d'environ 1 kW pour l'eau.

## Interfaces modélisées

| Interface | Principe | Pièces du commerce supposées |
|---|---|---|
| Charnières des foils avant | Deux joues alu de 6 mm prennent le couple porteur en sandwich (4 vis M8). Une chape pivote autour d'un axe de 12 mm et se verrouille par goupille, repliée ou déployée. | Mât de foil à platine (entraxe 165 × 90 à vérifier) |
| Arbre arrière | Arbre de 25 mm, paliers à semelle vissés sur la face avant du couple porteur, contre-plaques alu à l'arrière. | Paliers type UCP205 |
| Direction avant | Console pivotante entre deux joues alu boulonnées sur l'étrave, verrouillée par goupille. Elle porte un jeu de direction classique et une fourche de 20 pouces. | Fourche et jeu de direction 1 1/8 |
| Bras des roues arrière | Deux flasques alu de 6 mm par roue, pivotant sur l'arbre. Une goupille les verrouille sur une équerre fixée au couple porteur, en position route ou relevée (69°). Chaîne entre les flasques. | Moyeu arrière de 110 mm à roue libre (type BMX), roue de 20 pouces |
| Foil arrière | Tête de safran relevable : deux joues alu pivotent sur deux fémelots vissés au tableau (direction), le mât pivote entre les joues (relevage), avec trois positions de goupille. Palonnier pour les câbles. | Mât de foil, moteur immergé |
| Siège | Deux rails alu posés sur les varangues, assise et dossier en contreplaqué de 9 mm. | |

Dans l'assemblage STEP, le côté bâbord est en configuration eau (foil déployé, roue relevée) et le côté tribord en configuration route (foil replié, roue au sol).

Cotes qui découlent de ces interfaces : largeur hors tout sur route d'environ 1,00 m (imposée par les moyeux arrière), envergure des foils avant déployés d'environ 1,74 m.

Non modélisé à ce stade : commande de direction (leviers vers la fourche et vers le palonnier arrière), transmission complète (chaîne du pédalier à l'arbre), freins, étanchéité des sorties d'arbre, visserie.

## Avertissement

Ce dépôt décrit un prototype non construit. Avant toute navigation : calcul ou essai statique de la structure, vérification de la flottabilité, et respect des règles de circulation et de navigation locales.
