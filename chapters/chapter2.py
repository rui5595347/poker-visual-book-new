
from dash import html, dcc, Input, Output, State, ctx, ALL
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import re

# ====== 数据加载 ======
DATA_PATH = "data/date ready for using.csv"
df = pd.read_csv(DATA_PATH)
df.columns = df.columns.str.strip()
df["hand"] = df["hand"].str.strip()  # 保持标准格式：如 AJs, T9o
NAME_SET = set(df["hand"])

# ====== 牌型顺序与网格结构（保留 T，不换成 10）======
GRID_ORDER = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]
hands_grid = [[f"{r}{r}s" if r == c else f"{r}{c}s" if GRID_ORDER.index(r) < GRID_ORDER.index(c) else f"{r}{c}o"
               for c in GRID_ORDER] for r in GRID_ORDER]

# ====== 色带映射函数 ======
viridis = px.colors.sequential.Viridis
def map_color(value):
    if pd.isna(value): return "lightgray"
    idx = int(min(max(value, 0), 1) * (len(viridis) - 1))
    return viridis[idx]

# ====== 页面布局 ======
def get_layout():
    return html.Div([
        html.H2("Chapter 2: Starting Hand Strength & Radar Comparison", style={"textAlign": "center"}),

        html.Div([
            html.H4("📘 How to read the hand grid:"),
            html.P("Each square represents one of the 169 starting hands. Deeper color = stronger."),
            html.P("Try finding hands that stay strong even with 9 players – they're your all-around champions!")
        ], style={"backgroundColor": "#f9f9f9", "padding": "10px", "borderRadius": "6px"}),

        html.Div([
            html.Label("👥 Number of Opponents:"),
            dcc.Slider(id="player-slider", min=2, max=10, step=1, value=2,
                       marks={i: str(i) for i in range(2, 11)}),

            html.Label("📊 Show Content:"),
            dcc.Dropdown(id="info-mode",
                         options=[{"label": "All", "value": "all"},
                                  {"label": "Only Win Rate", "value": "win"},
                                  {"label": "Only EV", "value": "ev"},
                                  {"label": "Only Action", "value": "rec"}],
                         value="all", clearable=False, style={"width": "60%"})
        ], style={"padding": "10px"}),

        html.Div([
            html.Div(id="card-grid", className="grid", style={"width": "70%"}),
            html.Div(id="detail-card", style={"width": "30%", "paddingLeft": "20px"})
        ], style={"display": "flex", "justifyContent": "center", "gap": "12px"}),

        html.Hr(),

        html.Div([
            html.H4("📈 EV Radar Chart – Compare Hands Across Player Counts"),
            dcc.Dropdown(id="hand-selector",
                         options=[{"label": h, "value": h} for h in sorted(df["hand"].unique())],
                         value=["AKs"], multi=True,
                         placeholder="Select hands to compare",
                         style={"width": "60%"}),
            dcc.Graph(id="radar-chart-ch2")
        ]),

        html.Hr(),

        html.Div([
            html.H4("🧠 Mini Quiz: Which hand has higher EV in a 6-player game?"),
            dcc.RadioItems(id="quiz-choice",
                           options=[
                               {"label": "A♠ J♠ (AJs)", "value": "AJs"},
                               {"label": "K♣ Q♣ (KQs)", "value": "KQs"}
                           ], value=None),
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

    @app.callback(Output("card-grid", "children"),
                  Input("player-slider", "value"),
                  Input("info-mode", "value"),
                  Input("detail-card", "children"))
    def update_grid(pc, mode, _):
        win_col, ev_col, rec_col = f"{pc}_win", f"EV_{pc}p", f"rec_{pc}p"
        rows = []
        for r_idx, row in enumerate(hands_grid):
            cards = []
            for c_idx, hand in enumerate(row):
                win, ev, rec = (0.2, 0.0, "N/A")
                if hand in NAME_SET:
                    d = df[df["hand"] == hand].iloc[0]
                    win = float(d.get(win_col, 0.2))
                    ev = float(d.get(ev_col, 0.0))
                    rec = str(d.get(rec_col, "N/A"))
                style_front = {
                    "backgroundColor": map_color(win),
                    "border": "1px solid #888",
                    "height": "60px", "width": "60px",
                    "display": "flex", "alignItems": "center", "justifyContent": "center"
                }
                content = []
                if mode in ("win", "all"): content.append(html.P(f"Win: {win:.2f}"))
                if mode in ("ev", "all"): content.append(html.P(f"EV: {ev:.2f}"))
                if mode in ("rec", "all"): content.append(html.P(f"Action: {rec}"))
                cards.append(html.Div([
                    html.Div(hand, className="flip-card-front", style=style_front),
                    html.Div(content, className="flip-card-back")
                ], className="flip-card",
                   id={"type": "card", "index": r_idx * 13 + c_idx},
                   **{"data-hand": hand}, n_clicks=0))
            rows.append(html.Div(cards, className="row", style={"display": "flex"}))
        return rows

    @app.callback(Output("detail-card", "children"),
                  Input({'type': 'card', 'index': ALL}, 'n_clicks'),
                  State({'type': 'card', 'index': ALL}, 'data-hand'),
                  State("player-slider", "value"))
    def update_detail(n_clicks_list, hands, pc):
        if not n_clicks_list or max(n_clicks_list) is None:
            return html.Div("Click a card to view details.")
        idx = n_clicks_list.index(max(n_clicks_list))
        selected = hands[idx]
        d = df[df["hand"] == selected].iloc[0]
        return html.Div([
            html.H4(f"{selected} Details:"),
            html.P(f"Win Rate ({pc}P): {d[f'{pc}_win']:.2f}"),
            html.P(f"EV ({pc}P): {d[f'EV_{pc}p']:.2f}"),
            html.P(f"Suggested Action: {d[f'rec_{pc}p']}")
        ], style={"border": "1px solid #ccc", "padding": "10px", "borderRadius": "6px"})

    @app.callback(Output("radar-chart-ch2", "figure"),
                  Input("hand-selector", "value"))
    def radar_plot(selected):
        if not selected:
            return go.Figure(layout={"title": "Select hands to compare"})
        ev_cols = [c for c in df.columns if re.match(r"^EV_\d+p$", c)]
        pcs = [int(re.findall(r"\d+", c)[0]) for c in ev_cols]
        theta = [f"{p}P" for p in pcs]
        fig = go.Figure()
        palette = px.colors.qualitative.Safe
        for i, hand in enumerate(selected):
            d = df[df["hand"] == hand].iloc[0]
            fig.add_trace(go.Scatterpolar(
                r=[d[c] for c in ev_cols], theta=theta,
                fill='toself', name=hand,
                line=dict(color=palette[i % len(palette)])))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True)),
                          showlegend=True,
                          margin=dict(t=30, b=30, l=30, r=30))
        return fig

    @app.callback(Output("quiz-feedback-ch2", "children"),
                  Input("quiz-submit", "n_clicks"),
                  State("quiz-choice", "value"))
    def quiz_check(_, answer):
        if not answer:
            return "Please choose an answer."
        correct = "KQs"
        if answer == correct:
            return "✅ Correct! KQs performs slightly better in multiway pots due to its connectivity and flush potential."
        return "❌ Not quite. KQs usually outperforms AJs when 6+ players are involved."
