"""Die eingefrorenen Messreihen "Was kostet das Finden?" (cvg_messungen.json), ihre exakte Nachprüfung und ihre Zusammenfassung."""

import json
from functools import lru_cache
from pathlib import Path
from statistics import median

from cvg_graphen import groesstes_gewicht, maximale_cliquen
from cvg_katalog import multiplikatoren
from cvg_konflikt import gnp
from cvg_leiter import cliquenzeilen
from cvg_lp import loese
from cvg_schnitt import schnitt_aus
from cvg_trennung import GESCHLOSSEN, KEINE_LUECKE, NICHT_BESTIMMT, OFFEN_BEWIESEN

DATEI = Path(__file__).resolve().parent / "cvg_messungen.json"
TOL = 1e-5


@lru_cache(maxsize=1)
def lade() -> dict:
    return json.loads(DATEI.read_text(encoding="utf-8"))


def pruefe_eintrag(e: dict, p: int) -> list:
    """Verstöße (leer = bestanden): Jeder gespeicherte Schnitt wird exakt aus den Multiplikatoren gerechnet; er ist damit gültig.
    Das LP mit Cliquen und diesen Schnitten gibt den gespeicherten Endwert; der Ausgang passt zu den Werten."""
    inst = gnp(e["n"], p, e["seed"])
    w = [1] * e["n"] if e["gewichte"] == "eins" else list(inst.werte)
    basis = cliquenzeilen(e["n"], maximale_cliquen(inst.adj))
    name = f"n={e['n']} Zufalls-Seed {e['seed']} {e['gewichte']}"
    fehler = []
    opt, menge = groesstes_gewicht(inst.adj, w)
    if opt != e["optimum"]:
        fehler.append(f"{name}: Optimum")
    if abs(loese(w, basis)[0] - e["wert_cliquen"]) > TOL:
        fehler.append(f"{name}: Cliquenwert")
    zeilen = list(basis) + [schnitt_aus(basis, multiplikatoren(s["u"])) for s in e["schnitte"]]
    punkt = tuple(menge >> v & 1 for v in range(e["n"]))
    if any(sum(c * x for c, x in zip(a, punkt)) > b for a, b in zeilen):
        fehler.append(f"{name}: ein Schnitt schneidet die optimale stabile Menge ab")
    ende = loese(w, zeilen)[0]
    if abs(ende - e["wert_ende"]) > TOL:
        fehler.append(f"{name}: Endwert {ende} gegen {e['wert_ende']}")
    geschlossen = e["wert_ende"] <= opt + TOL
    if (e["status"] in (GESCHLOSSEN, KEINE_LUECKE)) != geschlossen:
        fehler.append(f"{name}: Ausgang {e['status']} passt nicht zum Wert")
    return fehler


def zusammenfassung_raster(eintraege) -> list:
    """Je Zelle (n, Gewichte): Graphen mit Cliquenlücke, davon geschlossen, bewiesen offen, nicht bestimmt; Sekunden der Lückengraphen."""
    out = []
    zellen = sorted({(e["gewichte"] != "eins", e["n"]) for e in eintraege})
    for ist_wert, n in zellen:
        modus = "werte" if ist_wert else "eins"
        zelle = [e for e in eintraege if e["n"] == n and e["gewichte"] == modus]
        luecke = [e for e in zelle if e["status"] != KEINE_LUECKE]
        sek = [e["sekunden"] for e in luecke]
        out.append({"n": n, "gewichte": modus, "graphen": len(zelle), "mit_luecke": len(luecke),
                    "geschlossen": sum(e["status"] == GESCHLOSSEN for e in luecke),
                    "offen_bewiesen": sum(e["status"] == OFFEN_BEWIESEN for e in luecke),
                    "nicht_bestimmt": sum(e["status"] == NICHT_BESTIMMT for e in luecke),
                    "sekunden_median": median(sek) if sek else None, "sekunden_max": max(sek) if sek else None})
    return out


def zusammenfassung_gross(eintraege) -> list:
    """Je Größe: Zahl der Graphen mit Lücke nach Cliquen bzw. Kreisen und der Ausgang der Suche."""
    out = []
    for n in sorted({e["n"] for e in eintraege}):
        zelle = [e for e in eintraege if e["n"] == n]
        nach_kreisen = [e for e in zelle if e["wert_kreise"] > e["optimum"] + TOL]
        out.append({"n": n, "graphen": len(zelle),
                    "luecke_cliquen": sum(e["wert_cliquen"] > e["optimum"] + TOL for e in zelle),
                    "luecke_kreise": len(nach_kreisen),
                    "davon_geschlossen": sum(e["status"] == GESCHLOSSEN for e in nach_kreisen),
                    "offen_bewiesen": sum(e["status"] == OFFEN_BEWIESEN for e in zelle),
                    "nicht_bestimmt": sum(e["status"] == NICHT_BESTIMMT for e in zelle),
                    "sekunden_max": max(e["sekunden"] for e in zelle)})
    return out
