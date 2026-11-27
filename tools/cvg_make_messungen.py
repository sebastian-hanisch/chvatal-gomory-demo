"""Erzeugt cvg_messungen.json: Was kostet das Finden? Alle Messungen mit scipy-HiGHS und SplitMix64-Instanzen, Gewichte wie angegeben.

  raster   G(n; 0,4), n = 8, 12, 16, 20, je 40 Graphen (Zufalls-Seeds 26200 bis 26239), Gewichte alle 1 und Werte 1 bis 100:
           Suche ab den Cliquenzeilen ohne vorab geladene Kreise, Budget je Graph und je Programm wie in BUDGET_RASTER
  gross    G(20; 0,4), 100 Graphen, und G(30; 0,4), 30 Graphen (Gewichte alle 1, Zufalls-Seeds ab 26100): Cliquen, ungerade
           Kreise, dann die Suche mit vorab geladenen Kreisschnitten, Budget wie in BUDGET_GROSS

Zeiten, Zahl der Schnitte und der Ausgang "nicht bestimmt" hängen am Löser, am Budget und am Rechner; sie sind nicht bitgleich
wiederholbar. Gespeichert werden deshalb alle Schnitte als Multiplikatoren.

Aufruf:  python tools/cvg_make_messungen.py            schreibt die Datei (mehr als zehn Minuten)
         python tools/cvg_make_messungen.py --check    rechnet jeden gespeicherten Schnitt exakt nach und prüft die LP-Werte
"""

import argparse
import json
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cvg_graphen import groesstes_gewicht, maximale_cliquen  # noqa: E402
from cvg_konflikt import gnp  # noqa: E402
from cvg_leiter import cliquenzeilen, lade_bis_fertig, schnitte_der_familien  # noqa: E402
from cvg_lp import loese  # noqa: E402
from cvg_messung import DATEI, pruefe_eintrag  # noqa: E402
from cvg_schnitt import bruch  # noqa: E402
from cvg_trennung import suche_runde  # noqa: E402

P_DICHTE = 400
RASTER_N = (8, 12, 16, 20)
RASTER_SEEDS = tuple(range(26200, 26240))
BUDGET_RASTER = (20.0, 10.0)          # Sekunden je Graph, je Programm
GROSS = ((20, 100), (30, 30))         # (Knoten, Zahl der Graphen)
GROSS_BASIS = 26100
BUDGET_GROSS = (25.0, 8.0)


def eintrag(n: int, seed: int, werte_modus: str, budget, vorab_kreise: bool) -> dict:
    inst = gnp(n, P_DICHTE, seed)
    w = [1] * n if werte_modus == "eins" else list(inst.werte)
    cliquen = maximale_cliquen(inst.adj)
    basis = cliquenzeilen(n, cliquen)
    opt = groesstes_gewicht(inst.adj, w)[0]
    out = {"n": n, "seed": seed, "gewichte": werte_modus, "optimum": opt, "wert_cliquen": loese(w, basis)[0]}
    vorab = None
    if vorab_kreise:
        out["wert_kreise"] = lade_bis_fertig(w, inst.adj, cliquen, ("kreis",))[0]
        vorab = lambda x: schnitte_der_familien(inst.adj, cliquen, basis, x, ("kreis",))  # noqa: E731
    s = suche_runde(w, basis, opt, budget=budget[0], je_programm=budget[1], vorab=vorab)
    out.update({"status": s.status, "grund": s.grund, "wert_ende": s.wert_ende, "sekunden": round(s.sekunden, 2),
                "schnitte": [{"art": t.herkunft, "u": {str(i): bruch(f) for i, f in sorted(t.u.items())}} for t in s.schritte]})
    return out


def baue(laut=print) -> dict:
    raster, gross = [], []
    for modus in ("eins", "werte"):
        for n in RASTER_N:
            t0 = time.time()
            teil = [eintrag(n, s, modus, BUDGET_RASTER, False) for s in RASTER_SEEDS]
            raster += teil
            laut(f"raster n={n} {modus}: {time.time() - t0:.0f} s", flush=True)
    for n, anzahl in GROSS:
        t0 = time.time()
        for k in range(anzahl):
            gross.append(eintrag(n, GROSS_BASIS + k, "eins", BUDGET_GROSS, True))
            if k % 10 == 9:
                laut(f"gross n={n}: {k + 1} Graphen, {time.time() - t0:.0f} s", flush=True)
    import scipy

    return {"p": P_DICHTE, "budget_raster": list(BUDGET_RASTER), "budget_gross": list(BUDGET_GROSS),
            "umgebung": {"python": platform.python_version(), "scipy": scipy.__version__, "system": platform.system()},
            "raster": raster, "gross": gross}


def check() -> int:
    daten = json.loads(DATEI.read_text(encoding="utf-8"))
    fehler = []
    for teil in ("raster", "gross"):
        for e in daten[teil]:
            fehler += pruefe_eintrag(e, daten["p"])
    erwartet = len(RASTER_N) * len(RASTER_SEEDS) * 2, sum(a for _, a in GROSS)
    if (len(daten["raster"]), len(daten["gross"])) != erwartet:
        fehler.append("Zahl der Einträge weicht ab")
    for f in fehler[:20]:
        print("FEHLER:", f)
    print(f"--check: {len(daten['raster'])} + {len(daten['gross'])} Einträge, {len(fehler)} Fehler")
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
