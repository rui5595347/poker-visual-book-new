from dash import html, dcc, Input, Output, State
import plotly.graph_objs as go
import random
from collections import Counter   # (left here on purpose; I sometimes import it when prototyping)

# simple rank map for quick checks
rank_map = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7,
            '8':8, '9':9, 'T':10, 'J':11, 'Q':12, 'K':13, 'A':14}


# ========== Layout ==========
def get_layout():
    # small intro with what "outs" means
    return html.Div([

        html.H2("Chapter 1: Outs & Odds",
                style={'fontSize': '36px', 'fontWeight': 'bold', 'textAlign': 'center'}),

        html.Div([
            html.H4(" What are 'Outs' in Poker?"),
            html.P("Outs are the unseen cards that can improve your hand into a winning one."),
            html.P("For example: You hold ♠10 and ♠J. The flop shows ♠K ♠2 ♦Q."),
            html.Ul([
                html.Li("9 spades complete a flush"),
                html.Li("4 Aces complete a straight")
            ]),
            html.P("That gives you 13 potential outs!")
        ], style={"marginBottom": "25px"}),

        html.Label(" Select number of outs:"),
        dcc.Slider(
            id="outs", min=0, max=20, value=8,
            marks={i: str(i) for i in range(0, 21, 2)}, step=1
        ),

        html.Div(id="outs-tip", style={"marginBottom": "20px", "fontStyle": "italic"}),

        html.Label(" Cards left to be dealt:"),
        dcc.RadioItems(
            id="cards_left",
            options=[
                {"label": "1 card (Turn or River)", "value": 1},
                {"label": "2 cards (Turn + River)", "value": 2}
            ],
            value=2,
            labelStyle={"display": "inline-block", "marginRight": "15px"}
        ),

        html.Label(" Calculation method:"),
        dcc.RadioItems(
            id="method",
            options=[
                {"label": "Rule of 4 and 2", "value": "rule"},
                {"label": "Exact Formula", "value": "exact"},
                {"label": "Monte Carlo Simulation", "value": "monte"}
            ],
            value="rule",
            labelStyle={"display": "block"}
        ),

        html.Hr(),
        dcc.Graph(id="probability_chart"),
        html.Div(id="explanation", style={"marginTop": "20px", "fontSize": "16px"}),

        html.Hr(),
        html.H3(" Practice Time: Count the Outs!"),
        html.Div(id="quiz-question-text", style={"fontSize": "18px", "marginBottom": "10px"}),

        dcc.Input(id="quiz-input", type="number", placeholder="Enter outs", min=0, max=20),
        html.Button("Check Answer", id="quiz-submit", n_clicks=0),
        html.Button("Next Question", id="quiz-next", n_clicks=0, style={"marginLeft": "10px"}),
        html.Div(id="quiz-feedback", style={"marginTop": "20px", "fontWeight": "bold"}),
        dcc.Store(id="quiz-question-store"),

        html.Hr(),
        html.Div([
            dcc.Link("Next Chapter →", href="/chapter-2", refresh=True)
        ], style={"textAlign": "right", "marginTop": "40px"})
    ], style={"padding": "40px"})


layout = get_layout()



# ========== Callbacks ==========
def register_callbacks(app):

    # real Monte Carlo: sample without replacement from unseen cards
    # note: I keep it simple on purpose. we treat "outs" as the first N indices
    def monte_prob(outs, cards_left, trials=20000):
        deck_size = 47 if cards_left == 2 else 46    # 47 unseen with two to come, else 46
        hits = 0

        for _ in range(trials):
            draw = random.sample(range(deck_size), cards_left)
            # if any drawn index falls in [0, outs), we say we hit an out
            if any(x < outs for x in draw):
                hits += 1

        return hits / trials * 100.0   # return percent



    @app.callback(
        Output("probability_chart", "figure"),
        Output("explanation", "children"),
        Output("outs-tip", "children"),
        Input("outs", "value"),
        Input("cards_left", "value"),
        Input("method", "value")
    )
    def update_chart(outs, cards_left, method):
        # choose the method: quick rule, exact, or simulation
        if method == "rule":
            # mental math: 4x on turn+river, 2x on one street
            prob = outs * (4 if cards_left == 2 else 2)
            method_text = "Rule of 4 and 2: fast estimate."

        elif method == "exact":
            # exact math. this is the standard way for ≥1 success
            if cards_left == 2:
                # 1 - [(47-outs)/47] * [(46-outs)/46]
                prob = 1 - ((47 - outs) / 47) * ((46 - outs) / 46)
            else:
                # for one card to come we have outs/46
                prob = outs / 46
            prob *= 100
            method_text = "Exact odds from probability theory."

        else:
            # Monte Carlo. bigger trials → smoother number, but slower
            prob = monte_prob(outs, cards_left, trials=20000)
            method_text = "Monte Carlo simulation (approximate)."

        # clamp to [0,100] just in case
        prob = max(0, min(100, prob))

        # gauge is okay for a single percentage
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=prob,
            title={'text': "Estimated Win Probability (%)"},
            gauge={'axis': {'range': [0, 100]}}
        ))

        tip = f" With {outs} outs and {cards_left} card(s) left, this is your chance to hit."
        # I leave the ** here; I sometimes like the look even if it is just plain text
        explain = f"You have **{outs} outs**, and **{cards_left} card(s)** to come. Estimated win: **{prob:.1f}%**. {method_text}"

        return fig, explain, tip



    # quick random quiz: we draw 5 cards (2 hole + 3 flop)
    def generate_quiz():
        suits = ["♠", "♥", "♦", "♣"]
        ranks = list(rank_map.keys())
        deck = [r + s for r in ranks for s in suits]
        cards = random.sample(deck, 5)
        return {"hole": cards[:2], "flop": cards[2:]}



    # compute a very rough outs count:
    # - flush draw → 9
    # - straight draw (gutshot approx) → 4
    # this is enough for a small practice widget
    def compute_outs(hole, flop):
        suits = [c[1] for c in hole + flop]
        ranks = [rank_map[c[0]] for c in hole + flop]

        flush_outs = 9 if any(suits.count(s) == 4 for s in set(suits)) else 0

        values = sorted(set(ranks))
        straight_outs = 0
        for v in values:
            # if we have 4 in a 5-long window, we call it a gutshot-like thing
            if sum((v + i in values) for i in range(5)) == 4:
                straight_outs = 4
                break

        total = flush_outs + straight_outs

        explain = []
        if flush_outs:    explain.append("Flush draw → 9 outs")
        if straight_outs: explain.append("Straight draw → approx. 4 outs")

        return total, explain



    @app.callback(
        Output("quiz-question-store", "data"),
        Output("quiz-question-text", "children"),
        Input("quiz-next", "n_clicks")
    )
    def serve_question(n):
        # just give a new random question each time
        q = generate_quiz()
        txt = f"You hold {q['hole'][0]} and {q['hole'][1]}. Flop: {q['flop'][0]}, {q['flop'][1]}, {q['flop'][2]}"
        return q, txt



    @app.callback(
        Output("quiz-feedback", "children"),
        Input("quiz-submit", "n_clicks"),
        State("quiz-input", "value"),
        State("quiz-question-store", "data"),
        prevent_initial_call=True
    )
    def check_quiz(_, user_ans, q):
        # safe guards first
        if not q or user_ans is None:
            return " Please input a number."

        correct, explain = compute_outs(q['hole'], q['flop'])

        # small corner case: user says 1~2 while true is 0 (often thinking runner-runner)
        if correct == 0 and user_ans in [1, 2]:
            return html.Div([
                html.Span(" Nice thinking! ", style={"color": "orange", "fontWeight": "bold"}),
                "You're probably hoping for a ", html.Em("runner-runner straight"),
                " – that means you’d need two perfect cards in a row.",
                html.Br(),
                "But that’s not counted in standard 'outs', which only include one-card draws.",
                html.Br(), html.Strong("Correct outs: 0. No major draws.")
            ])

        if user_ans == correct:
            return f" Correct! {' | '.join(explain)}" if explain else " Correct! No major draws."

        return f" Not quite. Correct = {correct}. " + (" | ".join(explain) if explain else "No major draws.")
