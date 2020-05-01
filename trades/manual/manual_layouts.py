import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import plotly.express as px

from trades.manual import stock_calculations


def make_manual_dashboard(portfolio_list):
    individual_graph, total_graph, roi_graph = make_total_graph_layout("Total", portfolio_list)
    single_graph = make_individual_graph_layout("Individual", portfolio_list)
    controls = make_manual_controls()
    return_toggle = make_return_toggle()
    purchase = make_purchase_layout()

    dashboard_div = html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    individual_graph
                ],
                    style={'background-color': '#f9f9f9',
                           'border-radius': '5px',
                           'margin': '10px',
                           'padding': '15px',
                           'box-shadow': '2px 2px 2px lightgrey'})
            ]),
            dbc.Col([
                html.Div([
                    controls
                ],
                    style={'background-color': '#f9f9f9',
                           'border-radius': '5px',
                           'margin': '10px',
                           'padding': '15px',
                           'box-shadow': '2px 2px 2px lightgrey'}
                )
            ])
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    return_toggle,
                    roi_graph,
                ],
                    style={'background-color': '#f9f9f9',
                           'border-radius': '5px',
                           'margin': '10px',
                           'padding': '15px',
                           'box-shadow': '2px 2px 2px lightgrey'}
                )
            ]),
            dbc.Col([
                html.Div([
                    purchase,
                    single_graph,
                ],
                    style={'background-color': '#f9f9f9',
                           'border-radius': '5px',
                           'margin': '10px',
                           'padding': '15px',
                           'box-shadow': '2px 2px 2px lightgrey'}
                )
            ])
        ]),
    ])
    return dashboard_div


def make_return_toggle():
    return_toggle = html.Div([

        dbc.Row([
            dbc.Col([
                dbc.RadioItems(
                    id='return_radio',
                    options=[
                        {'label': 'Portfolio Value', 'value': 1},
                        {'label': 'Portfolio Return', 'value': 2}
                    ],
                    value=1,
                    inline=True)
            ])
        ]),
        ])
    return return_toggle


def make_individual_graph_layout(brand_name, portfolio_list):

    table_input = dbc.FormGroup([
        dash_table.DataTable(id='portfolio_entries',
                             columns=(
                                 [{'id': 'security', 'name': 'Company'},
                                  {'id': 'value', 'name': 'Value'},
                                  {'id': 'purchase_date', 'name': 'Purchase Date'},
                                  {'id': 'sell_date', 'name': 'Sell Date', 'type': 'datetime'}
                                  ]),
                             row_selectable='single'),
    ])

    graph = px.line()

    graph_div = html.Div([
        dbc.Row([
            dbc.Col([
                html.Div(dbc.Alert(id='sell_alert',
                                   children="Select Individual Securities",
                                   color="warning",
                                   is_open=False,
                                   duration=4000))
            ])
        ]),

        dbc.Row([
            dbc.Col([
                dcc.Graph(id='portfolio_graph',
                          figure=graph)
            ])
        ])

    ])

    return graph_div


def make_total_graph_layout(brand_name, portfolio_list):

    graph = px.line()

    individual_graph = dcc.Graph(id='individual_graph',
                      figure=graph)

    total_graph = dcc.Graph(id='total_graph',
                      figure=graph)

    roi_graph = dcc.Graph(id='roi_graph',
                      figure=graph)

    return individual_graph, total_graph, roi_graph


def make_purchase_layout():

    purchase_alert = dbc.FormGroup([
        dbc.Alert(id = 'purchase_alert',
                  children="No new security has been added",
                  color="warning",
                  is_open=False,
                  duration=4000)
    ])

    securities_list = stock_calculations.get_securities_list()

    security_input = dbc.FormGroup([
        dbc.Label("Company"),
        dcc.Dropdown(
            id='manage_security_input',
            options=securities_list,
            value='CVX',
        ),
    ])

    value_input = dbc.FormGroup([
        dbc.Label("Value (US $)"),
        dbc.Input(id='value_input',
                  type='number',
                  value=100.00,
                  ),
    ])

    purchase_date_input = dbc.FormGroup([
        dbc.Label("Purchase Date"),
        dcc.DatePickerSingle(id = 'purchase_date_input', style={'width': '99%'}),
    ])

    source_input = dbc.FormGroup([
        dbc.Label("Source"),
        dbc.RadioItems(id="source_input",
                       options=[{'label': "Re-invest", 'value':'re-invest'},
                                {'label': 'External funds', 'value': 'add'}],
                       value = 'add'),


    ])

    submit_input = dbc.FormGroup([
        dbc.Button(id='submit_input',
                   children="Purchase",
                   block=True)
    ])

    form_div = html.Div([
        dbc.Form([
            dbc.Row([
                dbc.Col([
                    security_input
                ]),
                dbc.Col([
                    value_input
                ]),
                dbc.Col([
                    purchase_date_input
                ]),
                dbc.Col([
                    source_input
                ]),
                dbc.Col([
                    submit_input
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    purchase_alert
                ])
            ]),
        ])
    ],
        style={'margin-top': '5px'}
    )

    return form_div


def make_manual_controls():
    purchase_div = make_purchase_layout()
    sell_div = make_sell_layout()
    sell_input, sell_date = make_sell_controls()
    return_toggle = make_return_toggle()

    controls = dbc.Form([
        dbc.Row([
            dbc.Col([
                dbc.FormGroup([
                    dbc.Label("Portfolio List with Purchase and Sale Dates", color="success"),
                    sell_div
                ],
                    style={'margin-top': '15px'},
                )
            ]),
            dbc.Col([
                dbc.FormGroup([
                    dbc.Label("Choose the date to sell the selected Stocks", color="success"),
                    dbc.Row([
                        dbc.Col([sell_date]),
                        dbc.Col([sell_input])
                    ])
                ],
                    style={'margin-top': '15px'},
                ),
                # dbc.FormGroup([
                #     dbc.Label("Toggle Between Portfolio Value and Portfolio Returns", color="success"),
                #     return_toggle
                # ]),
            ])
        ]),
        # dbc.Row([
        #     dbc.Col([
        #         dbc.FormGroup([
        #             dbc.Label("Purchase New Stocks from the S&P500", color="success"),
        #             purchase_div
        #         ])
        #     ])
        # ]),
    ])

    return controls


def make_sell_controls():
    sell_input = dbc.FormGroup([
        dbc.Button(id='sell_input', children="Sell", block=True),
    ])

    sell_date = dbc.FormGroup([
        dcc.DatePickerSingle(id='sell_date'),
    ])

    return sell_input, sell_date


def make_sell_layout():

    sell_alert = dbc.Alert(id='sell_alert',
                           children="Sell or Delete Stocks from the Selected Portfolio",
                           color='warning',
                           is_open=False,
                           duration=4000)

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

    data_div = html.Div([
        dbc.Row([
            dbc.Col([
                table_input,
            ],
            style={'margin-left': '15px', 'margin-right': '15px'}),
        ]),
        dbc.Row([
            dbc.Col([
                sell_alert
            ]),
        ]),
    ],
        style={'margin-top': '5px', 'width': '100%', 'margin-right': '15px'})

    return data_div


def make_navbar_view():
    navbar_div = html.Div([
        dbc.Row([
            dbc.Col([
                dbc.NavbarSimple(
                    id='stock_navbar',
                    children=[
                        dcc.Dropdown(
                            id='portfolio_input',
                            placeholder="Select Portfolio",
                            style={'min-width': '200px'})
                    ],
                    color="primary",
                    dark=True)
            ],
                width=12)
        ]),
    ])
    return navbar_div
