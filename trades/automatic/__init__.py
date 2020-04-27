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

    page_nav = automatic_layouts.make_auto_navbar()

    app.layout = html.Div([
        dcc.Location(id='url', refresh=False, pathname='/purchase/'),
        page_nav,
        html.Div(id='page_content'),
    ],
    style={'width': '97%'})

    # TODO:  Add in explanation of theory behind charts
    # TODO:  Add in loading box around left side graphs
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
                          yaxis=dict(title='Return on Investment (ROI)'))
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
        # print(value_df)
        time_values = strategic_df.columns
        n_weeks = len(time_values)
        cash_values = np.array([100*(i+1) for i in range(n_weeks)])

        total_return = strategic_df.to_numpy()[-1, :]-cash_values
        total_value = strategic_df.to_numpy()[-1, :]
        weekly_return = dca_df.to_numpy()[-1, :]-cash_values
        weekly_value = dca_df.to_numpy()[-1, :]

        portfolio_return = go.Figure()
        portfolio_return.add_trace(go.Scatter(
            x=time_values, y=weekly_return, name='DCA'
        ))
        portfolio_return.add_trace(go.Scatter(
            x=time_values, y=total_return, name='Strategic'
        ))
        portfolio_return.update_layout(title="Portfolio Return by Week",
                                       legend_orientation='h',
                                       yaxis=dict(title='Change in Portfolio Value ($)'))

        portfolio_value = go.Figure()
        portfolio_value.add_trace(go.Scatter(
            x=time_values, y = weekly_value, name='DCA'
        ))
        portfolio_value.add_trace(go.Scatter(
            x=time_values, y = total_value, name='Strategic'
        ))
        portfolio_value.add_trace(go.Scatter(
            x=time_values, y=cash_values, name='Cash'
        ))
        portfolio_value.update_layout(title="Portfolio Value by Week",
                                      legend_orientation='h',
                                      yaxis=dict(title='Portfolio Value ($)'))

        buy_correct = []
        buy_wrong = []
        sell_correct = []
        sell_wrong = []
        choice_dates = choice_df.index
        choice_list = choice_df.to_numpy()[0]
        for date, choice in zip(choice_dates, choice_list):
            next_week = date+timedelta(days=7)
            spy_value = spy_full_df.iloc[abs(spy_full_df.index-date) == min(abs(spy_full_df.index-date))]['Close'].to_numpy()[0]
            next_spy_value = spy_full_df.iloc[abs(spy_full_df.index-next_week) == min(abs(spy_full_df.index-next_week))]['Close'].to_numpy()[0]

            if choice=="invest":
                if next_spy_value > spy_value:
                    buy_correct.append([date, spy_value])
                else:
                    buy_wrong.append([date, spy_value])
            else:
                if next_spy_value > spy_value:
                    sell_wrong.append([date, spy_value])
                else:
                    sell_correct.append([date, spy_value])

        buy_correct_array = np.array(buy_correct)
        sell_correct_array = np.array(sell_correct)
        buy_wrong_array = np.array(buy_wrong)
        sell_wrong_array = np.array(sell_wrong)

        spy_value = go.Figure()
        spy_value.add_trace(go.Scatter(
            x=spy_full_df.index, y=spy_full_df['Close'], name='SPY',
        ))
        if sell_correct_array.any():
            spy_value.add_trace(go.Scatter(
                x=sell_correct_array[:, 0], y=sell_correct_array[:, 1],
                mode='markers', name='Sell (Correct)', marker_symbol='triangle-up',
                marker_color='Red', marker_size=12
            ))
        if sell_wrong_array.any():
            spy_value.add_trace(go.Scatter(
                x=sell_wrong_array[:, 0], y=sell_wrong_array[:, 1],
                mode='markers', name='Sell (Wrong)', marker_symbol='triangle-down',
                marker_color='Red', marker_size=12
            ))

        if buy_correct_array.any():
            spy_value.add_trace(go.Scatter(
                x=buy_correct_array[:, 0], y=buy_correct_array[:, 1],
                mode='markers', name='Buy (Correct)', marker_symbol='triangle-up',
                marker_color = 'Green', marker_size=12
            ))
        if buy_wrong_array.any():
            spy_value.add_trace(go.Scatter(
                x=buy_wrong_array[:, 0], y=buy_wrong_array[:, 1],
                mode='markers', name='Buy (Wrong)', marker_symbol='triangle-down',
                marker_color = 'Green', marker_size=12
            ))

        spy_value.add_trace(go.Scatter(
            x=spy_full_df.index, y=spy_full_df['200'], name='200 Day'
        ))
        spy_value.add_trace(go.Scatter(
            x=spy_full_df.index, y=spy_full_df['50'], name='50 Day'
        ))

        spy_value.update_layout(title='SPY Daily Closing Value',
                                showlegend=True,
                                legend_orientation='h',
                                xaxis=dict(range=[spy_full_df.index[0], spy_full_df.index[-1]]),
                                yaxis=dict(title='SPY Closing Value ($)'))

        if weekly_roi_radio == 1:
            return portfolio_value, spy_value
        else:
            return portfolio_return, spy_value

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

