"""PDF-Export (nur Latin-1) und Abbildungen: gesperrte Achsen, feste Knotenlagen."""

import pytest

import cvg_beispiele as B
import cvg_evaluation as E
import cvg_pdf_export as PDF
import cvg_visualization as V


def test_pdf_mit_allen_verdikttexten():
    abschnitte = [("Kernfrage", [E.verdict_kernfrage(3, 1)[1]]), ("Clique", [E.verdict_clique(6, 2)[1]]),
                  ("Zeuge", [E.verdict_zeuge(1)[1], E.verdict_zeuge(2, 9, 13)[1]]),
                  ("Matching", [E.verdict_matching(E.ergebnis_matching("fuenfeck", (0, 1, 2, 3, 4)))[1]]),
                  ("Suche", [E.verdict_suche("offen_bewiesen", 2, 5, 5.25)[1], E.verdict_suche("nicht_bestimmt", 0, 5, 6.0, "zeit")[1]]),
                  ("Abrunden", [E.verdict_abrunden(E.ergebnis_abrunden("rad_cliquen", ("1/2",) * 5))[1]]),
                  ("Titel mit ⌈log₂(k−1)⌉", ["x(S) ≤ 1, √, α, β, ⅓, ⅙"])]
    daten = PDF.erzeuge_pdf(abschnitte)
    assert daten[:5] == b"%PDF-" and len(daten) > 1000


def test_unbekanntes_zeichen_wird_gemeldet():
    with pytest.raises(UnicodeEncodeError):
        PDF.latin1("ℚ")


def _gesperrt(fig):
    achsen = [fig.layout[k] for k in fig.layout.to_plotly_json() if k.startswith(("xaxis", "yaxis"))]
    return achsen and all(a.fixedrange for a in achsen)


def test_alle_abbildungen_haben_feste_achsen():
    figuren = [V.zeichne_graph(B.RAD.lage, B.RAD.kanten, B.RAD.namen, werte=["1/2"] * 6, markiert=(1,), innen=(0,), rand=(1,)),
               V.kantenwerte(B.FUENFECK.lage, B.FUENFECK.kanten, ["1/2"] * 6, B.FUENFECK.namen),
               V.balken(["a", "b"], [2.5, 2], ["5/2", "2"], ziel=2, ziel_name="ganzzahlig", hervor=1),
               V.haeufigkeiten((9,) * 13, soll=9), V.suchverlauf(7.5, [7.2, 7.0], 7), V.suchverlauf(7.0, [], 7)]
    assert all(_gesperrt(f) for f in figuren)


def test_knotenlagen_sind_fest_und_verschieden():
    for bild in (B.DREIECK, B.K4, B.FUENFECK, B.RAD, B.BRUECKE, B.K5, B.PETERSEN, B.SECHSECK):
        assert len(set((round(x, 6), round(y, 6)) for x, y in bild.lage)) == bild.n
    assert B.kreis_lage(4)[0] == pytest.approx((0.0, 1.0))
