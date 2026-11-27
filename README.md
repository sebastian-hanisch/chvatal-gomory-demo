# Chvátal-Gomory: fehlende Ungleichungen durch Abrunden – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-chvatal-gomory-demo.streamlit.app/)** -->

Teil der Reihe „Fehlende Ungleichungen: Polyedrische Kombinatorik“. Davor liegen die stabilen Mengen
([stabile-mengen-polytop-demo](https://github.com/sebastian-hanisch/stabile-mengen-polytop-demo): welche Familien dem LP fehlen), daneben das
Matching ([matching-polytop-demo](https://github.com/sebastian-hanisch/matching-polytop-demo): die Ungleichungen für ungerade Mengen). Dort
wurden die fehlenden Ungleichungen **nachgeschlagen**; hier werden sie **erzeugt**: Zeilen einer Beschreibung gewichtet addieren, dann die
Koeffizienten und die rechte Seite abrunden (Chvátal-Gomory-Schnitt).

## Warum dieses Problem

Ein CG-Schnitt ist ohne jede Kenntnis der Struktur gültig: Seine Gewichte sind der Gültigkeitsbeweis. Die Kernfrage ist: **Kann man die
fehlenden Ungleichungen erzeugen, statt sie nachzuschlagen, und wie oft muss man dafür abrunden?** Beantwortet wird sie für das Matching, für
stabile Mengen aus Kanten- und aus Cliquenzeilen, für eine Sammlung kleiner und mittlerer Graphen und für einen Graphen mit 13 Knoten, dem eine
Runde nicht genügt. Alle Instanzen sind ausgedachte Beispielgraphen, keine echten Daten.

## Modell

Beschreibung $P = \{x \ge 0 : Ax \le b\}$ mit ganzen Zahlen. Für Gewichte $u \ge 0$ gilt $\lfloor u^{\mathsf T}A \rfloor x \le \lfloor u^{\mathsf T}b \rfloor$ für
jeden ganzzahligen Punkt von $P$. Alle solchen Schnitte zugleich geben eine **Chvátal-Runde**; der **Chvátal-Rang** ist die Zahl der Runden bis
zur ganzzahligen Hülle und gehört immer zu einer genannten **Startbeschreibung**:

| Startbeschreibung | Zeilen |
|---|---|
| Gradzeilen (Matching) | je Knoten: Summe der gewählten Kanten an ihm ≤ 1; Variablen sind die Kanten |
| Kantenzeilen (stabile Mengen) | je Kante x_u + x_v ≤ 1 |
| Cliquenzeilen (stabile Mengen) | je maximaler Clique C: Summe der x_v über C ≤ 1 |

Eine **Chvátal-Runde** (alle Schnitte zugleich) ist etwas anderes als ein **Nachladeschritt** (eine Ungleichung dazunehmen und das LP neu lösen).
Formeln und Herleitungen stehen im Expander „📐 Mathematische Formulierung“ der App.

## Methodik

- **Schnitte und Zertifikate** rechnet die App mit Brüchen (`cvg_schnitt.py`). Jeder angezeigte Schnitt wird gegen alle ganzzahligen Lösungen
  geprüft (bei stabilen Mengen über das größte Gewicht der Koeffizienten): in den Experimenten 1, 2, 4 und 6 live in der App, die Schnitte zum
  13-Knoten-Graphen (Experiment 5) in den Tests.
- **Bekannte Familien als Schnitte** (`cvg_familien.py`): ungerader Kreis mit ½ auf je einer Clique je Kreiskante, ungerades Rad mit ½ auf je
  einer Clique je Dreieck, Antiloch mit 2k+1 Knoten mit 1/k auf 2k+1 Cliquen. Kreise und Räder werden exakt getrennt (kürzester ungerader
  Weg), Antilöcher ab 7 Knoten vorab vollständig aufgezählt.
- **Facetten und Sammlung** (`tools/cvg_make_katalog.py` → `cvg_katalog.json`): alle nichtperfekten Graphen mit 5 bis 7 Knoten (eigene
  Aufzählung bis auf Umnummerieren), ganze Hülle mit ganzen Zahlen (doppelte Beschreibung, nachgeprüft), je Facette ein Zertifikat aus einer
  Cliquenüberdeckung, mit Brüchen geprüft. Für die Instanzen mit 20 Knoten: Schnitte aus den Familien und aus dem Trenn-Programm, bis der
  LP-Wert das Optimum erreicht, danach ein **exakter Dualbeweis** in Brüchen. `--check` rechnet die Auswahl neu und prüft jedes Zertifikat
  (nicht, ob der Löser unter Linux dieselben Gewichte fände).
- **Trenn-Programm** (`cvg_trennung.py`, eigene Formulierung, `scipy.optimize.milp` mit HiGHS): Gewichte u in [0; 0,999], ganze Koeffizienten
  unterhalb uA, ganze rechte Seite oberhalb ub − 0,999; gesucht ist die größte Verletzung abzüglich 0,0001 mal der Summe der u. Findet dieser
  Lauf nichts, rechnet ein zweiter ohne den Strafterm nach; erst seine Optimalitätsmeldung heißt „keiner verletzt“. Jeder Schnitt wird aus
  den auf Nenner ≤ 1000 gerundeten Gewichten exakt neu gerechnet. Harte Zeitgrenzen je Programm und je Suche; läuft eine ab, ist der Ausgang
  **„nicht bestimmt“**, und der LP-Wert ist nur eine obere Schranke für den Wert der Runde. Die Suche endet, sobald der LP-Wert das Optimum
  erreicht: Der Wert der Runde kann nicht darunter liegen.
- **Sechs Experimente** in der App: selbst abrunden (acht Handbeispiele), Matching, Cliquen aus Kantenzeilen, eine Runde über den Cliquen
  (Sammlung), der Graph mit 13 Knoten, die Live-Suche mit 8 bis 16 Knoten und die vorgerechneten Reihen mit 20 und 30 Knoten.

## Befunde (gemessen, keine Behauptungen)

| Frage | Befund | Voraussetzung / Zähleinheit | Test |
|---|---|---|---|
| Matching: wie viele Runden über den Gradzeilen? | Bei nichtbipartiten Graphen genau 1, bei bipartiten 0. Jede Ungleichung x(E[U]) ≤ (\|U\|−1)/2 entsteht aus Gewichten ½ | nachgerechnet für alle 63.887 Paare (Graph, ungerade Menge ab 3 Knoten) der 1.245 Graphen mit 2 bis 7 Knoten und mindestens einer Kante; „Hülle“ nach dem Satz von Edmonds; nur das nicht perfekte Matching | `test_oracle_chvatal_gomory.py`, `test_claims.py` |
| Was liefert eine Runde über den Kantenzeilen? | Kanten und ungerade Kreise (eigene Herleitung) | Graphen ohne isolierte Knoten; geprüft: exakt jeder Schnitt mit Gewichten in Halben bzw. in Dritteln auf allen Graphen mit 5 Knoten, höchstens 6 Kanten und ohne isolierte Knoten; auf Zufallsgraphen mit 6 bis 9 Knoten erreicht die Suche über den Kantenzeilen den LP-Wert mit allen ungeraden Kreisen | `test_oracle_chvatal_gomory.py` |
| Chvátal-Rang der Clique mit k Knoten aus den Kantenzeilen | genau ⌈log₂(k−1)⌉ (obere Schranke durch Mitteln, untere eigene Herleitung); größtes x(K) nach r Runden: max(1, k/(2^r+1)) | Herleitung für jedes k; unabhängig vom Beweis der unteren Schranke geprüft: x = ⅓ übersteht Runde 1 auf K4 bis K6, x = ⅕ Runde 2 auf K6, wobei die erste Runde nach der Zeile darüber als Kanten und ungerade Kreise angesetzt ist (exakt für alle ganzen Zielvektoren mit Einträgen 0 bis 4 bzw. 0 bis 3) | `test_oracle_chvatal_gomory.py`, `test_claims.py` |
| Wie weit reichen Cliquen und ungerade Kreise auf kleinen Graphen? | Von 200 Facetten jenseits der Cliquen liefern die ungeraden Kreise dazu 103 (Wert gleich der rechten Seite), ihre ganze Hülle ist damit bei 68 von 147 Graphen beschrieben | alle 147 nichtperfekten Graphen mit 5 bis 7 Knoten bis auf Isomorphie; Werte exakt aus den Ecken | `test_claims.py` |
| Eine Runde über den Cliquenzeilen, 5 bis 7 Knoten | Alle 200 Facetten, also die ganze Hülle auf 147 von 147 Graphen: **Chvátal-Rang über den Cliquenzeilen genau 1** | dieselben Graphen; je Facette ein mit Brüchen geprüftes Zertifikat, kein MILP | `test_claims.py`, `test_oracle_chvatal_gomory.py` |
| Eine Runde über den Cliquen, Rest mit 20 Knoten | 47 von 47 geschlossen | je 200 Instanzen aus G(20; 0,2 / 0,4 / 0,6) und K(20; 10; 200 / 400), Werte 1 bis 100, Zufalls-Seeds in der Datei: 47 von 1.000 offen nach Cliquen, ungeraden Kreisen, Antilöchern und Rädern (4, 11, 9, 5, 18). Je Instanz **ein** Wertvektor, nicht die Hülle; Beweis durch Dualwerte in Brüchen | `test_claims.py`, `test_eingefroren.py` |
| Genügt eine Runde über den Cliquen immer? | **Nein:** Beim Komplement des Kreisgraphen C13(1, 5) ist der Chvátal-Rang genau 2 (eigene Herleitung) | 13 Knoten, 52 Kanten, 39 maximale Cliquen, 40 stabile Mengen (mit der leeren), α = 2, ω = 4; ganze Hülle exakt: 92 Facetten, davon 13 x_v ≥ 0 und 39 Cliquen, 39 weitere in Runde 1, nur x(V) ≤ 2 erst in Runde 2 | `test_claims.py`, `test_oracle_chvatal_gomory.py` |
| Größtes x(V) dieses Graphen je Runde | 13/4 (Cliquen), **26/11** (nach Runde 1), 2 (nach Runde 2) | exakt: x = 2/11 übersteht jeden Schnitt der ersten Runde; 13 Schnitte zu je 11 Knoten geben 11·x(V) ≤ 26 | `test_claims.py`, `test_oracle_chvatal_gomory.py` |
| Wie viele Verschiebungen genügen der zweiten Runde in fester Reihenfolge? | Folgen mit 9 Knoten: alle 13; mit 10 Knoten: ab 10; mit 11 Knoten: ab 7 | Schnitte zu den Starts 0, 1, 2, … in dieser Reihenfolge; keine Mindestzahl bei freier Wahl der Starts | `test_kern.py`, `test_claims.py` |

Es genügen auch 12 Knoten: Ohne einen Knoten (12 Knoten) hat der Graph ebenfalls eine Facette x(V) ≤ 2 außerhalb der ersten Runde (kleinste
Cliquenüberdeckung 3). **Welcher kleinste Graph mehr als eine Runde braucht, ist nicht untersucht** (bis 7 Knoten keiner, siehe oben; 8 bis 11
Knoten offen). Der Graph mit 13 Knoten ist nicht als kleinster gemeint.

### Was das Finden kostet

Die Zahlen dieses Abschnitts sind **einmal gemessen** (scipy 1.18.1 mit HiGHS, Python 3.14.6 unter Windows, SplitMix64-Instanzen,
G(n; 0,4)) und liegen mit allen Schnitten in `cvg_messungen.json`; `--check` rechnet jeden Schnitt exakt nach. Zahl der Schnitte, Zeiten und
der Anteil „nicht bestimmt“ hängen am Löser, am Budget und am Rechner (der Rechner war dabei belastet).

**Live-Suche (ohne vorab geladene Kreise).** Je 40 Graphen (Zufalls-Seeds 26200 bis 26239), höchstens 20 s je Graph und 10 s je Programm;
Sekunden nur für Graphen mit Lücke nach den Cliquen.

| Knoten | Gewichte | mit Lücke | geschlossen | mit Runde offen | nicht bestimmt | Sekunden (Median) | Sekunden (größte) |
|---|---|---|---|---|---|---|---|
| 8 | alle 1 | 3 | 3 | 0 | 0 | 0,02 | 0,02 |
| 12 | alle 1 | 2 | 2 | 0 | 0 | 0,04 | 0,05 |
| 16 | alle 1 | 14 | 13 | 1 | 0 | 0,52 | 5,16 |
| 20 | alle 1 | 13 | 12 | 0 | 1 | 3,32 | 20,01 |
| 8 | Werte 1 bis 100 | 1 | 1 | 0 | 0 | 0,04 | 0,04 |
| 12 | Werte 1 bis 100 | 0 | 0 | 0 | 0 | – | – |
| 16 | Werte 1 bis 100 | 4 | 4 | 0 | 0 | 0,17 | 0,45 |
| 20 | Werte 1 bis 100 | 5 | 5 | 0 | 0 | 0,30 | 0,85 |

In dieser Messung brauchte die Suche bis 16 Knoten höchstens 5,2 s je Graph; die App sucht deshalb live nur bis 16 Knoten, mit einer
Zeitgrenze von 1 bis 10 s (Voreinstellung 5 s, knapp unter der längsten hier gemessenen Suche). „Mit Runde offen“ heißt: Der Löser meldet, kein Schnitt der ersten Runde sei mehr verletzt (bis auf Toleranzen und
u ≤ 0,999); ein exaktes Zertifikat dafür gibt es nicht. Den einen solchen Fall der Messreihe (16 Knoten, Zufalls-Seed 26207) rechnet ein Test mit SCIP
als zweitem Löser nach, mit demselben Ergebnis, ebenfalls in Gleitkommazahlen. Live in der App rechnet nur HiGHS.

**Größere Graphen (mit vorab geladenen Kreisschnitten).** Gewichte alle 1, Zufalls-Seeds ab 26100 (100 Graphen mit 20, 30 mit 30 Knoten);
vorab alle verletzten ungeraden Kreise als Schnitte der Runde, dann das Trenn-Programm; höchstens 25 s je Graph und 8 s je Programm.

| Knoten | Graphen | Lücke mit Cliquen | Lücke auch mit Kreisen | davon durch die Runde geschlossen | mit Runde offen | nicht bestimmt |
|---|---|---|---|---|---|---|
| 20 | 100 | 43 | 38 | 37 | 0 | 1 |
| 30 | 30 | 28 | 28 | 6 | 0 | 22 |

Mittlere Lücke (LP-Wert − Optimum)/Optimum über alle Graphen der Größe, nach den Cliquen und mit ungeraden Kreisen (beides reine LP-Werte):
bei 20 Knoten 3,70 % und 2,44 %, bei 30 Knoten 8,27 % und 7,67 %. **Bei 30 Knoten war der Wert der Runde in
22 von 30 Graphen mit diesem Budget nicht bestimmbar.** Das ist eine Eigenschaft von Löser, Budget und Rechner, kein Befund über die
Runde: Für diese Graphen steht nur fest, dass die Runde **mindestens** so viel schließt wie erreicht. Das Finden ist hier selbst ein
gemischt-ganzzahliges Programm.

## Befunde und Korrekturen gegenüber früheren Rechnungen

- **Weniger als 13 Verschiebungen reichen manchmal.** Eine frühere Fassung sagte, mit weniger als 13 Verschiebungen ergebe die Summe keine
  Ungleichung für x(V). Das stimmt nur für die Folgen mit 9 Knoten. Wegen x ≥ 0 genügt, dass jeder Knoten mindestens m-mal vorkommt; bei 11
  Knoten reichen die ersten 7 Verschiebungen (5·x(V) ≤ 14), bei 10 Knoten die ersten 10. Die App rechnet das für jede Einstellung aus.
- **„Keiner verletzt“ braucht einen Lauf ohne Strafterm.** Mit dem Strafterm 0,0001·Σu allein hätte das Programm eine kleine Verletzung bei
  großer Gewichtssumme als „keiner“ melden können. Es rechnet deshalb ohne Strafe nach, bevor es „keiner“ meldet.
- **26/11 ist exakt, nicht nur eine Messung des Lösers:** x = 2/11 übersteht jeden Schnitt der ersten Runde (dieselbe Fallunterscheidung wie
  bei x = ⅙).
- **Die 47 Fälle mit 20 Knoten haben jetzt einen exakten Beweis** (Dualwerte in Brüchen) statt eines LP-Werts bis auf Toleranzen; dieselbe
  Auswahl wurde mit eigener Trennung neu bestimmt.
- **Die ganze Hülle der kleinen Graphen ist ohne MILP belegt:** je Facette ein Zertifikat aus einer Cliquenüberdeckung.

## Ehrliche Grenzen

- Die als **eigene Herleitung** bezeichneten Aussagen (erste Runde über den Kanten, untere Schranke des Cliquenrangs, größtes x(K) nach r
  Runden, Rang 2 beim Graphen mit 13 Knoten) sind **nicht extern geprüft**; Tests sichern sie nur auf Instanzen ab.
- „Eine Runde über den Cliquen genügt“ ist **nur** für die 147 Graphen mit 5 bis 7 Knoten belegt; die 47 Fälle mit 20 Knoten betreffen je einen
  Wertvektor.
- Die Live-Suche und die vorgerechneten Reihen hängen am Löser, am Budget und am Rechner: Zahl der Schnitte, Nenner, Zeiten und der Anteil
  „nicht bestimmt“ sind nicht wiederholbar. Ein abgebrochenes „nichts gefunden“ beweist nicht „nichts verletzt“.
- „Kein Schnitt mehr verletzt“ beruht auf HiGHS in Gleitkomma, der Grenze u ≤ 0,999 und der Schwelle 10⁻⁵; ein exaktes Zertifikat dafür gibt es
  hier nicht.
- Ein gefundener Schnitt hat keinen Namen und keine Garantie, eine Facette zu sein.
- Rundreise und Rucksack sind nicht gemessen; ob Kämme in einer Runde entstehen, ist hier weder gemessen noch belegt. Das perfekte Matching mit
  Gleichungen ist nicht behandelt.
- Literatur: Der CG-Schritt ist Lehrbuchstoff; dass der erste Abschluss eines rationalen Polyeders wieder ein Polyeder ist, stammt von Schrijver
  (1980, hier nach einem Referat, Original nicht gelesen); der Satz von Edmonds zum Matching-Polytop nach Schrijver, *A Course in
  Combinatorial Optimization*, Korollar 5.6b. Weitere Originale wurden nicht gelesen.

## Bewusst nicht umgesetzt

- Gomory-Schnitte aus dem Simplex-Tableau: nur genannt (eine Rechenvorschrift für bestimmte Gewichte; ihre Folge hängt an Basis und
  Zeilenwahl; Simplex siehe [dualer-simplex-demo](https://github.com/sebastian-hanisch/dualer-simplex-demo)).
- Abrunden an anderen Modellen: Beim Netzentwurf mit Fixkosten
  ([fixkosten-netzdesign-demo](https://github.com/sebastian-hanisch/fixkosten-netzdesign-demo)) kommt dasselbe Abrunden an Schnittmengen
  vor; Cover-Schnitte am Rucksack zeigen [cutting-planes-demo](https://github.com/sebastian-hanisch/cutting-planes-demo) und
  [branch-cut-demo](https://github.com/sebastian-hanisch/branch-cut-demo).
- Die Suche nach dem kleinsten Graphen, dem eine Runde nicht genügt, und Graphen mit Rang 3 oder mehr über den Cliquen.
- Ganze Hüllen und Chvátal-Ränge auf Graphen mit mehr als 13 Knoten.

## Verifikation

- **Einheiten** an Mini-Instanzen von Hand (`tests/test_kern.py`): Abrunden, Matching- und Cliquengewichte, Familienzertifikate, Trennung,
  Suche mit allen vier Ausgängen, exakte Dualbeweise.
- **Orakel** (`tests/test_oracle_chvatal_gomory.py`): networkx (Cliquen, induzierte und alle Kreise, größte stabile Menge, Graphenatlas,
  Matching), Aufzählung aller Gewichte mit kleinen Nennern, exakte Ecken, der Rechenschritt der unteren Cliquenschranke für viele ganze
  Vektoren. Die gespeicherten Schnitte werden gegen alle stabilen Mengen geprüft.
- **Eigenschaften** (`tests/test_eigenschaften_chvatal_gomory.py`): ganzzahlige Lösungen überstehen jeden Schnitt, ganzzahliger Gewichtsanteil
  ist überflüssig, Umnummerieren ändert keine Werte, Monotonie, gleicher Zufalls-Seed in zwei Prozessen.
- **Zahlen dieser README** (`tests/test_claims.py`), Verdikte (`tests/test_verdicts.py`), Randfälle, Presets, Layout, ausgeblendete Regler,
  AppTest, PDF, Kopier-Tests, `--check` beider Erzeugerskripte, zweite Prüfwege (`tests/test_zweitpruefung.py`: SCIP für den offenen Fall, Schnitte zum 13-Knoten-Graphen).

**Anzahl:** 369 Tests.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App mit sechs Experimenten |
| `cvg_schnitt.py` | CG-Schnitt mit Brüchen, Matching- und Cliquengewichte, Rang der Clique |
| `cvg_graphen.py` | Cliquen, stabile Mengen, größtes Gewicht, Kreise, Graph mit 13 Knoten |
| `cvg_familien.py`, `cvg_leiter.py` | Trennung von Kreisen, Rädern, Antilöchern; ihre Gewichte; die Leiter der Werte |
| `cvg_lp.py` | LP (HiGHS), Zertifikat einer Facette, exakter Dualbeweis |
| `cvg_trennung.py` | das einzige Modul mit `milp`: Trenn-Programm und Suche mit Zeitgrenzen |
| `cvg_zeuge.py` | der Graph mit 13 Knoten: Beweisfälle, Zertifikate, zweite Runde |
| `cvg_beispiele.py` | Handbeispiele mit festen Knotenlagen |
| `cvg_katalog.py`, `cvg_katalog.json` | eingefrorene Sammlung und ihre exakte Prüfung |
| `cvg_messung.py`, `cvg_messungen.json` | eingefrorene Messreihen und ihre Prüfung |
| `tools/cvg_make_katalog.py`, `tools/cvg_make_messungen.py` | Erzeugerskripte mit `--check` |
| `cvg_evaluation.py` | Rechnungen der Experimente und Verdikte |
| `cvg_visualization.py`, `cvg_pdf_export.py`, `cvg_layout.py`, `cvg_presets.py`, `cvg_constants.py` | Abbildungen, PDF, Kopf, Presets, Konstanten |
| `cvg_rng.py`, `cvg_konflikt.py`, `cvg_dd.py` | Kopien aus [ganzzahlige-ecken-demo](https://github.com/sebastian-hanisch/ganzzahlige-ecken-demo) (SplitMix64, Graphenfamilien, doppelte Beschreibung) |
| `modul_frisch.py` | lädt geänderte Hilfsmodule nach einem Update neu |
| `tests/` | siehe Verifikation |

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy, SciPy, pandas und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Fehlende Ungleichungen: von Ecken bis Runden](https://sebastianhanisch.net/konzepte-polyeder.html).
