"""Die Handbeispiele: Graphen mit festen Knotenlagen, ihre Startbeschreibungen und die Zertifikate, die man von Hand findet."""

import itertools
import math
from dataclasses import dataclass
from fractions import Fraction

import cvg_dd
from cvg_graphen import maximale_cliquen
from cvg_konflikt import adj_aus_kanten
from cvg_schnitt import matching_zeilen, zeile

BUCHSTABEN = "abcdefghij"


def kreis_lage(n: int, radius: float = 1.0, mitte=(0.0, 0.0), start: float = 90.0) -> list:
    """Knoten gleichmäßig auf einem Kreis, Knoten 0 oben, im Uhrzeigersinn."""
    return [(mitte[0] + radius * math.cos(math.radians(start - 360.0 * i / n)),
             mitte[1] + radius * math.sin(math.radians(start - 360.0 * i / n))) for i in range(n)] if n else []


@dataclass(frozen=True)
class Graphbild:
    name: str
    n: int
    kanten: tuple
    lage: tuple
    namen: tuple        # Knotennamen

    @property
    def adj(self) -> tuple:
        return adj_aus_kanten(self.n, self.kanten)


def _bild(name, n, kanten_, lage, namen=None):
    return Graphbild(name, n, tuple(sorted(tuple(sorted(e)) for e in kanten_)), tuple(lage),
                     tuple(namen if namen else (str(i) for i in range(n))))


DREIECK = _bild("Dreieck", 3, [(0, 1), (1, 2), (0, 2)], kreis_lage(3), "abc")
K4 = _bild("K4", 4, itertools.combinations(range(4), 2), kreis_lage(4, start=135.0), "abcd")
FUENFECK = _bild("Fünfeck mit Ausgangskante", 6, [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4), (4, 5)],
                 kreis_lage(5, start=108.0) + [(-2.1, 0.0)])          # Knoten 4 links, die Ausgangskante zeigt nach außen
# Knoten 0 bis 4 ein Fünfeck, Knoten 5 an 0, 1 und 2: ein Rad mit fehlenden Speichen
RAD = _bild("Fünfeck mit Zusatzknoten", 6, [(0, 1), (1, 2), (2, 3), (3, 4), (0, 4), (0, 5), (1, 5), (2, 5)],
            kreis_lage(5) + [(0.45, 0.2)])
BRUECKE = _bild("zwei Dreiecke mit Brücke", 6, [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (2, 3)],
                [(-2.0, 0.8), (-2.0, -0.8), (-0.8, 0.0), (0.8, 0.0), (2.0, 0.8), (2.0, -0.8)])
K5 = _bild("K5", 5, itertools.combinations(range(5), 2), kreis_lage(5))
PETERSEN = _bild("Petersen-Graph", 10,
                 [(i, (i + 1) % 5) for i in range(5)] + [(i, i + 5) for i in range(5)] + [(5 + i, 5 + (i + 2) % 5) for i in range(5)],
                 kreis_lage(5, 2.0) + kreis_lage(5, 0.9))
SECHSECK = _bild("Sechseck (bipartit)", 6, [(i, (i + 1) % 6) for i in range(6)], kreis_lage(6))


# ------------------------------------------------------------------------------------------------ Experiment "Selbst abrunden"

@dataclass(frozen=True)
class Handfall:
    titel: str
    bild: Graphbild
    start: str            # "kanten", "cliquen" oder "grade"
    loesung: tuple        # Multiplikatoren als Text je Zeile: das Zertifikat von Hand


START_TEXT = {"kanten": "Kantenzeilen", "cliquen": "Cliquenzeilen (eine je maximaler Clique)", "grade": "Gradzeilen (Matching)"}

HANDFAELLE = {
    "dreieck_kanten": Handfall("Dreieck, Kantenzeilen", DREIECK, "kanten", ("1/2",) * 3),
    "dreieck_cliquen": Handfall("Dreieck, Cliquenzeilen", DREIECK, "cliquen", ("0",)),
    "k4_kanten": Handfall("K4, Kantenzeilen", K4, "kanten", ("1/2", "1/2", "0", "1/2", "0", "0")),
    "k4_cliquen": Handfall("K4, Cliquenzeilen", K4, "cliquen", ("0",)),
    "fuenfeck_grade": Handfall("Fünfeck mit Ausgangskante, Gradzeilen (Matching)", FUENFECK, "grade", ("1/2",) * 5 + ("0",)),
    "fuenfeck_kanten": Handfall("Fünfeck mit Ausgangskante, Kantenzeilen", FUENFECK, "kanten", ("1/2",) * 5 + ("0",)),
    "rad_cliquen": Handfall("Fünfeck mit Zusatzknoten, Cliquenzeilen", RAD, "cliquen", ("1/2",) * 5),
    # die Kanten 01, 04, 12, 23, 34: das äußere Fünfeck
    "rad_kanten": Handfall("Fünfeck mit Zusatzknoten, Kantenzeilen", RAD, "kanten", ("1/2", "1/2", "0", "1/2", "0", "1/2", "0", "1/2")),
}


@dataclass(frozen=True)
class Startbeschreibung:
    zeilen: tuple         # ((a, b), ...)
    zeilennamen: tuple    # "x_a + x_b ≤ 1"
    variablen: tuple      # Namen der Variablen
    punkte: tuple         # alle ganzzahligen Punkte (0/1), die die Beschreibung meint


def startbeschreibung(fall: Handfall) -> Startbeschreibung:
    """Zeilen, Variablen und alle ganzzahligen Punkte (stabile Mengen bzw. Matchings) eines Handfalls."""
    g = fall.bild
    if fall.start == "grade":
        zeilen = matching_zeilen(g.n, g.kanten)
        variablen = tuple(f"x_{g.namen[a]}{g.namen[b]}" for a, b in g.kanten)
        namen = tuple(f"Knoten {g.namen[v]}" for v in range(g.n))
        punkte = tuple(tuple(m >> i & 1 for i in range(len(g.kanten))) for m in range(1 << len(g.kanten))
                       if all(sum(m >> i & 1 for i, e in enumerate(g.kanten) if v in e) <= 1 for v in range(g.n)))
    else:
        mengen = list(g.kanten) if fall.start == "kanten" else list(maximale_cliquen(g.adj))
        zeilen = [zeile(g.n, m) for m in mengen]
        variablen = tuple(f"x_{n}" for n in g.namen)
        wort = "Kante" if fall.start == "kanten" else "Clique"
        namen = tuple(f"{wort} " + "".join(g.namen[v] for v in m) for m in mengen)
        punkte = tuple(tuple(m >> v & 1 for v in range(g.n)) for m in range(1 << g.n)
                       if not any(m >> a & 1 and m >> b & 1 for a, b in g.kanten))
    return Startbeschreibung(tuple(zeilen), namen, variablen, punkte)


def lp_ecke(beschreibung: Startbeschreibung) -> tuple:
    """Eine Ecke der Startbeschreibung mit größter Summe aller Variablen, exakt aus allen Ecken; Regel bei Gleichstand: zuerst eine
    gebrochene, darunter die größte in der Reihenfolge der Koordinaten."""
    ecken_ = cvg_dd.ecken(len(beschreibung.variablen), beschreibung.zeilen)
    beste = max(sum(e) for e in ecken_)
    kandidaten = [e for e in ecken_ if sum(e) == beste]
    return max(kandidaten, key=lambda e: (any(v.denominator > 1 for v in e), e))


MULTIPLIKATOREN = ("0", "1/6", "1/4", "1/3", "1/2", "2/3")


def als_brueche(texte) -> list:
    return [Fraction(t) for t in texte]


# ------------------------------------------------------------------------------------------------ Experiment "Matching"

MATCHINGGRAPHEN = {
    "fuenfeck": (FUENFECK, (0, 1, 2, 3, 4)),
    "bruecke": (BRUECKE, (0, 1, 2)),
    "k5": (K5, (0, 1, 2, 3, 4)),
    "petersen": (PETERSEN, (0, 1, 2, 3, 4)),
    "sechseck": (SECHSECK, (0, 1, 2)),
}
