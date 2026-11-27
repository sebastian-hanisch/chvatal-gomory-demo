"""Der Chvátal-Gomory-Schnitt und die Zertifikate, die man ohne Löser aufschreiben kann. Alles exakt mit Brüchen.

Zeilenform: P = {x >= 0 : a·x <= b für (a, b) in zeilen} mit ganzzahligen a und b. Ein Schnitt der ersten Runde entsteht aus
Multiplikatoren u >= 0: erst die Zeilen gewichtet addieren, dann die Koeffizienten und die rechte Seite abrunden.
"""

import itertools
from fractions import Fraction
from math import comb, floor


def zeile(n: int, knoten, rechts: int = 1) -> tuple:
    """Zeile x(knoten) <= rechts."""
    s = set(knoten)
    return tuple(1 if j in s else 0 for j in range(n)), rechts


def zeilen_der_mengen(n: int, mengen) -> list:
    return [zeile(n, m) for m in mengen]


def wert(a, x):
    """Linke Seite a·x."""
    return sum(c * v for c, v in zip(a, x) if c)


def gewichtete_summe(zeilen, u) -> tuple:
    """(u·A, u·b) als Brüche. u: ein Multiplikator je Zeile, alle >= 0."""
    u = [Fraction(v) for v in u]
    if len(u) != len(zeilen):
        raise ValueError("ein Multiplikator je Zeile")
    if any(v < 0 for v in u):
        raise ValueError("Multiplikatoren müssen >= 0 sein")
    if not zeilen:
        return (), Fraction(0)
    n = len(zeilen[0][0])
    links = [Fraction(0)] * n
    rechts = Fraction(0)
    for v, (a, b) in zip(u, zeilen):
        if v:
            for j, c in enumerate(a):
                if c:
                    links[j] += v * c
            rechts += v * b
    return tuple(links), rechts


def abrunden(links, rechts) -> tuple:
    """(floor(links), floor(rechts))."""
    return tuple(floor(v) for v in links), floor(rechts)


def cg_schnitt(zeilen, u) -> tuple:
    """CG-Schnitt floor(u A) x <= floor(u b). Rückgabe (alpha, beta, ungerundet links, ungerundet rechts)."""
    links, rechts = gewichtete_summe(zeilen, u)
    alpha, beta = abrunden(links, rechts)
    return alpha, beta, links, rechts


def als_liste(zeilen, multiplikatoren: dict) -> list:
    """Multiplikatoren als {Zeilennummer: Bruch} in eine Liste mit einem Eintrag je Zeile."""
    if any(not 0 <= i < len(zeilen) for i in multiplikatoren):
        raise ValueError("Multiplikator zu einer Zeile, die es nicht gibt")
    return [Fraction(multiplikatoren.get(i, 0)) for i in range(len(zeilen))]


def schnitt_aus(zeilen, multiplikatoren: dict) -> tuple:
    """(alpha, beta) zu dünn gespeicherten Multiplikatoren {Zeile: Bruch}."""
    alpha, beta, _, _ = cg_schnitt(zeilen, als_liste(zeilen, multiplikatoren))
    return alpha, beta


def ist_gueltig(alpha, beta, punkte) -> bool:
    """Erfüllt jeder der ganzzahligen Punkte die Ungleichung?"""
    return all(wert(alpha, p) <= beta for p in punkte)


def traegermaske(alpha) -> int:
    return sum(1 << j for j, c in enumerate(alpha) if c)


# ------------------------------------------------------------------------------------------------ Matching (Gradzeilen)

def matching_zeilen(n_knoten: int, kanten) -> list:
    """Je Knoten die Gradzeile: Summe der x_e über die Kanten am Knoten <= 1 (Variablen = Kanten)."""
    return [(tuple(1 if v in e else 0 for e in kanten), 1) for v in range(n_knoten)]


def matching_multiplikatoren(n_knoten: int, U) -> list:
    """1/2 auf der Gradzeile jedes Knotens in U, sonst 0."""
    U = set(U)
    if any(not 0 <= v < n_knoten for v in U):
        raise ValueError("Knoten außerhalb des Graphen")
    return [Fraction(1, 2) if v in U else Fraction(0) for v in range(n_knoten)]


def kanten_in_menge(kanten, U) -> tuple:
    """Indizes der Kanten mit beiden Enden in U."""
    U = set(U)
    return tuple(i for i, (a, b) in enumerate(kanten) if a in U and b in U)


def kanten_am_rand(kanten, U) -> tuple:
    """Indizes der Kanten mit genau einem Ende in U."""
    U = set(U)
    return tuple(i for i, (a, b) in enumerate(kanten) if (a in U) != (b in U))


# ------------------------------------------------------------------------------------------------ Cliquen aus Kantenzeilen

def cliquen_multiplikatoren(k: int, m: int) -> tuple:
    """Aus allen m-Cliquen einer k-Clique (m <= k <= 2m - 1) mit gleichem Gewicht 1/C(k-1, m-1) entsteht in einer Runde x(K) <= 1.
    Rückgabe: (Liste der m-Teilmengen, Multiplikator je Teilmenge)."""
    if not 2 <= m <= k <= 2 * m - 1:
        raise ValueError(f"k = {k} liegt außerhalb von {m} bis {2 * m - 1}")
    return list(itertools.combinations(range(k), m)), Fraction(1, comb(k - 1, m - 1))


def groesste_clique_nach(r: int) -> int:
    """Die größte Clique, deren Ungleichung nach r Runden aus den Kantenzeilen folgt: 2, 3, 5, 9, 17, ..."""
    return 2 ** r + 1


def cliquen_rang(k: int) -> int:
    """Kleinste Rundenzahl r mit k <= 2^r + 1, also die aufgerundete Zweierlogarithmus-Zahl von k - 1 (ab k = 2)."""
    if k < 2:
        raise ValueError("eine Clique hat mindestens 2 Knoten")
    return (k - 2).bit_length()


def punkt_nach_runden(r: int) -> Fraction:
    """Der Wert je Knoten der Clique, der r Runden aus den Kantenzeilen übersteht: 1/(2^r + 1)."""
    if r < 0:
        raise ValueError("r >= 0")
    return Fraction(1, 2 ** r + 1)


def max_summe_nach_runden(k: int, r: int) -> Fraction:
    """Größtes x(K) der k-Clique nach r Runden: max(1, k/(2^r + 1)). Untere Schranke durch den Punkt oben (und einen Einheitsvektor),
    obere durch Mitteln über alle Cliquen mit 2^r + 1 Knoten."""
    return max(Fraction(1), k * punkt_nach_runden(r))


def treppenstufen(r_max: int) -> list:
    """[(Runde, aus Cliquen mit so vielen Knoten, größte erzeugte Clique)]."""
    return [(r, groesste_clique_nach(r - 1), groesste_clique_nach(r)) for r in range(1, r_max + 1)]


# ------------------------------------------------------------------------------------------------ Bruchtext

def bruch(v) -> str:
    """Bruch als Text: 3, 1/2, -7/3."""
    v = Fraction(v)
    return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"


def ungleichung_text(alpha, beta, namen=None, leer: str = "0") -> str:
    """'x_a + 2·x_b <= 1' mit den Namen der Variablen (Standard x0, x1, ...)."""
    teile = []
    for j, c in enumerate(alpha):
        if c:
            name = namen[j] if namen else f"x{j}"
            teile.append(name if c == 1 else f"{bruch(c)}·{name}")
    return f"{' + '.join(teile) if teile else leer} ≤ {bruch(beta)}"
