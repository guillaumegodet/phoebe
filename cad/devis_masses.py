#!/usr/bin/env python3
"""
Devis de masses de Phoebe : masse à vide, centre de gravité, charge sur les roues, assiette sur l'eau.

Les pièces dessinées sont pesées par leur volume (matériau déduit de leur couleur dans le modèle). Les pièces du
commerce et les encombrements reçoivent une masse estimée (table COMMERCE). Ce qui n'est pas modélisé est ajouté
à la main (table NON_MODELISE), avec une position supposée. Tout est à l'estime : aucune pièce n'a été pesée.

Usage : python3 devis_masses.py [dossier_de_sortie]      (écrit devis-masses.json)
"""
import sys, os, json, math, tempfile, importlib.util
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
RHO = {  # kg/m3, par couleur du modèle
    (0.54, 0.35, 0.19): 500, (0.72, 0.53, 0.31): 500, (0.81, 0.66, 0.45): 500, (0.62, 0.42, 0.24): 500, (0.86, 0.78, 0.6): 500,   # contreplaqué okoumé
    (0.85, 0.72, 0.5): 450,                                                  # épicéa
    (0.72, 0.75, 0.78): 2700, (0.35, 0.37, 0.4): 7850,                       # aluminium, acier
    (0.12, 0.13, 0.15): 1600, (0.1, 0.1, 0.11): 1100, (0.85, 0.38, 0.17): 1000, (0.25, 0.25, 0.27): 0,
}
# masse imposée (kg) pour les pièces du commerce et les encombrements : (motif du nom, masse)
COMMERCE = [
    ("roue_arriere_encombrement", 1.6), ("roue_avant_encombrement", 1.8), ("moyeu_arriere", 0.9), ("tambour_frein", 0.4),
    ("moyeu_vitesses_encombrement", 1.7), ("machine_arbre_encombrement", 1.0), ("moteur_immerge_encombrement", 3.0),
    ("helice_tuyere_encombrement", 0.6), ("palan_relevage_arriere_encombrement", 0.3), ("pedale_", 0.2),
    ("mat_foil_arriere_encombrement", 1.6), ("aile_foil_arriere_encombrement", 0.8),
    ("palier_corps", 0.6), ("palier_semelle", 0.2), ("fourreau_pivot_bras", 0.35),
    ("douille_direction", 0.2), ("pivot_fourche", 0.35), ("te_fourche", 0.25), ("fourreau_fourche", 0.3),
]
FACTEUR = [("chaine_", 0.52)]          # les chaînes sont dessinées comme des barres pleines
# (désignation, masse kg, x mm, z mm) : à l'estime, positions supposées
NON_MODELISE = [
    ("toile vernie de la coque et des ponts", 3.0, 0, 330), ("colle, visserie, vernis du bois", 2.5, -100, 300),
    ("chaîne primaire dans son fourreau", 0.3, -142, 180), ("variateurs et câblage", 1.5, -700, 300),
    ("câble du moteur immergé", 0.5, -1000, 400), ("capote solaire et ses arceaux", 4.0, -100, 1300),
    ("housses de foils", 0.8, 100, 900), ("phare, feu arrière, fanion", 0.6, 900, 600),
    ("garniture du siège", 0.5, -400, 400), ("câbles et petit accastillage", 0.8, -200, 400),
]
BATTERIE = 6.0          # kg, environ 1 kWh en 48 V
PILOTE = 80.0
SEGMENTS = {"tronc et tête": 0.58, "bras": 0.10, "cuisses": 0.20, "jambes et pieds": 0.12}

def charger():
    spec = importlib.util.spec_from_file_location("phoebe_cad", os.path.join(ICI, "phoebe_cad.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def categorie(nm, col):
    if RHO.get(col) in (500, 450) or "lisse" in nm: return "coque et squelette en bois"
    for motifs, cat in ((("foil", "sabot", "charniere", "chape", "platine_de_mat", "secteur", "sandow", "bout_", "taquet", "filoir", "tenon",
                          "safran", "femelot", "moteur_immerge", "helice", "palan", "garant", "poulie", "ferrure_porteuse_foils", "goupille_verrou"), "foils, ferrures et relevage"),
                        (("roue", "fourche", "direction", "bras", "palier", "arbre_arriere", "frein", "verrou", "traversee", "bride", "joint",
                          "levier", "butee", "palonnier", "cable", "gaine", "poignee", "eclisse", "ferrure_porteuse_arriere", "console", "douille"), "roues, direction, freins"),
                        (("pedal", "manivelle", "plateau", "chaine", "galet", "moyeu_vitesses", "pignon", "couronne", "machine", "platine_moyeu", "fourreau_brin"), "transmission et machine d'arbre"),
                        (("siege", "rail"), "siège")):
        if any(k in nm for k in motifs): return cat
    return "divers"

def pilote(P, avance):
    """centres de gravité des segments du pilote (x, z), siège avancé de `avance`"""
    hip = (P.hip_x + avance, P.hip_z); sa = math.radians(P.seat_angle); dos = (-math.cos(sa), math.sin(sa))
    H = 1850.0; cuisse, jambe = 0.245 * H, 0.246 * H + 60
    bb = (P.bb_x, P.bb_z); d = math.dist(hip, bb)
    a = (cuisse ** 2 - jambe ** 2 + d * d) / (2 * d); h = math.sqrt(max(cuisse ** 2 - a * a, 0.0))
    ux, uz = (bb[0] - hip[0]) / d, (bb[1] - hip[1]) / d
    genou = (hip[0] + a * ux - h * uz, hip[1] + a * uz + h * ux)
    if genou[1] < hip[1]: genou = (hip[0] + a * ux + h * uz, hip[1] + a * uz - h * ux)
    epaule = (hip[0] + 500 * dos[0], hip[1] + 500 * dos[1]); main = (P.lever_x, P.lever_z + P.lever_len - 40)
    mil = lambda p, q: ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
    return {"tronc et tête": (hip[0] + 330 * dos[0], hip[1] + 330 * dos[1]), "bras": mil(epaule, main),
            "cuisses": mil(hip, genou), "jambes et pieds": mil(genou, bb)}

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ICI, "out")
    m = charger(); P = m.P
    with tempfile.TemporaryDirectory() as tmp:
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()): parts, hull = m.build(tmp, apercu=False)
    brut = {nm: (s.Volume(), s.Center()) for nm, s, _ in parts}
    bb_rel = dict((nm, s) for nm, s, _ in parts)["roue_arriere_encombrement_babord_releve"].BoundingBox()
    lignes = []
    for nm, s, col in parts:
        vol, g = brut[nm]; col = tuple(round(c, 3) for c in col)
        masse = vol * RHO[col] / 1e9; src = "volume"
        for motif, k in FACTEUR:
            if nm.startswith(motif): masse *= k
        for motif, kg in COMMERCE:
            if motif in nm: masse, src = kg, "estimée"
        if "foil_L_encombrement" in nm: masse, src = P.foil_mass, "hypothèse du modèle"
        # configuration route : le bras bâbord, dessiné relevé, est pesé à la place du bras tribord
        x, z = g.x, g.z
        jumeau = nm.replace("_babord_releve", "_tribord_route")
        if jumeau != nm and jumeau in brut: x, z = brut[jumeau][1].x, brut[jumeau][1].z
        lignes.append((nm, categorie(nm, col), masse, x, z, src))
    for nm, kg, x, z in NON_MODELISE: lignes.append((nm, "non modélisé (à l'estime)", kg, x, z, "estimée"))

    def somme(L):
        M = sum(l[2] for l in L)
        return M, sum(l[2] * l[3] for l in L) / M, sum(l[2] * l[4] for l in L) / M
    cats = {}
    for l in lignes: cats.setdefault(l[1], []).append(l)
    x_av = P.axle_x; x_ar = brut["roue_arriere_encombrement_tribord_route"][1].x

    def cas(avance, x_bat):
        L = list(lignes) + [("batterie", "", BATTERIE, x_bat, 300, "")]
        Mv, xv, zv = somme(L)
        seg = pilote(P, avance)
        L += [(k, "", PILOTE * f, seg[k][0], seg[k][1], "") for k, f in SEGMENTS.items()]
        Mt, xt, zt = somme(L); xr = x_ar
        part_ar = (x_av - xt) / (x_av - xr)
        return {"masse_a_vide_kg": round(Mv, 1), "cg_a_vide_x_mm": round(xv), "masse_totale_kg": round(Mt, 1), "cg_x_mm": round(xt), "cg_z_mm": round(zt),
                "roues_arriere_x_mm": round(xr), "part_sur_les_roues_arriere_pct": round(100 * part_ar, 1),
                "charge_roue_avant_kg": round(Mt * (1 - part_ar), 1),
                "cg_devant_l_axe_arriere_mm": round(xt - xr),
                "pente_de_cabrage_deg": round(math.degrees(math.atan2(xt - xr, zt)), 1) if xt > xr else 0.0,
                "part_sur_les_foils_avant_pct": round(100 * (xt - P.rud_Lx) / (P.x_frame_foil - P.rud_Lx), 1)}

    seg0 = pilote(P, 0.0)
    xp = sum(f * seg0[k][0] for k, f in SEGMENTS.items())
    # assiette sur l'eau : flottaison inclinée qui met le centre de carène à l'aplomb du centre de gravité
    from shapely.geometry import box
    trap = getattr(np, "trapezoid", None) or np.trapz
    ts = np.linspace(-1, P.t_bow, 81); xs = ts * P.HL; polys = [m.hull_poly(t, deck=False) for t in ts]
    def carene(z0, pente):                       # volume (L) et abscisse du centre de carène ; pente > 0 : l'arrière s'enfonce
        A = np.array([q.intersection(box(-1000, 0, 1000, z0 - pente * x)).area for q, x in zip(polys, xs)])
        V = float(trap(A, xs)); return V / 1e6, float(trap(A * xs, xs)) / V
    def equilibre(masse, xg):
        def z_pour(pente):
            lo, hi = P.z_keel, P.z_gun + 100
            for _ in range(26):
                mid = (lo + hi) / 2
                if carene(mid, pente)[0] < masse: lo = mid
                else: hi = mid
            return (lo + hi) / 2
        a, b = -0.15, 0.15
        for _ in range(16):
            c = (a + b) / 2
            if carene(z_pour(c), c)[1] > xg: a = c
            else: b = c
        pente = (a + b) / 2; z0 = z_pour(pente); xt = P.x_transom
        return {"assiette_deg_arriere_enfonce": round(math.degrees(math.atan(pente)), 1),
                "franc_bord_au_tableau_mm": round(m.zg(xt / P.HL) - (z0 - pente * xt)),
                "tirant_d_eau_au_tableau_mm": round(z0 - pente * xt - m.zk(xt / P.HL)),
                "tirant_d_eau_a_l_etrave_mm": round(max(0.0, z0 - pente * 1200 - m.zk(1200 / P.HL)))}
    c0 = cas(0, -750); c1 = cas(0, 800)
    lcb = carene(P.z_keel + m.draft_for(c0["masse_totale_kg"]), 0.0)[1]
    rep = {
        "avertissement": "masses à l'estime, aucune pièce pesée ; pilote de 80 kg et 1,85 m ; batterie de 6 kg",
        "par_categorie_kg": {c: round(somme(L)[0], 1) for c, L in sorted(cats.items())},
        "pieces_les_plus_lourdes_kg": {l[0]: round(l[2], 2) for l in sorted(lignes, key=lambda l: -l[2])[:14]},
        "pilote_cg_x_mm_siege_recule": round(xp), "empattement_mm": round(x_av - x_ar),
        "roue_arriere_relevee": {"bas_z_mm": round(bb_rel.zmin), "haut_z_mm": round(bb_rel.zmax), "arriere_x_mm": round(bb_rel.xmin),
                                 "au_dessus_de_la_flottaison_mm": {f"{k} kg": round(bb_rel.zmin - P.z_keel - m.draft_for(k)) for k in (165, 195)}}, "roue_avant_x_mm": round(x_av), "centre_de_carene_a_plat_x_mm": round(lcb),
        "sur_l_eau": {"batterie derrière le siège": equilibre(c0["masse_totale_kg"], c0["cg_x_mm"]),
                      "batterie à l'avant du cockpit": equilibre(c1["masse_totale_kg"], c1["cg_x_mm"])},
        "cas": {
            "batterie derrière le siège (x = -750)": cas(0, -750),
            "batterie à l'avant du cockpit (x = +800)": cas(0, 800),
            "pilote de 1,60 m (siège avancé de 150), batterie derrière le siège": cas(150, -750),
        },
    }
    json.dump(rep, open(os.path.join(out, "devis-masses.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(rep, indent=1, ensure_ascii=False))

if __name__ == "__main__":
    main()
