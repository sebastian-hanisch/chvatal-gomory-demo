# Kopie aus ganzzahlige-ecken-demo/gze_konflikt.py, geändert ist nur das Präfix (Kopier-Test: tests/test_kopien.py).
"""Zwei Graphenfamilien: der Konfliktgraph K(n; L; q) und der Zufallsgraph G(n, p). Nur ganze Zahlen, Zufall nur über SplitMix64.

Konfliktgraph (ausgedachtes Modell, keine echten Daten): Knoten = Aufträge, Kante = die beiden Aufträge schließen sich aus.
Je Auftrag i = 0, ..., n-1 werden in dieser Reihenfolge gezogen:
  1. Start s = below(100),
  2. Dauer d = 1 + below(2L - 1), also gleichverteilt von 1 bis 2L - 1 (Mittel L); der Auftrag belegt [s, s + d),
  3. Wert w = 1 + below(100) (immer gezogen, auch wenn die Rechnung alle Werte auf 1 setzt),
  4. für j = 0, ..., i-1: r = below(1000) (immer gezogen, auch wenn sich die Zeiten schon überschneiden).
Kante (j, i), wenn sich die Belegungen überschneiden (Zeitkonflikt) oder r < q (Zusatzregel ohne Zeitbezug, q in Promille).

Folgen der festen Reihenfolge: Die Instanz mit n Aufträgen ist der von den ersten n Knoten erzeugte Teilgraph der Instanz mit n + 1; ein größeres q
fügt bei gleichem Zufalls-Seed nur Kanten hinzu; q = 0 ergibt einen Intervallgraphen.

G(n, p): je Knoten i erst der Wert w = 1 + below(100), dann für j = 0, ..., i-1 eine Kante bei below(1000) < p (p in Promille).

Graphen sind Tupel von Bitmasken: Bit j von adj[i] ist gesetzt, wenn i und j durch eine Kante verbunden sind.
Dieses Modul hängt nur von cvg_rng.py ab, hat keinen Oberflächen-Code und ist als Kopierquelle für andere Demos gedacht.
"""

from dataclasses import dataclass

from cvg_rng import SplitMix64

HORIZONT = 100      # Zeitraster: Startzeiten 0 bis HORIZONT - 1
WERT_MAX = 100      # Werte 1 bis WERT_MAX
PROMILLE = 1000


@dataclass(frozen=True)
class Instanz:
    n: int
    adj: tuple          # Nachbarschaft je Knoten als Bitmaske
    werte: tuple        # ganze Werte 1 bis WERT_MAX
    intervalle: tuple = ()  # (Start, Ende) je Auftrag; leer bei G(n, p)
    zusatz: tuple = ()      # Kanten (j, i), die nur aus der Zusatzregel kommen; leer bei G(n, p)


def bits(maske: int):
    """Die gesetzten Bits einer Maske, aufsteigend."""
    while maske:
        b = maske & -maske
        yield b.bit_length() - 1
        maske ^= b


def kanten(adj) -> list:
    """Alle Kanten (i, j) mit i < j, sortiert."""
    return [(i, j) for i in range(len(adj)) for j in bits(adj[i]) if j > i]


def adj_aus_kanten(n: int, liste) -> tuple:
    """Bitmasken aus einer Kantenliste; Schleifen und Knoten außerhalb 0..n-1 sind Fehler."""
    adj = [0] * n
    for u, v in liste:
        if u == v or not (0 <= u < n and 0 <= v < n):
            raise ValueError(f"ungültige Kante ({u}, {v}) bei n = {n}")
        adj[u] |= 1 << v
        adj[v] |= 1 << u
    return tuple(adj)


def ueberschneiden(a: tuple, b: tuple) -> bool:
    """Zeitkonflikt zweier halboffener Belegungen [Start, Ende)."""
    return a[0] < b[1] and b[0] < a[1]


def ziehe_auftrag(rng: SplitMix64, laenge: int) -> tuple:
    """Ein Auftrag: ((Start, Ende), Wert), Züge in der Reihenfolge Start, Dauer, Wert."""
    start = rng.below(HORIZONT)
    dauer = 1 + rng.below(2 * laenge - 1)
    wert = 1 + rng.below(WERT_MAX)
    return (start, start + dauer), wert


def build(n: int, laenge: int, q: int, seed: int) -> Instanz:
    """Konfliktgraph K(n; L = laenge; q in Promille) zum Zufalls-Seed."""
    if n < 0 or laenge < 1 or not 0 <= q <= PROMILLE:
        raise ValueError(f"ungültige Parameter n = {n}, L = {laenge}, q = {q}")
    rng = SplitMix64(seed)
    adj = [0] * n
    intervalle, werte, zusatz = [], [], []
    for i in range(n):
        intervall, wert = ziehe_auftrag(rng, laenge)
        intervalle.append(intervall)
        werte.append(wert)
        for j in range(i):
            r = rng.below(PROMILLE)
            zeit = ueberschneiden(intervalle[j], intervall)
            if zeit or r < q:
                adj[i] |= 1 << j
                adj[j] |= 1 << i
                if not zeit:
                    zusatz.append((j, i))
    return Instanz(n, tuple(adj), tuple(werte), tuple(intervalle), tuple(sorted(zusatz)))


def gnp(n: int, p: int, seed: int) -> Instanz:
    """Zufallsgraph G(n, p), p in Promille, zum Zufalls-Seed."""
    if n < 0 or not 0 <= p <= PROMILLE:
        raise ValueError(f"ungültige Parameter n = {n}, p = {p}")
    rng = SplitMix64(seed)
    adj = [0] * n
    werte = []
    for i in range(n):
        werte.append(1 + rng.below(WERT_MAX))
        for j in range(i):
            if rng.below(PROMILLE) < p:
                adj[i] |= 1 << j
                adj[j] |= 1 << i
    return Instanz(n, tuple(adj), tuple(werte))
