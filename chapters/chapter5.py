# TODO(r): revisit shrink factors after we add real data
# chapter_5.py - Poker Range Filtering Visualization (robust, human-notes)
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import pandas as pd


# --------------------------- Basic Hand Grid and Classification ---------------------------
# build a 13x13 matrix for starting hands
# rule: upper triangle = suited (e.g. AKs), diagonal = pairs (AA), lower = offsuit (KAo)
hand_order = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
n = len(hand_order)

matrix_hands = []
labels = []

for i, r in enumerate(hand_order):
    row = []
    for j, c in enumerate(hand_order):
        if i < j:
            label = r + c + 's'     # suited
        elif i == j:
            label = r + c           # pair (no suffix)
        else:
            label = c + r + 'o'     # offsuit (note the flip)
        row.append(label)
        labels.append(label)
    matrix_hands.append(row)



# --- Top 15% Starting Hand Example (just a tiny preset to play with) ---
top_15_range = set([
    'AA','KK','QQ','JJ','TT','99','88','AKs','AKo','AQs','AQo','AJs','AJo',
    'KQs','KQo','KJs','KJo','QJs','QJo','ATs','KTs','QTs','JTs','A9s','JTo'
])

# quick-n-dirty tags. simple buckets, nothing fancy.
hand_type_dict = {}
for h in labels:
    if h in ['AA','KK','QQ','JJ','TT','99','88']:
        hand_type_dict[h] = 'Strong Pair'
    elif 's' in h and h[0] in 'AKQJ' and h[1] in 'AKQJ':
        hand_type_dict[h] = 'Suited Broadway'
    elif h in ['AK','AQ','KQ','AJ','KJ']:   # note: these are bare codes; keeping as-is on purpose
        hand_type_dict[h] = 'Offsuit Broadway'
    elif h in ['A5s','A4s','A3s','A2s','KTs','QTs','JTs']:
        hand_type_dict[h] = 'Suited Connector'
    else:
        hand_type_dict[h] = 'Air/Other'



def get_range(filters):
    """Filter hand range by action sequence. Return initial range if no actions.
       tiny rule set: keep behavior exactly as before."""
    r = set(top_15_range)
    if not filters:
        return r

    # after a flop c-bet → keep stronger made hands and good draws
    if "CBet" in filters:
        r = {h for h in r if (hand_type_dict[h] in ['Strong Pair','Suited Broadway','Suited Connector'])}

    # after turn barrel → even tighter
    if "Turn" in filters:
        r = {h for h in r if (hand_type_dict[h] in ['Strong Pair','Suited Broadway'])}

    return r



def hand_matrix_figure(current_range):
    """Generate dynamic matrix highlighting filtered hands (robust).
       1 = highlight, 0 = dim."""
    z = []
    for i, r in enumerate(hand_order):
        row = []
        for j, c in enumerate(hand_order):
            h = matrix_hands[i][j]
            row.append(1 if h in current_range else 0)
        z.append(row)

    # guard: if nothing selected, still render a valid matrix
    if sum(sum(row) for row in z) == 0:
        z = [[0]*n for _ in range(n)]

    colorscale = [[0, '#E0E0E0'], [1, '#29B6F6']]

    fig = go.Figure(go.Heatmap(
        z=z, x=hand_order, y=hand_order, colorscale=colorscale, showscale=False,
        hoverinfo='x+y+z',
        hovertemplate='<b>%{y}%{x}</b> <extra></extra>'   # show like "KAo" etc.
    ))
    fig.update_layout(
        title="Hand Combination Matrix – Highlighted: Current Opponent Range",
        height=420, margin=dict(t=40, l=40, b=30, r=10)
    )
    return fig



def sankey_figure(filters, cur_count, total_count):
    """Build a small Sankey to show the narrowing process.
       Note: numbers are illustrative; keep original math."""
    stages = ['Start', 'PFR', 'CBet', 'Turn']
    selected = ['Start']

    if "PFR"  in filters: selected.append("PFR")
    if "CBet" in filters: selected.append("CBet")
    if "Turn" in filters: selected.append("Turn")

    vals = [total_count]
    cur  = total_count

    # shrink factors (kept as-is, just annotated)
    shrink = [1, 0.15, 0.08, 0.05]
    for i, s in enumerate(["PFR", "CBet", "Turn"]):
        if s in filters:
            cur = int(cur * shrink[i+1] / shrink[i])
            vals.append(cur)

    # if user toggles oddly, make sure we still have a last value
    if len(vals) < len(selected):
        vals.append(cur_count)

    # if only start is selected, add a PFR step to make the flow visible
    if len(selected) == 1:
        vals = [total_count, cur_count]
        selected.append("PFR")

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=15, thickness=22, line=dict(color="black", width=0.5),
            label=[s for s in selected],
            color=["#90caf9"] * len(selected)
        ),
        link=dict(
            source=list(range(len(selected)-1)),
            target=list(range(1, len(selected))),
            value=[v for v in vals[1:]]
        )
    ))
    fig.update_layout(title="Range Narrowing Process (Sankey)",
                      height=300, margin=dict(l=10, r=10, t=30, b=10))
    return fig



def quality_stats_panel(current_range):
    """Range composition text + pie (fallback safe)."""
    counts = {"Strong Pair":0, "Suited Broadway":0, "Suited Connector":0, "Air/Other":0}
    for h in current_range:
        counts[hand_type_dict[h]] += 1

    total = sum(counts.values())
    shown_total = total if total > 0 else 1   # avoid divide-by-zero

    # simple text block. I like preformatted because it lines up nicely.
    text = f"Remaining hand types: {total}, covering approximately {100*total/169:.1f}% of all starting hands\n"
    for k in counts:
        text += f"{k}: {counts[k]} combos, {100*counts[k]/shown_total:.1f}%\n"

    # pie needs at least one non-zero
    safe_values = list(counts.values())
    if sum(safe_values) == 0:
        safe_values = [1, 0, 0, 0]

    fig = go.Figure(data=[go.Pie(
        labels=list(counts.keys()), values=safe_values,
        marker_colors=["#43a047","#1e88e5","#fbc02d","#bdbdbd"],
        textinfo='label+percent', hole=.4
    )])
    fig.update_layout(height=220, margin=dict(t=10, b=10, l=10, r=10))
    return text, fig



# --------------------------- Dash Layout ---------------------------
header = html.H2(
    "Chapter 5: Opponent Range Filtering and Visualization",
    style={'fontSize': '36px', 'fontWeight': 'bold', 'textAlign': 'center'}
)

intro = html.P(
    "This module shows how opponent ranges shrink as actions progress. "
    "The matrix, the Sankey flow, and the small pie help you build intuition."
)

checkboxes = dbc.Checklist(
    id="filter-actions",
    options=[
        {"label": "Preflop Raise", "value": "PFR"},
        {"label": "Flop C-Bet",   "value": "CBet"},
        {"label": "Turn Barrel",  "value": "Turn"}
    ],
    value=["PFR"],     # default: start from PFR so the page is not empty
    inline=True
)

preset_buttons = html.Div([
    dbc.Button("Tight Aggressive: PFR+CBet", id="preset-tight", color="primary",   outline=True, className="me-2"),
    dbc.Button("Loose Passive: Only PFR",    id="preset-loose", color="secondary", outline=True),
], style={"marginTop": "10px"})

matrix_graph = dcc.Graph(id='range-matrix',  style={"height": "440px", "maxHeight": "440px"})
sankey_graph = dcc.Graph(id='sankey-flow',   style={"height": "340px", "maxHeight": "340px"})

stat_card = dbc.Card([
    dbc.CardHeader("Range Composition Summary"),
    dbc.CardBody([
        html.Pre(id="range-stats", style={"fontSize": "1.05rem"}),
        dcc.Graph(id="range-quality-chart")
    ])
], style={"marginTop": "10px"})

layout = dbc.Container([
    header,
    intro,
    checkboxes,
    preset_buttons,

    dbc.Row([
        dbc.Col(matrix_graph, width=6),
        dbc.Col([sankey_graph, stat_card], width=6)
    ]),

    html.Hr(),
    html.Div([
        dcc.Link("← Previous: Table Position & Strategy Visualization", href="/chapter-4", style={'marginRight': '40px'}),
        dcc.Link("Next: Bluffing Skills & Frequency Control →",         href="/chapter-6", style={'marginLeft': '40px'})
    ], style={'margin': '40px 0 0 0', 'fontSize': '16px', 'textAlign': 'center'})
], fluid=True)



# --------------------------- Callbacks ---------------------------
def register_callbacks(app):

    @app.callback(
        Output("filter-actions", "value"),
        [Input("preset-tight", "n_clicks"), Input("preset-loose", "n_clicks")]
    )
    def apply_preset(tight_clicks, loose_clicks):
        # pick which preset button fired (Dash helper)
        ctx = callback_context.triggered_id
        if ctx == "preset-tight":
            return ["PFR", "CBet"]
        elif ctx == "preset-loose":
            return ["PFR"]
        return ["PFR"]     # default if nothing happened yet



    @app.callback(
        [Output("range-matrix", "figure"),
         Output("sankey-flow", "figure"),
         Output("range-stats", "children"),
         Output("range-quality-chart", "figure")],
        Input("filter-actions", "value")
    )
    def update_visuals(selected_filters):
        # compute current range → then update all three visuals
        cur_range = get_range(selected_filters)

        fig_matrix = hand_matrix_figure(cur_range)
        sankey     = sankey_figure(selected_filters, len(cur_range), 169)
        text, qual_fig = quality_stats_panel(cur_range)

        return fig_matrix, sankey, text, qual_fig



__all__ = ["layout", "register_callbacks"]
