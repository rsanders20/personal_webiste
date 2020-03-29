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
            dbc.NavItem(dbc.NavLink("Purchase Securities", active=True, href='/purchase/',
                                    style={'margin-top': '5px'})),
            dbc.NavItem(dbc.NavLink("Sell Securities", active=True, href='/sell/',
                                    style={'margin-top': '5px'})),
            dbc.NavItem(dbc.NavLink("Visualize Portfolio", active=True, href='/visualize/',
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

    security_input = dbc.FormGroup([
        dbc.Label("Company"),
        dcc.Dropdown(
            id='security_input',
            options=[],
            multi=True,
        ),
        dbc.FormText("Select the security to graph"),
    ])

    table_input = dbc.FormGroup([
        dash_table.DataTable(id='portfolio_entries',
                             columns=(
                                 [{'id': 'security', 'name': 'Company'},
                                  {'id': 'value', 'name': 'Value'},
                                  {'id': 'purchase_date', 'name': 'Purchase Date'},
                                  {'id': 'sell_date', 'name': 'Sell Date', 'type': 'datetime'}
                                  ]),
                             row_selectable='multi'),
        dbc.FormText("Select the Security to Sell, or Delete"),
    ])

    graph = px.line()

    graph_div = html.Div([
        dbc.Row([
            dbc.Col([
                html.Div(dbc.Alert(id='sell_alert'), style={'display': 'none'})
            ])
        ]),
        dbc.Row([
            dbc.Col([
                portfolio_input,
            ])
        ]),
        dbc.Row([
            dbc.Col([
                table_input,
            ],
                style={'margin-left': '15px', 'margin-right': '15px'},
            ),
        ]),
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
            id='manage_security_input',
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

    source_input = dbc.FormGroup([
        dbc.Label("Source"),
        dbc.RadioItems(id="source_input",
                       options=[{'label': "Re-invest existing cash", 'value':'re-invest'},
                                {'label': 'Use all money from outside the portfolio', 'value': 'add'}],
                       value = 'add'),
        dbc.FormText("Choose if the invested money will use existing cash first or not")


    ])

    submit_input = dbc.FormGroup([
        dbc.Button(id='submit_input',
                   children="Add to Portfolio")
    ])

    form_div = html.Div([
        dbc.Form([manage_alert, portfolio_input, security_input, value_input,
                  purchase_date_input, source_input, submit_input])
    ],
        style={'width': '100%', 'margin-top': '5px'}
    )

    manage_div = get_base_layout(brand_name, nav_portfolio, form_div)

    return manage_div


def make_sell_layout(brand_name, portfolio_list):

    nav_portfolio = make_nav()

    sell_alert = dbc.Alert(id='sell_alert',
                           children="Sell or Delete Stocks from the Selected Portfolio",
                           color='success')

    portfolio_input = dbc.FormGroup([
        dbc.Label("Portfolio"),
        dcc.Dropdown(
            id='portfolio_input',
            options=[{'label': i.name, 'value': i.name} for i in portfolio_list],
        ),
        dbc.FormText("Select the portfolio to manage"),
    ])

    table_input = dbc.FormGroup([
        dash_table.DataTable(id='portfolio_entries',
                             columns=(
                                 [{'id': 'portfolio', 'name': 'Portfolio'},
                                  {'id': 'security', 'name': 'Company'},
                                  {'id': 'value', 'name': 'Value'},
                                  {'id': 'purchase_date', 'name': 'Purchase Date'},
                                  {'id': 'sell_date', 'name': 'Sell Date', 'type': 'datetime'}
                                  ]),
                             row_selectable='single'),
        dbc.FormText("Select the Secruity to Sell, or Delete"),
    ])

    sell_input = dbc.FormGroup([
        html.Button(id='sell_input', children="Sell"),
        dbc.FormText("Sell Selected")
    ])

    sell_date = dbc.FormGroup([
        dcc.DatePickerSingle(id='sell_date'),
        dbc.FormText("Select the date of the sale")
    ])


    data_div = html.Div([
        dbc.Row([
            dbc.Col([
                sell_alert,
            ])
        ]),
        dbc.Row([
            dbc.Col([
                portfolio_input,
            ])
        ]),
        dbc.Row([
            dbc.Col([
                table_input,
            ],
                style={'margin-left': '15px', 'margin-right': '15px'},
            )
        ]),
        dbc.Row([
            dbc.Col([
                sell_date
            ]),
            dbc.Col([
                sell_input
            ]),
        ]),
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



