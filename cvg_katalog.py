"""Die eingefrorene Sammlung (cvg_katalog.json, erzeugt von tools/cvg_make_katalog.py) und die exakte Prüfung ihrer Zertifikate.

Gespeichert sind nur Multiplikatoren und Dualwerte als Brüche. Jeder Schnitt wird beim Anzeigen mit Brüchen neu gerechnet.
"""

import json
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

from cvg_graphen import groesstes_gewicht, maximale_cliquen
from cvg_konflikt import adj_aus_kanten, build, gnp
from cvg_leiter import cliquenzeilen, lade_bis_fertig
from cvg_lp import loese, pruefe_dualbeweis
from cvg_schnitt import schnitt_aus, wert

DATEI = Path(__file__).resolve().parent / "cvg_katalog.json"
LAENGE = 10          # L der Konfliktgraphen


@lru_cache(maxsize=1)
def lade() -> dict:
    return json.loads(DATEI.read_text(encoding="utf-8"))


def instanz_zwanzig(familie: str, param: int, seed: int):
    """G(20; p) oder der Konfliktgraph K(20; 10; q); p bzw. q in Promille."""
    return gnp(20, param, seed) if familie == "gnp" else build(20, LAENGE, param, seed)


def familien_name(familie: str, param: int) -> str:
    p = f"{param / 1000:.1f}".replace(".", ",")
    return f"G(20; {p})" if familie == "gnp" else f"K(20; {LAENGE}; {param})"


def multiplikatoren(u: dict) -> dict:
    return {int(i): Fraction(f) for i, f in u.items()}


def schnitt_klein(eintrag: dict, f: int) -> dict:
    """Zur f-ten Facette eines kleinen Graphen: Cliquen, Zeilen, Multiplikatoren und der exakt gerechnete Schnitt."""
    adj = adj_aus_kanten(eintrag["n"], eintrag["kanten"])
    cliquen = maximale_cliquen(adj)
    zeilen = cliquenzeilen(eintrag["n"], cliquen)
    facette = eintrag["facetten"][f]
    u = multiplikatoren(facette["u"])
    alpha, beta = schnitt_aus(zeilen, u)
    return {"adj": adj, "cliquen": cliquen, "zeilen": zeilen, "u": u, "alpha": alpha, "beta": beta,
            "a": tuple(facette["a"]), "b": facette["b"], "cliquen_wert": Fraction(facette["cliquen"]),
            "kreise_wert": Fraction(facette["kreise"])}


def pruefe_klein(eintrag: dict) -> list:
    """Verstöße (leer = bestanden): der gespeicherte Schnitt ist mindestens so stark wie die Facette."""
    fehler = []
    for f in range(len(eintrag["facetten"])):
        s = schnitt_klein(eintrag, f)
        if s["beta"] > s["b"] or any(x < y for x, y in zip(s["alpha"], s["a"])):
            fehler.append(f"Schnitt zu schwach: {eintrag['kanten']} Facette {f}")
        if not Fraction(s["b"]) <= s["kreise_wert"] <= s["cliquen_wert"]:
            fehler.append(f"Werte nicht geordnet: {eintrag['kanten']} Facette {f}")
    return fehler


def schnitte_zwanzig(eintrag: dict) -> dict:
    """Instanz, Cliquen, die exakt gerechneten Schnitte und der Dualbeweis y·b <= Optimum."""
    inst = instanz_zwanzig(eintrag["familie"], eintrag["param"], eintrag["seed"])
    n = len(inst.adj)
    cliquen = maximale_cliquen(inst.adj)
    basis = cliquenzeilen(n, cliquen)
    schnitte = []
    for s in eintrag["schnitte"]:
        u = multiplikatoren(s["u"])
        alpha, beta = schnitt_aus(basis, u)
        schnitte.append({"art": s["art"], "u": u, "alpha": alpha, "beta": beta, "y": Fraction(s["y"])})
    zeilen = basis + [(s["alpha"], s["beta"]) for s in schnitte]
    y = multiplikatoren(eintrag["y_cliquen"])
    y.update({len(basis) + i: s["y"] for i, s in enumerate(schnitte)})
    return {"instanz": inst, "cliquen": cliquen, "basis": basis, "schnitte": schnitte, "zeilen": zeilen, "y": y}


def pruefe_zwanzig(eintrag: dict, mit_lp: bool = True) -> list:
    """Verstöße (leer = bestanden): exakt beweist y über Cliquen und Schnitten w·x <= Optimum; das Optimum wird erreicht."""
    fehler = []
    d = schnitte_zwanzig(eintrag)
    w = list(d["instanz"].werte)
    opt, menge = groesstes_gewicht(d["instanz"].adj, w)
    name = f"{eintrag['familie']} {eintrag['param']} Zufalls-Seed {eintrag['seed']}"
    if opt != eintrag["optimum"]:
        fehler.append(f"{name}: Optimum {opt} gegen {eintrag['optimum']}")
    try:
        if pruefe_dualbeweis(w, d["zeilen"], d["y"]) > opt:
            fehler.append(f"{name}: Dualbeweis erreicht das Optimum nicht")
    except ValueError as e:
        fehler.append(f"{name}: {e}")
    punkt = tuple(menge >> v & 1 for v in range(len(w)))
    if any(wert(a, punkt) > b for a, b in d["zeilen"]):
        fehler.append(f"{name}: die optimale stabile Menge verletzt eine Zeile")
    if mit_lp:
        n = len(w)
        werte = {"wert_cliquen": loese(w, d["basis"])[0],
                 "wert_kreise": lade_bis_fertig(w, d["instanz"].adj, d["cliquen"], ("kreis",))[0],
                 "wert_familien": lade_bis_fertig(w, d["instanz"].adj, d["cliquen"], ("kreis", "antiloch", "rad"))[0]}
        for k, v in werte.items():
            if abs(v - eintrag[k]) > 1e-5:
                fehler.append(f"{name}: {k} {v} gegen {eintrag[k]} (n = {n})")
    return fehler
