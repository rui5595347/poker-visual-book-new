# chapters/chapter6.py
from dash import dcc, html, Input, Output
import plotly.graph_objs as go

# simple slider config (pot-size bet as a ratio)
slider_marks = {0: '0%', 0.25: '25%', 0.5: '50%', 1: '100%', 1.5: '150%'}
slider_min = 0
slider_max = 1.5
slider_step = 0.01


def calc_bluff_ratio(bet_pot_ratio):
    """
    given bet size as pot ratio, compute value:bluff mix by GTO formula
    bluff% = b / (1 + b)
    value% = 1 - bluff%
    keep it non-negative, nothing fancy
    """
    bluff_ratio = bet_pot_ratio / (1 + bet_pot_ratio) if bet_pot_ratio >= 0 else 0
    value_ratio = 1 - bluff_ratio
    return max(value_ratio, 0), max(bluff_ratio, 0)


def get_example(value_ratio, bluff_ratio, value_count=30):
    """
    tiny helper to give a concrete combo example.
    say we have 30 value combos → how many bluffs can we add.
    """
    if value_ratio == 0:
        bluff_count = 0
    else:
        bluff_count = int(round((bluff_ratio / value_ratio) * value_count))

    return f"If your value betting range has {value_count} combinations, you can add about {bluff_count} bluff combos for balance."


def get_warning(bet_pot_ratio):
    """soft guard rails; just some text hints"""
    if bet_pot_ratio < 0.05:
        return "Note: Extremely small bets are rare in real games; this theoretical frequency is for reference only."
    elif bet_pot_ratio > 1.5:
        return "Note: Oversized bets are seldom seen except in specific spots; use the theory as a guideline."
    return ""


# keep all ids with prefix "chapter6-" so they do not clash with other chapters
layout = html.Div([

    html.H2(
        "Chapter 6: Bluffing Skills & Frequency Control",
        style={'fontSize': '36px', 'fontWeight': 'bold', 'textAlign': 'center'}
    ),

    html.Div(
        "Learn the art of bluffing: when to bluff, how to choose bluff combos, and how to control bluff frequency to avoid being exploited.",
        style={'fontSize': '18px', 'color': '#333', 'marginBottom': '18px'}
    ),

    html.Div([
        html.Strong("Key Concept: "),
        html.Span([
            "A successful poker strategy requires balancing value bets and bluffs. ",
            "The optimal bluffing frequency (GTO) is tied to your bet size — bigger bets need a higher bluff ratio to keep opponents guessing."
        ])
    ], style={'background': '#f2fbf2', 'borderLeft': '5px solid #43A047',
              'padding': '14px 16px', 'borderRadius': '8px', 'marginBottom': '28px'}),

    html.Div([
        html.Label("Choose your bet size (as % of pot):", style={'fontWeight': 'bold', 'fontSize': '16px'}),
        dcc.Slider(
            id='chapter6-bet-slider',
            min=slider_min, max=slider_max, step=slider_step,
            marks=slider_marks, value=0.5,
            tooltip={'always_visible': False}
        ),
    ], style={'margin': '18px 0 16px 0'}),

    dcc.Graph(id='chapter6-bluff-pie',      style={'height': '330px'}),

    html.Div(id='chapter6-ratio-output',    style={'fontSize': '18px', 'marginTop': '18px'}),
    html.Div(id='chapter6-example-output',  style={'fontSize': '16px', 'margin': '8px 0 0 0', 'color': '#23689b'}),
    html.Div(id='chapter6-warning-output',  style={'fontSize': '15px', 'marginTop': '8px', 'color': '#D84315'}),

    html.Hr(style={'margin': '40px 0 22px 0'}),

    html.Div([
        html.Strong("Teaching Tip: "),
        "Even with mathematically balanced frequencies, some bluffs will get caught. That is okay. ",
        "Keep calm, follow the plan, and manage bankroll well. ",
        html.Span("Up next: handling variance and building a stronger poker mindset.", style={'color': '#388e3c', 'fontWeight': 'bold'})
    ], style={'background': '#fff9e6', 'padding': '16px', 'borderRadius': '8px', 'fontSize': '16px'}),

    html.Div([
        dcc.Link("← Previous: Range Filtering & Hand Reading", href="/chapter-5", style={'marginRight': '40px'}),
        dcc.Link("Next: Bankroll Management & Psychology →", href="/chapter-7",    style={'marginLeft':  '40px'})
    ], style={'margin': '40px 0 0 0', 'fontSize': '16px', 'textAlign': 'center'})

], style={'maxWidth': '650px', 'margin': '0 auto',
          'padding': '36px 10px 20px 10px', 'fontFamily': 'system-ui'})


# register interactions
def register_callbacks(app):

    @app.callback(
        Output('chapter6-bluff-pie', 'figure'),
        Output('chapter6-ratio-output', 'children'),
        Output('chapter6-example-output', 'children'),
        Output('chapter6-warning-output', 'children'),
        Input('chapter6-bet-slider', 'value')
    )
    def update_bluff_pie(bet_pot_ratio):
        """
        main updater:
        - compute value/bluff mix
        - draw a donut chart
        - write small text lines
        """
        value_ratio, bluff_ratio = calc_bluff_ratio(bet_pot_ratio)

        labels = ['Value bet', 'Bluff']
        values = [value_ratio, bluff_ratio]

        # Okabe–Ito colorblind-friendly pair (blue/orange)
        # Value = blue, Bluff = orange
        colors = ['#0072B2', '#E69F00']

        fig = go.Figure(data=[go.Pie(
            labels=labels, values=values, hole=0.45,
            marker=dict(colors=colors),
            textinfo='label+percent', sort=False,
            pull=[0.01, 0.01]
        )])

        fig.update_layout(
            showlegend=True,
            legend=dict(orientation='h', y=-0.13, x=0.21, font=dict(size=15)),
            margin=dict(l=10, r=10, t=20, b=20),
            annotations=[dict(
                text=f"{int(round(value_ratio*100))}% : {int(round(bluff_ratio*100))}%",
                x=0.5, y=0.5, font_size=28, showarrow=False
            )]
        )

        ratio_str   = f"Current bet size: {int(round(bet_pot_ratio*100))}% of pot — Value bet: {int(round(value_ratio*100))}%, Bluff: {int(round(bluff_ratio*100))}%"
        example_str = get_example(value_ratio, bluff_ratio, value_count=30)
        warning     = get_warning(bet_pot_ratio)

        return fig, ratio_str, example_str, warning


# optional, I like being explicit when importing modules elsewhere
__all__ = ["layout", "register_callbacks"]
