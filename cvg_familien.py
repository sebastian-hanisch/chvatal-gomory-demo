"""Bekannte Familien als Chvátal-Gomory-Schnitte über den Cliquenzeilen: ungerade Kreise, ungerade Räder, ungerade Antilöcher.

Zu jeder gefundenen Ungleichung entstehen Multiplikatoren über die Zeilen der maximalen Cliquen, die sie in einer Runde liefern (oder
eine noch stärkere Ungleichung mit derselben rechten Seite):
  ungerader Kreis   1/2 auf je einer maximalen Clique, die eine Kreiskante enthält
  ungerades Rad     1/2 auf je einer maximalen Clique, die ein Dreieck (Kreiskante und Nabe) enthält
  Antiloch (2k+1)   1/k auf je einer maximalen Clique, die {i, i+2, ..., i+2(k-1)} enthält
Die Kreise und Räder werden exakt getrennt (kürzester ungerader Weg, Dijkstra auf Knoten und Parität), die Antilöcher ab 7 Knoten
vorab vollständig aufgezählt. Kreise und Räder setzen eine Lösung voraus, die die Cliquenzeilen erfüllt (Kantengewichte >= 0).
"""

import heapq
from fractions import Fraction

from cvg_graphen import induzierte_kreise, komplement, maske
from cvg_konflikt import bits

TOL = 1e-6


def kuerzester_ungerader_weg(nachbarn, gewicht, start: int, schranke: float):
    """Dijkstra auf Zuständen (Knoten, Parität). Geschlossener Weg ungerader Länge ab `start` mit Gewicht < schranke als Knotenliste
    (ohne Wiederholung des Starts am Ende) oder None."""
    ziel = (start, 1)
    abstand = {(start, 0): 0.0}
    vor = {}
    halde = [(0.0, start, 0)]
    while halde:
        d, u, par = heapq.heappop(halde)
        if d > abstand[(u, par)]:
            continue
        if (u, par) == ziel:
            break
        for v in nachbarn[u]:
            nd = d + gewicht[(u, v)]
            schluessel = (v, 1 - par)
            if nd < schranke and nd < abstand.get(schluessel, float("inf")):
                abstand[schluessel] = nd
                vor[schluessel] = (u, par)
                heapq.heappush(halde, (nd, v, 1 - par))
    if ziel not in abstand or abstand[ziel] >= schranke:
        return None
    weg, z = [], ziel
    while z != (start, 0):
        z = vor[z]
        weg.append(z[0])
    return weg[::-1]


def einfacher_ungerader_kreis(adj, weg) -> list:
    """Aus einem geschlossenen ungeraden Weg einen einfachen ungeraden Kreis ohne Sehne: gerade Teilschleifen fallen weg, an einer
    Sehne bleibt die ungerade Hälfte. Bei Kantengewichten >= 0 wird die Verletzung dabei nicht kleiner."""
    stapel = []
    for v in weg:
        if v in stapel:
            k = stapel.index(v)
            if (len(stapel) - k) % 2 == 1:
                stapel = stapel[k:]
                break
            del stapel[k + 1:]
        else:
            stapel.append(v)
    kreis = stapel
    gekuerzt = True
    while gekuerzt:
        gekuerzt = False
        k = len(kreis)
        for i in range(k):
            for j in range(i + 2, k):
                if (i, j) == (0, k - 1) or not adj[kreis[i]] >> kreis[j] & 1:
                    continue
                a = kreis[i:j + 1]
                b = kreis[j:] + kreis[:i + 1]
                kreis = a if len(a) % 2 == 1 else b
                gekuerzt = True
                break
            if gekuerzt:
                break
    return kreis


def trenne_kreise(adj, x, tol: float = TOL) -> list:
    """Verletzte ungerade Kreisungleichungen: je Startknoten ein kürzester Kreis. Rückgabe: Liste von Knotenfolgen (verschiedene Mengen)."""
    n = len(adj)
    nachbarn = [list(bits(a)) for a in adj]
    gewicht = {(u, v): max(0.0, 1.0 - x[u] - x[v]) for u in range(n) for v in nachbarn[u]}
    out = {}
    for s in range(n):
        weg = kuerzester_ungerader_weg(nachbarn, gewicht, s, 1.0 - 2 * tol)
        if weg is None:
            continue
        kreis = einfacher_ungerader_kreis(adj, weg)
        if len(kreis) >= 3 and sum(x[v] for v in kreis) > (len(kreis) - 1) / 2 + tol:
            out[maske(kreis)] = tuple(kreis)
    return [out[m] for m in sorted(out)]


def trenne_raeder(adj, x, tol: float = TOL) -> list:
    """Verletzte Radungleichungen x(C) + (|C|-1)/2 · x_h <= (|C|-1)/2 mit einem ungeraden Kreis C in der Nachbarschaft der Nabe h.
    Verletzt genau dann, wenn C mit Kantengewichten 1 - x_a - x_c - x_h (>= 0, weil jedes Dreieck erfüllt ist) weniger als 1 - x_h wiegt."""
    n = len(adj)
    out = {}
    for h in range(n):
        innen = [adj[u] & adj[h] if adj[h] >> u & 1 else 0 for u in range(n)]
        nachbarn = [list(bits(a)) for a in innen]
        gewicht = {(a, c): max(0.0, 1.0 - x[a] - x[c] - x[h]) for a in range(n) for c in nachbarn[a]}
        for s in bits(adj[h]):
            weg = kuerzester_ungerader_weg(nachbarn, gewicht, s, 1.0 - x[h] - 2 * tol)
            if weg is None:
                continue
            kreis = einfacher_ungerader_kreis(innen, weg)
            k = (len(kreis) - 1) // 2
            if len(kreis) >= 3 and sum(x[u] for u in kreis) + k * x[h] > k + tol:
                out[(h, maske(kreis))] = (h, tuple(kreis))
    return [out[s] for s in sorted(out)]


def antiloecher(adj) -> list:
    """Alle ungeraden Antilöcher ab 7 Knoten als Knotenfolge im Komplement-Kreis (das Antiloch mit 5 Knoten ist selbst ein Kreis)."""
    return induzierte_kreise(komplement(adj), 7, True)


def trenne_antiloecher(folgen, x, tol: float = TOL) -> list:
    """Alle verletzten Antiloch-Ungleichungen x(A) <= 2 aus der vorab aufgezählten Liste."""
    return [f for f in folgen if sum(x[v] for v in f) > 2 + tol]


# ------------------------------------------------------------------------------------------------ Zertifikate über den Cliquenzeilen

def clique_mit(cliquen, knoten) -> int:
    """Nummer der ersten maximalen Clique, die alle Knoten enthält."""
    s = set(knoten)
    for i, c in enumerate(cliquen):
        if s <= set(c):
            return i
    raise ValueError(f"keine maximale Clique enthält {sorted(s)}")


def _summiere(cliquen, mengen, gewicht: Fraction) -> dict:
    out = {}
    for m in mengen:
        i = clique_mit(cliquen, m)
        out[i] = out.get(i, Fraction(0)) + gewicht
    return out


def kreis_zertifikat(cliquen, kreis) -> dict:
    """1/2 auf je einer Clique je Kreiskante (dieselbe Clique mehrfach: Gewichte addieren sich)."""
    kanten = [(kreis[i], kreis[(i + 1) % len(kreis)]) for i in range(len(kreis))]
    return _summiere(cliquen, kanten, Fraction(1, 2))


def rad_zertifikat(cliquen, nabe: int, kreis) -> dict:
    """1/2 auf je einer Clique je Dreieck (Kreiskante und Nabe)."""
    dreiecke = [(kreis[i], kreis[(i + 1) % len(kreis)], nabe) for i in range(len(kreis))]
    return _summiere(cliquen, dreiecke, Fraction(1, 2))


def antiloch_zertifikat(cliquen, folge) -> dict:
    """1/k auf je einer Clique je Menge {folge[i], folge[i+2], ..., folge[i+2(k-1)]} (Antiloch mit 2k+1 Knoten)."""
    n = len(folge)
    k = (n - 1) // 2
    mengen = [[folge[(i + 2 * j) % n] for j in range(k)] for i in range(n)]
    return _summiere(cliquen, mengen, Fraction(1, k))
