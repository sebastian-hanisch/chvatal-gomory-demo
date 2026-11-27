"""Chvátal-Gomory: fehlende Ungleichungen durch Abrunden - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Kann man die Ungleichungen, die einem LP zur ganzzahligen Hülle fehlen, erzeugen statt sie nachzuschlagen, und wie oft muss man dafür
abrunden? Sechs Experimente: selbst abrunden, Matching, Cliquen aus Kantenzeilen, eine Runde über den Cliquen, ein Graph, dem eine
Runde nicht genügt, und die Suche nach den Multiplikatoren.

Lauffähig mit: streamlit run app.py
"""

from fractions import Fraction

import pandas as pd
import streamlit as st

import cvg_beispiele as B
import cvg_constants as C
import cvg_evaluation as E
import cvg_katalog as K
import cvg_messung as M
import cvg_pdf_export as PDF
import cvg_schnitt as S
import cvg_visualization as V
import cvg_zeuge as Z
from cvg_graphen import groesstes_gewicht, maximale_cliquen
from cvg_layout import dunkles_design, kopf_css
from cvg_presets import (
    aktives_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    merke,
    neuer_seed,
    seed_widget,
    setze_loesung,
    sidebar_presets,
    sync_query_params,
    wechsle_beispiel,
    wechsle_graph,
    wechsle_matchinggraph,
    wert,
)
import modul_frisch

modul_frisch.aktualisieren(__file__)      # geänderte Hilfsmodule nach einem Update neu laden (die Cloud behält sie sonst bis zum Neustart)

st.set_page_config(page_title="Chvátal-Gomory – Sebastian Hanisch", layout="wide")

REPO = "https://github.com/sebastian-hanisch/"


@st.cache_data(show_spinner=False, max_entries=64)
def _abrunden(schluessel, u):
    return E.ergebnis_abrunden(schluessel, u)


@st.cache_data(show_spinner=False, max_entries=128)
def _matching(schluessel, menge):
    return E.ergebnis_matching(schluessel, menge)


@st.cache_data(show_spinner=False, max_entries=64)
def _leiter(fall):
    return E.leiter_zwanzig(K.lade()["zwanzig"][fall])


@st.cache_data(show_spinner=False)
def _facetten13():
    return E.facetten13()


@st.cache_data(show_spinner=False, max_entries=64)
def _suche(n, gewichte, seed, budget):
    return E.suche_live(n, gewichte, seed, float(budget))


@st.cache_data(show_spinner=False)
def _vorgerechnet():
    daten = M.lade()
    return M.zusammenfassung_gross(daten["gross"]), M.zusammenfassung_raster(daten["raster"]), daten


def zeige(verdikt):
    art, text = verdikt
    getattr(st, art)(text)


def tabelle(spalten: dict):
    st.dataframe(pd.DataFrame(spalten), hide_index=True, width="stretch")


def menge_text(knoten, namen) -> str:
    return "{" + ", ".join(namen[v] for v in knoten) + "}"


def multiplikator_text(u: dict, zeilennamen) -> str:
    """'½ · Clique abf, ½ · Clique bcf' für Multiplikatoren {Zeile: Bruch}."""
    return ", ".join(f"{S.bruch(f)} · {zeilennamen[i]}" for i, f in sorted(u.items()))


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in cvg_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧩 Chvátal-Gomory: fehlende Ungleichungen durch Abrunden")
st.markdown(
    f"""
Bei [stabilen Mengen]({REPO}stabile-mengen-polytop-demo) und beim [Matching]({REPO}matching-polytop-demo) wurden die fehlenden Ungleichungen aus
**bekannten Familien** nachgeschlagen. Der **Chvátal-Gomory-Schnitt** erzeugt sie selbst: Zeilen gewichtet addieren, dann **abrunden**.
Die App zeigt, was eine **Chvátal-Runde** leistet, wann man mehrere braucht und was das **Finden** der Gewichte kostet.
Unten folgen sechs Experimente (🔬), der Abschnitt **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert Chvátal-Gomory", expanded=True):
    st.markdown(
        r"""
1. **Start:** eine Beschreibung $Ax \le b$, $x \ge 0$ mit ganzen Zahlen, etwa je Kante $x_u + x_v \le 1$. Alle gesuchten ganzzahligen
   Lösungen erfüllen sie, aber ihre Ecken sind zum Teil gebrochen.
2. **Addieren:** Man wählt Gewichte $u \ge 0$ und addiert die Zeilen damit. Das Ergebnis gilt für jede Lösung des LP.
3. **Abrunden:** Erst werden die Koeffizienten auf ganze Zahlen abgerundet (wegen $x \ge 0$ wird die linke Seite höchstens kleiner), dann die
   rechte Seite (bei ganzzahligem $x$ ist die linke Seite eine ganze Zahl). Die neue Ungleichung gilt für **jede ganzzahlige** Lösung, kann
   aber gebrochene Ecken abschneiden.
4. **Runden zählen:** Alle solchen Schnitte zugleich bilden eine **Chvátal-Runde**. Der **Chvátal-Rang** ist die Zahl der Runden bis zur
   ganzzahligen Hülle und gehört immer zu einer genannten Startbeschreibung.
        """
    )

with st.expander("Begriffe, Startbeschreibungen und Familien", expanded=True):
    tabelle({"Begriff": [z[0] for z in C.BEGRIFFE], "Was ist das?": [z[1] for z in C.BEGRIFFE],
             "Beispiel": [z[2] for z in C.BEGRIFFE]})
    tabelle({"Startbeschreibung": [z[0] for z in C.STARTBESCHREIBUNGEN], "Zeilen": [z[1] for z in C.STARTBESCHREIBUNGEN]})
    tabelle({"Familie": [z[0] for z in C.FAMILIEN], "Ungleichung": [z[1] for z in C.FAMILIEN],
             "Gewichte über den Cliquenzeilen": [z[2] for z in C.FAMILIEN]})
    st.caption("$x(S)$ ist die Summe der $x_v$ über die Knoten in $S$. Eine **stabile Menge** ist eine Knotenmenge ohne Kante; α ist die "
               "Größe einer größten, ω die Größe einer größten Clique. Jede Familie entsteht in einer Chvátal-Runde aus den Cliquenzeilen.")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.caption("Die Regler stehen bei den einzelnen Experimenten.")

befunde = {}      # Überschrift -> Absätze für das PDF

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Kann man die fehlenden Ungleichungen erzeugen, und wie oft muss man dafür abrunden?")
uebersicht = E.ueberblick()
tabelle({"Aufgabe": [z[0] for z in uebersicht], "Startbeschreibung": [z[1] for z in uebersicht],
         "Chvátal-Runden bis zur ganzzahligen Hülle": [z[2] for z in uebersicht], "Beleg": [z[3] for z in uebersicht]})
zeige(E.verdict_kernfrage(S.cliquen_rang(6), len(_facetten13()["ausserhalb"])))

st.markdown("---")

# --- 1 Selbst abrunden ---------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Selbst abrunden")
st.caption("Je Zeile der Startbeschreibung ein Gewicht u wählen. Rechts stehen die gewichtete Summe und das Ergebnis des Abrundens, alles "
           "mit Brüchen gerechnet.")
c1, c2 = st.columns([2, 1])
c1.selectbox("Handbeispiel und Startbeschreibung", list(B.HANDFAELLE), format_func=C.hand_titel, key="e1_select",
             on_change=wechsle_beispiel)
c2.button("✍️ Gewichte von Hand einsetzen", width="stretch", on_click=setze_loesung,
          help="Setzt die Gewichte, mit denen man den Schnitt von Hand findet (bei Cliquenzeilen am Dreieck und an K4: nichts zu tun).")
beschreibung = B.startbeschreibung(B.HANDFAELLE[st.session_state["e1_select"]])
spalten = st.columns(4)
for i, name in enumerate(beschreibung.zeilennamen):
    schluessel = f"u{i}_select"
    seed_widget(schluessel)
    spalten[i % 4].selectbox(f"u: {name}", list(B.MULTIPLIKATOREN), key=schluessel,
                             help=S.ungleichung_text(*beschreibung.zeilen[i], namen=beschreibung.variablen))
    merke(schluessel)
a = _abrunden(st.session_state["e1_select"], tuple(wert(f"u{i}_select") for i in range(len(beschreibung.zeilen))))
if not a.gueltig:
    st.error("Prüfung fehlgeschlagen: Der Schnitt schneidet eine ganzzahlige Lösung ab. Das dürfte nie vorkommen.")

links, rechts = st.columns([1, 2])
with links:
    g = a.fall.bild
    if a.fall.start == "grade":
        st.plotly_chart(V.kantenwerte(g.lage, g.kanten, [S.bruch(v) for v in a.ecke], g.namen), width="stretch", key="e1_graph")
        st.caption("Zahlen an den Kanten: eine LP-Ecke mit größter Summe.")
    else:
        st.plotly_chart(V.zeichne_graph(g.lage, g.kanten, g.namen, werte=[S.bruch(v) for v in a.ecke]), width="stretch",
                        key="e1_graph")
        st.caption("Zahlen an den Knoten: eine LP-Ecke mit größter Summe.")
with rechts:
    tabelle({"Zeile": list(beschreibung.zeilennamen),
             "Ungleichung": [S.ungleichung_text(*z, namen=beschreibung.variablen) for z in beschreibung.zeilen],
             "Gewicht u": [S.bruch(v) for v in a.u]})
    tabelle({"": ["gewichtete Summe", "abgerundet"],
             **{n: [S.bruch(a.links[j]), str(a.alpha[j])] for j, n in enumerate(beschreibung.variablen)},
             "rechte Seite": [S.bruch(a.rechts), str(a.beta)]})
    m1, m2, m3 = st.columns(3)
    m1.metric("Größte Summe, Startbeschreibung", S.bruch(a.lp_vorher))
    m2.metric("… mit dem Schnitt", E.zahl_oder_bruch(a.lp_nachher))
    m3.metric("… ganzzahlig", str(a.ganz_optimum))
zeige(E.verdict_abrunden(a))
befunde["Selbst abrunden: " + a.fall.titel] = [E.verdict_abrunden(a)[1]]

st.markdown("---")

# --- 2 Matching ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Beim Matching genügt eine Runde")
st.caption("Ein Matching wählt Kanten ohne gemeinsamen Knoten. Die Gradzeilen der Knoten in U werden je mit ½ addiert.")
c1, c2 = st.columns([1, 2])
c1.selectbox("Graph", list(B.MATCHINGGRAPHEN), format_func=lambda k: B.MATCHINGGRAPHEN[k][0].name, key="m_select",
             on_change=wechsle_matchinggraph)
bild = B.MATCHINGGRAPHEN[st.session_state["m_select"]][0]
c2.multiselect("Knotenmenge U", list(range(bild.n)), format_func=lambda v: bild.namen[v], key="m_menge")
m = _matching(st.session_state["m_select"], tuple(wert("m_menge")))
if not m.gueltig:
    st.error("Prüfung fehlgeschlagen: Der Schnitt schneidet ein Matching ab. Das dürfte nie vorkommen.")
links, rechts = st.columns([1, 2])
with links:
    st.plotly_chart(V.kantenwerte(bild.lage, bild.kanten, [S.bruch(v) if v else "" for v in m.ecke], bild.namen, markiert=m.U,
                                  innen=m.innen, rand=m.rand), width="stretch", key="m_graph")
    st.caption("Gelb: U. Grün: Kanten in U. Rot gepunktet: Kanten mit einem Ende in U. Zahlen: eine LP-Ecke des Grad-LP mit größter Summe "
               "(Kanten mit 0 ohne Zahl).")
with rechts:
    ordnung = list(m.innen) + list(m.rand) + [i for i in range(len(bild.kanten)) if i not in m.innen and i not in m.rand]
    lage_text = {i: "in U" for i in m.innen} | {i: "am Rand" for i in m.rand}
    tabelle({"Kante": [bild.namen[bild.kanten[i][0]] + "–" + bild.namen[bild.kanten[i][1]] for i in ordnung],
             "Lage": [lage_text.get(i, "außerhalb") for i in ordnung],
             "Koeffizient in der halben Summe": [S.bruch(m.links[i]) for i in ordnung],
             "abgerundet": [str(m.alpha[i]) for i in ordnung]})
    st.markdown(f"Rechte Seite: ½ · {len(m.U)} = **{S.bruch(m.rechts)}**, abgerundet **{m.beta}**.")
    m1, m2, m3 = st.columns(3)
    m1.metric("Grad-LP, größtes Matching", S.bruch(m.lp_vorher))
    m2.metric("… mit dieser Ungleichung", E.zahl_oder_bruch(m.lp_nachher))
    m3.metric("… ganzzahlig", str(m.ganz_optimum))
zeige(E.verdict_matching(m))
befunde["Matching: " + bild.name + ", U = " + menge_text(m.U, bild.namen)] = [E.verdict_matching(m)[1]]

st.markdown("---")

# --- 3 Cliquen -----------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Wie viele Runden braucht eine Clique?")
st.caption("Start sind nur die Kantenzeilen einer Clique mit k Knoten. Nach wie vielen Runden folgt x(K) ≤ 1? Rechnung nach einer eigenen "
           "Herleitung (siehe 📐), nicht mit einem Löser.")
c1, c2 = st.columns(2)
c1.slider("Cliquengröße k", *bounds("k_slider"), key="k_slider")
c2.slider("Runden r", *bounds("r_slider"), key="r_slider")
k, r = int(st.session_state["k_slider"]), int(st.session_state["r_slider"])
rang = S.cliquen_rang(k)
links, rechts = st.columns([3, 2])
with links:
    stufen = S.treppenstufen(max(rang, 1))
    zeilen_ = []
    for runde, aus, bis in stufen:
        ziel = min(bis, k) if runde >= rang else bis
        mengen, gewicht = S.cliquen_multiplikatoren(ziel, aus)
        zeilen_.append((runde, aus, bis, f"{len(mengen)} Cliquen mit {aus} Knoten in K{ziel}, je {S.bruch(gewicht)}"))
    tabelle({"Runde": [z[0] for z in zeilen_], "aus Cliquen bis": [z[1] for z in zeilen_], "entstehen Cliquen bis": [z[2] for z in zeilen_],
             "Gewichte für die größte (höchstens bis k)": [z[3] for z in zeilen_]})
    st.caption("Obere Schranke: Mittelt man alle Cliquen mit m Knoten innerhalb einer Clique mit höchstens 2m − 1 Knoten, so rundet die "
               "rechte Seite auf 1. Also 2 → 3 → 5 → 9 → 17.")
with rechts:
    verlauf = E.clique_verlauf(k, C.R_MAX)
    st.plotly_chart(V.balken([f"{rr}" for rr, _ in verlauf], [float(v) for _, v in verlauf], [S.bruch(v) for _, v in verlauf], ziel=1,
                             ziel_name="ganzzahlig: 1", achse=f"größtes x(K{k})", hervor=r, hoehe=280), width="stretch",
                    key="k_chart")
    punkt = S.punkt_nach_runden(r)
    st.caption(f"Nach r = {r} Runden übersteht x = {S.bruch(punkt)} an jedem Knoten (Summe {S.bruch(k * punkt)}). Waagerecht: "
               "Rundenzahl.")
zeige(E.verdict_clique(k, r))
befunde[f"Cliquen: k = {k}, r = {r}"] = [E.verdict_clique(k, r)[1]]

st.markdown("---")

# --- 4 Eine Runde über den Cliquen -------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Eine Runde über den Cliquen")
st.caption("Start sind die Cliquenzeilen. Alle Zertifikate sind vorgerechnet (Datei cvg_katalog.json) und werden hier mit Brüchen neu "
           "gerechnet und gegen alle stabilen Mengen geprüft.")
st.radio("Sammlung", list(C.SAMMLUNGEN), format_func=C.SAMMLUNGEN.get, key="sammlung_radio", horizontal=True)
katalog = K.lade()
if st.session_state["sammlung_radio"] == "klein":
    st.caption("Alle nichtperfekten Graphen mit 5 bis 7 Knoten (bis auf Umnummerieren). Je Graph die Facetten seiner ganzzahligen Hülle "
               "jenseits von x ≥ 0 und den Cliquen; Zielgröße ist die linke Seite der gewählten Facette.")

    def graph_name(i):
        e = katalog["klein"][i]
        zusatz = " (Handbeispiel)" if e.get("hand") else " (Fünfeck)" if i == C.KLEIN_C5 else ""
        anzahl = len(e["facetten"])
        return f"Graph {i + 1}: {e['n']} Knoten, {len(e['kanten'])} Kanten, {anzahl} {'Facette' if anzahl == 1 else 'Facetten'}{zusatz}"

    c1, c2 = st.columns([2, 1])
    seed_widget("graph_select")
    c1.selectbox("Graph", range(len(katalog["klein"])), format_func=graph_name, key="graph_select", on_change=wechsle_graph)
    merke("graph_select")
    eintrag = katalog["klein"][st.session_state["graph_select"]]
    facette = 0
    if len(eintrag["facetten"]) > 1:
        seed_widget("facette_select")
        if st.session_state["facette_select"] >= len(eintrag["facetten"]):
            st.session_state["facette_select"] = 0
        c2.selectbox("Facette", range(len(eintrag["facetten"])),
                     format_func=lambda f: S.ungleichung_text(eintrag["facetten"][f]["a"], eintrag["facetten"][f]["b"]),
                     key="facette_select")
        merke("facette_select")
        facette = st.session_state["facette_select"]
    s = K.schnitt_klein(eintrag, facette)
    n_ = eintrag["n"]
    if not E.pruefe_gueltig_durch_gewicht(s["adj"], [(s["alpha"], s["beta"])]):
        st.error("Prüfung fehlgeschlagen: Der Schnitt schneidet eine stabile Menge ab.")
    lage = B.RAD.lage if eintrag.get("hand") else B.kreis_lage(n_)
    links, rechts = st.columns([1, 2])
    with links:
        st.plotly_chart(V.zeichne_graph(lage, [tuple(e) for e in eintrag["kanten"]], [str(v) for v in range(n_)],
                                        werte=[f"{c}" if c else "" for c in s["a"]]), width="stretch", key="klein_graph")
        st.caption("Zahlen an den Knoten: Koeffizienten der gewählten Facette.")
    with rechts:
        st.plotly_chart(V.balken(["Cliquen", "+ ungerade Kreise", "+ eine Runde"],
                                 [float(s["cliquen_wert"]), float(s["kreise_wert"]), s["b"]],
                                 [S.bruch(s["cliquen_wert"]), S.bruch(s["kreise_wert"]), str(s["b"])], ziel=s["b"],
                                 ziel_name="ganzzahlig", achse="größte linke Seite"), width="stretch", key="klein_leiter")
        namen = ["Clique " + menge_text(c, [str(v) for v in range(n_)]) for c in s["cliquen"]]
        tabelle({"Zeile": [namen[i] for i in sorted(s["u"])], "Gewicht u": [S.bruch(s["u"][i]) for i in sorted(s["u"])]})
        st.markdown(f"Abgerundet entsteht **{S.ungleichung_text(s['alpha'], s['beta'])}**; die Facette lautet "
                    f"{S.ungleichung_text(s['a'], s['b'])}.")
    zeige(E.verdict_klein(s))
    befunde[f"Eine Runde: Graph {st.session_state['graph_select'] + 1} der kleinen Sammlung"] = [E.verdict_klein(s)[1]]
else:
    st.caption("Je 200 Instanzen aus fünf Zellen (G(20; 0,2 / 0,4 / 0,6) und Konfliktgraphen K(20; 10; 200 / 400), Werte 1 bis 100): die "
               "47 von 1.000, die nach Cliquen, ungeraden Kreisen, Antilöchern und Rädern noch eine Lücke haben.")

    def fall_name(i):
        e = katalog["zwanzig"][i]
        return f"{i + 1}: {K.familien_name(e['familie'], e['param'])}, Zufalls-Seed {e['seed']}, {len(e['schnitte'])} Schnitte"

    seed_widget("fall_select")
    st.selectbox("Instanz", range(len(katalog["zwanzig"])), format_func=fall_name, key="fall_select")
    merke("fall_select")
    fall = st.session_state["fall_select"]
    eintrag = katalog["zwanzig"][fall]
    d = K.schnitte_zwanzig(eintrag)
    adj = d["instanz"].adj
    w = list(d["instanz"].werte)
    werte_leiter = _leiter(fall)
    if not E.pruefe_gueltig_durch_gewicht(adj, [(t["alpha"], t["beta"]) for t in d["schnitte"]]):
        st.error("Prüfung fehlgeschlagen: Ein Schnitt schneidet eine stabile Menge ab.")
    try:
        schranke = K.pruefe_dualbeweis(w, d["zeilen"], d["y"])
    except ValueError as fehler:
        schranke = None
        st.error(f"Dualbeweis fehlgeschlagen: {fehler}")
    links, rechts = st.columns([1, 1])
    with links:
        opt, menge = groesstes_gewicht(adj, w)
        from cvg_konflikt import kanten as kantenliste

        st.plotly_chart(V.zeichne_graph(B.kreis_lage(20), kantenliste(adj), [str(v) for v in range(20)], werte=[str(x) for x in w],
                                        markiert=[v for v in range(20) if menge >> v & 1], hoehe=420, knotengroesse=26),
                        width="stretch", key="zwanzig_graph")
        st.caption("Zahlen: Werte der Knoten. Gelb: eine stabile Menge mit größtem Gewicht.")
    with rechts:
        st.plotly_chart(V.balken(["Cliquen", "+ Kreise", "+ Antilöcher, Räder", "+ eine Runde"],
                                 [werte_leiter.cliquen, werte_leiter.kreise, werte_leiter.familien, eintrag["optimum"]],
                                 [E.zahl_oder_bruch(werte_leiter.cliquen, 2), E.zahl_oder_bruch(werte_leiter.kreise, 2),
                                  E.zahl_oder_bruch(werte_leiter.familien, 2), str(eintrag["optimum"])], ziel=eintrag["optimum"],
                                 ziel_name="Optimum", achse="größtes Gewicht"), width="stretch", key="zwanzig_leiter")
        if schranke is not None:
            st.markdown(f"**Dualbeweis:** Mit den gespeicherten Gewichten y ≥ 0 über Cliquenzeilen und Schnitten ist y·A ≥ w und "
                        f"y·b = **{S.bruch(schranke)}**. Also erreicht keine zulässige Lösung mehr als das Optimum {eintrag['optimum']}.")
    namen = ["Clique " + menge_text(c, [str(v) for v in range(20)]) for c in d["cliquen"]]
    art_name = {"kreis": "aus einem ungeraden Kreis", "rad": "aus einem ungeraden Rad", "antiloch": "aus einem Antiloch",
                "milp": "vom Trenn-Programm"}
    tabelle({"Schnitt": [S.ungleichung_text(t["alpha"], t["beta"]) for t in d["schnitte"]],
             "Herkunft der Gewichte": [art_name[t["art"]] for t in d["schnitte"]],
             "Gewichte u über den Cliquen": [multiplikator_text(t["u"], namen) for t in d["schnitte"]],
             "Dualgewicht y": [S.bruch(t["y"]) for t in d["schnitte"]]})
    st.caption("Gewichte aus einem Kreis oder Rad können mehr geben als dessen Ungleichung: Die größeren Cliquen bringen dann weitere "
               "Koeffizienten mit. Gezeigt sind nur die Schnitte, die der Dualbeweis braucht.")
    zeige(E.verdict_zwanzig(eintrag))
    befunde[f"Eine Runde: {fall_name(fall)}"] = [E.verdict_zwanzig(eintrag)[1]]

st.markdown("---")

# --- 5 Wenn eine Runde nicht genügt -------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 5: Wenn eine Runde nicht genügt")
info13 = _facetten13()
if info13["fehler"]:
    st.error("Prüfung fehlgeschlagen: Eine Facette ist ungültig. Das dürfte nie vorkommen.")
st.markdown(
    f"Der Graph G ist das Komplement des Kreisgraphen C13(1, 5): 13 Knoten, verbunden, wenn der Abstand modulo 13 weder 1 noch 5 ist. "
    f"Er hat {len(Z.CLIQUEN)} maximale Cliquen (die größten mit {Z.OMEGA} Knoten) und {info13['stabile_mengen']} stabile Mengen (mit der "
    f"leeren), die größten mit {Z.ALPHA} Knoten. Zielgröße ist x(V), die Summe über alle Knoten."
)
st.radio("Nach wie vielen Runden über den Cliquenzeilen?", (0, 1, 2), format_func=lambda v: f"Runde {v}", key="runde_radio",
         horizontal=True)
runde = int(st.session_state["runde_radio"])
laenge, anzahl = int(wert("laenge_radio")), int(wert("anzahl_slider"))
if runde == 2:
    c1, c2 = st.columns(2)
    seed_widget("laenge_radio")
    c1.radio("Länge der Knotenfolge", Z.LAENGEN, key="laenge_radio", horizontal=True)
    merke("laenge_radio")
    seed_widget("anzahl_slider")
    c2.slider("Zahl der addierten Verschiebungen", *bounds("anzahl_slider"), key="anzahl_slider")
    merke("anzahl_slider")
    laenge, anzahl = int(st.session_state["laenge_radio"]), int(st.session_state["anzahl_slider"])
links, rechts = st.columns([1, 2])
with links:
    punkt = {0: "1/4", 1: "1/6", 2: ""}[runde]
    from cvg_konflikt import kanten as kantenliste

    markiert = Z.folge(laenge, 0) if runde == 2 else ()
    st.plotly_chart(V.zeichne_graph(B.kreis_lage(13), kantenliste(Z.ADJ), [str(v) for v in range(13)],
                                    werte=[punkt] * 13, markiert=markiert, hoehe=380), width="stretch", key="g13_graph")
    st.caption("Gelb: die Knotenfolge ab Knoten 0." if runde == 2 else "Zahlen: der Punkt x, an jedem Knoten gleich.")
with rechts:
    st.plotly_chart(V.balken(["Runde 0 (Cliquen)", "Runde 1", "Runde 2"], [float(v) for v in Z.WERT_RUNDE],
                             [S.bruch(v) for v in Z.WERT_RUNDE], ziel=Z.ALPHA, ziel_name="ganzzahlig: 2", achse="größtes x(V)",
                             hervor=runde, hoehe=280), width="stretch", key="g13_leiter")
    st.caption(f"Ganze Hülle (mit ganzen Zahlen ausgerechnet): {info13['gesamt']} Facetten, davon {info13['nichtnegativ']} x_v ≥ 0 und "
               f"{info13['cliquen']} Cliquen. {info13['eine_runde']} weitere entstehen in einer Runde (je ein exaktes Zertifikat), nicht "
               f"in Runde 1: {len(info13['ausserhalb'])}.")
    if runde == 0:
        st.markdown(f"Jede Clique hat höchstens 4 Knoten, also gilt für x = ¼ jede Cliquenzeile. 13 Cliquen mit je ¼ (eine Clique und "
                    f"ihre Verschiebungen) zeigen x(V) ≤ 13/4; mehr geht über den Cliquen nicht.")
    elif runde == 1:
        st.markdown("**Warum x = ⅙ jeden Schnitt der ersten Runde übersteht** (eigene Herleitung). Ein Schnitt entsteht aus Gewichten u "
                    "auf den Cliquen. U ist ihre Summe, a_v die Summe an den Cliquen durch v, k = ⌊U⌋. Wegen höchstens 4 Knoten je "
                    "Clique ist die Summe der ⌊a_v⌋ höchstens ⌊4U⌋ ≤ 4k + 3.")
        faelle = Z.faelle(Z.ZEUGE)
        tabelle({"Fall": [f[0] for f in faelle], "Begründung": [f[1] for f in faelle],
                 "erfüllt": ["ja" if f[2] else "nein" for f in faelle]})
        st.markdown("Auch x = 2/11 übersteht nach derselben Fallunterscheidung jeden Schnitt. Umgekehrt geben die 13 Schnitte zu je 11 "
                    "aufeinanderfolgenden Knoten zusammen 11·x(V) ≤ 26. **Der größte Wert nach Runde 1 ist also genau 26/11.**")
    else:
        alpha, beta = Z.runde1_schnitt(laenge, 0)
        u = Z.multiplikatoren(laenge, 0)
        namen = ["Clique " + menge_text(c, [str(v) for v in range(13)]) for c in Z.CLIQUEN]
        st.markdown(f"**Ein Schnitt der ersten Runde** für die Folge ab Knoten 0 (Gewichtssumme "
                    f"{S.bruch(sum(u.values()))}, also rechte Seite {beta}):")
        tabelle({"Zeile": [namen[i] for i in sorted(u)], "Gewicht u": [S.bruch(u[i]) for i in sorted(u)]})
        st.markdown(f"Ergebnis: **{S.ungleichung_text(alpha, beta)}**. Durch Verschieben (i → i + 1 modulo 13) entstehen die Schnitte für "
                    "die anderen Folgen.")
if runde == 2:
    h, rs, mini, schranke_ = E.schranke_text(laenge, anzahl)
    st.plotly_chart(V.haeufigkeiten(h, soll=mini or None), width="stretch", key="g13_haeufigkeit")
    summe_text = " + ".join(f"{h[v]}·x{v}" for v in range(13) if h[v])
    st.caption(f"Summe der ersten {anzahl} Ungleichungen x(Folge) ≤ 2: {summe_text} ≤ {rs}.")
    zr = Z.zweite_runde(laenge, anzahl)
    if zr is not None:
        st.markdown(f"Mit Gewicht 1/{mini} auf jedem der {anzahl} Schnitte entsteht in **Runde 2** abgerundet "
                    f"**{S.ungleichung_text(zr[0], zr[1])}**.")
zeige(E.verdict_zeuge(runde, laenge, anzahl))
befunde["Graph mit 13 Knoten, Runde " + str(runde)] = [E.verdict_zeuge(runde, laenge, anzahl)[1]]

st.markdown("---")

# --- 6 Was kostet das Finden? -------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 6: Was kostet das Finden?")
st.caption("Zufallsgraph G(n; 0,4) ab den Cliquenzeilen. Je Schritt sucht ein gemischt-ganzzahliges Programm Gewichte eines verletzten "
           "Schnitts; jeder Schnitt wird mit Brüchen neu gerechnet. Die Suche endet, sobald der LP-Wert das Optimum erreicht. Zahl der "
           "Schnitte und Zeiten hängen am Löser und am Rechner.")
c1, c2, c3, c4 = st.columns(4)
c1.slider("Knoten n", *bounds("n_slider"), key="n_slider")
c2.radio("Gewichte", list(C.SUCHE_GEWICHTE), format_func=C.SUCHE_GEWICHTE.get, key="gewichte_radio", horizontal=True)
c3.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
c3.button("🎲 Neue Instanz", on_click=neuer_seed, width="stretch")
c4.slider("Zeitgrenze (Sekunden)", *bounds("budget_slider"), key="budget_slider")
n = int(st.session_state["n_slider"])
gewichte = st.session_state["gewichte_radio"]
seed = int(st.session_state["seed_input"])
budget = int(st.session_state["budget_slider"])
with st.spinner(f"Suche läuft, höchstens etwa {budget} Sekunden …"):
    inst, w, cliquen, zeilen_, suche = _suche(n, gewichte, seed, budget)
if suche.schritte and not E.pruefe_gueltig_durch_gewicht(inst.adj, [(t.alpha, t.beta) for t in suche.schritte]):
    st.error("Prüfung fehlgeschlagen: Ein Schnitt schneidet eine stabile Menge ab.")
m1, m2, m3, m4 = st.columns(4)
m1.metric("LP-Wert mit Cliquen", E.zahl_oder_bruch(suche.wert_start))
m2.metric("LP-Wert nach der Suche", E.zahl_oder_bruch(suche.wert_ende))
m3.metric("Optimum (ganzzahlig)", str(suche.optimum))
m4.metric("Gefundene Schnitte", str(len(suche.schritte)))
links, rechts = st.columns([1, 2])
with links:
    from cvg_konflikt import kanten as kantenliste

    st.plotly_chart(V.zeichne_graph(B.kreis_lage(n), kantenliste(inst.adj), [str(v) for v in range(n)],
                                    werte=[E.zahl_oder_bruch(v, 2) if v > 1e-9 else "" for v in suche.x], hoehe=380),
                    width="stretch", key="suche_graph")
    st.caption("Zahlen: die letzte LP-Lösung (0 ohne Zahl). Bei Werten 1 bis 100 ist die Zielgröße der Gesamtwert.")
with rechts:
    st.plotly_chart(V.suchverlauf(suche.wert_start, [t.wert_danach for t in suche.schritte], suche.optimum), width="stretch",
                    key="suche_verlauf")
    st.caption(f"Rechenzeit dieses Laufs: etwa {E.komma(suche.sekunden, 2)} s.")
if suche.schritte:
    namen = ["Clique " + menge_text(c, [str(v) for v in range(n)]) for c in cliquen]
    tabelle({"Schritt": list(range(1, len(suche.schritte) + 1)),
             "Schnitt": [S.ungleichung_text(t.alpha, t.beta) for t in suche.schritte],
             "Gewichte u über den Cliquen": [multiplikator_text(t.u, namen) for t in suche.schritte],
             "Verletzung": [E.komma(t.verletzung) for t in suche.schritte],
             "LP-Wert danach": [E.zahl_oder_bruch(t.wert_danach) for t in suche.schritte]})
zeige(E.verdict_suche(suche.status, len(suche.schritte), suche.optimum, suche.wert_ende, suche.grund))
befunde[f"Suche: G({n}; 0,4), Gewichte {C.SUCHE_GEWICHTE[gewichte]}, Zufalls-Seed {seed}, Zeitgrenze {budget} s"] = [
    E.verdict_suche(suche.status, len(suche.schritte), suche.optimum, suche.wert_ende, suche.grund)[1]]

st.markdown("#### Vorgerechnet: größere Graphen")
gross, raster, daten = _vorgerechnet()
st.caption(f"Gewichte alle 1; Zufalls-Seeds ab 26100. Vorab alle verletzten ungeraden Kreise (als Schnitte der Runde), dann das "
           f"Trenn-Programm; höchstens {int(daten['budget_gross'][0])} s je Graph und {int(daten['budget_gross'][1])} s je Programm. "
           f"Einmal gemessen mit scipy {daten['umgebung']['scipy']} unter {daten['umgebung']['system']}; die Zahlen hängen an Löser, "
           "Budget und Rechner.")
tabelle({"Knoten": [z["n"] for z in gross], "Graphen": [z["graphen"] for z in gross],
         "Lücke mit Cliquen": [z["luecke_cliquen"] for z in gross], "Lücke auch mit Kreisen": [z["luecke_kreise"] for z in gross],
         "davon durch die Runde geschlossen": [z["davon_geschlossen"] for z in gross],
         "mit Runde offen (Löser meldet keinen Schnitt)": [z["offen_bewiesen"] for z in gross],
         "nicht bestimmt": [z["nicht_bestimmt"] for z in gross]})
zeige(E.verdict_gross(gross[-1]))
with st.expander("Vorgerechnet: Rechenzeit der Suche ab den Cliquenzeilen (ohne vorab geladene Kreise)"):
    st.caption(f"G(n; 0,4), je 40 Graphen (Zufalls-Seeds 26200 bis 26239), höchstens {int(daten['budget_raster'][0])} s je Graph. "
               "Sekunden nur für Graphen mit Cliquenlücke; grob und rechnerabhängig.")
    tabelle({"Knoten": [z["n"] for z in raster], "Gewichte": [C.SUCHE_GEWICHTE[z["gewichte"]] for z in raster],
             "mit Lücke": [z["mit_luecke"] for z in raster], "geschlossen": [z["geschlossen"] for z in raster],
             "mit Runde offen": [z["offen_bewiesen"] for z in raster], "nicht bestimmt": [z["nicht_bestimmt"] for z in raster],
             "Sekunden (Median)": ["–" if z["sekunden_median"] is None else E.komma(z["sekunden_median"], 2) for z in raster],
             "Sekunden (größte)": ["–" if z["sekunden_max"] is None else E.komma(z["sekunden_max"], 2) for z in raster]})

st.markdown("---")

# --- PDF -----------------------------------------------------------------------------------------------------------------------------------

st.markdown("#### 📄 Zusammenfassung der aktuellen Befunde")
stand = tuple((k_, tuple(v)) for k_, v in befunde.items())
if st.button("PDF erstellen"):
    st.session_state["pdf"] = (stand, PDF.erzeuge_pdf(stand))
if st.session_state.get("pdf") and st.session_state["pdf"][0] == stand:
    st.download_button("PDF herunterladen", st.session_state["pdf"][1], file_name="chvatal-gomory.pdf", mime="application/pdf")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    f"""
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Startbeschreibung ist genannt** | Der Rang ändert sich mit ihr: x(K6) ≤ 1 braucht aus den Kantenzeilen drei Runden und steht in den Cliquenzeilen schon da. | – |
| **Kleine Graphen** | „Eine Runde über den Cliquen genügt“ ist für die 147 nichtperfekten Graphen mit 5 bis 7 Knoten belegt; beim Graphen mit 13 Knoten genügt sie nicht. Welcher kleinste Graph mehr als eine braucht, ist hier offen. | – |
| **Ein Zielvektor** | Die 47 geschlossenen Fälle mit 20 Knoten gelten je für einen Wertvektor, nicht für die ganze Hülle. | – |
| **Die Suche läuft zu Ende** | Bricht die Zeit ab, ist der Wert nur eine obere Schranke; „nichts gefunden“ heißt nicht „nichts verletzt“. Auch „kein Schnitt mehr“ gilt nur bis auf Toleranzen und u ≤ 0,999. | – |
| **Stabile Mengen und Matching** | Rundreise und Rucksack sind hier nicht gemessen; ob Kämme in einer Runde entstehen, ist hier weder gemessen noch belegt. | [Rundreise-Polytop]({REPO}rundreise-polytop-demo) |
| **Schnitte aus Gewichten** | Gomory-Schnitte aus dem Simplex-Tableau sind nur eine Rechenvorschrift für bestimmte Gewichte; sie werden hier nicht gerechnet. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** $P = \{x \ge 0 : Ax \le b\}$ mit ganzzahligem $A$ und $b$; gesucht ist die Hülle $P_I = \mathrm{conv}(P \cap \mathbb{Z}^n)$. Für
Gewichte $u \ge 0$ ist der **Chvátal-Gomory-Schnitt**

$$
\lfloor u^{\mathsf T} A \rfloor \, x \;\le\; \lfloor u^{\mathsf T} b \rfloor
$$

für jeden Punkt von $P_I$ gültig. Es genügen Gewichte kleiner als 1: Der ganzzahlige Anteil von $u$ liefert eine Ungleichung, die schon in $P$
gilt. Der **erste Chvátal-Abschluss** $P'$ ist $P$ mit allen diesen Schnitten; für rationale Polyeder ist er wieder ein Polyeder (Schrijver
1980, hier nach einem Referat zitiert, Original nicht gelesen). Der **Chvátal-Rang** ist die kleinste Zahl $r$ mit $P^{(r)} = P_I$.

**Trennung** (eigene Formulierung). Zu einer LP-Lösung $x^*$:

$$
\max \; \alpha^{\mathsf T} x^* - \beta - 10^{-4} \sum_i u_i
$$

$$
\alpha \le u^{\mathsf T} A, \qquad \beta \ge u^{\mathsf T} b - 0{,}999, \qquad 0 \le u_i \le 0{,}999, \qquad \alpha, \beta \text{ ganzzahlig}, \; \alpha \ge 0
$$

($\alpha \ge 0$ passt, weil hier $A \ge 0$ ist.) Findet dieses Programm nichts Verletztes, rechnet ein zweites ohne den Strafterm nach.

**Matching.** Für eine Knotenmenge $U$ addiert man die Gradzeilen in $U$ mit je $\tfrac12$:

$$
x(E[U]) + \tfrac12\, x(\delta(U)) \;\le\; \tfrac{|U|}{2}
$$

Abgerundet bleibt für ungerades $|U|$ die Ungleichung $x(E[U]) \le (|U|-1)/2$; mit dem Satz von Edmonds (Schrijver, *A Course in
Combinatorial Optimization*, Korollar 5.6b) ist das die ganze Hülle. Bei nichtbipartiten Graphen ist der Rang also genau 1, bei bipartiten 0.

**Eine Runde über den Kantenzeilen = Kanten und ungerade Kreise** (eigene Herleitung, nicht extern geprüft; für Graphen ohne isolierte Knoten,
sonst kommt $x_v \le 1$ dazu). Jede ungerade Kreisungleichung entsteht mit $u = \tfrac12$ auf den Kreiskanten. Umgekehrt sei
$\alpha = \lfloor u^{\mathsf T} M \rfloor$, $\beta = \lfloor \sum_e u_e \rfloor$ ($M$: Kanten-Knoten-Inzidenz). Das Problem
$\min \sum_e y_e$ mit $y \ge 0$ und $\sum_{e \ni v} y_e \ge \alpha_v$ hat $u$ als zulässigen Punkt und eine optimale Basislösung $y^*$. Nach der
Struktur der Basislösungen ist sie halbganzzahlig, und ihre halben Anteile liegen auf knotendisjunkten ungeraden Kreisen $C_i$. Schreibe

$$
y^* = z + \tfrac12 \sum_i \chi(C_i), \qquad z \ge 0 \text{ ganzzahlig}
$$

Für jedes $x \ge 0$, das die Kanten- und Kreisungleichungen erfüllt, gilt dann

$$
\alpha^{\mathsf T} x \;\le\; \sum_e z_e (x_u + x_v) + \sum_i x(C_i) \;\le\; \sum_e z_e + \sum_i \tfrac{|C_i| - 1}{2}
$$

Rechts steht eine ganze Zahl, die höchstens $\sum_e y^*_e \le \sum_e u_e$ ist, also höchstens $\beta$. $\qquad\blacksquare$

**Clique aus Kantenzeilen: genau $\lceil \log_2(k-1) \rceil$ Runden.** Obere Schranke: Aus allen $m$-Cliquen folgt mit gleichen Gewichten jede
Clique mit $k \le 2m-1$ Knoten. **Untere Schranke** (eigene Herleitung, nicht extern geprüft): Nach $r$ Runden ist auf der Clique $K$ der Punkt
$x = 1/(2^r+1)$ (außerhalb 0) noch zulässig. Für $r = 0$ ist $x = \tfrac12$ zulässig. Alle Abschlüsse sind in $x \ge 0$ nach unten
abgeschlossen; deshalb genügen Schnitte $c\,x$ mit $c \ge 0$, und der neue Punkt liegt schon im Abschluss davor. Sei $m = 2^{r-1}+1$,
$s = \sum_{v \in K} c_v$ und $h$ der größte Wert von $c\,y$ im Abschluss davor. Dann ist $h \ge s/m$ (Induktion) und $h \ge \max_v c_v$
(Einheitsvektoren sind ganzzahlig). Zu zeigen ist

$$
\lfloor h \rfloor \;\ge\; \frac{s}{2m-1}
$$

Für $0 < s < m$ ist die rechte Seite kleiner als 1 und $\lfloor h \rfloor \ge 1$. Für $s = qm + \rho$ mit $q \ge 1$, $0 \le \rho < m$ ist
$q(2m-1) = qm + q(m-1) \ge s$ und $\lfloor h \rfloor \ge q$; $s = 0$ ist trivial. $\qquad\blacksquare$ Zusammen mit der oberen Schranke ist das
größte $x(K_k)$ nach $r$ Runden genau $\max(1, k/(2^r+1))$.

**Graph mit 13 Knoten** (eigene Herleitung, exakt nachgerechnet): $G$ ist das Komplement von $C_{13}(1,5)$ mit $\alpha = 2$, $\omega = 4$.
$x(V) \le 2$ ist eine Facette (26 straffe stabile Paare vom affinen Rang 12). Eine Runde liefert sie nicht:

$$
x = \tfrac16 \cdot (1, \dots, 1) \in P', \qquad x(V) = \tfrac{13}{6} > 2
$$

(Fallunterscheidung in Experiment 5). Die zweite Runde liefert sie: 13 Schnitte $x(S_i) \le 2$ zu je 9 aufeinanderfolgenden Knoten geben
zusammen

$$
9 \, x(V) \;\le\; 26, \qquad \text{also} \qquad x(V) \le \lfloor 26/9 \rfloor = 2
$$

Die übrigen 91 Facetten gelten schon nach höchstens einer Runde. Der Chvátal-Rang über den Cliquenzeilen ist also genau 2. Ob ein kleinerer
Graph genügt, ist hier nicht untersucht.

**Quellen und Grenzen.** Der CG-Schritt, der Satz von Edmonds und der Satz von Schrijver sind Lehrbuchstoff. Die als eigene Herleitung
bezeichneten Aussagen sind nicht extern geprüft.
"""
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Fehlende Ungleichungen: von Ecken bis Runden](https://sebastianhanisch.net/konzepte-polyeder.html)."
)

sync_query_params()
