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
from trades.portfolio import manual_layouts, stock_calculations
from trades.models import User, Trade, Portfolio, Dollar, Strategy, Signal

from trades import protect_dash_route


def get_strategies():
    user_name = session.get('user_name', None)
    user = User.query.filter_by(user_name=user_name).one_or_none()
    strategy_list = []
    if user:
        strategy_list = Strategy.query.filter_by(user_id=user.id).all()

    return strategy_list


def register_strategy(server):
    custom_css = r'/static/css/custom.css'
    external_stylesheets = [dbc.themes.GRID, dbc.themes.FLATLY, custom_css]
    app = dash.Dash(__name__,
                    server=server,
                    url_base_pathname='/dash/strategy/',
                    external_stylesheets=external_stylesheets,
                    suppress_callback_exceptions=True)

    protect_dash_route(app)

    page_nav = strategy_layouts.make_auto_navbar()
    app.layout = html.Div([
        dcc.Location(id='url', refresh=False, pathname='/purchase/'),
        page_nav,
        html.Div(id='page_content'),
    ],
    style={'width': '97%'})

    @app.callback(Output('page_content', 'children'),
                  [Input('url', 'pathname')])
    def display_page(pathname):
        if pathname == "/purchase/":
            return strategy_layouts.make_automatic_dashboard()

    @app.callback([Output('new_strategy_alert', 'is_open'),
                   Output('new_strategy_alert', 'children'),
                   Output('new_strategy_alert', 'color')],
                  [Input('new_strategy_button', 'n_clicks')],
                  [State('new_strategy_name', 'value'),
                   State('new_strategy_type', 'value'),
                   State('strategy_name', 'value')])
    def make_new_strategy(n_clicks, new_strategy_name, new_strategy_type,
                          old_strategy_name):
        if n_clicks:
            if new_strategy_name=="" or new_strategy_name is None:
                return True, "Strategy Name Cannot Be Blank", "danger"
            user_name = session.get('user_name', None)
            user = User.query.filter_by(user_name=user_name).one_or_none()
            is_strategy = Strategy.query.filter_by(user_id=user.id, name=new_strategy_name).one_or_none()
            if is_strategy:
                return True, "Please select a new Strategy Name.  This one already exists.", "danger"

            strategy = Strategy(
                user_id=user.id,
                name=new_strategy_name,
                stock_ticker='SPY',
                buy_threshold=-2.5,
                sell_threshold=-2.5)
            db.session.add(strategy)
            db.session.commit()
            if new_strategy_type == 'Empty':
                return True, "Empty Strategy Created!", "success"
            elif new_strategy_type == 'Default':
                rules_list = [
                    # {'Larger: When?': -15, 'Larger: What?': 'Close', 'Smaller: When?': 0, 'Smaller: What?': 'Close',
                    #  'Percentage': 10.0, "Weight": -2.0},
                    {'Larger: When?': -10, 'Larger: What?': 'Close', 'Smaller: When?': 0, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -2.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -1, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -1.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -3, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -1.0},
                    {'Larger: When?': 0, 'Larger: What?': 'Close', 'Smaller: When?': -5, 'Smaller: What?': 'Close',
                     'Percentage': 1.0, "Weight": -1.0},
                    # {'Larger: When?': -5, 'Larger: What?': 'Close', 'Smaller: When?': -6, 'Smaller: What?': 'Close',
                    #  'Percentage': 0.0, "Weight": -1.0},
                ]
                for row in rules_list:
                    signal = Signal(strategy_id=strategy.id,
                                    larger_when=row['Larger: When?'],
                                    larger_what = row['Larger: What?'],
                                    smaller_when = row['Smaller: When?'],
                                    smaller_what = row['Smaller: What?'],
                                    percentage = row['Percentage'],
                                    weight = row['Weight'])
                    db.session.add(signal)
                db.session.commit()
                return True, "Default Strategy Created!", "success"
            else:  #  Copy
                old_strategy = Strategy.query.filter_by(user_id=user.id, name=old_strategy_name).one_or_none()

                strategy.stock_ticker = old_strategy.stock_ticker
                strategy.buy_threshold = old_strategy.buy_threshold
                strategy.sell_threshold = old_strategy.sell_threshold
                old_signals = Signal.query.filter_by(strategy_id = old_strategy.id).all()
                for old_signal in old_signals:
                    signal = Signal(strategy_id=strategy.id,
                                    larger_when=old_signal.larger_when,
                                    larger_what = old_signal.larger_what,
                                    smaller_when = old_signal.smaller_when,
                                    smaller_what = old_signal.smaller_what,
                                    percentage = old_signal.percentage,
                                    weight = old_signal.weight)
                    db.session.add(signal)
                db.session.commit()
                return True, f"{old_strategy_name} Strategy Copied!", "success"

        return False, "", "warning"

    @app.callback([Output('delete_strategy_alert', 'is_open'),
                   Output('delete_strategy_alert', 'children'),
                   Output('delete_strategy_alert', 'color')],
                  [Input('delete_strategy_button', 'n_clicks')],
                  [State('strategy_name', 'value')])
    def delete_strategy(n_clicks, strategy_name):
        if n_clicks:
            user_name = session.get('user_name', None)
            user = User.query.filter_by(user_name=user_name).one_or_none()
            is_strategy = Strategy.query.filter_by(user_id=user.id, name=strategy_name).one_or_none()
            if is_strategy:
                # delete all existing signals
                signal_list = Signal.query.filter_by(strategy_id=is_strategy.id).all()
                if signal_list:
                    for signal in signal_list:
                        db.session.delete(signal)
                db.session.delete(is_strategy)
                db.session.commit()
                return True, "Strategy Removed!", "success"

        return False, "", "warning"

    @app.callback([Output('strategy_name', 'options'),
                   Output('strategy_name', 'value')],
                  [Input('url', 'pathname'),
                   Input('new_strategy_alert', 'children'),
                   Input('delete_strategy_alert', 'children')])
    def display_nav(pathname, n_new, n_del):
        strategy_list = get_strategies()
        if strategy_list:
            options = [{'label': i.name, 'value': i.name} for i in strategy_list]
            value = strategy_list[-1].name
            return options, value
        else:
            return [], ""

    @app.callback([Output('historic_roi', 'figure'),
                   Output('historic_alert', 'children'),
                   Output('historic_alert', 'color')],
                  [Input('historic_input', 'n_clicks')],
                  [State('historic_date', 'start_date'),
                   State('historic_date', 'end_date'),
                   State('ticker_input', 'value'),
                   State('ticker_sp500_input', 'value'),
                   State('ticker_input_radio', 'value'),
                   State('signal_table', 'data'),
                   # State('signal_table', 'selected_rows'),
                   State('buy_threshold', 'value'),
                   State('sell_threshold', 'value')]
                  )
    def historic_roi(n_clicks, start_date, end_date, ticker_input, ticker_sp500_input,
                     ticker_input_radio, data,  buy_threshold, sell_threshold):
        rules_list = []
        # for i in selected_rows:
        #     rules_list.append(data[i])
        rules_list = data

        if ticker_input_radio == "SP500":
            ticker = ticker_sp500_input
        else:
            ticker = ticker_input

        base_time = datetime.strptime(start_date[0:10], "%Y-%m-%d")
        now_time = datetime.strptime(end_date[0:10], "%Y-%m-%d")

        # Lump Sum Code
        fig, score_str, score_color, opt_score = strategy_calculations.get_historic_roi(ticker, base_time, now_time,
                                                                                        rules_list, buy_threshold, sell_threshold)

        return fig,  score_str, score_color

    @app.callback(Output('hidden-data', 'children'),
                   [Input('buy_threshold', 'value'),
                   Input('sell_threshold', 'value'),
                   Input('ticker_input', 'value'),
                   Input('ticker_sp500_input', 'value'),
                   Input('ticker_input_radio', 'value')]
                  )
    def make_hidden_data(buy_threshold, sell_threshold, ticker_input, ticker_sp500_input, ticker_input_radio):
        if not buy_threshold or not sell_threshold:
            return {}

        if ticker_input_radio == "SP500":
            ticker = ticker_sp500_input
            if not ticker:
                return {}
        else:
            ticker = ticker_input
            if not ticker:
                return {}

        hidden_dict = {
            'buy_threshold': buy_threshold,
            'sell_threshold': sell_threshold,
            'ticker': ticker
        }
        return json.dumps(hidden_dict)

    @app.callback([Output('daily-graph', 'figure'),
                   Output('ticker_alert', 'is_open')],
                  [Input('date_range', 'start_date'),
                   Input('date_range', 'end_date'),
                   Input('tabs', 'active_tab'),
                   Input('hidden-data', 'children'),
                   Input('signal_table', 'data')
                   ]
                  )
    def weekly_roi(start_date, end_date, active_tab, hidden_json, data):
        if not hidden_json or not start_date or not end_date or not active_tab or not data:
            return px.line(), False

        hidden_data = json.loads(hidden_json)
        # print(hidden_data)

        buy_threshold = hidden_data['buy_threshold']
        sell_threshold = hidden_data['sell_threshold']
        ticker = hidden_data['ticker']

        rules_list = data
        data_error = False
        for rule in rules_list:
            for key in rule:
                if rule[key] == '':
                    data_error = True
        if data_error:
            return px.line(), False

        base_time = datetime.strptime(start_date[0:10], "%Y-%m-%d")
        now_time = datetime.strptime(end_date[0:10], "%Y-%m-%d")+timedelta(days=1)
        portfolio_value = 1000

        # print(base_time, now_time)
        values_df = strategy_calculations.get_roi(ticker, base_time, now_time, rules_list, buy_threshold, sell_threshold, portfolio_value)
        if values_df.empty:
            return px.line(), False

        if active_tab == 'tab-1':
            spy_value = strategy_calculations.make_spy_graph(ticker, values_df)
            return spy_value, False
        elif active_tab == 'tab-2':
            portfolio = strategy_calculations.make_portfolio_graph(values_df, 1)
            return portfolio, False
        elif active_tab == 'tab-3':
            portfolio = strategy_calculations.make_portfolio_graph(values_df, 2)
            return portfolio, False
        else:
            return px.line(), False

    @app.callback(
        [Output('date_range', 'start_date'),
         Output('date_range', 'end_date')],
        [Input('historic_roi', 'clickData')],
        [State('date_range', 'start_date'),
         State('date_range', 'end_date')]
    )
    def change_yr(clicked_data, start_date, end_date):
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

    # @app.callback(
    #     Output('signal_table', 'data'),
    #     [Input('editing-rows-button', 'n_clicks')],
    #     [State('signal_table', 'data'),
    #      State('signal_table', 'columns')])
    # def add_row(n_clicks, rows, columns):
    #     if n_clicks:
    #         rows.append({c['id']: '' for c in columns})
    #     return rows

    @app.callback(
        [Output('save_alert', 'children'),
         Output('save_alert', 'color'),
         Output('save_alert', 'is_open')],
        [Input('save_button', 'n_clicks')],
        [State('signal_table', 'data'),
         State('signal_table', 'columns'),
         State('strategy_name', 'value'),
         State('buy_threshold', 'value'),
         State('sell_threshold', 'value'),
         State('ticker_input', 'value'),
         State('ticker_sp500_input', 'value'),
         State('ticker_input_radio', 'value'),
         ])
    def save_signals(n_clicks, rows, columns, strategy_name,
                     buy_threshold, sell_threshold, ticker_input,
                     ticker_sp500_input, ticker_input_radio):
        if ticker_input_radio == "SP500":
            ticker = ticker_sp500_input
        else:
            ticker = ticker_input

        if n_clicks:
            user_name = session.get('user_name', None)
            user = User.query.filter_by(user_name=user_name).one_or_none()
            is_strategy = Strategy.query.filter_by(user_id=user.id, name=strategy_name).one_or_none()
            if is_strategy:
                # delete all existing signals
                signal_list = Signal.query.filter_by(strategy_id=is_strategy.id).all()
                if signal_list:
                    for signal in signal_list:
                        db.session.delete(signal)
                # Add the ticker and thresholds
                is_strategy.buy_threshold = buy_threshold
                is_strategy.sell_threshold = sell_threshold
                is_strategy.stock_ticker = ticker

                # Add the new signals to the table
                for row in rows:
                    signal = Signal(strategy_id=is_strategy.id,
                                    larger_when=row['Larger: When?'],
                                    larger_what = row['Larger: What?'],
                                    smaller_when = row['Smaller: When?'],
                                    smaller_what = row['Smaller: What?'],
                                    percentage = row['Percentage'],
                                    weight = row['Weight'])
                    db.session.add(signal)
                db.session.commit()
                return "All Signals Saved to Database!", 'success', True
            return "No Signals to save", "warning", True
        return "", 'warning', False

    @app.callback(
        [Output('row_alert', 'is_open'),
         Output('row_alert', 'children')],
        [Input('editing-rows-button', 'n_clicks')]
    )
    def add_row(n_clicks):
        if n_clicks:
            return True, "Adding Row"
        return False, ""

    @app.callback(
        [Output('opt_alert', 'is_open'),
         Output('opt_alert', 'children')],
        [Input('opt_button', 'n_clicks')]
    )
    def add_row(n_clicks):
        if n_clicks:
            return True, "Optimizing Percentages..."
        return False, ""

    @app.callback(
        [Output('signal_table', 'data'),
         Output('buy_threshold', 'value'),
         Output('sell_threshold', 'value'),
         Output('ticker_input', 'value')],
        [Input('save_alert', 'children'),
         Input('strategy_name', 'value'),
         Input('row_alert', 'children'),
         Input('opt_alert', 'children')],
        [State('row_alert', 'is_open'),
         State('opt_alert', 'is_open'),
         State('signal_table', 'data'),
         State('signal_table', 'columns'),
         State('buy_threshold', 'value'),
         State('sell_threshold', 'value'),
         State('ticker_input', 'value'),
         State('optimize-type-radio', 'value'),
         State('optimize-dates', 'start_date'),
         State('optimize-dates', 'end_date'),
         ]
    )
    def get_data(save_alert, strategy_name, row_children, opt_children, is_rows, is_opt,
                 existing_data, columns, buy_threshold, sell_threshold, ticker_input,
                 optimize_type, optimize_start, optimize_end):

        if is_opt:
            now_time = datetime.strptime(optimize_end[0:10], '%Y-%m-%d')
            base_time = datetime.strptime(optimize_start[0:10], '%Y-%m-%d')
            bounds = []
            for rule in existing_data:
                lower_bound = rule['Percentage'] * 0.75
                upper_bound = rule['Percentage'] * 1.5
                bounds.append((lower_bound, upper_bound))
            goal = optimize_type
            results, performance = create_single_solutions(
                existing_data, buy_threshold, sell_threshold, ticker_input,
                base_time, now_time, bounds, goal)
            print(results)
            for i, row in enumerate(existing_data):
                row['Percentage'] = results[i]

            return existing_data, buy_threshold, sell_threshold, ticker_input

        if is_rows:
            existing_data.append({c['id']: '' for c in columns})
            return existing_data, buy_threshold, sell_threshold, ticker_input

        data = []
        user_name = session.get('user_name', None)
        user = User.query.filter_by(user_name=user_name).one_or_none()
        is_strategy = Strategy.query.filter_by(user_id=user.id, name=strategy_name).one_or_none()
        if is_strategy:
            signal_list = Signal.query.filter_by(strategy_id=is_strategy.id).all()
            if signal_list:
                for signal in signal_list:
                    data.append({'Larger: When?': signal.larger_when,
                                 'Larger: What?': signal.larger_what,
                                 'Smaller: When?': signal.smaller_when,
                                 'Smaller: What?': signal.smaller_what,
                                 'Percentage': signal.percentage,
                                'Weight': signal.weight})
                buy_threshold = is_strategy.buy_threshold
                sell_threshold = is_strategy.sell_threshold
                ticker_input = is_strategy.stock_ticker
            return data, buy_threshold, sell_threshold, ticker_input

        return data, buy_threshold, sell_threshold, ticker_input
