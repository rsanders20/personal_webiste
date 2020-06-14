import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import datetime

import pandas as pd

import plotly.express as px

from trades.portfolio import stock_calculations


def make_automatic_dashboard():
    weekly_roi = make_weekly_graph()
    spy_graph = make_spy_graph()
    dashboard_controls = make_dashboard_controls()
    optimize_controls = make_optimize_controls()
    new_strategy = make_new_strategy()

    weekly_progress = make_weekly_progress()
    weekly_toggle = make_weekly_toggle()
    historic_button = make_historic_button()

    now_time = datetime.datetime.now()
    start_time = now_time-datetime.timedelta(days=20*365)

    dashboard_div = html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4(children="New Stragety",
                            style={'text-align': 'center'}),
                    new_strategy,
                ],
                    className='pretty_container')
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4(children="Optimize Percentages",
                            style={'text-align': 'center'}),
                    optimize_controls,
                ],
                    className='pretty_container')
            ]),
        ]),
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
                    dbc.Tabs([
                        dbc.Tab(label='Decisions', tab_id='tab-1'),
                        dbc.Tab(label='Performance', tab_id='tab-2'),
                        dbc.Tab(label='Returns', tab_id='tab-3'),
                        dbc.Tab(label='Historic', tab_id='tab-4')

                    ],
                        id='tabs',
                        active_tab='tab-1'),
                    dcc.Graph(id='daily-graph'),
                ],
                    className='pretty_container'

                ),
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                weekly_progress
            ])
        ]),
        dbc.Row([
            dbc.Col([
                historic_button
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.FormGroup([
                    dcc.DatePickerRange(id='historic_date',
                                        start_date=start_time,
                                        end_date=now_time)
                ], style={'text-align': 'center'})

            ]),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div(id='hidden-data', style={'display': None})
            ])
        ])
    ])
    return dashboard_div
    # return html.Div(children="Hello!")


def make_historic_roi_graph():

    historic_roi = dcc.Loading(
        type='circle',
        fullscreen=True,
        children = [html.Div(
            [dcc.Graph(id='historic_roi'),
             dbc.FormText("Click on a point to view the buy/sell decisions on the upper graph")]
        )
        ]
    )

    return historic_roi


def make_spy_graph():
    spy_graph = html.Div([
        dcc.Graph(id = 'spy_graph')
    ])

    return spy_graph


def make_optimize_controls():

    optimize_type = dbc.FormGroup([
        dbc.Label("Realizations/ROI"),
        dbc.RadioItems(
            id='optimize-type-radio',
            options=[
                {'label': 'Realizations', 'value': 'Realizations'},
                {'label': 'ROI', 'value': 'ROI'}
            ],
            value='ROI',
        ),
        dbc.FormText("Choose to optimize for total return (ROI) or number of times the strategy has worked (Realizations)")
    ])

    optimize_time = dbc.FormGroup([
        dbc.Label("Optimize Dates"),
        dcc.DatePickerRange(id='optimize-dates',
                            start_date = datetime.datetime.now()-datetime.timedelta(days=365*1),
                            end_date = datetime.datetime.now(),
                            style={'display': 'block'}),
        dbc.FormText(
            "Choose the time over which to optimize")
    ])

    optimize_button = dbc.FormGroup([
        dbc.Label("Optimize Percentages"),
        dbc.Button(
            id='opt_button',
            children="Optimize",
            block=True),
        dbc.FormText("Optimization can take >1 Min.")
    ])

    optimize_controls = html.Div([
        dbc.Row([
            dbc.Col([
                optimize_type
            ],width=4),
            dbc.Col([
                optimize_time
            ], width=4),
            dbc.Col([
                optimize_button
            ], width=4),
        ]),
    ])

    return optimize_controls


def make_dashboard_controls():
    signal_div = make_signal_table()
    securities_list = stock_calculations.get_securities_list()

    buy_threshold = dbc.FormGroup([
        dbc.Label("Buy Threshold"),
        dbc.Input(id="buy_threshold",
                  type='number'),
        dbc.FormText("Buy if the weighted sum is greater than this threshold")

    ])
    sell_threshold = dbc.FormGroup([
        dbc.Label("Sell Threshold"),
        dbc.Input(id="sell_threshold",
                  type='number'),
        dbc.FormText("Sell if the weighted sum is less than this threshold")

    ])
    security_input = dbc.FormGroup([
        dbc.Label("Stock Ticker"),
        dbc.Input(
            id='ticker_input',
            type='text',
        ),
        dcc.Dropdown(
            id='ticker_sp500_input',
            options=securities_list,
            style={'display': 'none'}
        ),
    ])

    security_radio = dbc.FormGroup([
        dbc.Label("SP500/Custom"),
        dcc.Loading([
            dbc.RadioItems(
                id='ticker_input_radio',
                options=[
                    {'label': 'SP500', 'value': 'SP500'},
                    {'label': 'Custom', 'value': 'Custom'}
                ],
                value='Custom',
            ),
        ]),
        dbc.FormText("Choose from SP500 or Custom")
    ])

    controls_form = dbc.FormGroup([
            signal_div,
            dbc.FormText("Create weighted signals that determine when to buy or sell. "
                         " Select When (how many days ago) what (open, close, or a moving average) "
                         "and how important (weight) each event is.")
        ],
        style={'margin-top': '15px'})

    form_div = html.Div([
        dbc.Form([
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
            ]),
            dbc.Row([
                dbc.Col([
                    controls_form
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
                    dbc.Button(id='save_button',
                               children='Save Signals',
                               block=True)
                ]),
                dbc.Col([
                    dbc.Button(
                        id='run_analysis',
                        children='Run',
                        block=True,
                    )
                ]),
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
    historic_roi = make_historic_roi_graph()

    historic_div = html.Div([
        html.H4(children="Returns Over 1 Yr. of Investment",
                style={'text-align': 'center'}),
        dbc.Row([
            dbc.Col([
                dbc.Alert(id='historic_alert',
                          children='Strategy Score:  ',
                          color='primary')
            ]),
            dbc.Col([
                dbc.Button(id='historic_input',
                           children='Run Statistical Comparison',
                           block=True,
                           style={'min-height': '45px'}),
            ]),
        ]),
        historic_roi,

    ],
        className='pretty_container')

    return historic_div


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


def make_new_strategy():

    new_strat = dbc.Row([
        dbc.Col([
            dbc.RadioItems(
                id='new_strategy_type',
                options=[
                    {'label': 'Empty Strategy', 'value': 'Empty'},
                    {'label': 'Copy Current Strategy', 'value': 'Copy'},
                    {'label': 'Default Strategy', 'value': 'Default'}
                ],
                value='Default'),
        ]),
        dbc.Col([
            dbc.Input(
                id='new_strategy_name',
                placeholder='New Strategy Name',
            ),
        ]),
        dbc.Col([
            dbc.Button(
                id='new_strategy_button',
                children='Make New Strategy',
                block=True
            )
        ])
    ])

    return new_strat


def make_auto_navbar():
    navbar_div = dbc.Navbar(
        [
            dbc.Col([
                dbc.NavbarBrand("Strategy", className="ml-2")
            ],
                width=4),

            dbc.Col([
                dcc.Dropdown(
                    id='strategy_name',
                    placeholder='Select Existing Strategy'
                ),
            ],
                width=4),
            dbc.Col([
                dbc.Button(
                    id='delete_strategy_button',
                    children='Delete Strategy',
                    block=True
                )
            ],
                width=4),
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




