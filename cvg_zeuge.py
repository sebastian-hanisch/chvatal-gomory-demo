"""Der Graph mit 13 Knoten, dem eine Chvátal-Runde über den Cliquenzeilen nicht genügt. Alles exakt, ohne Löser.

G = Komplement des Kreisgraphen C13(1, 5): verbunden sind zwei Knoten, wenn ihr Abstand modulo 13 weder 1 noch 5 ist.
G hat größte stabile Mengen der Größe 2 und größte Cliquen der Größe 4. Die Ungleichung x(V) <= 2 gilt für jede stabile Menge.

Eigene Herleitung (nicht extern geprüft), dass x = t an jedem Knoten jeden Schnitt der ersten Runde übersteht, für t = 1/6 und sogar bis
t = 2/11: Ein Schnitt entsteht aus Multiplikatoren u >= 0 auf den Cliquenzeilen; sei U die Summe der u, a_v die Summe der u an den
Cliquen durch v und k = floor(U). Der Schnitt ist Summe floor(a_v) x_v <= k. Jede Clique hat höchstens omega = 4 Knoten, also ist
Summe floor(a_v) <= floor(4U) <= 4k + 3.
  k = 0:    a_v <= U < 1, also floor(a_v) = 0: links steht 0.
  k >= 2:   t (4k + 3) <= k gilt für jedes k >= 2, sobald es für k = 2 gilt (11 t <= 2).
  k = 1:    a_v <= U < 2, also floor(a_v) in {0, 1}. Verletzt ist der Schnitt erst ab floor(1/t) + 1 Einsen: bei t = 1/6 ab 7,
            bei t = 2/11 ab 6. Er hieße x(S) <= 1. Eine Menge S mit mehr als 4 Knoten ist keine Clique, enthält also eine stabile Menge
            aus zwei Knoten: x(S) <= 1 wäre ungültig, kann also kein CG-Schnitt sein.
Damit ist der größte Wert x(V) nach der ersten Runde mindestens 13 · 2/11 = 26/11. Höchstens 26/11 ist er, weil 13 Schnitte der ersten
Runde (je 11 aufeinanderfolgende Knoten) in der Summe 11 x(V) <= 26 ergeben. Also ist er genau 26/11.
"""

from fractions import Fraction
from math import floor

from cvg_graphen import graph13, maximale_cliquen
from cvg_schnitt import schnitt_aus, zeile

N = 13
OMEGA = 4
ALPHA = 2
ZEUGE = Fraction(1, 6)
ZEUGE_GROESSTER = Fraction(2, 11)
LAENGEN = (9, 10, 11)

# Multiplikatoren für die Folge ab Knoten 0: {Clique: Gewicht}; die anderen Folgen entstehen durch Verschieben (Drehung ist eine Symmetrie).
_H = Fraction(1, 2)
_D = Fraction(1, 3)
_F = Fraction(1, 5)
BASIS = {
    9: {(0, 2, 4, 6): _H, (0, 3, 7, 9): _H, (1, 3, 5, 7): _H, (1, 5, 8, 11): _H, (2, 4, 6, 8): _H},
    10: {(0, 2, 4, 6): _D, (0, 2, 6, 9): _D, (0, 3, 7, 9): _D, (1, 3, 5, 7): _D, (1, 4, 8, 10): _D, (1, 5, 8, 11): _D,
         (2, 4, 6, 8): _D, (3, 5, 7, 9): _D},
    11: {(0, 2, 6, 9): 3 * _F, (0, 3, 7, 10): _F, (0, 4, 6, 10): _F, (1, 3, 5, 7): 2 * _F, (1, 4, 8, 10): 3 * _F,
         (2, 4, 6, 8): _F, (2, 5, 8, 11): _F, (3, 5, 7, 9): 2 * _F},
}

ADJ = graph13()
CLIQUEN = maximale_cliquen(ADJ)
ZEILEN = [zeile(N, c) for c in CLIQUEN]


def verschiebe(menge, s: int) -> tuple:
    return tuple(sorted((v + s) % N for v in menge))


def folge(laenge: int, start: int) -> tuple:
    """Die `laenge` aufeinanderfolgenden Knoten ab `start` (modulo 13)."""
    return verschiebe(range(laenge), start)


def multiplikatoren(laenge: int, start: int) -> dict:
    """{Zeilennummer: Bruch} über den 39 Cliquenzeilen: die Basis, um `start` verschoben."""
    return {CLIQUEN.index(verschiebe(c, start)): f for c, f in BASIS[laenge].items()}


def runde1_schnitt(laenge: int, start: int) -> tuple:
    """(alpha, beta) des Schnitts der ersten Runde zur verschobenen Folge. Er ist x(Folge) <= 2 oder stärker."""
    return schnitt_aus(ZEILEN, multiplikatoren(laenge, start))


def summe_der_verschiebungen(laenge: int, anzahl: int) -> tuple:
    """Die Ungleichungen x(Folge) <= 2 für die Starts 0, ..., anzahl-1 addiert: (Häufigkeit je Knoten, rechte Seite 2 · anzahl)."""
    if not 1 <= anzahl <= N:
        raise ValueError("1 bis 13 Verschiebungen")
    haeufigkeit = [0] * N
    for s in range(anzahl):
        for v in folge(laenge, s):
            haeufigkeit[v] += 1
    return tuple(haeufigkeit), 2 * anzahl


def schranke_aus_summe(haeufigkeit, rechts: int):
    """Kommt jeder Knoten mindestens m-mal vor (m > 0), so folgt wegen x >= 0: m · x(V) <= rechts, also in einer weiteren Runde
    x(V) <= floor(rechts / m). Rückgabe (m, floor(rechts / m)) oder (0, None), wenn ein Knoten fehlt."""
    m = min(haeufigkeit)
    return (m, floor(Fraction(rechts, m))) if m else (0, None)


def zweite_runde(laenge: int, anzahl: int) -> tuple:
    """Der CG-Schnitt der zweiten Runde mit Gewicht 1/m auf jedem der ersten `anzahl` Schnitte: (alpha, beta) oder None."""
    haeufigkeit, _ = summe_der_verschiebungen(laenge, anzahl)
    m = min(haeufigkeit)
    if not m:
        return None
    zeilen = [runde1_schnitt(laenge, s) for s in range(anzahl)]
    return schnitt_aus(zeilen, {i: Fraction(1, m) for i in range(anzahl)})


def faelle(t: Fraction) -> list:
    """Die Fälle des Beweises für den Punkt x = t: Liste (Fall, Aussage, erfüllt)."""
    ab = floor(1 / t) + 1
    return [
        ("Cliquen", f"jede Clique hat höchstens 4 Knoten, 4 · t = {4 * t} ≤ 1", 4 * t <= 1),
        ("k = 0", "alle abgerundeten Koeffizienten sind 0", True),
        ("k ≥ 2", f"t · (4k + 3) ≤ k gilt ab k = 2: 11 · t = {11 * t} ≤ 2", 11 * t <= 2),
        ("k = 1", f"verletzt erst ab {ab} Koeffizienten 1; mehr als 4 Knoten sind keine Clique, also wäre x(S) ≤ 1 ungültig",
         ab > OMEGA),
    ]


def zeuge_uebersteht(t: Fraction) -> bool:
    """Übersteht x = t an jedem Knoten nach dieser Fallunterscheidung jeden Schnitt der ersten Runde? (hinreichend, nicht notwendig)"""
    return all(ok for _, _, ok in faelle(t))


WERT_RUNDE = (Fraction(13, 4), Fraction(26, 11), Fraction(2))     # größtes x(V) nach 0, 1, 2 Runden
