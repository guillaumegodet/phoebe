# Phoebe : mémoire du projet

Ce fichier garde l'état du projet d'une session de travail à l'autre : décisions prises, chiffres de référence, points ouverts. À mettre à jour à chaque évolution notable. Dernière mise à jour : 17 novembre 2026.

## Le projet

Phoebe est un véhicule amphibie personnel imaginé par Guillaume Godet (Nantes) : un trike couché à assistance électrique qui roule, flotte et vole sur foils, pensé pour passer de la route à la rivière (l'Erdre).

Le nom vient de la titanide Phoebé : « je vais en Phoebe » = amphibie.

Intentions de départ : carrosserie low-tech, très légère mais solide ; passage facile de la route à l'eau ; un véhicule attachant.

**État : étude de concept. Rien n'est construit, calculé ni essayé.**

## Décisions prises par Guillaume

- Roues arrière motrices et roue avant directrice placée devant l'étrave, plutôt qu'une roue avant motrice, qui aurait traversé la coque.
- Le projet ne se présente pas comme dérivé d'un autre véhicule : aucune référence à un projet d'origine, ni dans le dépôt ni sur le site.
- Une seule machine électrique sur l'arbre transversal, au sec (17 novembre 2026) : moteur d'assistance sur route, génératrice sur l'eau. Elle remplace le moteur de pédalier, abandonné. Pas de moteurs-roues.
- Objectif : le vol sur foils. Donc un second moteur, immergé, au pied du foil arrière, commandé depuis les leviers.
- Direction sur l'eau par le mât arrière orientable (poussée orientée).
- Équipements voulus : un seul phare à l'avant, de style vintage (deux phares n'ont pas de sens ; 17 novembre 2026), batterie, capote faisant panneau solaire et rangeable pour voler, siège inclinable (mode sieste), housses de foils pour la route, squelette porteur.
- Variantes demandées : une version de série au design haut de gamme, une version avec siège enfant à l'arrière.
- Conception en CAO paramétrique (CadQuery), versionnée dans ce dépôt.
- Position du pédalier confirmée le 17 novembre 2026 : sur sa potence, à x = 470, z = 570 (voir « Pédalier reculé »).
- **Le projet n'est pas open source** (17 novembre 2026). Ce véhicule n'existe pas dans le commerce, des brevets sont envisagés et une commercialisation doit rester possible. Tous droits réservés : voir `LICENCE.md`. Ne plus écrire « projet ouvert », « plans ouverts » ; les liens de discussion vers GitHub restent (voir « Propriété intellectuelle ») ; ne pas proposer de téléchargement du modèle ou des plans ; ne pas ajouter de détail technique nouveau sur le site sans l'accord de Guillaume.
- Une seule tension à bord : 48 V, pour la machine d'arbre comme pour le moteur immergé, donc une seule batterie.
- Changement de vitesses avec des pièces standard du commerce (voir « Pistes retenues »).
- Sur l'eau, la poussée du moteur immergé doit suivre le pédalage plutôt qu'une manette : conduite plus amusante (voir « Pistes retenues »).
- Foils avant repliés basculés vers l'avant pour porter la capote : **abandonné**. Guillaume ne le voulait que si la charnière et la position n'en étaient pas compliquées, or il faut tourner l'axe de charnière de 90° (joues à refaire, hors du plan du couple porteur) et retourner les ailes vers l'intérieur, sans quoi elles dépassent à 1,74 m de large sur route. Le visuel d'accueil du site est revenu aux foils repliés à la verticale.

## Architecture retenue

- **Coque** : 2,58 m × 0,74 m, lattes d'épicéa de 18 × 18 mm et toile tendue vernie (skin-on-frame).
- **Squelette en contreplaqué** : poutre de quille en caisson 120 × 60 mm, 13 couples dont 2 cloisons étanches et 2 couples porteurs doublés, étrave prolongée, tableau arrière et gousset.
- **Pédalier** : sur une potence en contreplaqué de 18 mm encastrée dans la poutre, entre les couples +320 et +540 (x = 470, z = 570). Il est fixe : c'est le siège qui coulisse pour s'adapter au pilote. Il n'est plus sur l'étrave (voir « Pédalier reculé » plus bas).
- **Foils avant** : deux foils en L d'une seule pièce, à coude arrondi (rayon 120 mm, corde constante de 150 mm), articulés sur le couple porteur avant (x = +100), repliés vers le haut sur route. Déployés, ils sont verrouillés en bas par un sabot (voir « Sabot de verrouillage »).
- **Foil arrière** : en T, sur une tête de safran relevable et orientable fixée au tableau.
- **Roues** : 20 pouces. Bras arrière relevables de 69° autour de l'arbre transversal ; console de direction avant relevable sur l'étrave.
- **Transmission** : plateau de 42 dents, chaîne dans le caisson de quille (plan y = −35) jusqu'au pignon de 16 dents d'un moyeu à huit vitesses monté en renvoi sous le dossier (voir « Moyeu à vitesses en renvoi »). Un pignon de 16 dents vissé sur la fixation de disque du moyeu entraîne, par une chaîne courte à bâbord (plan y = +61), le pignon de 24 dents de l'arbre transversal de 25 mm (x ≈ −572), puis une chaîne et une roue libre par roue arrière. Brin tendu rectiligne entre deux galets vissés sur la semelle haute ; brin mou dans un fourreau au fond du caisson.
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
| Développement | huit vitesses, de 1,45 à 4,44 m par tour de pédalier : 7,0 à 21,3 km/h à 80 tr/min |
| Chaîne primaire | 2,99 m, 236 maillons |
| Chaîne secondaire | 36 maillons, entraxe de 100 mm |
| Moyeu à vitesses | axe à x = −491, z = 300 ; 17 mm sous le dossier (siège reculé), 23 mm au-dessus de la poutre |
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

Le pédalier a donc été reculé de 48 cm et monté de 9 cm, sur une potence. Il est réglé pour Guillaume, qui mesure 1,85 m : siège presque en butée arrière, à sa position d'origine. Demande de Guillaume : le siège doit coulisser d'avant en arrière pour s'adapter au pilote. Il avance donc de 180 mm au plus sur ses rails pour les pilotes plus petits (environ 5 cm par 10 cm de taille). Les tailles sont estimées avec un rapport jambe / taille de 0,503 (`leg_ratio`), à vérifier sur un gabarit. Les leviers et le centrage des masses ne changent pas pour Guillaume ; un pilote petit se retrouve plus en avant des leviers, qui restent fixes. L'alternative, avancer le siège de 35 cm en gardant le pédalier près de l'étrave, a été écartée : Guillaume a confirmé le pédalier sur potence le 17 novembre 2026. Tout suit `bb_x` et `bb_z` dans `Params`.

Conséquences : l'avant du cockpit (x = 600 à 1014) est libre, et le prolongement de l'étrave vers l'arrière (x = 840 à 1014) ne sert plus au pédalier.

## Moyeu à vitesses en renvoi (modélisé le 17 novembre 2026)

Un moyeu de vélo à huit vitesses à frein à disque (type Shimano Nexus ou Alfine 8, plage de 307 %) est tenu par son axe entre deux platines d'aluminium de 6 mm vissées sur les flancs de la poutre, sous le dossier. La chaîne primaire entraîne son pignon ; un pignon vissé sur sa fixation de disque entraîne l'arbre transversal par une chaîne courte, à bâbord. Commande par une poignée tournante sur le levier de direction tribord. Tout suit `hub_x`, `hub_z` et les `z_hub_*` dans `Params`.

- **Dentures** : 42 → 16, puis 16 → 24 (au lieu de 42 → 18 et 18 → 24 prévus : même rapport global, mais des pignons plus petits, sans quoi rien ne passait). Rapport d'entrée de 2,62, au-dessus du minimum habituel de ces moyeux.
- **Place** : elle est comptée. Le moyeu est coincé entre le dossier (17 mm de jeu, siège en butée arrière), la poutre (23 mm), le couple −440 et l'arbre. Il ne peut ni avancer ni monter. Un dossier qui fléchit sous le pilote peut le toucher : à raidir, ou à protéger par un carter.
- **Galets arrière déplacés** : galet tendu à x = −479,5, ramené à 11 dents ; galet mou à x = −530. La lumière arrière de la semelle passe de 147 à 120 mm.
- **Tension** : les platines ont une lumière de 16 mm dans l'axe moyeu → arbre, pour tendre la chaîne secondaire. La chaîne primaire n'a toujours pas de tendeur.
- **Platine bâbord** : sur une cale de 14,5 mm, parce que le moyeu est décalé de 7 mm vers bâbord pour aligner son pignon sur le plan de chaîne.
- **À vérifier sur les fiches** : largeur de 135 mm, ligne de chaîne de 42 mm, diamètre du corps (104 mm retenus), position de la fixation de disque. Les moyeux Shimano de ce type sont en Center Lock : il faut un adaptateur six trous ou un pignon Center Lock, à trouver dans le commerce. Rondelles anti-rotation à choisir selon l'angle des lumières.
- Le moyeu gauche des roues garde sa roue libre inversée. Variante pour la série : un bloc moteur et boîte de vitesses intégrés dans le pédalier, en 48 V.

## Machine d'arbre (modélisée le 17 novembre 2026)

Un moteur sans balais (encombrement retenu : 63 mm de diamètre, 74 mm de long, noté de mémoire) est en prise permanente sur l'arbre transversal par une chaîne : couronne de 36 dents sur l'arbre, pignon de 11 dents, rapport 3,27, 44 maillons, plan y = −80 (tribord). Il est vissé sur une platine d'aluminium de 6 mm fixée au flanc tribord de la poutre, derrière le couple porteur, au-dessus de la poutre (axe à x = −669, z = 291, 25 mm au-dessus de la poutre). Tout suit `gen_*` et `z_gen*` dans `Params`.

- **Couronne limitée à 36 dents** par le dossier : 14 mm de jeu, siège en butée arrière. 48 dents ne passent pas.
- La machine ne pouvait pas se visser contre le couple porteur : il est ouvert à cette hauteur. D'où la platine sur la poutre.
- La gaine du frein arrière tribord, qui traversait au-dessus de l'arbre, passe maintenant au-dessus de la couronne, sous le dossier.
- Le moteur de pédalier a disparu du modèle ; la ligne de chaîne du pédalier passe de 50 à 45 mm.

## Relevage des foils (modélisé le 17 novembre 2026)

Principe : un secteur à gorge, solidaire du foil et centré sur son axe, garde un bras de levier constant sur les 180° de rotation. Le relevage ne porte que le poids du foil ; en vol, l'effort est repris par les charnières et les sabots de verrouillage. Masses supposées, à remplacer par celles des foils réels : 2,3 kg par foil avant (centre de gravité à 0,55 m de l'axe), 6 kg pour le foil arrière avec son moteur (à 0,60 m). Tout suit `lift_*`, `foil_*` et `rud_*` dans `Params`.

- **Foils avant** : secteur de 70 mm de rayon (limité par le plat-bord), vissé sur la platine de mât, devant la joue avant. Couple maximal de 12 N·m, soit 18 kg de traction sans aide, pour 22 cm de bout. Un sandow de rappel compense le poids : attaché au secteur, renvoyé sur un réa de la joue, ancré en bas de la joue, côté cockpit. Il lui faut environ 225 N à mi-course. Le bout passe par deux filoirs sur la joue et file au taquet coinceur sur le plat-bord (x = −120).
- **Foil arrière** : secteur de 90 mm (limité par le palonnier), claveté sur l'axe de relevage, à bâbord de la tête de safran. L'axe doit donc être solidaire du mât et transmettre 35 N·m. Le bout descend à une poulie sur le tableau, à 15 mm de l'axe de direction pour ne pas gêner le braquage, passe sur le pont arrière et rejoint un palan à six brins le long du plat-bord bâbord. Environ 65 N au garant sans les frottements, pour 1,7 m de cordage à reprendre. Taquet à x = −200. Pas de rappel : un vérin à gaz est à étudier.
- **Non traité** : départ de la descente (foil replié à la verticale, il faut le décoller de sa butée : ressort ou second bout), tenue du sandow, trajectoires pendant la rotation et pendant le braquage du mât arrière (seules les positions extrêmes sont contrôlées), contact des bouts avec la toile du pont.

## Sabot de verrouillage et foil à coude arrondi (modélisés le 17 novembre 2026)

En vol, la portance s'applique en dehors de la charnière : elle cherche à replier le foil vers l'extérieur, et le mât tire donc sur la coque. Le sabot le retient 152 mm sous la charnière (goupille à z = 335), au lieu des 35 mm de la goupille de charnière. Tout suit `shoe_*` et `foil_elbow_r` dans `Params`.

- **Sabot** : une console en aluminium sur le flanc, terminée par une chape. Un tenon fixé à la face intérieure du mât y entre quand le foil se déploie ; une goupille de 10 mm les traverse. Le sabot est serré autour du couple porteur par deux tirants M8 qui passent de part et d'autre des joues, jusqu'à une contre-plaque appuyée sur le chant intérieur du couple. Une cale de contreplaqué remplit les 6 mm entre la toile et le couple. Rien n'est vissé dans le chant du contreplaqué.
- **Efforts** (hypothèse : 70 % de 135 kg sur les deux foils avant, portance au milieu de l'aile) : 464 N par foil, 113 N·m autour de la charnière, 0,74 kN au sabot, 2,2 kN à trois fois la charge, soit 1,1 kN par tirant. Sans sabot, la goupille de charnière prendrait 9,7 kN à trois fois la charge.
- **Encombrement** : il dépasse le flanc de 110 mm et reste dans la largeur sur route. Son dessous est à 26 mm de la flottaison à 135 kg, 6 mm à 165 kg : il traîne dans l'eau au clapot.
- **Foil** : le coude arrondi remplace l'assemblage d'un mât et d'une aile. La corde est constante (150 mm au lieu de 120 pour le mât et 180 pour l'aile) : la surface portante projetée passe de 0,067 à 0,056 m² par foil, à envergure égale (1,74 m). Ce n'est plus un mât de foil du commerce : pièce à faire faire, en carbone ou en profilé d'aluminium cintré (masse à revoir, l'hypothèse de 2,3 kg date du carbone).
- **Non traité** : étanchéité des deux tirants à travers la toile, fixation du tenon sur le mât, mise en place de la goupille depuis le siège (le sabot est hors de la coque, à bout de bras), efforts latéraux en virage, vitesse de décollage avec la surface réduite.

## Foils coulissant dans un puits : écarté (17 novembre 2026)

Idée venue des dériveurs à foils BirdyFish et Ioda (Saint-Herblain). Une variante à foils en arc de cercle coulissant dans un puits courbe a été dessinée puis retirée du modèle, à la demande de Guillaume. La version à charnières reste la seule.

- **Pourquoi** : la coque est trop peu haute. Le puits ne guidait le foil que sur 276 mm, d'où 6,3 kN sur l'appui bas à trois fois la charge, contre 3 kN par vis pour les charnières. Le foil ne se manœuvrait plus depuis le siège et il fallait le retirer pour rouler.
- **L'Ioda réel** (vidéo de montage) : des L en aluminium d'une seule pièce, à coude arrondi. Le mât droit coulisse dans un puits droit, l'aile reste sous la coque. Enfilés par en dessous, ils restent à bord. Sur route, une telle aile resterait déployée sous la coque : la charnière reste préférable.
- **À reprendre peut-être** : le coude arrondi d'une seule pièce, le verrouillage par un axe retenu par un sandow, une position mi-hauteur pour quitter la cale, un sandow sur crochet pour tenir le foil relevé.
- **Question ouverte** : comment l'Ioda règle son altitude avec une aile horizontale. À demander au constructeur.
- **Brevet** : une demande française FR3134792A1 (« hydroptère à foil rétractable ») est apparue dans la recherche. Ni lue ni attribuée.

## Pistes retenues, pas encore modélisées (17 novembre 2026)

**Une seule tension, 48 V.** La machine d'arbre et le moteur immergé ont chacun leur variateur (type VESC, à vérifier), sur le même bus 48 V, reliés par bus CAN. Le moteur immergé d'environ 1 kW demande une vingtaine d'ampères sous 48 V. Pour rester un vélo à assistance sur route : 250 W nominaux, assistance seulement quand on pédale, coupée à 25 km/h. Avec un moteur bridé par logiciel plutôt qu'un kit marqué 250 W, ce statut est plus discutable : à vérifier.

**Pédalier électrique sur l'eau (« pedal-by-wire »).** Aucune chaîne ne peut atteindre le moteur immergé, et roues relevées la transmission tourne à vide. La machine d'arbre sert donc de génératrice : elle oppose une résistance au pédalage, mesure la puissance fournie (tension × courant) et la renvoie sur le bus 48 V. Règle de poussée retenue : poussée = gâchette + k × puissance pédalée, plafonnée ; la gâchette donne la base, les jambes modulent (voler avec k seul demanderait 125 à 200 W en continu). Mesure lissée sur au moins un tour de pédalier ; descente progressive de la poussée sur 1 à 2 s quand on cesse de pédaler, pour ne pas faire retomber la coque. Si le bus CAN ou la génératrice tombe : retour à la gâchette seule. Le coupe-circuit à cordon coupe les deux variateurs. Les huit vitesses du moyeu servent aussi sur l'eau : elles règlent la cadence. Ni roue libre ni crabot au départ : les roues relevées tournent dans le vide. **Risque principal : la sensation sous les pieds.** Sans inertie, la génératrice freine aussi aux points morts ; le freinage doit croître avec la vitesse (comme un home-trainer), pas être constant. À valider d'abord sur un établi (pédalier, machine, variateur), avant toute autre dépense. L'énergie pédalée est consommée aussitôt par le moteur immergé : environ 8 à 10 % de courant en moins, pas une recharge.

## Propriété intellectuelle

- Le dépôt GitHub et le site sont **publics** depuis novembre 2026. En droit européen des brevets, ce qui a été rendu public ne peut plus être breveté (pas de délai de grâce) : ne rien publier de nouveau qui pourrait l'être avant d'avoir vu un conseil en propriété industrielle.
- Pistes à voir avec un conseil ou l'INPI : enveloppe e-Soleau pour dater les créations, dépôt de la marque Phoebe (disponibilité à vérifier), dessins et modèles pour l'apparence (délai de grâce de 12 mois après divulgation), brevet pour ce qui n'est pas encore divulgué.
- Décision de Guillaume (17 novembre 2026) : le dépôt reste **public** à ce stade du projet, et le site garde ses liens « En discuter » vers les tickets GitHub. La licence « tous droits réservés » reste en place. À reposer si un brevet devient concret.

## Points durs connus

1. **Charnières et sabots des foils avant** : environ 3 kN par vis dans le contreplaqué à trois fois la charge, estimés avant le sabot ; à recalculer, le sabot reprend maintenant le moment (2,2 kN à trois fois la charge). À valider par essai statique. La goupille du sabot est hors de la coque : à rendre manœuvrable depuis le siège.
2. **Verrou des bras arrière** : il porte le poids sur route, environ 2,6 kN par vis à trois fois la charge.
3. **Régulation d'altitude des foils** : non conçue (palpeurs, foils en V ou volets).
4. **Largeur de 1,00 m**, imposée par les moyeux arrière standard. La réduire demande des roues en porte-à-faux.
5. **Roue arrière relevée proche de l'eau** : environ 3 cm au-dessus de la flottaison à 135 kg.
6. **Moyeu gauche** : roue libre inversée nécessaire.
7. **Mât arrière** : le verrouillage par goupille suppose de percer le carbone ; un collier serait préférable.
8. **Machine d'arbre** : elle se dimensionne au couple, pas à la puissance. À 80 tr/min de pédalage elle tourne de 241 à 740 tr/min et doit fournir 1,9 à 5,9 N·m pour 150 W pédalés ; sur route, 868 tr/min à 25 km/h. Il faut un moteur lent (de l'ordre de 80 tr/min par volt, type moteur de skate de 63 mm ; à choisir sur fiche). Sur route elle agit après le moyeu, sans profiter des vitesses : peu de couple à basse vitesse pour sortir d'une cale. Batterie à placer.
9. **Étanchéité** des sorties d'arbre et du passage des joues à l'étrave.
10. **Réglementation** : vitesse limitée sur l'Erdre, statut de vélo à assistance sur route, marquage CE des bateaux à vérifier.
11. **Pédalier haut** : 30 cm au-dessus de l'assise pour que les talons passent au-dessus des varangues (pédale au plus bas à z = 400). À valider sur un gabarit grandeur ; des manivelles plus courtes le feraient descendre.
12. **Lumières dans la semelle haute de la poutre** : deux de 20 mm de large pour la chaîne (environ 180 et 120 mm de long) et une pour la potence. Elles affaiblissent la poutre là où elle travaille en compression : à renforcer ou à calculer.
13. **Ancrage de la potence de pédalier** : l'effort de chaîne (jusqu'à 1,8 kN) tire à 35 cm au-dessus de la poutre. Collage dans le caisson à valider par essai.
14. **Place du moyeu à vitesses** : 17 mm sous le dossier et 23 mm au-dessus de la poutre, avec des cotes de moyeu notées de mémoire. À valider sur un gabarit avec le moyeu réel ; pas de tendeur sur la chaîne primaire.
15. **Direction reliée en permanence** : sur route le mât arrière relevé pivote avec la roue avant. À découpler si cela gêne (capote, housses).
16. **Ligne de chaîne** : le caisson impose y = −35, un pédalier courant donne environ 45 mm. Le boîtier est décalé de 10 mm vers bâbord, donc les pédales aussi.
17. **Eau dans le caisson** : les lumières l'ouvrent sur le cockpit. Prévoir un nable de vidange, et vérifier que le caisson ne relie pas les deux compartiments étanches.
18. **Mode sieste et couronne** : la couronne de la machine d'arbre limite l'inclinaison du dossier. La maquette prend 28° avec le siège avancé de 180 mm (toute la course des rails) : 16 mm au-dessus de la couronne d'après les cotes de la CAO. À 24°, il la touchait. Non modélisé dans la CAO.

## Ce qui reste à faire

- Crans et verrou du siège sur ses rails (la course est chiffrée, le mécanisme n'est pas dessiné). Voir si les leviers doivent suivre le siège.
- Moyeu à vitesses : vérifier ses cotes sur la fiche, trouver le pignon de sortie (Center Lock ou adaptateur six trous), dessiner un tendeur de chaîne primaire. Puis les carters de chaîne et les chaînes des bras arrière.
- Mode sieste : dessiner la béquille à crans du dossier dans la CAO, avec sa butée à 28° (voir point dur 18).
- Pédalier électrique : essai sur établi de la sensation de pédalage, puis choix de la machine d'arbre, des deux variateurs et de la loi de commande. Placer variateurs et batterie, à l'abri des projections.
- Dernier tronçon des gaines de frein arrière : la boucle qui suit le relevage du bras, jusqu'au levier du tambour.
- Capteur de pédalage au pédalier pour l'assistance sur route (cadence, ou boîtier à capteur de couple du commerce). Tension de la chaîne de la machine d'arbre (trous oblongs dans sa platine, non dessinés).
- Version siège enfant dans le modèle CAO (roues arrière reculées : `arm_dx` négatif).
- Sabots de foil : verrou manœuvrable depuis le siège, étanchéité des tirants, tenon sur le mât.
- Relevage des foils : peser ou estimer les foils réels, dimensionner sandows et palan, dessiner le départ de la descente et un rappel pour le foil arrière.
- Capote solaire, housses, éclairage : présents dans la maquette, absents de la CAO.
- Propriété intellectuelle : consulter un conseil (voir « Propriété intellectuelle »).
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
- `maquette/index.html` : maquette 3D de communication (three.js, un seul fichier). Elle sert à montrer le concept, pas à coter. Réalignée sur la CAO le 16 novembre 2026 (largeur, foils, fourche, pédalier, chaîne, leviers, câbles, pilote de 1,85 m), puis le 17 pour le moyeu à vitesses, la machine d'arbre, les sabots et les foils à coude arrondi : ses cotes sont recopiées à la main, à reprendre après chaque évolution du modèle. Pour la contrôler sans navigateur piloté : capture avec Chrome en mode headless, l'ancre `#capture` masque l'interface.
- Langue du projet : français. Messages de commit en français.

## Identité graphique et site

- Site public (GitHub Pages, branche `main`, racine du dépôt) : https://guillaumegodet.github.io/phoebe/. Page d'accueil `index.html`, styles communs `assets/phoebe.css`, charte `identite/index.html`. Pas de build : fichiers statiques, `.nojekyll`.
- Logo : un croissant orange (la coque, et la lune de Phoebé) porté par un foil au-dessus d'une vague. Fichiers SVG dans `identite/`, mot « phoebe » vectorisé en Bricolage Grotesque gras.
- Couleurs : encre `#16252b`, Erdre `#0f6f86`, housse (orange) `#d9622b`, toile `#f6f3ea`, ciel `#dfe9ec`, écume `#7cc4d6`, okoumé `#cfa873`. Polices : Bricolage Grotesque (titres), Barlow (texte).
- Ton : phrase signature « Je vais en Phoebe. », Phoebe au féminin, toujours rappeler que c'est une étude de concept, distinguer chiffres calculés et estimés. Projet personnel, tous droits réservés : pas de fichiers à télécharger. La section « Participer » (ancre `#participer`, bouton dans l'en-tête) est revenue à la demande de Guillaume : chaque carte a un lien « En discuter » qui ouvre un ticket GitHub au sujet prérempli, suivie du bloc d'appel aux contributions et du bouton « Proposer une idée ». On invite à discuter, sans écrire « projet ouvert ».
- Le site reprend les chiffres de référence et les points durs de ce fichier : les mettre à jour ensemble. `assets/cao-apercu.png` et `assets/cao-gabarits.png` sont des recadrages de `cad/out/phoebe-apercu.png` : cadres (130, 150, 1700, 575) et (630, 748, 1090, 1503), refaits le 17 novembre 2026.
