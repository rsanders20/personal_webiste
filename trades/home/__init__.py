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
            html.H1("Algo-Rhythm", className="display-8"),
            html.P(
                "Its all about timing!",
                className="lead",
            ),
            html.Hr(className="my-2"),
            html.P("Start by creating a New Portfolio"),
            html.Hr(className="my-2"),
            html.P("Predict when to buy and sell by developing a strategy for each trade"),
            html.Hr(className="my-2"),
            html.P("Compare the strategic decisions to the base portfolio to refine decision making"),
            html.Hr(className="my-2"),
        ]
    )

    create_alert = dbc.FormGroup([
        dbc.Alert(id='create_alert',
                  is_open=False,
                  duration=4000
                  )
    ])

    name_input = dbc.FormGroup([
        dbc.Label("Name"),
        dbc.Input(id='name_input',
                  type='text',
                  placeholder='Portfolio Name',
                  ),
        dbc.FormText("Name this Portfolio"),
    ])

    create_input = dbc.FormGroup([
        dbc.Label("Create"),
        dbc.Button(id='create_input',
                   children="Create Portfolio",
                   block=True),
        dbc.FormText("Make a New Portfolio")
    ])

    about_layout = html.Div([
        dbc.Row([
            dbc.Col([
                jumbotron
            ])
        ]),
        dbc.Row([
            dbc.Col([
                name_input
            ]),
            dbc.Col([
                create_input
            ])
        ]),
        dbc.Row([
            dbc.Col([
                create_alert
            ])
        ])
    ])

    # about_layout_div = get_dashboard_layout(about_layout_content)

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

    @app.callback([Output('create_alert', 'children'),
                   Output('create_alert', 'color'),
                   Output('create_alert', 'is_open')],
                  [Input('create_input', 'n_clicks')],
                  [State('name_input', 'value')])
    def create_portfolio(_, name):
        if not _:
            return "", "danger", False

        user_name = session.get('user_name', None)
        user = User.query.filter_by(user_name=user_name).one_or_none()
        is_portfolio = Portfolio.query.filter_by(user_id= user.id, name=name).one_or_none()
        if is_portfolio:
            return "Please select a new Portfolio Name.  This one already exists.", "danger", True

        portfolio = Portfolio(
            user_id=user.id,
            name=name)
        db.session.add(portfolio)
        db.session.commit()
        return "Portfolio Created!", "success", True

