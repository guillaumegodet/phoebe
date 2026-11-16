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
from shapely.geometry import Polygon, LineString, box
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
    floor_over_U: float = 40.0  # idem couples porteurs
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

P = Params()

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
    return biggest(body.buffer(0)).simplify(0.2)

def stem_with_slots():
    g = STEM
    for x, kind in P.stations:
        if STEM.bounds[0] + 30 < x < STEM.bounds[2]:
            seg = STEM.intersection(LineString([(x, 0), (x, 2000)]))
            zm = (seg.bounds[1] + seg.bounds[3]) / 2
            g = g.difference(box(x - P.t_frame / 2 - P.tol, zm, x + P.t_frame / 2 + P.tol, 2000))
    return biggest(g.buffer(0)).simplify(0.2)

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
            pts = [V(*to3d(a, b)) for a, b in list(ring.coords)[:-1]]
            return cq.Wire.makePolygon(pts + [pts[0]])
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
    for th in sorted({f[1] for f in flats}):
        cx = 0.0; rowh = 0.0
        msp.add_text(f"CONTREPLAQUE {th:g} mm", dxfattribs={'layer': 'TEXTE', 'height': 40}).set_placement((0, cy - 70))
        for nm, t_, q, poly, eng in [f for f in flats if f[1] == th]:
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
    for nm, t_, q, poly, _ in flats: area[t_] = area.get(t_, 0) + q * poly.area / 1e6
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
    for k, (el, az) in enumerate(((22, -58), (8, -90))):
        ax = fig.add_subplot(2, 2, k + 1, projection='3d')
        for nm, s, col in parts:
            vs, tr = s.tessellate(1.5)
            v = np.array([(p.x, p.y, p.z) for p in vs])
            ax.add_collection3d(Poly3DCollection(v[np.array(tr)], facecolor=col, edgecolor=(0, 0, 0, 0.15), linewidths=0.1))
        ax.set_xlim(-1300, 1300); ax.set_ylim(-1300, 1300); ax.set_zlim(-1000, 1600); ax.view_init(el, az); ax.set_axis_off()
        ax.set_box_aspect((1, 1, 1), zoom=1.5)
    ax = fig.add_subplot(2, 1, 2)
    for poly, lab, th in placed:
        ax.fill(*poly.exterior.xy, color='#d8b98a', ec='k', lw=0.5)
        for r in poly.interiors: ax.fill(*r.xy, color='white', ec='k', lw=0.5)
        ax.text(poly.bounds[0], poly.bounds[3] + 8, lab.split('  ')[0], fontsize=5)
    ax.set_aspect('equal'); ax.set_title('Gabarits de découpe (mm)'); ax.grid(alpha=0.2)
    fig.tight_layout(); fig.savefig(os.path.join(outdir, "phoebe-apercu.png"), dpi=110)

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    build(out)
