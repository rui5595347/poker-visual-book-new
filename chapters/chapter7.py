# chapters/chapter7.py
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import numpy as np


# layout: keep ids the same so other modules work
layout = dbc.Container([

    html.H2("Chapter 7: Variance and Bankroll Management",
            style={'fontSize': '36px', 'fontWeight': 'bold', 'textAlign': 'center'}),

    html.Div(
        "Understand poker variance and learn how to manage your bankroll to survive downswings and maximize long-term success.",
        style={'fontSize': '18px', 'color': '#333', 'textAlign': 'center', 'marginBottom': '18px'}
    ),

    dbc.Row([
        dbc.Col([
            # small inputs on the left
            html.Div([
                html.Label("Winrate (BB/100):", style={'marginRight': '6px'}),
                dcc.Input(id="chapter7-winrate", type="number", value=2, debounce=True, min=-20, max=20, step=0.1,
                          style={'width': '80px', 'marginRight': '18px'}),
            ], style={"marginBottom": "8px"}),

            html.Div([
                html.Label("Std Deviation (BB/100):", style={'marginRight': '6px'}),
                dcc.Input(id="chapter7-stdev", type="number", value=90, debounce=True, min=10, max=200, step=1,
                          style={'width': '80px'}),
            ], style={"marginBottom": "8px"}),

            html.Div([
                html.Label("Hands to Simulate:", style={'marginRight': '6px'}),
                dcc.Input(id="chapter7-numhands", type="number", value=5000, min=500, max=100000, step=100,
                          style={'width': '100px', 'marginRight': '18px'}),
            ], style={"marginBottom": "8px"}),

            html.Div([
                html.Label("Simulations:", style={'marginRight': '6px'}),
                dcc.Input(id="chapter7-numsim", type="number", value=50, min=10, max=200, step=1,
                          style={'width': '80px'}),
            ], style={"marginBottom": "12px"}),

            dbc.Button("Run Simulation", id="chapter7-run-sim", color="primary", className="mt-1"),
        ], width=4),

        dbc.Col([
            # plots on the right with a loading spinner
            dcc.Loading(
                id="chapter7-loading-curves",
                type="circle",
                children=[
                    dcc.Graph(id="chapter7-bankroll-curves", style={"height": "390px"}),
                    dcc.Graph(id="chapter7-end-result-hist", style={"height": "200px"})
                ]
            ),
            html.Div(id="chapter7-summary-output", style={'marginTop': '18px', 'fontSize': '16px'})
        ], width=8),
    ]),

    html.Hr(),

    html.Div([
        html.Strong("Teaching Tip: "),
        "Poker is a long-run game! Even with a winning strategy, downswings are inevitable. "
        "Solid bankroll management and mindset are crucial to success."
    ], style={'background': '#fff9e6', 'padding': '14px', 'borderRadius': '8px', 'fontSize': '16px'}),

    html.Div([
        dcc.Link("← Previous: Bluffing & Frequency Control", href="/chapter-6", style={'marginRight': '40px'}),
        html.Span("End of Book", style={'marginLeft': '40px', 'color': '#aaa'})
    ], style={'margin': '40px 0 0 0', 'fontSize': '16px', 'textAlign': 'center'})

], fluid=True)



# --------------------- Callback registration ---------------------
def register_callbacks(app):

    @app.callback(
        Output("chapter7-bankroll-curves", "figure"),
        Output("chapter7-end-result-hist", "figure"),
        Output("chapter7-summary-output", "children"),
        Input("chapter7-run-sim", "n_clicks"),
        State("chapter7-winrate", "value"),
        State("chapter7-stdev", "value"),
        State("chapter7-numhands", "value"),
        State("chapter7-numsim", "value")
    )
    def simulate_curves(n_clicks, winrate, stdev, numhands, numsim):
        """
        run a simple Monte Carlo:
        - treat result per 100 hands as Normal(winrate, stdev)
        - accumulate to make a curve
        - repeat many times to see variance
        note: units are BB per 100 hands (BB/100)
        """
        if not n_clicks or winrate is None or stdev is None or numhands is None or numsim is None:
            # initial blank figures
            fig1 = go.Figure(); fig2 = go.Figure()
            return fig1, fig2, ""

        winrate = float(winrate)
        stdev   = float(stdev)
        numhands = int(numhands)
        numsim   = int(numsim)

        # simulate in chunks of 100 hands
        steps  = numhands // 100
        curves = []
        end_vals = []

        for i in range(numsim):
            per100_win = np.random.normal(loc=winrate, scale=stdev, size=steps)
            cum_curve  = np.cumsum(per100_win)
            full_curve = np.insert(cum_curve, 0, 0)   # start at 0 for nicer plot
            curves.append(full_curve)
            end_vals.append(full_curve[-1])

        # bankroll curves figure
        fig1 = go.Figure()
        x_vals = np.arange(0, numhands + 1, 100)

        for curve in curves:
            fig1.add_trace(go.Scatter(
                x=x_vals, y=curve, mode='lines',
                line=dict(width=1.5), opacity=0.48, showlegend=False
            ))

        fig1.update_layout(
            title="Simulated Bankroll Curves",
            xaxis_title="Hands Played",
            yaxis_title="Net Result (BB)",
            height=390,
            template="plotly_white",
            margin=dict(l=20, r=20, t=50, b=10)
        )

        # histogram for final outcomes
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(
            x=end_vals, nbinsx=22,
            marker_color="#43A047", opacity=0.82
        ))
        fig2.update_layout(
            title="Final Bankroll Distribution",
            xaxis_title="Total Profit/Loss (BB)",
            yaxis_title="Frequency",
            height=200,
            template="plotly_white",
            margin=dict(l=20, r=20, t=38, b=10)
        )

        # quick text summary (kept same fields)
        n_win   = sum(v > 0 for v in end_vals)
        n_loss  = sum(v < 0 for v in end_vals)
        max_win = int(np.max(end_vals))
        max_loss = int(np.min(end_vals))
        mean_val   = np.mean(end_vals)
        median_val = np.median(end_vals)

        stats = f"""
Simulations: {numsim} | Hands: {numhands} | Winrate: {winrate} BB/100 | Stdev: {stdev} BB/100  
Profitable runs: {n_win} | Losing runs: {n_loss}  
Max Profit: {max_win} BB | Max Loss: {max_loss} BB  
Mean: {mean_val:.1f} BB | Median: {median_val:.1f} BB
        """

        return fig1, fig2, stats


__all__ = ["layout", "register_callbacks"]
