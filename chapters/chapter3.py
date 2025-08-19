import dash
from dash import dcc, html, Input, Output, State, ALL, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import numpy as np

# --- Data ---
# simple mock numbers for teaching. keep it small and readable.
positions = ["UTG", "UTG+1", "UTG+2", "MP", "HJ", "CO", "BTN", "SB", "BB"]
position_metrics = {
    "UTG":  [0.2, 0.3, 0.2, 0.1, 0.3],
    "UTG+1":[0.25,0.35,0.25,0.15,0.35],
    "UTG+2":[0.28,0.38,0.3, 0.18,0.37],
    "MP":   [0.3, 0.4, 0.35,0.2, 0.4],
    "HJ":   [0.32,0.42,0.38,0.3, 0.43],
    "CO":   [0.4, 0.5, 0.45,0.35,0.5],
    "BTN":  [0.5, 0.6, 0.5, 0.6, 0.6],
    "SB":   [0.15,0.25,0.2, 0.1, 0.25],
    "BB":   [0.1, 0.2, 0.15,0.05,0.2]
}
metric_labels = ["Win Rate", "VPIP", "PFR", "Steal", "Aggression"]

# short, friendly notes per seat
position_desc = {
    "UTG":   "First to act. Tightest range: only the strongest hands.",
    "UTG+1": "Still early. You can add AQ, JJ.",
    "UTG+2": "Early-ish. Can mix in some suited connectors.",
    "MP":    "Middle. Start to loosen up a bit.",
    "HJ":    "Hijack. If late seats are passive, push more.",
    "CO":    "Cutoff. Good spot to attack the blinds.",
    "BTN":   "Button. Best seat. Open widest, apply pressure.",
    "SB":    "Small blind. Tough spot. Defend tight.",
    "BB":    "Big blind. Defend often, but out of position."
}

# --- Color palette (Okabe–Ito, colorblind-friendly) ---
# note: I avoid red/green to be safe for color-blind users.
BLUE   = "#0072B2"   # positive / main accent
SKY    = "#56B4E9"   # fill / secondary
ORANGE = "#E69F00"   # contrast
PURPLE = "#CC79A7"   # spare
GREY   = "#999999"   # spare gray


# --- Radar Chart ---
def radar_figure(metrics, pos):
    """build a single-seat radar. keep it clean."""
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=metrics + [metrics[0]],
        theta=metric_labels + [metric_labels[0]],
        fill='toself', name=pos,
        fillcolor='rgba(86,180,233,0.5)',   # SKY with alpha
        line_color=BLUE
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 0.7])),
        showlegend=False,
        margin=dict(t=30, l=20, r=20, b=20)
    )
    return fig


def compare_radar_figure(metrics, pos):
    """compare the chosen seat vs BTN. quick visual contrast."""
    fig = go.Figure()

    # current pick → sky/blue (focus)
    fig.add_trace(go.Scatterpolar(
        r=metrics + [metrics[0]],
        theta=metric_labels + [metric_labels[0]],
        fill='toself', name=pos,
        fillcolor='rgba(86,180,233,0.4)',    # SKY with alpha
        line_color=BLUE
    ))

    # reference → BTN in orange (contrast)
    fig.add_trace(go.Scatterpolar(
        r=position_metrics['BTN'] + [position_metrics['BTN'][0]],
        theta=metric_labels + [metric_labels[0]],
        fill='toself', name='BTN (reference)',
        fillcolor='rgba(230,159,0,0.35)',    # ORANGE with alpha
        line_color=ORANGE
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 0.7])),
        showlegend=True,
        margin=dict(t=30, l=20, r=20, b=20)
    )
    return fig


def profit_bar_figure():
    """simple bar: long-term win rate per seat (illustrative only)."""
    profits = [position_metrics[s][0] for s in positions]

    # blue for better, orange for worse. no red/green.
    colors = [BLUE if p > 0.25 else ORANGE for p in profits]
    max_p = max(profits)

    fig = go.Figure(go.Bar(
        x=positions, y=profits,
        marker=dict(color=colors),
        text=[f"{p:+.2f}" for p in profits],
        textposition="outside",
        cliponaxis=False
    ))
    fig.update_layout(
        title="Long-term Win Rate (illustrative)",
        yaxis_title="Win Rate",
        height=240,
        margin=dict(l=30, r=20, t=50, b=30),
        plot_bgcolor="#fff"
    )
    fig.update_yaxes(range=[0, max_p * 1.25])   # leave some headroom
    return fig


def animation_comparison_figure():
    """tiny bar pair: same hand, different seat → very different EV."""
    fig = go.Figure(go.Bar(
        x=["BTN (In Position)", "UTG (Out of Position)"],
        y=[2.5, -1.2],
        marker_color=[BLUE, ORANGE],   # colorblind-safe pair
        text=["+2.5BB", "-1.2BB"],
        textposition="auto",
        cliponaxis=False
    ))
    fig.update_layout(
        title="Same Hand, Different Position Outcome",
        title_x=0.5,                   # center title a bit
        yaxis_title="Sample Profit (BB)",
        margin=dict(l=40, r=20, t=44, b=26),
        plot_bgcolor="#e3f2fd"
    )
    return fig



# --- Layout ---
layout = dbc.Container([

    html.H2("Chapter 3: Table Position & Strategy Visualization",
            className="text-center mt-4 mb-4",
            style={'fontSize': '36px', 'fontWeight': 'bold', 'textAlign': 'center'}),

    dbc.Row([
        # left column: poker table + bar chart
        dbc.Col([
            html.Div([
                html.Div([
                    html.Img(
                        src="/assets/table_background.png",
                        className="poker-table-img",
                        style={"width": "100%", "display": "block"}
                    ),
                    html.Div("Dealer", className="dealer-chip"),
                    *[html.Div(pos, className=f"seat seat-{i}", id={"type": "seat", "index": pos}, n_clicks=0)
                      for i, pos in enumerate(positions)]
                ],
                    id="poker-table",
                    style={
                        "position": "relative",
                        "width": "100%",
                        "maxWidth": "500px",
                        "margin": "0"
                    }
                ),
            ], style={"width": "100%"}),

            dcc.Graph(id="profit-bar", figure=profit_bar_figure(),
                      style={"height": "220px", "marginTop": "16px"})
        ], width=5),

        # right column: radar card
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
###  Metric Explanation
-  **VPIP**: Voluntarily Put Money In Pot – more aggressive if higher.
-  **PFR**: Pre-Flop Raise frequency – shows aggression level.
-  **Steal**: Trying to steal blinds – key in CO/BTN.
-  **Aggression**: Ratio of raises to calls – shows pressure.
                    """, className="mt-4")
                ])
            ])
        ], width=7),
    ]),

    # --- centered block: Position Advantage (small animation style snippet) ---
    dbc.Row(
        dbc.Col([
            html.Hr(),
            html.H4("Position Advantage Animation:", style={'textAlign': 'center'}),
            dcc.Graph(
                id="anim-comp",
                figure=animation_comparison_figure(),
                style={'height': '225px', 'width': '70%', 'margin': '0 auto'}  # center graph and limit width a bit
            ),
            html.Div(
                "Animation: Same hand, different seat. BTN acts last and often wins more; "
                "UTG acts first and may lose due to less info.",
                style={'fontSize': '15px', 'color': '#546e7a',
                       'display': 'flex', 'justifyContent': 'center', 'marginTop': '6px'}
            )
        ], width=10),
        justify="center"   # center the whole column
    ),

    html.Hr(),
    html.Div([
        dcc.Link("« Chapter 2: EV Radar", href="/chapter-2", style={"marginRight": "20px"}),
        dcc.Link("Next Chapter ►", href="/chapter-4")
    ], className="text-center mb-4")

], fluid=True)



# --- Callback ---
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
        # no click yet → show hint and keep default styles
        if not clicks or all(c is None or c == 0 for c in clicks):
            # when classes is None/empty, build a safe default (avoid errors later)
            if not classes:
                classes = [f"seat seat-{i}" for i in range(len(positions))]
            return "Select a Position", "Click on a table seat to view strategy details.", {}, "", [cls for cls in classes]

        # take the most recent (highest count) as the current pick
        last_click_idx = np.argmax([c or 0 for c in clicks])
        triggered_id   = ids[last_click_idx]['index']

        metrics = position_metrics.get(triggered_id, [0.2]*5)

        radar = radar_figure(metrics, triggered_id)

        compare_card = dbc.Card([
            dbc.CardHeader(f" {triggered_id} vs BTN (Button Position)"),
            dbc.CardBody([
                dcc.Graph(figure=compare_radar_figure(metrics, triggered_id), style={"height": "300px"}),
                dcc.Markdown("""
 **Analysis Tips**:
- Compared to BTN, you have a positional disadvantage.
- If your VPIP/PFR is much lower than BTN, tighten your range.
- BTN can steal more; defend your range wisely.
                """)
            ])
        ])

        # short markdown block. easy to scan. nothing fancy.
        desc_text = f"""
 **Selected Position**: **{triggered_id}**
 **Strengths & Weaknesses**: Use the radar chart to assess your position.
 **Suggested Strategy**: Adjust range or aggression based on VPIP / PFR.
️ **Common Pitfall**: Avoid excessive limping or calling with marginal hands.
{position_desc.get(triggered_id, "")}
        """

        # highlight the active seat (append a class)
        new_classes = []
        for i, seat in enumerate(ids):
            base = f"seat seat-{i}"
            if seat['index'] == triggered_id:
                base += " seat-active"
            new_classes.append(base)

        return f"Position: {triggered_id}", dcc.Markdown(desc_text), radar, compare_card, new_classes



__all__ = ["layout", "register_callbacks"]
