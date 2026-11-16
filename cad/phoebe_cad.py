#!/usr/bin/env python3
"""
Phoebe - véhicule amphibie à foils, inspiré du trike open-source Moskitos.
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
    bb_x: float = 950.0         # repère d'axe de pédalier
    bb_z: float = 480.0
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
    plate_L: float = 190.0          # platine de mât (entraxe courant 165 x 90, à vérifier)
    plate_W: float = 110.0
    mast_len: float = 850.0
    mast_chord: float = 120.0
    mast_thk: float = 16.0
    wing_span: float = 370.0
    wing_chord: float = 180.0
    # arbre arrière et paliers à semelle vissés sur la face avant du couple
    shaft_d: float = 25.0
    shaft_z: float = 360.0
    brg_y: float = 265.0            # centre des paliers
    brg_h: float = 36.5             # hauteur d'axe du palier (type UCP205)
    brg_J: float = 105.0            # entraxe des vis du palier
    brg_bolt: float = 10.5
    arm_y: float = 425.0            # plan des bras de roue
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

P = Params()
HINGE_BOLTS = [(300, 315), (325, 360), (300, 405), (325, 438)]          # (y, z) dans le couple porteur des foils
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
        zf = beam_top(x) + (P.floor_over_U if kind == 'U' else P.floor_over)
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
    if abs(x - P.x_frame_foil) < 1: holes += [(sg * yy, zz, 8.5) for sg in (1, -1) for yy, zz in HINGE_BOLTS]
    if abs(x - P.x_frame_axle) < 1: holes += [(sg * (P.brg_y + d), P.shaft_z, P.brg_bolt) for sg in (1, -1) for d in (-P.brg_J / 2, P.brg_J / 2)]
    for yy, zz, d in holes: body = body.difference(Point(yy, zz).buffer(d / 2, 16))
    return biggest(body.buffer(0)).simplify(0.1)

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
# CONSTRUCTION
# ----------------------------------------------------------------------------
def build(outdir):
    import cadquery as cq
    V = cq.Vector
    def solid(poly, to3d, vec):
        def wire(ring):
            """contour -> fil : cercles vrais, courbes en splines, angles vifs conservés (STEP léger)"""
            c2 = np.array(ring.coords)[:-1]; n = len(c2)
            pts = [V(*to3d(a, b)) for a, b in c2]
            d0 = c2 - np.roll(c2, 1, axis=0); d1 = np.roll(c2, -1, axis=0) - c2
            turn = np.abs(np.degrees(np.arctan2(d0[:, 0] * d1[:, 1] - d0[:, 1] * d1[:, 0], (d0 * d1).sum(axis=1))))
            corners = [i for i in range(n) if turn[i] > 15]
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
        parts.append((nm, solid(band(BEAM_X0, BEAM_X1, f0, f1), lambda a, b: (a, -P.beam_w / 2, b), (0, P.beam_w, 0)), (0.62, 0.42, 0.24)))
    flats.append(("poutre_semelle_a_cintrer", tf, 2, box(0, 0, arc, P.beam_w), []))

    # étrave prolongée et gousset arrière
    stem = stem_with_slots()
    parts.append(("etrave_support_pedalier", solid(stem, lambda a, b: (a, -P.t_plate / 2, b), (0, P.t_plate, 0)), (0.54, 0.35, 0.19)))
    cross = [LineString([(P.bb_x - 15, P.bb_z), (P.bb_x + 15, P.bb_z)]), LineString([(P.bb_x, P.bb_z - 15), (P.bb_x, P.bb_z + 15)])]
    flats.append(("etrave_support_pedalier", P.t_plate, 1, stem, cross))
    parts.append(("gousset_arriere", solid(KNEE, lambda a, b: (a, -P.t_plate / 2, b), (0, P.t_plate, 0)), (0.54, 0.35, 0.19)))
    flats.append(("gousset_arriere", P.t_plate, 1, KNEE, []))

    # ======================================================== INTERFACES
    ALU = (0.72, 0.75, 0.78); STEEL = (0.35, 0.37, 0.4); CARB = (0.12, 0.13, 0.15); ENV = (0.25, 0.25, 0.27)
    def bx(x0, x1, y0, y1, z0, z1): return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
    def cyl(p0, p1, r):
        d = V(*p1) - V(*p0); return cq.Solid.makeCylinder(r, d.Length, V(*p0), d)
    def circ(a, b, d): return Point(a, b).buffer(d / 2, 16)

    # --- 1. charnières des foils avant : deux joues alu prennent le couple porteur en sandwich
    hx, hy, hz, tU = P.x_frame_foil, P.hinge_y, P.hinge_z, P.t_U
    cheek = unary_union([box(278, 295, 340, hz + 18), box(278, 464, hy + 38, hz + 21)])
    for yy, zz in HINGE_BOLTS: cheek = cheek.difference(circ(yy, zz, 8.5))
    cheek = cheek.difference(circ(hy, hz, 12.5)).difference(circ(hy - P.hinge_lock_r, hz, 10.5))
    flats.append(("joue_charniere_foil", P.t_cheek, 4, cheek, [], 'ALU'))
    def hinge_side(mirror, folded, tag):
        out = []
        for i, x0 in enumerate((hx - tU - P.t_cheek, hx + tU)):
            out.append((f"joue_charniere_{i + 1}_{tag}", solid(cheek, lambda a, b, x0=x0: (x0, a, b), (P.t_cheek, 0, 0)), ALU))
        out.append((f"axe_charniere_{tag}", cyl((hx - tU - 10, hy, hz), (hx + tU + 10, hy, hz), 6), STEEL))
        yl = hy - P.hinge_lock_r
        out.append((f"goupille_verrou_{tag}", cyl((hx - tU - 10, yl, hz), (hx + tU + 10, yl, hz), 5), STEEL))
        ym = hy + P.hinge_e; zt = hz - 21
        mov = [("chape_pivotante", bx(hx - tU + 1, hx + tU - 1, hy - 45, hy + 70, zt, hz + 13), ALU),
               ("platine_de_mat", bx(hx - P.plate_L / 2, hx + P.plate_L / 2, ym - P.plate_W / 2, ym + P.plate_W / 2, zt - 8, zt), ALU),
               ("mat_foil_encombrement", bx(hx - P.mast_chord / 2, hx + P.mast_chord / 2, ym - P.mast_thk / 2, ym + P.mast_thk / 2, zt - 8 - P.mast_len, zt - 8), CARB),
               ("aile_foil_encombrement", bx(hx - P.wing_chord / 2, hx + P.wing_chord / 2, ym, ym + P.wing_span, zt - 16 - P.mast_len, zt - P.mast_len), CARB)]
        for nm, sd, c in mov:
            if folded: sd = sd.rotate(V(0, hy, hz), V(1, hy, hz), 180)
            out.append((f"{nm}_{tag}", sd, c))
        return [(nm, sd.mirror("XZ") if mirror else sd, c) for nm, sd, c in out]
    parts += hinge_side(False, False, "babord_deploye") + hinge_side(True, True, "tribord_replie")

    # --- 2. arbre arrière : paliers à semelle vissés sur la face avant du couple porteur
    xf = P.x_frame_axle + tU; xa = xf + P.brg_h
    parts.append(("arbre_arriere", cyl((xa, -P.arm_y - 30, P.shaft_z), (xa, P.arm_y + 30, P.shaft_z), P.shaft_d / 2), STEEL))
    for sg, tag in ((1, "babord"), (-1, "tribord")):
        yc = sg * P.brg_y
        parts.append((f"palier_semelle_{tag}", bx(xf, xf + 15, yc - 70, yc + 70, P.shaft_z - 19, P.shaft_z + 19), ALU))
        parts.append((f"palier_corps_{tag}", cyl((xa, yc - 17, P.shaft_z), (xa, yc + 17, P.shaft_z), 32), ALU))
        parts.append((f"contre_plaque_palier_{tag}", bx(P.x_frame_axle - tU - 5, P.x_frame_axle - tU, yc - 75, yc + 75, P.shaft_z - 25, P.shaft_z + 25), ALU))
        parts.append((f"moyeu_bras_{tag}", cyl((xa, sg * (P.arm_y - 20), P.shaft_z), (xa, sg * (P.arm_y + 20), P.shaft_z), 22), STEEL))

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
        parts.append((f"rail_siege_{tag}", bx(-440, 110, sg * 50 - 10, sg * 50 + 10, zr, zr + 20), ALU))
    zs = zr + 20; sa = math.radians(P.seat_angle)
    pan = slab((P.seat_x, zs), (P.seat_x + 340, zs + 30), 9)
    back = slab((P.seat_x, zs), (P.seat_x - P.seat_back * math.cos(sa), zs + P.seat_back * math.sin(sa)), 9)
    for nm, pl, L in (("siege_assise", pan, 341.3), ("siege_dossier", back, P.seat_back)):
        parts.append((nm, solid(pl, lambda a_, b_: (a_, -P.seat_w / 2, b_), (0, P.seat_w, 0)), (0.86, 0.78, 0.6)))
        flats.append((nm, 9.0, 1, box(0, 0, L, P.seat_w), []))
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
        "tirant_eau_mm": {f"{m} kg": round(draft_for(m)) for m in (135, 165)},
        "contreplaque_m2_par_epaisseur": {f"{k:g} mm": round(v, 2) for k, v in sorted(area.items())},
        "masse_contreplaque_kg": round(m_ply, 1), "lisses_m": round(str_len / 1000, 1), "masse_lisses_kg": round(m_str, 1),
        "nb_pieces_3D": len(parts),
    }
    json.dump(rep, open(os.path.join(outdir, "bilan.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps(rep, indent=1, ensure_ascii=False))

    # ------------------------------------------------------------ aperçu
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(16, 14))
    for k, (el, az) in enumerate(((20, -55), (4, -90))):
        ax = fig.add_subplot(2, 2, k + 1, projection='3d')
        for nm, s, col in parts:
            vs, tr = s.tessellate(1.5)
            v = np.array([(p.x, p.y, p.z) for p in vs])
            ax.add_collection3d(Poly3DCollection(v[np.array(tr)], facecolor=col, edgecolor=(0, 0, 0, 0.15), linewidths=0.1))
        ax.set_xlim(-1400, 1900); ax.set_ylim(-1650, 1650); ax.set_zlim(-1150, 2150); ax.view_init(el, az); ax.set_axis_off()
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
