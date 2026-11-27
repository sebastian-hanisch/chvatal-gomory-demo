"""LP über eine Zeilenliste (HiGHS, dualer Simplex) und zwei exakte Nachprüfungen mit Brüchen.

Die Gleitkomma-Lösung dient nur als Vorschlag. Was die App als bewiesen zeigt, wird mit Brüchen neu geprüft:
  facetten_zertifikat   Multiplikatoren, mit denen EINE Runde die Ungleichung a·x <= b liefert (Cliquenüberdeckung mit Gewicht < b + 1)
  dualbeweis            Gewichte y >= 0 über Zeilen mit y A >= w: beweisen exakt, dass kein zulässiger Punkt mehr als y·b erreicht
"""

from fractions import Fraction

import numpy as np

from cvg_schnitt import als_liste, cg_schnitt, wert

NENNER = 10_000


def loese(w, zeilen):
    """max w·x über {x >= 0 : a·x <= b}. Rückgabe (Wert, Lösung, Dualwerte je Zeile)."""
    from scipy.optimize import linprog

    a = np.array([z[0] for z in zeilen], float)
    b = np.array([z[1] for z in zeilen], float)
    res = linprog(-np.asarray(w, float), A_ub=a, b_ub=b, bounds=[(0, None)] * len(w), method="highs-ds")
    if res.status != 0:
        raise RuntimeError(f"LP ohne Lösung: {res.message}")
    return float(-res.fun), np.asarray(res.x, float), -np.asarray(res.ineqlin.marginals, float)


def als_brueche(werte, nenner: int = NENNER) -> list:
    """Gleitkommazahlen in nahe Brüche; Rauschen unter 1e-9 wird 0."""
    return [Fraction(float(v)).limit_denominator(nenner) if abs(v) > 1e-9 else Fraction(0) for v in werte]


def ueberdeckungswert(a, cliquen):
    """Kleinste gebrochene Cliquenüberdeckung von a: min Summe u mit Summe_{C enthält v} u_C >= a_v, u >= 0.
    Nach LP-Dualität ist das der LP-Wert max a·x über den Cliquenzeilen."""
    from scipy.optimize import linprog

    n = len(a)
    mat = np.array([[1.0 if v in c else 0.0 for c in cliquen] for v in range(n)])
    res = linprog(np.ones(len(cliquen)), A_ub=-mat, b_ub=-np.asarray(a, float), bounds=[(0, None)] * len(cliquen), method="highs-ds")
    if res.status != 0:
        raise RuntimeError(f"Überdeckungs-LP ohne Lösung: {res.message}")
    return float(res.fun), np.asarray(res.x, float)


def facetten_zertifikat(a, b, cliquen):
    """Multiplikatoren {Clique: Bruch}, mit denen ein einziger CG-Schnitt a·x <= b (oder stärker) liefert, oder None.
    Rückgabe nur, wenn exakt gilt: u A >= a und Summe u < b + 1."""
    _, u = ueberdeckungswert(a, cliquen)
    brueche = {i: f for i, f in enumerate(als_brueche(u)) if f > 0}
    zeilen = [(tuple(1 if v in c else 0 for v in range(len(a))), 1) for c in cliquen]
    alpha, beta, _, _ = cg_schnitt(zeilen, als_liste(zeilen, brueche))
    if beta <= b and all(x >= y for x, y in zip(alpha, a)):
        return brueche
    return None


def pruefe_dualbeweis(w, zeilen, y: dict) -> Fraction:
    """Exakt: Sind alle y >= 0 und ist y A >= w, so ist w·x <= y·b für jeden zulässigen Punkt. Rückgabe y·b; sonst ValueError."""
    if any(v < 0 for v in y.values()):
        raise ValueError("negativer Dualwert")
    liste_y = als_liste(zeilen, y)
    n = len(w)
    for j in range(n):
        if sum(v * z[0][j] for v, z in zip(liste_y, zeilen) if v) < w[j]:
            raise ValueError(f"y A >= w verletzt bei Spalte {j}")
    return sum((v * z[1] for v, z in zip(liste_y, zeilen) if v), Fraction(0))


def dualbeweis(w, zeilen, ziel: int):
    """Dualwerte des LP als Brüche; Rückgabe {Zeile: Bruch}, wenn sie exakt w·x <= ziel beweisen, sonst None."""
    _, _, dual = loese(w, zeilen)
    for nenner in (NENNER, 1_000_000):
        y = {i: f for i, f in enumerate(als_brueche(dual, nenner)) if f > 0}
        try:
            if pruefe_dualbeweis(w, zeilen, y) <= ziel:
                return y
        except ValueError:
            continue
    return None


def erfuellt(zeilen, x, tol: float = 1e-9) -> bool:
    """Liegt x in {x >= 0 : a·x <= b}?"""
    return all(v >= -tol for v in x) and all(wert(a, x) <= b + tol for a, b in zeilen)
