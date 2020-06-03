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
                    html.H4(children="Purchase Stocks",
                            style={'text-align': 'center'}),
                ],
                    className='pretty_container'
                )
            ],
                width=6),
            dbc.Col([
                html.Div([
                    html.H4(children="Sell Stocks",
                            style={'text-align': 'center'}),
                ],
                    className='pretty_container'
                )
            ],
            width=6)
        ]),
    ])
    return dashboard_div


def make_auto_controls():
    auto_controls = html.Div([
        dbc.Row([
            dbc.Col([
                dash_table.DataTable(id='strat_table')
            ])
        ])
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