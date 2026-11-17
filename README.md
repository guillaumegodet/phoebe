<p align="center"><img src="identite/phoebe-logo.svg" alt="Phoebe" width="320"></p>

# Phoebe

**[Site du projet et maquette 3D](https://guillaumegodet.github.io/phoebe/)** · [Identité graphique](https://guillaumegodet.github.io/phoebe/identite/) · [Discussions](https://github.com/guillaumegodet/phoebe/issues)

Véhicule amphibie léger : un trike couché à assistance électrique qui roule, flotte et vole sur foils.

Dans la mythologie grecque, Phébé ou Phœbé (en grec ancien Φοίϐη / Phoíbē, « brillante ») est une Titanide, fille d'Ouranos (le Ciel) et de Gaïa (la Terre). Par ailleurs, Phoebe dans Friends est jolie, attachante et un peu barrée, comme ce projet. 

**État : étude de concept.** Rien ici n'est calculé ni validé par essai. Les cotes, épaisseurs et sections sont des choix de départ.

## Contenu

| Dossier | Contenu |
|---|---|
| `cad/phoebe_cad.py` | Modèle paramétrique CadQuery : coque, squelette, interfaces, transmission, direction, freins |
| `cad/verifier.py` | Contrôle après modification : solides valides, relecture du STEP, collisions entre pièces |
| `cad/devis_masses.py` | Devis de masses : masse à vide, centre de gravité, charge sur les roues (à l'estime) |
| `cad/out/` | Fichiers générés : assemblage STEP, gabarits DXF à l'échelle 1, aperçu, bilan |
| `CLAUDE.md` | Mémoire du projet : décisions, chiffres de référence, points ouverts |
| `maquette/index.html` | Maquette 3D interactive (three.js), à ouvrir dans un navigateur |

## Régénérer les fichiers

```bash
pip install cadquery shapely ezdxf matplotlib
python3 cad/phoebe_cad.py cad/out
```

Après une modification, `python3 cad/verifier.py` régénère les fichiers puis contrôle les solides et les collisions (une dizaine de minutes ; `--seulement motif1,motif2` limite le contrôle aux pièces nommées).

Tous les réglages sont dans le bloc `Params` en tête du script. Unités : millimètres. Repère : X vers l'avant, Y vers bâbord, Z vers le haut, Z = 0 au sol en mode route.

## Architecture

- Coque de 2,58 m en lattes d'épicéa et toile tendue (technique skin-on-frame), sur un squelette en contreplaqué : poutre de quille en caisson, 13 couples, étrave et tableau arrière pleins.
- Roue avant directrice relevable devant l'étrave, deux roues arrière motrices sur bras relevables.
- Pédalier sur une potence encastrée dans la poutre de quille. La chaîne court dans le caisson, sous le siège, jusqu'à l'arbre transversal.
- Deux leviers de part et d'autre du siège commandent par câbles la fourche avant et la tête de safran arrière.
- Deux foils avant repliables sur le plat-bord, un foil arrière orientable qui porte le moteur immergé.
- Une seule machine électrique sur l'arbre transversal : moteur d'assistance de 250 W sur route, génératrice sur l'eau. Moteur immergé de 1,5 à 2 kW pour l'eau.

## Interfaces modélisées

| Interface | Principe | Pièces du commerce supposées |
|---|---|---|
| Charnières des foils avant | Une ferrure porteuse en aluminium : deux tôles de 6 mm d'un seul tenant, d'une charnière à l'autre, prennent le couple porteur en sandwich (14 vis M8) et reprennent la flexion au-dessus de la poutre de quille. Une chape pivote autour d'un axe de 12 mm et se verrouille par goupille, repliée ou déployée. | Foil en L d'une seule pièce à coude arrondi, sur platine (entraxe 165 × 90 à vérifier) |
| Sabots de verrouillage des foils | Une console en aluminium sur le flanc, 152 mm sous la charnière, terminée par une chape. Un tenon fixé au mât y entre quand le foil se déploie ; une goupille les traverse. Deux tirants serrent le sabot autour du couple porteur et de sa ferrure, jusqu'à une contre-plaque intérieure. | Tirants M8, goupille de 10 mm |
| Arbre arrière | Arbre creux de 25 × 3 mm, paliers à semelle vissés sur la face avant du couple porteur. À l'arrière, une ferrure porteuse en aluminium de 4 mm, d'un palier à l'autre, reprend la flexion au-dessus de la poutre de quille. | Paliers type UCP205 |
| Direction avant | Console pivotante entre deux joues alu boulonnées sur l'étrave, verrouillée par goupille. Elle porte un jeu de direction classique et une fourche de 20 pouces. | Fourche et jeu de direction 1 1/8 |
| Bras des roues arrière | Deux flasques alu de 6 mm par roue, pivotant sur l'arbre et tournés vers l'arrière : les roues sont 270 mm derrière l'arbre, pour charger la roue avant (empattement de 2,40 m). Une goupille les verrouille sur une patte de la ferrure porteuse, prolongée par une éclisse sur le plat-bord, en position route ou relevée (69°). Chaîne entre les flasques. | Moyeu arrière de 110 mm à roue libre (type BMX), roue de 20 pouces |
| Foil arrière | Tête de safran relevable : deux joues alu pivotent sur deux fémelots vissés au tableau (direction), le mât pivote entre les joues (relevage), avec trois positions de goupille. Une corne des joues porte le palonnier sur l'axe de direction, au-dessus du pont. | Mât de foil, moteur immergé |
| Siège | Deux rails alu posés sur les varangues, assise et dossier en contreplaqué de 9 mm. Le siège coulisse de 180 mm pour s'adapter au pilote, de 1,55 m à 1,89 m environ ; le pédalier est fixe. Crans et verrou non dessinés. | |
| Pédalier | Potence en contreplaqué de 18 mm, encastrée dans la poutre entre les couples +320 et +540, boîtier pris entre deux platines alu de 4 mm. Boîtier décalé de 10 mm vers bâbord pour amener la chaîne dans le caisson. | Pédalier courant sans moteur (ligne de chaîne supposée de 45 mm), manivelles de 170 mm |
| Transmission primaire | Plateau de 42 dents, pignon de 16 dents sur le moyeu à vitesses. Le brin tendu passe sous deux galets vissés sur la semelle haute et file droit dans le caisson. Le brin mou revient dans un fourreau posé au fond. Deux lumières dans la semelle haute, entre les couples. | Chaîne au pas de 12,7 mm (236 maillons), galets dentés de 15 et 11 dents, fourreau de chaîne |
| Relevage des foils | Un secteur à gorge sur chaque foil, centré sur son axe. Foils avant : bout vers un taquet sur le plat-bord, sandow de rappel. Foil arrière : secteur sur l'axe de relevage, poulie sur le tableau, palan à six brins dans le cockpit. Masses des foils supposées. | Cordage, taquets coinceurs, filoirs, sandow, poulies de palan |
| Machine d'arbre | Un moteur sans balais en prise permanente sur l'arbre transversal : couronne de 36 dents, pignon de 11 dents. Platine alu vissée sur le flanc tribord de la poutre, derrière le couple porteur. Moteur d'assistance sur route, génératrice sur l'eau. | Moteur sans balais lent (encombrement de 63 mm supposé), chaîne de 44 maillons, deux variateurs |
| Changement de vitesses | Moyeu de vélo à huit vitesses monté en renvoi sous le dossier, entre deux platines vissées sur les flancs de la poutre. Un pignon de 16 dents sur sa fixation de disque entraîne le pignon de 24 dents de l'arbre par une chaîne courte, à bâbord. Lumières de tension dans les platines. Poignée tournante sur le levier tribord. | Moyeu à vitesses intégrées à frein à disque (cotes à vérifier), pignon pour fixation de disque, chaîne de 36 maillons, poignée tournante et sa gaine |
| Commande de direction | Deux leviers pivotant sur un longeron d'épicéa fixé aux couples. Chaque levier tire deux câbles sous gaine : un vers le palonnier de fourche (même côté), un vers le palonnier de la tête de safran (croisé). Les gaines courent sous le plat-bord puis sur les ponts : aucune traversée de coque. | Câbles et gaines de frein de vélo, butées réglables |
| Freins | Tambours dans les deux moyeux arrière, commandés ensemble par un levier à double tirage (levier de direction bâbord). Disque sur la roue avant (levier tribord). | Moyeux arrière à tambour et roue libre, étrier mécanique, disque de 160 mm |
| Sorties d'arbre | Une platine en contreplaqué collée contre le couple porteur reçoit un tube traversant. La toile est pincée entre deux brides autour du tube. Un joint à lèvre ferme le tube côté extérieur. | Joint à lèvre 25 × 35 × 7, tube alu 44 × 35 |

Dans l'assemblage STEP, le côté bâbord est en configuration eau (foil déployé, roue relevée) et le côté tribord en configuration route (foil replié, roue au sol).

Cotes qui découlent de ces interfaces : largeur hors tout sur route d'environ 1,00 m (imposée par les moyeux arrière), envergure des foils avant déployés d'environ 1,74 m.

Chiffres de la transmission et de la direction (voir `cad/out/bilan.json`) : huit vitesses, de 1,45 à 4,44 m par tour de pédalier, soit 7 à 21 km/h à 80 tr/min ; 30° de braquage pour 23° de débattement des leviers.

Non modélisé à ce stade : variateurs, batterie et capteur de pédalage, carters de chaîne, chaînes des bras arrière, dernier tronçon des gaines de frein arrière (la boucle qui suit le relevage du bras), découplage de la direction entre route et eau, visserie.

## Droits

© 2026 Guillaume Godet. Tous droits réservés. Voir [LICENCE.md](LICENCE.md). Le contenu peut être consulté, mais ni copié, ni modifié, ni utilisé pour fabriquer ou vendre quoi que ce soit sans accord écrit.

## Avertissement

Ce dépôt décrit un prototype non construit. Avant toute navigation : calcul ou essai statique de la structure, vérification de la flottabilité, et respect des règles de circulation et de navigation locales.
