from dash import html, dcc, Input, Output, State, ctx, ALL
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import re

# ====== Data load ======
# note: local csv path. I keep it as-is.
import os
CURRENT_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(CURRENT_DIR, "..", "data", "date_ready_for_using.csv")

df = pd.read_csv(DATA_PATH)
df.columns = df.columns.str.strip()
df["hand"] = df["hand"].str.strip()   # keep standard hand code like AJs, T9o
NAME_SET = set(df["hand"])            # quick membership check (used in find helper)



# ====== rank order and 13x13 grid (keep 'T', do not use '10') ======
GRID_ORDER = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]

# little list-comp that builds a 13x13 starting hand matrix
# rule: diagonal is pairs; upper is suited; lower is off-suit
hands_grid = [[
    f"{r}{r}s" if r == c else (
        f"{r}{c}s" if GRID_ORDER.index(r) < GRID_ORDER.index(c) else f"{r}{c}o"
    )
    for c in GRID_ORDER] for r in GRID_ORDER
]



# ====== continuous colormap (viridis) helper ======
viridis = px.colors.sequential.Viridis

def map_color(value):
    # value is expected in [0, 1]; if NaN -> light gray
    if pd.isna(value):
        return "lightgray"
    idx = int(min(max(value, 0), 1) * (len(viridis) - 1))
    return viridis[idx]



# ====== discrete palette for action categories ======
CAT_PALETTE = px.colors.qualitative.Safe
ACTION_COLORS = {
    "RAISE": CAT_PALETTE[0],
    "CALL":  CAT_PALETTE[1],
    "FOLD":  CAT_PALETTE[2],
    "CHECK": CAT_PALETTE[3],
    "N/A":   "#cccccc"
}

def action_color(rec):
    # tiny guard: map unknown text to "N/A"
    key = str(rec or "").strip().upper()
    return ACTION_COLORS.get(key, ACTION_COLORS["N/A"])



# ====== tolerant lookup for a row by hand name ======
# supports: AA / AAs / AAo, AKo / KAo, and "10" -> "T"
def find_row_by_hand(hand_str):
    h = str(hand_str).strip().upper().replace("10", "T")
    cand = {h}

    # pairs: allow AA, AAs, AAo
    if len(h) >= 2 and h[0] == h[1]:
        base = h[0] * 2
        cand |= {base, base + "O", base + "S"}

    # non-pair with suffix: AKo / AKs, also try KAo / KAs
    if len(h) == 3 and h[2] in ("S", "O"):
        a, b, suf = h[0], h[1], h[2]
        cand |= {a + b + suf, b + a + suf}

    # non-pair no suffix: AK -> try AKo/AKs and KAo/KAs
    if len(h) == 2 and h[0] != h[1]:
        a, b = h[0], h[1]
        cand |= {a + b + "O", a + b + "S", b + a + "O", b + a + "S"}

    sub = df[df["hand"].astype(str).str.strip().str.upper().isin(cand)]
    return None if sub.empty else sub.iloc[0]



# ====== tiny figure to show only a colorbar (no heatmap body) ======
def _legend_figure_win():
    # trick: transparent heatmap to keep only the colorbar
    fig = go.Figure(go.Heatmap(
        z=[[0, 1]],
        showscale=True,
        colorscale=viridis,
        opacity=0,                    # hide the body
        colorbar=dict(
            title=dict(text="Win Rate", side="right", font=dict(size=12)),
            tickformat=".0%",
            thickness=18,
            len=0.95,
            tickfont=dict(size=11),
        )
    ))
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig



# ====== Layout ======
def get_layout():
    legend_fig = _legend_figure_win()

    return html.Div([

        html.H2("Chapter 2: Starting Hand Strength & Radar Comparison",
                style={'fontSize': '36px', 'fontWeight': 'bold', 'textAlign': 'center'}),

        html.Div([
            html.H4(" How to read the hand grid:"),
            html.P("Each square is one of the 169 starting hands. Stronger hand → deeper color."),
            html.P("Try to spot hands that stay strong even with 9 players. Those are steady winners.")
        ], style={"backgroundColor": "#f9f9f9", "padding": "10px", "borderRadius": "6px"}),

        html.Div([
            html.Label(" Number of Opponents:"),
            dcc.Slider(
                id="player-slider", min=2, max=10, step=1, value=2,
                marks={i: str(i) for i in range(2, 11)}
            ),

            html.Label(" Show Content:"),
            dcc.Dropdown(
                id="info-mode",
                options=[
                    {"label": "All", "value": "all"},
                    {"label": "Only Win Rate", "value": "win"},
                    {"label": "Only EV", "value": "ev"},
                    {"label": "Only Action", "value": "rec"},
                ],
                value="all", clearable=False, style={"width": "60%"}
            )
        ], style={"padding": "10px"}),

        # hand grid + legend (continuous or discrete) + detail card
        html.Div([
            html.Div(id="card-grid", className="grid", style={"width": "70%"}),

            html.Div([
                dcc.Graph(id="color-legend", figure=legend_fig,
                          style={"width": "100%", "height": "720px"}),
                html.Div(id="cat-legend", style={"display": "none", "padding": "6px 0"})
            ], style={"width": "8%"}),     # a bit wider so the title does not clip

            html.Div(id="detail-card", style={"width": "22%", "paddingLeft": "20px"})
        ], style={"display": "flex", "justifyContent": "center", "gap": "12px"}),

        html.Hr(),

        html.Div([
            html.H4(" EV Radar Chart – Compare Hands Across Player Counts"),
            dcc.Dropdown(
                id="hand-selector",
                options=[{"label": h, "value": h} for h in sorted(df["hand"].unique())],
                value=["AKs"], multi=True,
                placeholder="Select hands to compare",
                style={"width": "60%"}
            ),
            dcc.Graph(id="radar-chart-ch2")
        ]),

        html.Hr(),

        html.Div([
            html.H4(" Mini Quiz: Which hand has higher EV in a 6-player game?"),
            dcc.RadioItems(
                id="quiz-choice",
                options=[
                    {"label": "A♠ J♠ (AJs)", "value": "AJs"},
                    {"label": "K♣ Q♣ (KQs)", "value": "KQs"}
                ],
                value=None
            ),
            html.Button("Check Answer", id="quiz-submit", n_clicks=0),
            html.Div(id="quiz-feedback-ch2", style={"marginTop": "10px"})
        ], style={"padding": "20px"}),

        html.Hr(),

        html.Div([
            dcc.Link("« Chapter 1: Outs & Odds", href="/chapter-1"),
            dcc.Link("Next Chapter »", href="/chapter-3", style={"float": "right"})
        ])
    ], style={"padding": "40px"})


layout = get_layout()



def register_callbacks(app):

    @app.callback(
        Output("card-grid", "children"),
        Input("player-slider", "value"),
        Input("info-mode", "value"),
        Input("detail-card", "children")
    )
    def update_grid(pc, mode, _):
        # columns depend on player count (pc): e.g. "2_win", "EV_2p", "rec_2p"
        win_col, ev_col, rec_col = f"{pc}_win", f"EV_{pc}p", f"rec_{pc}p"

        # pre-calc EV min/max (used only for EV mode)
        ev_min = ev_max = None
        if mode == "ev" and ev_col in df.columns:
            ev_series = pd.to_numeric(df[ev_col], errors="coerce").dropna()
            if not ev_series.empty:
                ev_min = float(ev_series.min())
                ev_max = float(ev_series.max())

        def color_from_mode(win, ev, rec):
            # decide the tile color based on current mode
            if mode in ("win", "all"):
                return map_color(win)       # win ∈ [0,1]
            elif mode == "ev":
                if ev_min is None or ev_max is None or ev_max <= ev_min:
                    return map_color(0.5)   # fallback to neutral if cannot normalize
                norm = (float(ev) - ev_min) / (ev_max - ev_min)
                return map_color(norm)
            else:
                return action_color(rec)

        rows = []
        for r_idx, row in enumerate(hands_grid):
            cards = []
            for c_idx, hand in enumerate(row):

                # defaults in case we cannot find the row
                win, ev, rec = (0.2, 0.0, "N/A")
                rowdata = find_row_by_hand(hand)
                if rowdata is not None:
                    win = float(rowdata.get(win_col, win))
                    ev  = float(rowdata.get(ev_col, ev))
                    rec = str(rowdata.get(rec_col, rec))

                bg = color_from_mode(win, ev, rec)

                style_front = {
                    "backgroundColor": bg,
                    "border": "1px solid #888",
                    "height": "60px", "width": "60px",
                    "display": "flex", "alignItems": "center", "justifyContent": "center"
                }

                content = []
                if mode in ("win", "all"): content.append(html.P(f"Win: {win:.2f}"))
                if mode in ("ev",  "all"): content.append(html.P(f"EV: {ev:.2f}"))
                if mode in ("rec", "all"): content.append(html.P(f"Action: {rec}"))

                cards.append(html.Div([
                    html.Div(hand, className="flip-card-front", style=style_front),
                    html.Div(content, className="flip-card-back")
                ], className="flip-card",
                   id={"type": "card", "index": r_idx * 13 + c_idx},
                   **{"data-hand": hand}, n_clicks=0))

            rows.append(html.Div(cards, className="row", style={"display": "flex"}))

        return rows



    @app.callback(
        Output("color-legend", "figure"),
        Output("color-legend", "style"),
        Output("cat-legend", "children"),
        Output("cat-legend", "style"),
        Input("info-mode", "value"),
        Input("player-slider", "value")
    )
    def update_legend(mode, pc):
        # win / all → show continuous colorbar; hide category legend
        if mode in ("win", "all"):
            fig = _legend_figure_win()
            return fig, {"width": "100%", "height": "720px"}, None, {"display": "none"}

        # EV → also a continuous bar but with EV ticks
        elif mode == "ev":
            ev_col = f"EV_{pc}p"
            ev_min, ev_max = -1.0, 1.0

            if ev_col in df.columns:
                ev_series = pd.to_numeric(df[ev_col], errors="coerce").dropna()
                if not ev_series.empty:
                    ev_min = float(ev_series.min())
                    ev_max = float(ev_series.max())
                    if ev_max <= ev_min:
                        ev_max = ev_min + 1e-6

            tickvals = [0.0, 0.25, 0.5, 0.75, 1.0]
            ticktext = [f"{ev_min + (ev_max-ev_min)*t:.2f}" for t in tickvals]

            fig = go.Figure(go.Heatmap(
                z=[[0, 1]],
                showscale=True,
                colorscale=viridis,
                opacity=0,
                colorbar=dict(
                    title=dict(text=f"EV ({pc}P)", side="right", font=dict(size=12)),
                    thickness=18, len=0.95,
                    tickvals=tickvals, ticktext=ticktext,
                    tickfont=dict(size=11),
                )
            ))
            fig.update_layout(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            return fig, {"width": "100%", "height": "720px"}, None, {"display": "none"}

        # rec → hide continuous bar, show discrete legend chips
        else:
            chips = []
            for label in ["Raise", "Call", "Fold", "Check", "N/A"]:
                chips.append(
                    html.Div([
                        html.Div(style={
                            "display": "inline-block", "width": "14px", "height": "14px",
                            "backgroundColor": ACTION_COLORS[label.upper()], "marginRight": "6px",
                            "border": "1px solid #777"
                        }),
                        html.Span(label)
                    ], style={"marginBottom": "8px"})
                )

            cat = html.Div(chips, style={"fontSize": "12px", "lineHeight": "16px"})
            empty_fig = go.Figure(); empty_fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
            return empty_fig, {"display": "none"}, cat, {"display": "block"}



    @app.callback(
        Output("detail-card", "children"),
        Input({'type': 'card', 'index': ALL}, 'n_clicks'),
        State({'type': 'card', 'index': ALL}, 'data-hand'),
        State("player-slider", "value")
    )
    def update_detail(n_clicks_list, hands, pc):
        # if nothing clicked yet
        if not n_clicks_list or max(n_clicks_list) is None:
            return html.Div("Click a card to view details.")

        idx = n_clicks_list.index(max(n_clicks_list))
        selected = hands[idx]

        rowdata = find_row_by_hand(selected)
        if rowdata is None:
            return html.Div(f"No data for {selected} under current filters.", style={"color": "#b00"})

        d = rowdata
        return html.Div([
            html.H4(f"{selected} Details:"),
            html.P(f"Win Rate ({pc}P): {d[f'{pc}_win']:.2f}"),
            html.P(f"EV ({pc}P): {d[f'EV_{pc}p']:.2f}"),
            html.P(f"Suggested Action: {d[f'rec_{pc}p']}")
        ], style={"border": "1px solid #ccc", "padding": "10px", "borderRadius": "6px"})



    @app.callback(
        Output("radar-chart-ch2", "figure"),
        Input("hand-selector", "value")
    )
    def radar_plot(selected):
        # no selection → empty figure with hint
        if not selected:
            return go.Figure(layout={"title": "Select hands to compare"})

        # collect EV columns like EV_2p, EV_3p, ...
        ev_cols = [c for c in df.columns if re.match(r"^EV_\d+p$", c)]
        pcs = [int(re.findall(r"\d+", c)[0]) for c in ev_cols]
        theta = [f"{p}P" for p in pcs]

        fig = go.Figure()
        palette = px.colors.qualitative.Safe

        for i, hand in enumerate(selected):
            rowdata = find_row_by_hand(hand)
            if rowdata is None:
                continue

            d = rowdata
            fig.add_trace(go.Scatterpolar(
                r=[d[c] for c in ev_cols], theta=theta,
                fill='toself', name=hand,
                line=dict(color=palette[i % len(palette)])
            ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            showlegend=True,
            margin=dict(t=30, b=30, l=30, r=30)
        )
        return fig



    @app.callback(
        Output("quiz-feedback-ch2", "children"),
        Input("quiz-submit", "n_clicks"),
        State("quiz-choice", "value")
    )
    def quiz_check(_, answer):
        # small guard
        if not answer:
            return "Please choose an answer."

        # one fixed question; keep it simple
        correct = "KQs"
        if answer == correct:
            return " Correct! KQs performs slightly better in multiway pots due to its connectivity and flush potential."

        return " Not quite. KQs usually outperforms AJs when 6+ players are involved."
