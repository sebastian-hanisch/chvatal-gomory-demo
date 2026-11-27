"""Jede Kern-Einheit an einer kleinen Instanz, von Hand nachgerechnet."""

from fractions import Fraction as F

import pytest

import cvg_beispiele as B
import cvg_familien as FA
import cvg_graphen as G
import cvg_leiter as L
import cvg_lp as LP
import cvg_schnitt as S
import cvg_trennung as T
import cvg_zeuge as Z
from cvg_konflikt import adj_aus_kanten


# ------------------------------------------------------------------------------------------------ CG-Schnitt

def test_dreieck_drei_halbe_kantenzeilen(dreieck):
    _, zeilen = dreieck
    alpha, beta, links, rechts = S.cg_schnitt(zeilen, [F(1, 2)] * 3)
    assert links == (1, 1, 1) and rechts == F(3, 2)
    assert (alpha, beta) == ((1, 1, 1), 1)


def test_ohne_multiplikatoren_entsteht_null_kleiner_gleich_null(dreieck):
    _, zeilen = dreieck
    assert S.cg_schnitt(zeilen, [0] * 3)[:2] == ((0, 0, 0), 0)


def test_abrunden_von_hand():
    zeilen = [((2, 1), 3), ((1, 3), 4)]
    links, rechts = S.gewichtete_summe(zeilen, [F(1, 3), F(1, 2)])
    assert links == (F(2, 3) + F(1, 2), F(1, 3) + F(3, 2)) and rechts == F(1) + F(2)
    assert S.abrunden(links, rechts) == ((1, 1), 3)


def test_negative_oder_fehlende_multiplikatoren_werden_abgewiesen(dreieck):
    _, zeilen = dreieck
    with pytest.raises(ValueError):
        S.cg_schnitt(zeilen, [F(-1, 2), 0, 0])
    with pytest.raises(ValueError):
        S.cg_schnitt(zeilen, [F(1, 2)] * 2)
    with pytest.raises(ValueError):
        S.schnitt_aus(zeilen, {3: F(1, 2)})


def test_gleiche_zeile_zweimal_ist_wie_doppeltes_gewicht(dreieck):
    _, zeilen = dreieck
    doppelt = zeilen + [zeilen[0]]
    assert S.cg_schnitt(doppelt, [F(1, 3), F(1, 2), F(1, 2), F(1, 3)])[:2] == S.cg_schnitt(zeilen, [F(2, 3), F(1, 2), F(1, 2)])[:2]


def test_ist_gueltig_und_traeger():
    assert S.ist_gueltig((1, 1, 1), 1, [(1, 0, 0), (0, 0, 1), (0, 0, 0)])
    assert not S.ist_gueltig((1, 1, 1), 1, [(1, 1, 0)])
    assert S.traegermaske((0, 2, 1)) == 0b110


def test_ungleichung_text():
    assert S.ungleichung_text((1, 0, 2), 2, ("a", "b", "c")) == "a + 2·c ≤ 2"
    assert S.ungleichung_text((0, 0), 0) == "0 ≤ 0"


# ------------------------------------------------------------------------------------------------ Matching

def test_matching_fuenfeck_mit_ausgangskante():
    """Kanten 01, 04, 12, 23, 34, 45: halbe Gradzeilen der Knoten 0..4. Die Kante 45 hat nur ½ und fällt beim Abrunden weg."""
    kanten = [(0, 1), (0, 4), (1, 2), (2, 3), (3, 4), (4, 5)]
    zeilen = S.matching_zeilen(6, kanten)
    u = S.matching_multiplikatoren(6, range(5))
    assert u == [F(1, 2)] * 5 + [0]
    alpha, beta, links, rechts = S.cg_schnitt(zeilen, u)
    assert links == (1, 1, 1, 1, 1, F(1, 2)) and rechts == F(5, 2)
    assert (alpha, beta) == ((1, 1, 1, 1, 1, 0), 2)
    assert S.kanten_in_menge(kanten, range(5)) == (0, 1, 2, 3, 4) and S.kanten_am_rand(kanten, range(5)) == (5,)
    with pytest.raises(ValueError):
        S.matching_multiplikatoren(6, [6])


# ------------------------------------------------------------------------------------------------ Cliquen

def test_cliquen_multiplikatoren_k5_aus_dreiecken():
    mengen, gewicht = S.cliquen_multiplikatoren(5, 3)
    assert len(mengen) == 10 and gewicht == F(1, 6)
    zeilen = [S.zeile(5, m) for m in mengen]
    assert S.cg_schnitt(zeilen, [gewicht] * 10)[:2] == ((1,) * 5, 1)


def test_cliquen_multiplikatoren_weisen_zu_grosse_k_ab():
    with pytest.raises(ValueError):
        S.cliquen_multiplikatoren(6, 3)            # 6 > 2·3 − 1
    with pytest.raises(ValueError):
        S.cliquen_multiplikatoren(2, 3)


@pytest.mark.parametrize("k, rang", [(2, 0), (3, 1), (4, 2), (5, 2), (6, 3), (9, 3), (10, 4), (17, 4), (18, 5)])
def test_cliquen_rang(k, rang):
    assert S.cliquen_rang(k) == rang
    assert S.groesste_clique_nach(rang) >= k and (rang == 0 or S.groesste_clique_nach(rang - 1) < k)


def test_cliquen_rang_unter_zwei_knoten():
    with pytest.raises(ValueError):
        S.cliquen_rang(1)


def test_punkt_und_summe_nach_runden():
    assert [S.punkt_nach_runden(r) for r in (0, 1, 2)] == [F(1, 2), F(1, 3), F(1, 5)]
    assert S.max_summe_nach_runden(6, 2) == F(6, 5)
    assert S.max_summe_nach_runden(3, 1) == 1 and S.max_summe_nach_runden(3, 0) == F(3, 2)
    assert S.treppenstufen(3) == [(1, 2, 3), (2, 3, 5), (3, 5, 9)]


# ------------------------------------------------------------------------------------------------ Graphen

def test_cliquen_des_fuenfecks_mit_zusatzknoten(rad_fehlend):
    assert G.maximale_cliquen(rad_fehlend) == ((0, 1, 5), (0, 4), (1, 2, 5), (2, 3), (3, 4))
    assert max(bin(m).count("1") for m in G.stabile_mengen(rad_fehlend)) == 2


def test_isolierter_knoten_ist_eine_clique_und_leerer_graph():
    assert G.maximale_cliquen(adj_aus_kanten(3, [(0, 1)])) == ((0, 1), (2,))
    assert G.maximale_cliquen(()) == ()
    assert G.stabile_mengen(()) == [0]


def test_stabile_mengen_des_dreiecks_und_groesstes_gewicht(dreieck):
    adj, _ = dreieck
    assert sorted(G.stabile_mengen(adj)) == [0, 1, 2, 4]
    assert G.groesstes_gewicht(adj, (2, 7, 5)) == (7, 0b010)
    pfad = adj_aus_kanten(4, [(0, 1), (1, 2), (2, 3)])
    gewicht, menge = G.groesstes_gewicht(pfad, (3, 4, 4, 3))                 # {0, 2} oder {1, 3}: je 7
    assert gewicht == 7 and menge in (0b0101, 0b1010)


def test_obergrenzen_der_aufzaehlungen():
    leer = (0,) * 20
    with pytest.raises(G.ZuViele):
        G.stabile_mengen(leer, grenze=1000)
    with pytest.raises(G.ZuViele):
        G.maximale_cliquen(leer, grenze=5)


def test_graph13_eigenschaften():
    adj = Z.ADJ
    h = G.komplement(adj)
    assert all(bin(a).count("1") == 4 for a in h)
    assert not any(h[i] >> j & 1 and h[i] >> k & 1 and h[j] >> k & 1 for i in range(13) for j in range(13) for k in range(13))
    assert sum(bin(a).count("1") for a in adj) // 2 == 52
    assert len(G.maximale_cliquen(adj)) == 39 and max(map(len, G.maximale_cliquen(adj))) == 4
    stabil = G.stabile_mengen(adj)
    assert len(stabil) == 40 and max(bin(m).count("1") for m in stabil) == 2


def test_induzierte_kreise_und_antiloecher():
    c7 = G.kreisgraph(7, (1,))
    assert G.induzierte_kreise(c7, 7) == [(0, 1, 2, 3, 4, 5, 6)]
    assert len(FA.antiloecher(G.komplement(c7))) == 1
    assert FA.antiloecher(G.komplement(G.kreisgraph(5, (1,)))) == []           # das Antiloch mit 5 Knoten zählt als Kreis
    assert G.induzierte_kreise(adj_aus_kanten(5, [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4), (0, 2)]), 5) == []   # Sehne 02


def test_alle_ungeraden_kreise_des_fuenfecks_mit_zusatzknoten(rad_fehlend):
    groessen = sorted(bin(m).count("1") for m in G.alle_ungeraden_kreise(rad_fehlend))
    assert groessen == [3, 3, 5, 5]


# ------------------------------------------------------------------------------------------------ Familien als Schnitte

def test_kreis_zertifikat_fuenfeck():
    adj = G.kreisgraph(5, (1,))
    cl = G.maximale_cliquen(adj)
    u = FA.kreis_zertifikat(cl, (0, 1, 2, 3, 4))
    assert S.schnitt_aus(L.cliquenzeilen(5, cl), u) == ((1,) * 5, 2)


def test_rad_zertifikat_fuenferrad():
    rad = adj_aus_kanten(6, [(i, (i + 1) % 5) for i in range(5)] + [(i, 5) for i in range(5)])
    cl = G.maximale_cliquen(rad)
    u = FA.rad_zertifikat(cl, 5, (0, 1, 2, 3, 4))
    assert S.schnitt_aus(L.cliquenzeilen(6, cl), u) == ((1, 1, 1, 1, 1, 2), 2)


@pytest.mark.parametrize("k", [3, 4, 5, 6])
def test_antiloch_zertifikat(k):
    n = 2 * k + 1
    adj = G.komplement(G.kreisgraph(n, (1,)))
    cl = G.maximale_cliquen(adj)
    folge = tuple(range(n))
    u = FA.antiloch_zertifikat(cl, folge)
    assert S.schnitt_aus(L.cliquenzeilen(n, cl), u) == ((1,) * n, 2)


def test_zertifikat_ohne_passende_clique():
    with pytest.raises(ValueError):
        FA.clique_mit(((0, 1), (2,)), (0, 2))


def test_kreistrennung_findet_das_dreieck_und_bei_ganzzahlig_nichts(dreieck):
    adj, _ = dreieck
    assert [sorted(k) for k in FA.trenne_kreise(adj, [0.5] * 3)] == [[0, 1, 2]]
    assert FA.trenne_kreise(adj, [1.0, 0.0, 0.0]) == []


def test_einfacher_ungerader_kreis_kuerzt_an_der_sehne():
    # Weg 0-1-2-3-4 mit Sehne 0-2: es bleibt das Dreieck 012 (ungerade Hälfte)
    adj = adj_aus_kanten(5, [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4), (0, 2)])
    assert sorted(FA.einfacher_ungerader_kreis(adj, [0, 1, 2, 3, 4])) == [0, 1, 2]


def test_radtrennung_findet_die_nabe():
    rad = adj_aus_kanten(6, [(i, (i + 1) % 5) for i in range(5)] + [(i, 5) for i in range(5)])
    x = [0.4] * 5 + [0.2]                      # Dreiecke: 0,4 + 0,4 + 0,2 = 1; Rad: 5·0,4 + 2·0,2 = 2,4 > 2
    gefunden = FA.trenne_raeder(rad, x)
    assert (5, (0, 1, 2, 3, 4)) in [(h, tuple(sorted(k))) for h, k in gefunden]
    assert FA.trenne_raeder(rad, [1.0, 0, 1.0, 0, 0, 0]) == []


def test_familien_ungleichung_je_art():
    assert L.familien_ungleichung(4, "rad", (3, (0, 1, 2))) == ((1, 1, 1, 1), 1)
    assert L.familien_ungleichung(3, "kreis", (0, 1, 2)) == ((1, 1, 1), 1)
    assert L.familien_ungleichung(7, "antiloch", range(7)) == ((1,) * 7, 2)
    with pytest.raises(ValueError):
        L.familien_ungleichung(3, "kamm", ())


def test_leiter_fuenfeck_mit_zusatzknoten(rad_fehlend):
    """Von Hand: Cliquen 5/2, mit dem Fünfeck 01234 noch 7/3 (x = ⅓, ⅓, ⅓, ⅔, ⅓, ⅓)."""
    werte = L.leiter([1] * 6, rad_fehlend)
    assert werte["cliquen"][0] == pytest.approx(2.5)
    assert werte["kreise"][0] == pytest.approx(7 / 3)
    zeuge = [F(1, 3), F(1, 3), F(1, 3), F(2, 3), F(1, 3), F(1, 3)]
    cl = L.cliquenzeilen(6, G.maximale_cliquen(rad_fehlend)) + [S.zeile(6, range(5), 2)]
    assert sum(zeuge) == F(7, 3) and all(S.wert(a, zeuge) <= b for a, b in cl)


# ------------------------------------------------------------------------------------------------ LP und exakte Nachprüfung

def test_facetten_zertifikat_dreieck_und_ablehnung():
    kanten = [(0, 1), (0, 2), (1, 2)]
    u = LP.facetten_zertifikat((1, 1, 1), 1, kanten)
    assert u == {0: F(1, 2), 1: F(1, 2), 2: F(1, 2)}
    assert LP.facetten_zertifikat((1, 1, 1), 0, kanten) is None


def test_ueberdeckungswert_ist_der_lp_wert(dreieck):
    _, zeilen = dreieck
    assert LP.ueberdeckungswert((1, 1, 1), [(0, 1), (0, 2), (1, 2)])[0] == pytest.approx(1.5)
    assert LP.loese([1, 1, 1], zeilen)[0] == pytest.approx(1.5)


def test_dualbeweis(dreieck):
    _, zeilen = dreieck
    y = {0: F(1, 2), 1: F(1, 2), 2: F(1, 2)}
    assert LP.pruefe_dualbeweis([1, 1, 1], zeilen, y) == F(3, 2)
    assert LP.pruefe_dualbeweis([1, 1, 1], zeilen + [((1, 1, 1), 1)], {3: F(1)}) == 1
    with pytest.raises(ValueError):
        LP.pruefe_dualbeweis([1, 1, 1], zeilen, {0: F(1)})              # Spalte c ungedeckt
    with pytest.raises(ValueError):
        LP.pruefe_dualbeweis([1, 1, 1], zeilen, {0: F(-1)})
    assert LP.dualbeweis([1, 1, 1], zeilen + [((1, 1, 1), 1)], 1) is not None
    assert LP.dualbeweis([1, 1, 1], zeilen, 1) is None                   # das Kanten-LP erreicht 3/2


def test_erfuellt(dreieck):
    _, zeilen = dreieck
    assert LP.erfuellt(zeilen, [0.5] * 3) and not LP.erfuellt(zeilen, [1, 1, 0])
    assert not LP.erfuellt(zeilen, [-0.1, 0, 0])


# ------------------------------------------------------------------------------------------------ Trennung

def test_trennung_findet_am_dreieck_den_schnitt(dreieck):
    _, zeilen = dreieck
    t = T.trenne_runde([0.5] * 3, zeilen, 10.0)
    assert t.status == "verletzt" and (t.alpha, t.beta) == ((1, 1, 1), 1)


def test_trennung_meldet_bei_ganzzahliger_loesung_keinen(dreieck):
    _, zeilen = dreieck
    assert T.trenne_runde([1.0, 0.0, 0.0], zeilen, 10.0).status == "keiner"


def test_exakter_schnitt_rundet_die_multiplikatoren():
    u, alpha, beta = T.exakter_schnitt([0.4999999999, 0.5000000001, 0.5, 1e-9], [((1, 1, 0), 1), ((0, 1, 1), 1), ((1, 0, 1), 1),
                                                                                  ((1, 1, 1), 1)])
    assert u == {0: F(1, 2), 1: F(1, 2), 2: F(1, 2)} and (alpha, beta) == ((1, 1, 1), 1)


def test_programm_hat_die_beschriebene_form(dreieck):
    _, zeilen = dreieck
    ziel, neben, rechts, ganz, oben = T.baue_programm([0.5, 0.0, 0.5], zeilen, 1e-4)
    assert len(ziel) == 3 + 2 + 1                      # u, alpha nur für x > 0, beta
    assert list(ziel) == [1e-4] * 3 + [-0.5, -0.5, 1.0]
    assert list(ganz) == [0] * 3 + [1] * 3 and rechts[-1] == pytest.approx(0.999)
    assert list(oben[:3]) == [0.999] * 3


def test_suche_am_dreieck_schliesst_mit_einem_schnitt(dreieck):
    _, zeilen = dreieck
    s = T.suche_runde([1, 1, 1], zeilen, 1, budget=10, je_programm=5)
    assert s.status == T.GESCHLOSSEN and len(s.schritte) == 1 and s.wert_ende == pytest.approx(1)
    assert s.wert_start == pytest.approx(1.5)


def test_suche_ohne_luecke_ruft_kein_programm(monkeypatch, dreieck):
    _, zeilen = dreieck
    monkeypatch.setattr(T, "trenne_runde", lambda *a, **k: (_ for _ in ()).throw(AssertionError("nicht nötig")))
    s = T.suche_runde([1, 1, 1], zeilen + [((1, 1, 1), 1)], 1, budget=10, je_programm=5)
    assert s.status == T.KEINE_LUECKE and s.schritte == ()


def test_suche_ohne_zeit_oder_schritte_ist_nicht_bestimmt(dreieck):
    _, zeilen = dreieck
    s = T.suche_runde([1, 1, 1], zeilen, 1, budget=0.0, je_programm=5)
    assert s.status == T.NICHT_BESTIMMT and s.grund == "zeit" and s.wert_ende == pytest.approx(1.5)
    s = T.suche_runde([1, 1, 1], zeilen, 1, budget=10, je_programm=5, max_schritte=0)
    assert s.status == T.NICHT_BESTIMMT and s.grund == "schritte"


def test_suche_mit_offenem_loeser_ist_nicht_bestimmt(monkeypatch, dreieck):
    _, zeilen = dreieck
    monkeypatch.setattr(T, "trenne_runde", lambda *a, **k: T.Trennung("offen"))
    s = T.suche_runde([1, 1, 1], zeilen, 1, budget=10, je_programm=5)
    assert s.status == T.NICHT_BESTIMMT and s.wert_ende == pytest.approx(1.5)


def test_suche_mit_bewiesener_luecke(monkeypatch, dreieck):
    _, zeilen = dreieck
    monkeypatch.setattr(T, "trenne_runde", lambda *a, **k: T.Trennung("keiner"))
    assert T.suche_runde([1, 1, 1], zeilen, 1, budget=10, je_programm=5).status == T.OFFEN_BEWIESEN


class _Res:
    def __init__(self, status, x, fun):
        self.status, self.x, self.fun = status, x, fun


def test_keiner_verletzt_erst_nach_dem_lauf_ohne_strafe(monkeypatch, dreieck):
    """Findet der Lauf mit Strafe nichts, muss ein Lauf ohne Strafe folgen; nur dessen Optimalität zählt."""
    _, zeilen = dreieck
    gesehen = []

    def lauf(x, z, strafe, grenze):
        gesehen.append(strafe)
        if strafe > 0:
            return _Res(0, [0.0] * 3 + [0.0] * 4, 0.0)
        return _Res(0, [0.5] * 3 + [1.0, 1.0, 1.0, 1.0], -0.5)

    monkeypatch.setattr(T, "_ein_lauf", lauf)
    t = T.trenne_runde([0.5] * 3, zeilen, 10.0)
    assert gesehen == [T.STRAFE, 0.0] and t.status == "verletzt" and t.alpha == (1, 1, 1)


def test_zeitgrenze_des_programms_ergibt_offen(monkeypatch, dreieck):
    _, zeilen = dreieck
    monkeypatch.setattr(T, "_ein_lauf", lambda *a: _Res(1, None, None))
    assert T.trenne_runde([0.5] * 3, zeilen, 10.0).status == "offen"


# ------------------------------------------------------------------------------------------------ Graph mit 13 Knoten

def test_basis_besteht_aus_cliquen_und_gibt_die_folge():
    for laenge, summe in ((9, F(5, 2)), (10, F(8, 3)), (11, F(14, 5))):
        assert all(G.ist_clique(Z.ADJ, G.maske(c)) for c in Z.BASIS[laenge])
        assert sum(Z.BASIS[laenge].values()) == summe < 3
        for start in range(13):
            alpha, beta = Z.runde1_schnitt(laenge, start)
            assert beta == 2 and all(alpha[v] >= 1 for v in Z.folge(laenge, start))


def test_die_cliquen_fuer_neun_knoten_von_hand():
    erwartet = [(0, 2, 4, 6), (0, 3, 7, 9), (1, 3, 5, 7), (1, 5, 8, 11), (2, 4, 6, 8)]
    assert sorted(Z.BASIS[9]) == erwartet and set(Z.BASIS[9].values()) == {F(1, 2)}
    assert all(sum(v in c for c in erwartet) >= 2 for v in range(9))


def test_summe_der_verschiebungen():
    h, rechts = Z.summe_der_verschiebungen(9, 13)
    assert h == (9,) * 13 and rechts == 26
    assert Z.schranke_aus_summe(h, rechts) == (9, 2)
    h, rechts = Z.summe_der_verschiebungen(9, 1)
    assert min(h) == 0 and Z.schranke_aus_summe(h, rechts) == (0, None)
    h, rechts = Z.summe_der_verschiebungen(9, 12)                   # Knoten 8..11 fehlen je viermal: mindestens 8
    assert min(h) == 8 and Z.schranke_aus_summe(h, rechts) == (8, 3)
    with pytest.raises(ValueError):
        Z.summe_der_verschiebungen(9, 14)
    with pytest.raises(ValueError):
        Z.summe_der_verschiebungen(9, 0)


def test_welche_anzahl_je_laenge_genuegt():
    """Länge 9 braucht alle 13 Verschiebungen, Länge 10 ab 10, Länge 11 ab 7 (wegen x >= 0 genügt ein Mindestvorkommen)."""
    ab = {}
    for laenge in Z.LAENGEN:
        gut = [m for m in range(1, 14) if (s := Z.schranke_aus_summe(*Z.summe_der_verschiebungen(laenge, m))[1]) is not None and s <= 2]
        ab[laenge] = gut
    assert ab == {9: [13], 10: [10, 11, 12, 13], 11: [7, 8, 9, 10, 11, 12, 13]}


def test_zweite_runde():
    assert Z.zweite_runde(9, 13) == ((1,) * 13, 2)
    assert Z.zweite_runde(9, 1) is None
    alpha, beta = Z.zweite_runde(11, 7)
    assert beta == 2 and all(c >= 1 for c in alpha)


def test_faelle_des_beweises():
    assert Z.zeuge_uebersteht(F(1, 6)) and Z.zeuge_uebersteht(F(2, 11))
    assert not Z.zeuge_uebersteht(F(1, 5))                           # 11/5 > 2 im Fall k >= 2
    assert not Z.zeuge_uebersteht(F(1, 4))
    assert "ab 7" in Z.faelle(F(1, 6))[3][1] and "ab 6" in Z.faelle(F(2, 11))[3][1]


# ------------------------------------------------------------------------------------------------ Handbeispiele

def test_alle_handfaelle_haben_passende_gewichte_und_lagen():
    for name, fall in B.HANDFAELLE.items():
        s = B.startbeschreibung(fall)
        assert len(fall.loesung) <= len(s.zeilen) <= 8, name
        assert set(fall.loesung) <= set(B.MULTIPLIKATOREN)
        assert len(fall.bild.lage) == fall.bild.n
        assert all(0 <= v <= 1 for p in s.punkte for v in p)


def test_lp_ecke_dreieck_und_fuenfeck_matching():
    s = B.startbeschreibung(B.HANDFAELLE["dreieck_kanten"])
    assert B.lp_ecke(s) == (F(1, 2),) * 3
    s = B.startbeschreibung(B.HANDFAELLE["fuenfeck_grade"])
    ecke = B.lp_ecke(s)
    assert sum(ecke) == 3                                            # ein perfektes Matching oder 5/2 + 1/2
