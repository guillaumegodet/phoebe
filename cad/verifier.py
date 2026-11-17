#!/usr/bin/env python3
"""
Contrôle du modèle Phoebe après une modification :
  1. régénère les sorties (STEP, DXF, aperçu, bilan) ;
  2. vérifie que chaque solide est valide et relit le STEP ;
  3. cherche les collisions entre pièces (volume commun > seuil).

Usage : python3 verifier.py [dossier_de_sortie] [--module chemin/vers/phoebe_cad.py] [--seulement motif1,motif2]

--seulement limite le contrôle des collisions aux paires dont au moins un nom contient un des motifs
(le contrôle complet prend une dizaine de minutes, à cause des lisses).

Les contacts voulus (chaîne sur ses pignons, axe dans son palier...) sont listés
dans CONTACTS_VOULUS : une paire est ignorée si chaque nom contient un des deux motifs.
"""
import sys, os, itertools, importlib.util

SEUIL_MM3 = 60.0
CONTACTS_VOULUS = [
    ("chaine", "pignon"), ("chaine", "plateau"), ("chaine", "galet"), ("chaine", "couronne"), ("bout", "secteur"), ("bout", "poulie"), ("chaine", "chaine"),
    ("gaine", "gaine"), ("moyeu_vitesses_encombrement", "moyeu_vitesses_axe"),
]

def charger(chemin):
    spec = importlib.util.spec_from_file_location("phoebe_cad", chemin)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def voulu(a, b):
    return any((p in a and q in b) or (p in b and q in a) for p, q in CONTACTS_VOULUS)

def main():
    args = [a for a in sys.argv[1:]]
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phoebe_cad.py")
    if "--module" in args:
        i = args.index("--module"); chemin = args[i + 1]; del args[i:i + 2]
    seulement = None
    if "--seulement" in args:
        i = args.index("--seulement"); seulement = args[i + 1].split(","); del args[i:i + 2]
    out = args[0] if args else os.path.join(os.path.dirname(chemin), "out")
    os.makedirs(out, exist_ok=True)
    mod = charger(chemin)
    parts, hull = mod.build(out)
    import cadquery as cq

    print(f"\n--- {len(parts)} pièces")
    invalides = [nm for nm, s, _ in parts if not s.isValid()]
    print("solides invalides :", invalides or "aucun")
    noms = [nm for nm, _, _ in parts]
    doublons = sorted({n for n in noms if noms.count(n) > 1})
    print("noms en double :", doublons or "aucun")

    step = cq.importers.importStep(os.path.join(out, "phoebe-assemblage.step"))
    sol = step.solids().vals()
    print(f"STEP relu : {len(sol)} solides, {sum(1 for s in sol if not s.isValid())} invalide(s)")

    bbs = [s.BoundingBox() for _, s, _ in parts]
    def touche(a, b, m=0.0):
        return (a.xmin < b.xmax - m and b.xmin < a.xmax - m and a.ymin < b.ymax - m and b.ymin < a.ymax - m
                and a.zmin < b.zmax - m and b.zmin < a.zmax - m)
    col = []; n_test = 0
    for i, j in itertools.combinations(range(len(parts)), 2):
        if not touche(bbs[i], bbs[j], 0.05): continue
        a, b = parts[i], parts[j]
        if voulu(a[0], b[0]): continue
        if seulement and not any(m in a[0] or m in b[0] for m in seulement): continue
        n_test += 1
        try:
            v = a[1].intersect(b[1]).Volume()
        except Exception as e:
            print("  ? intersection impossible :", a[0], b[0], e); continue
        if v > SEUIL_MM3: col.append((v, a[0], b[0]))
    print(f"collisions : {n_test} paires testées, {len(col)} au-dessus de {SEUIL_MM3:g} mm3")
    for v, a, b in sorted(col, reverse=True): print(f"  {v:10.0f} mm3  {a}  x  {b}")
    return 1 if (invalides or col) else 0

if __name__ == "__main__":
    sys.exit(main())
