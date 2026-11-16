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
- **Squelette en contreplaqué** : poutre de quille en caisson 120 × 60 mm, 13 couples dont 2 cloisons étanches et 2 couples porteurs doublés, étrave prolongée qui porte le pédalier, tableau arrière et gousset.
- **Foils avant** : deux foils en L articulés sur le couple porteur avant (x = +100), repliés vers le haut sur route.
- **Foil arrière** : en T, sur une tête de safran relevable et orientable fixée au tableau.
- **Roues** : 20 pouces. Bras arrière relevables de 69° autour de l'arbre transversal ; console de direction avant relevable sur l'étrave.
- **Transmission** : pédalier, chaîne vers l'arbre transversal de 25 mm (x ≈ −572), une chaîne et une roue libre par roue arrière.

## Chiffres de référence

Calculés par le script (voir `cad/out/bilan.json`) :

| Grandeur | Valeur |
|---|---|
| Volume de coque sous le plat-bord | 416 L |
| Tirant d'eau à 135 kg (véhicule et pilote) | 154 mm |
| Tirant d'eau à 165 kg (avec un enfant) | 174 mm |
| Contreplaqué du squelette | ≈ 2,4 m², ≈ 11,6 kg en okoumé |
| Lisses | 18,3 m, ≈ 2,7 kg |
| Largeur hors tout sur route | ≈ 1,00 m |
| Envergure des foils avant déployés | ≈ 1,74 m |

Estimés à la main, à confirmer :

- Masse à vide visée : 50 à 55 kg.
- Puissance pour voler : de l'ordre de 1 kW vers 20 km/h. Autonomie en vol inférieure à une heure avec 1 kWh.
- Budget du prototype : 6 000 à 12 000 € de matériel, médiane vers 8 000 €.
- Version de série : 18 000 à 25 000 € en petite série.

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

## Ce qui reste à faire

- Commande de direction : des leviers vers la fourche avant et vers le palonnier arrière.
- Transmission complète du pédalier à l'arbre, freins.
- Réaligner la maquette web sur le modèle CAO (elle montre encore 0,89 m de large et l'ancienne roue avant).
- Version siège enfant dans le modèle CAO (roues arrière reculées : `arm_dx` négatif).
- Capote solaire, housses, éclairage : présents dans la maquette, absents de la CAO.
- Choisir une licence pour le dépôt.
- Essai statique, puis calcul de structure, avant toute construction.

## Travailler dans ce dépôt

- `cad/phoebe_cad.py` : modèle paramétrique. Tous les réglages sont dans la classe `Params`. Lancer `python3 cad/phoebe_cad.py cad/out` régénère le STEP, le DXF, l'aperçu et le bilan.
- Unités en millimètres. Repère : X vers l'avant, Y vers bâbord, Z vers le haut, Z = 0 au sol en mode route, X = 0 au milieu de la coque.
- Les pièces plates sont construites en 2D avec shapely, puis extrudées. Leurs contours alimentent aussi le DXF.
- Dans l'assemblage, bâbord est en configuration eau (foil déployé, roue relevée) et tribord en configuration route.
- Après toute modification : relire le STEP et vérifier que tous les solides sont valides, puis contrôler les collisions entre pièces.
- Les cotes des pièces du commerce (paliers UCP205, platine de mât 165 × 90, moyeu de 110 mm) sont notées de mémoire : les vérifier sur les fiches des fournisseurs avant de découper.
- `maquette/index.html` : maquette 3D de communication (three.js, un seul fichier). Elle sert à montrer le concept, pas à coter.
- Langue du projet : français. Messages de commit en français.

## Identité graphique et site

- Site public (GitHub Pages, branche `main`, racine du dépôt) : https://guillaumegodet.github.io/phoebe/. Page d'accueil `index.html`, styles communs `assets/phoebe.css`, charte `identite/index.html`. Pas de build : fichiers statiques, `.nojekyll`.
- Logo : un croissant orange (la coque, et la lune de Phoebé) porté par un foil au-dessus d'une vague. Fichiers SVG dans `identite/`, mot « phoebe » vectorisé en Bricolage Grotesque gras.
- Couleurs : encre `#16252b`, Erdre `#0f6f86`, housse (orange) `#d9622b`, toile `#f6f3ea`, ciel `#dfe9ec`, écume `#7cc4d6`, okoumé `#cfa873`. Polices : Bricolage Grotesque (titres), Barlow (texte).
- Ton : phrase signature « Je vais en Phoebe. », Phoebe au féminin, toujours rappeler que c'est une étude de concept, distinguer chiffres calculés et estimés.
- Le site reprend les chiffres de référence et les points durs de ce fichier : les mettre à jour ensemble. `assets/cao-apercu.png` et `assets/cao-gabarits.png` sont des recadrages de `cad/out/phoebe-apercu.png`.
