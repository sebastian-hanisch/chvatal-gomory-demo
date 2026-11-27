"""Layout (DEMO-PLAYBOOK §2): fester Kopf, Schnellstart oben in der Seitenleiste, aktives Preset hervorgehoben.

Die Regler stehen bei den Experimenten. Die Hervorhebung vergleicht alle unter dem Preset sichtbaren Regler; die Tests stellen sicher,
dass jeder Regler in SETTING_SPECS steht und seine Änderung die Markierung aufhebt."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import cvg_constants as C
import cvg_presets as P

APP = str(Path(__file__).resolve().parent.parent / "app.py")
REGLER_ARTEN = ("slider", "number_input", "selectbox", "radio", "multiselect")


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _typen(at) -> dict:
    return {b.label: b.proto.type for b in at.sidebar.button if b.label in C.PRESETS}


def _hervorgehoben(at):
    return [n for n, typ in _typen(at).items() if typ == "primary"]


def _regler(at, key):
    for art in REGLER_ARTEN:
        try:
            return getattr(at, art)(key=key)
        except KeyError:
            continue
    raise AssertionError(f"Regler {key} fehlt")


def _schluessel(at) -> set:
    return {w.key for art in REGLER_ARTEN for w in getattr(at, art) if w.key}


def test_presets_stehen_in_der_seitenleiste_und_nicht_im_hauptbereich():
    at = _app()
    assert [b.label for b in at.sidebar.button] == list(C.PRESETS)
    assert not [b for b in at.main.button if b.label in C.PRESETS]


def test_titel_steht_im_festen_kopf():
    at = _app()
    assert "st-key-kopf" in " ".join(h.proto.body for h in at.get("html"))
    assert at.title[0].value


def test_beim_start_ist_genau_das_standard_preset_hervorgehoben():
    assert _hervorgehoben(_app()) == [C.STANDARD]


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_angeklicktes_preset_ist_hervorgehoben_und_bleibt_es_im_naechsten_lauf(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]
    assert _hervorgehoben(at) == [name]
    at.run()
    assert _hervorgehoben(at) == [name]


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_jeder_sichtbare_regler_steht_in_setting_specs_und_ist_der_erwartete(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    werte = P.preset_werte(name)
    assert _schluessel(at) == set(P.sichtbare(lambda k: werte[k]))
    assert _schluessel(at) <= set(P.SETTING_SPECS)


AENDERUNGEN = [
    ("e1_select", "dreieck_kanten", None), ("u0_select", "1/3", None), ("m_select", "k5", None), ("m_menge", [0, 1, 2], None),
    ("k_slider", 4, None), ("r_slider", 0, None), ("sammlung_radio", "zwanzig", None), ("graph_select", 3, None),
    ("runde_radio", 0, None), ("n_slider", 9, None), ("gewichte_radio", "werte", None), ("seed_input", 3, None),
    ("budget_slider", 2, None), ("fall_select", 3, "Viele Schnitte"), ("laenge_radio", 9, "Viele Schnitte"),
    ("anzahl_slider", 3, "Viele Schnitte"),
]


@pytest.mark.parametrize("key, neu, preset", AENDERUNGEN)
def test_jede_aenderung_eines_reglers_hebt_die_hervorhebung_auf(key, neu, preset):
    at = _app()
    name = preset or C.STANDARD
    if preset:
        at.sidebar.button(key=f"preset_{preset}").click().run()
    _regler(at, key).set_value(neu).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert name not in _hervorgehoben(at)
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert _hervorgehoben(at) == [name]


def test_die_facette_ist_nur_bei_mehreren_sichtbar_und_hebt_die_hervorhebung_auf():
    import cvg_katalog as K

    at = _app()
    assert "facette_select" not in _schluessel(at)
    mehrere = next(i for i, e in enumerate(K.lade()["klein"]) if len(e["facetten"]) > 1)
    at.selectbox(key="graph_select").set_value(mehrere).run()
    assert "facette_select" in _schluessel(at)
    at.selectbox(key="facette_select").set_value(1).run()
    assert not at.exception


def test_alle_regler_aus_setting_specs_kommen_in_der_oberflaeche_vor():
    gesehen = set()
    at = _app()
    gesehen |= _schluessel(at)
    at.sidebar.button(key="preset_Viele Schnitte").click().run()
    gesehen |= _schluessel(at)
    at.selectbox(key="e1_select").set_value("rad_kanten").run()
    gesehen |= _schluessel(at)
    at.sidebar.button(key=f"preset_{C.STANDARD}").click().run()
    import cvg_katalog as K

    mehrere = next(i for i, e in enumerate(K.lade()["klein"]) if len(e["facetten"]) > 1)
    at.selectbox(key="graph_select").set_value(mehrere).run()
    gesehen |= _schluessel(at)
    assert gesehen == set(P.SETTING_SPECS)
