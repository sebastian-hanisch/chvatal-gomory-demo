"""Die kopierten Module stimmen bis auf das Präfix mit ihrer Quelle überein (übersprungen, wenn die Quelle nicht daneben liegt)."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
KOPIEN = [("cvg_rng.py", "ganzzahlige-ecken-demo/gze_rng.py", "gze_"), ("cvg_konflikt.py", "ganzzahlige-ecken-demo/gze_konflikt.py", "gze_"),
          ("cvg_dd.py", "ganzzahlige-ecken-demo/gze_dd.py", "gze_"), ("modul_frisch.py", "taktik-muster-demo/modul_frisch.py", None)]


@pytest.mark.parametrize("kopie, quelle, praefix", KOPIEN)
def test_kopie_stimmt_mit_der_quelle_ueberein_falls_vorhanden(kopie, quelle, praefix):
    pfad = ROOT.parent / quelle
    if not pfad.exists():
        pytest.skip("Quelle liegt nicht neben dem Repo")
    erwartet = pfad.read_text(encoding="utf-8")
    text = (ROOT / kopie).read_text(encoding="utf-8")
    if praefix:
        kopf, text = text.split("\n", 1)
        assert kopf.startswith("# Kopie aus " + quelle), "Herkunft fehlt im Modulkopf"
        erwartet = erwartet.replace(praefix, "cvg_")
    assert text == erwartet


def test_der_generator_liefert_die_bekannte_folge():
    from cvg_rng import SplitMix64

    assert SplitMix64(0).next_u64() == 0xE220A8397B1DCDAF
