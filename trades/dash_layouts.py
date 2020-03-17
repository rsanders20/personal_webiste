from datetime import datetime

import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import plotly.express as px

from . import stock_calculations


def make_nav():
    nav_portfolio = dbc.Nav(
        [
            dbc.NavItem(dbc.NavLink("Create Portfolio", active=True, href='/create/',
                                    style={'margin-top': '5px'})),
            dbc.NavItem(dbc.NavLink("Manage Portfolio", active=True, href='/manage/',
                                    style={'margin-top': '5px'})),
            dbc.NavItem(dbc.NavLink("List Portfolio", active=True, href='/list/',
                                    style={'margin-top': '5px'})),
            dbc.NavItem(dbc.NavLink("Graph Portfolio", active=True, href='/graph/',
                                    style={'margin-top': '5px'}))
        ],
        vertical='md',
        pills=True,
        justified=True
    )

    return nav_portfolio


def make_graph_layout(brand_name, portfolio_list):
    nav_portfolio = make_nav()

    portfolio_input = dbc.FormGroup([
        dbc.Label("Portfolio"),
        dcc.Dropdown(
            id='portfolio_input',
            options=[{'label': i.name, 'value': i.name} for i in portfolio_list],
        ),
        dbc.FormText("Select the portfolio to graph"),
    ])

    # security_options = []
    # for stock in data:
    #     stock_string = stock['security'] + ", " + stock['purchase_date'] + ", " + str(stock["value"])
    #     security_options.append({'label': stock_string, 'value': stock_string})
    graph = px.line()

    graph_div = html.Div([
        dbc.Row([
            dbc.Col([
                portfolio_input,
            ])
        ]),
        # dbc.Row([
        #     dbc.Col([
        #         dcc.Dropdown(
        #             id='security_input',
        #             options=security_options,
        #             multi=True,
        #             value=[security_options[-1]['value']],
        #         ),
        #     ]),
        # ]),
        dbc.Row([

            dbc.Col([
                dcc.Graph(id='portfolio_graph',
                          figure=graph)
            ])
        ])

    ],
        style={'margin-top': '5px', 'width': '100%', 'margin-right': '15px'}
    )

    graph_layout_div = get_base_layout(brand_name, nav_portfolio, graph_div)
    return graph_layout_div


def make_manage_layout(brand_name, portfolio_list):

    nav_portfolio = make_nav()

    manage_alert = dbc.FormGroup([
        dbc.Alert(id = 'manage_alert',
                  children="No new security has been added",
                  color="warning")
    ])

    portfolio_input = dbc.FormGroup([
        dbc.Label("Portfolio"),
        dcc.Dropdown(
            id='portfolio_input',
            options=[{'label': i.name, 'value': i.name} for i in portfolio_list],
        ),
        dbc.FormText("Select the portfolio to manage"),
    ])

    securities_list = stock_calculations.get_securities_list()

    security_input = dbc.FormGroup([
        dbc.Label("Company"),
        dcc.Dropdown(
            id='security_input',
            options=securities_list,
            value='CVX',
        ),
        dbc.FormText("Select the company that you would like to add to your portfolio"),
    ])

    value_input = dbc.FormGroup([
        dbc.Label("Quantity (US $)"),
        dbc.Input(id='value_input',
                  type='number',
                  value=100.00,
                  ),
        dbc.FormText("Select the value of the security being added to your portfolio"),
    ])

    purchase_date_input = dbc.FormGroup([
        dbc.Label("Purchase Date"),
        dcc.DatePickerSingle(id = 'purchase_date_input', style={'width': '99%'}),
        dbc.FormText("Select the value of the security being added to your portfolio"),
    ])

    submit_input = dbc.FormGroup([
        dbc.Button(id='submit_input',
                   children="Add to Portfolio")
    ])

    form_div = html.Div([
        dbc.Form([manage_alert, portfolio_input, security_input, value_input, purchase_date_input, submit_input])
    ],
        style={'width': '100%', 'margin-top': '5px'}
    )

    manage_div = get_base_layout(brand_name, nav_portfolio, form_div)

    return manage_div


def make_list_layout(brand_name, portfolio_list):

    nav_portfolio = make_nav()

    portfolio_input = dbc.FormGroup([
        dbc.Label("Portfolio"),
        dcc.Dropdown(
            id='portfolio_input',
            options=[{'label': i.name, 'value': i.name} for i in portfolio_list],
        ),
        dbc.FormText("Select the portfolio to manage"),
    ])

    display_table = dash_table.DataTable(id='portfolio_entries',
                                         columns=(
                                             [{'id': 'portfolio', 'name': 'Portfolio'},
                                              {'id': 'security', 'name': 'Company'},
                                              {'id': 'value', 'name': 'Value'},
                                              {'id': 'purchase_date', 'name': 'Purchase Date'}
                                              ]),
                                         )

    data_div = html.Div([
        dbc.Row([
            dbc.Col([
                portfolio_input,
            ])
        ]),
        dbc.Row([
            dbc.Col([
                display_table
            ])
        ])

    ],
        style={'margin-top': '5px', 'width': '100%', 'margin-right': '15px'})

    view_div = get_base_layout(brand_name, nav_portfolio, data_div)
    return view_div


def make_create_layout(brand_name):
    nav_portfolio = make_nav()

    create_alert = dbc.FormGroup([
        dbc.Alert(id='create_alert',
                  children="No new portfolio has been added",
                  color="warning")
    ])

    name_input = dbc.FormGroup([
        dbc.Label("Name"),
        dbc.Input(id='name_input',
                  type='text',
                  placeholder = 'Portfolio Name',
                  ),
        dbc.FormText("Name this Portfolio"),
    ])

    strategy_input = dbc.FormGroup([
        dbc.Label("Strategy"),
        dcc.Dropdown(
            id='strategy_input',
            options=[{'label': i, 'value': i} for i in ['Buy Low', 'Sell High']],
        ),
        dbc.FormText("Select a strategy for this portfolio"),
    ])

    create_input = dbc.FormGroup([
        dbc.Button(id='create_input',
                   children="Create Portfolio")
    ])

    form_div = html.Div([
        dbc.Form([create_alert, name_input, strategy_input, create_input])
    ],
        style={'width': '100%', 'margin-top': '5px'}
    )

    manage_div = get_base_layout(brand_name, nav_portfolio, form_div)

    return manage_div


def get_base_layout(brand_name, nav_div, content_div):
    view_portfolio_div = html.Div([
        dbc.Row([
            dbc.Col([
                dbc.NavbarSimple(
                    brand=brand_name,
                    color="primary",
                    dark=True, )
            ],
                width=12)
        ]),
        dbc.Row([
            dbc.Col([
                nav_div,
            ],
                width=4),
            dbc.Col([
                content_div
            ],
                style={'display': 'flex', 'justify-content': 'center'},
                width=8),
        ]),
    ])

    return view_portfolio_div



