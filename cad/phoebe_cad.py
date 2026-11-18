#!/usr/bin/env python3
"""
Phoebe - véhicule amphibie à foils.
Modèle paramétrique de la coque et du squelette porteur.

Sorties :
  phoebe-assemblage.step   assemblage 3D (pièces nommées)
  phoebe-gabarits.dxf     gabarits de découpe à l'échelle 1 (mm)
  phoebe-apercu.png       contrôle visuel

Unités : millimètres. Repère : X vers l'avant, Y vers bâbord, Z vers le haut,
Z = 0 au sol en mode route, X = 0 au milieu de la coque.

ATTENTION : géométrie de conception, pas un calcul de structure. Les épaisseurs
et sections sont des choix de départ à valider par essai statique.

Usage : python3 phoebe_cad.py [dossier_de_sortie]
Dépendances : cadquery, shapely, ezdxf, matplotlib
"""
import math, sys, os, json
from dataclasses import dataclass, field
import numpy as np
from shapely.geometry import Polygon, LineString, Point, box
from shapely import affinity
from shapely.ops import unary_union

# ----------------------------------------------------------------------------
# PARAMÈTRES - tout se règle ici
# ----------------------------------------------------------------------------
@dataclass
class Params:
    # formes de coque
    HL: float = 1300.0          # demi-longueur de coque
    B_half: float = 370.0       # demi-largeur maxi
    z_keel: float = 140.0       # hauteur de la quille au milieu (garde au sol)
    z_gun: float = 460.0        # hauteur du plat-bord au milieu
    rise_fwd: float = 240.0     # relevé de quille à l'étrave
    rise_aft: float = 120.0     # relevé de quille à l'arrière
    sheer: float = 50.0         # tonture du plat-bord aux extrémités
    crown: float = 45.0         # bouge du pont
    t_bow: float = 0.985        # fin de la coque vers l'avant (fraction de HL)
    # peau et lisses
    skin_gap: float = 6.0       # retrait des couples sous la toile
    stringer: float = 18.0      # section carrée des lisses (épicéa)
    stringer_pos: tuple = (0.2, 0.36, 0.5, 0.64, 0.8)   # positions autour du bouchain (0 = plat-bord bâbord, 1 = tribord)
    tol: float = 0.4            # jeu des encoches
    # couples
    ring: float = 45.0          # largeur des couples courants
    ring_U: float = 80.0        # largeur des couples porteurs
    t_frame: float = 9.0        # contreplaqué des couples et cloisons
    t_U: float = 12.0           # contreplaqué des couples porteurs (x2, collés)
    t_plate: float = 18.0       # tableau arrière, étrave, gousset arrière
    floor_half: float = 100.0   # demi-largeur des varangues
    floor_over: float = 25.0    # matière au-dessus de la poutre (couples courants)
    floor_over_U: float = 25.0  # idem couples porteurs
    floor_over_foil: float = 62.0   # couple porteur des foils : varangue haute, limitée par l'assise du siège avancé
    # (x, type) : closed = avec barrot de pont, open = cockpit, bulk = cloison étanche, U = couple porteur
    stations: tuple = ((-1170, 'closed'), (-975, 'closed'), (-806, 'bulk'), (-620, 'U'),
                       (-440, 'open'), (-260, 'open'), (-80, 'open'), (100, 'U'),
                       (320, 'open'), (540, 'open'), (760, 'open'), (1014, 'bulk'), (1170, 'closed'))
    x_transom: float = -1280.0
    # poutre de quille en caisson
    beam_w: float = 120.0
    beam_h: float = 60.0
    t_web: float = 12.0
    t_flange: float = 6.0
    # étrave prolongée (porte le pédalier) et gousset arrière
    stem_x0: float = 840.0
    stem_top_aft: float = 525.0
    knee_x1: float = -985.0
    # divers
    z_ref: float = 400.0        # ligne de référence gravée sur chaque couple
    rho_ply: float = 500.0      # kg/m3, okoumé
    rho_spruce: float = 450.0
    # ---------------- interfaces (cotes des pièces du commerce à vérifier sur leurs fiches) ----------------
    x_frame_foil: float = 100.0     # couple porteur des foils avant
    x_frame_axle: float = -620.0    # couple porteur de l'arbre arrière
    # charnières des foils avant
    hinge_y: float = 440.0          # axe de pivot (parallèle à X)
    hinge_z: float = 487.0
    hinge_e: float = 58.0           # déport pivot -> mât
    hinge_lock_r: float = 35.0      # rayon de la goupille de verrouillage
    t_cheek: float = 6.0            # joues en aluminium
    t_ferr_ar: float = 4.0          # ferrure porteuse arrière : 4 mm, la machine d'arbre est juste derrière
    ferr_ar_top: float = 330.0      # haut de son âme, au-dessus de la poutre
    plate_L: float = 190.0          # platine de mât (entraxe courant 165 x 90, à vérifier)
    plate_W: float = 110.0
    mast_len: float = 850.0
    # Foil avant d'une seule pièce : un L à coude arrondi, de corde constante (profilé cintré), au lieu d'un mât
    # et d'une aile assemblés. La platine de mât reste l'interface avec la chape.
    mast_chord: float = 150.0
    mast_thk: float = 16.0
    wing_span: float = 370.0        # du mât au bout de l'aile
    wing_chord: float = 150.0
    foil_elbow_r: float = 120.0     # rayon du coude, sur la ligne moyenne
    # Sabot de verrouillage : une chape sur le flanc, sous la charnière, reçoit un tenon fixé au mât. Une goupille
    # les traverse. En vol la portance cherche à replier le foil vers l'extérieur : le sabot retient le mât, avec
    # un bras de levier bien plus grand que la goupille de la charnière. Il est serré autour du couple porteur
    # par deux tirants et une contre-plaque : rien n'est vissé dans le chant du contreplaqué.
    shoe_z: float = 335.0           # hauteur de la goupille du sabot (au-dessus de la flottaison à 165 kg)
    shoe_w: float = 80.0            # largeur du sabot, le long de la coque
    shoe_pin_y: float = 465.0
    foil_share: float = 0.8         # part du poids portée par les deux foils avant (79 à 83 % d'après le devis de masses, batterie à l'avant)
    # masses de calcul, d'après le devis de masses (cad/devis_masses.py) : à corriger quand il change
    mass_ref: float = 170.0         # kg, véhicule, batterie de 2 kWh et pilote de 80 kg
    rear_share: float = 0.75        # part du poids sur les deux roues arrière, sur route (72 à 74 % d'après le devis)
    # arbre arrière et paliers à semelle vissés sur la face avant du couple
    shaft_d: float = 25.0
    shaft_bore: float = 19.0        # arbre creux (tube 25 x 3) : 1,7 kg au lieu de 3,9 ; acier à haute limite élastique
    shaft_z: float = 360.0
    brg_y: float = 265.0            # centre des paliers
    brg_h: float = 36.5             # hauteur d'axe du palier (type UCP205)
    brg_J: float = 105.0            # entraxe des vis du palier
    brg_bolt: float = 10.5
    arm_y: float = 430.0            # plan médian des roues arrière
    hub_old: float = 110.0          # largeur du moyeu arrière (type BMX à roue libre)
    arm_dx: float = -270.0          # axe de roue par rapport au pivot : roues derrière l'arbre, pour charger la roue avant (devis de masses)
    arm_dz: float = -110.0
    arm_lift: float = 90.0          # angle de relevage des roues, en degrés (69 jusqu'au 18 novembre 2026 : les roues trempaient)
    arm_lock_r: float = 130.0       # rayon de la goupille de verrouillage du bras
    # foil arrière : tête de safran relevable et orientable sur le tableau
    rud_pin_x: float = -1325.0      # axe vertical de direction
    rud_gz: tuple = (360.0, 470.0)  # hauteur des deux fémelots
    rud_Lx: float = -1400.0         # axe de relevage du mât
    rud_Lz: float = 520.0
    rud_lock_r: float = 120.0
    rud_mast: float = 870.0
    # direction avant relevable
    fork_px: float = 1305.0         # pivot de relevage (parallèle à Y)
    fork_pz: float = 495.0
    fork_kz: float = 425.0          # goupille de verrouillage
    axle_x: float = 1560.0
    wheel_r: float = 250.0
    head_angle: float = 72.0
    rake: float = 35.0
    # siège
    seat_x: float = -360.0
    seat_w: float = 380.0
    seat_back: float = 645.0
    seat_angle: float = 49.4
    hip_x: float = -280.0           # articulation de hanche du pilote, siège en butée arrière (repère d'ergonomie)
    hip_z: float = 360.0
    seat_travel: float = 180.0      # réglage du siège vers l'avant, sur ses rails, pour les pilotes plus petits
    leg_ratio: float = 0.503        # (hanche -> axe de pédale, jambe tendue) / taille du pilote, à l'estime
    # ---------------- pédalier et transmission primaire ----------------
    # Le pédalier est porté par une potence en contreplaqué encastrée dans la poutre, entre deux couples.
    # Il est fixe : c'est le siège qui coulisse pour s'adapter au pilote. Siège en butée arrière, il convient à
    # un pilote de 1,89 m environ (Guillaume, 1,85 m, s'assoit 2 cm plus en avant). Manivelles et talons
    # tournent sans toucher ni la cloison avant ni les varangues.
    bb_x: float = 470.0
    bb_z: float = 570.0
    crank: float = 170.0
    bb_shell: float = 68.0          # largeur du boîtier
    bb_chainline: float = 45.0      # ligne de chaîne d'un pédalier courant, sans moteur (à vérifier sur sa fiche)
    chain_y: float = -35.0          # plan de la chaîne primaire : elle passe dans le caisson de quille
    z_ring: int = 42                # dents du plateau
    z_shaft: int = 24               # dents du pignon d'arbre (chaîne secondaire)
    z_idler: int = 15               # galet avant du brin tendu
    z_idler_aft: int = 11           # galet arrière du brin tendu, plus petit pour passer devant le moyeu
    z_idler_slack: int = 11         # galets du brin mou
    idler_fwd_x: float = 160.0      # galets avant (entre les couples +100 et +320)
    slack_fwd_x: float = 235.0
    idler_aft_x: float = -479.5     # galets arrière (entre les couples -620 et -440)
    slack_aft_x: float = -530.0
    # Changement de vitesses : un moyeu de vélo à vitesses intégrées monté en renvoi sous le dossier, entre deux
    # platines vissées sur les flancs de la poutre. La chaîne primaire entraîne son pignon ; un pignon vissé sur
    # sa fixation de disque entraîne l'arbre par une chaîne courte, à bâbord. Cotes du moyeu notées de mémoire
    # (type Shimano Nexus ou Alfine 8) : à vérifier sur la fiche.
    hub_x: float = -491.0           # axe du moyeu, au milieu de ses lumières de tension
    hub_z: float = 300.0
    hub_r: float = 52.0             # rayon d'encombrement du corps (flasques)
    hub_width: float = 135.0        # entre contre-écrous
    hub_chainline: float = 42.0     # ligne de chaîne du pignon d'entrée
    hub_disc_off: float = 15.0      # face d'appui du disque, depuis le contre-écrou gauche
    hub_gears: tuple = (0.527, 0.644, 0.748, 0.851, 1.0, 1.223, 1.419, 1.615)
    z_hub_in: int = 16              # pignon d'entrée du moyeu
    z_hub_out: int = 16             # pignon vissé sur la fixation de disque
    hub_slot: float = 16.0          # course de tension de la chaîne secondaire
    # Machine d'arbre : un seul moteur sans balais, en prise permanente sur l'arbre transversal. Moteur
    # d'assistance sur route, génératrice sur l'eau (elle charge le pédalage et mesure sa puissance, qui sert
    # de consigne au moteur immergé). Encombrement d'un moteur de 63 mm, noté de mémoire.
    z_gen_ring: int = 36            # couronne sur l'arbre (la plus grande qui passe sous le dossier)
    z_gen: int = 11                 # pignon de la machine
    gen_y: float = -80.0            # plan de sa chaîne, à tribord
    gen_x: float = -669.0           # axe de la machine, derrière le couple porteur, au-dessus de la poutre
    gen_z: float = 291.0
    gen_r: float = 32.0
    gen_len: float = 74.0
    z_arm: tuple = (16, 16)         # dents arbre -> roue, sur chaque bras
    # ---------------- commande de direction ----------------
    lever_x: float = -230.0         # pivot des leviers (axe parallèle à Y)
    lever_y: float = 262.0
    lever_z: float = 335.0
    lever_len: float = 290.0        # du pivot au haut de la poignée
    lever_arm: float = 95.0         # du pivot à l'attache des câbles
    horn: float = 75.0              # demi-longueur des palonniers (fourche et tête de safran)
    steer_deg: float = 30.0         # braquage visé de chaque côté
    rud_bar_z: float = 600.0        # palonnier arrière, au-dessus du pont
    # ---------------- freins ----------------
    drum_r: float = 50.0            # tambours dans les moyeux arrière (encombrement)
    disc_r: float = 80.0            # disque avant
    # ---------------- relevage des foils ----------------
    # Un secteur à gorge, solidaire du foil et centré sur son axe, garde un bras de levier constant sur les 180
    # degrés de rotation. Foils avant : bout de manoeuvre vers un taquet sur le plat-bord, et sandow de rappel
    # qui compense le poids. Foil arrière : secteur claveté sur l'axe de relevage, palan dans le cockpit.
    # Masses et centres de gravité supposés, à remplacer par ceux des foils réels.
    lift_r: float = 70.0            # rayon du secteur des foils avant (limité par le plat-bord)
    lift_q: float = 60.0            # rayon d'attache du sandow sur le secteur
    foil_mass: float = 2.3          # kg, mât et aile d'un foil avant (hypothèse)
    foil_cg: float = 550.0          # distance de l'axe au centre de gravité (hypothèse)
    rud_lift_r: float = 90.0        # rayon du secteur du foil arrière (limité par le palonnier)
    rud_mass: float = 6.0           # kg, mât, aile, moteur et hélice (hypothèse)
    rud_cg: float = 600.0
    rud_tackle: int = 6             # brins du palan arrière
    # ---------------- batterie ----------------
    # 2 kWh en 48 V, en deux caissons étanches de part et d'autre de l'étrave, à l'avant du cockpit : c'est là
    # qu'elle charge le mieux la roue avant et redresse l'assiette sur l'eau (devis de masses). Encombrement supposé.
    batt_x0: float = 780.0          # derrière le couple +760, hors de portée des pieds
    batt_len: float = 220.0
    batt_w: float = 95.0
    batt_h: float = 140.0
    batt_y0: float = 15.0           # jeu avec l'étrave
    # ---------------- étanchéité des sorties d'arbre ----------------
    seal_tube_r: float = 22.0       # tube de traversée (diamètre 44, alésage 35 pour un joint 25 x 35 x 7)
    seal_flange_r: float = 36.0     # bride qui pince la toile

P = Params()
HINGE_BOLTS = [(300, 315), (325, 360), (300, 405), (325, 438)]          # (y, z) dans le couple porteur des foils
FERR_AR_BOLTS = [(215, 250), (120, 222)]                                # (y, z) vis de couture de la ferrure porteuse arrière
FERRURE_BOLTS = [(270, 250), (190, 228), (82, 215)]                     # (y, z) vis de couture de la ferrure porteuse, le long du couple
LOCK_BOLTS = [(300, 440), (325, 415)]                                   # (y, z) équerre de verrou des bras
STEM_BOLTS = [(1200, 435), (1200, 500), (1262, 440), (1262, 500)]        # (x, z) dans l'étrave

# ----------------------------------------------------------------------------
# FORMES DE COQUE
# ----------------------------------------------------------------------------
def hb(t):
    if t >= 0: return P.B_half * max(0.0, 1 - t ** 2.4) ** 0.7
    return P.B_half * (1 - 0.35 * (-t) ** 3)
def zk(t): return P.z_keel + (P.rise_fwd * t ** 3 if t >= 0 else P.rise_aft * (-t) ** 3)
def zg(t): return P.z_gun + P.sheer * t * t
def sect(t, th):
    """point (y, z) de la section à l'abscisse t, th de 0 (plat-bord bâbord) à pi (tribord)"""
    g, k = zg(t), zk(t)
    return (hb(t) * math.cos(th), g - (g - k) * max(0.0, math.sin(th)) ** 0.6)
def section_pts(t, n=121):
    u = np.linspace(0, 1, n)
    return [sect(t, math.pi * (0.5 - 0.5 * math.cos(math.pi * a))) for a in u]
def deck_pts(t, n=25):
    return [(hb(t) * u, zg(t) + P.crown * (1 - u * u)) for u in np.linspace(-1, 1, n)[1:-1]]
def hull_poly(t, deck=True):
    return Polygon(section_pts(t) + (deck_pts(t) if deck else [])).buffer(0)
def normal(t, th):
    e = 1e-4
    a, b = sect(t, max(th - e, 0)), sect(t, min(th + e, math.pi))
    ty, tz = b[0] - a[0], b[1] - a[1]; L = math.hypot(ty, tz)
    n = (tz / L, -ty / L); p = sect(t, th)
    if n[0] * p[0] + n[1] * (p[1] - (zg(t) + zk(t)) / 2) < 0: n = (-n[0], -n[1])
    return n
def stringer_frames(t):
    """liste de (centre, n, tg) des 7 lisses + plats-bords à l'abscisse t"""
    s = P.stringer; out = []
    for sg in (1, -1):                                   # plats-bords, affleurants
        out.append(((sg * (hb(t) - s / 2), zg(t) - s / 2), (sg, 0.0), (0.0, sg)))
    for f in P.stringer_pos:
        th = math.pi * f; p = sect(t, th); n = normal(t, th)
        out.append(((p[0] - n[0] * s / 2, p[1] - n[1] * s / 2), n, (-n[1], n[0])))
    return out

# ----------------------------------------------------------------------------
# POUTRE, ÉTRAVE, GOUSSET (profils dans le plan XZ)
# ----------------------------------------------------------------------------
BEAM_X0 = P.x_transom + P.t_plate / 2
BEAM_X1 = 1014 - P.t_frame / 2
def beam_bot(x): return zk(x / P.HL) + P.stringer
def beam_top(x): return beam_bot(x) + P.beam_h
def band(x0, x1, f0, f1, n=160):
    xs = np.linspace(x0, x1, n)
    return Polygon([(x, f0(x)) for x in xs] + [(x, f1(x)) for x in xs[::-1]])
def deck_under(x):
    t = x / P.HL; return zg(t) + P.crown - P.skin_gap - P.stringer
def stem_poly():
    xb = BEAM_X1; x_tip = P.t_bow * P.HL
    bot = [(x, beam_top(x)) for x in np.linspace(P.stem_x0, xb, 12)]
    bot += [(x, zk(x / P.HL) + P.stringer) for x in np.linspace(xb, x_tip, 40)]
    top = [(x, deck_under(x)) for x in np.linspace(x_tip, 1014, 30)]
    top += [(1014, P.stem_top_aft), (P.stem_x0 + 60, P.stem_top_aft)]
    return Polygon(bot + top).buffer(0)
def knee_poly():
    x0 = BEAM_X0
    bot = [(x, beam_top(x)) for x in np.linspace(x0, P.knee_x1, 20)]
    return Polygon(bot + [(P.knee_x1, beam_top(P.knee_x1) + 50), (x0, deck_under(x0))]).buffer(0)

# ----------------------------------------------------------------------------
# COUPLES (plan YZ)
# ----------------------------------------------------------------------------
def biggest(g):
    if g.geom_type == 'Polygon': return g
    parts = [q for q in g.geoms if q.geom_type == 'Polygon' and q.area > 50]
    if len(parts) > 1: print('  ! pièce en plusieurs morceaux, je garde le plus grand :', [round(q.area) for q in parts])
    return max(parts, key=lambda q: q.area)

STEM = stem_poly(); KNEE = knee_poly()
def frame_poly(x, kind):
    t = x / P.HL; s = P.stringer; tol = P.tol
    closed = kind in ('closed', 'bulk', 'transom')
    outer = hull_poly(t, deck=closed).buffer(-P.skin_gap, 24)
    if kind in ('bulk', 'transom'):
        body = outer
    else:
        w = P.ring_U if kind == 'U' else P.ring
        inner = outer.buffer(-w, 24)
        if not closed and not inner.is_empty:
            inner = unary_union([inner, affinity.translate(inner, yoff=4 * w)]).convex_hull
        body = outer.difference(inner)
        zf = beam_top(x) + (P.floor_over_foil if abs(x - P.x_frame_foil) < 1 else P.floor_over_U if kind == 'U' else P.floor_over)
        body = body.union(box(-P.floor_half, 0, P.floor_half, zf).intersection(outer))
        if abs(x - P.x_frame_axle) < 1:          # surépaisseurs pour les paliers
            for sg in (1, -1):
                y0, y1 = sorted((sg * (P.brg_y - 78), sg * 400))
                body = body.union(box(y0, P.shaft_z - 40, y1, P.shaft_z + 40).intersection(outer))
    # encoches de lisses
    for (c, n, tg) in stringer_frames(t):
        h = (s + tol) / 2
        if n[1] == 0:    # plat-bord
            sg = n[0]; y0 = sg * (hb(t) - s - tol); y1 = sg * (hb(t) + 10)
            body = body.difference(box(min(y0, y1), zg(t) - s - tol, max(y0, y1), zg(t) + 60))
        else:
            p = (c[0] + n[0] * s / 2, c[1] + n[1] * s / 2)
            q = [(p[0] + n[0] * a + tg[0] * b, p[1] + n[1] * a + tg[1] * b) for a, b in ((10, h), (10, -h), (-(s + tol), -h), (-(s + tol), h))]
            body = body.difference(Polygon(q))
    if closed:           # lisse d'axe de pont
        zt = zg(t) + P.crown
        body = body.difference(box(-(s + tol) / 2, zt - s - tol, (s + tol) / 2, zt + 10))
    # passage de la poutre
    if BEAM_X0 < x < BEAM_X1:
        body = body.difference(box(-P.beam_w / 2 - tol, 0, P.beam_w / 2 + tol, beam_top(x) + tol))
    # mi-bois avec l'étrave
    xs0, _, xs1, _ = STEM.bounds
    if xs0 + 30 < x < xs1:
        seg = STEM.intersection(LineString([(x, 0), (x, 2000)]))
        zb, zt = seg.bounds[1], seg.bounds[3]
        body = body.difference(box(-P.t_plate / 2 - tol, 0, P.t_plate / 2 + tol, (zb + zt) / 2))
    holes = []
    if abs(x - P.x_frame_foil) < 1: holes += [(sg * yy, zz, 8.5) for sg in (1, -1) for yy, zz in HINGE_BOLTS + FERRURE_BOLTS]
    if kind == 'transom': holes += [(sg * 30, zz, 8.5) for sg in (1, -1) for zz in P.rud_gz]
    if abs(x - P.x_frame_axle) < 1: holes += [(sg * yy, zz, 8.5) for sg in (1, -1) for yy, zz in LOCK_BOLTS + FERR_AR_BOLTS]
    if abs(x - P.x_frame_axle) < 1: holes += [(sg * (P.brg_y + d), P.shaft_z, P.brg_bolt) for sg in (1, -1) for d in (-P.brg_J / 2, P.brg_J / 2)]
    for yy, zz, d in holes: body = body.difference(Point(yy, zz).buffer(d / 2, 16))
    return biggest(body.buffer(0)).simplify(0.1)

def ferrure_poly():
    """Ferrure porteuse des foils avant : une tôle d'aluminium d'un seul tenant, d'une charnière à l'autre, plaquée
    sur chaque face du couple porteur. Elle reprend la flexion que le contreplaqué ne peut pas passer au-dessus de
    la poutre de quille. En retrait des lisses : aucune encoche."""
    x = P.x_frame_foil; hy, hz = P.hinge_y, P.hinge_z
    dedans = hull_poly(x / P.HL, deck=False).buffer(-(P.skin_gap + P.stringer + 2), 24)
    g = frame_poly(x, 'U').intersection(dedans)
    for sg in (1, -1):
        for y0, z0, y1, z1 in ((278, 295, 340, hz + 18), (278, 467, hy + 38, hz + 21)):       # oreilles de charnière, au-dessus du plat-bord
            g = g.union(box(min(sg * y0, sg * y1), z0, max(sg * y0, sg * y1), z1))
    g = biggest(g.buffer(0)); plein = Polygon(g.exterior).buffer(-9)
    for sg in (1, -1):
        for yy, zz in HINGE_BOLTS + FERRURE_BOLTS:
            assert plein.contains(Point(sg * yy, zz)), ("vis de ferrure trop près du bord", yy, zz)
            g = g.difference(Point(sg * yy, zz).buffer(4.25, 16))
        g = g.difference(Point(sg * hy, hz).buffer(6.25, 16)).difference(Point(sg * (hy - P.hinge_lock_r), hz).buffer(5.25, 16))
    return biggest(g.buffer(0)).simplify(0.1)

def stem_with_slots():
    g = STEM
    for x, kind in P.stations:
        if STEM.bounds[0] + 30 < x < STEM.bounds[2]:
            seg = STEM.intersection(LineString([(x, 0), (x, 2000)]))
            zm = (seg.bounds[1] + seg.bounds[3]) / 2
            g = g.difference(box(x - P.t_frame / 2 - P.tol, zm, x + P.t_frame / 2 + P.tol, 2000))
    for xx, zz in STEM_BOLTS: g = g.difference(Point(xx, zz).buffer(4.25, 16))
    return biggest(g.buffer(0)).simplify(0.1)

# ----------------------------------------------------------------------------
# HYDROSTATIQUE (intégration numérique des sections)
# ----------------------------------------------------------------------------
def volume_below(zw, deck=False, n=261):
    ts = np.linspace(-1, P.t_bow, n); A = []
    for t in ts:
        h = hull_poly(t, deck=deck)
        A.append(h.intersection(box(-1000, 0, 1000, zw)).area if zw is not None else h.area)
    return float(getattr(np, 'trapezoid', None)(A, ts * P.HL) if hasattr(np, 'trapezoid') else np.trapz(A, ts * P.HL)) / 1e6      # litres
def draft_for(mass_kg):
    lo, hi = P.z_keel, P.z_gun
    for _ in range(40):
        m = (lo + hi) / 2
        if volume_below(m) < mass_kg: lo = m
        else: hi = m
    return (lo + hi) / 2 - P.z_keel

# ----------------------------------------------------------------------------
# TRANSMISSION PRIMAIRE (tracé dans le plan XZ, vu de tribord)
# ----------------------------------------------------------------------------
# La chaîne descend du plateau, court dans le caisson de quille sous le siège, puis remonte au pignon
# de l'arbre. Brin tendu : rectiligne entre deux galets. Brin mou : dans un fourreau posé au fond du caisson.
PITCH = 12.7
def rp(z): return PITCH / (2 * math.sin(math.pi / z))          # rayon primitif
XA = P.x_frame_axle + P.t_U + P.brg_h                           # abscisse de l'arbre arrière
def tube_z(x): return beam_bot(x) + P.t_flange + 9.0            # axe du fourreau du brin mou
def tangent(cA, rA, cB, rB):
    """brin droit de la roue A vers la roue B. Rayon signé : + si la chaîne tourne dans le sens horaire."""
    D = (cB[0] - cA[0], cB[1] - cA[1]); dist = math.hypot(*D)
    a = math.atan2(D[1], D[0]) + math.acos((rA - rB) / dist)
    n = (math.cos(a), math.sin(a))
    return (cA[0] + rA * n[0], cA[1] + rA * n[1]), (cB[0] + rB * n[0], cB[1] + rB * n[1])
def chain_layout():
    ri, rs, ria = rp(P.z_idler), rp(P.z_idler_slack), rp(P.z_idler_aft)
    W = {'moyeu': ((P.hub_x, P.hub_z), rp(P.z_hub_in)),
         'tendu_ar': ((P.idler_aft_x, beam_top(P.idler_aft_x) + 6), -ria),
         'tendu_av': ((P.idler_fwd_x, beam_top(P.idler_fwd_x) + 8), -ri),
         'plateau': ((P.bb_x, P.bb_z), rp(P.z_ring)),
         'mou_av': ((P.slack_fwd_x, tube_z(P.slack_fwd_x) + rs), rs),
         'mou_ar': ((P.slack_aft_x, tube_z(P.slack_aft_x) + rs), rs)}
    order = ['moyeu', 'tendu_ar', 'tendu_av', 'plateau', 'mou_av']
    segs = [tangent(*W[a], *W[b]) for a, b in zip(order, order[1:])]
    tube = [(x, tube_z(x)) for x in np.linspace(P.slack_fwd_x, P.slack_aft_x, 40)]
    last = tangent(*W['mou_ar'], *W['moyeu'])
    def arc(name, p_in, p_out):
        c, r = W[name]
        a0 = math.atan2(p_in[1] - c[1], p_in[0] - c[0]); a1 = math.atan2(p_out[1] - c[1], p_out[0] - c[0])
        return abs(r) * (((a0 - a1) if r > 0 else (a1 - a0)) % (2 * math.pi))
    L = sum(math.dist(a, b) for a, b in segs + [last]) + sum(math.dist(a, b) for a, b in zip(tube, tube[1:]))
    L += arc('moyeu', last[1], segs[0][0]) + arc('tendu_ar', segs[0][1], segs[1][0]) + arc('tendu_av', segs[1][1], segs[2][0])
    L += arc('plateau', segs[2][1], segs[3][0]) + arc('mou_av', segs[3][1], tube[0]) + arc('mou_ar', tube[-1], last[0])
    def x_at(seg, z):                                            # abscisse d'un brin à la cote z
        (x0, z0), (x1, z1) = seg; return x0 + (x1 - x0) * (z - z0) / (z1 - z0)
    # lumières dans la semelle haute de la poutre : (x0, x1, y0, y1)
    m = 12.0; cy = P.chain_y
    s_fwd = (P.idler_fwd_x - ri - m, max(x_at(segs[3], beam_top(P.slack_fwd_x)), P.slack_fwd_x + rs) + m, cy - 10, cy + 10)
    s_aft = (min(x_at(last, beam_top(P.slack_aft_x)), P.slack_aft_x - rs) - m, P.idler_aft_x + ria + m, cy - 10, cy + 10)
    # chaîne secondaire : du pignon de sortie du moyeu au pignon de l'arbre
    hub, arb = (W['moyeu'][0], rp(P.z_hub_out)), ((XA, P.shaft_z), rp(P.z_shaft))
    sec = [tangent(*hub, *arb), tangent(*arb, *hub)]
    ent = math.dist(hub[0], arb[0]); da = math.asin((arb[1] - hub[1]) / ent)
    L2 = 2 * math.dist(*sec[0]) + arb[1] * (math.pi + 2 * da) + hub[1] * (math.pi - 2 * da)
    jeux = {'galet tendu arrière / pignon du moyeu': math.dist(W['tendu_ar'][0], W['moyeu'][0]) - ria - W['moyeu'][1],
            'galets arrière entre eux': math.dist(W['tendu_ar'][0], W['mou_ar'][0]) - ria - rs,
            'pignons de la chaîne secondaire': ent - hub[1] - arb[1]}
    for k, v in jeux.items():                                    # entre cercles primitifs : il faut la place des dents
        if v < 8: print(f"  ! {k} : {v:.1f} mm entre cercles primitifs")
    return {'roues': W, 'brins_tendus': segs[:3], 'brins_mous': [segs[3], last], 'fourreau': tube,
            'longueur': L, 'lumieres': [s_fwd, s_aft], 'secondaire': sec, 'longueur_secondaire': L2, 'entraxe_secondaire': ent,
            'jeux': jeux}
CH = chain_layout()

# potence de pédalier : plaque encastrée dans la poutre, entre les deux couples qui encadrent le pédalier
def _half(kind): return P.t_U if kind == 'U' else P.t_frame / 2
POT_X0 = max(x + _half(k) for x, k in P.stations if x < P.bb_x) + P.tol
POT_X1 = min(x - _half(k) for x, k in P.stations if x > P.bb_x) - P.tol
BB_BOLTS = [(-40, -28), (40, -28), (-40, 28), (40, 28)]
def potence_poly():
    bot = [(x, beam_bot(x) + P.t_flange) for x in np.linspace(POT_X0, POT_X1, 10)]
    top = [(POT_X1, beam_top(POT_X1) + 60), (P.bb_x + 55, P.bb_z + 50), (P.bb_x - 55, P.bb_z + 50), (POT_X0, beam_top(POT_X0) + 60)]
    g = Polygon(bot + top).buffer(0).difference(Point(P.bb_x, P.bb_z).buffer(21.5, 24))
    for dx, dz in BB_BOLTS: g = g.difference(Point(P.bb_x + dx, P.bb_z + dz).buffer(3.25, 12))
    return g
CH['lumieres'].append((POT_X0 - P.tol, POT_X1 + P.tol, -P.t_plate / 2 - P.tol, P.t_plate / 2 + P.tol))
for _x0, _x1, _, _ in CH['lumieres'][:2]:                       # les lumières de chaîne doivent rester entre deux couples
    for _x, _k in P.stations:
        if _x0 - _half(_k) < _x < _x1 + _half(_k): print(f"  ! lumière de chaîne {_x0:.0f}..{_x1:.0f} sous le couple x={_x}")

# ----------------------------------------------------------------------------
# CONSTRUCTION
# ----------------------------------------------------------------------------
def build(outdir, apercu=True):
    import cadquery as cq
    V = cq.Vector
    def solid(poly, to3d, vec):
        def wire(ring):
            """contour -> fil : cercles vrais, courbes en splines, angles vifs conservés (STEP léger)"""
            c2 = np.array(ring.coords)[:-1]; n = len(c2)
            pts = [V(*to3d(a, b)) for a, b in c2]
            d0 = c2 - np.roll(c2, 1, axis=0); d1 = np.roll(c2, -1, axis=0) - c2
            turn = np.abs(np.degrees(np.arctan2(d0[:, 0] * d1[:, 1] - d0[:, 1] * d1[:, 0], (d0 * d1).sum(axis=1))))
            l0 = np.hypot(*d0.T); l1 = np.hypot(*d1.T); med = np.median(l1)
            corners = [i for i in range(n) if turn[i] > 15 or max(l0[i], l1[i]) > 4 * med]   # angles vifs et extrémités de segments droits
            if not corners:
                cen = c2.mean(axis=0); r = np.hypot(*(c2 - cen).T)
                if n >= 16 and r.std() < 0.02 * r.mean():
                    o = V(*to3d(0, 0)); nrm = (V(*to3d(1, 0)) - o).cross(V(*to3d(0, 1)) - o)
                    return cq.Wire.makeCircle(float(r.mean()), V(*to3d(*cen)), nrm)
                return cq.Wire.assembleEdges([cq.Edge.makeSpline(pts, periodic=True)])
            edges = []
            for k, i in enumerate(corners):
                j = corners[(k + 1) % len(corners)]
                run = [pts[m % n] for m in range(i, (j if j > i else j + n) + 1)]
                edges.append(cq.Edge.makeLine(run[0], run[1]) if len(run) == 2 else cq.Edge.makeSpline(run))
            return cq.Wire.assembleEdges(edges)
        return cq.Solid.extrudeLinear(wire(poly.exterior), [wire(r) for r in poly.interiors], V(*vec))

    parts = []   # (nom, solide, couleur)
    flats = []   # (nom, épaisseur, quantité, polygone 2D, gravures)
    def engr_frame(poly, x):
        L = [LineString([(0, 0), (0, 2000)]), LineString([(-1000, P.z_ref), (1000, P.z_ref)])]
        return [l.intersection(poly) for l in L]

    # couples, cloisons, tableau arrière
    names = {'closed': 'couple', 'open': 'couple', 'bulk': 'cloison', 'U': 'couple-porteur', 'transom': 'tableau-arriere'}
    stations = [(P.x_transom, 'transom')] + list(P.stations)
    for i, (x, kind) in enumerate(stations):
        poly = frame_poly(x, kind)
        th = {'U': 2 * P.t_U, 'transom': P.t_plate}.get(kind, P.t_frame)
        nm = f"C{i:02d}_{names[kind]}_x{int(x):+05d}"
        parts.append((nm, solid(poly, lambda a, b, x=x, th=th: (x - th / 2, a, b), (th, 0, 0)),
                      {'U': (0.54, 0.35, 0.19), 'bulk': (0.81, 0.66, 0.45), 'transom': (0.54, 0.35, 0.19)}.get(kind, (0.72, 0.53, 0.31))))
        flats.append((nm, P.t_U if kind == 'U' else th, 2 if kind == 'U' else 1, poly, engr_frame(poly, x)))

    # poutre de quille
    tf = P.t_flange
    web = band(BEAM_X0, BEAM_X1, lambda x: beam_bot(x) + tf, lambda x: beam_top(x) - tf)
    for sg, nm in ((1, 'babord'), (-1, 'tribord')):
        y0 = sg * (P.beam_w / 2) - (P.t_web if sg > 0 else 0)
        parts.append((f"poutre_ame_{nm}", solid(web, lambda a, b, y0=y0: (a, y0, b), (0, P.t_web, 0)), (0.54, 0.35, 0.19)))
    flats.append(("poutre_ame", P.t_web, 2, web, []))
    xs = np.linspace(BEAM_X0, BEAM_X1, 400)
    arc = float(np.sum(np.hypot(np.diff(xs), np.diff([beam_bot(x) for x in xs]))))
    for nm, f0, f1 in (("poutre_semelle_basse", beam_bot, lambda x: beam_bot(x) + tf), ("poutre_semelle_haute", lambda x: beam_top(x) - tf, beam_top)):
        sd = solid(band(BEAM_X0, BEAM_X1, f0, f1), lambda a, b: (a, -P.beam_w / 2, b), (0, P.beam_w, 0))
        if nm.endswith("haute"):                             # lumières : chaîne (avant, arrière) et potence de pédalier
            for x0, x1, y0, y1 in CH['lumieres']: sd = sd.cut(cq.Solid.makeBox(x1 - x0, y1 - y0, 400, V(x0, y0, 0)))
        parts.append((nm, sd, (0.62, 0.42, 0.24)))
    s_of = lambda x: float(np.interp(x, xs, np.concatenate([[0], np.cumsum(np.hypot(np.diff(xs), np.diff([beam_bot(q) for q in xs])))])))
    top_flat = box(0, 0, arc, P.beam_w)
    for x0, x1, y0, y1 in CH['lumieres']: top_flat = top_flat.difference(box(s_of(x0), y0 + P.beam_w / 2, s_of(x1), y1 + P.beam_w / 2))
    flats.append(("poutre_semelle_basse_a_cintrer", tf, 1, box(0, 0, arc, P.beam_w), []))
    flats.append(("poutre_semelle_haute_a_cintrer", tf, 1, top_flat, []))

    # étrave prolongée et gousset arrière
    stem = stem_with_slots()
    parts.append(("etrave", solid(stem, lambda a, b: (a, -P.t_plate / 2, b), (0, P.t_plate, 0)), (0.54, 0.35, 0.19)))
    flats.append(("etrave", P.t_plate, 1, stem, []))
    parts.append(("gousset_arriere", solid(KNEE, lambda a, b: (a, -P.t_plate / 2, b), (0, P.t_plate, 0)), (0.54, 0.35, 0.19)))
    flats.append(("gousset_arriere", P.t_plate, 1, KNEE, []))

    # ======================================================== INTERFACES
    ALU = (0.72, 0.75, 0.78); STEEL = (0.35, 0.37, 0.4); CARB = (0.12, 0.13, 0.15); ENV = (0.25, 0.25, 0.27)
    def bx(x0, x1, y0, y1, z0, z1): return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
    def cyl(p0, p1, r):
        d = V(*p1) - V(*p0); return cq.Solid.makeCylinder(r, d.Length, V(*p0), d)
    def circ(a, b, d): return Point(a, b).buffer(d / 2, 16)
    PLY = (0.81, 0.66, 0.45); SPRUCE = (0.85, 0.72, 0.5); RUBBER = (0.1, 0.1, 0.11)
    def ring(p0, p1, r_out, r_in):
        d = (V(*p1) - V(*p0)).normalized()
        return cyl(p0, p1, r_out).cut(cyl((V(*p0) - d).toTuple(), (V(*p1) + d).toTuple(), r_in))
    def sy(sg, a, b): return tuple(sorted((sg * a, sg * b)))        # intervalle en Y, symétrisé
    def gaine(pts, r=3.0):
        """tube souple passant par une liste de points (gaine de câble, fourreau de chaîne)"""
        vp = [V(*q) for q in pts]; e = cq.Edge.makeSpline(vp)
        return cq.Solid.sweep(cq.Wire.makeCircle(r, vp[0], e.tangentAt(0)), [], cq.Wire.assembleEdges([e]), True, True)

    # --- 1. charnières des foils avant : deux joues alu prennent le couple porteur en sandwich
    hx, hy, hz, tU = P.x_frame_foil, P.hinge_y, P.hinge_z, P.t_U
    ferr = ferrure_poly()                                    # remplace les quatre joues de charnière
    flats.append(("ferrure_porteuse_foils", P.t_cheek, 2, ferr, [], 'ALU'))
    for i, x0 in enumerate((hx - tU - P.t_cheek, hx + tU)):
        parts.append((f"ferrure_porteuse_foils_{i + 1}", solid(ferr, lambda a, b, x0=x0: (x0, a, b), (P.t_cheek, 0, 0)), ALU))
    def hinge_side(mirror, folded, tag):
        out = []
        out.append((f"axe_charniere_{tag}", cyl((hx - tU - 10, hy, hz), (hx + tU + 21, hy, hz), 6), STEEL))
        yl = hy - P.hinge_lock_r
        out.append((f"goupille_verrou_{tag}", cyl((hx - tU - 10, yl, hz), (hx + tU + 10, yl, hz), 5), STEEL))
        ym = hy + P.hinge_e; zt = hz - 21
        mov = [("chape_pivotante", bx(hx - tU + 1, hx + tU - 1, hy - 45, hy + 70, zt, hz + 13), ALU),
               ("platine_de_mat", bx(hx - P.plate_L / 2, hx + P.plate_L / 2, ym - P.plate_W / 2, ym + P.plate_W / 2, zt - 8, zt), ALU),
               ("foil_L_encombrement", solid(foil_L, lambda a, b: (hx - P.mast_chord / 2, a, b), (P.mast_chord, 0, 0)), CARB),
               ("tenon_sabot", bx(hx - 9.5, hx + 9.5, P.shoe_pin_y - 14, ym - P.mast_thk / 2, P.shoe_z - 13, P.shoe_z + 13), ALU)]
        # relevage : secteur à gorge fixé sur la platine de mât, devant la joue avant
        xs0 = hx + tU + P.t_cheek + 5; xc = xs0 + 4; xe = xs0 + 16       # plan du secteur, plan du sandow
        mov += [("secteur_relevage", solid(sect_f, lambda a, b: (xs0, a, b), (8, 0, 0)), ALU),
                ("equerre_secteur", bx(xs0 - 4, xs0 + 12, hy + 12, hy + 62, zt, zt + 6), ALU),
                ("attache_sandow_secteur", cyl((xs0 + 8, hy + P.lift_q, hz), (xe + 4, hy + P.lift_q, hz), 4), STEEL)]
        for nm, sd, c in mov:
            if folded: sd = sd.rotate(V(0, hy, hz), V(1, hy, hz), 180)
            out.append((f"{nm}_{tag}", sd, c))
        yR, zA = 300.0, 300.0                                            # renvoi du sandow sur la joue, ancrage en bas de la joue
        out.append((f"rea_sandow_{tag}", cyl((hx + tU + P.t_cheek, yR, hz), (xe + 4, yR, hz), 4), STEEL))
        out.append((f"ancrage_sandow_{tag}", cyl((hx + tU + P.t_cheek, yR, zA), (xe + 4, yR, zA), 4), STEEL))
        yq = hy - P.lift_q if folded else hy + P.lift_q
        out.append((f"sandow_rappel_1_{tag}", cyl((xe, yq - 5, hz), (xe, yR + 5, hz), 3.5), RUBBER))
        out.append((f"sandow_rappel_2_{tag}", cyl((xe, yR, hz - 5), (xe, yR, zA + 5), 3.5), RUBBER))
        # bout de relevage : du secteur à deux filoirs sur la joue, puis au taquet coinceur sur le plat-bord
        B = (318.0, hz + 11.0); a0 = math.asin((zt + 6 - hz) / P.lift_r)
        if folded: T = (hy + P.lift_r * math.cos(math.pi + a0), hz + P.lift_r * math.sin(math.pi + a0))     # le bout tire sur son attache
        else:
            d = math.hypot(hy - B[0], hz - B[1]); a = math.atan2(hz - B[1], hy - B[0]) + math.asin(P.lift_r / d)
            L = math.sqrt(d * d - P.lift_r ** 2); T = (B[0] + L * math.cos(a), B[1] + L * math.sin(a))          # tangent au secteur
        xq = -120.0; tq = xq / P.HL; yq_ = hb(tq) - P.stringer / 2
        out.append((f"bout_relevage_brin_{tag}", cyl((xc, T[0], T[1]), (xc, B[0], B[1]), 2.5), (0.85, 0.38, 0.17)))
        out.append((f"bout_relevage_{tag}", gaine([(xc, B[0], B[1]), (xc, 290, B[1]), (xc, 262, B[1]), (xc - 24, 255, B[1] - 8), (40, 270, 484),
            (-50, 322, 473), (xq, yq_, zg(tq) + 9)], 2.5), (0.85, 0.38, 0.17)))
        for k, y0 in enumerate((311, 252)):
            out.append((f"filoir_relevage_{k + 1}_{tag}", bx(hx + tU + P.t_cheek, xc + 6, y0, y0 + 16, B[1] - 9, B[1] - 3.5), ALU))
        out.append((f"taquet_relevage_{tag}", bx(xq - 18, xq + 18, yq_ - 8, yq_ + 8, zg(tq), zg(tq) + 5.5), ALU))
        # sabot de verrouillage : corps et chape hors de la coque, cale entre la toile et le couple, contre-plaque
        # contre le chant intérieur du couple, deux tirants de part et d'autre des joues
        w2 = P.shoe_w / 2; zsb = P.shoe_z
        for k, x0 in enumerate((hx - w2, hx + w2 - 16)):                 # deux flasques de 16 mm, traversés par les tirants
            out.append((f"sabot_flasque_{k + 1}_{tag}", solid(sabot_p, lambda a, b, x0=x0: (x0, a, b), (16, 0, 0)), ALU))
        for k, x0 in enumerate((hx - 24, hx + 12)):
            out.append((f"sabot_oreille_{k + 1}_{tag}", bx(x0, x0 + 12, y_sab, P.shoe_pin_y + 14, zsb - 15, zsb + 15), ALU))
        out.append((f"goupille_sabot_{tag}", cyl((hx - 30, P.shoe_pin_y, zsb), (hx + 30, P.shoe_pin_y, zsb), 5), STEEL))
        out.append((f"cale_sabot_{tag}", solid(cale_p, lambda a, b: (hx - tU, a, b), (2 * tU, 0, 0)), PLY))
        out.append((f"contre_plaque_sabot_{tag}", bx(hx - w2 + 2, hx + w2 - 2, y_cp - 10, y_cp, zsb - 15, zsb + 15), ALU))
        for k, sgx in enumerate((-1, 1)):
            out.append((f"tirant_sabot_{k + 1}_{tag}", cyl((hx + sgx * (w2 - 12), y_cp - 16, zsb), (hx + sgx * (w2 - 12), y_sab - 22, zsb), 4), STEEL))
        return [(nm, sd.mirror("XZ") if mirror else sd, c) for nm, sd, c in out]
    # foil en L d'une seule pièce : mât droit, coude arrondi, aile droite (profil dans le plan YZ)
    ym_ = hy + P.hinge_e; zw_ = hz - 29 - P.mast_len; re = P.foil_elbow_r
    ligne = [(ym_, hz - 29), (ym_, zw_ + re)] + [(ym_ + re - re * math.cos(a), zw_ + re - re * math.sin(a)) for a in np.linspace(0, math.pi / 2, 14)[1:]] + [(ym_ + P.wing_span, zw_)]
    foil_L = LineString(ligne).buffer(P.mast_thk / 2, cap_style=2, resolution=8)
    # sabot : console trapézoïdale entre la toile et la chape
    Hs = hull_poly(hx / P.HL, deck=False); y_sab = P.shoe_pin_y - 25
    sabot_p = biggest(Polygon([(320, P.shoe_z - 32), (320, P.shoe_z + 32), (y_sab, P.shoe_z + 15), (y_sab, P.shoe_z - 15)]).difference(Hs))
    cale_p = biggest(Hs.difference(Hs.buffer(-P.skin_gap, 24)).intersection(box(200, P.shoe_z - 30, 500, P.shoe_z + 30)))
    seg = frame_poly(hx, 'U').intersection(LineString([(150, P.shoe_z), (500, P.shoe_z)]))
    y_cp = seg.bounds[0] - 7                                              # chant intérieur du couple porteur, à cette hauteur
    flats.append(("cale_sabot", 2 * tU, 2, cale_p, []))
    flats.append(("sabot_flasque", 16.0, 4, sabot_p, [], 'ALU'))
    zt_ = hz - 21                                                        # secteur : disque tronqué au ras de son équerre
    sect_f = Point(hy, hz).buffer(P.lift_r, 48).intersection(box(0, zt_ + 6, 1000, 1000)).difference(circ(hy, hz, 12.5))
    flats.append(("secteur_relevage_foil", 8.0, 2, sect_f, [], 'ALU'))
    parts += hinge_side(False, False, "babord_deploye") + hinge_side(True, True, "tribord_replie")

    # --- 1 ter. batterie : deux caissons posés sur la poutre, de part et d'autre de l'étrave, sanglés
    zb0 = beam_top(P.batt_x0 + P.batt_len) + 2
    for sg, tag in ((1, "babord"), (-1, "tribord")):
        y0, y1 = sy(sg, P.batt_y0, P.batt_y0 + P.batt_w)
        parts.append((f"batterie_caisson_{tag}", bx(P.batt_x0, P.batt_x0 + P.batt_len, y0, y1, zb0, zb0 + P.batt_h), ENV))
    # --- 2. arbre arrière : paliers à semelle vissés sur la face avant du couple porteur
    xf = P.x_frame_axle + tU; xa = xf + P.brg_h; zS = P.shaft_z
    ys = P.arm_y + P.hub_old / 2 + 25
    parts.append(("arbre_arriere", ring((xa, -ys, zS), (xa, ys, zS), P.shaft_d / 2, P.shaft_bore / 2), STEEL))
    zB = zg(xa / P.HL) + 5                                   # au-dessus du plat-bord
    yin = P.arm_y - P.hub_old / 2 - 6                        # face intérieure du flasque de bras
    brk = unary_union([box(190, zS - 25, 338, zS + 25), box(285, zS + 25, 336, zB + 37), box(285, zB, yin - 2, zB + 37)])
    for d in (-P.brg_J / 2, P.brg_J / 2): brk = brk.difference(circ(P.brg_y + d, zS, P.brg_bolt))
    for yy, zz in LOCK_BOLTS: brk = brk.difference(circ(yy, zz, 8.5))
    # Ferrure porteuse arrière : les deux équerres de verrou deviennent une seule tôle, d'un palier à l'autre, sur la
    # face arrière du couple. Son âme monte au-dessus de la poutre, là où le contreplaqué n'a que 25 mm, et laisse
    # passer la chaîne et la couronne de la machine d'arbre (à tribord). Un bord tombé raidit son bord supérieur.
    xA = P.x_frame_axle; tA = P.t_ferr_ar; zw = P.ferr_ar_top
    dedA = hull_poly(xA / P.HL, deck=False).buffer(-(P.skin_gap + P.stringer + 2), 24)
    fa = frame_poly(xA, 'U').intersection(dedA).intersection(box(-338, 0, 338, zS + 25))
    fa = fa.union(Polygon([(-68, zw), (110, zw), (170, 258), (170, 215), (-68, 215)]))
    fa = fa.union(brk).union(affinity.scale(brk, xfact=-1, origin=(0, 0)))
    fa = fa.difference(box(-P.beam_w / 2 - P.tol, 0, P.beam_w / 2 + P.tol, beam_top(xA - tU - tA) + 1.5)).difference(box(-94, 266, -70, 1000))
    fa = biggest(fa.buffer(0)); plein = Polygon(fa.exterior).buffer(-9)
    for sg in (1, -1):
        for yy, zz in FERR_AR_BOLTS:
            assert plein.contains(Point(sg * yy, zz)), ("vis de ferrure arrière trop près du bord", yy, zz)
            fa = fa.difference(circ(sg * yy, zz, 8.5))
        for d in (-P.brg_J / 2, P.brg_J / 2): fa = fa.difference(circ(sg * (P.brg_y + d), zS, P.brg_bolt))
        for yy, zz in LOCK_BOLTS: fa = fa.difference(circ(sg * yy, zz, 8.5))
    fa = biggest(fa.buffer(0)).simplify(0.1)
    flats.append(("ferrure_porteuse_arriere", tA, 1, fa, [], 'ALU'))
    parts.append(("ferrure_porteuse_arriere", solid(fa, lambda a, b: (xA - tU - tA, a, b), (tA, 0, 0)), ALU))
    parts.append(("ferrure_porteuse_arriere_bord_tombe", bx(xA - tU, xA - tU + 22, -54, 48, zw - tA, zw), ALU))
    # flasque de bras : pivot, axe de roue et deux trous de goupille (route / relevé)
    lift = math.radians(P.arm_lift); a0 = math.atan2(P.arm_dz, P.arm_dx)
    hornA = (xa, zS + P.arm_lock_r)
    aB = math.pi / 2 - lift if P.arm_dx > 0 else math.pi / 2 + lift
    hornB = (xa + P.arm_lock_r * math.cos(aB), zS + P.arm_lock_r * math.sin(aB))
    axl = (xa + P.arm_dx, zS + P.arm_dz)
    armp = unary_union([Point(xa, zS).buffer(36), Point(*axl).buffer(30), Point(*hornA).buffer(16), Point(*hornB).buffer(16)]).convex_hull
    sgx = 1 if P.arm_dx > 0 else -1; entret = ((xa + 70 * sgx, zS + 65), (xa + 10 * sgx, zS + 80))
    garde = unary_union([Point(xa, zS).buffer(44), Point(*axl).buffer(36), Point(*hornA).buffer(24), Point(*hornB).buffer(24)] + [Point(*q).buffer(18) for q in entret])
    jour = armp.buffer(-16).difference(garde).buffer(-5).buffer(5)                    # ajour : il reste 16 mm de bord et les bossages
    if not jour.is_empty: armp = armp.difference(jour)
    armp = armp.difference(circ(xa, zS, 30)).difference(circ(*axl, 10.5)).difference(circ(*hornA, 10.5)).difference(circ(*hornB, 10.5))
    armp = biggest(armp.buffer(0))
    flats.append(("flasque_bras_arriere", 6.0, 4, armp, [], 'ALU'))
    def rear_side(mirror, lifted, tag):
        out = []
        yc = P.brg_y
        out.append((f"palier_semelle_{tag}", bx(xf, xf + 15, yc - 70, yc + 70, zS - 19, zS + 19), ALU))
        out.append((f"palier_corps_{tag}", cyl((xa, yc - 17, zS), (xa, yc + 17, zS), 32), ALU))
        x0 = P.x_frame_axle - tU - P.t_ferr_ar
        out.append((f"equerre_verrou_patte_{tag}", bx(x0 + P.t_ferr_ar, xa + 32, yin - 8, yin - 2, zB, zB + 37), ALU))
        # éclisse : elle renvoie dans le plat-bord l'effort de la goupille, qui pousse d'avant en arrière
        ecl = Polygon([(x, zg(x / P.HL) + 0.5) for x in np.linspace(xa + 32, xa + 192, 9)] + [(x, zg(x / P.HL) + 4.5) for x in np.linspace(xa + 192, xa + 32, 9)])
        out.append((f"eclisse_verrou_plat_bord_{tag}", solid(ecl, lambda a, b: (a, 345, b), (0, 14, 0)), ALU))
        out.append((f"goupille_bras_{tag}", cyl((xa, yin - 14, hornA[1]), (xa, yin + 12, hornA[1]), 5), STEEL))
        # sortie d'arbre : platine rigide collée contre le couple, tube traversant, toile pincée entre deux brides, joint à lèvre
        yp = yc + 71; rt = P.seal_tube_r
        pl = bx(xf, xf + 72, yp, yp + 9, zS - 35, zS + 35).cut(cyl((xa, yp - 1, zS), (xa, yp + 10, zS), rt + 0.5))
        out.append((f"platine_traversee_{tag}", pl, PLY))
        out.append((f"tube_traversee_{tag}", ring((xa, yp + 1, zS), (xa, yin - 3, zS), rt, 17.5), ALU))
        out.append((f"contre_bride_{tag}", ring((xa, yp + 9, zS), (xa, yp + 13, zS), P.seal_flange_r, rt + 0.5), ALU))
        out.append((f"bride_de_toile_{tag}", ring((xa, yp + 19, zS), (xa, yp + 22, zS), P.seal_flange_r, rt + 0.5), ALU))
        out.append((f"joint_a_levre_{tag}", ring((xa, yin - 10, zS), (xa, yin - 3, zS), 17.5, P.shaft_d / 2), RUBBER))
        y1 = P.arm_y + P.hub_old / 2
        mov = [(f"flasque_bras_int", solid(armp, lambda a, b: (a, yin, b), (0, 6, 0)), ALU),
               (f"flasque_bras_ext", solid(armp, lambda a, b: (a, y1, b), (0, 6, 0)), ALU),
               ("fourreau_pivot_bras", cyl((xa, yin, zS), (xa, y1 + 6, zS), 15), STEEL),
               ("pignon_arbre", cyl((xa, yin + 12, zS), (xa, yin + 15, zS), 33), STEEL),
               ("pignon_roue_libre", cyl((axl[0], yin + 12, axl[1]), (axl[0], yin + 15, axl[1]), 33), STEEL),
               ("moyeu_arriere", cyl((axl[0], yin + 6, axl[1]), (axl[0], y1, axl[1]), 22), STEEL),
               ("tambour_frein", ring((axl[0], P.arm_y + 24, axl[1]), (axl[0], P.arm_y + 50, axl[1]), P.drum_r, 22.5), ALU),
               ("roue_arriere_encombrement", cyl((axl[0], P.arm_y - 22, axl[1]), (axl[0], P.arm_y + 22, axl[1]), P.wheel_r), ENV)]
        for k, (ex, ez) in enumerate(entret):
            mov.append((f"entretoise_bras_{k + 1}", cyl((ex, yin + 6, ez), (ex, y1, ez), 8), ALU))
        for nm, sd, c in mov:
            if lifted: sd = sd.rotate(V(xa, 0, zS), V(xa, 1, zS), -P.arm_lift if P.arm_dx > 0 else P.arm_lift)
            out.append((f"{nm}_{tag}", sd, c))
        return [(nm, sd.mirror("XZ") if mirror else sd, c) for nm, sd, c in out]
    parts += rear_side(False, True, "babord_releve") + rear_side(True, False, "tribord_route")
    flats.append(("platine_traversee_arbre", 9.0, 2, box(0, 0, 72, 70).difference(circ(P.brg_h, 35, 2 * P.seal_tube_r + 1)), []))

    # --- 2 bis. foil arrière : tête de safran relevable, orientable sur deux fémelots
    xp, Lx, Lz = P.rud_pin_x, P.rud_Lx, P.rud_Lz; xt = P.x_transom - P.t_plate / 2
    for k, z0 in enumerate(P.rud_gz):
        parts.append((f"femelot_{k + 1}_embase", bx(xt - 6, xt, -45, 45, z0 - 20, z0 + 20), ALU))
        parts.append((f"femelot_{k + 1}_bras", bx(xp - 20, xt - 6, -18, 18, z0 - 6, z0 + 6), ALU))
    g0, g1 = P.rud_gz
    parts.append(("axe_direction_arriere", cyl((xp, 0, g0 - 20), (xp, 0, g1 + 10), 6), STEEL))
    parts.append(("bloc_pivot_safran", bx(xp - 18, xp + 18, -11, 11, g0 + 6, g1 - 6), ALU))
    locks = [(Lx + P.rud_lock_r * math.cos(math.radians(a)), Lz + P.rud_lock_r * math.sin(math.radians(a))) for a in (270, 216, 90)]
    zb_ = P.rud_bar_z                                         # corne des joues : porte le palonnier sur l'axe de direction, au-dessus du pont
    rc = unary_union([Point(xp, g0 + 30).buffer(18), Point(xp, g1 - 28).buffer(18), Point(Lx, Lz).buffer(45), Point(xp, zb_).buffer(20)]
                     + [Point(*q).buffer(22) for q in locks]).convex_hull
    for z0 in P.rud_gz: rc = rc.difference(box(xp - 22, z0 - 8, xt, z0 + 8))
    rc = biggest(rc.difference(circ(Lx, Lz, 12.5))).difference(circ(xp, zb_, 16.5))
    for q in locks: rc = rc.difference(circ(*q, 10.5))
    flats.append(("joue_tete_de_safran", 6.0, 2, rc, [], 'ALU'))
    for sg, tag in ((1, "babord"), (-1, "tribord")):
        parts.append((f"joue_tete_de_safran_{tag}", solid(rc, lambda a, b, y0=(11 if sg > 0 else -17): (a, y0, b), (0, 6, 0)), ALU))
    parts.append(("palonnier_direction_arriere", cyl((xp, -P.horn - 7, zb_), (xp, P.horn + 7, zb_), 8), ALU))
    parts.append(("axe_relevage_foil_arriere", cyl((Lx, -22, Lz), (Lx, 31, Lz), 6), STEEL))
    # relevage : secteur claveté sur l'axe, à bâbord de la tête de safran ; le bout descend à une poulie sur le
    # tableau, tout près de l'axe de direction, passe sur le pont et rejoint un palan dans le cockpit
    rr = P.rud_lift_r; ys_ = 24.0
    sect_r = Point(Lx, Lz).buffer(rr, 48).difference(circ(Lx, Lz, 12.2))
    rayons = unary_union([affinity.rotate(box(Lx - rr, Lz - 8, Lx + rr, Lz + 8), a, origin=(Lx, Lz)) for a in (0, 60, 120)])
    sect_r = sect_r.difference(Point(Lx, Lz).buffer(rr - 18, 48).difference(Point(Lx, Lz).buffer(26, 32)).difference(rayons)).buffer(0)   # jante, moyeu et six rayons
    flats.append(("secteur_relevage_foil_arriere", 8.0, 1, sect_r, [], 'ALU'))
    parts.append(("secteur_relevage_foil_arriere", solid(sect_r, lambda a, b: (a, ys_ - 4, b), (0, 8, 0)), ALU))
    parts.append(("poulie_relevage_tableau", bx(xt - 14, xt, ys_ - 7, ys_ + 7, 496, 510), ALU))
    def zd(x, y, dz=9.0):                                    # au-dessus du pont
        t = x / P.HL; return zg(t) + P.crown * (1 - (y / hb(t)) ** 2) + dz
    def yb(x, dy): return hb(x / P.HL) - dy                  # depuis le plat-bord
    cord = [(Lx + rr + 2.5, ys_, Lz), (xt - 7, ys_, 492), (xt - 22, ys_ + 4, 530), (xt - 4, ys_ + 12, zd(xt, ys_) + 8)]
    cord += [(x, y, zd(x, y)) for x, y in ((-1200, 70), (-1090, 125), (-975, 165), (-870, 200))]
    cord += [(-800, 232, zd(-806, 232) + 6), (-730, yb(-730, 62), zg(-730 / P.HL) + 42), (-625, yb(-625, 52), zg(-625 / P.HL) + 52)]
    parts.append(("bout_relevage_arriere", gaine(cord, 2.5), (0.85, 0.38, 0.17)))
    pa, pb = (-612, yb(-612, 52), zg(-0.47) + 52), (-330, yb(-330, 40), zg(-0.25) + 30)
    parts.append(("palan_relevage_arriere_encombrement", cyl(pa, pb, 11), ENV))
    xq = -200.0; tq = xq / P.HL
    parts.append(("garant_relevage_arriere", gaine([(pb[0] + 4, pb[1], pb[2]), (-270, yb(-270, 22), zg(-0.2) + 18), (xq, yb(xq, 9), zg(tq) + 9)], 2.5), (0.85, 0.38, 0.17)))
    parts.append(("taquet_relevage_arriere", bx(xq - 18, xq + 18, yb(xq, 17), yb(xq, 1), zg(tq), zg(tq) + 5.5), ALU))
    parts.append(("goupille_foil_arriere", cyl((locks[0][0], -22, locks[0][1]), (locks[0][0], 22, locks[0][1]), 5), STEEL))
    zb = Lz + 40 - P.rud_mast
    parts.append(("mat_foil_arriere_encombrement", bx(Lx - 55, Lx + 55, -8, 8, zb, Lz + 40), CARB))
    parts.append(("aile_foil_arriere_encombrement", bx(Lx - 55, Lx + 55, -300, 300, zb - 8, zb + 8), CARB))
    parts.append(("moteur_immerge_encombrement", cyl((Lx - 100, 0, zb + 90), (Lx + 170, 0, zb + 90), 40), ALU))
    parts.append(("helice_tuyere_encombrement", cyl((Lx - 190, 0, zb + 90), (Lx - 105, 0, zb + 90), 95), ENV))

    # --- 3. direction avant relevable : console pivotante + jeu de direction + fourche
    ang = math.radians(P.head_angle); u = (-math.cos(ang), math.sin(ang)); wv = (math.sin(ang), math.cos(ang))
    A = (P.axle_x, P.wheel_r); Q = (A[0] - P.rake * wv[0], A[1] - P.rake * wv[1])
    at = lambda sv: (Q[0] + u[0] * sv, Q[1] + u[1] * sv)
    C = at(P.wheel_r + 20); H = at(P.wheel_r + 90)
    p3 = lambda q, y=0.0: (q[0], y, q[1])
    fcheek = box(1185, 405, P.fork_px + 30, 520)
    for xx, zz in STEM_BOLTS: fcheek = fcheek.difference(circ(xx, zz, 8.5))
    fcheek = fcheek.difference(circ(P.fork_px, P.fork_pz, 12.5)).difference(circ(P.fork_px, P.fork_kz, 10.5))
    flats.append(("joue_direction", 5.0, 2, fcheek, [], 'ALU'))
    for sg, tag in ((1, "babord"), (-1, "tribord")):
        y0 = 20 if sg > 0 else -25
        parts.append((f"joue_direction_{tag}", solid(fcheek, lambda a_, b_, y0=y0: (a_, y0, b_), (0, 5, 0)), ALU))
        parts.append((f"cale_direction_{tag}", bx(1185, 1278, 9 if sg > 0 else -20, 20 if sg > 0 else -9, 405, 520), (0.81, 0.66, 0.45)))
    parts.append(("axe_relevage_direction", cyl((P.fork_px, -32, P.fork_pz), (P.fork_px, 32, P.fork_pz), 6), STEEL))
    parts.append(("goupille_direction", cyl((P.fork_px, -32, P.fork_kz), (P.fork_px, 32, P.fork_kz), 5), STEEL))
    parts.append(("console_direction_patte", bx(P.fork_px - 18, P.fork_px + 18, -18, 18, P.fork_kz - 18, P.fork_pz + 18), ALU))
    parts.append(("console_direction_bras", cyl(p3((P.fork_px, P.fork_pz)), p3(H), 18), ALU))
    parts.append(("douille_direction", cyl(p3(at(P.wheel_r + 30)), p3(at(P.wheel_r + 150)), 22), ALU))
    parts.append(("pivot_fourche", cyl(p3(C), p3(at(P.wheel_r + 170)), 14.3), STEEL))
    parts.append(("te_fourche", cyl(p3(C, -55), p3(C, 55), 14), STEEL))
    for sg, tag in ((1, "babord"), (-1, "tribord")):
        parts.append((f"fourreau_fourche_{tag}", cyl(p3(C, sg * 55), p3(A, sg * 55), 10), STEEL))
    parts.append(("axe_roue_avant", cyl(p3(A, -60), p3(A, 60), 5), STEEL))
    parts.append(("roue_avant_encombrement", cyl(p3(A, -20), p3(A, 20), P.wheel_r), ENV))

    # --- 4. siège sur deux rails posés sur les varangues
    zr = max(beam_top(x) for x in (-440, -260, -80, 100)) + P.floor_over
    def slab(p0, p1, th):
        dx, dz = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dz); n = (-dz / L * th, dx / L * th)
        return Polygon([p0, p1, (p1[0] + n[0], p1[1] + n[1]), (p0[0] + n[0], p0[1] + n[1])])
    for sg, tag in ((1, "babord"), (-1, "tribord")):
        xr = P.x_frame_foil - P.t_U - P.t_cheek                # les rails s'arrêtent contre la ferrure porteuse, sur une équerre
        parts.append((f"rail_siege_{tag}", bx(-440, xr - 2, sg * 50 - 10, sg * 50 + 10, zr, zr + 20)
                      .cut(bx(-441, xr - 1, sg * 50 - 8, sg * 50 + 8, zr + 2, zr + 18)), ALU))     # tube carré 20 x 20 x 2
        parts.append((f"equerre_rail_siege_{tag}", bx(xr - 30, xr, sg * 50 - 10, sg * 50 + 10, zr - 6, zr), ALU))
    zs = zr + 20; sa = math.radians(P.seat_angle)
    pan = slab((P.seat_x, zs), (P.seat_x + 340, zs + 30), 9)
    back = slab((P.seat_x, zs), (P.seat_x - P.seat_back * math.cos(sa), zs + P.seat_back * math.sin(sa)), 9)
    for nm, pl, L in (("siege_assise", pan, 341.3), ("siege_dossier", back, P.seat_back)):
        parts.append((nm, solid(pl, lambda a_, b_: (a_, -P.seat_w / 2, b_), (0, P.seat_w, 0)), (0.86, 0.78, 0.6)))
        flats.append((nm, 9.0, 1, box(0, 0, L, P.seat_w), []))

    # --- 5. pédalier et transmission primaire (chaîne dans le caisson de quille)
    cy = P.chain_y; ybb = cy + P.bb_chainline; bbx, bbz = P.bb_x, P.bb_z
    pot = potence_poly()
    parts.append(("potence_pedalier", solid(pot, lambda a, b: (a, -P.t_plate / 2, b), (0, P.t_plate, 0)), (0.54, 0.35, 0.19)))
    flats.append(("potence_pedalier", P.t_plate, 1, pot, []))
    plt_ = box(bbx - 55, bbz - 42, bbx + 55, bbz + 42).difference(circ(bbx, bbz, 43))
    for dx, dz in BB_BOLTS: plt_ = plt_.difference(circ(bbx + dx, bbz + dz, 6.5))
    flats.append(("platine_pedalier", 4.0, 2, plt_, [], 'ALU'))
    for y0, tag in ((P.t_plate / 2, "babord"), (-P.t_plate / 2 - 4, "tribord")):
        parts.append((f"platine_pedalier_{tag}", solid(plt_, lambda a, b, y0=y0: (a, y0, b), (0, 4, 0)), ALU))
    hs = P.bb_shell / 2
    parts.append(("boitier_pedalier", ring((bbx, ybb - hs, bbz), (bbx, ybb + hs, bbz), 21, 12), ALU))
    parts.append(("axe_pedalier", cyl((bbx, ybb - 78, bbz), (bbx, ybb + 78, bbz), 8.5), STEEL))
    parts.append(("plateau", ring((bbx, cy - 1.5, bbz), (bbx, cy + 1.5, bbz), rp(P.z_ring), 30), STEEL))
    for sg, tag in ((-1, "tribord"), (1, "babord")):         # manivelle tribord vers l'avant, bâbord vers l'arrière
        ya, yb_ = sy(sg, abs(ybb + sg * 78), abs(ybb + sg * 78) + 12); xe = bbx - sg * P.crank
        parts.append((f"manivelle_{tag}", bx(min(bbx, xe) - 14, max(bbx, xe) + 14, ya, yb_, bbz - 11, bbz + 11), ALU))
        yo = ybb + sg * 90
        parts.append((f"pedale_{tag}", cyl((xe, yo, bbz), (xe, yo + sg * 95, bbz), 8), ENV))
    W = CH['roues']
    for key, nm, ri_ in (('moyeu', 'pignon_entree_moyeu', 17.0), ('tendu_av', 'galet_tendu_avant', 5.1), ('tendu_ar', 'galet_tendu_arriere', 5.1),
                         ('mou_av', 'galet_mou_avant', 4.1), ('mou_ar', 'galet_mou_arriere', 4.1)):
        (x0, z0), r = W[key]; h = 1.5 if key == 'moyeu' else 4.0
        parts.append((nm, ring((x0, cy - h, z0), (x0, cy + h, z0), abs(r), ri_), STEEL))
    for key, tag in (('tendu_av', 'avant'), ('tendu_ar', 'arriere')):      # galets tendus : axe sur deux paliers vissés sur la semelle
        (x0, z0), _ = W[key]; zt = max(beam_top(x0 - 12), beam_top(x0 + 12)) + 0.3
        sup = cyl((x0, cy - 22, z0), (x0, cy + 22, z0), 5)
        for ya in (cy - 22, cy + 14): sup = sup.fuse(bx(x0 - 12, x0 + 12, ya, ya + 8, zt, zt + 18))
        parts.append((f"support_galet_tendu_{tag}", sup, ALU))
    for key, tag in (('mou_av', 'avant'), ('mou_ar', 'arriere')):          # galets mous : axe traversant le caisson, en appui dans les âmes
        (x0, z0), _ = W[key]; w = P.beam_w / 2 - P.t_web - 1
        parts.append((f"axe_galet_mou_{tag}", cyl((x0, -w, z0), (x0, w, z0), 4), STEEL))
    for k, (a, b) in enumerate(CH['brins_tendus']):
        parts.append((f"chaine_brin_tendu_{k + 1}", cyl((a[0], cy, a[1]), (b[0], cy, b[1]), 4.5), STEEL))
    for k, (a, b) in enumerate(CH['brins_mous']):
        parts.append((f"chaine_brin_mou_{k + 1}", cyl((a[0], cy, a[1]), (b[0], cy, b[1]), 4.5), STEEL))
    parts.append(("fourreau_brin_mou", gaine([(x, cy, z) for x, z in CH['fourreau'] if P.slack_aft_x + 18 < x < P.slack_fwd_x - 18], 8), RUBBER))

    xl, yl, zl = P.lever_x, P.lever_y, P.lever_z; zc = zl + P.lever_arm; hn = P.horn; zgr = zl + P.lever_len
    # --- 5 bis. changement de vitesses : moyeu à vitesses intégrées en renvoi, sous le dossier
    hx, hz = P.hub_x, P.hub_z; yh = cy + P.hub_chainline              # milieu du moyeu
    yR, yL = yh - P.hub_width / 2, yh + P.hub_width / 2               # contre-écrous droit (tribord) et gauche
    y2 = yL - P.hub_disc_off + 1.5                                    # plan de la chaîne secondaire
    parts.append(("moyeu_vitesses_encombrement", cyl((hx, yh - 28, hz), (hx, yh + 36, hz), P.hub_r), ENV))
    parts.append(("moyeu_vitesses_axe", cyl((hx, yR - 24, hz), (hx, yL + 24, hz), 5), STEEL))
    parts.append(("moyeu_vitesses_commande", ring((hx, yR + 3, hz), (hx, cy - 6, hz), 30, 8), ALU))
    parts.append(("pignon_sortie_moyeu", ring((hx, y2 - 1.5, hz), (hx, y2 + 1.5, hz), rp(P.z_hub_out), 17), STEEL))
    parts.append(("pignon_arbre_secondaire", ring((xa, y2 - 1.5, zS), (xa, y2 + 1.5, zS), rp(P.z_shaft), P.shaft_d / 2 + 0.1), STEEL))
    for k, (a, b) in enumerate(CH['secondaire']):
        parts.append((f"chaine_secondaire_brin_{k + 1}", cyl((a[0], y2, a[1]), (b[0], y2, b[1]), 4.5), STEEL))
    # platines : vissées sur les flancs de la poutre, lumière de tension dans l'axe moyeu -> arbre
    ux, uz = (hx - xa) / CH['entraxe_secondaire'], (hz - zS) / CH['entraxe_secondaire']; e = P.hub_slot / 2
    fente = LineString([(hx - e * ux, hz - e * uz), (hx + e * ux, hz + e * uz)])
    pied = box(hx - 52, beam_bot(hx) + 14, hx + 43, beam_top(hx) - 4)
    HUB_BOLTS = [(hx + dx, (beam_bot(hx) + beam_top(hx)) / 2 + 5 + dz) for dx in (-42, 33) for dz in (-10, 10)]
    plm = unary_union([pied, fente.buffer(24)]).convex_hull.difference(fente.buffer(5.2))
    for q in HUB_BOLTS: plm = plm.difference(circ(*q, 6.5))
    flats.append(("platine_moyeu_vitesses", 6.0, 2, plm, [], 'ALU'))
    parts.append(("platine_moyeu_tribord", solid(plm, lambda a, b: (a, yR - 6, b), (0, 6, 0)), ALU))
    parts.append(("platine_moyeu_babord", solid(plm, lambda a, b: (a, yL, b), (0, 6, 0)), ALU))
    parts.append(("cale_platine_moyeu_babord", solid(pied, lambda a, b: (a, P.beam_w / 2, b), (0, yL - P.beam_w / 2, 0)), SPRUCE))
    # --- 5 ter. machine d'arbre (moteur sur route, génératrice sur l'eau) : platine vissée sur le flanc tribord de la poutre
    gx, gz_, gy = P.gen_x, P.gen_z, P.gen_y; yf = -P.beam_w / 2      # flanc de la poutre
    parts.append(("couronne_machine_arbre", ring((xa, gy - 1.5, zS), (xa, gy + 1.5, zS), rp(P.z_gen_ring), P.shaft_d / 2 + 0.1), STEEL))
    parts.append(("pignon_machine_arbre", ring((gx, gy - 1.5, gz_), (gx, gy + 1.5, gz_), rp(P.z_gen), 5.1), STEEL))
    parts.append(("machine_arbre_encombrement", cyl((gx, yf, gz_), (gx, yf + P.gen_len, gz_), P.gen_r), ENV))
    parts.append(("machine_arbre_axe", cyl((gx, gy - 10, gz_), (gx, yf, gz_), 5), STEEL))
    cg, cs = ((xa, zS), rp(P.z_gen_ring)), ((gx, gz_), rp(P.z_gen))
    for k, (a, b) in enumerate((tangent(*cg, *cs), tangent(*cs, *cg))):
        parts.append((f"chaine_machine_brin_{k + 1}", cyl((a[0], gy, a[1]), (b[0], gy, b[1]), 4.5), STEEL))
    xb = P.x_frame_axle - tU - 4                                      # la platine s'arrête derrière le couple porteur
    plg = unary_union([box(gx - 44, beam_bot(gx) + 14, xb, beam_top(gx) - 4), Point(gx, gz_).buffer(40)]).convex_hull
    plg = plg.intersection(box(gx - 60, 0, xb, 1000)).difference(circ(gx, gz_, 30))
    for k in range(4):
        a = math.radians(45 + 90 * k); plg = plg.difference(circ(gx + 22 * math.cos(a), gz_ + 22 * math.sin(a), 4.5))
    for dx in (-36, 26):
        for dz in (-10, 10): plg = plg.difference(circ(gx + dx, (beam_bot(gx) + beam_top(gx)) / 2 + 5 + dz, 6.5))
    flats.append(("platine_machine_arbre", 6.0, 1, plg, [], 'ALU'))
    parts.append(("platine_machine_arbre", solid(plg, lambda a, b: (a, yf - 6, b), (0, 6, 0)), ALU))
    # commande : poignée tournante sur le levier tribord, gaine jusqu'au boîtier de commande du moyeu
    parts.append(("poignee_tournante_vitesses", ring((xl, -yl, zgr - 185), (xl, -yl, zgr - 147), 17, 11.2), RUBBER))
    parts.append(("gaine_vitesses", gaine([(xl - 22, -yl + 6, zgr - 170), (xl - 60, -yl + 25, 400), (-390, -215, 318), (-450, -140, 304),
        (hx + 30, yR - 14, hz + 26), (hx + 14, yR + 12, hz + 30)]), RUBBER))

    # --- 6. commande de direction : deux leviers, câbles sous gaine en va-et-vient vers la fourche et vers la tête de safran
    Pb = at(P.wheel_r + 179)                                 # palonnier de fourche, en tête de pivot
    parts.append(("palonnier_fourche", cyl(p3(Pb, -hn - 7), p3(Pb, hn + 7), 8), ALU))
    parts.append(("potence_butees_avant", bx(1287, 1299, -6, 6, P.fork_pz + 18, 628).fuse(cyl((1293, -hn - 7, 620), (1293, hn + 7, 620), 6)), ALU))
    parts.append(("support_butees_arriere", bx(-1173, -1167, -hn - 20, hn + 20, 548, zb_ + 12), ALU))
    def gz(x, dz=30.0): return zg(x / P.HL) - dz             # hauteur de passage sous le plat-bord
    for sg, tag in ((1, "babord"), (-1, "tribord")):
        parts.append((f"longeron_commande_{tag}", bx(-450, -70, *sy(sg, yl + 14, yl + 32), zl - 17, zl + 18), SPRUCE))
        parts.append((f"levier_direction_{tag}", cyl((xl, sg * yl, zl - 15), (xl, sg * yl, zgr - 110), 11), ALU))
        parts.append((f"poignee_{tag}", cyl((xl, sg * yl, zgr - 110), (xl, sg * yl, zgr), 15), RUBBER))
        parts.append((f"axe_levier_{tag}", cyl((xl, sg * (yl + 11), zl), (xl, sg * (yl + 14), zl), 5), STEEL))
        for x0, nm in ((xl + 80, "avant"), (xl - 92, "arriere")):          # butées de gaine, en équerre sur le longeron
            st = bx(x0, x0 + 12, *sy(sg, yl + 14, yl + 26), zl + 18, zc + 8).fuse(bx(x0, x0 + 12, *sy(sg, yl - 7, yl + 14), zc - 8, zc + 8))
            parts.append((f"butee_levier_{nm}_{tag}", st, ALU))
        parts.append((f"cable_levier_avant_{tag}", cyl((xl + 11, sg * yl, zc), (xl + 80, sg * yl, zc), 1.5), STEEL))
        parts.append((f"cable_levier_arriere_{tag}", cyl((xl - 80, sg * yl, zc), (xl - 11, sg * yl, zc), 1.5), STEEL))
        # vers la fourche : même côté, la gaine arrive par l'avant du levier
        parts.append((f"gaine_direction_avant_{tag}", gaine([(xl + 92, sg * yl, zc), (-80, sg * (yl + 2), zc + 2), (100, sg * 266, gz(100, 32)),
            (320, sg * 296, gz(320)), (540, sg * 278, gz(540)), (760, sg * 232, gz(760)), (900, sg * 190, 500), (1014, sg * 115, 534),
            (1170, sg * 80, 542), (1250, sg * hn, 590), (1287, sg * hn, 620)]), RUBBER))
        a_ = V(1299, sg * hn, 620); b_ = V(Pb[0], sg * hn, Pb[1])
        parts.append((f"cable_direction_avant_{tag}", cyl(a_.toTuple(), (b_ + (a_ - b_).normalized() * 8.5).toTuple(), 1.5), STEEL))
        # vers la tête de safran : croisée (levier tribord -> corne bâbord), la gaine arrive par l'arrière du levier
        parts.append((f"gaine_direction_arriere_{tag}", gaine([(xl - 92, sg * yl, zc), (-440, sg * (yl + 2), gz(-440)), (-620, sg * 256, 440),
            (-740, sg * 232, 492), (-806, sg * 195, 522), (-900, sg * 105, 550 + 6 * sg), (-1030, -sg * 15, 560 + 6 * sg),
            (-1120, -sg * 70, 592), (-1167, -sg * hn, zb_)]), RUBBER))
        parts.append((f"cable_direction_arriere_{tag}", cyl((-1173, sg * hn, zb_), (xp + 8.5, sg * hn, zb_), 1.5), STEEL))

    # --- 7. freins : tambours dans les moyeux arrière (levier à double tirage, à bâbord), disque à l'avant (levier tribord)
    parts.append(("disque_frein_avant", ring(p3(A, -32), p3(A, -30), P.disc_r, 20), STEEL))
    parts.append(("etrier_frein_avant", bx(A[0] - 60, A[0] - 30, -44.5, -34, A[1] + 50, A[1] + 85), ALU))
    for sg, tag, nm in ((1, "babord", "arriere_double_tirage"), (-1, "tribord", "avant")):
        parts.append((f"levier_frein_{nm}", cyl((xl + 21, sg * yl, zgr - 15), (xl + 45, sg * yl, zgr - 100), 5), ALU))
    out_ = lambda sg: [(-560, sg * 320, 480), (-600, sg * (yin - 5), 520)]     # sortie par-dessus le plat-bord, au pivot du bras
    parts.append(("gaine_frein_arriere_babord", gaine([(xl - 14, yl + 6, zgr - 125), (xl - 40, yl + 8, 468), (-300, 270, 458), (-440, 278, 450)] + out_(1)), RUBBER))
    parts.append(("gaine_frein_arriere_tribord", gaine([(xl - 14, yl - 6, zgr - 125), (xl - 40, yl - 10, 462), (-330, 248, 440), (-440, 244, 420),
        (-490, 225, 400), (-535, 150, 438), (-560, 0, 465), (-560, -200, 462), (-560, -280, 448)] + out_(-1)), RUBBER))
    parts.append(("gaine_frein_avant", gaine([(xl + 14, -yl + 6, zgr - 125), (xl + 50, -yl + 8, 470), (-80, -yl + 8, 452), (100, -256, gz(100, 20)),
        (320, -286, gz(320, 18)), (540, -268, gz(540, 18)), (760, -222, gz(760, 18)), (900, -178, 508), (1014, -98, 538), (1170, -60, 546),
        (1262, -36, 562), (1340, -30, 566), (1420, -36, 480), (1468, -36, 420), (A[0] - 45, -39, A[1] + 87)]), RUBBER))
    flats[:] = [f if len(f) == 6 else f + ('CONTREPLAQUE',) for f in flats]

    # lisses (lofts de sections carrées)
    xs = np.linspace(P.x_transom - P.t_plate / 2, 1255, 42); h = P.stringer / 2
    n_str = len(stringer_frames(0)); str_len = 0.0
    for j in range(n_str):
        wires = []; prev = None
        for x in xs:
            c, n, tg = stringer_frames(x / P.HL)[j]
            pts = [V(x, c[0] + n[0] * a + tg[0] * b, c[1] + n[1] * a + tg[1] * b) for a, b in ((h, h), (h, -h), (-h, -h), (-h, h))]
            wires.append(cq.Wire.makePolygon(pts + [pts[0]]))
            if prev is not None: str_len += math.dist((x, *c), prev)
            prev = (x, *c)
        parts.append((f"lisse_{j + 1}", cq.Solid.makeLoft(wires, True), (0.85, 0.72, 0.5)))

    # volume de coque de référence (surface de la toile)
    wires = []
    for t in np.linspace(-1, P.t_bow, 15):
        e1 = cq.Edge.makeSpline([V(t * P.HL, y, z) for y, z in section_pts(t, 25)])
        dk = [sect(t, math.pi)] + deck_pts(t, 9) + [sect(t, 0)]
        e2 = cq.Edge.makeSpline([V(t * P.HL, y, z) for y, z in dk])
        wires.append(cq.Wire.assembleEdges([e1, e2]))
    hull = cq.Solid.makeLoft(wires)

    assy = cq.Assembly(name="phoebe")
    for nm, s, col in parts: assy.add(s, name=nm, color=cq.Color(*col, 1))
    assy.add(hull, name="volume_coque_reference_a_masquer", color=cq.Color(0.93, 0.89, 0.78, 0.25))
    getattr(assy, "export", assy.save)(os.path.join(outdir, "phoebe-assemblage.step"))

    # ------------------------------------------------------------ DXF
    import ezdxf
    doc = ezdxf.new('R2010'); doc.units = 4; msp = doc.modelspace()
    for nm, col in (('DECOUPE', 7), ('GRAVURE', 1), ('TEXTE', 3)): doc.layers.add(nm, color=col)
    placed = []; cy = 0.0
    for mat, th in sorted({(f[5], f[1]) for f in flats}, key=lambda k: (k[0] != 'CONTREPLAQUE', k[1])):
        cx = 0.0; rowh = 0.0
        msp.add_text(f"{mat} {th:g} mm", dxfattribs={'layer': 'TEXTE', 'height': 40}).set_placement((0, cy - 70))
        for nm, t_, q, poly, eng, _m in [f for f in flats if (f[5], f[1]) == (mat, th)]:
            x0, y0, x1, y1 = poly.bounds
            if cx > 0 and cx + (x1 - x0) > 2500: cx = 0; cy += rowh + 60; rowh = 0
            dx, dy = cx - x0, cy - y0
            for ring in [poly.exterior] + list(poly.interiors):
                msp.add_lwpolyline([(a + dx, b + dy) for a, b in ring.coords], close=True, dxfattribs={'layer': 'DECOUPE'})
            for g in eng:
                for l in (getattr(g, 'geoms', [g]) if not g.is_empty else []):
                    if l.geom_type == 'LineString': msp.add_lwpolyline([(a + dx, b + dy) for a, b in l.coords], dxfattribs={'layer': 'GRAVURE'})
            lab = f"{nm}  ep.{t_:g}  x{q}"
            msp.add_text(lab, dxfattribs={'layer': 'TEXTE', 'height': 14}).set_placement((cx, cy + (y1 - y0) + 12))
            placed.append((affinity.translate(poly, dx, dy), lab, th))
            cx += (x1 - x0) + 50; rowh = max(rowh, y1 - y0 + 40)
        cy += rowh + 160
    doc.saveas(os.path.join(outdir, "phoebe-gabarits.dxf"))

    # ------------------------------------------------------------ bilan
    area = {}
    for nm, t_, q, poly, _, m_ in flats:
        if m_ == 'CONTREPLAQUE': area[t_] = area.get(t_, 0) + q * poly.area / 1e6
    m_ply = sum(a * t_ / 1000 * P.rho_ply for t_, a in area.items())
    m_str = str_len / 1000 * (P.stringer / 1000) ** 2 * P.rho_spruce
    rep = {
        "longueur_coque_mm": round(P.HL * (1 + P.t_bow)), "largeur_mm": 2 * P.B_half,
        "volume_sous_plat_bord_L": round(volume_below(None, deck=False)),
        "volume_total_avec_pont_L": round(volume_below(None, deck=True)),
        "volume_solide_STEP_L": round(hull.Volume() / 1e6),
        "masse_de_calcul_kg": P.mass_ref,
        "tirant_eau_mm": {f"{m:g} kg": round(draft_for(m)) for m in (135, P.mass_ref, P.mass_ref + 30)},
        "contreplaque_m2_par_epaisseur": {f"{k:g} mm": round(v, 2) for k, v in sorted(area.items())},
        "masse_contreplaque_kg": round(m_ply, 1), "lisses_m": round(str_len / 1000, 1), "masse_lisses_kg": round(m_str, 1),
        "nb_pieces_3D": len(parts),
        "largeur_hors_tout_route_mm": round(2 * (P.arm_y + P.hub_old / 2 + 6 + 8)),
        "envergure_foils_avant_mm": round(2 * (P.hinge_y + P.hinge_e + P.wing_span)),
    }
    ratio = P.z_ring / P.z_hub_in * P.z_hub_out / P.z_shaft * P.z_arm[0] / P.z_arm[1]
    devs = [ratio * g * 2 * math.pi * P.wheel_r / 1000 for g in P.hub_gears]
    sous_dossier = lambda x, z: -(x - P.seat_x) * math.sin(sa) - (z - zs) * math.cos(sa) - 9
    jeu_dossier = sous_dossier(P.hub_x, P.hub_z) - P.hub_r
    kg = P.z_gen_ring / P.z_gen; ent_g = math.dist((XA, P.shaft_z), (P.gen_x, P.gen_z))
    dag = math.asin((rp(P.z_gen_ring) - rp(P.z_gen)) / ent_g)
    Lg = 2 * ent_g * math.cos(dag) + rp(P.z_gen_ring) * (math.pi + 2 * dag) + rp(P.z_gen) * (math.pi - 2 * dag)
    arbre_80 = [80 * P.z_ring / P.z_hub_in * g * P.z_hub_out / P.z_shaft for g in P.hub_gears]
    arbre_25 = 25 / 3.6 / (2 * math.pi * P.wheel_r / 1000) * 60 * P.z_arm[1] / P.z_arm[0]
    course = P.horn * math.sin(math.radians(P.steer_deg)); a_lev = math.asin(course / P.lever_arm)
    rep["transmission"] = {
        "plateau_dents": P.z_ring, "moyeu_pignon_entree_dents": P.z_hub_in, "moyeu_pignon_sortie_dents": P.z_hub_out,
        "pignon_arbre_dents": P.z_shaft, "bras_dents_arbre_roue": list(P.z_arm), "vitesses": len(P.hub_gears),
        "rapport_plateau_sur_pignon_du_moyeu": round(P.z_ring / P.z_hub_in, 2),
        "developpement_m_par_tour_de_pedalier": [round(d, 2) for d in devs],
        "vitesse_kmh_a_80_tr_min": [round(d * 80 * 60 / 1000, 1) for d in devs],
        "moyeu_axe_x_z_mm": [P.hub_x, P.hub_z], "jeu_moyeu_sous_dossier_siege_recule_mm": round(jeu_dossier, 1),
        "jeu_moyeu_au_dessus_de_la_poutre_mm": round(P.hub_z - P.hub_r - beam_top(P.hub_x), 1),
        "chaine_secondaire_entraxe_mm": round(CH['entraxe_secondaire'], 1),
        "chaine_secondaire_mm": round(CH['longueur_secondaire']), "chaine_secondaire_maillons": round(CH['longueur_secondaire'] / PITCH, 1),
        "jeux_entre_cercles_primitifs_mm": {k: round(v, 1) for k, v in CH['jeux'].items()},
        "lumieres_de_chaine_mm": [round(l[1] - l[0]) for l in CH['lumieres'][:2]],
        "chaine_primaire_mm": round(CH['longueur']), "chaine_primaire_maillons": 2 * math.ceil(CH['longueur'] / PITCH / 2),
        "plan_de_chaine_y_mm": P.chain_y,
    }
    rep["machine_d_arbre"] = {
        "couronne_dents": P.z_gen_ring, "pignon_dents": P.z_gen, "rapport": round(kg, 2),
        "plan_de_chaine_y_mm": P.gen_y, "axe_x_z_mm": [P.gen_x, P.gen_z],
        "chaine_entraxe_mm": round(ent_g, 1), "chaine_maillons": round(Lg / PITCH, 1),
        "arbre_tr_min_a_80_tr_min_de_pedalage": [round(arbre_80[0]), round(arbre_80[-1])],
        "machine_tr_min_a_80_tr_min_de_pedalage": [round(arbre_80[0] * kg), round(arbre_80[-1] * kg)],
        "machine_tr_min_a_25_kmh": round(arbre_25 * kg),
        "couple_machine_Nm_pour_150_W_pedales": [round(150 / (a * kg * 2 * math.pi / 60), 1) for a in (arbre_80[0], arbre_80[-1])],
        "jeu_couronne_sous_dossier_mm": round(sous_dossier(XA, P.shaft_z) - rp(P.z_gen_ring) - 4.5, 1),
        "jeu_machine_au_dessus_de_la_poutre_mm": round(P.gen_z - P.gen_r - beam_top(P.gen_x), 1),
    }
    c_av = P.foil_mass * 9.81 * P.foil_cg / 1000; c_ar = P.rud_mass * 9.81 * P.rud_cg / 1000
    rep["relevage_des_foils"] = {
        "hypotheses": {"foil_avant_kg": P.foil_mass, "foil_avant_centre_de_gravite_mm": P.foil_cg,
                       "foil_arriere_kg": P.rud_mass, "foil_arriere_centre_de_gravite_mm": P.rud_cg},
        "foil_avant": {"couple_maxi_Nm": round(c_av, 1), "rayon_secteur_mm": P.lift_r,
                       "traction_sans_rappel_N": round(c_av / P.lift_r * 1000), "bout_a_reprendre_mm": round(math.pi * P.lift_r),
                       "bras_de_levier_sandow_a_mi_course_mm": round((hy - 300.0) * P.lift_q / math.hypot(hy - 300.0, P.lift_q)),
                       "tension_sandow_pour_compenser_a_mi_course_N": round(c_av * 1000 / ((hy - 300.0) * P.lift_q / math.hypot(hy - 300.0, P.lift_q)))},
        "foil_arriere": {"couple_maxi_Nm": round(c_ar, 1), "rayon_secteur_mm": P.rud_lift_r, "palan_brins": P.rud_tackle,
                         "traction_au_garant_N_sans_frottement": round(c_ar / P.rud_lift_r * 1000 / P.rud_tackle),
                         "garant_a_reprendre_mm": round(math.pi * P.rud_lift_r * P.rud_tackle)},
    }
    Fz = P.foil_share * P.mass_ref * 9.81 / 2; Mf = Fz * (P.hinge_e + P.wing_span / 2) / 1000      # portance au milieu de l'aile
    bras = P.hinge_z - P.shoe_z; Fs = Mf / bras * 1000
    rep["foils_avant"] = {
        "forme": "L d'une seule pièce à coude arrondi", "corde_mm": P.mast_chord, "rayon_du_coude_mm": P.foil_elbow_r,
        "surface_portante_projetee_par_foil_m2": round(P.wing_span * P.wing_chord / 1e6, 4),
        "sabot_de_verrouillage": {
            "hypothese": f"{round(P.foil_share * 100)} % de {P.mass_ref:g} kg sur les deux foils avant, portance au milieu de l'aile",
            "portance_par_foil_N": round(Fz), "moment_autour_de_la_charniere_Nm": round(Mf),
            "hauteur_goupille_mm": P.shoe_z, "bras_de_levier_sous_la_charniere_mm": round(bras),
            "effort_au_sabot_N": round(Fs), "effort_au_sabot_a_trois_fois_la_charge_N": round(3 * Fs),
            "par_tirant_a_trois_fois_la_charge_N": round(1.5 * Fs),
            "sans_sabot_effort_sur_la_goupille_de_charniere_a_trois_fois_la_charge_N": round(3 * Mf / P.hinge_lock_r * 1000),
            "au_dessus_de_la_flottaison_mm": {f"{m:g} kg": round(P.shoe_z - 15 - P.z_keel - draft_for(m)) for m in (P.mass_ref, P.mass_ref + 30)},
            "depassement_du_flanc_mm": round(P.shoe_pin_y + 14 - hb(P.x_frame_foil / P.HL)),
        },
    }
    # flexion du couple porteur des foils : la portance, à l'extérieur, est équilibrée par le poids, au milieu
    def haut(g, y): return g.intersection(LineString([(y, 0), (y, 900)])).length
    def larg(g, z): return g.intersection(LineString([(150, z), (600, z)])).length
    yL = P.hinge_y + P.hinge_e + P.wing_span / 2; cp = frame_poly(P.x_frame_foil, 'U')
    def sig(g, ep, n, y=None, z=None):
        h = haut(g, y) if y is not None else larg(g, z); bras = yL - (y if y is not None else 300.0)
        return round(Fz * bras / (n * ep * h * h / 6), 1)
    rep["foils_avant"]["ferrure_porteuse"] = {
        "principe": "deux tôles d'aluminium de 6 mm, d'une charnière à l'autre, de part et d'autre du couple porteur",
        "masse_des_deux_toles_kg": round(2 * ferr.area * P.t_cheek * 2.7e-6, 2), "vis_M8": 2 * len(HINGE_BOLTS + FERRURE_BOLTS),
        "hauteur_au_dessus_de_la_poutre_mm": round(haut(ferr, 0), 1),
        "contrainte_de_flexion_MPa_a_une_fois_la_charge": {
            "toles_seules_au_milieu": sig(ferr, P.t_cheek, 2, y=0), "toles_seules_dans_le_bras_z350": sig(ferr, P.t_cheek, 2, z=350),
            "contreplaque_seul_au_milieu": sig(cp, 2 * P.t_U, 1, y=0), "contreplaque_seul_dans_le_bras_z350": sig(cp, 2 * P.t_U, 1, z=350)},
        "contrainte_toles_seules_au_milieu_a_trois_fois_la_charge_MPa": round(3 * sig(ferr, P.t_cheek, 2, y=0)),
        "pression_axe_de_charniere_sur_les_toles_a_trois_fois_la_charge_MPa": round(3 * math.hypot(Fz, Fs) / (12 * 2 * P.t_cheek), 1),
    }
    # couple porteur arrière, sur route : tout le poids sur les deux roues arrière (majorant)
    Rr = P.rear_share * P.mass_ref * 9.81 / 2; port = P.arm_y - P.brg_y; Ma = Rr * port / 1000; Mc = Rr * P.brg_y / 1000
    cpa = frame_poly(P.x_frame_axle, 'U'); Zs = math.pi * (P.shaft_d ** 4 - P.shaft_bore ** 4) / (32 * P.shaft_d)
    def sga(g, ep, y): return round(Rr * (P.brg_y - abs(y)) / (ep * haut(g, y) ** 2 / 6), 1)
    Pg = Rr * abs(P.arm_dx) / P.arm_lock_r
    rep["couple_porteur_arriere"] = {
        "hypothese": f"{round(P.rear_share * 100)} % de {P.mass_ref:g} kg sur les deux roues arrière, paliers assimilés à des appuis simples, poids repris au milieu du couple",
        "reaction_par_roue_N": round(Rr),
        "arbre": {"porte_a_faux_roue_palier_mm": round(port), "moment_Nm": round(Ma), "contrainte_MPa_a_une_fois_la_charge": round(Ma * 1000 / Zs),
                  "contrainte_MPa_a_trois_fois_la_charge": round(3 * Ma * 1000 / Zs)},
        "moment_au_milieu_du_couple_Nm": round(Mc),
        "contrainte_de_flexion_MPa_a_une_fois_la_charge": {
            "contreplaque_seul_au_milieu": sga(cpa, 2 * P.t_U, 0), "ferrure_seule_au_milieu": sga(fa, P.t_ferr_ar, 0),
            "ferrure_seule_sous_la_chaine_de_la_machine": sga(fa, P.t_ferr_ar, -80)},
        "ferrure_seule_au_milieu_a_trois_fois_la_charge_MPa": round(3 * sga(fa, P.t_ferr_ar, 0)),
        "ferrure_masse_kg": round(fa.area * P.t_ferr_ar * 2.7e-6, 2),
        "goupille_de_bras": {"effort_N_a_une_fois_la_charge": round(Pg), "effort_N_a_trois_fois_la_charge": round(3 * Pg),
                             "direction": "d'avant en arrière, hors du plan du couple : renvoyé au plat-bord par une éclisse"},
    }
    # vol, à l'estime : vitesse à laquelle les foils portent le poids, puissance à l'hélice puis à la batterie
    W = P.mass_ref * 9.81; S_av = P.wing_span * P.wing_chord / 1e6; S_ar = 600 * 110 / 1e6; CL = 0.6
    v = math.sqrt(P.foil_share * W / 2 / (500 * CL * S_av))
    rep["vol_a_l_estime"] = {
        "hypotheses": {"masse_kg": P.mass_ref, "coefficient_de_portance_des_foils_avant": CL, "finesse_de_l_ensemble": [8, 12],
                       "rendement_helice_moteur_variateur": [0.55, 0.65], "batterie_Wh": 2000},
        "surface_portante_m2": {"un_foil_avant": round(S_av, 4), "foil_arriere": round(S_ar, 4)},
        "vitesse_de_vol_kmh": round(v * 3.6, 1),
        "coefficient_de_portance_du_foil_arriere_a_cette_vitesse": round((1 - P.foil_share) * W / (500 * v * v * S_ar), 2),
        "puissance_electrique_W": [round(W / 12 * v / 0.65, -1), round(W / 8 * v / 0.55, -1)],
        "autonomie_min": [round(2000 / (W / 8 * v / 0.55) * 60), round(2000 / (W / 12 * v / 0.65) * 60)],
    }
    def taille(avance):
        return round((math.hypot(P.bb_x - P.hip_x - avance, P.bb_z - P.hip_z) + P.crank) / P.leg_ratio / 1000, 2)
    def avance_pour(h):
        return round(P.bb_x - P.hip_x - math.sqrt((h * 1000 * P.leg_ratio - P.crank) ** 2 - (P.bb_z - P.hip_z) ** 2))
    rep["reglage_siege"] = {
        "course_mm": P.seat_travel,
        "taille_pilote_m_siege_en_butee_arriere": taille(0), "taille_pilote_m_siege_en_butee_avant": taille(P.seat_travel),
        "avance_du_siege_mm_par_taille": {f"{h:.2f} m": avance_pour(h) for h in (1.60, 1.70, 1.75, 1.80, 1.85)},
    }
    rep["ergonomie"] = {
        "pedalier_x_z_mm": [P.bb_x, P.bb_z],
        "hanche_a_axe_de_pedale_jambe_tendue_siege_recule_mm": round(math.hypot(P.bb_x - P.hip_x, P.bb_z - P.hip_z) + P.crank),
        "pedalier_au_dessus_de_l_assise_mm": round(P.bb_z - zs),
        "pedale_au_plus_bas_z_mm": round(P.bb_z - P.crank),
        "manivelle_au_plus_avant_x_mm": round(P.bb_x + P.crank),
    }
    rep["direction"] = {
        "braquage_vise_deg": P.steer_deg, "course_de_cable_mm": round(course, 1),
        "debattement_levier_deg": round(math.degrees(a_lev), 1), "course_poignee_mm": round(P.lever_len * math.sin(a_lev)),
    }
    json.dump(rep, open(os.path.join(outdir, "bilan.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps(rep, indent=1, ensure_ascii=False))

    if not apercu: return parts, hull
    # ------------------------------------------------------------ aperçu
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(16, 14))
    for k, (el, az) in enumerate(((20, -55), (4, -90))):
        ax = fig.add_subplot(2, 2, k + 1, projection='3d')
        for nm, s, col in parts:
            souple = any(m in nm for m in ("gaine", "fourreau", "cable"))     # tubes souples : maillage grossier, sinon l'aperçu rame
            vs, tr = s.tessellate(6.0, 0.9) if souple else s.tessellate(1.5)
            v = np.array([(p.x, p.y, p.z) for p in vs])
            ax.add_collection3d(Poly3DCollection(v[np.array(tr)], facecolor=col, edgecolor=(0, 0, 0, 0.15), linewidths=0.1))
        ax.set_xlim(-1750, 1850); ax.set_ylim(-1800, 1800); ax.set_zlim(-1300, 2300); ax.view_init(el, az); ax.set_axis_off()
        ax.set_box_aspect((1, 1, 1), zoom=1.9)
    ax = fig.add_subplot(2, 1, 2)
    for poly, lab, th in placed:
        ax.fill(*poly.exterior.xy, color='#d8b98a', ec='k', lw=0.5)
        for r in poly.interiors: ax.fill(*r.xy, color='white', ec='k', lw=0.5)
        ax.text(poly.bounds[0], poly.bounds[3] + 8, lab.split('  ')[0], fontsize=5)
    ax.set_aspect('equal'); ax.set_title('Gabarits de découpe (mm)'); ax.grid(alpha=0.2)
    fig.tight_layout(); fig.savefig(os.path.join(outdir, "phoebe-apercu.png"), dpi=110)
    return parts, hull

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    build(out)
