"""Jede Zahl der README, auf dem Weg nachgerechnet, den die App benutzt. Löser- und rechnerabhängige Zahlen (Schnittzahlen, Zeiten,
"nicht bestimmt") werden nur gegen die eingefrorene Datei gehalten, nie neu gemessen."""

import itertools
import re
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

import pytest

import cvg_evaluation as E
import cvg_graphen as G
import cvg_katalog as K
import cvg_messung as M
import cvg_schnitt as S
import cvg_zeuge as Z
from cvg_konflikt import adj_aus_kanten, kanten

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")


def steht(text):
    assert " ".join(text.split()) in " ".join(README.split()), text


def test_kleine_sammlung_zahlen():
    daten = K.lade()["klein"]
    facetten = [f for e in daten for f in e["facetten"]]
    durch_kreise = [f for f in facetten if F(f["kreise"]) == f["b"]]
    ganz = [e for e in daten if all(F(f["kreise"]) == f["b"] for f in e["facetten"])]
    assert (len(daten), len(facetten), len(durch_kreise), len(ganz)) == (147, 200, 103, 68)
    assert Counter(e["n"] for e in daten) == {5: 1, 6: 8, 7: 138}
    steht("Von 200 Facetten jenseits der Cliquen liefern die ungeraden Kreise dazu 103")
    steht("68 von 147 Graphen")
    # eine Runde: jede Facette hat ein exaktes Zertifikat
    assert all(K.pruefe_klein(e) == [] for e in daten)
    steht("Alle 200 Facetten, also die ganze Hülle auf 147 von 147 Graphen")


def test_zwanzig_zahlen():
    daten = K.lade()
    je = Counter((e["familie"], e["param"]) for e in daten["zwanzig"])
    assert [je[(f, p)] for f, p, _ in daten["zellen"]] == [4, 11, 9, 5, 18]
    assert daten["je_zelle"] == 200 and len(daten["zellen"]) == 5 and len(daten["zwanzig"]) == 47
    steht("47 von 1.000 offen nach Cliquen, ungeraden Kreisen, Antilöchern und Rädern (4, 11, 9, 5, 18)")
    steht("47 von 47 geschlossen")
    assert all(K.pruefe_zwanzig(e, mit_lp=False) == [] for e in daten["zwanzig"])


def test_matching_zahlen():
    # die Zählung selbst prüft test_oracle (alle 63.887 Paare); hier die Zählformel
    anzahl = {2: 1, 3: 3, 4: 10, 5: 33, 6: 155, 7: 1043}          # Graphen mit mindestens einer Kante je Knotenzahl
    paare = sum(a * sum(len(list(itertools.combinations(range(n), k))) for k in range(3, n + 1, 2)) for n, a in anzahl.items())
    assert (sum(anzahl.values()), paare) == (1245, 63887)
    steht("alle 63.887 Paare (Graph, ungerade Menge ab 3 Knoten) der 1.245 Graphen mit 2 bis 7 Knoten")


def test_cliquenrang_und_summe():
    for k in range(2, 40):
        r = S.cliquen_rang(k)
        assert S.max_summe_nach_runden(k, r) == 1 and (r == 0 or S.max_summe_nach_runden(k, r - 1) > 1)
        if k >= 3:
            assert r == len(bin(k - 2)) - 2                          # aufgerundeter Zweierlogarithmus von k - 1
    steht("genau ⌈log₂(k−1)⌉")
    steht("max(1, k/(2^r+1))")


def test_graph13_zahlen():
    adj = Z.ADJ
    assert len(kanten(adj)) == 52 and len(G.maximale_cliquen(adj)) == 39
    stabil = G.stabile_mengen(adj)
    assert len(stabil) == 40
    assert max(bin(m).count("1") for m in stabil) == 2 and max(len(c) for c in Z.CLIQUEN) == 4
    h = E.facetten13()
    assert (h["gesamt"], h["nichtnegativ"], h["cliquen"], h["eine_runde"], len(h["ausserhalb"])) == (92, 13, 39, 39, 1)
    steht("13 Knoten, 52 Kanten, 39 maximale Cliquen, 40 stabile Mengen (mit der leeren), α = 2, ω = 4")
    steht("92 Facetten, davon 13 x_v ≥ 0 und 39 Cliquen, 39 weitere in Runde 1, nur x(V) ≤ 2 erst in Runde 2")
    assert Z.WERT_RUNDE == (F(13, 4), F(26, 11), F(2))
    steht("13/4 (Cliquen), **26/11** (nach Runde 1), 2 (nach Runde 2)")
    steht("x = 2/11 übersteht jeden Schnitt der ersten Runde; 13 Schnitte zu je 11 Knoten geben 11·x(V) ≤ 26")
    assert Z.zeuge_uebersteht(F(2, 11)) and Z.summe_der_verschiebungen(11, 13) == ((11,) * 13, 26)


def test_zwoelf_knoten_text():
    steht("Ohne einen Knoten (12 Knoten) hat der Graph ebenfalls eine Facette x(V) ≤ 2 außerhalb der ersten Runde")
    steht("Cliquenüberdeckung 3")


def test_der_13er_graph_wird_nirgends_der_kleinste_genannt():
    """Die einzige Stelle mit „kleinste“ zum 13er-Graphen verneint es."""
    app = (Path(__file__).resolve().parent.parent / "app.py").read_text(encoding="utf-8")
    for text in (README, app):
        for satz in re.split(r"(?<=[.!?])\s", text.replace("\n", " ")):
            if "13" in satz and re.search(r"[Kk]leinste[rn]? Graph", satz):
                assert re.search(r"nicht|offen", satz), satz


def test_verschiebungen_je_laenge():
    ab = {}
    for laenge in (9, 10, 11):
        gut = [m for m in range(1, 14) if (s := Z.schranke_aus_summe(*Z.summe_der_verschiebungen(laenge, m))[1]) is not None and s <= 2]
        assert gut == list(range(gut[0], 14))
        ab[laenge] = gut[0]
    assert ab == {9: 13, 10: 10, 11: 7}
    steht("Folgen mit 9 Knoten: alle 13; mit 10 Knoten: ab 10; mit 11 Knoten: ab 7")
    assert Z.summe_der_verschiebungen(11, 7)[1] == 14 and min(Z.summe_der_verschiebungen(11, 7)[0]) == 5
    steht("5·x(V) ≤ 14")


def _tabelle_nach(ueberschrift: str) -> list:
    teil = README.split(ueberschrift, 1)[1]
    zeilen = []
    for z in teil.split("\n"):
        if z.startswith("|") and not z.startswith("|---"):
            zeilen.append([c.strip() for c in z.strip("|").split("|")])
        elif zeilen and not z.startswith("|"):
            break
    return zeilen


def test_rastertabelle_stimmt_mit_der_datei():
    daten = M.lade()
    z = _tabelle_nach("**Live-Suche (ohne vorab geladene Kreise).**")
    erwartet = M.zusammenfassung_raster(daten["raster"])
    assert len(z) - 1 == len(erwartet)
    for zeile, e in zip(z[1:], erwartet):
        modus = "alle 1" if e["gewichte"] == "eins" else "Werte 1 bis 100"
        assert zeile[:6] == [str(e["n"]), modus, str(e["mit_luecke"]), str(e["geschlossen"]), str(e["offen_bewiesen"]),
                             str(e["nicht_bestimmt"])], (zeile, e)


def test_grosse_tabelle_stimmt_mit_der_datei():
    daten = M.lade()
    z = _tabelle_nach("**Größere Graphen (mit vorab geladenen Kreisschnitten).**")
    erwartet = M.zusammenfassung_gross(daten["gross"])
    assert [e["n"] for e in erwartet] == [20, 30] and [e["graphen"] for e in erwartet] == [100, 30]
    assert len(z) - 1 == len(erwartet)
    for zeile, e in zip(z[1:], erwartet):
        assert zeile == [str(e[k]) for k in ("n", "graphen", "luecke_cliquen", "luecke_kreise", "davon_geschlossen", "offen_bewiesen",
                                             "nicht_bestimmt")]


def test_mittlere_luecken_und_nicht_bestimmt():
    """Mittel der Lücken aus reinen LP-Werten (neu gerechnet); die Zahl "nicht bestimmt" steht nur in der eingefrorenen Datei."""
    daten = M.lade()
    mittel = {}
    for n in (20, 30):
        zelle = [e for e in daten["gross"] if e["n"] == n]
        for feld in ("wert_cliquen", "wert_kreise"):
            mittel[n, feld] = sum((e[feld] - e["optimum"]) / e["optimum"] for e in zelle) / len(zelle) * 100
    text = {k: f"{v:.2f}".replace(".", ",") for k, v in mittel.items()}
    steht(f"bei 20 Knoten {text[20, 'wert_cliquen']} % und {text[20, 'wert_kreise']} %, bei 30 Knoten {text[30, 'wert_cliquen']} % und "
          f"{text[30, 'wert_kreise']} %")
    g30 = M.zusammenfassung_gross(daten["gross"])[1]
    steht(f"Bei 30 Knoten war der Wert der Runde in {g30['nicht_bestimmt']} von {g30['graphen']} Graphen mit diesem Budget nicht bestimmbar.")


def test_budgets_und_seeds_im_text():
    daten = M.lade()
    assert daten["budget_gross"] == [25.0, 8.0] and daten["budget_raster"] == [20.0, 10.0]
    steht("höchstens 25 s je Graph und 8 s je Programm")
    steht("höchstens 20 s je Graph und 10 s je Programm")
    assert sorted({e["seed"] for e in daten["raster"]}) == list(range(26200, 26240))
    assert [e["seed"] for e in daten["gross"] if e["n"] == 20] == list(range(26100, 26200))
    assert [e["seed"] for e in daten["gross"] if e["n"] == 30] == list(range(26100, 26130))
    steht("Zufalls-Seeds 26200 bis 26239")
    steht("Zufalls-Seeds ab 26100")


def test_zeitaussage_zur_live_suche():
    """Die Zeiten sind eingefroren (nicht neu gemessen): die README nennt die größte Zeit bis 16 Knoten, aufgerundet."""
    daten = M.lade()
    groesste = max(e["sekunden"] for e in daten["raster"] if e["n"] <= 16)
    m = re.search(r"bis 16 Knoten höchstens (\d+(?:,\d+)?) s", README)
    assert m, "Satz fehlt"
    assert groesste <= float(m.group(1).replace(",", ".")) <= groesste + 1.0


def test_umgebung_regler_und_konstanten_wie_beschrieben():
    import cvg_beispiele as B
    import cvg_constants as C
    import cvg_trennung as T

    umgebung = M.lade()["umgebung"]
    steht(f"scipy {umgebung['scipy']} mit HiGHS, Python {umgebung['python']} unter {umgebung['system']}")
    assert (C.SUCHE_N_MIN, C.SUCHE_N_MAX) == (8, 16) and (C.BUDGET_MIN, C.BUDGET_MAX, C.BUDGET_DEFAULT) == (1, 10, 5)
    steht("die Live-Suche mit 8 bis 16 Knoten")
    steht("Zeitgrenze von 1 bis 10 s (Voreinstellung 5 s")
    assert C.BUDGET_DEFAULT < max(e["sekunden"] for e in M.lade()["raster"] if e["n"] <= 16)
    assert len(B.HANDFAELLE) == 8
    steht("acht Handbeispiele")
    assert (T.DELTA, T.STRAFE, T.VERLETZT_AB, T.NENNER) == (1e-3, 1e-4, 1e-5, 1000)
    steht("Gewichte u in [0; 0,999]")
    steht("abzüglich 0,0001 mal der Summe der u")
    steht("Nenner ≤ 1000")
    steht("der Schwelle 10⁻⁵")


def test_testzahl_in_der_readme():
    """Die Zahl am Ende der Verifikation (readme_test_counts.py prüft sie gegen die Suite)."""
    assert re.search(r"\*\*Anzahl:\*\* \d+ Tests\.", README)


@pytest.mark.parametrize("wort", ["Phase 0", "Vormessung", " Stück ", "Linie ", " V1", " B8", " Z1", "trägt", "tragen", "Saatwert",
                                  "läuft lokal", "geplant"])
def test_keine_planungswoerter(wort):
    wurzel = Path(__file__).resolve().parent.parent
    for pfad in [wurzel / "README.md", *wurzel.glob("*.py"), *(wurzel / "tests").glob("*.py"), *(wurzel / "tools").glob("*.py")]:
        if pfad.name == "test_claims.py":
            continue
        text = pfad.read_text(encoding="utf-8")
        assert wort not in text, (pfad.name, wort)
