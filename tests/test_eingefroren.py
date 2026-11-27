"""Die eingefrorenen Dateien: --check beider Erzeugerskripte (neu rechnen, jedes Zertifikat exakt prüfen)."""

import copy

import cvg_katalog as K
import cvg_make_katalog as MK
import cvg_make_messungen as MM
import cvg_messung as M


def test_katalog_check(capsys):
    assert MK.check() == 0, capsys.readouterr().out


def test_messungen_check(capsys):
    assert MM.check() == 0, capsys.readouterr().out


def test_ein_verfaelschtes_zertifikat_faellt_auf():
    e = copy.deepcopy(K.lade()["klein"][0])
    erste = next(iter(e["facetten"][0]["u"]))
    e["facetten"][0]["u"][erste] = "1/7"
    assert K.pruefe_klein(e)


def test_ein_verfaelschter_dualbeweis_faellt_auf():
    e = copy.deepcopy(K.lade()["zwanzig"][0])
    e["schnitte"][0]["y"] = "0"
    assert K.pruefe_zwanzig(e, mit_lp=False)


def test_ein_verfaelschter_schnitt_der_messung_faellt_auf():
    daten = M.lade()
    e = copy.deepcopy(next(x for x in daten["raster"] if x["schnitte"]))
    e["schnitte"] = e["schnitte"][:-1]
    assert M.pruefe_eintrag(e, daten["p"])


def test_kanonische_form_ist_unabhaengig_von_der_nummerierung():
    import itertools

    import numpy as np

    kanten = MK._kantenliste(4)
    pfad = [(0, 1), (1, 2), (2, 3)]
    masken = []
    for p in itertools.permutations(range(4)):
        masken.append(sum(1 << kanten.index(tuple(sorted((p[a], p[b])))) for a, b in pfad))
    assert len(set(MK.kanonisch(4, np.array(masken)).tolist())) == 1
    assert [len(v) for v in MK.graphen_bis_isomorphie(5).values()] == [1, 2, 4, 11, 34]
