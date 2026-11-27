"""Ausblendbare Regler: Der Wert bleibt erhalten, wenn der Regler verschwindet und wiederkommt, und die App rechnet mit dem
angezeigten Wert (Gotcha: Frontend/Backend-Abweichung bei ausgeblendeten Reglern)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

import cvg_constants as C
import cvg_presets as P

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    assert not at.exception
    return at


def test_laenge_und_anzahl_ueberleben_das_ausblenden():
    at = _app()
    at.radio(key="runde_radio").set_value(2).run()
    at.radio(key="laenge_radio").set_value(11).run()
    at.slider(key="anzahl_slider").set_value(4).run()
    at.radio(key="runde_radio").set_value(0).run()
    assert not [w for w in at.slider if w.key == "anzahl_slider"]
    at.radio(key="runde_radio").set_value(2).run()
    assert at.radio(key="laenge_radio").value == 11 and at.slider(key="anzahl_slider").value == 4
    # 4 Verschiebungen zu 11 Knoten: Knoten fehlen höchstens zweimal, jeder kommt mindestens 2-mal vor: 2·x(V) <= 8
    assert any("2·x(V) ≤ 8, abgerundet x(V) ≤ 4" in i.value for i in at.info), [i.value for i in at.info]


def test_der_fall_ueberlebt_den_wechsel_der_sammlung():
    at = _app()
    at.radio(key="sammlung_radio").set_value("zwanzig").run()
    at.selectbox(key="fall_select").set_value(5).run()
    at.radio(key="sammlung_radio").set_value("klein").run()
    assert at.selectbox(key="graph_select").value == C.KLEIN_DEFAULT
    at.radio(key="sammlung_radio").set_value("zwanzig").run()
    assert at.selectbox(key="fall_select").value == 5


def test_multiplikatoren_werden_beim_beispielwechsel_zurueckgesetzt_und_von_hand_gesetzt():
    at = _app()
    at.selectbox(key="e1_select").set_value("k4_kanten").run()
    assert [at.selectbox(key=f"u{i}_select").value for i in range(6)] == ["0"] * 6
    next(b for b in at.button if "Gewichte von Hand" in b.label).click().run()
    assert [at.selectbox(key=f"u{i}_select").value for i in range(6)] == ["1/2", "1/2", "0", "1/2", "0", "0"]
    at.selectbox(key="e1_select").set_value("dreieck_kanten").run()
    assert [at.selectbox(key=f"u{i}_select").value for i in range(3)] == ["0"] * 3
    next(b for b in at.button if "Gewichte von Hand" in b.label).click().run()
    assert [at.selectbox(key=f"u{i}_select").value for i in range(3)] == ["1/2"] * 3
    assert any("Aus drei Zeilen mit je ½" in s.value for s in at.success)


def test_kept_schluessel_decken_alle_ausblendbaren_ab():
    assert set(P.KEPT) == set(P.AUSBLENDBAR)
    assert not set(P.AUSBLENDBAR) & {"e1_select", "m_select", "m_menge", "k_slider", "r_slider", "sammlung_radio", "runde_radio"}
