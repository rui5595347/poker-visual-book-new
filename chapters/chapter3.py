import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

# 玩家位置和指标数据
positions = ["UTG", "UTG+1", "UTG+2", "MP", "HJ", "CO", "BTN", "SB", "BB"]
position_metrics = {
    "UTG": [0.2, 0.3, 0.2, 0.1, 0.3],
    "UTG+1": [0.25, 0.35, 0.25, 0.15, 0.35],
    "UTG+2": [0.28, 0.38, 0.3, 0.18, 0.37],
    "MP": [0.3, 0.4, 0.35, 0.2, 0.4],
    "HJ": [0.32, 0.42, 0.38, 0.3, 0.43],
    "CO": [0.4, 0.5, 0.45, 0.35, 0.5],
    "BTN": [0.5, 0.6, 0.5, 0.6, 0.6],
    "SB": [0.15, 0.25, 0.2, 0.1, 0.25],
    "BB": [0.1, 0.2, 0.15, 0.05, 0.2]
}
metric_labels = ["Win Rate", "VPIP", "PFR", "Steal", "Aggression"]

# 页面布局
layout = dbc.Container([
    html.H2("Chapter 3: Table Position & Strategy Visualization", className="text-center mt-4 mb-4"),

    dbc.Row([
        dbc.Col([
            html.Div([
                html.Img(src="/assets/table_background.png", className="poker-table-img"),
                html.Div("Dealer", className="dealer-chip"),
                *[html.Div(pos, className=f"seat seat-{i}", id={"type": "seat", "index": pos})
                  for i, pos in enumerate(positions)]
            ], className="table-container position-relative", id="poker-table")
        ], width=5),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5(id='position-title', children="Select a Position")),
                dbc.CardBody([
                    dcc.Graph(id='radar-graph', style={"height": "350px"}),
                    html.Div(id='position-desc', className="mt-3"),
                    html.Hr(),
                    html.Div(id='radar-compare', className="mt-3"),
                    html.Hr(),
                    dcc.Markdown("""
### 📘 指标解释
- 📈 **VPIP**: 主动参与底池的频率，越高越攻击
- ⚔️ **PFR**: 翻牌前加注频率，衡量进攻意图
- 🨊 **Steal**: 偷盲率，CO/BTN 位重要策略
- 🔥 **Aggression**: 主动性比率，加注 vs 跟注
                    """, className="mt-4")
                ])
            ])
        ], width=7)
    ]),

    html.Hr(),
    html.Div([
        dcc.Link("« Chapter 2: EV Radar", href="/chapter-2", style={"marginRight": "20px"}),
        dcc.Link("Next Chapter ►", href="/chapter-4")
    ], className="text-center mb-4")

], fluid=True)

# 注册回调函数
def register_callbacks(app):
    @app.callback(
        Output('position-title', 'children'),
        Output('position-desc', 'children'),
        Output('radar-graph', 'figure'),
        Output('radar-compare', 'children'),
        Output({'type': 'seat', 'index': ALL}, 'className'),
        Input({'type': 'seat', 'index': ALL}, 'n_clicks'),
        State({'type': 'seat', 'index': ALL}, 'id'),
        State({'type': 'seat', 'index': ALL}, 'className')
    )
    def update_position(clicks, ids, classes):
        triggered = dash.callback_context.triggered
        if not triggered or all(c is None for c in clicks):
            return "Select a Position", "Click on a table seat to view strategy details.", {}, "", [cls for cls in classes]

        triggered_id = eval(triggered[0]['prop_id'].split('.')[0])['index']
        metrics = position_metrics.get(triggered_id, [0.2]*5)

        # 当前雷达图
        radar = go.Figure()
        radar.add_trace(go.Scatterpolar(
            r=metrics + [metrics[0]],
            theta=metric_labels + [metric_labels[0]],
            fill='toself', name=triggered_id,
            fillcolor='rgba(100,149,237,0.5)',
            line_color='royalblue'
        ))
        radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=False,
            margin=dict(t=30, l=20, r=20, b=20)
        )

        # 与 BTN 对比图
        compare_fig = go.Figure()
        compare_fig.add_trace(go.Scatterpolar(
            r=metrics + [metrics[0]],
            theta=metric_labels + [metric_labels[0]],
            fill='toself', name=triggered_id,
            fillcolor='rgba(0,123,255,0.4)', line_color='blue'
        ))
        compare_fig.add_trace(go.Scatterpolar(
            r=position_metrics['BTN'] + [position_metrics['BTN'][0]],
            theta=metric_labels + [metric_labels[0]],
            fill='toself', name='BTN (reference)',
            fillcolor='rgba(40,167,69,0.4)', line_color='green'
        ))
        compare_fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=True,
            margin=dict(t=30, l=20, r=20, b=20)
        )

        # 描述文本
        desc_text = f"""
🌟 **当前选中位置**：**{triggered_id}**
🧠 **核心优势/劣势**：依据图中蓝色区域判断你的位置表现
✅ **推荐打法**：根据 VPIP / PFR 值，考虑是否扩宽范围或加强进攻
⚠️ **新手误区**：避免 Limp 太多，或在早位用边缘手牌跟注
➡️ 请结合雷达图理解你的位置策略应如何调整。
        """

        compare_card = dbc.Card([
            dbc.CardHeader(f"🔁 {triggered_id} vs BTN (Button Position)"),
            dbc.CardBody([
                dcc.Graph(figure=compare_fig, style={"height": "300px"}),
                dcc.Markdown("""
✅ **分析建议**：
- 与 BTN 相比，你的位置在行动顺序上存在劣势。
- 若你 VPIP/PFR 明显低于 BTN，应采取 tighter 策略。
- BTN 可更频繁 Steal，因此你的范围需更谨慎。
                """)
            ])
        ])

        new_classes = []
        for i, seat in enumerate(ids):
            base = f"seat seat-{i}"
            if seat['index'] == triggered_id:
                base += " seat-active"
            new_classes.append(base)

        return f"Position: {triggered_id}", dcc.Markdown(desc_text), radar, compare_card, new_classes

from dash import dcc, html, Input, Output, State, ALL, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import numpy as np

# --- 数据 ---
positions = ["UTG", "UTG+1", "UTG+2", "MP", "HJ", "CO", "BTN", "SB", "BB"]
position_metrics = {
    "UTG": [0.2, 0.3, 0.2, 0.1, 0.3],
    "UTG+1": [0.25, 0.35, 0.25, 0.15, 0.35],
    "UTG+2": [0.28, 0.38, 0.3, 0.18, 0.37],
    "MP": [0.3, 0.4, 0.35, 0.2, 0.4],
    "HJ": [0.32, 0.42, 0.38, 0.3, 0.43],
    "CO": [0.4, 0.5, 0.45, 0.35, 0.5],
    "BTN": [0.5, 0.6, 0.5, 0.6, 0.6],
    "SB": [0.15, 0.25, 0.2, 0.1, 0.25],
    "BB": [0.1, 0.2, 0.15, 0.05, 0.2]
}
metric_labels = ["Win Rate", "VPIP", "PFR", "Steal", "Aggression"]

position_desc = {
    "UTG": "First to act. Tightest range: only strongest hands.",
    "UTG+1": "Still early, add AQ, JJ.",
    "UTG+2": "Can mix in more suited connectors.",
    "MP": "Middle, start to loosen up.",
    "HJ": "Hijack: exploit if late seats are passive.",
    "CO": "Cutoff: attack the blinds!",
    "BTN": "Button: the best spot. Open widest, max pressure.",
    "SB": "Small blind: defend tight, awkward spot.",
    "BB": "Big blind: defend often, but out of position."
}

def radar_figure(metrics, pos):
    radar = go.Figure()
    radar.add_trace(go.Scatterpolar(
        r=metrics + [metrics[0]],
        theta=metric_labels + [metric_labels[0]],
        fill='toself', name=pos,
        fillcolor='rgba(100,149,237,0.5)',
        line_color='royalblue'
    ))
    radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 0.7])),
        showlegend=False,
        margin=dict(t=30, l=20, r=20, b=20)
    )
    return radar

def compare_radar_figure(metrics, pos):
    compare_fig = go.Figure()
    compare_fig.add_trace(go.Scatterpolar(
        r=metrics + [metrics[0]],
        theta=metric_labels + [metric_labels[0]],
        fill='toself', name=pos,
        fillcolor='rgba(0,123,255,0.4)', line_color='blue'
    ))
    compare_fig.add_trace(go.Scatterpolar(
        r=position_metrics['BTN'] + [position_metrics['BTN'][0]],
        theta=metric_labels + [metric_labels[0]],
        fill='toself', name='BTN (reference)',
        fillcolor='rgba(40,167,69,0.4)', line_color='green'
    ))
    compare_fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 0.7])),
        showlegend=True,
        margin=dict(t=30, l=20, r=20, b=20)
    )
    return compare_fig

def profit_bar_figure():
    profits = [position_metrics[s][0] for s in positions]
    colors = ["#43a047" if p > 0.25 else "#e53935" for p in profits]
    fig = go.Figure(go.Bar(
        x=positions, y=profits,
        marker=dict(color=colors),
        text=[f"{p:+.2f}" for p in profits],
        textposition="outside"
    ))
    fig.update_layout(
        title="Long-term Win Rate (示意)",
        yaxis_title="Win Rate",
        height=220,
        margin=dict(l=30, r=20, t=38, b=20),
        plot_bgcolor="#fff"
    )
    return fig

def animation_comparison_figure():
    x = ["BTN (Position)", "UTG (Out of Position)"]
    y = [2.5, -1.2]
    colors = ["#43a047", "#e53935"]
    fig = go.Figure(go.Bar(
        x=x, y=y, marker_color=colors, text=["+2.5BB", "-1.2BB"], textposition="auto"
    ))
    fig.update_layout(
        title="Same Hand, Different Position Outcome",
        yaxis_title="Sample Profit (BB)",
        margin=dict(l=40, r=20, t=44, b=26),
        plot_bgcolor="#e3f2fd"
    )
    return fig

# --- 页面布局 ---
layout = dbc.Container([
    html.H2("Chapter 3: Table Position & Strategy Visualization", className="text-center mt-4 mb-4"),

    dbc.Row([
        dbc.Col([
            html.Div([
                html.Img(src="/assets/table_background.png", className="poker-table-img", style={"width": "100%", "maxWidth": "500px"}),
                html.Div("Dealer", className="dealer-chip"),
                *[html.Div(pos, className=f"seat seat-{i}", id={"type": "seat", "index": pos}, n_clicks=0)
                  for i, pos in enumerate(positions)]
            ], className="table-container position-relative", id="poker-table", style={"minHeight": "390px"}),
            dcc.Graph(id="profit-bar", figure=profit_bar_figure(), style={"height": "220px", "marginTop": "16px"}),
        ], width=5),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5(id='position-title', children="Select a Position")),
                dbc.CardBody([
                    dcc.Graph(id='radar-graph', style={"height": "350px"}),
                    html.Div(id='position-desc', className="mt-3"),
                    html.Hr(),
                    html.Div(id='radar-compare', className="mt-3"),
                    html.Hr(),
                    dcc.Markdown("""
### 📘 指标解释
- 📈 **VPIP**: 主动参与底池的频率，越高越攻击
- ⚔️ **PFR**: 翻牌前加注频率，衡量进攻意图
- 🨊 **Steal**: 偷盲率，CO/BTN 位重要策略
- 🔥 **Aggression**: 主动性比率，加注 vs 跟注
                    """, className="mt-4")
                ])
            ])
        ], width=7)
    ]),

    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.H4("Position Advantage Animation:"),
            dcc.Graph(id="anim-comp", figure=animation_comparison_figure(), style={'height': '225px'}),
            html.Div(
                "Animation: With the same hand, BTN can win by acting last; UTG, acting first, loses due to lack of info.",
                style={'fontSize': '15px', 'color': '#546e7a'}
            )
        ])
    ]),

    html.Hr(),
    html.Div([
        dcc.Link("« Chapter 2: EV Radar", href="/chapter-2", style={"marginRight": "20px"}),
        dcc.Link("Next Chapter ►", href="/chapter-4")
    ], className="text-center mb-4")

], fluid=True)

# --- 回调注册 ---
def register_callbacks(app):
    @app.callback(
        Output('position-title', 'children'),
        Output('position-desc', 'children'),
        Output('radar-graph', 'figure'),
        Output('radar-compare', 'children'),
        Output({'type': 'seat', 'index': ALL}, 'className'),
        Input({'type': 'seat', 'index': ALL}, 'n_clicks'),
        State({'type': 'seat', 'index': ALL}, 'id'),
        State({'type': 'seat', 'index': ALL}, 'className')
    )
    def update_position(clicks, ids, classes):
        triggered = callback_context.triggered
        if not triggered or all(c is None or c == 0 for c in clicks):
            return "Select a Position", "Click on a table seat to view strategy details.", {}, "", [cls for cls in classes]

        last_click_idx = np.argmax([c or 0 for c in clicks])
        triggered_id = ids[last_click_idx]['index']
        metrics = position_metrics.get(triggered_id, [0.2]*5)

        radar = radar_figure(metrics, triggered_id)
        compare_card = dbc.Card([
            dbc.CardHeader(f"🔁 {triggered_id} vs BTN (Button Position)"),
            dbc.CardBody([
                dcc.Graph(figure=compare_radar_figure(metrics, triggered_id), style={"height": "300px"}),
                dcc.Markdown("""
✅ **分析建议**：
- 与 BTN 相比，你的位置在行动顺序上存在劣势。
- 若你 VPIP/PFR 明显低于 BTN，应采取 tighter 策略。
- BTN 可更频繁 Steal，因此你的范围需更谨慎。
                """)
            ])
        ])

        desc_text = f"""
🌟 **当前选中位置**：**{triggered_id}**
🧠 **优势/劣势**：依据雷达蓝色区域判断你的位置表现
✅ **推荐打法**：根据 VPIP / PFR 值，考虑是否扩宽范围或加强进攻
⚠️ **新手误区**：避免 Limp 太多，或在早位用边缘手牌跟注
{position_desc.get(triggered_id, "")}
        """

        new_classes = []
        for i, seat in enumerate(ids):
            base = f"seat seat-{i}"
            if seat['index'] == triggered_id:
                base += " seat-active"
            new_classes.append(base)

        return f"Position: {triggered_id}", dcc.Markdown(desc_text), radar, compare_card, new_classes

__all__ = ["layout", "register_callbacks"]

