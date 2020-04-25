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
    external_stylesheets = [dbc.themes.FLATLY]
    app = dash.Dash(__name__,
                    server=server,
                    url_base_pathname='/dash/automatic/',
                    external_stylesheets=external_stylesheets,
                    suppress_callback_exceptions=True)

    protect_dash_route(app)

    page_nav = manual_layouts.make_navbar_view()

    app.layout = html.Div([
        dcc.Location(id='url', refresh=False, pathname='/purchase/'),
        page_nav,
        html.Div(id='page_content'),
    ])
    # TODO:  Add in arrows up or down if choice was good or bad
    # TODO:  Add in a toggle to show portfolio value or difference
    # TODO:  Add in explanation of theory behind charts
    # TODO:  Add in loading box around left side graphs
    # TODO:  Add in a view with statistics on performance (and score)
    # TODO:  Add in borders to break up button view

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
                   State('positive_rule', 'value'),
                   State('and_or', 'value'),
                   State('negative_rule', 'value')]
    )
    def historic_roi(_, buy_or_sell, positive_rule, and_or, negative_rule):
        base_time = datetime.strptime("2000-01-03", "%Y-%m-%d")
        now_time = datetime.strptime("2020-04-13", "%Y-%m-%d")
        value_df, choice_df, weekly_df, spy_full_df, fig = historical_calculations.get_spy_roi(base_time,
                                                              now_time,
                                                              buy_or_sell,
                                                              positive_rule,
                                                              and_or,
                                                              negative_rule)
        return fig

    @app.callback([Output('weekly_roi', 'figure'),
                   Output('spy_graph', 'figure')],
                  [Input('date_range', 'start_date'),
                   Input('date_range', 'end_date')],
                  [State('buy_or_sell', 'value'),
                   State('positive_rule', 'value'),
                   State('and_or', 'value'),
                   State('negative_rule', 'value')]
    )
    def weekly_roi(start_date, end_date, buy_or_sell, positive_rule, and_or, negative_rule):
        # print(start_date, end_date)

        base_time = datetime.strptime(start_date[0:10], "%Y-%m-%d")
        now_time = datetime.strptime(end_date[0:10], "%Y-%m-%d")

        strategic_df, choice_df, dca_df, spy_full_df, fig = historical_calculations.get_spy_roi(base_time,
                                                              now_time,
                                                              buy_or_sell,
                                                              positive_rule,
                                                              and_or,
                                                              negative_rule)
        strategic_df.loc['Total'] = strategic_df.select_dtypes(pd.np.number).sum()
        dca_df.loc['Total'] = dca_df.select_dtypes(pd.np.number).sum()
        # print(value_df)
        time_values = strategic_df.columns
        n_weeks = len(time_values)
        cash_values = np.array([100*(i+1) for i in range(n_weeks)])

        total_values = strategic_df.to_numpy()[-1, :]-cash_values
        weekly_values = dca_df.to_numpy()[-1, :]-cash_values

        portfolio_value = go.Figure()
        portfolio_value.add_trace(go.Scatter(
            x=time_values, y=weekly_values, name='DCA'
        ))
        portfolio_value.add_trace(go.Scatter(
            x=time_values, y=total_values, name='Strategic'
        ))
        # portfolio_value.add_trace(go.Scatter(
        #     x=time_values, y=cash_values, name='Cash'
        # ))
        portfolio_value.update_layout(title="Portfolio Value by Week")

        buy = []
        sell = []
        choice_dates = choice_df.index
        choice_list = choice_df.to_numpy()[0]
        for date, choice in zip(choice_dates, choice_list):
            spy_value = spy_full_df.iloc[abs(spy_full_df.index-date) == min(abs(spy_full_df.index-date))]['Close'].to_numpy()[0]

            if choice=="invest":
                buy.append([date, spy_value])
            else:
                sell.append([date, spy_value])

        buy_array = np.array(buy)
        sell_array = np.array(sell)

        spy_value = go.Figure()
        spy_value.add_trace(go.Scatter(
            x=spy_full_df.index, y=spy_full_df['Close'], name='SPY',
        ))
        spy_value.add_trace(go.Scatter(
            x=sell_array[:, 0], y=sell_array[:, 1], mode='markers', name='Sell'
        ))
        spy_value.add_trace(go.Scatter(
            x=buy_array[:, 0], y=buy_array[:, 1], mode='markers', name='Buy'
        ))
        spy_value.update_layout(title='SPY Daily Closing Value', showlegend=True)

        return portfolio_value, spy_value

    @app.callback(
        [Output('date_range', 'start_date'),
         Output('date_range', 'end_date')],
        [Input('advance_input', 'n_clicks')],
        [State('date_range', 'start_date'),
        State('date_range', 'end_date')]
    )
    def advance_1_yr(n_clicks, start_date, end_date):
        if n_clicks:
            start_year = str(int(start_date[0:4])+1)
            end_year = str(int(end_date[0:4])+1)
            # TODO:  make it the first monday of the year
            nsd = datetime.strptime(start_year+'-01-01', '%Y-%m-%d')
            ned = datetime.strptime(end_year+'-01-01', '%Y-%m-%d')
            return nsd, ned

        return start_date, end_date

