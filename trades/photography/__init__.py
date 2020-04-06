from dash import dash

import dash_html_components as html
import dash_bootstrap_components as dbc

from trades import protect_dash_route


def register_photography_dashapp(server):
    external_stylesheets = [dbc.themes.LUX]
    app = dash.Dash(__name__,
                    server=server,
                    url_base_pathname='/dash/photography/',
                    external_stylesheets=external_stylesheets,
                    suppress_callback_exceptions=True)

    protect_dash_route(app)

    app.layout = html.Div([
        dbc.Alert(children="This Page is Coming Soon", color="danger")
    ])
