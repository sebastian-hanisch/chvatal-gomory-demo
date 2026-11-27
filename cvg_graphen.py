"""Graphen als Tupel von Bitmasken: maximale Cliquen, stabile Mengen, größtes Gewicht, induzierte Kreise und der Kreisgraph mit 13 Knoten.

Alle Rechnungen sind ganzzahlig und ohne Zufall. Bit j von adj[i] ist gesetzt, wenn i und j verbunden sind. Jede Aufzählung hat eine
Obergrenze (ZuViele), damit keine Eingabe die App hängen lässt.
"""

from cvg_konflikt import adj_aus_kanten, bits

MAX_CLIQUEN = 20_000
MAX_MENGEN = 200_000


class ZuViele(Exception):
    """Eine Obergrenze der Aufzählung wurde überschritten: Ergebnis nicht bestimmt."""


def maske(knoten) -> int:
    """Bitmaske zu einer Knotenmenge."""
    m = 0
    for v in knoten:
        m |= 1 << v
    return m


def liste(m: int) -> tuple:
    """Knoten einer Bitmaske, aufsteigend."""
    return tuple(bits(m))


def ist_clique(adj, m: int) -> bool:
    """Sind je zwei Knoten der Maske verbunden?"""
    return all((m & ~(1 << v)) & ~adj[v] == 0 for v in bits(m))


def ist_stabil(adj, m: int) -> bool:
    """Enthält die Maske keine Kante?"""
    return all(m & adj[v] == 0 for v in bits(m))


def maximale_cliquen(adj, grenze: int = MAX_CLIQUEN) -> tuple:
    """Alle maximalen Cliquen (Bron-Kerbosch mit Pivot), als sortierte Knotentupel; ein isolierter Knoten ist selbst eine."""
    n = len(adj)
    out = []

    def rec(r, p, x):
        if not p and not x:
            out.append(liste(r))
            if len(out) > grenze:
                raise ZuViele("zu viele maximale Cliquen")
            return
        pivot = max(bits(p | x), key=lambda v: (bin(adj[v] & p).count("1"), -v))
        for v in bits(p & ~adj[pivot]):
            rec(r | 1 << v, p & adj[v], x & adj[v])
            p &= ~(1 << v)
            x |= 1 << v

    if n:
        rec(0, (1 << n) - 1, 0)
    return tuple(sorted(out))


def stabile_mengen(adj, grenze: int = MAX_MENGEN) -> list:
    """Alle stabilen Mengen als Masken, die leere eingeschlossen (Aufbau Knoten für Knoten)."""
    mengen = [0]
    for v in range(len(adj)):
        neu = [m | 1 << v for m in mengen if not m & adj[v]]
        mengen += neu
        if len(mengen) > grenze:
            raise ZuViele("zu viele stabile Mengen")
    return mengen


def groesstes_gewicht(adj, w) -> tuple:
    """Exakt größtes Gewicht einer stabilen Menge (Gewichte ganzzahlig, >= 0) und eine solche Menge als Maske.
    Rekursion auf dem Knoten größten Grades im Rest: ohne ihn oder mit ihm ohne seine Nachbarn; mit Merkspeicher."""
    merk = {}

    def rec(rest):
        if not rest:
            return 0, 0
        if rest in merk:
            return merk[rest]
        v = max(bits(rest), key=lambda u: (bin(adj[u] & rest).count("1"), -u))
        if not adj[v] & rest:                       # kein Rest hat noch eine Kante: alle nehmen
            ergebnis = sum(w[u] for u in bits(rest)), rest
        else:
            ohne = rec(rest & ~(1 << v))
            mit_wert, mit_menge = rec(rest & ~(adj[v] | 1 << v))
            mit = mit_wert + w[v], mit_menge | 1 << v
            ergebnis = mit if mit[0] > ohne[0] else ohne
        merk[rest] = ergebnis
        return ergebnis

    return rec((1 << len(adj)) - 1)


def komplement(adj) -> tuple:
    n = len(adj)
    voll = (1 << n) - 1
    return tuple(voll & ~adj[v] & ~(1 << v) for v in range(n))


def kreisgraph(n: int, schritte) -> tuple:
    """Kreisgraph C_n(schritte): Knoten i ist mit i + d und i - d (modulo n) verbunden, d aus `schritte`."""
    return adj_aus_kanten(n, sorted({tuple(sorted((i, (i + d) % n))) for i in range(n) for d in schritte}))


def graph13() -> tuple:
    """Das Komplement des Kreisgraphen C13(1, 5): 13 Knoten; verbunden, wenn der Abstand modulo 13 nicht 1 oder 5 ist."""
    return komplement(kreisgraph(13, (1, 5)))


def induzierte_kreise(adj, mindestlaenge: int, ungerade: bool = True, grenze: int = MAX_MENGEN) -> list:
    """Alle induzierten Kreise (ohne Sehne) mit mindestens `mindestlaenge` Knoten als Knotenfolge im Kreis.
    Start ist der kleinste Knoten; jede Richtung zählt einmal (zweiter Knoten kleiner als letzter)."""
    out = []

    def rec(pfad, gesperrt):
        start, ende = pfad[0], pfad[-1]
        for w in bits(adj[ende]):
            if w <= start or gesperrt >> w & 1:
                continue
            if adj[w] >> start & 1:                 # w schließt den Kreis
                if len(pfad) >= 2 and len(pfad) + 1 >= mindestlaenge and pfad[1] < w \
                        and (not ungerade or len(pfad) % 2 == 0):
                    out.append(tuple(pfad) + (w,))
                    if len(out) > grenze:
                        raise ZuViele("zu viele induzierte Kreise")
                if len(pfad) >= 2:
                    continue                         # mit w am Start wäre jede Verlängerung nicht mehr induziert
            # keine Sehne zu inneren Knoten: wird das bisherige Ende innen, sind seine Nachbarn gesperrt (nicht die des Starts,
            # denn der schließende Knoten ist ein Nachbar des Starts)
            rec(pfad + [w], gesperrt | (adj[ende] if len(pfad) >= 2 else 0) | 1 << w)

    for s in range(len(adj)):
        rec([s], 1 << s)
    return out


def alle_ungeraden_kreise(adj, grenze: int = MAX_MENGEN) -> list:
    """Knotenmengen (Masken) aller ungeraden Kreise, mit oder ohne Sehne. Nur für kleine Graphen gedacht."""
    gefunden = set()
    schritte = [0]

    def rec(start, v, benutzt, laenge):
        schritte[0] += 1
        if schritte[0] > 40 * grenze:
            raise ZuViele("zu viele Wege")
        for w in bits(adj[v]):
            if w == start and laenge >= 3 and laenge % 2 == 1:
                gefunden.add(benutzt)
            elif w > start and not benutzt >> w & 1:
                rec(start, w, benutzt | 1 << w, laenge + 1)

    for s in range(len(adj)):
        rec(s, s, 1 << s, 1)
    return sorted(gefunden, key=lambda m: (bin(m).count("1"), liste(m)))
