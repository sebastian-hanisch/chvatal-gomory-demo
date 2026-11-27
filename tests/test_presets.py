"""Presets: vollständig, Werte gültig, Standard gleich Standardeinstellung, Wirkung je Preset wie beschrieben."""

import cvg_beispiele as B
import cvg_constants as C
import cvg_evaluation as E
import cvg_katalog as K
import cvg_presets as P
import cvg_trennung as T


def test_jedes_preset_hat_hilfe_und_alle_schluessel():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS) | {"u"}, name
        assert C.PRESET_HELP[name]


def test_alle_werte_gueltig_und_zu_den_beispielen_passend():
    for name in C.PRESETS:
        w = P.preset_werte(name)
        for k, spec in P.SETTING_SPECS.items():
            v = w[k]
            assert P.begrenze(k, P.als_url(k, v)) == v, (name, k)
        bild = B.MATCHINGGRAPHEN[w["m_select"]][0]
        assert set(w["m_menge"]) <= set(range(bild.n))
        assert len(C.PRESETS[name]["u"]) <= P.zeilenzahl(w["e1_select"])
        assert w["facette_select"] < P.facettenzahl(w["graph_select"])


def test_standard_preset_gleich_standardeinstellung():
    w = P.preset_werte(C.STANDARD)
    assert all(w[k] == spec.default for k, spec in P.SETTING_SPECS.items())


def test_presets_sind_verschieden_in_sichtbaren_reglern():
    for a in C.PRESETS:
        werte = P.preset_werte(a)
        assert [n for n in C.PRESETS if P.preset_passt(n, lambda k: werte[k])] == [a]


def test_anzahlen_der_sammlungen_stimmen_mit_den_reglergrenzen():
    daten = K.lade()
    assert len(daten["klein"]) == C.KLEIN_ANZAHL and len(daten["zwanzig"]) == C.ZWANZIG_ANZAHL
    assert max(len(e["facetten"]) for e in daten["klein"]) == C.FACETTEN_MAX
    assert daten["klein"][C.KLEIN_DEFAULT].get("hand") is True
    c5 = daten["klein"][C.KLEIN_C5]
    assert c5["n"] == 5 and len(c5["kanten"]) == 5


def _verdikte(name):
    w = P.preset_werte(name)
    a = E.ergebnis_abrunden(w["e1_select"], [w[f"u{i}_select"] for i in range(8)])
    m = E.ergebnis_matching(w["m_select"], w["m_menge"])
    out = {"e1": E.verdict_abrunden(a), "m": E.verdict_matching(m), "k": E.verdict_clique(w["k_slider"], w["r_slider"])}
    if w["sammlung_radio"] == "klein":
        s = K.schnitt_klein(K.lade()["klein"][w["graph_select"]], w["facette_select"])
        out["leiter"] = E.verdict_klein(s)
    else:
        out["leiter"] = E.verdict_zwanzig(K.lade()["zwanzig"][w["fall_select"]])
    out["zeuge"] = E.verdict_zeuge(w["runde_radio"], w["laenge_radio"], w["anzahl_slider"])
    return out, w


def test_standard_preset_zeigt_die_hauptergebnisse():
    v, w = _verdikte(C.STANDARD)
    assert v["e1"][0] == "success" and "Aus fünf Zeilen mit je ½ wird **x_0 + x_1 + x_2 + x_3 + x_4 + x_5 ≤ 2**" in v["e1"][1]
    assert v["m"][0] == "success" and "x(E[U]) ≤ 2" in v["m"][1]
    assert v["k"][0] == "info" and "6/5" in v["k"][1]
    assert v["leiter"][0] == "success" and "lassen **7/3** stehen" in v["leiter"][1] and "senkt den Wert auf **2**" in v["leiter"][1]
    assert v["zeuge"][0] == "warning" and "13/6" in v["zeuge"][1]


def test_preset_ohne_wirkung_meldet_keine_wirkung():
    v, _ = _verdikte("Abrunden ohne Wirkung")
    assert v["e1"][0] == "info" and "schon ganzzahlig" in v["e1"][1]
    assert v["m"][0] == "info" and "nichts Neues" in v["m"][1]
    assert v["leiter"][0] == "info" and "ändert den Wert nicht" in v["leiter"][1]
    assert v["zeuge"][0] == "info" and "x(V) ≤ 3" in v["zeuge"][1]
    assert v["k"][0] == "success"


def test_uebrige_presets():
    v, _ = _verdikte("Dreieck und Petersen-Graph")
    assert v["e1"][0] == "success" and "Aus drei Zeilen mit je ½" in v["e1"][1]
    assert v["m"][0] == "success" and "links steht 5/2" in v["m"][1] and v["k"][0] == "success"
    v, _ = _verdikte("Zwei Runden genügen")
    assert v["k"][0] == "success" and v["zeuge"][0] == "success" and "9·x(V) ≤ 26" in v["zeuge"][1]
    v, w = _verdikte("Viele Schnitte")
    assert v["leiter"][0] == "success" and len(K.lade()["zwanzig"][w["fall_select"]]["schnitte"]) >= 7
    assert v["zeuge"][0] == "success" and "mindestens 5-mal" in v["zeuge"][1]


def test_such_presets_haben_die_beschriebenen_ausgaenge():
    """Nur der Ausgang, keine Schnittzahlen (löserabhängig)."""
    erwartet = {C.STANDARD: T.GESCHLOSSEN, "Abrunden ohne Wirkung": T.KEINE_LUECKE, "Viele Schnitte": T.GESCHLOSSEN}
    for name, status in erwartet.items():
        w = P.preset_werte(name)
        s = E.suche_live(w["n_slider"], w["gewichte_radio"], w["seed_input"], 10.0)[4]
        assert s.status == status, (name, s.status, s.grund)
        if status == T.GESCHLOSSEN:
            assert len(s.schritte) >= 1
