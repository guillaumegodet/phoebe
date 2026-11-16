# Phoebe

Véhicule amphibie léger : un trike couché à assistance électrique qui roule, flotte et vole sur foils. Inspiré du trike open-source [Moskitos](https://moskitos.org/).

Le nom vient de la titanide Phoebé, fille d'Ouranos et de Gaïa : « je vais en Phoebe » = amphibie.

**État : étude de concept.** Rien ici n'est calculé ni validé par essai. Les cotes, épaisseurs et sections sont des choix de départ.

## Contenu

| Dossier | Contenu |
|---|---|
| `cad/phoebe_cad.py` | Modèle paramétrique CadQuery : coque, squelette, interfaces |
| `cad/out/` | Fichiers générés : assemblage STEP, gabarits DXF à l'échelle 1, aperçu, bilan |
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

## Avertissement

Ce dépôt décrit un prototype non construit. Avant toute navigation : calcul ou essai statique de la structure, vérification de la flottabilité, et respect des règles de circulation et de navigation locales.
