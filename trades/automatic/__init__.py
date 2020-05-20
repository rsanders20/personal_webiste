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
    external_stylesheets = [dbc.themes.GRID, dbc.themes.FLATLY, custom_css]
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

    # TODO:  9)  Add in a warning if the ticker is not recognized.  Add to manual as well.
    #       10)  Provide a score for the historic graph
    #       12)  Add in an "optimize-rules" button
    #       10)  Add in a way to save the strategy to a database
    #       10)  Label the historic graph with the strategy name and ticker
    #       11)  Add in a way to apply a strategy to a portfolio
    #           (For each stock, add dropdown to select strategy as well as the date the strategy starts working)
    #       13)  Add in more than just the moving averages...alpha, beta, theta, etc.

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
                  [State('historic_date', 'start_date'),
                   State('historic_date', 'end_date'),
                   State('ticker_input', 'value'),
                   State('ticker_sp500_input', 'value'),
                   State('ticker_input_radio', 'value'),
                   State('signal_table', 'data'),
                   State('signal_table', 'selected_rows'),
                   State('buy_threshold', 'value'),
                   State('sell_threshold', 'value')]
                  )
    def historic_roi(n_clicks, start_date, end_date, ticker_input, ticker_sp500_input,
                   ticker_input_radio, data, selected_rows, buy_threshold, sell_threshold):
        rules_list = []
        for i in selected_rows:
            rules_list.append(data[i])

        if ticker_input_radio == "SP500":
            ticker = ticker_sp500_input
        else:
            ticker = ticker_input

        base_time = datetime.strptime(start_date[0:10], "%Y-%m-%d")
        now_time = datetime.strptime(end_date[0:10], "%Y-%m-%d")

        # Lump Sum Code
        fig = historical_calculations.get_historic_roi(ticker, base_time, now_time,
                                                       rules_list, buy_threshold, sell_threshold)

        return fig

    @app.callback([Output('weekly_roi_graph', 'figure'),
                   Output('spy_graph', 'figure')],
                  [Input('date_range', 'start_date'),
                   Input('date_range', 'end_date'),
                   Input('run_analysis', 'n_clicks'),
                   Input('weekly_roi_radio', 'value')],
                  [State('buy_threshold', 'value'),
                   State('sell_threshold', 'value'),
                   State('ticker_input', 'value'),
                   State('ticker_sp500_input', 'value'),
                   State('ticker_input_radio', 'value'),
                   State('signal_table', 'selected_rows'),
                   State('signal_table', 'data')]
                  )
    def weekly_roi(start_date, end_date, n_clicks, weekly_roi_radio,
                   buy_threshold, sell_threshold, ticker_input, ticker_sp500_input,
                   ticker_input_radio, selected_rows, data):
        rules_list = []
        for i in selected_rows:
            rules_list.append(data[i])

        if ticker_input_radio == "SP500":
            ticker = ticker_sp500_input
        else:
            ticker = ticker_input

        print(rules_list)
        base_time = datetime.strptime(start_date[0:10], "%Y-%m-%d")
        now_time = datetime.strptime(end_date[0:10], "%Y-%m-%d")+timedelta(days=1)
        values_df = historical_calculations.get_roi(ticker, base_time, now_time,
                                                    rules_list, buy_threshold, sell_threshold)

        # SPY Value Graph
        spy_value = go.Figure()
        spy_value.add_trace(go.Scatter(
            x=values_df.index, y = values_df['Close'], name = ticker_input
        ))
        spy_value.add_trace(go.Scatter(
            x=values_df.index, y = values_df['200'], name = '200'
        ))
        spy_value.add_trace(go.Scatter(
            x=values_df.index, y=values_df['50'], name='50'
        ))
        spy_value.add_trace(go.Scatter(
            x=values_df.loc[values_df['strategic_decisions']=='Sell'].index,
            y = values_df.loc[values_df['strategic_decisions']=='Sell', 'Close'],
            mode='markers', name='Sell', marker_symbol='triangle-down', marker_color='Red', marker_size=12
        ))
        spy_value.add_trace(go.Scatter(
            x=values_df.loc[values_df['strategic_decisions']=='Buy'].index,
            y = values_df.loc[values_df['strategic_decisions']=='Buy', 'Close'],
            mode='markers', name='Buy', marker_symbol='triangle-up', marker_color='Green', marker_size=12
        ))

        spy_value.update_layout(showlegend=True,
                                legend_orientation='h',
                                yaxis=dict(title=f'{ticker_input} Closing Value ($)'),
                                margin=dict(t=0, b=0, r=0, l=0),
                                paper_bgcolor='#f9f9f9'
                                )

        # Portfolio Graph
        portfolio = go.Figure()
        if weekly_roi_radio == 1:
            portfolio.add_trace(go.Scatter(
                x = values_df.index, y = values_df['simple_values'], name='Simple'
            ))
            portfolio.add_trace(go.Scatter(
                x=values_df.index, y=values_df['strategic_values'], name='Strategic'
            ))

            portfolio.update_layout(legend_orientation='h',
                                          yaxis=dict(title='Portfolio Value ($)'),
                                          margin=dict(t=0, b=0, r=0, l=0),
                                          paper_bgcolor='#f9f9f9'
                                          )
        else:
            portfolio.add_trace(go.Scatter(
                x=values_df.index, y=values_df['simple_values']/1000, name='Simple'
            ))
            portfolio.add_trace(go.Scatter(
                x=values_df.index, y=values_df['strategic_values']/1000, name='Strategic'
            ))

            portfolio.update_layout(legend_orientation='h',
                                    yaxis=dict(title='Portfolio ROI []'),
                                    margin=dict(t=0, b=0, r=0, l=0),
                                    paper_bgcolor='#f9f9f9'
                                    )

        return portfolio, spy_value

    @app.callback(
        [Output('date_range', 'start_date'),
         Output('date_range', 'end_date')],
        [Input('historic_roi', 'clickData')],
        [State('date_range', 'start_date'),
         State('date_range', 'end_date')]
    )
    def advance_1_yr(clicked_data, start_date, end_date):
        if clicked_data:
            start_str = clicked_data["points"][0]['x']
            start_date = datetime.strptime(start_str, '%Y-%m-%d')
            end_date = start_date+timedelta(days=365)
            return start_date, end_date

        return start_date, end_date

    @app.callback(
        [Output('ticker_input', 'style'),
         Output('ticker_sp500_input', 'style')],
        [Input('ticker_input_radio', 'value')]
    )
    def change_ticker_input(ticker_input_radio):
        hidden_style = {'display': 'none'}
        visible_style = {'display': 'block'}
        if ticker_input_radio == 'SP500':
            return hidden_style, visible_style
        else:
            return visible_style, hidden_style

    @app.callback(
        Output('signal_table', 'data'),
        [Input('editing-rows-button', 'n_clicks')],
        [State('signal_table', 'data'),
         State('signal_table', 'columns')])
    def add_row(n_clicks, rows, columns):
        if n_clicks:
            rows.append({c['id']: '' for c in columns})
        return rows
