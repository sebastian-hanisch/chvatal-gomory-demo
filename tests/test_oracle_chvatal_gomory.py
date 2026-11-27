"""Orakel: dieselben Größen auf einem anderen Rechenweg (networkx, Aufzählung aller Multiplikatoren, exakte Ecken, Lemma mit allen
kleinen Zielvektoren). Nur hier wird networkx importiert."""

import itertools
from fractions import Fraction as F

import numpy as np
import pytest

nx = pytest.importorskip("networkx")

import cvg_dd as D  # noqa: E402
import cvg_graphen as G  # noqa: E402
import cvg_katalog as K  # noqa: E402
import cvg_leiter as L  # noqa: E402
import cvg_lp as LP  # noqa: E402
import cvg_schnitt as S  # noqa: E402
import cvg_trennung as T  # noqa: E402
import cvg_zeuge as Z  # noqa: E402
from cvg_konflikt import adj_aus_kanten, gnp, kanten  # noqa: E402
from cvg_rng import SplitMix64  # noqa: E402


def als_nx(adj):
    g = nx.Graph()
    g.add_nodes_from(range(len(adj)))
    g.add_edges_from(kanten(adj))
    return g


def groesstes_gewicht_nx(adj, w) -> int:
    """Größtes Gewicht einer stabilen Menge = größte gewichtete Clique im Komplement (networkx)."""
    h = nx.complement(als_nx(adj))
    for v in h.nodes:
        h.nodes[v]["weight"] = int(w[v])
    return nx.max_weight_clique(h)[1]


def zufaellig(n, p, seed):
    return gnp(n, p, seed).adj


@pytest.mark.parametrize("seed", range(0, 120, 7))
def test_maximale_cliquen_gegen_networkx(seed):
    adj = zufaellig(4 + seed % 12, 300 + 100 * (seed % 5), seed)
    erwartet = sorted(tuple(sorted(c)) for c in nx.find_cliques(als_nx(adj)))
    assert list(G.maximale_cliquen(adj)) == erwartet


def test_stabile_mengen_und_gewicht_gegen_aufzaehlung():
    for seed in range(40):
        inst = gnp(3 + seed % 9, 400, 900 + seed)
        n = len(inst.adj)
        alle = [m for m in range(1 << n) if not any(m >> a & 1 and m >> b & 1 for a, b in kanten(inst.adj))]
        assert sorted(G.stabile_mengen(inst.adj)) == alle
        best = max(sum(inst.werte[v] for v in range(n) if m >> v & 1) for m in alle)
        wert_, menge = G.groesstes_gewicht(inst.adj, inst.werte)
        assert wert_ == best and menge in alle and sum(inst.werte[v] for v in range(n) if menge >> v & 1) == best
        assert groesstes_gewicht_nx(inst.adj, inst.werte) == best


def test_induzierte_kreise_gegen_networkx():
    for seed in range(60):
        adj = zufaellig(7 + seed % 5, 450, 1000 + seed)
        for g_adj in (adj, G.komplement(adj)):
            meine = sorted(sorted(k) for k in G.induzierte_kreise(g_adj, 5, True))
            nx_kreise = sorted(sorted(c) for c in nx.chordless_cycles(als_nx(g_adj)) if len(c) >= 5 and len(c) % 2 == 1)
            assert meine == nx_kreise, seed


def test_kreistrennung_gleich_allen_ungeraden_kreisen():
    """Der LP-Wert mit getrennten Kreisen ist der LP-Wert mit allen ungeraden Kreisen (aufgezählt mit networkx)."""
    for seed in range(40):
        inst = gnp(8 + seed % 3, 400, 1100 + seed)
        n = len(inst.adj)
        cl = G.maximale_cliquen(inst.adj)
        w = [1] * n if seed % 2 else list(inst.werte)
        kreise = {frozenset(c) for c in nx.simple_cycles(als_nx(inst.adj)) if len(c) % 2 == 1}
        alle = L.cliquenzeilen(n, cl) + [S.zeile(n, c, (len(c) - 1) // 2) for c in sorted(kreise, key=sorted)]
        assert L.lade_bis_fertig(w, inst.adj, cl, ("kreis",))[0] == pytest.approx(LP.loese(w, alle)[0], abs=1e-6), seed


# ------------------------------------------------------------------------------------------------ Aufzählung der Multiplikatoren

def schnitte_der_aufzaehlung(zeilen, q: int) -> tuple:
    """Alle Schnitte mit u in {0, 1/q, ..., (q-1)/q}^m, ganzzahlig mit numpy: (alpha je Zeile, beta je Zeile)."""
    a = np.array([z[0] for z in zeilen], dtype=np.int64)
    b = np.array([z[1] for z in zeilen], dtype=np.int64)
    u = np.array(list(itertools.product(range(q), repeat=len(zeilen))), dtype=np.int64)
    return (u @ a) // q, (u @ b) // q


def test_jede_facette_kleiner_graphen_entsteht_schon_durch_aufzaehlen():
    """Unabhängig vom LP: für jede Facette der Graphen mit höchstens 10 maximalen Cliquen findet die Aufzählung der Nenner 2 und 3
    einen Schnitt, der mindestens so stark ist."""
    daten = K.lade()["klein"]
    geprueft = 0
    for e in daten:
        adj = adj_aus_kanten(e["n"], e["kanten"])
        cl = G.maximale_cliquen(adj)
        if len(cl) > 10:
            continue
        zeilen = L.cliquenzeilen(e["n"], cl)
        gefunden = [schnitte_der_aufzaehlung(zeilen, q) for q in (2, 3)]
        for f in e["facetten"]:
            ok = any(bool(np.any(np.all(alpha >= np.array(f["a"]), axis=1) & (beta <= f["b"]))) for alpha, beta in gefunden)
            assert ok, (e["kanten"], f)
            geprueft += 1
    assert geprueft >= 190


def test_eine_runde_ueber_den_kanten_ist_kanten_und_ungerade_kreise_exakt():
    """Alle Graphen mit 5 Knoten ohne isolierte Knoten und höchstens 6 Kanten: jeder Schnitt mit Nennern 2 und 3 gilt auf jeder Ecke
    des Polytops aus Kanten und ungeraden Kreisen (exakt, ohne LP-Löser)."""
    paare = list(itertools.combinations(range(5), 2))
    graphen = schnitte = 0
    for maske in range(1, 1 << len(paare)):
        e = [paare[i] for i in range(len(paare)) if maske >> i & 1]
        if len(e) > 6 or {v for k in e for v in k} != set(range(5)):
            continue
        adj = adj_aus_kanten(5, e)
        kanten_z = [S.zeile(5, k) for k in e]
        kreise = [S.zeile(5, [v for v in range(5) if m >> v & 1], (bin(m).count("1") - 1) // 2) for m in G.alle_ungeraden_kreise(adj)]
        ecken = D.ecken(5, kanten_z + kreise)
        for q in (2, 3):
            alpha, beta = schnitte_der_aufzaehlung(kanten_z, q)
            for al, be in {(tuple(int(v) for v in x), int(y)) for x, y in zip(alpha, beta)}:
                assert all(S.wert(al, x) <= be for x in ecken), (e, al, be)
                schnitte += 1
        graphen += 1
    assert graphen > 60 and schnitte > 1000


def test_erster_abschluss_ueber_den_kanten_erreicht_die_kreise():
    """Auf Zufallsgraphen senkt die Suche über den Kantenzeilen den LP-Wert bis auf den Wert mit allen ungeraden Kreisen, und jeder
    gefundene Schnitt gilt auf jeder Ecke dieses Polytops."""
    zahl = 0
    for seed in range(14):
        inst = gnp(6 + seed % 4, 500, 1200 + seed)
        n = len(inst.adj)
        if any(a == 0 for a in inst.adj):
            continue
        w = [1] * n
        kz = [S.zeile(n, k) for k in kanten(inst.adj)]
        kreise = [S.zeile(n, [v for v in range(n) if m >> v & 1], (bin(m).count("1") - 1) // 2) for m in G.alle_ungeraden_kreise(inst.adj)]
        ziel = LP.loese(w, kz + kreise)[0]
        s = T.suche_runde(w, kz, ziel, budget=30.0, je_programm=10.0)
        assert s.status in (T.GESCHLOSSEN, T.KEINE_LUECKE), (seed, s.status)
        assert s.wert_ende == pytest.approx(ziel, abs=1e-5)
        ecken = D.ecken(n, kz + kreise)
        for t in s.schritte:
            assert all(S.wert(t.alpha, x) <= t.beta for x in ecken)
        zahl += 1
    assert zahl >= 8


# ------------------------------------------------------------------------------------------------ Cliquen: Lemma ohne den Beweis

def _kk(k):
    return [S.zeile(k, e) for e in itertools.combinations(range(k), 2)]


@pytest.mark.parametrize("k", [4, 5, 6])
def test_ein_drittel_uebersteht_runde_1_alle_kleinen_zielvektoren(k):
    """Für jedes c mit Einträgen 0 bis 4: c·(1/3) <= floor(max c·y über das Kantenpolytop), exakt über dessen Ecken."""
    ecken = D.ecken(k, _kk(k))
    x = F(1, 3)
    for c in itertools.combinations_with_replacement(range(5), k):         # symmetrisch: Multimengen genügen
        h = max(S.wert(c, e) for e in ecken)
        assert x * sum(c) <= h.numerator // h.denominator, c


def test_ein_fuenftel_uebersteht_runde_2_auf_k6():
    """Nach Runde 1 ist das Polytop von K6 das aus Kanten und ungeraden Kreisen (erste Runde über den Kanten). Für jedes c mit
    Einträgen 0 bis 3 übersteht x = 1/5 den Schnitt c der zweiten Runde; damit ist max x(K6) nach zwei Runden mindestens 6/5."""
    adj = G.komplement((0,) * 6)
    zeilen = _kk(6) + [S.zeile(6, [v for v in range(6) if m >> v & 1], (bin(m).count("1") - 1) // 2) for m in G.alle_ungeraden_kreise(adj)]
    ecken = D.ecken(6, zeilen)
    for c in itertools.combinations_with_replacement(range(4), 6):
        h = max(S.wert(c, e) for e in ecken)
        assert F(sum(c), 5) <= h.numerator // h.denominator, c
    # obere Schranke: die sechs Fünfercliquen (in Runde 2 enthalten) geben 6/5
    assert max(sum(x) for x in D.ecken(6, [S.zeile(6, s) for s in itertools.combinations(range(6), 5)])) == F(6, 5)


def test_untere_schranke_lemma_fuer_alle_kleinen_vektoren():
    """Der Rechenschritt des Beweises: floor(max(max c, s/m)) >= s/(2m-1) für alle c mit Einträgen 0 bis 6."""
    for m in (2, 3, 5, 9):
        k = min(2 * m, 12)
        for c in itertools.combinations_with_replacement(range(7), k):
            s = sum(c)
            if s:
                assert int(max(F(max(c)), F(s, m))) >= F(s, 2 * m - 1)


# ------------------------------------------------------------------------------------------------ Matching

def test_jede_ungerade_menge_aller_graphen_bis_sieben_knoten():
    """Alle 1.245 Graphen mit 2 bis 7 Knoten und mindestens einer Kante (networkx-Atlas), alle ungeraden Knotenmengen ab 3: die halben
    Gradzeilen geben exakt x(E[U]) <= (|U|-1)/2."""
    graphen = paare = 0
    for g in nx.graph_atlas_g():
        n = g.number_of_nodes()
        if not 2 <= n <= 7 or g.number_of_edges() == 0:
            continue
        graphen += 1
        ek = sorted(tuple(sorted(e)) for e in g.edges)
        zeilen = S.matching_zeilen(n, ek)
        for k in range(3, n + 1, 2):
            for U in itertools.combinations(range(n), k):
                alpha, beta, _, _ = S.cg_schnitt(zeilen, S.matching_multiplikatoren(n, U))
                menge = set(U)
                assert alpha == tuple(1 if a in menge and b in menge else 0 for a, b in ek) and beta == (k - 1) // 2
                paare += 1
    assert (graphen, paare) == (1245, 63887)


def test_matching_groesse_gegen_networkx():
    import cvg_beispiele as B
    import cvg_evaluation as E

    for name, (bild, _) in B.MATCHINGGRAPHEN.items():
        m = E.ergebnis_matching(name, range(bild.n))
        g = als_nx(bild.adj)
        assert m.ganz_optimum == len(nx.max_weight_matching(g, maxcardinality=True)), name
        assert m.bipartit == nx.is_bipartite(g), name


# ------------------------------------------------------------------------------------------------ Sammlung und Zertifikate

def _ist_perfekt_nx(g) -> bool:
    for h in (g, nx.complement(g)):
        if any(len(c) >= 5 and len(c) % 2 == 1 for c in nx.chordless_cycles(h)):
            return False
    return True


def test_die_147_graphen_sind_genau_die_nichtperfekten_des_atlas():
    atlas = [g for g in nx.graph_atlas_g() if 5 <= g.number_of_nodes() <= 7 and not _ist_perfekt_nx(g)]
    katalog = []
    for e in K.lade()["klein"]:
        g = nx.Graph()
        g.add_nodes_from(range(e["n"]))
        g.add_edges_from(e["kanten"])
        katalog.append(g)
    assert len(atlas) == len(katalog) == 147
    rest = list(atlas)
    for g in katalog:
        treffer = next(i for i, h in enumerate(rest) if g.number_of_nodes() == h.number_of_nodes()
                       and g.number_of_edges() == h.number_of_edges() and nx.is_isomorphic(g, h))
        rest.pop(treffer)
    assert not rest


def test_jeder_gespeicherte_schnitt_gegen_networkx():
    """Jeder Schnitt der Sammlung gilt für jede stabile Menge: das größte Gewicht alpha (networkx) ist höchstens beta."""
    zahl = 0
    for e in K.lade()["klein"]:
        for f in range(len(e["facetten"])):
            s = K.schnitt_klein(e, f)
            assert groesstes_gewicht_nx(s["adj"], s["alpha"]) <= s["beta"]
            zahl += 1
    for e in K.lade()["zwanzig"]:
        d = K.schnitte_zwanzig(e)
        for t in d["schnitte"]:
            assert groesstes_gewicht_nx(d["instanz"].adj, t["alpha"]) <= t["beta"]
            zahl += 1
        assert groesstes_gewicht_nx(d["instanz"].adj, d["instanz"].werte) == e["optimum"]
    assert zahl > 300


def test_zufaellige_schnitte_ueberstehen_den_zeugen_im_13er_graphen():
    """Eigenschaft statt Beweis: 3.000 zufällige Multiplikatoren; x = 1/6 und x = 2/11 erfüllen jeden Schnitt."""
    rng = SplitMix64(13)
    zeilen = Z.ZEILEN
    for _ in range(3000):
        nenner = 2 + rng.below(11)
        u = {}
        for _ in range(1 + rng.below(15)):
            u[rng.below(len(zeilen))] = F(1 + rng.below(nenner - 1), nenner)
        alpha, beta = S.schnitt_aus(zeilen, u)
        assert Z.ZEUGE_GROESSTER * sum(alpha) <= beta
        assert Z.ZEUGE * sum(alpha) <= beta


def test_der_zeuge_ueber_die_ecken_der_symmetrie_und_26_elftel():
    """Mit den 13 Schnitten zu 11 Knoten ist das größte x(V) höchstens 26/11 (LP); x = 2/11 erreicht das."""
    zeilen = list(Z.ZEILEN) + [Z.runde1_schnitt(11, s) for s in range(13)]
    wert_, _, _ = LP.loese([1] * 13, zeilen)
    assert wert_ == pytest.approx(26 / 11, abs=1e-9)
    assert LP.erfuellt(zeilen, [2 / 11] * 13)
    assert LP.pruefe_dualbeweis([1] * 13, zeilen, {39 + s: F(1, 11) for s in range(13)}) == F(26, 11)


def test_ganze_huelle_des_13er_graphen():
    import cvg_evaluation as E

    h = E.facetten13(vollstaendig=True)
    assert h["fehler"] == []
    assert (h["gesamt"], h["nichtnegativ"], h["cliquen"], h["eine_runde"]) == (92, 13, 39, 39)
    assert h["ausserhalb"] == [((1,) * 13, 2)]
    # zweiter Weg: das LP über den Cliquen erreicht 13/4 >= alpha + 1
    assert LP.ueberdeckungswert((1,) * 13, Z.CLIQUEN)[0] == pytest.approx(3.25)


def test_zwoelf_knoten_genuegen_auch():
    """Ohne Knoten 0 ist x(V) <= 2 wieder eine Facette außerhalb der ersten Runde (Überdeckung 3 = alpha + 1)."""
    paare = [tuple(v - 1 for v in range(1, 13) if m >> v & 1) for m in G.stabile_mengen(Z.ADJ) if not m & 1 and bin(m).count("1") == 2]
    punkte = [tuple(1 if v in p else 0 for v in range(12)) for p in paare]
    assert D.affiner_rang(punkte) == 11
    adj12 = adj_aus_kanten(12, [(a - 1, b - 1) for a, b in kanten(Z.ADJ) if a])
    cl = G.maximale_cliquen(adj12)
    assert LP.ueberdeckungswert((1,) * 12, cl)[0] == pytest.approx(3.0)
    assert LP.facetten_zertifikat((1,) * 12, 2, cl) is None


# ------------------------------------------------------------------------------------------------ Trennprogramm

def test_trennung_findet_was_die_aufzaehlung_findet():
    """Findet die Aufzählung (Nenner 2 bis 5) einen deutlich verletzten Schnitt, so meldet auch das Programm "verletzt";
    meldet es "keiner", findet auch die Aufzählung nichts. Als Zielvektoren dienen die Facetten der nichtperfekten Graphen."""
    treffer = keiner = 0
    for nummer, e in enumerate(K.lade()["klein"]):
        if nummer % 3:
            continue
        adj = adj_aus_kanten(e["n"], e["kanten"])
        cl = G.maximale_cliquen(adj)
        if len(cl) > 8:
            continue
        zeilen = L.cliquenzeilen(e["n"], cl)
        _, x, _ = LP.loese(e["facetten"][0]["a"], zeilen)
        beste = 0.0
        for q in (2, 3, 4, 5):
            alpha, beta = schnitte_der_aufzaehlung(zeilen, q)
            beste = max(beste, float(np.max(alpha @ x - beta)))
        t = T.trenne_runde(x, zeilen, 10.0)
        if beste > 1e-3:
            assert t.status == "verletzt", (nummer, beste, t.status)
            treffer += 1
        if t.status == "keiner":
            assert beste <= 1e-4, (nummer, beste)
            keiner += 1
        if t.status == "verletzt":
            assert groesstes_gewicht_nx(adj, t.alpha) <= t.beta
        # ganzzahlige Lösung: nichts zu trennen
        opt_menge = G.groesstes_gewicht(adj, e["facetten"][0]["a"])[1]
        assert T.trenne_runde([opt_menge >> v & 1 for v in range(e["n"])], zeilen, 10.0).status == "keiner"
    assert treffer >= 5
