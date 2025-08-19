from dash import Dash, dcc, html, Input, Output
from chapters import chapter1, chapter2, chapter3, chapter4, chapter5, chapter6, chapter7


# small single-file app bootstrap
# note: suppress_callback_exceptions=True because we swap pages dynamically
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "Poker Visual Learning Book"


# root layout: url + a slot where we render each chapter
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])



# --- simple router ---
# keep ids and paths the same so existing links do not break
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    # default: chapter 1
    if pathname in ["/", "/chapter-1"]:
        return chapter1.layout

    elif pathname == "/chapter-2":
        return chapter2.layout

    elif pathname == "/chapter-3":
        return chapter3.layout

    elif pathname == "/chapter-4":
        return chapter4.layout

    elif pathname in ["/chapter-5", "/chapter5"]:
        return chapter5.layout

    elif pathname in ["/chapter-6", "/chapter6"]:
        return chapter6.layout

    elif pathname in ["/chapter-7", "/chapter7"]:   # explicit branch for chapter 7
        return chapter7.layout

    # 404 fallback (plain text is fine here)
    return html.Div("404 – Page not found", style={"padding": "40px"})



# --- register callbacks for each chapter ---
# guard with hasattr so import order or future edits won't crash the app
chapter1.register_callbacks(app)
chapter2.register_callbacks(app)

if hasattr(chapter3, "register_callbacks"):
    chapter3.register_callbacks(app)

if hasattr(chapter4, "register_callbacks"):
    chapter4.register_callbacks(app)

if hasattr(chapter5, "register_callbacks"):
    chapter5.register_callbacks(app)

if hasattr(chapter6, "register_callbacks"):
    chapter6.register_callbacks(app)

if hasattr(chapter7, "register_callbacks"):         # register chapter 7 as well
    chapter7.register_callbacks(app)



# run the dev server
if __name__ == "__main__":
    # NOTE: keep debug=True for hot reload while developing
    app.run(debug=True, port=8050)
