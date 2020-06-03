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
from trades.automatic import automatic_layouts
from trades.manual.stock_calculations import get_yahoo_stock_data, flatten_df
from trades.strategy import strategy_layouts, strategy_calculations
from trades.strategy.optimize import create_single_solutions
from trades.manual import manual_layouts, stock_calculations, get_manual_portfolios
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

    page_nav = automatic_layouts.make_auto_navbar_view()
    app.layout = html.Div([
        dcc.Location(id='url', refresh=False, pathname='/auto/'),
        page_nav,
        html.Div(id='page_content'),
    ],
    style = {'width': '97%'})

    @app.callback(Output('page_content', 'children'),
                  [Input('url', 'pathname')])
    def display_page(pathname):
        if pathname == "/auto/":
            return automatic_layouts.make_automatic_dashboard()

    @app.callback([Output('portfolio_input', 'options'),
                   Output('stock_navbar', 'brand'),
                   Output('portfolio_input', 'value')],
                  [Input('url', 'pathname')])
    def display_nav(pathname):
        portfolio_list = get_manual_portfolios()
        options = [{'label': i.name, 'value': i.name} for i in portfolio_list]
        brand_name = "Automatic Portfolio"
        return options, brand_name, portfolio_list[-1].name

    @app.callback([Output('strat_table', 'columns'),
                   Output('strat_table', 'data')],
                  [Input('portfolio_input', 'value')]
                  )
    def get_manual_data(portfolio_name):
        #TODO:  Get this callback to fire on load. (put strat table as part of page layout)
        print(portfolio_name)
        user_name = session.get('user_name', None)
        user = User.query.filter_by(user_name=user_name).one_or_none()
        portfolio = Portfolio.query.filter_by(user_id=user.id, name=portfolio_name).one_or_none()
        all_cash = Dollar.query.filter_by(portfolio_id=portfolio.id).all()
        trades = Trade.query.filter_by(portfolio_id=portfolio.id).all()

        end_date = datetime.now()

        ticker_list = []
        start_dates = []
        value_list = []
        sell_dates = []
        for trade in trades:
            ticker_list.append(trade.security)
            start_dates.append(trade.purchase_date)
            value_list.append(trade.value)
            if trade.sell_date:
                sell_dates.append(trade.sell_date)
            else:
                sell_dates.append(end_date)

        start_date = min([sti for sti in start_dates])

        df = get_yahoo_stock_data(ticker_list, start_date, end_date)
        pxdf, total, roi = flatten_df(df, ticker_list, value_list, start_dates, sell_dates, all_cash)

        print(pxdf.columns)

        data = [{'1': 1, '2': 2, '3': 3},
                {'1': 2, '2': 4, '3': 6}]

        columns = [{'id': '1', 'name': '1'},
                   {'id': '2', 'name': '2'},
                   {'id': '3', 'name': '3'}]

        return columns, data

