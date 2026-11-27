"""Die Oberfläche je Preset: die erwarteten Verdikte erscheinen, nichts meldet einen Fehler, Permalink und Eckfälle."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import cvg_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _app(**query) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in query.items():
        at.query_params[k] = v
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texte(at):
    return [e.value for art in ("success", "info", "warning") for e in getattr(at, art)]


ERWARTET = {
    C.STANDARD: ["Aus fünf Zeilen mit je ½", "x(E[U]) ≤ 2", "6/5", "lassen **7/3** stehen", "Eine Runde genügt hier nicht",
                 "Die Lücke ist geschlossen", "**Ja, erzeugen geht:**"],
    "Dreieck und Petersen-Graph": ["Aus drei Zeilen mit je ½", "links steht 5/2", "Nach einer Runde gilt x(K3) ≤ 1"],
    "Abrunden ohne Wirkung": ["schon ganzzahlig", "ist gerade", "ändert den Wert nicht", "x(V) ≤ 3", "nichts zu tun"],
    "Zwei Runden genügen": ["9·x(V) ≤ 26", "Zwei Runden genügen"],
    "Viele Schnitte": ["Schnitte der ersten Runde senken", "mindestens 5-mal", "geschlossen"],
}


@pytest.mark.parametrize("name", list(ERWARTET))
def test_verdikte_je_preset(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]
    assert not at.error, [e.value for e in at.error]
    texte = " | ".join(_texte(at))
    for teil in ERWARTET[name]:
        assert teil in texte, (name, teil, texte)


def test_permalink_setzt_die_regler():
    at = _app(bsp="dreieck_kanten", u0="1/2", u1="1/2", u2="1/2", rd="2", len="11", anz="7", k="4", r="1", n="9", seed="4")
    assert at.selectbox(key="e1_select").value == "dreieck_kanten"
    assert [at.selectbox(key=f"u{i}_select").value for i in range(3)] == ["1/2"] * 3
    assert at.radio(key="runde_radio").value == 2 and at.radio(key="laenge_radio").value == 11
    assert at.slider(key="anzahl_slider").value == 7 and at.slider(key="k_slider").value == 4
    assert at.slider(key="n_slider").value == 9 and at.number_input(key="seed_input").value == 4


def test_permalink_mit_unsinn_wird_begrenzt_oder_ignoriert():
    at = _app(k="999", r="-3", bsp="gibtsnicht", U="0.1.99", g="9999", f="55", t="abc", mg="k5")
    assert at.slider(key="k_slider").value == C.K_MAX and at.slider(key="r_slider").value == 0
    assert at.selectbox(key="e1_select").value == C.HAND_DEFAULT
    assert at.multiselect(key="m_menge").value == [0, 1]
    assert at.selectbox(key="graph_select").value == C.KLEIN_ANZAHL - 1
    assert at.slider(key="budget_slider").value == C.BUDGET_DEFAULT


def test_matchinggraph_wechsel_setzt_die_menge():
    at = _app()
    at.selectbox(key="m_select").set_value("bruecke").run()
    assert at.multiselect(key="m_menge").value == [0, 1, 2]
    at.multiselect(key="m_menge").set_value([]).run()
    assert not at.exception and any("0 ≤ 0" in i.value for i in at.info)


@pytest.mark.parametrize("beispiel", ["dreieck_kanten", "dreieck_cliquen", "k4_kanten", "k4_cliquen", "fuenfeck_grade",
                                      "fuenfeck_kanten", "rad_cliquen", "rad_kanten"])
def test_jedes_handbeispiel_mit_und_ohne_gewichte(beispiel):
    at = _app()
    at.selectbox(key="e1_select").set_value(beispiel).run()
    assert not at.exception and not at.error
    next(b for b in at.button if "Gewichte von Hand" in b.label).click().run()
    assert not at.exception and not at.error


@pytest.mark.parametrize("fall", [0, 23, 46])
def test_faelle_mit_20_knoten(fall):
    at = _app(sam="zwanzig", fall=str(fall))
    assert not at.error
    assert any("Dualbeweis" in m.value for m in at.markdown)


@pytest.mark.parametrize("graph", [0, 6, 77, 146])
def test_graphen_der_kleinen_sammlung(graph):
    at = _app(g=str(graph))
    assert not at.error


def test_suche_mit_kleinstem_budget_haengt_nicht_und_hat_einen_ausgang():
    at = _app(n="16", gw="werte", t="1", seed="26201")
    assert not at.error
    assert any(("geschlossen" in t) or ("Nicht bestimmt" in t) or ("nichts zu tun" in t) or ("bleibt eine" in t) for t in _texte(at))


def test_pdf_erst_nach_klick():
    at = _app()
    assert not at.get("download_button")
    next(b for b in at.button if b.label == "PDF erstellen").click().run()
    assert not at.exception
    assert at.get("download_button")


def test_vorgerechnete_tabelle_und_erklaertabellen_stehen_da():
    at = _app()
    text = " ".join(m.value for m in at.markdown)
    assert "Vorgerechnet: größere Graphen" in text
    spalten = [list(d.value.columns) for d in at.dataframe]
    assert ["Begriff", "Was ist das?", "Beispiel"] in spalten
    assert ["Familie", "Ungleichung", "Gewichte über den Cliquenzeilen"] in spalten
