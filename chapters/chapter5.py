# chapter_5.py - Poker Range Filtering Visualization (防呆完善版)
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# --------------------------- 基础数据与手牌分类 ---------------------------
hand_order = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
n = len(hand_order)
matrix_hands = []
labels = []
for i, r in enumerate(hand_order):
    row = []
    for j, c in enumerate(hand_order):
        if i < j:
            label = r + c + 's'
        elif i == j:
            label = r + c
        else:
            label = c + r + 'o'
        row.append(label)
        labels.append(label)
    matrix_hands.append(row)

# --- 前15%标准范围示例 ---
top_15_range = set([
    'AA','KK','QQ','JJ','TT','99','88','AKs','AKo','AQs','AQo','AJs','AJo',
    'KQs','KQo','KJs','KJo','QJs','QJo','ATs','KTs','QTs','JTs','A9s','JTo'
])

hand_type_dict = {}
for h in labels:
    if h in ['AA','KK','QQ','JJ','TT','99','88']:
        hand_type_dict[h] = 'Strong Pair'
    elif 's' in h and h[0] in 'AKQJ' and h[1] in 'AKQJ':
        hand_type_dict[h] = 'Suited Broadway'
    elif h in ['AK','AQ','KQ','AJ','KJ']:
        hand_type_dict[h] = 'Offsuit Broadway'
    elif h in ['A5s','A4s','A3s','A2s','KTs','QTs','JTs']:
        hand_type_dict[h] = 'Suited Connector'
    else:
        hand_type_dict[h] = 'Air/Other'

def get_range(filters):
    """根据行为路径过滤范围，若无行为直接返回初始范围"""
    r = set(top_15_range)
    if not filters:
        return r
    if "CBet" in filters:
        r = {h for h in r if (hand_type_dict[h] in ['Strong Pair','Suited Broadway','Suited Connector'])}
    if "Turn" in filters:
        r = {h for h in r if (hand_type_dict[h] in ['Strong Pair','Suited Broadway'])}
    return r

def hand_matrix_figure(current_range):
    """生成动态高亮矩阵图（全防呆）"""
    z = []
    for i, r in enumerate(hand_order):
        row = []
        for j, c in enumerate(hand_order):
            h = matrix_hands[i][j]
            row.append(1 if h in current_range else 0)
        z.append(row)
    # 若范围全空，则全灰
    if sum(sum(row) for row in z) == 0:
        z = [[0]*n for _ in range(n)]
    colorscale = [[0, '#E0E0E0'], [1, '#29B6F6']]
    fig = go.Figure(go.Heatmap(z=z, x=hand_order, y=hand_order, colorscale=colorscale, showscale=False,
                               hoverinfo='x+y+z',
                               hovertemplate='<b>%{y}%{x}</b> <extra></extra>'))
    fig.update_layout(title="Hand Combination Matrix – Highlighted: Current Opponent Range",
                     height=420, margin=dict(t=40, l=40, b=30, r=10))
    return fig

def sankey_figure(filters, cur_count, total_count):
    """构建Sankey流程图数据，防呆（如无行为也正常显示）"""
    stages = ['Start', 'PFR', 'CBet', 'Turn']
    selected = ['Start']
    if "PFR" in filters:
        selected.append("PFR")
    if "CBet" in filters:
        selected.append("CBet")
    if "Turn" in filters:
        selected.append("Turn")
    # node values
    vals = [total_count]
    cur = total_count
    shrink = [1, 0.15, 0.08, 0.05]
    for i, s in enumerate(["PFR", "CBet", "Turn"]):
        if s in filters:
            cur = int(cur * shrink[i+1]/shrink[i])
            vals.append(cur)
    if len(vals) < len(selected):
        vals.append(cur_count)
    if len(selected) == 1:
        vals = [total_count, cur_count]
        selected.append("PFR")
    # Sankey设置
    fig = go.Figure(go.Sankey(
        arrangement = "snap",
        node=dict(
            pad=15, thickness=22, line=dict(color="black", width=0.5),
            label=[s for s in selected],
            color=["#90caf9"]*len(selected)
        ),
        link=dict(
            source=list(range(len(selected)-1)),
            target=list(range(1,len(selected))),
            value=[v for v in vals[1:]]
        )
    ))
    fig.update_layout(title="Range Narrowing Process (Sankey)", height=300, margin=dict(l=10, r=10, t=30, b=10))
    return fig

def quality_stats_panel(current_range):
    """统计范围质量 + 饼图，始终输出非空饼图"""
    counts = {"Strong Pair":0, "Suited Broadway":0, "Suited Connector":0, "Air/Other":0}
    for h in current_range:
        counts[hand_type_dict[h]] += 1
    total = sum(counts.values())
    shown_total = total if total > 0 else 1
    text = f"当前剩余组合数 = {total}，占全部起手牌约{100*total/169:.1f}%\n"
    for k in counts:
        text += f"{k}：{counts[k]}种，占{100*counts[k]/shown_total:.1f}%\n"
    # 饼图防呆
    safe_values = list(counts.values())
    if sum(safe_values) == 0:
        safe_values = [1, 0, 0, 0]
    fig = go.Figure(data=[go.Pie(labels=list(counts.keys()), values=safe_values,
                                 marker_colors=["#43a047","#1e88e5","#fbc02d","#bdbdbd"],
                                 textinfo='label+percent', hole=.4)])
    fig.update_layout(height=220, margin=dict(t=10,b=10,l=10,r=10))
    return text, fig

# --------------------------- Dash Layout ---------------------------
header = html.H2("Chapter 5: Opponent Range Filtering and Visualization")
intro = html.P("This module demonstrates how opponent hand ranges shrink and concentrate as actions progress. Interactive matrix, Sankey flow and quality statistics reinforce learning.")
checkboxes = dbc.Checklist(
    id="filter-actions",
    options=[
        {"label": "Preflop Raise", "value": "PFR"},
        {"label": "Flop C-Bet", "value": "CBet"},
        {"label": "Turn Barrel", "value": "Turn"}
    ],
    value=["PFR"],    # 默认勾选一项，不是空
    inline=True
)
preset_buttons = html.Div([
    dbc.Button("Tight Aggressive: PFR+CBet", id="preset-tight", color="primary", outline=True, className="me-2"),
    dbc.Button("Loose Passive: Only PFR", id="preset-loose", color="secondary", outline=True),
], style={"marginTop": "10px"})

matrix_graph = dcc.Graph(id='range-matrix')
sankey_graph = dcc.Graph(id='sankey-flow')
stat_card = dbc.Card([
    dbc.CardHeader("Range Composition Summary"),
    dbc.CardBody([
        html.Pre(id="range-stats", style={"fontSize":"1.05rem"}),
        dcc.Graph(id="range-quality-chart")
    ])
], style={"marginTop": "10px"})

# ...（上面已有内容）
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
        dcc.Link("Next: Bluffing Skills & Frequency Control →", href="/chapter-6", style={'marginLeft': '40px'})
    ], style={'margin': '40px 0 0 0', 'fontSize': '16px', 'textAlign': 'center'})
], fluid=True)


# --------------------------- 回调实现 ---------------------------
def register_callbacks(app):
    @app.callback(
        Output("filter-actions", "value"),
        [Input("preset-tight", "n_clicks"), Input("preset-loose", "n_clicks")]
    )
    def apply_preset(tight_clicks, loose_clicks):
        ctx = callback_context.triggered_id
        if ctx == "preset-tight":
            return ["PFR","CBet"]
        elif ctx == "preset-loose":
            return ["PFR"]
        return ["PFR"]

    @app.callback(
        [Output("range-matrix", "figure"),
         Output("sankey-flow", "figure"),
         Output("range-stats", "children"),
         Output("range-quality-chart", "figure")],
        Input("filter-actions", "value")
    )
    def update_visuals(selected_filters):
        cur_range = get_range(selected_filters)
        fig_matrix = hand_matrix_figure(cur_range)
        sankey = sankey_figure(selected_filters, len(cur_range), 169)
        text, qual_fig = quality_stats_panel(cur_range)
        return fig_matrix, sankey, text, qual_fig

__all__ = ["layout", "register_callbacks"]
