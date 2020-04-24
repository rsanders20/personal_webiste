import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import plotly.express as px

from trades.manual import stock_calculations


def make_manual_dashboard(portfolio_list):
    purchase_div = make_purchase_layout("Purchase", portfolio_list)
    sell_div = make_sell_layout("Sell", portfolio_list)
    individual_graph, total_graph, roi_graph = make_total_graph_layout("Total", portfolio_list)
    single_graph = make_individual_graph_layout("Individual", portfolio_list)

    dashboard_div = html.Div([
        dbc.Row([
            dbc.Col([
                individual_graph
            ]),
            dbc.Col([
                purchase_div,
                sell_div,
            ])
        ]),
        dbc.Row([
            dbc.Col([
                roi_graph
            ]),
            dbc.Col([
                single_graph,
            ])
        ]),
    ])
    return dashboard_div


def make_nav():
    nav_portfolio = dbc.Nav(
        [
            dbc.NavItem(dbc.NavLink("Purchase Securities", active=True, href='/purchase/',
                                    style={'margin-top': '5px', 'text-align': 'left'})),
            dbc.NavItem(dbc.NavLink("Sell Securities", active=True, href='/sell/',
                                    style={'margin-top': '5px', 'text-align': 'left'})),
            dbc.NavItem(dbc.NavLink(children="Visualize", id = 'collapse_button', active=True,
                                    style={'margin-top': '5px', 'text-align': 'left'})),
            dbc.Collapse(
                id='collapse',
                is_open=True,
                children=[
                    dbc.NavItem(dbc.NavLink("Individual", active=True, href='/visualize_individual/',
                                            style={'margin-top': '5px', 'margin-left': '15px', 'text-align': 'left'})),
                    dbc.NavItem(dbc.NavLink("Total", active=True, href='/visualize_total/',
                                            style={'margin-top': '5px', 'margin-left': '15px', 'text-align': 'left'}))
                ]
            )
        ],
        pills=True,
    )

    return nav_portfolio


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


def make_purchase_layout(brand_name, portfolio_list):

    manage_alert = dbc.FormGroup([
        dbc.Alert(id = 'manage_alert',
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
            ]),
            dbc.Row([
                dbc.Col([
                    submit_input
                ])
            ]),
        ])
    ],
        style={'margin-top': '5px'}
    )

    return form_div


def make_sell_layout(brand_name, portfolio_list):

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

    sell_input = dbc.FormGroup([
        dbc.Button(id='sell_input', children="Sell", block=True),
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
                table_input,
            ]),
            dbc.Col([
                sell_date
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                sell_input
            ]),
        ]),
    ],
        style={'margin-top': '5px', 'width': '100%', 'margin-right': '15px'})

    return data_div



    # # TODO:  Add this view to the purchase layout, allow many rules to be created
    # # Show the rules in tables backed by db
    # # Create a button to generate the individual buying and selling
    # auto_dates_input = dbc.FormGroup([
    #     dbc.Label("Dates"),
    #     dcc.DatePickerRange(id='auto_dates_input', style={'width': '99%'}),
    #     dbc.FormText("Select the start and end dates for the automatic portfolio"),
    # ],
    # style={'margin-bottom': '30px'})
    #
    # auto_purchase_rule = dbc.FormGroup([
    #     dbc.Label("Set the Value and Frequency of each purchase"),
    #     dbc.Row([
    #         dbc.Col([
    #             dcc.Dropdown(id='auto_purchase_target',
    #                          options=[{'label': i, 'value': i} for i in ['Target Rule', 'Individual', 'ETF']],
    #                          placeholder='Purchase Target')
    #         ],
    #         width=4),
    #         dbc.Col([
    #             dcc.Dropdown(id='auto_purchase_frequency',
    #                          options=[{'label': i, 'value': i} for i in [1, 5, 7, 20, 50, 100, 365]],
    #                          placeholder='Purchase Frequency (days)')
    #         ],
    #         width=4),
    #         dbc.Col([
    #             dcc.Dropdown(id='auto_purchase_value',
    #                          options=[{'label': i, 'value': i} for i in [100, 200, 300, 400, 500, 1000]],
    #                          placeholder='Purchase Value ($)')
    #         ],
    #         width=4),
    #     ]),
    #     dbc.FormText("Select the logic for making purchases"),
    # ],
    #     style={'margin-bottom': '30px'}
    # )
    #
    # auto_select_rule = dbc.FormGroup([
    #     dbc.Label("Select Which Stock or ETF to Purchase"),
    #     dbc.Row([
    #         dbc.Col([
    #             dcc.Dropdown(id='auto_select_type',
    #                          options=[{'label': i, 'value': i} for i in
    #                                   ['Best', 'Worst', 'Moving Average Up-Crossing', 'Moving Average Down-Crossing']],
    #                          placeholder='Performance Criteria')
    #         ],
    #         width=6),
    #         dbc.Col([
    #             dcc.Dropdown(id='auto_select_frequency',
    #                          options=[{'label': i, 'value': i} for i in [1, 5, 7, 20, 50, 100, 365]],
    #                          placeholder='Performance Duration in Days'),
    #         ],
    #         width=6),
    #     ]),
    #     dbc.FormText("Create the logic for selecting the targets of the purchases and sales"),
    # ],
    #     style={'margin-bottom': '30px'}
    # )
    #
    # auto_sell_rule = dbc.FormGroup([
    #     dbc.Label("Select Which Stock or ETF to Sell"),
    #     dbc.Row([
    #         dbc.Col([
    #             dcc.Dropdown(id='auto_sell_type',
    #                          options=[{'label': i, 'value': i} for i in
    #                                   ['Best', 'Worst', 'Moving Average Up-Crossing', 'Moving Average Down-Crossing']],
    #                          placeholder='Performance Criteria')
    #         ],
    #         width=6),
    #         dbc.Col([
    #             dcc.Dropdown(id='auto_sell_frequency',
    #                          options=[{'label': i, 'value': i} for i in [1, 5, 7, 20, 50, 100, 365]],
    #                          placeholder='Performance Duration in Days'),
    #         ],
    #         width=6),
    #     ]),
    #     dbc.FormText("Create the logic for deciding when to sell a previous purchase"),
    # ],
    #     style={'margin-bottom': '30px'}
    # )



    # Automatic Cash Inflow: Lump Sum, Dollar Cost Averaging
    #        Shadow Manual Portfolio:  Manual/Automatic
    # Cash Input: Weekly Amount, Starting Amount, or Manual Factor
    # Start Date
    # End Date
    # Automatic Purchase Target: SPY, Single Stock
    # Trading Style: Buy and Hold, Buy after Event, Sell after Event
    # Event Frequency: Daily, Weekly, Monthly

    # Add Automatic Rules Table:
    # start date, end date

    # Add Target Rule:
    # Type (Best, Worst, Up-Crossing, Down-Crossing) over last (5-day, 20-day 50-day, 1-year) compared to (all)

    # Add Purchase Rule:
    # Weekly Investment, Target (Name, or Rule)

    # Add Sell Rule
    # Percentage, Target

    # Save and Purchase all Securities


def get_base_layout(brand_name, nav_div, content_div, portfolio_list):

    view_portfolio_div = html.Div([
        dbc.Row([
            dbc.Col([
                nav_div,
            ],
                width=3),
            dbc.Col([
                content_div
            ],
                style={'display': 'flex', 'justify-content': 'center'},
                width=9),
        ]),
    ])

    return view_portfolio_div


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




