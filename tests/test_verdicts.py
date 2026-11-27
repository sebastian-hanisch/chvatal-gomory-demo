"""Verdikte an von Hand gesetzten Werten: jeder Zweig, die Schwellen und jede Zahl im Text."""

from dataclasses import replace
from fractions import Fraction as F

import pytest

import cvg_beispiele as B
import cvg_evaluation as E
import cvg_trennung as T


def abrunden_mit(u, alpha, beta, rechts, wert_ecke, ecke=(F(1, 2),) * 3):
    a = E.ergebnis_abrunden("dreieck_kanten", ("1/2",) * 3)
    return replace(a, u=u, alpha=alpha, beta=beta, rechts=rechts, wert_ecke=wert_ecke, ecke=ecke)


def test_abrunden_ohne_multiplikatoren():
    assert E.verdict_abrunden(abrunden_mit((F(0),) * 3, (0, 0, 0), 0, F(0), F(0))) == ("info", "Ohne Multiplikatoren entsteht 0 ≤ 0.")


def test_abrunden_trennt():
    art, text = E.verdict_abrunden(abrunden_mit((F(1, 2),) * 3, (1, 1, 1), 1, F(3, 2), F(3, 2)))
    assert art == "success" and "Aus drei Zeilen mit je ½" in text and "links steht 3/2, erlaubt ist 1" in text


def test_abrunden_trennt_mit_verschiedenen_gewichten_ohne_halbe():
    art, text = E.verdict_abrunden(abrunden_mit((F(2, 3), F(1, 2), F(0)), (1, 1, 0), 1, F(7, 6), F(3, 2)))
    assert art == "success" and "mit je ½" not in text and "Aus zwei Zeilen wird" in text


def test_abrunden_schwelle_gleich_ist_nicht_getrennt():
    art, text = E.verdict_abrunden(abrunden_mit((F(1, 2),) * 3, (1, 1, 1), 1, F(3, 2), F(1)))
    assert art == "info" and "trennt hier aber nicht" in text


def test_abrunden_alle_koeffizienten_null():
    art, text = E.verdict_abrunden(abrunden_mit((F(1, 4), F(0), F(0)), (0, 0, 0), 0, F(1, 4), F(0)))
    assert art == "info" and "Alle Koeffizienten werden auf 0 abgerundet: 0 ≤ 0" in text


def test_abrunden_rechte_seite_schon_ganzzahlig():
    art, text = E.verdict_abrunden(abrunden_mit((F(1, 2), F(1, 2), F(0)), (0, 1, 0), 1, F(1), F(1, 2)))
    assert art == "info" and "Die rechte Seite 1 war schon ganzzahlig" in text


def test_abrunden_mit_ganzzahliger_ecke_sagt_das():
    art, text = E.verdict_abrunden(abrunden_mit((F(1, 3), F(0), F(0)), (0, 1, 0), 0, F(1, 3), F(0), ecke=(F(1), F(0), F(0))))
    assert "(sie ist ganzzahlig)" in text


@pytest.mark.parametrize("U, art, teil", [((0, 1, 2, 3, 4), "success", "x(E[U]) ≤ 2"), ((0, 1, 2), "success", "x(E[U]) ≤ 1"),
                                          ((0, 1, 2, 3), "info", "|U| = 4 ist gerade"), ((2,), "info", "weniger als zwei Knoten"),
                                          ((), "info", "0 ≤ 0")])
def test_matching_zweige(U, art, teil):
    a, text = E.verdict_matching(E.ergebnis_matching("fuenfeck", U))
    assert a == art and teil in text


def test_matching_trennend_nennt_den_wert_und_nicht_trennend():
    art, text = E.verdict_matching(E.ergebnis_matching("fuenfeck", (0, 1, 2, 3, 4)))
    m = E.ergebnis_matching("fuenfeck", (0, 1, 2, 3, 4))
    assert (("verletzt sie: links steht" in text) == (m.wert_ecke > m.beta))
    _, text = E.verdict_matching(replace(m, wert_ecke=F(2)))
    assert "erfüllt sie schon" in text
    _, text = E.verdict_matching(replace(m, wert_ecke=F(5, 2)))
    assert "links steht 5/2" in text


def test_matching_bipartit_wird_gesagt():
    art, text = E.verdict_matching(E.ergebnis_matching("sechseck", (0, 1, 2)))
    assert "bipartit" in text and "Rang" not in text
    _, text = E.verdict_matching(E.ergebnis_matching("fuenfeck", (0, 1, 2)))
    assert "bipartit" not in text


@pytest.mark.parametrize("k, r, art, teil", [
    (6, 0, "info", "Ohne Runde ist x = 1/2 an jedem Knoten noch zulässig, die Summe ist 3 > 1. Erst nach 3 Runden"),
    (6, 2, "info", "Nach zwei Runden ist x = 1/5 an jedem Knoten noch zulässig, die Summe ist 6/5 > 1. Erst mit der nächsten Runde"),
    (6, 3, "success", "Nach drei Runden gilt x(K6) ≤ 1; gebraucht werden genau 3 Runden"),
    (3, 1, "success", "Nach einer Runde gilt x(K3) ≤ 1; gebraucht werden genau 1 Runde "),
    (5, 4, "success", "gebraucht werden genau 2 Runden"),
])
def test_clique_zweige(k, r, art, teil):
    a, text = E.verdict_clique(k, r)
    assert a == art and teil in text
    assert "Der Rang misst den Weg von der Startbeschreibung" in text


def test_klein_ohne_und_mit_wirkung():
    ohne = {"kreise_wert": F(2), "b": 2, "u": {0: F(1, 2)}}
    assert E.verdict_klein(ohne)[0] == "info" and "ändert den Wert nicht" in E.verdict_klein(ohne)[1]
    mit = {"kreise_wert": F(7, 3), "b": 2, "u": {i: F(1, 2) for i in range(5)}}
    art, text = E.verdict_klein(mit)
    assert art == "success" and "lassen **7/3** stehen" in text and "aus fünf Cliquenzeilen mit je ½ senkt den Wert auf **2**" in text
    gemischt = {"kreise_wert": F(7, 3), "b": 2, "u": {0: F(1, 3), 1: F(1, 2)}}
    assert "mit je ½" not in E.verdict_klein(gemischt)[1]


def test_zwanzig_ein_und_mehrere_schnitte():
    e = {"schnitte": [1], "wert_familien": 315.0, "optimum": 311}
    assert "lassen **315** stehen, das Optimum ist 311. Ein Schnitt der ersten Runde senkt den Wert auf **311**" in E.verdict_zwanzig(e)[1]
    e = {"schnitte": [1, 2, 3], "wert_familien": 461.0 + 2 / 3, "optimum": 458}
    assert "3 Schnitte der ersten Runde senken" in E.verdict_zwanzig(e)[1] and "1385/3" in E.verdict_zwanzig(e)[1]


def test_zeuge_runde_0_und_1():
    assert E.verdict_zeuge(0)[0] == "warning" and "13/4" in E.verdict_zeuge(0)[1]
    art, text = E.verdict_zeuge(1)
    assert art == "warning" and "13/6" in text and "26/11" in text and "Eine Runde genügt hier nicht" in text


@pytest.mark.parametrize("laenge, anzahl, art, teil", [
    (9, 1, "info", "fehlt noch mindestens ein Knoten"),
    (9, 12, "info", "8·x(V) ≤ 24, abgerundet x(V) ≤ 3"),
    (9, 13, "success", "Jeder Knoten kommt gleich oft vor: 9·x(V) ≤ 26, abgerundet **x(V) ≤ 2**"),
    (11, 7, "success", "Jeder Knoten kommt mindestens 5-mal vor: 5·x(V) ≤ 14"),
    (10, 9, "info", "6·x(V) ≤ 18, abgerundet x(V) ≤ 3"),
    (10, 10, "success", "7·x(V) ≤ 20"),
])
def test_zeuge_runde_2(laenge, anzahl, art, teil):
    a, text = E.verdict_zeuge(2, laenge, anzahl)
    assert a == art and teil in text, text


def test_suche_alle_ausgaenge():
    assert E.verdict_suche(T.KEINE_LUECKE, 0, 5, 5.0) == ("info", "Hier ist schon mit den Cliquen nichts zu tun: Der LP-Wert ist das Optimum 5.")
    art, text = E.verdict_suche(T.GESCHLOSSEN, 3, 5, 5.0)
    assert art == "success" and "fand 3 Schnitte" in text and "Die Lücke ist geschlossen" in text
    assert "fand einen Schnitt" in E.verdict_suche(T.GESCHLOSSEN, 1, 5, 5.0)[1]
    art, text = E.verdict_suche(T.OFFEN_BEWIESEN, 2, 5, 5.25)
    assert art == "warning" and "nach 2 Schnitten" in text and "Wert 21/4, Optimum 5" in text and "u ≤ 0,999" in text
    assert "ohne Schnitt" in E.verdict_suche(T.OFFEN_BEWIESEN, 0, 5, 5.5)[1]
    art, text = E.verdict_suche(T.NICHT_BESTIMMT, 1, 5, 5.5, "zeit")
    assert art == "warning" and "die Zeitgrenze ist erreicht" in text and "nur eine obere Schranke" in text
    assert "nicht „nichts verletzt“" in text and "Mit 1 Schnitt steht" in text
    assert "Höchstzahl der Schritte" in E.verdict_suche(T.NICHT_BESTIMMT, 200, 5, 5.5, "schritte")[1]
    assert "weder einen verletzten Schnitt" in E.verdict_suche(T.NICHT_BESTIMMT, 0, 5, 5.5, "loeser")[1]


def test_gross_nennt_die_zahlen_und_die_einschraenkung():
    art, text = E.verdict_gross({"nicht_bestimmt": 7, "graphen": 30, "n": 30})
    assert art == "info" and "In 7 von 30 Graphen mit 30 Knoten" in text and "kein Wert der Runde" in text


def test_kernfrage():
    art, text = E.verdict_kernfrage(3, 1)
    assert art == "info" and "Clique mit 6 Knoten aus den Kantenzeilen 3" in text and "(1 Facette" in text


def test_zahl_oder_bruch():
    assert E.zahl_oder_bruch(2.0) == "2" and E.zahl_oder_bruch(7 / 3) == "7/3" and E.zahl_oder_bruch(F(5, 2)) == "5/2"
    assert E.zahl_oder_bruch(2.0001234567) == "2,0001"


def test_alle_handfaelle_mit_loesung_haben_ein_verdikt():
    for name, fall in B.HANDFAELLE.items():
        a = E.ergebnis_abrunden(name, fall.loesung)
        assert a.gueltig, name
        assert E.verdict_abrunden(a)[0] in ("success", "info"), name
