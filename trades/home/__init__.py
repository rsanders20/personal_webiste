from dash import dash
from flask import session
from trades import db
from trades.models import User, Trade, Portfolio, Dollar

import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input, State


from trades.manual import manual_layouts


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
            html.H1("Welcome to the stock plotting tool", className="display-8"),
            html.P(
                "Asses investment strategies by creating multiple portfolios and comparing their performance",
                className="lead",
            ),
            html.Hr(className="my-2"),
            html.P("Start by creating a New Portfolio"),
            html.Hr(className="my-2"),
            html.P("Choose the portfolio type.  Manual to make all buying and selling decisions,"
                   " or automatic to assign rules for when to buy and sell"),
            html.Hr(className="my-2"),
            html.P("Manage your portfolio with the \"Purchase\" and \"Sell\" Pages"),
            html.Hr(className="my-2"),
            html.P("View portfolio value and ROI with the \"Visualize\" tab"),
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

    strategy_input = dbc.FormGroup([
        dbc.Label("Strategy"),
        dcc.Dropdown(
            id='strategy_input',
            options=[{'label': i, 'value': i} for i in ['Manual', 'Automatic']],
        ),
        dbc.FormText("Manual or Automatic"),

    ])

    create_input = dbc.FormGroup([
        dbc.Label("Create"),
        dbc.Button(id='create_input',
                   children="Create Portfolio",
                   block=True),
        dbc.FormText("Make a New Portfolio")
    ])

    form_div = html.Div([
        dbc.Form([
            dbc.Row([
                dbc.Col([
                    name_input
                ]),
                dbc.Col([
                    strategy_input
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
    ],
        style={'width': '100%', 'margin-top': '5px'}
    )

    about_layout_content = html.Div([
        dbc.Row([
            dbc.Col([jumbotron,
                    form_div,
            ])
        ])
    ])

    about_layout_div = get_dashboard_layout(about_layout_content)

    return about_layout_div


def register_home_dashapp(server):
    external_stylesheets = [dbc.themes.FLATLY]

    app = dash.Dash(__name__,
                    server=server,
                    url_base_pathname='/dash/home/',
                    external_stylesheets=external_stylesheets)

    app.layout = make_about_layout()

    @app.callback([Output('create_alert', 'children'),
                   Output('create_alert', 'color'),
                   Output('create_alert', 'is_open')],
                  [Input('create_input', 'n_clicks')],
                  [State('name_input', 'value'),
                   State('strategy_input', 'value')])
    def create_portfolio(_, name, strategy):
        if not _:
            return "", "danger", False

        if not name or not strategy:
            return "All fields must be filled in", "danger", True

        user_name = session.get('user_name', None)
        user = User.query.filter_by(user_name=user_name).one_or_none()
        is_portfolio = Portfolio.query.filter_by(user_id= user.id, name=name).one_or_none()
        if is_portfolio:
            return "Please select a new Portfolio Name.  This one already exists.", "danger", True

        portfolio = Portfolio(
            user_id=user.id,
            name=name,
            strategy = strategy)
        db.session.add(portfolio)
        db.session.commit()
        return "Portfolio Created!", "success", True

