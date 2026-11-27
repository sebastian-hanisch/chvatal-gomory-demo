"""Randfälle: leerer Graph, ein Knoten, zwei Knoten, vollständiger Graph, leere und gerade Knotenmengen, Grenzen inklusive."""

from fractions import Fraction as F

import pytest

import cvg_evaluation as E
import cvg_graphen as G
import cvg_leiter as L
import cvg_schnitt as S
import cvg_trennung as T
import cvg_zeuge as Z
from cvg_konflikt import adj_aus_kanten, gnp


def test_leerer_graph():
    assert G.groesstes_gewicht((), ()) == (0, 0)
    assert G.alle_ungeraden_kreise(()) == [] and G.induzierte_kreise((), 5) == []


@pytest.mark.parametrize("n", [1, 2])
def test_ein_und_zwei_knoten(n):
    adj = adj_aus_kanten(n, [(0, 1)] if n == 2 else [])
    cl = G.maximale_cliquen(adj)
    assert len(cl) == 1
    w = [1] * n
    s = T.suche_runde(w, L.cliquenzeilen(n, cl), 1, budget=5, je_programm=5)
    assert s.status == T.KEINE_LUECKE
    st = L.leiter(w, adj)
    assert st["familien"][0] == pytest.approx(1.0)


def test_vollstaendiger_graph_hat_keine_luecke():
    adj = adj_aus_kanten(7, [(i, j) for i in range(7) for j in range(i)])
    st = L.leiter([1] * 7, adj)
    assert st["cliquen"][0] == pytest.approx(1.0)


def test_isolierte_knoten_im_graphen():
    adj = adj_aus_kanten(5, [(0, 1), (1, 2), (0, 2)])
    assert L.leiter([1] * 5, adj)["cliquen"][0] == pytest.approx(3.0)


def test_leere_zeilenliste():
    assert S.cg_schnitt([], []) == ((), 0, (), F(0))


def test_gleiche_zeile_doppelt_in_der_suche(dreieck):
    _, zeilen = dreieck
    s = T.suche_runde([1, 1, 1], zeilen + [zeilen[0]], 1, budget=10, je_programm=5)
    assert s.status == T.GESCHLOSSEN


def test_leere_und_gerade_menge_beim_matching():
    m = E.ergebnis_matching("k5", ())
    assert m.alpha == (0,) * 10 and m.beta == 0 and m.gueltig
    m = E.ergebnis_matching("k5", (0, 1))
    assert m.beta == 1 and m.gueltig


def test_alle_knoten_in_u_beim_petersen_graphen():
    m = E.ergebnis_matching("petersen", range(10))
    assert m.beta == 5 and m.rand == () and m.gueltig


def test_grenzen_der_cliquen_und_runden():
    for k in (3, 9):
        for r in (0, 4):
            assert E.verdict_clique(k, r)[0] in ("info", "success")


def test_grenzen_der_verschiebungen():
    for laenge in Z.LAENGEN:
        for anzahl in (1, 13):
            assert E.verdict_zeuge(2, laenge, anzahl)[0] in ("info", "success")


@pytest.mark.parametrize("n, gewichte", [(8, "eins"), (16, "eins"), (16, "werte")])
def test_suche_an_den_reglergrenzen_hat_immer_einen_ausgang(n, gewichte):
    inst, w, cl, zeilen, s = E.suche_live(n, gewichte, 26200, 10.0)
    assert s.status in (T.KEINE_LUECKE, T.GESCHLOSSEN, T.OFFEN_BEWIESEN, T.NICHT_BESTIMMT)
    assert s.wert_ende >= s.optimum - 1e-6


def test_zwei_gleich_gute_werte_aendern_nichts_am_ausgang():
    inst = gnp(10, 400, 3)
    w = [5] * 10
    st = L.leiter(w, inst.adj)
    assert st["cliquen"][0] >= G.groesstes_gewicht(inst.adj, w)[0] - 1e-9
