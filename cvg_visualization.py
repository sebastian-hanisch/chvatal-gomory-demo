"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), Knotenlagen sind fest."""

import plotly.graph_objects as go

import cvg_constants as C


def sperre(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def zeichne_graph(lage, kanten, namen, werte=None, markiert=(), innen=(), rand=(), hoehe=340, knotengroesse=30) -> go.Figure:
    """Graph mit festen Knotenlagen. werte: Text je Knoten (unter dem Namen); markiert: hervorgehobene Knoten; innen/rand: Indizes
    hervorgehobener Kanten."""
    fig = go.Figure()
    innen, rand = set(innen), set(rand)
    for gruppe, farbe, breite, strich in ((None, C.COLOR_KANTE, 1.4, "solid"), (innen, C.COLOR_KANTE_INNEN, 3.5, "solid"),
                                          (rand, C.COLOR_KANTE_RAND, 2.2, "dot")):
        xs, ys = [], []
        for i, (a, b) in enumerate(kanten):
            passt = (i not in innen and i not in rand) if gruppe is None else i in gruppe
            if passt:
                xs += [lage[a][0], lage[b][0], None]
                ys += [lage[a][1], lage[b][1], None]
        if xs:
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=farbe, width=breite, dash=strich), hoverinfo="skip",
                                     showlegend=False))
    farben = [C.COLOR_KNOTEN_U if v in set(markiert) else C.COLOR_KNOTEN for v in range(len(lage))]
    fig.add_trace(go.Scatter(x=[p[0] for p in lage], y=[p[1] for p in lage], mode="markers",
                             marker=dict(size=knotengroesse, color=farben, line=dict(color=C.COLOR_RAND, width=1.5)),
                             hovertext=[f"Knoten {n}" + (f": {w}" if werte else "") for n, w in zip(namen, werte or namen)],
                             hoverinfo="text", showlegend=False))
    for v, (x, y) in enumerate(lage):
        zweizeilig = bool(werte) and werte[v] != ""
        text = f"<b>{namen[v]}</b>" + (f"<br>{werte[v]}" if zweizeilig else "")
        # zweizeilige Schrift ragt über den Knoten hinaus: heller Grund, damit sie auch im dunklen Design lesbar bleibt
        fig.add_annotation(x=x, y=y, text=text, showarrow=False, font=dict(size=11, color="#1b1b1b"),
                           bgcolor="rgba(255,255,255,0.75)" if zweizeilig else "rgba(255,255,255,0.0)", borderpad=1)
    xs = [p[0] for p in lage]
    ys = [p[1] for p in lage]
    rand_ = 0.28 * max(1.0, max(xs) - min(xs), max(ys) - min(ys)) / 2
    fig.add_trace(go.Scatter(x=[min(xs) - rand_, max(xs) + rand_], y=[min(ys) - rand_, max(ys) + rand_], mode="markers",
                             marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    fig.update_layout(height=hoehe, margin=dict(l=5, r=5, t=5, b=5), plot_bgcolor="rgba(0,0,0,0)")
    return sperre(fig)


def kantenwerte(lage, kanten, texte, namen, markiert=(), innen=(), rand=(), hoehe=340) -> go.Figure:
    """Wie zeichne_graph, zusätzlich ein Text auf jeder Kante (Werte der Matching-Variablen)."""
    fig = zeichne_graph(lage, kanten, namen, markiert=markiert, innen=innen, rand=rand, hoehe=hoehe)
    for (a, b), t in zip(kanten, texte):
        if t:
            fig.add_annotation(x=(lage[a][0] + lage[b][0]) / 2, y=(lage[a][1] + lage[b][1]) / 2, text=t, showarrow=False,
                               font=dict(size=12, color="#1b1b1b"), bgcolor="rgba(255,255,255,0.9)")
    return fig


def balken(beschriftungen, werte, texte, ziel=None, ziel_name="", achse="Wert", hervor=None, hoehe=300) -> go.Figure:
    """Balken mit Text je Balken und optionaler waagerechter Ziellinie. Beschriftungen sind Texte (Kategorieachse)."""
    farben = [C.COLOR_BALKEN if hervor is None or i == hervor else C.COLOR_BALKEN_HELL for i in range(len(werte))]
    fig = go.Figure(go.Bar(x=beschriftungen, y=werte, text=texte, textposition="outside", marker_color=farben, cliponaxis=False,
                           hovertemplate="%{x}: %{text}<extra></extra>"))
    oben = max(list(werte) + ([ziel] if ziel is not None else [])) * 1.18
    if ziel is not None:
        fig.add_shape(type="line", xref="paper", x0=0, x1=1, y0=ziel, y1=ziel, line=dict(color=C.COLOR_ZIEL, width=2, dash="dash"))
        fig.add_annotation(xref="paper", x=1.0, y=ziel, text=ziel_name, showarrow=False, yshift=9, xanchor="right",
                           font=dict(size=11, color=C.COLOR_ZIEL))
    fig.update_yaxes(title_text=achse, range=[0, oben])
    fig.update_layout(height=hoehe, margin=dict(l=10, r=10, t=20, b=10), plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
    return sperre(fig)


def haeufigkeiten(h, soll=None) -> go.Figure:
    """Wie oft kommt jeder der 13 Knoten in der Summe vor?"""
    return balken([str(v) for v in range(len(h))], list(h), [str(v) for v in h], ziel=soll,
                  ziel_name=f"mindestens {soll}" if soll else "", achse="Vorkommen", hoehe=260)


def suchverlauf(wert_start, werte, optimum) -> go.Figure:
    """LP-Wert nach jedem Schritt der Suche gegen das ganzzahlige Optimum."""
    ys = [wert_start] + list(werte)
    xs = list(range(len(ys)))
    fig = go.Figure(go.Scatter(x=xs, y=ys, mode="lines+markers", line=dict(color=C.COLOR_LINIE, width=3), name="LP-Wert",
                               hovertemplate="Schritt %{x}: %{y:.4f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[0, max(1, xs[-1])], y=[optimum, optimum], mode="lines",
                             line=dict(color=C.COLOR_ZIEL, width=2, dash="dash"), name="Optimum", hoverinfo="skip"))
    spanne = max(wert_start - optimum, 0.5)
    fig.update_yaxes(title_text="LP-Wert", range=[optimum - 0.1 * spanne, wert_start + 0.15 * spanne])
    fig.update_xaxes(title_text="Nachladeschritte", range=[-0.2, max(1, xs[-1]) + 0.2], dtick=max(1, len(xs) // 10))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.3),
                      plot_bgcolor="rgba(0,0,0,0)")
    return sperre(fig)
