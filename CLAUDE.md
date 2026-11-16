# Phoebe : mémoire du projet

Ce fichier garde l'état du projet d'une session de travail à l'autre : décisions prises, chiffres de référence, points ouverts. À mettre à jour à chaque évolution notable. Dernière mise à jour : 16 novembre 2026.

## Le projet

Phoebe est un véhicule amphibie personnel imaginé par Guillaume Godet (Nantes) : un trike couché à assistance électrique qui roule, flotte et vole sur foils, pensé pour passer de la route à la rivière (l'Erdre).

Le nom vient de la titanide Phoebé : « je vais en Phoebe » = amphibie.

Intentions de départ : carrosserie low-tech, très légère mais solide ; passage facile de la route à l'eau ; un véhicule attachant.

**État : étude de concept. Rien n'est construit, calculé ni essayé.**

## Décisions prises par Guillaume

- Roues arrière motrices et roue avant directrice placée devant l'étrave, plutôt qu'une roue avant motrice, qui aurait traversé la coque.
- Le projet ne se présente pas comme dérivé d'un autre véhicule : aucune référence à un projet d'origine, ni dans le dépôt ni sur le site.
- Assistance sur route par un moteur de pédalier (au sec), pas par des moteurs-roues.
- Objectif : le vol sur foils. Donc un second moteur, immergé, au pied du foil arrière, commandé depuis les leviers.
- Direction sur l'eau par le mât arrière orientable (poussée orientée).
- Équipements voulus : phares, batterie, capote faisant panneau solaire et rangeable pour voler, siège inclinable (mode sieste), housses de foils pour la route, squelette porteur.
- Variantes demandées : une version de série au design haut de gamme, une version avec siège enfant à l'arrière.
- Conception en CAO paramétrique (CadQuery), versionnée dans ce dépôt.

## Architecture retenue

- **Coque** : 2,58 m × 0,74 m, lattes d'épicéa de 18 × 18 mm et toile tendue vernie (skin-on-frame).
- **Squelette en contreplaqué** : poutre de quille en caisson 120 × 60 mm, 13 couples dont 2 cloisons étanches et 2 couples porteurs doublés, étrave prolongée, tableau arrière et gousset.
- **Pédalier** : sur une potence en contreplaqué de 18 mm encastrée dans la poutre, entre les couples +320 et +540 (x = 470, z = 570). Il est fixe : c'est le siège qui coulisse pour s'adapter au pilote. Il n'est plus sur l'étrave (voir « Pédalier reculé » plus bas).
- **Foils avant** : deux foils en L articulés sur le couple porteur avant (x = +100), repliés vers le haut sur route.
- **Foil arrière** : en T, sur une tête de safran relevable et orientable fixée au tableau.
- **Roues** : 20 pouces. Bras arrière relevables de 69° autour de l'arbre transversal ; console de direction avant relevable sur l'étrave.
- **Transmission** : plateau de 42 dents, chaîne dans le caisson de quille (plan y = −35), pignon de 16 dents sur l'arbre transversal de 25 mm (x ≈ −572), puis une chaîne et une roue libre par roue arrière. Brin tendu rectiligne entre deux galets vissés sur la semelle haute ; brin mou dans un fourreau au fond du caisson. Un seul rapport.
- **Direction** : deux leviers (x = −230, y = ±262) sur un longeron d'épicéa. Câbles sous gaine en va-et-vient : vers le palonnier de fourche du même côté, vers le palonnier de la tête de safran en croisant. Palonniers de ±75 mm, 30° de braquage. Les gaines passent sous le plat-bord puis sur les ponts, sans traverser la coque. Les deux directions restent reliées en permanence.
- **Freins** : tambours dans les moyeux arrière (un levier à double tirage, à bâbord), disque de 160 mm à l'avant (levier tribord). Un frein sur l'arbre ne servirait à rien : les roues libres sont dans les moyeux.
- **Sorties d'arbre** : platine en contreplaqué contre le couple porteur, tube traversant, toile pincée entre deux brides, joint à lèvre 25 × 35 × 7.

## Chiffres de référence

Calculés par le script (voir `cad/out/bilan.json`) :

| Grandeur | Valeur |
|---|---|
| Volume de coque sous le plat-bord | 416 L |
| Tirant d'eau à 135 kg (véhicule et pilote) | 154 mm |
| Tirant d'eau à 165 kg (avec un enfant) | 174 mm |
| Contreplaqué du squelette | ≈ 2,4 m², ≈ 12,3 kg en okoumé |
| Développement | 4,12 m par tour de pédalier, 19,8 km/h à 80 tr/min |
| Chaîne primaire | 3,14 m, 248 maillons |
| Hanche → axe de pédale, jambe tendue, siège reculé | 0,95 m |
| Réglage du siège | 180 mm de course : pilotes de 1,55 m (butée avant) à 1,89 m (butée arrière) ; Guillaume, 1,85 m, à 2 cm de la butée arrière |
| Pédalier au-dessus de l'assise | 0,30 m |
| Direction | 37,5 mm de course de câble, 23° de débattement des leviers |
| Lisses | 18,3 m, ≈ 2,7 kg |
| Largeur hors tout sur route | ≈ 1,00 m |
| Envergure des foils avant déployés | ≈ 1,74 m |

Estimés à la main, à confirmer :

- Masse à vide visée : 50 à 55 kg.
- Puissance pour voler : de l'ordre de 1 kW vers 20 km/h. Autonomie en vol inférieure à une heure avec 1 kWh.
- Budget du prototype : 6 000 à 12 000 € de matériel, médiane vers 8 000 €.
- Version de série : 18 000 à 25 000 € en petite série.

## Pédalier reculé (16 novembre 2026)

Le modèle précédent plaçait le pédalier sur l'étrave, à x = 950, z = 480. Trois choses ne tenaient pas :

- la cloison avant est à x = 1014 : ni le plateau ni les manivelles de 170 mm ne pouvaient tourner ;
- la hanche du pilote est vers x = −280 : il fallait des jambes de 1,18 m (la maquette web trichait ainsi) ;
- les talons passaient sous le niveau des varangues.

Le pédalier a donc été reculé de 48 cm et monté de 9 cm, sur une potence. Il est réglé pour Guillaume, qui mesure 1,85 m : siège presque en butée arrière, à sa position d'origine. Demande de Guillaume : le siège doit coulisser d'avant en arrière pour s'adapter au pilote. Il avance donc de 180 mm au plus sur ses rails pour les pilotes plus petits (environ 5 cm par 10 cm de taille). Les tailles sont estimées avec un rapport jambe / taille de 0,503 (`leg_ratio`), à vérifier sur un gabarit. Les leviers et le centrage des masses ne changent pas pour Guillaume ; un pilote petit se retrouve plus en avant des leviers, qui restent fixes. L'alternative, avancer le siège de 35 cm en gardant le pédalier près de l'étrave, chargerait mieux la roue avant mais déplacerait le centre de gravité : **c'est une décision d'architecture à confirmer par Guillaume**. Tout suit `bb_x` et `bb_z` dans `Params`.

Conséquences : l'avant du cockpit (x = 600 à 1014) est libre, et le prolongement de l'étrave vers l'arrière (x = 840 à 1014) ne sert plus au pédalier.

## Points durs connus

1. **Charnières des foils avant** : environ 3 kN par vis dans le contreplaqué à trois fois la charge. À valider par essai statique.
2. **Verrou des bras arrière** : il porte le poids sur route, environ 2,6 kN par vis à trois fois la charge.
3. **Régulation d'altitude des foils** : non conçue (palpeurs, foils en V ou volets).
4. **Largeur de 1,00 m**, imposée par les moyeux arrière standard. La réduire demande des roues en porte-à-faux.
5. **Roue arrière relevée proche de l'eau** : environ 3 cm au-dessus de la flottaison à 135 kg.
6. **Moyeu gauche** : roue libre inversée nécessaire.
7. **Mât arrière** : le verrouillage par goupille suppose de percer le carbone ; un collier serait préférable.
8. **Tensions électriques** : pédalier en 36 V, moteur immergé en 48 V ou plus. Deux batteries ou un pédalier 48 V.
9. **Étanchéité** des sorties d'arbre et du passage des joues à l'étrave.
10. **Réglementation** : vitesse limitée sur l'Erdre, statut de vélo à assistance sur route, marquage CE des bateaux à vérifier.
11. **Pédalier haut** : 30 cm au-dessus de l'assise pour que les talons passent au-dessus des varangues (pédale au plus bas à z = 400). À valider sur un gabarit grandeur ; des manivelles plus courtes le feraient descendre.
12. **Lumières dans la semelle haute de la poutre** : deux de 20 mm de large pour la chaîne (environ 170 et 145 mm de long) et une pour la potence. Elles affaiblissent la poutre là où elle travaille en compression : à renforcer ou à calculer.
13. **Ancrage de la potence de pédalier** : l'effort de chaîne (jusqu'à 1,8 kN) tire à 35 cm au-dessus de la poutre. Collage dans le caisson à valider par essai.
14. **Un seul rapport** : 4,12 m par tour, c'est long pour sortir de l'eau sur une cale. Piste : moyeu à vitesses intégrées en renvoi, ou plateau plus petit.
15. **Direction reliée en permanence** : sur route le mât arrière relevé pivote avec la roue avant. À découpler si cela gêne (capote, housses).
16. **Ligne de chaîne** : le caisson impose y = −35, le moteur de pédalier donne environ 50 mm. Le boîtier est décalé de 15 mm vers bâbord, donc les pédales aussi.
17. **Eau dans le caisson** : les lumières l'ouvrent sur le cockpit. Prévoir un nable de vidange, et vérifier que le caisson ne relie pas les deux compartiments étanches.

## Ce qui reste à faire

- Confirmer la position du pédalier (voir « Pédalier reculé »).
- Crans et verrou du siège sur ses rails (la course est chiffrée, le mécanisme n'est pas dessiné). Voir si les leviers doivent suivre le siège.
- Changement de vitesses, carters de chaîne, chaînes des bras arrière.
- Dernier tronçon des gaines de frein arrière : la boucle qui suit le relevage du bras, jusqu'au levier du tambour.
- Implantation du moteur de pédalier sur la potence, une fois le modèle choisi.
- Version siège enfant dans le modèle CAO (roues arrière reculées : `arm_dx` négatif).
- Capote solaire, housses, éclairage : présents dans la maquette, absents de la CAO.
- Choisir une licence pour le dépôt.
- Essai statique, puis calcul de structure, avant toute construction.

## Travailler dans ce dépôt

- `cad/phoebe_cad.py` : modèle paramétrique. Tous les réglages sont dans la classe `Params`. Lancer `python3 cad/phoebe_cad.py cad/out` régénère le STEP, le DXF, l'aperçu et le bilan.
- Unités en millimètres. Repère : X vers l'avant, Y vers bâbord, Z vers le haut, Z = 0 au sol en mode route, X = 0 au milieu de la coque.
- Les pièces plates sont construites en 2D avec shapely, puis extrudées. Leurs contours alimentent aussi le DXF.
- Dans l'assemblage, bâbord est en configuration eau (foil déployé, roue relevée) et tribord en configuration route.
- Après toute modification : lancer `python3 cad/verifier.py`. Il régénère les sorties, relit le STEP, vérifie que tous les solides sont valides et liste les collisions entre pièces. Compter une dizaine de minutes ; `--seulement motif1,motif2` limite le contrôle aux pièces nommées. Les collisions listées entre un axe ou une goupille et la pièce qu'il traverse sont attendues : les perçages ne sont pas tous modélisés.
- Sur le poste Windows de Guillaume, Python n'est pas dans le PATH : l'environnement est dans `.venv` (créé avec `uv venv --python 3.12`), à lancer par `.venv/Scripts/python.exe`. Préfixer par `PYTHONIOENCODING=utf-8` pour l'affichage des accents.
- Les tubes souples (gaines, fourreau de chaîne) sont des balayages le long d'une liste de points de passage. Ils montrent un cheminement, pas une longueur de câble.
- Les cotes des pièces du commerce (paliers UCP205, platine de mât 165 × 90, moyeu de 110 mm) sont notées de mémoire : les vérifier sur les fiches des fournisseurs avant de découper.
- `maquette/index.html` : maquette 3D de communication (three.js, un seul fichier). Elle sert à montrer le concept, pas à coter. Réalignée sur la CAO le 16 novembre 2026 (largeur, foils, fourche, pédalier, chaîne, leviers, câbles, pilote de 1,85 m) : ses cotes sont recopiées à la main, à reprendre après chaque évolution du modèle. Pour la contrôler sans navigateur piloté : capture avec Chrome en mode headless, l'ancre `#capture` masque l'interface.
- Langue du projet : français. Messages de commit en français.

## Identité graphique et site

- Site public (GitHub Pages, branche `main`, racine du dépôt) : https://guillaumegodet.github.io/phoebe/. Page d'accueil `index.html`, styles communs `assets/phoebe.css`, charte `identite/index.html`. Pas de build : fichiers statiques, `.nojekyll`.
- Logo : un croissant orange (la coque, et la lune de Phoebé) porté par un foil au-dessus d'une vague. Fichiers SVG dans `identite/`, mot « phoebe » vectorisé en Bricolage Grotesque gras.
- Couleurs : encre `#16252b`, Erdre `#0f6f86`, housse (orange) `#d9622b`, toile `#f6f3ea`, ciel `#dfe9ec`, écume `#7cc4d6`, okoumé `#cfa873`. Polices : Bricolage Grotesque (titres), Barlow (texte).
- Ton : phrase signature « Je vais en Phoebe. », Phoebe au féminin, toujours rappeler que c'est une étude de concept, distinguer chiffres calculés et estimés.
- Le site reprend les chiffres de référence et les points durs de ce fichier : les mettre à jour ensemble. `assets/cao-apercu.png` et `assets/cao-gabarits.png` sont des recadrages de `cad/out/phoebe-apercu.png`.
