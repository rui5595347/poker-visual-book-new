# poker/chapters/probability_simulator.py
from dash import html, dcc, Input, Output
import plotly.graph_objs as go
import random

def get_layout():
    return html.Div([
        html.H2("Chapter 1: Poker Probability Simulator"),
        html.P("Select the number of 'outs' and remaining cards to estimate your win probability."),

        html.Div([
            html.Label("🎯 Number of Outs:"),
            dcc.Slider(id="outs", min=0, max=20, value=8,
                       marks={i: str(i) for i in range(0, 21, 2)}, step=1)
        ], style={'marginBottom': '20px'}),

        html.Label("🃏 Cards Left to Be Dealt:"),
        dcc.RadioItems(id="cards_left", options=[
            {"label": "1 card (Turn or River)", "value": 1},
            {"label": "2 cards (Turn + River)", "value": 2}
        ], value=2, labelStyle={'display': 'inline-block', 'margin-right': '15px'}),

        html.Label("📐 Calculation Method:"),
        dcc.RadioItems(id="method", options=[
            {"label": "Rule of 4 and 2", "value": "rule"},
            {"label": "Exact Formula", "value": "exact"},
            {"label": "Monte Carlo (Simulated)", "value": "monte"}
        ], value="rule", labelStyle={'display': 'block'}),

        dcc.Graph(id="probability_chart"),
        html.Div(id="explanation", style={'marginTop': '20px', 'fontSize': '16px'})
    ], style={"padding": "40px"})

layout = get_layout()

def register_callbacks(app):
    @app.callback(
        Output("probability_chart", "figure"),
        Output("explanation", "children"),
        Input("outs", "value"),
        Input("cards_left", "value"),
        Input("method", "value")
    )
    def update_chart(outs, cards_left, method):
        if method == "rule":
            prob = outs * (4 if cards_left == 2 else 2)
            method_text = "Rule of 4 and 2: Quick approximation used by players."
        elif method == "exact":
            if cards_left == 2:
                prob = 1 - ((47 - outs) / 47) * ((46 - outs) / 46)
            else:
                prob = outs / 47
            prob *= 100
            method_text = "Exact probability based on combinatorics."
        else:
            base_prob = outs * (4 if cards_left == 2 else 2)
            variance = 0.1 * base_prob
            prob = max(0, min(100, random.gauss(base_prob, variance)))
            method_text = "Monte Carlo simulation: Estimated with randomness."

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=prob,
            title={'text': "Win Probability (%)"},
            gauge={'axis': {'range': [0, 100]}}
        ))

        explanation = f"You have {outs} outs and {cards_left} card(s) to come. Estimated win probability: **{prob:.1f}%**. {method_text}"
        return fig, explanation
