"""Erzeugt cvg_katalog.json: die Sammlung für "Eine Runde über den Cliquen".

  klein    alle nichtperfekten Graphen mit 5 bis 7 Knoten (bis auf Isomorphie), je Facette der ganzzahligen Hülle jenseits von
           x >= 0 und den Cliquen: Werte über den Cliquen und mit allen ungeraden Kreisen (exakt aus den Ecken) und die
           Multiplikatoren eines Schnitts der ersten Runde, der die Facette liefert
  zwanzig  Instanzen mit 20 Knoten und Werten 1 bis 100, die nach Cliquen, ungeraden Kreisen, Antilöchern und Rädern offen bleiben,
           mit Schnitten der ersten Runde, die den LP-Wert auf das Optimum senken, und einem exakten Dualbeweis

Aufruf:  python tools/cvg_make_katalog.py            schreibt die Datei (wenige Minuten)
         python tools/cvg_make_katalog.py --check    rechnet die Auswahl neu und prüft jedes gespeicherte Zertifikat exakt
Die Multiplikatoren hängen am Löser (Linux kann andere finden); --check verlangt deshalb nicht dieselben, sondern gültige.
"""

import argparse
import itertools
import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

import cvg_dd as D  # noqa: E402
from cvg_familien import antiloecher  # noqa: E402
from cvg_graphen import (alle_ungeraden_kreise, groesstes_gewicht, ist_clique, maximale_cliquen, stabile_mengen, maske)  # noqa: E402
from cvg_katalog import DATEI, pruefe_klein, pruefe_zwanzig, instanz_zwanzig  # noqa: E402
from cvg_konflikt import adj_aus_kanten, kanten  # noqa: E402
from cvg_leiter import cliquenzeilen, lade_bis_fertig, schnitte_der_familien  # noqa: E402
from cvg_lp import dualbeweis, facetten_zertifikat, loese  # noqa: E402
from cvg_schnitt import bruch, wert, zeile  # noqa: E402
from cvg_trennung import GESCHLOSSEN, suche_runde  # noqa: E402

# Fünf Zellen: (Familie, Parameter in Promille, erster Zufalls-Seed); je 200 Instanzen
ZELLEN = (("gnp", 200, 28000), ("gnp", 400, 24200), ("gnp", 600, 28400), ("konflikt", 200, 28600), ("konflikt", 400, 28800))
JE_ZELLE = 200
HANDGRAPH = ((0, 1), (0, 4), (0, 5), (1, 2), (1, 5), (2, 3), (2, 5), (3, 4))


# ------------------------------------------------------------------------------------------------ Graphen bis auf Isomorphie

def _kantenliste(n):
    return [(i, j) for j in range(n) for i in range(j)]


def kanonisch(n: int, masken: np.ndarray) -> np.ndarray:
    """Je Kantenmaske (Bit = Kante in der Ordnung _kantenliste) die kleinste Maske über alle Umnummerierungen."""
    kanten_ = _kantenliste(n)
    nummer = {k: i for i, k in enumerate(kanten_)}
    perms = list(itertools.permutations(range(n)))
    gewichte = np.array([[1 << nummer[tuple(sorted((p[i], p[j])))] for p in perms] for i, j in kanten_], dtype=np.int64)
    bits_ = ((masken[:, None] >> np.arange(len(kanten_))) & 1).astype(np.int64)
    out = np.empty(len(masken), dtype=np.int64)
    for s in range(0, len(masken), 1000):
        out[s:s + 1000] = (bits_[s:s + 1000] @ gewichte).min(axis=1)
    return out


def graphen_bis_isomorphie(n_max: int) -> dict:
    """{n: sortierte Liste kanonischer Kantenmasken}: je Knoten mehr jede Nachbarschaft anhängen, dann kanonisch machen."""
    stufen = {1: [0]}
    for n in range(2, n_max + 1):
        alt = _kantenliste(n - 1)
        neu_index = {k: i for i, k in enumerate(_kantenliste(n))}
        kandidaten = []
        for m in stufen[n - 1]:
            basis = sum(1 << neu_index[k] for i, k in enumerate(alt) if m >> i & 1)
            for nachbarn in range(1 << (n - 1)):
                kandidaten.append(basis | sum(1 << neu_index[(v, n - 1)] for v in range(n - 1) if nachbarn >> v & 1))
        stufen[n] = sorted({int(v) for v in kanonisch(n, np.array(sorted(set(kandidaten)), dtype=np.int64))})
    return stufen


def adj_aus_maske(n: int, m: int) -> tuple:
    return adj_aus_kanten(n, [k for i, k in enumerate(_kantenliste(n)) if m >> i & 1])


# ------------------------------------------------------------------------------------------------ kleine Graphen

def facetten_jenseits_der_cliquen(adj) -> list:
    n = len(adj)
    punkte = [tuple(m >> v & 1 for v in range(n)) for m in stabile_mengen(adj)]
    h = D.huelle(punkte)
    if D.pruefe_huelle(punkte, h):
        raise AssertionError("Hülle nicht bestanden")
    out = []
    for a, b in h.facetten:
        if b <= 0:
            continue
        if b == 1 and set(a) <= {0, 1} and ist_clique(adj, maske(j for j, c in enumerate(a) if c)):
            continue
        out.append((a, b))
    return out


def eintrag_klein(adj, facetten) -> dict:
    n = len(adj)
    cliquen = maximale_cliquen(adj)
    basis = cliquenzeilen(n, cliquen)
    kreise = [zeile(n, [v for v in range(n) if m >> v & 1], (bin(m).count("1") - 1) // 2) for m in alle_ungeraden_kreise(adj)]
    ecken_c = D.ecken(n, basis)
    ecken_k = D.ecken(n, basis + kreise)
    out = []
    for a, b in facetten:
        z = facetten_zertifikat(a, b, cliquen)
        if z is None:
            raise AssertionError(f"Facette {a} <= {b} nicht in der ersten Runde: {kanten(adj)}")
        out.append({"a": list(a), "b": b,
                    "cliquen": bruch(max(wert(a, x) for x in ecken_c)),
                    "kreise": bruch(max(wert(a, x) for x in ecken_k)),
                    "u": {str(i): bruch(f) for i, f in sorted(z.items())}})
    return {"n": n, "kanten": [list(k) for k in kanten(adj)], "facetten": out}


def baue_klein() -> list:
    stufen = graphen_bis_isomorphie(7)
    hand = adj_aus_kanten(6, HANDGRAPH)
    hand_m = sum(1 << i for i, (a, b) in enumerate(_kantenliste(6)) if hand[a] >> b & 1)
    hand_kanonisch = int(kanonisch(6, np.array([hand_m], dtype=np.int64))[0])
    out = []
    for n in (5, 6, 7):
        for m in stufen[n]:
            adj = hand if (n == 6 and m == hand_kanonisch) else adj_aus_maske(n, m)
            facetten = facetten_jenseits_der_cliquen(adj)
            if facetten:
                e = eintrag_klein(adj, facetten)
                if adj == hand:
                    e["hand"] = True
                out.append(e)
    return out


# ------------------------------------------------------------------------------------------------ 20 Knoten

def baue_zwanzig(laut=print) -> list:
    out = []
    for familie, param, basis_seed in ZELLEN:
        offen = 0
        for k in range(JE_ZELLE):
            seed = basis_seed + k
            inst = instanz_zwanzig(familie, param, seed)
            adj, w = inst.adj, list(inst.werte)
            opt = groesstes_gewicht(adj, w)[0]
            cliquen = maximale_cliquen(adj)
            wert_c = loese(w, cliquenzeilen(len(adj), cliquen))[0]
            if wert_c <= opt + 1e-5:
                continue
            liste = antiloecher(adj)
            wert_f = lade_bis_fertig(w, adj, cliquen, ("kreis", "antiloch", "rad"), liste)[0]
            if wert_f <= opt + 1e-5:
                continue
            offen += 1
            out.append(eintrag_zwanzig(familie, param, seed, adj, w, opt, cliquen, wert_c, wert_f, liste))
        laut(f"  {familie} {param}: {JE_ZELLE} Instanzen ab Zufalls-Seed {basis_seed}, offen nach Rädern {offen}", flush=True)
    return out


def eintrag_zwanzig(familie, param, seed, adj, w, opt, cliquen, wert_c, wert_f, liste) -> dict:
    n = len(adj)
    basis = cliquenzeilen(n, cliquen)
    wert_k = lade_bis_fertig(w, adj, cliquen, ("kreis",))[0]
    s = suche_runde(w, basis, opt, budget=120.0, je_programm=30.0, max_schritte=800,
                    vorab=lambda x: schnitte_der_familien(adj, cliquen, basis, x, ("kreis", "antiloch", "rad"), liste))
    if s.status != GESCHLOSSEN:
        raise AssertionError(f"{familie} {param} Zufalls-Seed {seed}: Ausgang {s.status} {s.grund}, Wert {s.wert_ende}, Optimum {opt}")
    zeilen = basis + [(t.alpha, t.beta) for t in s.schritte]
    y = dualbeweis(w, zeilen, opt)
    if y is None:
        raise AssertionError(f"Zufalls-Seed {seed}: kein exakter Dualbeweis")
    benutzt = sorted(i - len(basis) for i in y if i >= len(basis))
    schnitte = [{"art": s.schritte[i].herkunft, "u": {str(j): bruch(f) for j, f in sorted(s.schritte[i].u.items())},
                 "y": bruch(y[len(basis) + i])} for i in benutzt]
    return {"familie": familie, "param": param, "seed": seed, "optimum": opt, "wert_cliquen": wert_c, "wert_kreise": wert_k,
            "wert_familien": wert_f, "schnitte": schnitte,
            "y_cliquen": {str(i): bruch(f) for i, f in sorted(y.items()) if i < len(basis)}}


# ------------------------------------------------------------------------------------------------ Hauptprogramm

def baue() -> dict:
    print("kleine Graphen ...", flush=True)
    klein = baue_klein()
    print(f"  {len(klein)} nichtperfekte Graphen, {sum(len(e['facetten']) for e in klein)} Facetten", flush=True)
    print("Instanzen mit 20 Knoten ...", flush=True)
    zwanzig = baue_zwanzig()
    print(f"  {len(zwanzig)} offene Instanzen", flush=True)
    return {"klein": klein, "zwanzig": zwanzig, "zellen": [list(z) for z in ZELLEN], "je_zelle": JE_ZELLE}


def check() -> int:
    daten = json.loads(DATEI.read_text(encoding="utf-8"))
    fehler = []
    stufen = graphen_bis_isomorphie(7)
    neu = []
    for n in (5, 6, 7):
        for m in stufen[n]:
            adj = adj_aus_maske(n, m)
            if facetten_jenseits_der_cliquen(adj):
                neu.append(int(kanonisch(n, np.array([m], dtype=np.int64))[0]) | n << 40)
    gespeichert = []
    for e in daten["klein"]:
        index = {k: i for i, k in enumerate(_kantenliste(e["n"]))}
        m = sum(1 << index[tuple(k)] for k in e["kanten"])
        gespeichert.append(int(kanonisch(e["n"], np.array([m], dtype=np.int64))[0]) | e["n"] << 40)
        adj = adj_aus_kanten(e["n"], e["kanten"])
        if sorted((tuple(f["a"]), f["b"]) for f in e["facetten"]) != sorted(facetten_jenseits_der_cliquen(adj)):
            fehler.append(f"Facetten weichen ab: {e['kanten']}")
    if sorted(neu) != sorted(gespeichert):
        fehler.append("Liste der nichtperfekten Graphen weicht ab")
    for e in daten["klein"]:
        fehler += pruefe_klein(e)
    offen = []
    for familie, param, basis_seed in ZELLEN:
        for k in range(JE_ZELLE):
            inst = instanz_zwanzig(familie, param, basis_seed + k)
            adj, w = inst.adj, list(inst.werte)
            opt = groesstes_gewicht(adj, w)[0]
            cliquen = maximale_cliquen(adj)
            if loese(w, cliquenzeilen(len(adj), cliquen))[0] <= opt + 1e-5:
                continue
            if lade_bis_fertig(w, adj, cliquen, ("kreis", "antiloch", "rad"))[0] > opt + 1e-5:
                offen.append((familie, param, basis_seed + k))
    if offen != [(e["familie"], e["param"], e["seed"]) for e in daten["zwanzig"]]:
        fehler.append(f"Liste der offenen Instanzen weicht ab: {len(offen)} neu gegen {len(daten['zwanzig'])} gespeichert")
    for e in daten["zwanzig"]:
        fehler += pruefe_zwanzig(e)
    for f in fehler[:20]:
        print("FEHLER:", f)
    print(f"--check: {len(daten['klein'])} kleine Graphen, {len(daten['zwanzig'])} Instanzen mit 20 Knoten, {len(fehler)} Fehler")
    return 1 if fehler else 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    if p.parse_args().check:
        return check()
    daten = baue()
    DATEI.write_bytes((json.dumps(daten, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
    print("geschrieben:", DATEI, DATEI.stat().st_size, "Byte")
    return check()


if __name__ == "__main__":
    sys.exit(main())
