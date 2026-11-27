"""Zweite Prüfwege für Aussagen, die die App nicht selbst nachrechnet: die Schnitte zum Graphen mit 13 Knoten gegen alle stabilen Mengen und der eine
in den Messreihen offen gebliebene Fall mit einem zweiten Löser (SCIP aus OR-Tools). Beides ersetzt keinen exakten Beweis, dass kein Schnitt verletzt ist."""

import numpy as np
import pytest

import cvg_graphen as G
import cvg_messung as M
import cvg_trennung as T
import cvg_zeuge as Z
from cvg_graphen import maximale_cliquen
from cvg_katalog import multiplikatoren
from cvg_konflikt import gnp
from cvg_leiter import cliquenzeilen
from cvg_lp import loese
from cvg_schnitt import schnitt_aus


def _gilt_auf_allen_stabilen_mengen(alpha, beta) -> bool:
    return all(sum(a for v, a in enumerate(alpha) if m >> v & 1) <= beta for m in G.stabile_mengen(Z.ADJ))


def test_alle_gezeigten_schnitte_zum_13er_graphen_gelten_auf_jeder_stabilen_menge():
    assert len(G.stabile_mengen(Z.ADJ)) == 40
    for laenge in (9, 10, 11):
        for start in range(13):
            assert _gilt_auf_allen_stabilen_mengen(*Z.runde1_schnitt(laenge, start)), (laenge, start)
        for anzahl in range(1, 14):
            schnitt = Z.zweite_runde(laenge, anzahl)
            if schnitt is not None:
                assert _gilt_auf_allen_stabilen_mengen(*schnitt), (laenge, anzahl)


def test_der_offene_fall_der_messreihe_mit_scip_als_zweitem_loeser():
    """HiGHS meldet am letzten LP-Punkt: kein Schnitt der ersten Runde ist verletzt. SCIP rechnet dasselbe Trennprogramm (ohne Strafterm) und findet
    ebenfalls höchstens eine Verletzung bis zur Schwelle der App. Beides sind Gleitkommarechnungen."""
    pywraplp = pytest.importorskip("ortools.linear_solver.pywraplp")
    daten = M.lade()
    offen = [e for e in daten["raster"] + daten["gross"] if e["status"] == T.OFFEN_BEWIESEN]
    assert [(e["n"], e["seed"], e["gewichte"]) for e in offen] == [(16, 26207, "eins")]   # genau ein solcher Fall ist eingefroren
    e = offen[0]
    inst = gnp(e["n"], daten["p"], e["seed"])
    basis = cliquenzeilen(e["n"], maximale_cliquen(inst.adj))
    zeilen = list(basis) + [schnitt_aus(basis, multiplikatoren(s["u"])) for s in e["schnitte"]]
    wert, x, _ = loese([1] * e["n"], zeilen)
    assert wert == pytest.approx(5.25, abs=1e-6) and e["optimum"] == 5

    ziel, neben, rechts, ganz, oben = T.baue_programm(x, basis, 0.0)
    loeser = pywraplp.Solver.CreateSolver("SCIP")
    v = [(loeser.IntVar if ganz[j] else loeser.NumVar)(0, float(oben[j]) if np.isfinite(oben[j]) else loeser.infinity(), f"v{j}") for j in range(len(ziel))]
    for i in range(neben.shape[0]):
        loeser.Add(sum(float(neben[i, j]) * v[j] for j in range(len(v)) if neben[i, j]) <= float(rechts[i]))
    loeser.Minimize(sum(float(ziel[j]) * v[j] for j in range(len(v)) if ziel[j]))
    loeser.SetTimeLimit(120_000)
    parameter = pywraplp.MPSolverParameters()
    parameter.SetDoubleParam(parameter.RELATIVE_MIP_GAP, 0.0)
    assert loeser.Solve(parameter) == pywraplp.Solver.OPTIMAL
    assert -loeser.Objective().Value() <= T.VERLETZT_AB
    assert -loeser.Objective().BestBound() <= T.VERLETZT_AB
