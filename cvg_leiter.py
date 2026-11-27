"""Die Leiter eines Zielvektors: Cliquen, dann bekannte Familien (jede als Schnitt der ersten Runde mit Multiplikatoren)."""

from cvg_familien import (antiloch_zertifikat, antiloecher, kreis_zertifikat, rad_zertifikat, trenne_antiloecher, trenne_kreise,
                          trenne_raeder)
from cvg_graphen import maximale_cliquen
from cvg_lp import loese
from cvg_schnitt import schnitt_aus, zeile

OFFEN_AB = 1e-5
MAX_NACHLADEN = 2_000


def cliquenzeilen(n: int, cliquen) -> list:
    return [zeile(n, c) for c in cliquen]


def familien_ungleichung(n: int, art: str, daten) -> tuple:
    """Die Ungleichung der Familie selbst: (Koeffizienten, rechte Seite)."""
    a = [0] * n
    if art == "kreis":
        for v in daten:
            a[v] = 1
        return tuple(a), (len(daten) - 1) // 2
    if art == "rad":
        nabe, kreis = daten
        for v in kreis:
            a[v] = 1
        a[nabe] = (len(kreis) - 1) // 2
        return tuple(a), (len(kreis) - 1) // 2
    if art == "antiloch":
        for v in daten:
            a[v] = 1
        return tuple(a), 2
    raise ValueError(art)


def familien_zertifikat(cliquen, art: str, daten) -> dict:
    if art == "kreis":
        return kreis_zertifikat(cliquen, daten)
    if art == "rad":
        return rad_zertifikat(cliquen, daten[0], daten[1])
    return antiloch_zertifikat(cliquen, daten)


def schnitte_der_familien(adj, cliquen, zeilen, x, arten=("kreis",), antiloch_liste=None) -> list:
    """Verletzte Schnitte der ersten Runde aus der ersten Familie in `arten`, die etwas findet: [(u, alpha, beta, Art)].
    Jeder Schnitt ist mindestens so stark wie die Ungleichung seiner Familie (das wird hier geprüft)."""
    n = len(adj)
    for art in arten:
        if art == "kreis":
            funde = trenne_kreise(adj, x)
        elif art == "rad":
            funde = trenne_raeder(adj, x)
        else:
            funde = trenne_antiloecher(antiloch_liste if antiloch_liste is not None else antiloecher(adj), x)
        if not funde:
            continue
        out = []
        for daten in funde:
            u = familien_zertifikat(cliquen, art, daten)
            alpha, beta = schnitt_aus(zeilen, u)
            a, b = familien_ungleichung(n, art, daten)
            if beta > b or any(c < d for c, d in zip(alpha, a)):
                raise AssertionError(f"Zertifikat zur Familie {art} zu schwach")
            out.append((u, alpha, beta, art))
        return out
    return []


def verletzte_familien(adj, x, arten, antiloch_liste=None) -> list:
    """Die reinen Familienungleichungen (a, b), die x verletzt, aus der ersten Familie in `arten`, die etwas findet."""
    n = len(adj)
    for art in arten:
        if art == "kreis":
            funde = trenne_kreise(adj, x)
        elif art == "rad":
            funde = trenne_raeder(adj, x)
        else:
            funde = trenne_antiloecher(antiloch_liste if antiloch_liste is not None else antiloecher(adj), x)
        if funde:
            return [familien_ungleichung(n, art, daten) for daten in funde]
    return []


def lade_bis_fertig(w, adj, cliquen, arten, antiloch_liste=None) -> tuple:
    """Cliquen und alle verletzten Ungleichungen der Familien nachladen, bis nichts mehr verletzt ist: genau die Ungleichungen der
    Familien, ohne Verstärkung. Rückgabe (Wert, Lösung, nachgeladene Zeilen). Der Wert hängt nicht an der Reihenfolge (exakte
    Trennung), die Zahl der Zeilen schon."""
    arbeit = cliquenzeilen(len(adj), cliquen)
    start = len(arbeit)
    gesehen = set()
    wert_, x, _ = loese(w, arbeit)
    for _ in range(MAX_NACHLADEN):
        neu = [z for z in dict.fromkeys(verletzte_familien(adj, x, arten, antiloch_liste)) if z not in gesehen]
        if not neu:
            return wert_, x, arbeit[start:]
        gesehen.update(neu)
        arbeit += neu
        wert_, x, _ = loese(w, arbeit)
    raise RuntimeError("Obergrenze der Nachladeschritte erreicht: Wert nicht bestimmt")


def leiter(w, adj) -> dict:
    """Werte über den Cliquen, mit ungeraden Kreisen, mit Kreisen, Antilöchern und Rädern."""
    cliquen = maximale_cliquen(adj)
    zeilen = cliquenzeilen(len(adj), cliquen)
    wert_c, x_c, _ = loese(w, zeilen)
    wert_k, x_k, _ = lade_bis_fertig(w, adj, cliquen, ("kreis",))
    liste = antiloecher(adj)
    wert_f, x_f, _ = lade_bis_fertig(w, adj, cliquen, ("kreis", "antiloch", "rad"), liste)
    return {"cliquen": (wert_c, x_c), "kreise": (wert_k, x_k), "familien": (wert_f, x_f)}
