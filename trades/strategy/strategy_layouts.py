import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import datetime

import pandas as pd

import plotly.express as px

from trades.portfolio import stock_calculations


def make_automatic_dashboard():
    historic_roi = make_historic_roi_graph()
    weekly_roi = make_weekly_graph()
    spy_graph = make_spy_graph()
    dashboard_controls = make_dashboard_controls()

    weekly_progress = make_weekly_progress()
    weekly_toggle = make_weekly_toggle()
    historic_button = make_historic_button()

    dashboard_div = html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4(children="Buy/Sell Signals",
                            style={'text-align': 'center'}),
                    dashboard_controls,
                    dbc.Alert(id='ticker_alert',
                              children="No Ticker Data Found on Yahoo Finance",
                              color="warning",
                              is_open=False,
                              duration=4000,
                              style={"position": "fixed", "top": 0})
                ],
                    className='pretty_container')
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4(children='Daily Closing Value',
                            style={'text-align': 'center'}),
                    weekly_progress,
                    spy_graph

                ],
                    className='pretty_container')
            ],
                width=6
            ),
            dbc.Col([
                html.Div([
                    html.H4(children="Total Portfolio Value or Return",
                            style={'text-align': 'center',
                                   'margin-bottom': '20px'}),
                    weekly_toggle,
                    weekly_roi
                ],
                    className='pretty_container')
            ],
            width=6)
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4(children="Returns Over 1 Yr. of Investment",
                            style={'text-align': 'center'}),
                    historic_button,
                    historic_roi
                ],
                className='pretty_container')
            ]),
        ]),
    ])
    return dashboard_div
    # return html.Div(children="Hello!")


def make_historic_roi_graph():

    historic_roi = dcc.Loading(
        type='circle',
        fullscreen=True,
        children = [html.Div([dcc.Graph(id='historic_roi')])
        ]
    )

    return historic_roi


def make_spy_graph():
    spy_graph = html.Div([
        dcc.Graph(id = 'spy_graph')
    ])

    return spy_graph


def make_dashboard_controls():
    signal_div = make_signal_table()
    securities_list = stock_calculations.get_securities_list()

    buy_threshold = dbc.FormGroup([
        dbc.Label("Buy Threshold"),
        dbc.Input(id="buy_threshold",
                  type='number',
                  value=-0.5),
        dbc.FormText("Buy if the weighted sum is greater than this threshold")

    ])
    sell_threshold = dbc.FormGroup([
        dbc.Label("Sell Threshold"),
        dbc.Input(id="sell_threshold",
                  type='number',
                  value=-2.5),
        dbc.FormText("Sell if the weighted sum is less than this threshold")

    ])
    security_input = dbc.FormGroup([
        dbc.Label("Stock Ticker"),
        dbc.Input(
            id='ticker_input',
            type='text',
            value='SPY',
        ),
        dcc.Dropdown(
            id='ticker_sp500_input',
            options=securities_list,
            value='CVX',
            style={'display': 'none'}
        ),
    ])

    security_radio = dbc.FormGroup([
        dbc.Label("SP500/Custom"),
        dbc.RadioItems(
            id='ticker_input_radio',
            options=[
                {'label': 'SP500', 'value': 'SP500'},
                {'label': 'Custom', 'value': 'Custom'}
            ],
            value='Custom',
        ),
        dbc.FormText("Choose from SP500 or Custom")
    ])

    run_analysis = dbc.FormGroup([
        dbc.Label("Run"),
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        id='run_analysis',
                        children='Run',
                        block=True,
                    )
                ]),
            ]),
        dbc.FormText("Run the analysis")
    ])

    #TODO:  Remove the loading, and add update to status on the alert
    controls_form = dbc.FormGroup([
            dbc.Label("Weighted Signals"),
            dcc.Loading(id='loading_signal',
                        children=[signal_div],
                        type='default'),
            dbc.FormText("Create weighted signals that determine when to buy or sell. "
                         " Select When (how many days ago) what (open, close, or a moving average) "
                         "and how important (weight) each event is.")
        ],
        style={'margin-top': '15px'})

    form_div = html.Div([
        dbc.Form([
            dbc.Row([
                dbc.Col([
                    controls_form
                ])
            ]),
            dbc.Row([
                dbc.Col([
                   security_radio
                ]),
                dbc.Col([
                    security_input
                ]),
                dbc.Col([
                    buy_threshold
                ]),
                dbc.Col([
                    sell_threshold
                ]),
                dbc.Col([
                    run_analysis
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        id='editing-rows-button',
                        children='Add row',
                        block=True,
                    )
                ]),
                dbc.Col([
                    dbc.Button(
                        id='opt_button',
                        children='Optimize Percentages',
                        block=True
                    )
                ]),
                dbc.Col([
                    dbc.Button(id='save_button',
                               children='Save Signals to Database',
                               block=True)
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Alert(
                        id='save_alert',
                        duration=4000,
                        is_open=False,
                        children="",
                        color='warning',
                        style={"position": "fixed", "top": 0}),
                    dbc.Alert(
                        id='row_alert',
                        duration=1000,
                        is_open=False,
                        children="",
                        color='success',
                        style={"position": "fixed", "top": 0}),
                    dbc.Alert(
                        id='opt_alert',
                        duration=4000,
                        is_open=False,
                        children="",
                        color='success',
                        style = {"position": "fixed", "top": 0}),
                ]),
            ])
        ])
    ])

    return form_div


def make_weekly_toggle():
    weekly_toggle = html.Div([

        dbc.Row([
            dbc.Col([
                dbc.RadioItems(
                    id='weekly_roi_radio',
                    options=[
                        {'label': 'Portfolio Value', 'value': 1},
                        {'label': 'Portfolio Return', 'value': 2}
                    ],
                    value=1,
                    inline=True,
                    style={'text-align': 'center', 'margin-bottom': '30px'})
            ])
        ]),
        ])
    return weekly_toggle


def make_weekly_graph():
    weekly_roi = html.Div([
        dbc.Row([
            dbc.Col([dcc.Graph(id='weekly_roi_graph')]),
        ]),
    ])

    return weekly_roi


def make_weekly_progress():
    progress_alert = dbc.Alert(id='progress_alert',
                           is_open=False,
                           duration=4000,
                           style={"position": "fixed", "top": 0})

    now_time = datetime.datetime.now()
    start_time = now_time-datetime.timedelta(days=365)
    date_range = dbc.FormGroup([dcc.DatePickerRange(id='date_range',
                                                    start_date = start_time,
                                                    end_date = now_time)])

    data_div = html.Div([
        dbc.Row([
            dbc.Col([
                date_range,
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                progress_alert
            ]),
        ]),
    ],
        style={'margin-top': '5px', 'width': '100%', 'margin-right': '15px', 'text-align': 'center'})

    return data_div


def make_signal_table():
    signal_div = html.Div([
        dash_table.DataTable(
            id='signal_table',
            # data=rules_list,
            columns=[
                {'id': 'Larger: When?', 'name': 'Larger: When?', 'editable':True, 'type': 'numeric'},
                {'id': 'Larger: What?', 'name': 'Larger: What?', 'presentation': 'dropdown', 'editable':True, },
                {'id': 'Smaller: When?', 'name': 'Smaller: When?', 'editable':True, 'type': 'numeric'},
                {'id': 'Smaller: What?', 'name': 'Smaller: What?', 'presentation': 'dropdown', 'editable':True},
                {'id': 'Percentage', 'name': 'Percentage', 'editable':True, 'type': 'numeric'},
                {'id': 'Weight', 'name': 'Weight', 'editable':True, 'type': 'numeric', 'editable': True},
            ],

            editable=True,
            row_deletable=True,
            # row_selectable='multi',
            # selected_rows = [],
            # selected_rows = [i for i in range(len(rules_list))],
            dropdown={
                'Larger: What?': {
                    'options': [
                        {'label': i, 'value': i}
                        for i in ['Open', 'Close', '200', '50']
                    ]
                },
                'Smaller: What?': {
                    'options': [
                        {'label': i, 'value': i}
                        for i in ['Open', 'Close', '200', '50']
                    ]
                }
            }
        )
    ])

    return signal_div


def make_historic_button():
    now_time = datetime.datetime.now()
    start_time = now_time-datetime.timedelta(days=2*365)

    historic_input = dbc.FormGroup([
        dbc.Row([
            dbc.Col([
                dcc.DatePickerRange(id='historic_date',
                                    start_date=start_time,
                                    end_date=now_time)
            ]),
            dbc.Col([
               dbc.Alert(id='historic_alert',
                         children='Strategy Score:  ',
                         color='primary')
            ]),
            dbc.Col([
                dbc.Button(id='historic_input',
                           children='Run Statistical Comparison',
                           block=True)
            ]),
        ])

    ])

    return historic_input


def get_rules():
    rules_list = [
        '1 Wk. Positive Returns',
        '2 Wks. Positive Returns',
        '3 Wks. Positive Returns',
        '4 Wks. Positive Returns',
        '1 Wk. Negative Returns',
        '2 Wks. Negative Returns',
        '3 Wks. Negative Returns',
        '4 Wks. Negative Returns',

        'Above 200 Day Avg.',
        'Below 200 Day Avg.',
        'Above 50 Day Avg.',
        'Below 50 Day Avg.'
    ]

    return rules_list


def make_auto_navbar():
    navbar_div = dbc.Navbar(
        [
                dbc.Col([
                    dbc.NavbarBrand("Strategy", className="ml-2")
                ],
                    width=2),
                dbc.Col([
                    dbc.RadioItems(
                        id='new_strategy_type',
                        options=[
                            {'label': 'Empty', 'value': 'Empty'},
                            {'label': 'Copy', 'value': 'Copy'},
                            {'label': 'Default', 'value': 'Default'}
                        ],
                        value='Default',
                        style={'color': 'white'},
                    ),
                ]),
                dbc.Col([
                    dcc.Dropdown(
                        id='strategy_name',
                        placeholder='Select Existing Strategy'
                    ),
                ],
                    width=2),
                dbc.Col([
                    dbc.Input(
                        id='new_strategy_name',
                        placeholder='New Strategy Name',
                    ),
                ],
                    width=2),
                dbc.Col([
                    dbc.Button(
                        id='new_strategy_button',
                        children='Make New Strategy',
                        block=True
                    )
                ],
                    width=2),
            dbc.Col([
                dbc.Button(
                    id='delete_strategy_button',
                    children='Delete Strategy',
                    block=True
                )
            ],
                width=2),
        ],
        id='stock_navbar',
        color="primary",
        dark=True,
    )
    navbar = dbc.Row([
        dbc.Col([
            navbar_div,
            dbc.Alert(
                id='new_strategy_alert',
                duration=4000,
                is_open=False,
                children="No Portfolio Created",
                color="warning",
                style={"position": "fixed", "top": 0}
        ),
            dbc.Alert(
                id='delete_strategy_alert',
                duration=4000,
                is_open=False,
                children="No Portfolio Deleted",
                color="warning",
                style={"position": "fixed", "top": 0}
        )
        ])
    ])

    return navbar




