# # chapter_4.py - Final GTO vs Aggressive Visualization: Grouped Bar Chart Implementation
#
# from dash import dcc, html, Input, Output, State
# import plotly.graph_objects as go
# import dash_bootstrap_components as dbc
#
# POSITIONS = ['UTG', 'UTG+1', 'MP', 'MP+1', 'HJ', 'CO', 'BTN', 'SB', 'BB']
# ACTIONS = ['Raise', 'Check', 'Fold']
# ACTION_COLORS = {'Raise': '#2ECC71', 'Check': '#F1C40F', 'Fold': '#E74C3C'}
#
# WINRATE_TABLE = {
#     "AQo": {
#         "Loose": {i: 0.68 - i * 0.04 for i in range(1, 9)},
#         "Tight": {i: 0.65 - i * 0.05 for i in range(1, 9)}
#     },
#     "99": {
#         "Loose": {i: 0.61 - i * 0.03 for i in range(1, 9)},
#         "Tight": {i: 0.59 - i * 0.04 for i in range(1, 9)}
#     },
#     "JTs": {
#         "Loose": {i: 0.55 - i * 0.03 for i in range(1, 9)},
#         "Tight": {i: 0.51 - i * 0.035 for i in range(1, 9)}
#     }
# }
#
# ROUNDS = ['Preflop', 'Flop', 'Turn', 'River']
#
# def get_winrate(hand, opp_type, opp_count):
#     return max(0.05, min(0.95, WINRATE_TABLE[hand][opp_type][opp_count]))
#
# def get_position_factor(position):
#     idx = POSITIONS.index(position)
#     return 1.0 + (len(POSITIONS) - idx - 1) * 0.025
#
# def calc_ev(winrate, pot=4.0, cost=2.0):
#     return round(winrate * pot - (1 - winrate) * cost, 2)
#
# def decide_action(ev, mode):
#     if mode == "Aggressive":
#         if ev > -0.1:
#             return "Raise"
#         elif ev > -0.3:
#             return "Check"
#         else:
#             return "Fold"
#     else:  # GTO
#         if ev > 0.4:
#             return "Raise"
#         elif ev > 0.1:
#             return "Check"
#         else:
#             return "Fold"
#
# def generate_strategy(hand, pos, opp_type, opp_count, mode):
#     base_win = get_winrate(hand, opp_type, opp_count)
#     pos_factor = get_position_factor(pos)
#     result = []
#     for i, r in enumerate(ROUNDS):
#         win = base_win * pos_factor * (1 - 0.1 * i)
#         win = min(max(win, 0.05), 0.95)
#         ev = calc_ev(win, pot=4+i, cost=2)
#         action = decide_action(ev, mode)
#         result.append({"round": r, "action": action, "ev": round(ev, 2), "win": round(win, 2)})
#     return result
#
# def create_grouped_bar_chart(gto, agg):
#     fig = go.Figure()
#     for mode, path in zip(["GTO", "Aggressive"], [gto, agg]):
#         x = ROUNDS
#         y = [step['ev'] for step in path]
#         color = [ACTION_COLORS[step['action']] for step in path]
#         hover = [f"{mode} – {step['round']}<br>Action: {step['action']}<br>EV: {step['ev']}<br>WinRate: {step['win']*100:.1f}%" for step in path]
#         fig.add_trace(go.Bar(
#             x=x, y=y, name=mode,
#             marker_color=color,
#             hovertext=hover,
#             hoverinfo='text'
#         ))
#
#     fig.update_layout(
#         barmode='group',
#         title="EV Comparison by Street: GTO vs Aggressive",
#         yaxis_title="Expected Value (EV)",
#         height=450
#     )
#     return fig
#
# controls = dbc.Row([
#     dbc.Col([
#         html.Label("Hand:"),
#         dcc.Dropdown(id="ch4-hand", options=[{"label": h, "value": h} for h in WINRATE_TABLE], value="AQo")
#     ], width=3),
#     dbc.Col([
#         html.Label("Position:"),
#         dcc.Dropdown(id="ch4-pos", options=[{"label": p, "value": p} for p in POSITIONS], value="BTN")
#     ], width=3),
#     dbc.Col([
#         html.Label("Opponents:"),
#         dcc.Slider(id="ch4-opps", min=1, max=8, step=1, value=2, marks={i: str(i) for i in range(1, 9)})
#     ], width=3),
#     dbc.Col([
#         html.Label("Opponent Type:"),
#         dcc.RadioItems(id="ch4-type", options=[{"label": t, "value": t} for t in ['Loose', 'Tight']],
#                        value="Loose", labelStyle={'display': 'inline-block'})
#     ], width=3)
# ])
#
# legend_card = dbc.Card([
#     dbc.CardHeader("Legend: Action Colors"),
#     dbc.CardBody([
#         html.Ul([
#             html.Li([html.Span("Raise", style={"color": ACTION_COLORS['Raise']}), " – Aggressive action"]),
#             html.Li([html.Span("Check", style={"color": ACTION_COLORS['Check']}), " – Passive action"]),
#             html.Li([html.Span("Fold", style={"color": ACTION_COLORS['Fold']}), " – Give up hand"]),
#         ])
#     ])
# ], style={"marginTop": "20px"})
#
# chapter_4_layout = dbc.Container([
#     html.H2("Chapter 4: Strategic Visualization – GTO vs Aggressive"),
#     html.P("This final version compares strategy EVs using a grouped bar chart for each street."),
#     controls,
#     html.Hr(),
#     dcc.Graph(id="ch4-bar"),
#     legend_card,
#     html.Div(id="ch4-explanation", style={"marginTop": "20px"}),
#     # 直接在这里加导航
#     html.Div([
#         html.A("« Previous Chapter", href="/chapter-3", style={"marginRight":"12px"}),
#         html.A("Next Chapter: Range Visualization »", href="/chapter-5", style={"fontWeight":"bold"})
#     ], style={"marginTop":"32px"})
# ], fluid=True)
#
#
# def register_callbacks(app):
#     @app.callback(
#         [Output("ch4-bar", "figure"),
#          Output("ch4-explanation", "children")],
#         [Input("ch4-hand", "value"),
#          Input("ch4-pos", "value"),
#          Input("ch4-opps", "value"),
#          Input("ch4-type", "value")]
#     )
#     def update_graph(hand, pos, opps, opp_type):
#         gto = generate_strategy(hand, pos, opp_type, opps, "GTO")
#         agg = generate_strategy(hand, pos, opp_type, opps, "Aggressive")
#         fig = create_grouped_bar_chart(gto, agg)
#         explanation = f"EV comparison of {hand} on {pos} vs {opps} {opp_type} opponents reveals strategy divergence across streets."
#         return fig, explanation
#
# __all__ = ["chapter_4_layout", "register_callbacks"]

# chapters/chapter4.py
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import numpy as np
import random

# ====================== 多场景预设 ======================
SCENARIOS = [
    {
        "label": "AJ♠ vs 3 players, Flop: J♣7♠5♦",
        "hole": ["A♠", "J♠"],
        "villain_hands": [["K♣", "Q♦"], ["T♠", "9♠"], ["7♦", "7♥"]],
        "board": ["J♣", "7♠", "5♦", "2♥", "Q♣"],
        "texture": "Rainbow, One high two low",
        "quiz": [
            {
                "when": 0,  # flop
                "question": "You are on CO with J♠T♠, flop is J♣7♠5♦, you hit top pair. Facing a bet, what's your action?",
                "options": ["A. Call", "B. Raise", "C. Fold"],
                "answer": "A. Call",
                "explanation": "Calling is standard—top pair strong kicker, but raising risks only being called by better hands."
            },
            {
                "when": 1,  # turn
                "question": "Turn is 2♥, villain checks. Should you bet for value or check back?",
                "options": ["A. Value Bet", "B. Check Back"],
                "answer": "A. Value Bet",
                "explanation": "Still ahead most of the time—value bet gets calls from draws or weaker pairs."
            }
        ]
    },
    {
        "label": "KQ♥ vs 2 players, Flop: T♥9♥2♠ (Flush Draw)",
        "hole": ["K♥", "Q♥"],
        "villain_hands": [["A♦", "J♣"], ["T♣", "T♦"]],
        "board": ["T♥", "9♥", "2♠", "7♠", "A♥"],
        "texture": "Two-tone, Straight & Flush draws",
        "quiz": [
            {
                "when": 0,
                "question": "You flop a king-high flush draw with two overcards. Should you C-bet?",
                "options": ["A. Yes", "B. No"],
                "answer": "A. Yes",
                "explanation": "Semi-bluffing with strong draws applies pressure and builds the pot for when you hit."
            }
        ]
    }
]

# ====================== 工具函数 ======================
def get_board_visual(hole, villain_hands, board, street, player_cnt):
    suits = {"♠": "#1e88e5", "♥": "#e53935", "♦": "#fb8c00", "♣": "#43a047"}
    # 手牌展示
    hero_cards = [html.Span(card, style={"color": suits.get(card[-1], "#333"), "fontWeight": "bold", "fontSize": "22px", "marginRight": "8px"}) for card in hole]
    villain_cards = [html.Span("??", style={"color": "#888", "fontWeight": "bold", "marginRight": "4px"}) for _ in range(player_cnt - 1)]
    # 公共牌分阶段
    flop = board[:3]
    turn = board[3] if street > 0 else "?"
    river = board[4] if street > 1 else "?"
    flop_cards = [html.Span(card, style={"color": suits.get(card[-1], "#333"), "fontWeight": "bold", "fontSize": "21px", "marginRight": "6px"}) for card in flop]
    return html.Div([
        html.Div([
            html.Strong("Your Hand: "), *hero_cards,
            html.Strong("Villains: "), *villain_cards
        ], style={'marginBottom': '8px'}),
        html.Div([
            html.Strong("Board: "),
            *flop_cards,
            html.Span(turn, style={"color": "#333", "fontSize": "21px", "marginRight": "6px"}),
            html.Span(river, style={"color": "#333", "fontSize": "21px"})
        ], style={'marginBottom': '4px'})
    ])

def get_board_texture_tip(board):
    suits = [b[-1] for b in board[:3] if b != "?"]
    ranks = [b[:-1] for b in board[:3] if b != "?"]
    tip = []
    if len(set(suits)) == 3:
        tip.append("Rainbow flop: Flush draws impossible.")
    else:
        tip.append("Two-tone: Flush draws possible, extra caution needed.")
    if any(r in ['A', 'K', 'Q', 'J', 'T'] for r in ranks) and any(r in ['2', '3', '4', '5', '6', '7'] for r in ranks):
        tip.append("High card + low card: Aggression can fold out many weak hands.")
    if "J" in ranks and "T" in ranks:
        tip.append("Watch out for straight draws (QK, 98, etc).")
    if len(set(ranks)) < len(ranks):
        tip.append("Paired board: Sets and two-pair more likely.")
    return " ".join(tip) if tip else "Standard flop—play balanced."

def get_strategy_hint(street, scenario):
    if street == 0:
        if "flush" in scenario["texture"].lower():
            return "Flop: Draw-heavy board. Play aggressively with strong draws (C-bet/semi-bluff) and cautiously with weak hands."
        return "Flop: On dry boards, value bet strong hands, C-bet as bluff more often."
    elif street == 1:
        return "Turn: Continue value betting strong hands. If draw completes, slow down with weaker holdings."
    else:
        return "River: Value bet only the strongest hands; don't bluff into multiway pots."

def get_winrate_curve(scenario, street):
    # 这里用假数据代表动画效果，真实可接入概率计算
    hero = np.clip(np.linspace(0.42, 0.87, 3 + 1), 0, 1)
    villains = [np.clip(np.linspace(0.58, 0.13, 3 + 1), 0, 1) for _ in range(scenario['players'] - 1 if 'players' in scenario else 3)]
    return hero[:street + 2], [vill[:street + 2] for vill in villains]

def get_handtype_dist(scenario, street):
    # 随机生成主角此刻的牌型分布，实际可按已知算法调整
    stage = ["Flop", "Turn", "River"][street]
    if stage == "Flop":
        d = {"Top Pair": 0.45, "Draw": 0.25, "Middle Pair": 0.15, "Air": 0.15}
    elif stage == "Turn":
        d = {"Top Pair": 0.35, "Draw": 0.15, "Made Hand": 0.30, "Air": 0.20}
    else:
        d = {"Top Pair": 0.2, "Made Hand": 0.55, "Missed": 0.25}
    return d

def get_quiz_for_scenario(scenario, street):
    # 找到当前阶段的quiz
    quiz_list = scenario.get("quiz", [])
    for q in quiz_list:
        if q["when"] == street:
            return q
    return None

# ====================== Dash Layout ======================
layout = dbc.Container([
    html.H2("Chapter 4: Flop Decision Simulator", style={'marginTop': '24px', 'marginBottom': '8px'}),
    html.Div("Step through real-world flop scenarios: reveal each street, see how board texture and public cards affect equity and strategic actions, and test your judgment.",
             style={'fontSize': '18px', 'marginBottom': '20px'}),
    dbc.Row([
        dbc.Col([
            html.Label("Scenario:"),
            dcc.Dropdown(
                id="chapter4-scenario-dropdown",
                options=[{"label": s["label"], "value": i} for i, s in enumerate(SCENARIOS)],
                value=0,
                clearable=False,
                style={'width': '100%', 'marginBottom': '8px'}
            ),
        ], width=7),
        dbc.Col([
            html.Label("Quiz Challenge Mode:"),
            dcc.RadioItems(
                id="chapter4-quizmode",
                options=[
                    {"label": "Off", "value": "off"},
                    {"label": "On", "value": "on"}
                ],
                value="on", inline=True
            )
        ], width=5)
    ], style={"marginBottom": "8px"}),

    html.Div(id="chapter4-board-visual", style={'marginBottom': '12px', 'fontSize': '19px'}),

    dbc.Row([
        dbc.Col([
            dcc.Slider(
                id="chapter4-step-slider", min=0, max=2, step=1,
                marks={0: "Flop", 1: "Turn", 2: "River"}, value=0,
                included=False, updatemode='drag'
            ),
        ], width=8),
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("Previous", id="chapter4-prev-btn", outline=True, color="secondary", className="me-2"),
                dbc.Button("Next", id="chapter4-next-btn", outline=True, color="primary")
            ], size="sm")
        ], width=4)
    ], style={'margin': '12px 0'}),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="chapter4-winrate-graph", style={'height': '260px'}),
        ], width=8),
        dbc.Col([
            dcc.Graph(id="chapter4-handtype-pie", style={'height': '210px'}),
        ], width=4)
    ]),
    dbc.Row([
        dbc.Col([
            html.Div(id="chapter4-board-texture-tip", style={'fontSize': '16px', 'marginBottom': '8px'}),
            html.Div(id="chapter4-strategy-hint", style={'fontSize': '16px', 'marginBottom': '8px'}),
        ], width=7),
        dbc.Col([
            html.Div(id="chapter4-quiz-block", style={'marginTop': '8px'})
        ], width=5)
    ]),
    html.Hr(),
    html.Div([
        dcc.Link("← Previous: Table Position & Strategy Visualization", href="/chapter-3", style={'marginRight': '40px'}),
        dcc.Link("Next: Opponent Range Filtering →", href="/chapter-5", style={'marginLeft': '40px'})
    ], style={'margin': '40px 0 0 0', 'fontSize': '16px', 'textAlign': 'center'})
], fluid=True)

# ====================== 回调实现 ======================
def register_callbacks(app):
    # 步进控制
    @app.callback(
        Output("chapter4-step-slider", "value"),
        Input("chapter4-prev-btn", "n_clicks"),
        Input("chapter4-next-btn", "n_clicks"),
        State("chapter4-step-slider", "value"),
        prevent_initial_call=True
    )
    def step_slider_control(prev, nxt, val):
        triggered = ctx.triggered_id
        if triggered == "chapter4-prev-btn" and val > 0:
            return val - 1
        elif triggered == "chapter4-next-btn" and val < 2:
            return val + 1
        return val

    # 主视图刷新
    @app.callback(
        Output("chapter4-board-visual", "children"),
        Output("chapter4-winrate-graph", "figure"),
        Output("chapter4-handtype-pie", "figure"),
        Output("chapter4-board-texture-tip", "children"),
        Output("chapter4-strategy-hint", "children"),
        Output("chapter4-quiz-block", "children"),
        Input("chapter4-step-slider", "value"),
        Input("chapter4-scenario-dropdown", "value"),
        Input("chapter4-quizmode", "value")
    )
    def update_scene(street, scenario_idx, quizmode):
        scenario = SCENARIOS[scenario_idx]
        board = scenario["board"]
        visual = get_board_visual(
            scenario["hole"], scenario["villain_hands"], board, street, scenario.get("players", 4)
        )
        # 胜率曲线
        hero, villains = get_winrate_curve(scenario, street)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=["Flop", "Turn", "River"][:len(hero)], y=hero, mode="lines+markers",
            name="Your Equity", line=dict(width=3, color="#43A047")
        ))
        for i, v in enumerate(villains):
            fig.add_trace(go.Scatter(
                x=["Flop", "Turn", "River"][:len(v)], y=v, mode="lines+markers",
                name=f"Villain{i+1}", line=dict(width=2, dash="dot", color=f"rgba(30,136,229,{0.35+0.25*i})")
            ))
        fig.update_layout(
            title="Winrate/EQ Progression", yaxis=dict(range=[0, 1], tickformat=".0%"), xaxis_title="Street",
            yaxis_title="Winrate", template="plotly_white", height=260, showlegend=True, margin=dict(l=30,r=20,t=34,b=30)
        )
        # 牌型分布饼图
        dist = get_handtype_dist(scenario, street)
        pie_fig = go.Figure(data=[go.Pie(labels=list(dist.keys()), values=list(dist.values()), hole=.45,
                                         marker=dict(colors=["#43A047","#1E88E5","#fb8c00","#bdbdbd"]))])
        pie_fig.update_layout(height=210, margin=dict(l=8, r=8, t=28, b=12), title="Your Hand Type Dist.")
        # 公共牌纹理
        tip = get_board_texture_tip(board)
        # 策略提示
        strat = get_strategy_hint(street, scenario)
        # quiz
        quiz_block = None
        quizdata = get_quiz_for_scenario(scenario, street)
        if quizmode == "on" and quizdata:
            quiz_block = html.Div([
                html.Strong("Quiz: " + quizdata["question"]),
                dcc.RadioItems(
                    id="chapter4-quiz-radio",
                    options=[{"label": opt, "value": opt} for opt in quizdata["options"]],
                    value=None, style={"margin": "8px 0"}
                ),
                html.Div(id="chapter4-quiz-feedback")
            ], style={'marginTop': '10px', 'background': '#f3f6fb', 'padding': '14px', 'borderRadius': '9px'})
        return visual, fig, pie_fig, tip, strat, quiz_block

    # 测验反馈
    @app.callback(
        Output("chapter4-quiz-feedback", "children"),
        Input("chapter4-quiz-radio", "value"),
        State("chapter4-scenario-dropdown", "value"),
        State("chapter4-step-slider", "value")
    )
    def quiz_feedback(ans, scenario_idx, street):
        if not ans:
            return ""
        scenario = SCENARIOS[scenario_idx]
        quizdata = get_quiz_for_scenario(scenario, street)
        if not quizdata:
            return ""
        if ans == quizdata["answer"]:
            return html.Div("Correct! " + quizdata["explanation"], style={'color': '#388e3c', 'marginTop': '5px'})
        else:
            return html.Div(f"Incorrect. {quizdata['explanation']}", style={'color': '#E53935', 'marginTop': '5px'})

__all__ = ["layout", "register_callbacks"]
