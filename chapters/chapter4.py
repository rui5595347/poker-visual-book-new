from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import numpy as np


# ====================== Scenarios (preset) ======================
# note: small, hand-crafted examples. clear and easy to follow.
SCENARIOS = [
    {
        "label": "AJ♠ vs 3 players, Flop: J♣7♠5♦",
        "hole": ["A♠", "J♠"],
        "villain_hands": [["K♣", "Q♦"], ["T♠", "9♠"], ["7♦", "7♥"]],
        "board": ["J♣", "7♠", "5♦", "2♥", "Q♣"],
        "texture": "Rainbow, One high two low",
        "quiz": [
            {
                "when": 0,
                "question": "You are on CO with J♠T♠, flop is J♣7♠5♦, you hit top pair. Facing a bet, what's your action?",
                "options": ["A. Call", "B. Raise", "C. Fold"],
                "answer": "A. Call",
                "explanation": "Calling is standard—top pair strong kicker, but raising risks only being called by better hands."
            },
            {
                "when": 1,
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



# ====================== Helpers ======================
def get_board_visual(hole, villain_hands, board, street, player_cnt):
    """small visual block: hero hand + hidden villains + board (progressive)."""
    suits = {"♠": "#1e88e5", "♥": "#e53935", "♦": "#fb8c00", "♣": "#43a047"}

    hero_cards = [html.Span(card, style={"color": suits.get(card[-1], "#333"),
                                         "fontWeight": "bold", "fontSize": "22px", "marginRight": "8px"})
                  for card in hole]

    # villains hidden as "??" until you reveal; keep it simple
    villain_cards = [html.Span("??", style={"color": "#888", "fontWeight": "bold", "marginRight": "4px"})
                     for _ in range(player_cnt - 1)]

    flop = board[:3]
    turn = board[3] if street > 0 else "?"
    river = board[4] if street > 1 else "?"

    flop_cards = [html.Span(card, style={"color": suits.get(card[-1], "#333"),
                                         "fontWeight": "bold", "fontSize": "21px", "marginRight": "6px"})
                  for card in flop]

    return html.Div([
        html.Div([html.Strong("Your Hand: "), *hero_cards,
                  html.Strong("Villains: "), *villain_cards], style={'marginBottom': '8px'}),

        html.Div([html.Strong("Board: "), *flop_cards,
                  html.Span(turn,  style={"color": "#333", "fontSize": "21px", "marginRight": "6px"}),
                  html.Span(river, style={"color": "#333", "fontSize": "21px"})],
                 style={'marginBottom': '4px'})
    ])


def get_board_texture_tip(board):
    """tiny text tip based on flop texture; very rough rules on purpose."""
    suits = [b[-1] for b in board[:3] if b != "?"]
    ranks = [b[:-1] for b in board[:3] if b != "?"]
    tip = []

    if len(set(suits)) == 3:
        tip.append("Rainbow flop: Flush draws impossible.")
    else:
        tip.append("Two-tone: Flush draws possible, extra caution needed.")

    if any(r in ['A','K','Q','J','T'] for r in ranks) and any(r in ['2','3','4','5','6','7'] for r in ranks):
        tip.append("High card + low card: Aggression can fold out many weak hands.")

    if "J" in ranks and "T" in ranks:
        tip.append("Watch out for straight draws (QK, 98, etc).")

    if len(set(ranks)) < len(ranks):
        tip.append("Paired board: Sets and two-pair more likely.")

    return " ".join(tip) if tip else "Standard flop—play balanced."


def get_strategy_hint(street, scenario):
    """simple plan per street; keep it digestible."""
    if street == 0:
        if "flush" in scenario["texture"].lower():
            return "Flop: Draw-heavy board. Play aggressively with strong draws (C-bet/semi-bluff) and cautiously with weak hands."
        return "Flop: On dry boards, value bet strong hands, C-bet as bluff more often."
    elif street == 1:
        return "Turn: Continue value betting strong hands. If draw completes, slow down with weaker holdings."
    else:
        return "River: Value bet only the strongest hands; don't bluff into multiway pots."


def get_winrate_curve(scenario, street):
    """mock equity curves; hero up, villains down. visual effect only."""
    hero = np.clip(np.linspace(0.42, 0.87, 4), 0, 1)

    # note: if no 'players' key, default to 4 players (3 villains).
    # tiny quirk: using SCENARIOS[0] as default source; I keep it as-is (do not change logic).
    num_villains = max(1, (SCENARIOS[0].get('players', 4) - 1))

    villains = [np.clip(np.linspace(0.58, 0.13, 4), 0, 1) for _ in range(num_villains)]
    return hero[:street + 2], [vill[:street + 2] for vill in villains]


def get_handtype_dist(scenario, street):
    """pie slices by street; not from a solver, just for teaching."""
    stage = ["Flop", "Turn", "River"][street]
    if stage == "Flop":
        return {"Top Pair": 0.45, "Draw": 0.25, "Middle Pair": 0.15, "Air": 0.15}
    if stage == "Turn":
        return {"Top Pair": 0.35, "Draw": 0.15, "Made Hand": 0.30, "Air": 0.20}
    return {"Top Pair": 0.2, "Made Hand": 0.55, "Missed": 0.25}


def get_quiz_for_scenario(scenario, street):
    """pick the quiz that matches this street (if any)."""
    for q in scenario.get("quiz", []):
        if q["when"] == street:
            return q
    return None



# ====================== Layout (only buttons shown; others hidden but keep ids) ======================
layout = dbc.Container([
    html.H2("Chapter 4: Flop Decision Simulator",
            style={'fontSize': '36px', 'fontWeight': 'bold', 'textAlign': 'center'}),

    html.Div(
        "Step through real-world flop scenarios: reveal each street, see how board texture and public cards affect equity and strategic actions, and test your judgment.",
        style={'fontSize': '18px', 'marginBottom': '20px'}
    ),

    # hidden: scenario dropdown (default = first)
    dbc.Select(
        id="chapter4-scenario-dropdown",
        options=[{"label": s["label"], "value": i} for i, s in enumerate(SCENARIOS)],
        value=0,
        style={"display": "none"}
    ),

    # hidden: quiz mode switch (default off)
    dcc.RadioItems(
        id="chapter4-quizmode",
        options=[{"label": "Off", "value": "off"}, {"label": "On", "value": "on"}],
        value="off",
        style={"display": "none"}
    ),

    html.Div(id="chapter4-board-visual", style={'marginBottom': '12px', 'fontSize': '19px'}),

    # show only step buttons
    dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("Previous", id="chapter4-prev-btn", outline=True, color="secondary", className="me-2"),
                dbc.Button("Next",     id="chapter4-next-btn", outline=True, color="primary")
            ], size="sm")
        ], width=12, style={"textAlign": "center"})
    ], style={'margin': '12px 0'}),

    dbc.Row([
        dbc.Col([dcc.Graph(id="chapter4-winrate-graph", style={'height': '260px'})], width=8),
        dbc.Col([dcc.Graph(id="chapter4-handtype-pie", style={'height': '210px'})], width=4)
    ]),

    dbc.Row([
        dbc.Col([
            html.Div(id="chapter4-board-texture-tip", style={'fontSize': '16px', 'marginBottom': '8px'}),
            html.Div(id="chapter4-strategy-hint",     style={'fontSize': '16px', 'marginBottom': '8px'}),
        ], width=7),

        dbc.Col([html.Div(id="chapter4-quiz-block", style={'marginTop': '8px'})], width=5)
    ]),

    html.Hr(),
    html.Div([
        dcc.Link("← Previous: Table Position & Strategy Visualization", href="/chapter-3", style={'marginRight': '40px'}),
        dcc.Link("Next: Opponent Range Filtering →",                     href="/chapter-5", style={'marginLeft': '40px'})
    ], style={'margin': '40px 0 0 0', 'fontSize': '16px', 'textAlign': 'center'}),

    # hidden: slider (wrap in a div to hide; some versions of Slider ignore style directly)
    html.Div(
        dcc.Slider(
            id="chapter4-step-slider", min=0, max=2, step=1,
            marks={0: {"label": "Flop"}, 1: {"label": "Turn"}, 2: {"label": "River"}},
            value=0, included=False, updatemode='drag'
        ),
        style={"display": "none"}
    ),

    # hidden placeholders: quiz radio + feedback (keep ids alive for callbacks)
    dcc.RadioItems(id="chapter4-quiz-radio", options=[], value=None, style={"display": "none"}),
    html.Div(id="chapter4-quiz-feedback", style={"display": "none"}),
], fluid=True)



# ====================== Callbacks ======================
def register_callbacks(app):

    # step control (buttons → hidden slider)
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


    # main view refresh
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
        # fall back to scenario 0 if something odd
        try:
            idx = int(scenario_idx)
        except (TypeError, ValueError):
            idx = 0

        scenario = SCENARIOS[idx]
        board    = scenario["board"]

        visual = get_board_visual(scenario["hole"], scenario["villain_hands"],
                                  board, street, scenario.get("players", 4))

        hero, villains = get_winrate_curve(scenario, street)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=["Flop","Turn","River"][:len(hero)], y=hero, mode="lines+markers",
                                 name="Your Equity", line=dict(width=3, color="#43A047")))

        for i, v in enumerate(villains):
            fig.add_trace(go.Scatter(x=["Flop","Turn","River"][:len(v)], y=v, mode="lines+markers",
                                     name=f"Villain{i+1}", line=dict(width=2, dash="dot",
                                     color=f"rgba(30,136,229,{0.35+0.25*i})")))

        fig.update_layout(title="Winrate/EQ Progression",
                          yaxis=dict(range=[0,1], tickformat=".0%"),
                          xaxis_title="Street", yaxis_title="Winrate",
                          template="plotly_white", height=260, showlegend=True,
                          margin=dict(l=30, r=20, t=34, b=30))

        dist = get_handtype_dist(scenario, street)
        pie_fig = go.Figure(data=[go.Pie(labels=list(dist.keys()), values=list(dist.values()),
                                         hole=.45, marker=dict(colors=["#43A047","#1E88E5","#fb8c00","#bdbdbd"]))])
        pie_fig.update_layout(height=210, margin=dict(l=8, r=8, t=28, b=12), title="Your Hand Type Dist.")

        tip  = get_board_texture_tip(board)
        strat = get_strategy_hint(street, scenario)

        # quiz block (only when turned on)
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


    # quiz feedback
    @app.callback(
        Output("chapter4-quiz-feedback", "children"),
        Input("chapter4-quiz-radio", "value"),
        State("chapter4-scenario-dropdown", "value"),
        State("chapter4-step-slider", "value")
    )
    def quiz_feedback(ans, scenario_idx, street):
        if not ans:
            return ""

        # keep it safe to index
        try:
            idx = int(scenario_idx)
        except (TypeError, ValueError):
            idx = 0

        scenario = SCENARIOS[idx]
        quizdata = get_quiz_for_scenario(scenario, street)
        if not quizdata:
            return ""

        if ans == quizdata["answer"]:
            return html.Div("Correct! " + quizdata["explanation"], style={'color': '#388e3c', 'marginTop': '5px'})
        else:
            return html.Div(f"Incorrect. {quizdata['explanation']}", style={'color': '#E53935', 'marginTop': '5px'})


__all__ = ["layout", "register_callbacks"]
