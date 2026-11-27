"""Eigenschaften, die für den Chvátal-Gomory-Schnitt gelten müssen, ohne das richtige Ergebnis zu kennen."""

from fractions import Fraction as F
from math import floor

import pytest

import cvg_graphen as G
import cvg_leiter as L
import cvg_lp as LP
import cvg_schnitt as S
import cvg_trennung as T
from cvg_konflikt import adj_aus_kanten, build, gnp, kanten
from cvg_rng import SplitMix64


def zufallsgewichte(rng, m, anzahl):
    nenner = 2 + rng.below(6)
    u = [F(0)] * m
    for _ in range(anzahl):
        u[rng.below(m)] += F(1 + rng.below(2 * nenner - 1), nenner)
    return u


@pytest.mark.parametrize("seed", range(25))
def test_jede_ganzzahlige_loesung_uebersteht_jeden_schnitt(seed):
    inst = build(8, 10, 300, seed)
    cl = G.maximale_cliquen(inst.adj)
    zeilen = L.cliquenzeilen(8, cl)
    rng = SplitMix64(500 + seed)
    punkte = [tuple(m >> v & 1 for v in range(8)) for m in G.stabile_mengen(inst.adj)]
    for _ in range(40):
        alpha, beta, _, _ = S.cg_schnitt(zeilen, zufallsgewichte(rng, len(zeilen), 1 + rng.below(6)))
        assert S.ist_gueltig(alpha, beta, punkte)


@pytest.mark.parametrize("seed", range(25))
def test_der_ganzzahlige_anteil_der_gewichte_ist_ueberfluessig(seed):
    """cut(u) folgt aus cut(Nachkommaanteil von u) und den Zeilen selbst: gilt die zweite Ungleichung in x aus dem Polytop, so die erste."""
    inst = gnp(6, 500, 40 + seed)
    zeilen = L.cliquenzeilen(6, G.maximale_cliquen(inst.adj))
    rng = SplitMix64(900 + seed)
    u = zufallsgewichte(rng, len(zeilen), 5)
    teil = [v - floor(v) for v in u]
    a1, b1, _, _ = S.cg_schnitt(zeilen, u)
    a2, b2, _, _ = S.cg_schnitt(zeilen, teil)
    ganz = [int(floor(v)) for v in u]
    assert a1 == tuple(x + sum(g * z[0][j] for g, z in zip(ganz, zeilen)) for j, x in enumerate(a2))
    assert b1 == b2 + sum(g * z[1] for g, z in zip(ganz, zeilen))


@pytest.mark.parametrize("seed", range(20))
def test_umnummerieren_aendert_die_werte_nicht(seed):
    inst = gnp(11, 400, 70 + seed)
    rng = SplitMix64(seed)
    perm = list(range(11))
    rng.shuffle(perm)
    neu = adj_aus_kanten(11, [(perm[a], perm[b]) for a, b in kanten(inst.adj)])
    w = list(inst.werte)
    wn = [0] * 11
    for v in range(11):
        wn[perm[v]] = w[v]
    alt, nach = L.leiter(w, inst.adj), L.leiter(wn, neu)
    for stufe in ("cliquen", "kreise", "familien"):
        assert alt[stufe][0] == pytest.approx(nach[stufe][0], abs=1e-6)
    assert G.groesstes_gewicht(inst.adj, w)[0] == G.groesstes_gewicht(neu, wn)[0]


@pytest.mark.parametrize("seed", range(20))
def test_die_leiter_faellt_und_endet_nicht_unter_dem_optimum(seed):
    inst = build(12, 10, 300, 90 + seed)
    w = list(inst.werte)
    st = L.leiter(w, inst.adj)
    opt = G.groesstes_gewicht(inst.adj, w)[0]
    assert st["cliquen"][0] + 1e-7 >= st["kreise"][0] >= st["familien"][0] - 1e-7 and st["familien"][0] >= opt - 1e-7


def test_mehr_startzeilen_verschlechtern_den_wert_der_runde_nicht():
    """Cliquenzeilen schärfen die Kantenzeilen: Der Wert der ersten Runde über den Cliquen ist höchstens der über den Kanten."""
    for seed in range(8):
        inst = gnp(9, 500, 130 + seed)
        w = [1] * 9
        opt = G.groesstes_gewicht(inst.adj, w)[0]
        kz = [S.zeile(9, k) for k in kanten(inst.adj)] + [S.zeile(9, [v]) for v in range(9) if not inst.adj[v]]
        cz = L.cliquenzeilen(9, G.maximale_cliquen(inst.adj))
        ek = T.suche_runde(w, kz, opt, budget=30.0, je_programm=10.0)
        ec = T.suche_runde(w, cz, opt, budget=30.0, je_programm=10.0)
        if T.NICHT_BESTIMMT in (ek.status, ec.status):
            continue
        assert ec.wert_ende <= ek.wert_ende + 1e-5, seed


def test_monotonie_des_lp_mit_zusaetzlichen_zeilen():
    inst = gnp(10, 400, 5)
    cl = G.maximale_cliquen(inst.adj)
    z = L.cliquenzeilen(10, cl)
    w = list(inst.werte)
    assert LP.loese(w, z + [S.zeile(10, range(10), 3)])[0] <= LP.loese(w, z)[0] + 1e-9


def test_gleicher_zufalls_seed_gleiche_instanz_in_neuem_prozess():
    """Zweiter Prozess mit anderer Hash-Verteilung: dieselben Cliquen und Werte der Leiter."""
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    code = ("import sys, json; sys.path.insert(0, {!r}); import cvg_leiter as L, cvg_graphen as G; from cvg_konflikt import gnp; "
            "i = gnp(12, 400, 3); st = L.leiter(list(i.werte), i.adj); "
            "print(json.dumps([G.maximale_cliquen(i.adj), round(st['cliquen'][0], 6), round(st['familien'][0], 6)]))")
    root = str(Path(__file__).resolve().parent.parent)
    aus = []
    for h in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=h)
        aus.append(subprocess.run([sys.executable, "-c", code.format(root)], capture_output=True, text=True, env=env, check=True,
                                  stdin=subprocess.DEVNULL).stdout.strip().splitlines()[-1])
    assert json.loads(aus[0]) == json.loads(aus[1])
