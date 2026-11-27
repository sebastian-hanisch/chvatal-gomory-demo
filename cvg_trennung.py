"""Die Trennung über den ersten Chvátal-Abschluss als gemischt-ganzzahliges Programm (scipy.optimize.milp, HiGHS).

Gesucht sind Multiplikatoren u in [0, 1 - 0,001] je Zeile, ganze Koeffizienten alpha <= u A und eine ganze rechte Seite
beta >= u b - 0,999, sodass alpha·x - beta möglichst groß wird (eigene Formulierung). Jeder gefundene Schnitt wird aus den gerundeten
Multiplikatoren (Nenner höchstens 1000) exakt mit Brüchen neu gerechnet und ist damit gültig, egal was der Löser geliefert hat.
Nur die Antwort "kein Schnitt ist mehr verletzt" hängt am Löser, an seinen Toleranzen (verletzt ab 1e-5) und an der 0,001.

Auswahlregel je Schritt: eine Ungleichung, die mit der größten Verletzung abzüglich 1e-4 mal der Summe der u (dünne Schnitte).
Findet dieser Lauf nichts Verletztes, rechnet ein zweiter Lauf ohne die Strafe nach; erst seine Optimalitätsmeldung zählt als
"keiner verletzt" (mit Strafe allein könnten kleine Verletzungen mit großer Summe u übersehen werden). Bei Gleichstand entscheidet der Löser.

Harte Zeitgrenzen: je Programm eine Grenze, je Suche ein Gesamtbudget und eine Obergrenze für die Zahl der Schritte. Läuft eine
Grenze ab, ist der Ausgang "nicht bestimmt".
"""

import time
from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from cvg_lp import loese
from cvg_schnitt import schnitt_aus

DELTA = 1e-3          # u in [0, 1 - DELTA]
STRAFE = 1e-4         # Strafe je Einheit Summe u
VERLETZT_AB = 1e-5
NENNER = 1000
GESCHLOSSEN_TOL = 1e-6
MAX_SCHRITTE = 200

KEINE_LUECKE = "keine_luecke"
GESCHLOSSEN = "geschlossen"
OFFEN_BEWIESEN = "offen_bewiesen"
NICHT_BESTIMMT = "nicht_bestimmt"


@dataclass(frozen=True)
class Trennung:
    status: str                  # "verletzt", "keiner" oder "offen" (Zeitgrenze oder Numerik)
    u: dict = None               # {Zeile: Bruch}
    alpha: tuple = None
    beta: int = None


@dataclass(frozen=True)
class Schritt:
    u: dict
    alpha: tuple
    beta: int
    verletzung: float
    wert_danach: float
    herkunft: str = "milp"       # "milp" oder die Familie eines vorab geladenen Schnitts ("kreis", "rad", "antiloch")


@dataclass(frozen=True)
class Suche:
    status: str                  # KEINE_LUECKE, GESCHLOSSEN, OFFEN_BEWIESEN, NICHT_BESTIMMT
    optimum: int
    wert_start: float
    wert_ende: float
    schritte: tuple
    x: tuple                     # LP-Lösung am Ende
    grund: str = ""              # bei NICHT_BESTIMMT: "zeit", "schritte" oder "loeser"
    sekunden: float = 0.0


def baue_programm(x, zeilen, strafe: float):
    """Matrizen des Trenn-Programms. Variablen: u (je Zeile), alpha (je Knoten mit x > 0), beta."""
    m = len(zeilen)
    a = np.array([z[0] for z in zeilen], float)
    b = np.array([z[1] for z in zeilen], float)
    traeger = [j for j in range(len(x)) if x[j] > 1e-9]
    nt = len(traeger)
    ziel = np.zeros(m + nt + 1)
    ziel[:m] = strafe
    ziel[m:m + nt] = [-x[j] for j in traeger]
    ziel[-1] = 1.0
    neben = np.zeros((nt + 1, m + nt + 1))
    for k, j in enumerate(traeger):
        neben[k, :m] = -a[:, j]                  # alpha_j - u A_j <= 0
        neben[k, m + k] = 1.0
    neben[nt, :m] = b                            # u b - beta <= 1 - DELTA
    neben[nt, -1] = -1.0
    rechts = np.zeros(nt + 1)
    rechts[nt] = 1.0 - DELTA
    ganz = np.concatenate([np.zeros(m), np.ones(nt + 1)])
    oben = np.concatenate([np.full(m, 1.0 - DELTA), np.full(nt + 1, np.inf)])
    return ziel, neben, rechts, ganz, oben


def exakter_schnitt(u_roh, zeilen) -> tuple:
    """Gleitkomma-Multiplikatoren auf Brüche mit Nenner <= 1000 runden und den Schnitt exakt rechnen: (u, alpha, beta)."""
    u = {}
    for i, v in enumerate(u_roh):
        if v > 1e-7:
            f = Fraction(float(v)).limit_denominator(NENNER)
            if f > 0:
                u[i] = f
    alpha, beta = schnitt_aus(zeilen, u)
    return u, alpha, beta


def _ein_lauf(x, zeilen, strafe: float, zeitgrenze: float):
    from scipy.optimize import Bounds, LinearConstraint, milp

    ziel, neben, rechts, ganz, oben = baue_programm(x, zeilen, strafe)
    return milp(ziel, constraints=LinearConstraint(neben, -np.inf, rechts), integrality=ganz, bounds=Bounds(0, oben),
                options={"mip_rel_gap": 0.0, "time_limit": max(0.01, float(zeitgrenze))})


def trenne_runde(x, zeilen, zeitgrenze: float = 5.0) -> Trennung:
    """Ein verletzter CG-Schnitt der ersten Runde zu x, "keiner" (Löser hat Optimalität gemeldet) oder "offen"."""
    ende = time.perf_counter() + zeitgrenze
    for strafe in (STRAFE, 0.0):
        rest = ende - time.perf_counter()
        if rest <= 0:
            return Trennung("offen")
        res = _ein_lauf(x, zeilen, strafe, rest)
        if res.x is not None:
            u, alpha, beta = exakter_schnitt(res.x[:len(zeilen)], zeilen)
            if float(np.dot(alpha, x)) - beta > VERLETZT_AB:
                return Trennung("verletzt", u, alpha, beta)
        if res.status != 0:
            return Trennung("offen")
        if strafe == 0.0:
            return Trennung("keiner") if -res.fun <= VERLETZT_AB else Trennung("offen")
    return Trennung("offen")


def suche_runde(w, zeilen, optimum: int, budget: float, je_programm: float, max_schritte: int = MAX_SCHRITTE, vorab=None) -> Suche:
    """max w·x über dem ersten Abschluss, durch Nachladen: je Schritt eine Ungleichung des Trenn-Programms. `vorab(x)` liefert
    wahlweise günstige Schnitte der Runde [(u, alpha, beta, Herkunft)] (alle gefundenen je Schritt). Die Suche endet, sobald der
    LP-Wert das Optimum erreicht: Der Wert des Abschlusses kann nicht darunter liegen, weil jede ganzzahlige Lösung jeden Schnitt erfüllt."""
    start = time.perf_counter()
    arbeit = list(zeilen)
    gesehen = set()
    schritte = []
    wert_, x, _ = loese(w, arbeit)
    wert_start = wert_

    def fertig(status, grund=""):
        return Suche(status, optimum, wert_start, wert_, tuple(schritte), tuple(x), grund, time.perf_counter() - start)

    if wert_ <= optimum + GESCHLOSSEN_TOL:
        return fertig(KEINE_LUECKE)
    while True:
        if wert_ <= optimum + GESCHLOSSEN_TOL:
            return fertig(GESCHLOSSEN)
        if len(schritte) >= max_schritte:
            return fertig(NICHT_BESTIMMT, "schritte")
        rest = budget - (time.perf_counter() - start)
        if rest <= 0:
            return fertig(NICHT_BESTIMMT, "zeit")
        neu = {(al, be): (u, art) for u, al, be, art in (vorab(x) if vorab else []) if (al, be) not in gesehen}
        if neu:
            alt = x
            for al, be in neu:
                gesehen.add((al, be))
                arbeit.append((al, be))
            wert_, x, _ = loese(w, arbeit)
            for (al, be), (u, art) in neu.items():
                schritte.append(Schritt(u, al, be, float(np.dot(al, alt)) - be, wert_, art))
            continue
        # u bezieht sich immer auf die Startzeilen: EINE Runde, nie ein Schnitt aus schon nachgeladenen Schnitten
        t = trenne_runde(x, zeilen, min(je_programm, rest))
        if t.status == "keiner":
            return fertig(OFFEN_BEWIESEN)
        if t.status != "verletzt" or (t.alpha, t.beta) in gesehen:
            grund = "zeit" if time.perf_counter() - start >= budget - 0.01 or t.status == "offen" else "loeser"
            return fertig(NICHT_BESTIMMT, grund)
        verletzung = float(np.dot(t.alpha, x)) - t.beta
        gesehen.add((t.alpha, t.beta))
        arbeit.append((t.alpha, t.beta))
        wert_, x, _ = loese(w, arbeit)
        schritte.append(Schritt(t.u, t.alpha, t.beta, verletzung, wert_))
