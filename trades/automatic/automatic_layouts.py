import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import datetime

import pandas as pd

import plotly.express as px

from trades.manual import stock_calculations


def make_automatic_dashboard(portfolio_list):

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
                    html.H4(children='SPY Daily Closing Value',
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
                                   'margin-bottom': '45px'}),
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
                    html.H4(children="Historic Returns",
                            style={'text-align': 'center'}),
                    historic_button,
                    historic_roi
                ],
                className='pretty_container')
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4(children="Buy/Sell Logic",
                            style={'text-align': 'center'}),
                    dashboard_controls
                ],
                    className='pretty_container')
            ]),
        ])
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
    # rules_div = make_rules_form()
    rules_div = make_signal_table()

    controls = dbc.Form([

        dbc.FormGroup([
            dbc.Label("Set Buying and Selling Logic", color='success'),
            rules_div
        ],
        style={'margin-top': '15px'}),
    ])

    return controls


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
                    style={'text-align': 'center'})
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
                           duration=4000)

    table_input = dbc.FormGroup([
        dash_table.DataTable(id='portfolio_entries',
                             columns=(
                                 [{'id': 'purchase_date', 'name': 'Purchase Date', 'type': 'datetime'}]+
                                 [{'id': 'value_{}'.format(i+1), 'name': '{}'. format(i+1)} for i in range(10)])),
    ])

    buy_and_sell = dbc.FormGroup([
        dbc.Button(id='advance_input',
                   children=" <- 1 Yr.",
                   block=True),
    ])

    now_time = datetime.datetime.now()
    start_time = now_time-datetime.timedelta(days=365)

    date_range = dbc.FormGroup([dcc.DatePickerRange(id='date_range', start_date = start_time, end_date = now_time)])

    data_div = html.Div([
        dbc.Row([
            dbc.Col([
                date_range,
            ],
            width=8),
            dbc.Col([
                buy_and_sell,
            ],
            width=4),
        ]),
        dbc.Row([
            dbc.Col([
                progress_alert
            ]),
        ]),
    ],
        style={'margin-top': '5px', 'width': '100%', 'margin-right': '15px'})

    return data_div


def make_signal_table():
    rules_list = [
        {'Larger: When?': -15, 'Larger: What?': 'Close', 'Smaller: When?': 0, 'Smaller: What?': 'Close',
         'Percentage': 3.0, "Weight": -1.0},
        {'Larger: When?': -10, 'Larger: What?': 'Close', 'Smaller: When?': 0, 'Smaller: What?': 'Close',
         'Percentage': 2.0, "Weight": -1.0},
        {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -5, 'Smaller: What?': 'Close',
         'Percentage': 1.0, "Weight": -1.0},
    ]
    signal_div = html.Div([
        dash_table.DataTable(
            id='signal_table',
            data=rules_list,
            columns=[
                {'id': 'Larger: When?', 'name': 'Larger: When?', 'editable':True, 'type': 'numeric'},
                {'id': 'Larger: What?', 'name': 'Larger: What?', 'presentation': 'dropdown', 'editable':True, },
                {'id': 'Smaller: When?', 'name': 'Smaller: When?', 'editable':True, 'type': 'numeric'},
                {'id': 'Smaller: What?', 'name': 'Smaller: What?', 'presentation': 'dropdown', 'editable':True},
                {'id': 'Percentage', 'name': 'Percentage', 'editable':True},
                {'id': 'Weight', 'name': 'Weight', 'editable':True, 'type': 'numeric'},
            ],

            editable=True,
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


def make_rules_form():
    rules_alert = dbc.FormGroup([
        dbc.Alert(id='rules_alert',
                  children="No new rule has been added",
                  color="warning",
                  is_open=False,
                  duration=4000)
    ])

    buy_or_sell = dbc.FormGroup([
        dbc.Label("Buy/Sell"),
        dbc.RadioItems(id="buy_or_sell",
                       options=[{'label': "Buy", 'value': 'buy'},
                                {'label': 'Sell', 'value': 'sell'}],
                       value='sell'),

    ])

    # securities_list = stock_calculations.get_securities_list()

    positive_rule = dbc.FormGroup([
        # dbc.Label("If Last X Wks. Positive"),
        dcc.Dropdown(
            id='rule_1',
            options=[{'label': rule, 'value': i} for i, rule in enumerate(get_rules())],
            value=0,
        ),
    ])

    and_or = dbc.FormGroup([
        dbc.Label("And/Or"),
        dbc.RadioItems(id="and_or",
                       options=[{'label': "And", 'value': 'and'},
                                {'label': 'Or', 'value': 'or'}],
                       value='and'),

    ])

    negative_rule = dbc.FormGroup([
        # dbc.Label("If Last X Wks. Negative"),
        dcc.Dropdown(
            id='rule_2',
            options=[{'label': rule, 'value': i} for i, rule in enumerate(get_rules())],
            value=6,
        ),
    ])


    form_div = html.Div([
        dbc.Form([
            dbc.Row([
                dbc.Col([
                    buy_or_sell
                ],
                width=2),
                dbc.Col([
                    positive_rule
                ],
                width=4),
                dbc.Col([
                    and_or
                ],
                width=2),
                dbc.Col([
                    negative_rule
                ],
                width=4),
            ]),
        ])
    ])

    return form_div


def make_historic_button():
    historic_input = dbc.FormGroup([
        dbc.Button(id='historic_input',
                   children='Run Statistical Comparison',
                   block=True)
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
    navbar_div = html.Div([
        dbc.Row([
            dbc.Col([
                dbc.NavbarSimple(
                    id='stock_navbar',
                    color="primary",
                    dark=True,
                    # style={'padding': '0px'},
            )
            ],
                width=12)
        ]),
    ])
    return navbar_div




