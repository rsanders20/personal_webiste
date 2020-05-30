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
import pandas as pd

from trades import db
from trades.strategy import strategy_layouts, strategy_calculations
from trades.strategy.optimize import create_single_solutions
from trades.manual import manual_layouts, stock_calculations
from trades.models import User, Trade, Portfolio, Dollar, Strategy, Signal

from trades import protect_dash_route


def get_auto_portfolios():
    user_name = session.get('user_name', None)
    user = User.query.filter_by(user_name=user_name).one_or_none()
    portfolio_list = []
    if user:
        portfolio_list = Portfolio.query.filter_by(user_id=user.id, strategy="Automatic").all()

    return portfolio_list


def register_automatic(server):
    custom_css = r'/static/css/custom.css'
    external_stylesheets = [dbc.themes.GRID, dbc.themes.FLATLY, custom_css]
    app = dash.Dash(__name__,
                    server=server,
                    url_base_pathname='/dash/automatic/',
                    external_stylesheets=external_stylesheets,
                    suppress_callback_exceptions=True)

    protect_dash_route(app)

    page_nav = manual_layouts.make_navbar_view()
    app.layout = html.Div([
        dcc.Location(id='url', refresh=False, pathname='/auto/'),
        page_nav,
        html.Div(id='page_content'),
    ],
    style={'width': '97%'})

    @app.callback([Output('portfolio_input', 'options'),
                   Output('stock_navbar', 'brand'),
                   Output('portfolio_input', 'value')],
                  [Input('url', 'pathname')])
    def display_nav(pathname):
        portfolio_list = get_auto_portfolios()
        options = [{'label': i.name, 'value': i.name} for i in portfolio_list]
        brand_name = "Automatic Portfolio"
        return options, brand_name, portfolio_list[-1].name