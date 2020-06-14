from dash import dash
from flask import session
from trades import db
from trades.models import User, Trade, Portfolio, Dollar

import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input, State


from trades.portfolio import manual_layouts


def get_dashboard_layout(content_div):

    view_portfolio_div = html.Div([
        dbc.Row([
            dbc.Col([
                content_div
            ],
                style={'display': 'flex', 'justify-content': 'center'})
        ])
    ])

    return view_portfolio_div


def make_about_layout():
    jumbotron = dbc.Jumbotron(
        [
            html.H1("Algo-rhythm", className="display-8"),
            html.P(
                "Its all about timing!",
                className="lead",
            ),
            html.Hr(className="my-2"),
            html.P("Step 1:  Start by creating a New Portfolio"),
            html.Hr(className="my-2"),
            html.P("Step 2:  Predict when to buy and sell by developing strategies"),
            html.Hr(className="my-2"),
            html.P("Step 3:  Profit!"),
            html.Hr(className="my-2"),
        ]
    )

    about_layout = html.Div([
        dbc.Row([
            dbc.Col([
                jumbotron
            ])
        ])
    ])

    return about_layout


def register_home_dashapp(server):
    external_stylesheets = [dbc.themes.FLATLY]

    app = dash.Dash(__name__,
                    server=server,
                    url_base_pathname='/dash/home/',
                    external_stylesheets=external_stylesheets)

    app.layout = html.Div([
        make_about_layout()
        ])

