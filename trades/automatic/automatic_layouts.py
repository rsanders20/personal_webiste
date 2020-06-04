import json
from datetime import datetime, timedelta

from dash import dash
from dash.dependencies import Output, Input, State
from flask import session
import plotly.express as px
import plotly.graph_objs as go
import numpy as np

import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
import pandas as pd

from trades import db
from trades.strategy import strategy_layouts, strategy_calculations
from trades.strategy.optimize import create_single_solutions
from trades.manual import manual_layouts, stock_calculations, get_manual_portfolios
from trades.models import User, Trade, Portfolio, Dollar, Strategy, Signal

from trades import protect_dash_route


def make_automatic_dashboard():
    auto_controls = make_auto_controls()

    dashboard_div = html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4(children="Build Automatic Portfolio",
                            style={'text-align': 'center'}),
                    auto_controls,
                ],
                    className='pretty_container'
                )
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4(children="Daily Values",
                            style={'text-align': 'center'}),
                    dbc.Tabs([
                        dbc.Tab(label='Daily Values Table'),
                        dbc.Tab(label='Daily Values Graph')
                    ])
                ],
                    className='pretty_container'
                )
            ]),
        ])
    ])
    return dashboard_div


def make_auto_controls():
    auto_controls = html.Div([
        html.Div(id='strat-div'),
        dbc.Row([
            dbc.Col([
                dbc.Label("Pick the end-date for the automatic strategies"),
                dcc.DatePickerSingle(id='end-date-picker',
                                     date=datetime.now())
            ],
                width=6),
            dbc.Col([
                dbc.Label("Build the Automatic Portfolio"),
                dbc.Button(id='run-auto',
                           children='Run',
                           block=True)
            ],
            width=6),

        ],
        style={'margin-top': '25px'})
    ])


    return auto_controls


def make_auto_navbar_view():
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