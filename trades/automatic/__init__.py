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
from trades.automatic import automatic_layouts, historical_calculations
from trades.manual import manual_layouts, stock_calculations
from trades.models import User, Trade, Portfolio, Dollar

from trades import protect_dash_route


def get_portfolios():
    user_name = session.get('user_name', None)
    user = User.query.filter_by(user_name=user_name).one_or_none()
    portfolio_list = []
    if user:
        portfolio_list = Portfolio.query.filter_by(user_id=user.id).all()

    return portfolio_list


def register_automatic(server):
    custom_css = r'/static/css/custom.css'
    external_stylesheets = [dbc.themes.FLATLY, custom_css]
    app = dash.Dash(__name__,
                    server=server,
                    url_base_pathname='/dash/automatic/',
                    external_stylesheets=external_stylesheets,
                    suppress_callback_exceptions=True)

    protect_dash_route(app)

    page_nav = automatic_layouts.make_auto_navbar()

    app.layout = html.Div([
        dcc.Location(id='url', refresh=False, pathname='/purchase/'),
        page_nav,
        html.Div(id='page_content'),
    ],
    style={'width': '97%'})

    # TODO:  Add in explanation of theory behind charts
    # TODO:  Add in a database and table to keep track of portfolio rules
    # TODO:  Add in a view with statistics on performance (and score)
    # TODO:  Consider next steps:  higher frequency, machine learning, multiple stocks.

    @app.callback(Output('page_content', 'children'),
                  [Input('url', 'pathname')])
    def display_page(pathname):
        portfolio_list = get_portfolios()

        if pathname == "/purchase/":
            return automatic_layouts.make_automatic_dashboard(portfolio_list)

    @app.callback([Output('portfolio_input', 'options'),
                   Output('stock_navbar', 'brand')],
                  [Input('url', 'pathname')])
    def display_nav(pathname):
        portfolio_list = get_portfolios()
        options = [{'label': i.name, 'value': i.name} for i in portfolio_list]
        brand_name = "Automatic Portfolio"
        return options, brand_name

    @app.callback(Output('historic_roi', 'figure'),
                  [Input('historic_input', 'n_clicks')],
                  [State('buy_or_sell', 'value'),
                   State('rule_1', 'value'),
                   State('and_or', 'value'),
                   State('rule_2', 'value')]
    )
    def historic_roi(n_clicks, buy_or_sell, rule_1_index, and_or, rule_2_index):
        base_time = datetime.strptime("2000-01-03", "%Y-%m-%d")
        now_time = datetime.strptime("2020-04-13", "%Y-%m-%d")
        value_df, choice_df, weekly_df, spy_full_df, fig = historical_calculations.get_spy_roi(base_time,
                                                              now_time,
                                                              buy_or_sell,
                                                              rule_1_index,
                                                              and_or,
                                                              rule_2_index)

        fig.update_layout(xaxis=dict(title='Time Invested (Days)'),
                          yaxis=dict(title='Return on Investment (ROI)'),
                          margin=dict(t=0, b=0, r=0, l=0),
                          paper_bgcolor='#f9f9f9'
                          )
        return fig

    @app.callback([Output('weekly_roi_graph', 'figure'),
                   Output('spy_graph', 'figure')],
                  [Input('date_range', 'start_date'),
                   Input('date_range', 'end_date'),
                   Input('buy_or_sell', 'value'),
                   Input('rule_1', 'value'),
                   Input('and_or', 'value'),
                   Input('rule_2', 'value'),
                   Input('weekly_roi_radio', 'value')]
    )
    def weekly_roi(start_date, end_date, buy_or_sell, rule_1_index, and_or, rule_2_index, weekly_roi_radio):
        # print(start_date, end_date)

        base_time = datetime.strptime(start_date[0:10], "%Y-%m-%d")
        now_time = datetime.strptime(end_date[0:10], "%Y-%m-%d")

        strategic_df, choice_df, dca_df, spy_full_df, fig = historical_calculations.get_spy_roi(base_time,
                                                              now_time,
                                                              buy_or_sell,
                                                              rule_1_index,
                                                              and_or,
                                                              rule_2_index)
        strategic_df.loc['Total'] = strategic_df.select_dtypes(pd.np.number).sum()
        dca_df.loc['Total'] = dca_df.select_dtypes(pd.np.number).sum()

        portfolio = historical_calculations.make_portfolio_graph(strategic_df, dca_df, weekly_roi_radio)
        spy_value = historical_calculations.make_spy_value_graph(spy_full_df, choice_df)

        return portfolio, spy_value

    @app.callback(
        [Output('date_range', 'start_date'),
         Output('date_range', 'end_date')],
        [Input('advance_input', 'n_clicks')],
        [State('date_range', 'start_date'),
        State('date_range', 'end_date')]
    )
    def advance_1_yr(n_clicks, start_date, end_date):
        if n_clicks:
            start_time = datetime.strptime(start_date[0:10], '%Y-%m-%d')
            end_time = datetime.strptime(end_date[0:10], '%Y-%m-%d')
            # start_year = str(int(start_date[0:4])+1)
            # end_year = str(int(end_date[0:4])+1)
            # nsd = datetime.strptime(start_year+'-01-01', '%Y-%m-%d')
            nsd = start_time+timedelta(days=365)
            nsd = nsd+timedelta(days=-nsd.weekday())
            if nsd.year == start_time.year:
                nsd = nsd+timedelta(days=7)
            # ned = datetime.strptime(end_year+'-01-01', '%Y-%m-%d')
            ned = end_time+timedelta(days=365)
            ned = ned+timedelta(days=-ned.weekday())
            if ned.year == end_time.year:
                ned = ned+timedelta(days=7)
            print(nsd, ned)
            return nsd, ned

        return start_date, end_date

