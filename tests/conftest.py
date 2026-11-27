"""Gemeinsame Fixtures und Hilfen. Die Mini-Instanzen werden von Hand nachgerechnet (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from cvg_konflikt import adj_aus_kanten  # noqa: E402
from cvg_schnitt import zeile  # noqa: E402


@pytest.fixture
def dreieck():
    """Dreieck abc mit den drei Kantenzeilen x_a + x_b <= 1 (Knoten a=0, b=1, c=2)."""
    return adj_aus_kanten(3, [(0, 1), (0, 2), (1, 2)]), [zeile(3, e) for e in ((0, 1), (0, 2), (1, 2))]


@pytest.fixture
def rad_fehlend():
    """Fünfeck 0-1-2-3-4, Knoten 5 an 0, 1 und 2. Von Hand: maximale Cliquen 015, 04, 125, 23, 34; größte stabile Menge 2."""
    return adj_aus_kanten(6, [(0, 1), (0, 4), (0, 5), (1, 2), (1, 5), (2, 3), (2, 5), (3, 4)])


def zufallsgraph(n: int, p: int, seed: int):
    from cvg_konflikt import gnp

    return gnp(n, p, seed).adj
