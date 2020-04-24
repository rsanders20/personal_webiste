import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import datetime

import plotly.express as px

from trades.manual import stock_calculations


def make_automatic_dashboard(portfolio_list):

    rules_div = make_rules_form()
    weekly_progress = make_weekly_progress()
    historic_roi = make_historic_roi_graph()
    weekly_roi = make_weekly_graph()

    dashboard_div = html.Div([
        dbc.Row([
            dbc.Col([
                weekly_roi
            ]),
            dbc.Col([
                weekly_progress
            ])
        ]),
        dbc.Row([
            dbc.Col([
                historic_roi
            ]),
            dbc.Col([
                rules_div
            ])
        ]),
    ])

    return dashboard_div
    # return html.Div(children="Hello!")


def make_historic_roi_graph():
    historic_roi = html.Div([
        dcc.Graph(id='historic_roi')
        ])

    return historic_roi


def make_weekly_graph():
    weekly_roi = html.Div([
        dcc.Graph(id='weekly_roi')
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
                   children="Buy and Sell",
                   block=True),
    ])

    date_range = dbc.FormGroup([
        dcc.DatePickerRange(id='date_range',
                            start_date = datetime.datetime.now()-datetime.timedelta(days=61),
                            end_date = datetime.datetime.now()-datetime.timedelta(days=1)),
    ])

    data_div = html.Div([
        dbc.Row([
            dbc.Col([
                table_input,
            ],
            style={'margin-left': '15px', 'margin-right': '15px'}
            )
        ]),
        dbc.Row([
            dbc.Col([
                date_range,
            ]),
            dbc.Col([
                buy_and_sell,
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                progress_alert
            ]),
        ]),
    ],
        style={'margin-top': '5px', 'width': '100%', 'margin-right': '15px'})

    return data_div


def make_rules_form():
    rules_alert = dbc.FormGroup([
        dbc.Alert(id='rules_alert',
                  children="No new rule has been added",
                  color="warning",
                  is_open=False,
                  duration=4000)
    ])

    historic_input = dbc.FormGroup([
        dbc.Button(id='historic_input',
                   children='Run Statistical Comparison',
                   block=True)
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
        dbc.Label("If Last X Wks. Positive"),
        dcc.Dropdown(
            id='positive_rule',
            options=[{'label': i, 'value': i} for i in [1, 2, 3, 4]],
            value=1,
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
        dbc.Label("If Last X Wks. Negative"),
        dcc.Dropdown(
            id='negative_rule',
            options=[{'label': i, 'value': i} for i in [1, 2, 3, 4]],
            value=3,
        ),
    ])


    form_div = html.Div([
        dbc.Form([
            dbc.Row([
                dbc.Col([
                    buy_or_sell
                ]),
                dbc.Col([
                    positive_rule
                ]),
                dbc.Col([
                    and_or
                ]),
                dbc.Col([
                    negative_rule
                ]),
            ]),
            dbc.Row([
                dbc.Col([
                    historic_input
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    rules_alert
                ])
            ]),
        ])
    ],
        style={'margin-top': '5px'}
    )

    return form_div




