"""Rechnungen der Experimente (Zusammensetzung der Einheiten) und die Verdikte als reine Funktionen (Art, Text)."""

from dataclasses import dataclass
from fractions import Fraction
from math import floor

import cvg_beispiele as B
import cvg_katalog as K
import cvg_zeuge as Z
from cvg_graphen import groesstes_gewicht, maximale_cliquen
from cvg_leiter import cliquenzeilen, leiter
from cvg_lp import loese
from cvg_schnitt import (bruch, cg_schnitt, cliquen_rang, ist_gueltig, kanten_am_rand, kanten_in_menge, matching_multiplikatoren,
                         matching_zeilen, max_summe_nach_runden, punkt_nach_runden, ungleichung_text, wert)
from cvg_trennung import GESCHLOSSEN, KEINE_LUECKE, NICHT_BESTIMMT, OFFEN_BEWIESEN, suche_runde

ZAHLWORT = {1: "einer", 2: "zwei", 3: "drei", 4: "vier", 5: "fünf", 6: "sechs", 7: "sieben", 8: "acht", 9: "neun", 10: "zehn"}
HALB = Fraction(1, 2)


def komma(v: float, stellen: int = 3) -> str:
    """Gleitkommazahl mit Dezimalkomma."""
    return f"{v:.{stellen}f}".replace(".", ",")


def zahl_oder_bruch(v, stellen: int = 4) -> str:
    """Ganze Zahlen ohne Stellen, sonst als naher Bruch mit Nenner <= 1000, wenn er den Wert auf 1e-9 trifft, sonst mit Komma."""
    if isinstance(v, Fraction):
        return bruch(v)
    f = Fraction(float(v)).limit_denominator(1000)
    return bruch(f) if abs(float(f) - v) < 1e-9 else komma(v, stellen)


# ------------------------------------------------------------------------------------------------ 1  Selbst abrunden

@dataclass(frozen=True)
class Abrunden:
    fall: B.Handfall
    beschreibung: B.Startbeschreibung
    u: tuple
    alpha: tuple
    beta: int
    links: tuple          # ungerundete Koeffizienten
    rechts: Fraction      # ungerundete rechte Seite
    ecke: tuple           # LP-Ecke vorher
    wert_ecke: Fraction   # alpha · ecke
    lp_vorher: Fraction   # größte Summe über der Startbeschreibung
    lp_nachher: float     # größte Summe mit dem Schnitt
    ganz_optimum: int     # größte Summe über den ganzzahligen Punkten
    gueltig: bool         # der Schnitt gilt für alle ganzzahligen Punkte

    @property
    def text(self) -> str:
        return ungleichung_text(self.alpha, self.beta, self.beschreibung.variablen)


def ergebnis_abrunden(schluessel: str, u_texte) -> Abrunden:
    fall = B.HANDFAELLE[schluessel]
    s = B.startbeschreibung(fall)
    u = B.als_brueche(u_texte)[:len(s.zeilen)]
    u += [Fraction(0)] * (len(s.zeilen) - len(u))
    alpha, beta, links, rechts = cg_schnitt(s.zeilen, u)
    ecke = B.lp_ecke(s)
    eins = [1] * len(s.variablen)
    nachher = loese(eins, list(s.zeilen) + [(alpha, beta)])[0]
    return Abrunden(fall, s, tuple(u), alpha, beta, links, rechts, ecke, wert(alpha, ecke), sum(ecke), nachher,
                    max(sum(p) for p in s.punkte), ist_gueltig(alpha, beta, s.punkte))


def verdict_abrunden(a: Abrunden) -> tuple:
    benutzt = [v for v in a.u if v]
    if not benutzt:
        return "info", "Ohne Multiplikatoren entsteht 0 ≤ 0."
    if a.wert_ecke > a.beta:
        mit = " mit je ½" if all(v == HALB for v in benutzt) else ""
        n = len(benutzt)
        zeilen = f"{ZAHLWORT.get(n, n)} {'Zeile' if n == 1 else 'Zeilen'}"
        return "success", (f"Aus {zeilen}{mit} wird **{a.text}**. Die gebrochene LP-Ecke verletzt das: links steht "
                           f"{bruch(a.wert_ecke)}, erlaubt ist {a.beta}.")
    if not any(a.alpha):
        return "info", f"Alle Koeffizienten werden auf 0 abgerundet: 0 ≤ {a.beta} sagt nichts."
    if a.rechts.denominator == 1:
        return "info", (f"Die rechte Seite {bruch(a.rechts)} war schon ganzzahlig; Abrunden bringt hier nichts Neues: **{a.text}** folgt "
                        "schon aus der gewichteten Summe.")
    zusatz = " (sie ist ganzzahlig)" if all(v.denominator == 1 for v in a.ecke) else ""
    return "info", (f"Die Ungleichung **{a.text}** ist gültig (jeder CG-Schnitt ist es), trennt hier aber nicht: Die gezeigte "
                    f"LP-Ecke{zusatz} erfüllt sie.")


# ------------------------------------------------------------------------------------------------ 2  Matching

@dataclass(frozen=True)
class Matching:
    bild: B.Graphbild
    U: tuple
    innen: tuple          # Kantenindizes in E[U]
    rand: tuple           # Kantenindizes mit einem Ende in U
    alpha: tuple
    beta: int
    links: tuple
    rechts: Fraction
    ecke: tuple           # LP-Ecke des Grad-LP mit größter Summe
    wert_ecke: Fraction
    lp_vorher: Fraction
    lp_nachher: float
    ganz_optimum: int     # größte Matching-Größe
    bipartit: bool
    gueltig: bool


def ist_bipartit(adj) -> bool:
    farbe = {}
    for s in range(len(adj)):
        if s in farbe:
            continue
        farbe[s] = 0
        stapel = [s]
        while stapel:
            v = stapel.pop()
            for w in range(len(adj)):
                if adj[v] >> w & 1:
                    if w not in farbe:
                        farbe[w] = 1 - farbe[v]
                        stapel.append(w)
                    elif farbe[w] == farbe[v]:
                        return False
    return True


def alle_matchings(n_knoten: int, kanten_) -> list:
    """Alle Matchings als 0/1-Tupel über die Kanten (Aufbau Kante für Kante)."""
    out = [(0, ())]
    for e, (a, b) in enumerate(kanten_):
        out += [(m | 1 << a | 1 << b, wahl + (e,)) for m, wahl in out if not m & (1 << a | 1 << b)]
    return [tuple(1 if e in wahl else 0 for e in range(len(kanten_))) for _, wahl in out]


def ergebnis_matching(schluessel: str, U) -> Matching:
    bild, _ = B.MATCHINGGRAPHEN[schluessel]
    U = tuple(sorted(set(U)))
    zeilen = matching_zeilen(bild.n, bild.kanten)
    alpha, beta, links, rechts = cg_schnitt(zeilen, matching_multiplikatoren(bild.n, U))
    punkte = alle_matchings(bild.n, bild.kanten)
    ecke = B.lp_ecke(B.Startbeschreibung(tuple(zeilen), (), tuple(str(i) for i in range(len(bild.kanten))), ()))
    nachher = loese([1] * len(bild.kanten), zeilen + [(alpha, beta)])[0]
    return Matching(bild, U, kanten_in_menge(bild.kanten, U), kanten_am_rand(bild.kanten, U), alpha, beta, links, rechts, ecke,
                    wert(alpha, ecke), sum(ecke), nachher, max(sum(p) for p in punkte), ist_bipartit(bild.adj),
                    ist_gueltig(alpha, beta, punkte))


def verdict_matching(m: Matching) -> tuple:
    g = len(m.U)
    bip = " Dieser Graph ist bipartit: Hier ist schon das Grad-LP ganzzahlig, es fehlt keine Ungleichung." if m.bipartit else ""
    if g < 2:
        return "info", "Mit weniger als zwei Knoten steht links nichts: Es entsteht 0 ≤ 0." + bip
    if g % 2 == 0:
        return "info", (f"|U| = {g} ist gerade: Die rechte Seite {g // 2} ist schon ganzzahlig. Hier entsteht nichts Neues; nur die "
                        "halben Koeffizienten am Rand fallen weg." + bip)
    text = (f"Die {ZAHLWORT.get(g, g)} Gradzeilen mit je ½ ergeben nach einmal Abrunden **x(E[U]) ≤ {m.beta}**. So entsteht jede "
            "Ungleichung für eine ungerade Knotenmenge; nach dem Satz von Edmonds zum Matching-Polytop genügt damit eine Runde.")
    if m.wert_ecke > m.beta:
        return "success", text + f" Die gezeigte gebrochene LP-Ecke verletzt sie: links steht {bruch(m.wert_ecke)}." + bip
    return "success", text + " Die gezeigte LP-Ecke erfüllt sie schon." + bip


# ------------------------------------------------------------------------------------------------ 3  Cliquen aus Kantenzeilen

def runden_text(r: int) -> str:
    return "Ohne Runde" if r == 0 else "Nach einer Runde" if r == 1 else f"Nach {ZAHLWORT.get(r, r)} Runden"


def verdict_clique(k: int, r: int) -> tuple:
    rang = cliquen_rang(k)
    nachsatz = (" Als Cliquenzeile steht diese Ungleichung auch sofort zur Verfügung. **Der Rang misst den Weg von der "
                "Startbeschreibung, nicht die Schwierigkeit.**")
    if r < rang:
        t = punkt_nach_runden(r)
        wann = "Erst mit der nächsten Runde" if r == rang - 1 else f"Erst nach {rang} Runden"
        return "info", (f"{runden_text(r)} ist x = {bruch(t)} an jedem Knoten noch zulässig, die Summe ist {bruch(k * t)} > 1. {wann} gilt "
                        f"x(K{k}) ≤ 1." + nachsatz)
    return "success", (f"{runden_text(r)} gilt x(K{k}) ≤ 1; gebraucht werden genau {rang} "
                       f"{'Runde' if rang == 1 else 'Runden'} (Chvátal-Rang über den Kantenzeilen)." + nachsatz)


def clique_verlauf(k: int, r_max: int = 4) -> list:
    """[(Runde, größtes x(K_k) danach)] nach der eigenen Herleitung."""
    return [(r, max_summe_nach_runden(k, r)) for r in range(r_max + 1)]


# ------------------------------------------------------------------------------------------------ 4  Eine Runde über den Cliquen

def verdict_klein(s: dict) -> tuple:
    """Verdikt zu einer Facette eines kleinen Graphen (s aus cvg_katalog.schnitt_klein)."""
    if s["kreise_wert"] == s["b"]:
        return "info", (f"Hier schließen schon Cliquen und ungerade Kreise die Lücke (Wert {bruch(s['kreise_wert'])}): "
                        "Die volle Runde ändert den Wert nicht mehr.")
    m = len(s["u"])
    mit = " mit je ½" if all(f == HALB for f in s["u"].values()) else ""
    return "success", (f"Cliquen und ungerade Kreise lassen **{bruch(s['kreise_wert'])}** stehen. Ein Schnitt aus {ZAHLWORT.get(m, m)} "
                       f"Cliquenzeilen{mit} senkt den Wert auf **{s['b']}**: das Optimum.")


def verdict_zwanzig(eintrag: dict) -> tuple:
    n = len(eintrag["schnitte"])
    wort = "Ein Schnitt der ersten Runde senkt" if n == 1 else f"{n} Schnitte der ersten Runde senken"
    return "success", (f"Cliquen, ungerade Kreise, Antilöcher und Räder lassen **{zahl_oder_bruch(eintrag['wert_familien'])}** stehen, "
                       f"das Optimum ist {eintrag['optimum']}. {wort} den Wert auf **{eintrag['optimum']}**; den Beweis geben die "
                       "gespeicherten Dualwerte in Brüchen.")


@dataclass(frozen=True)
class Leiterwerte:
    cliquen: float
    kreise: float
    familien: float


def leiter_zwanzig(eintrag: dict) -> Leiterwerte:
    d = K.schnitte_zwanzig(eintrag)
    w = list(d["instanz"].werte)
    stufen = leiter(w, d["instanz"].adj)
    return Leiterwerte(stufen["cliquen"][0], stufen["kreise"][0], stufen["familien"][0])


def pruefe_gueltig_durch_gewicht(adj, zeilen) -> bool:
    """Jede Zeile mit ganzzahligen a >= 0 gilt für alle stabilen Mengen genau dann, wenn das größte Gewicht a höchstens b ist."""
    return all(groesstes_gewicht(adj, a)[0] <= b for a, b in zeilen)


# ------------------------------------------------------------------------------------------------ 5  Wenn eine Runde nicht genügt

def verdict_zeuge(runde: int, laenge: int = 9, anzahl: int = 13) -> tuple:
    if runde == 0:
        return "warning", ("Über den Cliquen allein ist x = ¼ an jedem Knoten erlaubt: Summe 13/4. In ganzen Zahlen passen höchstens "
                           "2 Knoten in eine stabile Menge.")
    if runde == 1:
        return "warning", ("x = ⅙ an jedem Knoten übersteht jeden Schnitt der ersten Runde und wählt doch 13/6 Knoten, erlaubt sind 2. "
                           "**Eine Runde genügt hier nicht.** Der größte Wert nach einer Runde ist genau 26/11.")
    haeufigkeit, rechts = Z.summe_der_verschiebungen(laenge, anzahl)
    m, schranke = Z.schranke_aus_summe(haeufigkeit, rechts)
    if m == 0:
        return "info", (f"Nach {anzahl} Verschiebungen fehlt noch mindestens ein Knoten in der Summe: Sie beschränkt x(V) nicht.")
    if schranke > Z.ALPHA:
        return "info", (f"Noch kommen nicht alle Knoten oft genug vor: Die Summe gibt nur {m}·x(V) ≤ {rechts}, abgerundet "
                        f"x(V) ≤ {schranke}.")
    gleich = "Jeder Knoten kommt gleich oft vor: " if m == max(haeufigkeit) else f"Jeder Knoten kommt mindestens {m}-mal vor: "
    return "success", (f"{gleich}{m}·x(V) ≤ {rechts}, abgerundet **x(V) ≤ {schranke}**. Zwei Runden genügen, und zwar für die ganze "
                       "Hülle: Die übrigen Facetten gelten schon nach höchstens einer Runde.")


def schranke_text(laenge: int, anzahl: int):
    haeufigkeit, rechts = Z.summe_der_verschiebungen(laenge, anzahl)
    m, schranke = Z.schranke_aus_summe(haeufigkeit, rechts)
    return haeufigkeit, rechts, m, schranke


def facetten13(vollstaendig: bool = False) -> dict:
    """Die ganze Hülle der stabilen Mengen des Graphen mit 13 Knoten: Anzahlen je Sorte und die Facetten außerhalb der ersten Runde.
    Geprüft wird die Gültigkeit jeder Facette; mit `vollstaendig` auch Facettenrang und Vollständigkeit (einige Sekunden, in den Tests)."""
    import cvg_dd as D
    from cvg_graphen import ist_clique, maske, stabile_mengen
    from cvg_lp import facetten_zertifikat

    punkte = [tuple(m >> v & 1 for v in range(Z.N)) for m in stabile_mengen(Z.ADJ)]
    huelle = D.huelle(punkte)
    if vollstaendig:
        fehler = D.pruefe_huelle(punkte, huelle)
    else:
        fehler = [f"ungültig: {a} <= {b}" for a, b in huelle.facetten if any(D.wert(a, p) > b for p in punkte)]
    nichtneg = sum(1 for a, b in huelle.facetten if b == 0)
    cliquen_f, eine_runde, ausserhalb = 0, 0, []
    for a, b in huelle.facetten:
        if b == 0:
            continue
        if b == 1 and set(a) <= {0, 1} and ist_clique(Z.ADJ, maske(j for j, c in enumerate(a) if c)):
            cliquen_f += 1
        elif facetten_zertifikat(a, b, Z.CLIQUEN) is not None:
            eine_runde += 1
        else:
            ausserhalb.append((a, b))
    return {"gesamt": len(huelle.facetten), "nichtnegativ": nichtneg, "cliquen": cliquen_f, "eine_runde": eine_runde,
            "ausserhalb": ausserhalb, "fehler": fehler, "stabile_mengen": len(punkte)}


# ------------------------------------------------------------------------------------------------ 6  Was kostet das Finden?

def instanz_suche(n: int, gewichte: str, seed: int):
    from cvg_konflikt import gnp

    inst = gnp(n, 400, seed)
    return inst, ([1] * n if gewichte == "eins" else list(inst.werte))


def suche_live(n: int, gewichte: str, seed: int, budget: float):
    inst, w = instanz_suche(n, gewichte, seed)
    cliquen = maximale_cliquen(inst.adj)
    zeilen = cliquenzeilen(n, cliquen)
    opt = groesstes_gewicht(inst.adj, w)[0]
    return inst, w, cliquen, zeilen, suche_runde(w, zeilen, opt, budget=budget, je_programm=budget)


GRUENDE = {"zeit": "die Zeitgrenze ist erreicht", "schritte": "die Höchstzahl der Schritte ist erreicht",
           "loeser": "der Löser hat weder einen verletzten Schnitt geliefert noch bewiesen, dass es keinen gibt"}


def verdict_suche(status: str, anzahl: int, optimum: int, wert_ende: float, grund: str = "") -> tuple:
    schnitte = "einen Schnitt" if anzahl == 1 else f"{anzahl} Schnitte"
    if status == KEINE_LUECKE:
        return "info", f"Hier ist schon mit den Cliquen nichts zu tun: Der LP-Wert ist das Optimum {optimum}."
    if status == GESCHLOSSEN:
        return "success", (f"Die Suche fand {schnitte} der ersten Runde, damit erreicht der LP-Wert das Optimum {optimum}. **Die Lücke "
                           "ist geschlossen.** Dafür muss das Trenn-Programm nichts beweisen: Jeder Schnitt ist exakt nachgerechnet und damit gültig. "
                           "Dass der LP-Wert mit diesen Schnitten das Optimum erreicht, rechnet HiGHS in Gleitkommazahlen (Toleranz 0,000001).")
    if status == OFFEN_BEWIESEN:
        nach = "ohne Schnitt" if anzahl == 0 else f"nach {anzahl} {'Schnitt' if anzahl == 1 else 'Schnitten'}"
        return "warning", (f"Der Löser (HiGHS-MILP, in der App ohne zweiten Löser) meldet {nach}: Kein Schnitt der ersten Runde ist mehr verletzt. "
                           f"**Nach dieser Meldung bleibt mit einer Runde eine Lücke** (Wert {zahl_oder_bruch(wert_ende)}, Optimum {optimum}), bis auf die Toleranzen des Lösers und die "
                           "Grenze u ≤ 0,999.")
    assert status == NICHT_BESTIMMT
    return "warning", (f"**Nicht bestimmt:** {GRUENDE.get(grund, grund)}. Mit {anzahl} {'Schnitt' if anzahl == 1 else 'Schnitten'} steht "
                       f"der Wert bei {zahl_oder_bruch(wert_ende)} (Optimum {optimum}). Das ist nur eine obere Schranke für den Wert der "
                       "Runde, und „nichts gefunden“ heißt nicht „nichts verletzt“.")


def verdict_gross(zeile_: dict) -> tuple:
    """Verdikt zur vorgerechneten Reihe mit 30 Knoten (zeile_ aus cvg_messung.zusammenfassung_gross)."""
    return "info", (f"In {zeile_['nicht_bestimmt']} von {zeile_['graphen']} Graphen mit {zeile_['n']} Knoten war der Wert der Runde mit "
                    "diesem Budget nicht bestimmbar. Das ist eine Eigenschaft von Löser, Budget und Rechner, kein Wert der Runde.")


# ------------------------------------------------------------------------------------------------ Überblick

def ueberblick() -> list:
    """Die Antwort auf die Kernfrage je Startbeschreibung: (Aufgabe, Startbeschreibung, Runden, Beleg)."""
    return [
        ("Matching, Graph nicht bipartit", "Gradzeilen", "genau 1", "halbe Summe der Gradzeilen, dazu der Satz von Edmonds"),
        ("Stabile Mengen, Clique mit k Knoten", "Kantenzeilen", "genau ⌈log₂(k−1)⌉", "eigene Herleitung"),
        ("Stabile Mengen, 147 nichtperfekte Graphen mit 5 bis 7 Knoten", "Cliquenzeilen", "genau 1",
         "alle 200 Facetten jenseits der Cliquen mit exaktem Zertifikat"),
        ("Stabile Mengen, Graph mit 13 Knoten", "Cliquenzeilen", "genau 2", "eigene Herleitung, exakt nachgerechnet"),
    ]


def verdict_kernfrage(rang_clique6: int, ausserhalb13: int) -> tuple:
    return "info", ("**Ja, erzeugen geht:** Gewichtet addieren und abrunden liefert nur gültige Ungleichungen. Wie viele Runden nötig "
                    "sind, hängt an der Startbeschreibung: beim Matching eine, bei der Clique mit 6 Knoten aus den Kantenzeilen "
                    f"{rang_clique6}, beim Graphen mit 13 Knoten über den Cliquen zwei ({ausserhalb13} Facette der ganzzahligen Hülle "
                    "fehlt nach der ersten). Das **Finden** der Multiplikatoren ist hier selbst ein gemischt-ganzzahliges Programm.")
