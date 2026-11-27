"""Permalink, Presets und Zufalls-Seed-Button (Muster des Portfolios, mit ausblendbaren Reglern).

Die Presets "Schnellstart" stehen in der Seitenleiste und setzen die Regler aller Experimente. Manche Regler sind nur unter bestimmten
Einstellungen sichtbar (ein Multiplikator je Zeile, die Facette, Länge und Anzahl der Verschiebungen). Streamlit löscht den Zustand eines
Reglers, der in einem Lauf nicht gezeichnet wird; deshalb steht sein zuletzt gewählter Wert zusätzlich unter einem eigenen Schlüssel
(KEPT). Preset und Permalink schreiben nur dorthin, und `seed_widget` setzt den Reglerzustand erst unmittelbar vor dem Zeichnen.
"""

import random
from dataclasses import dataclass
from typing import Callable

import streamlit as st

import cvg_beispiele as B
import cvg_constants as C
import cvg_katalog as K


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: float | None = None
    hi: float | None = None


def _wahl(optionen, typ=str):
    def umwandeln(roh):
        wert_ = typ(roh)
        if wert_ not in optionen:
            raise ValueError(roh)
        return wert_
    return umwandeln


def _menge(roh) -> tuple:
    """'0.1.2' -> (0, 1, 2); Tupel und Listen bleiben Mengen."""
    if isinstance(roh, (list, tuple)):
        return tuple(sorted({int(v) for v in roh}))
    return tuple(sorted({int(v) for v in str(roh).split(".") if v != ""}))


def _std(schluessel):
    return C.PRESETS[C.STANDARD][schluessel]


SETTING_SPECS = {
    "e1_select": SettingSpec("bsp", _wahl(B.HANDFAELLE), _std("e1")),
    **{f"u{i}_select": SettingSpec(f"u{i}", _wahl(B.MULTIPLIKATOREN),
                                   _std("u")[i] if i < len(_std("u")) else "0") for i in range(C.ZEILEN_MAX)},
    "m_select": SettingSpec("mg", _wahl(B.MATCHINGGRAPHEN), _std("m")),
    "m_menge": SettingSpec("U", _menge, _std("U")),
    "k_slider": SettingSpec("k", int, _std("k"), C.K_MIN, C.K_MAX),
    "r_slider": SettingSpec("r", int, _std("r"), C.R_MIN, C.R_MAX),
    "sammlung_radio": SettingSpec("sam", _wahl(C.SAMMLUNGEN), _std("sammlung")),
    "graph_select": SettingSpec("g", int, _std("graph"), 0, C.KLEIN_ANZAHL - 1),
    "facette_select": SettingSpec("f", int, _std("facette"), 0, C.FACETTEN_MAX - 1),
    "fall_select": SettingSpec("fall", int, _std("fall"), 0, C.ZWANZIG_ANZAHL - 1),
    "runde_radio": SettingSpec("rd", _wahl((0, 1, 2), int), _std("runde")),
    "laenge_radio": SettingSpec("len", _wahl((9, 10, 11), int), _std("laenge")),
    "anzahl_slider": SettingSpec("anz", int, _std("anzahl"), C.ANZAHL_MIN, C.ANZAHL_MAX),
    "n_slider": SettingSpec("n", int, _std("n"), C.SUCHE_N_MIN, C.SUCHE_N_MAX),
    "gewichte_radio": SettingSpec("gw", _wahl(C.SUCHE_GEWICHTE), _std("gewichte")),
    "seed_input": SettingSpec("seed", int, _std("seed"), 0, C.SEED_MAX),
    "budget_slider": SettingSpec("t", int, _std("budget"), C.BUDGET_MIN, C.BUDGET_MAX),
}
PRESET_KEYS = {"e1": "e1_select", "m": "m_select", "U": "m_menge", "k": "k_slider", "r": "r_slider", "sammlung": "sammlung_radio",
               "graph": "graph_select", "facette": "facette_select", "fall": "fall_select", "runde": "runde_radio",
               "laenge": "laenge_radio", "anzahl": "anzahl_slider", "n": "n_slider", "gewichte": "gewichte_radio", "seed": "seed_input",
               "budget": "budget_slider"}          # "u" (Multiplikatoren) wird auf u0 bis u7 verteilt
MULTIPLIKATOR_KEYS = tuple(f"u{i}_select" for i in range(C.ZEILEN_MAX))
AUSBLENDBAR = MULTIPLIKATOR_KEYS + ("graph_select", "facette_select", "fall_select", "laenge_radio", "anzahl_slider")
KEPT = {k: f"_kept_{k}" for k in AUSBLENDBAR}


def preset_werte(name: str) -> dict:
    """{Zustandsschlüssel: Wert} eines Presets."""
    preset = C.PRESETS[name]
    out = {state_key: preset[key] for key, state_key in PRESET_KEYS.items()}
    u = tuple(preset["u"]) + ("0",) * (C.ZEILEN_MAX - len(preset["u"]))
    out.update({f"u{i}_select": u[i] for i in range(C.ZEILEN_MAX)})
    return out


def zeilenzahl(beispiel: str) -> int:
    return len(B.startbeschreibung(B.HANDFAELLE[beispiel]).zeilen)


def facettenzahl(graph: int) -> int:
    return len(K.lade()["klein"][graph]["facetten"])


def sichtbare(einstellung: Callable) -> tuple:
    """Die Zustandsschlüssel aller Regler, die unter der Einstellung (Funktion Schlüssel -> Wert) gezeichnet werden."""
    out = ["e1_select", *MULTIPLIKATOR_KEYS[:zeilenzahl(einstellung("e1_select"))], "m_select", "m_menge", "k_slider", "r_slider",
           "sammlung_radio"]
    if einstellung("sammlung_radio") == "klein":
        out.append("graph_select")
        if facettenzahl(einstellung("graph_select")) > 1:
            out.append("facette_select")
    else:
        out.append("fall_select")
    out.append("runde_radio")
    if einstellung("runde_radio") == 2:
        out += ["laenge_radio", "anzahl_slider"]
    out += ["n_slider", "gewichte_radio", "seed_input", "budget_slider"]
    return tuple(out)


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key in AUSBLENDBAR:
            continue
        if state_key not in st.session_state:
            st.session_state[state_key] = list(spec.default) if state_key == "m_menge" else spec.default
    # die Knotenmenge muss zum gewählten Graphen passen (etwa nach einem Permalink)
    bild = B.MATCHINGGRAPHEN[st.session_state["m_select"]][0]
    menge = [v for v in st.session_state["m_menge"] if 0 <= v < bild.n]
    if menge != list(st.session_state["m_menge"]):
        st.session_state["m_menge"] = menge


def wert(state_key):
    """Der geltende Wert eines Reglers, auch wenn er gerade ausgeblendet ist."""
    if state_key in st.session_state:
        v = st.session_state[state_key]
    else:
        v = st.session_state.get(KEPT.get(state_key, state_key), SETTING_SPECS[state_key].default)
    return tuple(sorted(v)) if state_key == "m_menge" else v


def seed_widget(state_key):
    """Vor dem Zeichnen eines ausblendbaren Reglers: fehlt sein Zustand, kommt der zuletzt gewählte (oder der Standard-)Wert."""
    if state_key not in st.session_state:
        st.session_state[state_key] = st.session_state.get(KEPT[state_key], SETTING_SPECS[state_key].default)


def merke(state_key):
    """Nach dem Zeichnen: den Wert behalten, falls der Regler später ausgeblendet wird."""
    st.session_state[KEPT[state_key]] = st.session_state[state_key]


def setze(state_key, neu):
    """Einen Wert aus einem Rückruf setzen (Preset, Wahl eines anderen Beispiels), auch für ausblendbare Regler."""
    if state_key in KEPT:
        st.session_state[KEPT[state_key]] = neu
        st.session_state.pop(state_key, None)
    else:
        st.session_state[state_key] = list(neu) if state_key == "m_menge" else neu


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def begrenze(state_key, roh):
    """Wert aus der Adresszeile: umwandeln und auf die Grenzen beschränken."""
    spec = SETTING_SPECS[state_key]
    v = spec.caster(roh)
    if spec.lo is not None:
        v = max(spec.lo, min(spec.hi, v))
    return v


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                setze(state_key, begrenze(state_key, qp[spec.url_param]))
            except (ValueError, TypeError, OverflowError):
                continue
    # eine Facettennummer außerhalb der Facetten dieses Graphen gilt als 0
    if wert("facette_select") >= facettenzahl(wert("graph_select")):
        setze("facette_select", 0)
    st.session_state["permalink_loaded"] = True


def als_url(state_key, v) -> str:
    return ".".join(str(i) for i in v) if state_key == "m_menge" else str(v)


def sync_query_params():
    """Die Adresszeile zeigt die sichtbaren Regler, deren Wert vom Standard abweicht."""
    try:
        gewuenscht = {}
        for k in sichtbare(wert):
            if wert(k) != SETTING_SPECS[k].default:
                gewuenscht[SETTING_SPECS[k].url_param] = als_url(k, wert(k))
        for spec in SETTING_SPECS.values():
            if spec.url_param not in gewuenscht and spec.url_param in st.query_params:
                del st.query_params[spec.url_param]
        for k, v in gewuenscht.items():
            st.query_params[k] = v
    except Exception:
        pass


def apply_preset(name):
    for state_key, v in preset_werte(name).items():
        setze(state_key, v)


def preset_passt(name: str, einstellung: Callable) -> bool:
    """Entsprechen alle unter dem Preset sichtbaren Regler seinen Werten?"""
    werte = preset_werte(name)
    ziel = lambda k: tuple(werte[k]) if k == "m_menge" else werte[k]  # noqa: E731
    return all(einstellung(k) == ziel(k) for k in sichtbare(ziel))


def aktives_preset():
    for name in C.PRESETS:
        if preset_passt(name, wert):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispiel für alle Experimente laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
                  type="primary" if aktiv == name else "secondary")


def wechsle_beispiel():
    """Ein anderes Handbeispiel: alle Multiplikatoren auf 0."""
    for k in MULTIPLIKATOR_KEYS:
        setze(k, "0")


def setze_loesung():
    """Die Multiplikatoren des Zertifikats von Hand einsetzen."""
    loesung = B.HANDFAELLE[st.session_state["e1_select"]].loesung
    for i, k in enumerate(MULTIPLIKATOR_KEYS):
        setze(k, loesung[i] if i < len(loesung) else "0")


def wechsle_matchinggraph():
    st.session_state["m_menge"] = list(B.MATCHINGGRAPHEN[st.session_state["m_select"]][1])


def wechsle_graph():
    setze("facette_select", 0)


def neuer_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
