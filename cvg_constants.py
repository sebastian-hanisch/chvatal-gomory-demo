"""Konstanten: Regler-Grenzen, Farben, erklärende Tabellen und die Presets des Schnellstarts."""

import cvg_beispiele as B

SEED_MAX = 999_999

# Selbst abrunden
HAND_DEFAULT = "rad_cliquen"
ZEILEN_MAX = 8

# Cliquen aus Kantenzeilen
K_MIN, K_MAX, K_DEFAULT = 3, 9, 6
R_MIN, R_MAX, R_DEFAULT = 0, 4, 2

# Sammlung
SAMMLUNGEN = {"klein": "147 nichtperfekte Graphen mit 5 bis 7 Knoten", "zwanzig": "47 Instanzen mit 20 Knoten"}
KLEIN_ANZAHL, ZWANZIG_ANZAHL = 147, 47
KLEIN_DEFAULT = 6              # das Handbeispiel (Fünfeck mit Zusatzknoten)
KLEIN_C5 = 0                   # das Fünfeck selbst: schon die ungeraden Kreise schließen die Lücke
FACETTEN_MAX = 4               # so viele Facetten jenseits der Cliquen hat höchstens ein Graph der kleinen Sammlung

# Wenn eine Runde nicht genügt
RUNDE_DEFAULT = 1
LAENGE_DEFAULT = 9
ANZAHL_MIN, ANZAHL_MAX = 1, 13

# Was kostet das Finden?
SUCHE_N_MIN, SUCHE_N_MAX, SUCHE_N_DEFAULT = 8, 16, 16
SUCHE_GEWICHTE = {"eins": "alle 1", "werte": "Werte 1 bis 100"}
SUCHE_SEED_DEFAULT = 26211
SEED_OHNE_LUECKE = (12, 26200)        # G(12; 0,4): schon die Cliquen genügen
SEED_OFFEN = (16, 26207)              # G(16; 0,4): nach einer Runde bleibt (laut Löser) eine Lücke
SEED_VIELE = (16, 26230)              # G(16; 0,4): viele Schritte
BUDGET_MIN, BUDGET_MAX, BUDGET_DEFAULT = 1, 10, 5

COLOR_KNOTEN = "#e8eef5"
COLOR_KNOTEN_U = "#f2b950"
COLOR_RAND = "#2f4b6e"
COLOR_KANTE = "rgba(110,110,110,0.75)"
COLOR_KANTE_INNEN = "#2f6b65"
COLOR_KANTE_RAND = "#c0504d"
COLOR_LINIE = "#4c78a8"
COLOR_ZIEL = "#c0504d"
COLOR_BALKEN = "#2f6b65"
COLOR_BALKEN_HELL = "rgba(47,107,101,0.35)"

# Erklärtabellen (benannte Verfahren und Begriffe)
BEGRIFFE = [
    ("CG-Schnitt (Chvátal-Gomory)", "Zeilen mit Gewichten u ≥ 0 addieren, dann erst die Koeffizienten, dann die rechte Seite abrunden",
     "drei Kantenzeilen des Dreiecks mit je ½: x_a + x_b + x_c ≤ 1"),
    ("Chvátal-Runde", "alle CG-Schnitte einer Beschreibung gleichzeitig dazunehmen; was übrig bleibt, heißt erster Chvátal-Abschluss",
     "Matching: eine Runde über den Gradzeilen"),
    ("Chvátal-Rang", "Zahl der Runden bis zur ganzzahligen Hülle; gehört immer zu einer genannten Startbeschreibung",
     "K6 aus Kantenzeilen: 3; K6 aus Cliquenzeilen: 0"),
    ("Nachladeschritt", "eine Ungleichung, die die aktuelle LP-Lösung verletzt, dazunehmen und das LP neu lösen",
     "Experiment „Was kostet das Finden?“: je Schritt ein Schnitt"),
    ("Trenn-Programm", "ein gemischt-ganzzahliges Programm, das zu einer LP-Lösung Multiplikatoren eines verletzten CG-Schnitts sucht",
     "Auswahl: größte Verletzung abzüglich 0,0001 mal Summe der u; bei Gleichstand entscheidet der Löser"),
]
STARTBESCHREIBUNGEN = [
    ("Gradzeilen (Matching)", "je Knoten: Summe der gewählten Kanten an ihm ≤ 1; Variablen sind die Kanten"),
    ("Kantenzeilen (stabile Mengen)", "je Kante: x_u + x_v ≤ 1; Variablen sind die Knoten"),
    ("Cliquenzeilen (stabile Mengen)", "je maximaler Clique C: Summe der x_v über C ≤ 1; impliziert die Kantenzeilen"),
]
FAMILIEN = [
    ("Ungerader Kreis", "x(C) ≤ (|C|−1)/2 für einen Kreis C mit ungerader Knotenzahl",
     "½ auf je einer Clique, die eine Kreiskante enthält"),
    ("Ungerades Rad", "x(C) + (|C|−1)/2 · x_h ≤ (|C|−1)/2, Kreis C in der Nachbarschaft der Nabe h",
     "½ auf je einer Clique, die ein Dreieck aus Kreiskante und Nabe enthält"),
    ("Ungerades Antiloch", "x(A) ≤ 2 für das Komplement eines Kreises mit 2k+1 Knoten (k ≥ 3)",
     "1/k auf 2k+1 Cliquen {i, i+2, …, i+2(k−1)}"),
]


def hand_titel(schluessel: str) -> str:
    return B.HANDFAELLE[schluessel].titel


def _hand_u(schluessel: str) -> tuple:
    return B.HANDFAELLE[schluessel].loesung


STANDARD = "Handbeispiele (Voreinstellung)"
PRESETS = {
    STANDARD: {
        "e1": HAND_DEFAULT, "u": _hand_u(HAND_DEFAULT), "m": "fuenfeck", "U": (0, 1, 2, 3, 4), "k": K_DEFAULT, "r": R_DEFAULT,
        "sammlung": "klein", "graph": KLEIN_DEFAULT, "facette": 0, "fall": 0, "runde": RUNDE_DEFAULT, "laenge": LAENGE_DEFAULT,
        "anzahl": ANZAHL_MAX, "n": SUCHE_N_DEFAULT, "gewichte": "eins", "seed": SUCHE_SEED_DEFAULT, "budget": BUDGET_DEFAULT,
    },
    "Dreieck und Petersen-Graph": {
        "e1": "dreieck_kanten", "u": _hand_u("dreieck_kanten"), "m": "petersen", "U": (0, 1, 2, 3, 4), "k": 3, "r": 1,
        "sammlung": "klein", "graph": KLEIN_DEFAULT, "facette": 0, "fall": 0, "runde": RUNDE_DEFAULT, "laenge": LAENGE_DEFAULT,
        "anzahl": ANZAHL_MAX, "n": SEED_OFFEN[0], "gewichte": "eins", "seed": SEED_OFFEN[1], "budget": BUDGET_DEFAULT,
    },
    "Abrunden ohne Wirkung": {
        "e1": "k4_kanten", "u": ("1/2", "0", "0", "1/2", "0", "0"), "m": "fuenfeck", "U": (0, 1, 2, 3), "k": 3, "r": 2,
        "sammlung": "klein", "graph": KLEIN_C5, "facette": 0, "fall": 0, "runde": 2, "laenge": 9, "anzahl": 12,
        "n": SEED_OHNE_LUECKE[0], "gewichte": "eins", "seed": SEED_OHNE_LUECKE[1], "budget": BUDGET_DEFAULT,
    },
    "Zwei Runden genügen": {
        "e1": "rad_cliquen", "u": _hand_u("rad_cliquen"), "m": "bruecke", "U": (0, 1, 2), "k": 5, "r": 2,
        "sammlung": "klein", "graph": KLEIN_DEFAULT, "facette": 0, "fall": 0, "runde": 2, "laenge": 9, "anzahl": ANZAHL_MAX,
        "n": SUCHE_N_DEFAULT, "gewichte": "eins", "seed": SUCHE_SEED_DEFAULT, "budget": BUDGET_DEFAULT,
    },
    "Viele Schnitte": {
        "e1": "fuenfeck_grade", "u": _hand_u("fuenfeck_grade"), "m": "k5", "U": (0, 1, 2, 3, 4), "k": 9, "r": 3,
        "sammlung": "zwanzig", "graph": KLEIN_DEFAULT, "facette": 0, "fall": 5, "runde": 2, "laenge": 11, "anzahl": 7,
        "n": SEED_VIELE[0], "gewichte": "eins", "seed": SEED_VIELE[1], "budget": 10,
    },
}
PRESET_HELP = {
    STANDARD: "Fünfeck mit Zusatzknoten über den Cliquen, Matching mit Ausgangskante, K6, der Graph mit 13 Knoten nach einer Runde.",
    "Dreieck und Petersen-Graph": "Drei halbe Kantenzeilen, das äußere Fünfeck des Petersen-Graphen, K3 nach einer Runde und eine Suche, bei der eine Lücke bleibt.",
    "Abrunden ohne Wirkung": "Ganzzahlige rechte Seite, gerade Knotenmenge, Fünfeck (die Kreise genügen) und zu wenige Verschiebungen.",
    "Zwei Runden genügen": "K5 nach zwei Runden und die Summe aller 13 Verschiebungen beim Graphen mit 13 Knoten.",
    "Viele Schnitte": "Ein Fall mit 20 Knoten und acht Schnitten, Folgen mit 11 Knoten und eine Live-Suche mit vielen Schritten.",
}
