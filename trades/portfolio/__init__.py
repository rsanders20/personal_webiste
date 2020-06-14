from datetime import datetime, timedelta

from dash import dash
from dash.dependencies import Output, Input, State
from flask import session
import plotly.express as px

import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from trades import db
from trades.portfolio import manual_layouts, stock_calculations
from trades.models import User, Trade, Portfolio, Dollar

from trades import protect_dash_route
from trades.strategy import strategy_calculations


def get_portfolios():
    user_name = session.get('user_name', None)
    user = User.query.filter_by(user_name=user_name).one_or_none()
    portfolio_list = []
    if user:
        portfolio_list = Portfolio.query.filter_by(user_id=user.id).all()

    return portfolio_list


def register_manual(server):
    # TODO:  For next release
        # 7) Add custom dropdown for stocks in portfolio page
    # TODO: For Next Release
    #  Figure out the concat error that sometimes happen at the end of optimize
    #  Add a footer, with copyright protection.
    #  Add in more than just the moving averages...alpha, beta, theta, etc.

    custom_css = r'/static/css/custom.css'
    external_stylesheets = [dbc.themes.FLATLY, custom_css]

    app = dash.Dash(__name__,
                    server=server,
                    url_base_pathname='/dash/portfolio/',
                    external_stylesheets=external_stylesheets,
                    suppress_callback_exceptions=True)

    protect_dash_route(app)

    page_nav = manual_layouts.make_navbar_view()

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
            return manual_layouts.make_manual_dashboard()

    @app.callback([Output('portfolio_input', 'options'),
                   Output('stock_navbar', 'brand'),
                   Output('portfolio_input', 'value')],
                  [Input('url', 'pathname'),
                   Input('delete-portfolio-alert', 'children'),
                   Input('new-portfolio-alert', 'children')
                   ])
    def display_nav(pathname, del_alert, new_alert):
        portfolio_list = get_portfolios()
        brand_name = "Portfolio"
        if portfolio_list:
            print("list is not empty", portfolio_list)
            options = [{'label': i.name, 'value': i.name} for i in portfolio_list]
            return options, brand_name, portfolio_list[-1].name
        else:
            print("list is empty")
            return [], brand_name, ""

    @app.callback(
        Output('daily-graph', 'figure'),
        [Input('portfolio_input', 'value'),
         Input('tabs', 'active_tab'),
         Input('portfolio_entries', 'selected_rows'),
         Input('portfolio_entries', 'data')]
    )
    def update_total_graph(portfolio_name, active_tab, rows, data):
        if not portfolio_name:
            return px.line()
        if not data:
            return px.line()
        user_name = session.get('user_name', None)
        user = User.query.filter_by(user_name=user_name).one_or_none()
        portfolio = Portfolio.query.filter_by(user_id=user.id, name=portfolio_name).one_or_none()
        all_trades = Trade.query.filter_by(portfolio_id=portfolio.id).all()
        i_graph, t_graph, r_graph = stock_calculations.plot_stocks(user, all_trades)

        i_graph.update_layout(yaxis=dict(title='Individual Closing Value ($)'),
                              margin=dict(r=0, l=0, b=0, t=66), paper_bgcolor='#f9f9f9',
                              title="Individual Closing Values")
        t_graph.update_layout(yaxis=dict(title='Total Portfolio Closing Value ($)'),
                              margin=dict(r=0, l=0, b=0, t=66), paper_bgcolor='#f9f9f9',
                              title="Total Portfolio Closing Daily Value")
        r_graph.update_layout(yaxis=dict(title='Return on Investment (ROI)'),
                              margin=dict(r=0, l=0, b=0, t=66), paper_bgcolor='#f9f9f9',
                              title="Total Portfolio Returns (ROI)")

        if active_tab == 'tab-1':
            return i_graph
        elif active_tab == 'tab-2':
            if rows:
                row_dict = data[rows[0]]
                ticker = row_dict['security']
                row_data = {'Name': row_dict['security'],
                            'Value': row_dict['purchase_value'],
                            'Strategy': row_dict['strategy'],
                            'Start Date': row_dict['purchase_date']}
                values_df = strategy_calculations.get_values_df(row_data, user)
                trading_decisions_graph = strategy_calculations.make_spy_graph(ticker, values_df)
                return trading_decisions_graph
            return px.line(title='Select a Stock to View Automatic Trading Decisions')
        elif active_tab == 'tab-3':
            return t_graph
        elif active_tab == 'tab-4':
            return r_graph
        else:
            return px.line()

    @app.callback(Output('portfolio_entries', 'data'),
                  [Input('portfolio_input', 'value'),
                   Input('sell_alert', 'children'),
                   Input('purchase_alert', 'children'),
                   Input('delete_alert', 'children'),
                   Input('strategy_alert', 'children')])
    def update_sell_list(portfolio_name, n_sell, n_purchase, n_del, n_strat):
        print(portfolio_name)
        if not portfolio_name:
            return []
        user_name = session.get('user_name', None)
        user = User.query.filter_by(user_name=user_name).one_or_none()
        portfolio = Portfolio.query.filter_by(user_id=user.id, name=portfolio_name).one_or_none()
        trades = Trade.query.filter_by(portfolio_id=portfolio.id).all()
        data = []
        for trade in trades:
            if trade.sell_date:
                sell_date = datetime.strftime(trade.sell_date, '%Y-%m-%d')
            else:
                sell_date = None

            if trade.sell_value:
                sell_value = trade.sell_value
            else:
                sell_value = None

            data.append({'id': trade.id,
                         'portfolio': portfolio.name,
                         'security': trade.security,
                         'purchase_value': trade.purchase_value,
                         'purchase_date': datetime.strftime(trade.purchase_date, '%Y-%m-%d'),
                         'purchase_internal': trade.purchase_internal,
                         'sell_date': sell_date,
                         'sell_value': sell_value,
                         'strategy': trade.strategy
                         })

        return data

    @app.callback([Output('purchase_alert', 'children'),
                   Output('purchase_alert', 'color'),
                   Output('purchase_alert', 'is_open')],
                  [Input('submit_input', 'n_clicks')],
                  [State('portfolio_input', 'value'),
                   State('ticker_input', 'value'),
                   State('ticker_input_radio', 'value'),
                   State('ticker_sp500_input', 'value'),
                   State('value_input', 'value'),
                   State('purchase_date_input', 'date'),
                   State('source_input', 'value')])
    def add_to_portfolio(_, portfolio, ticker_input, ticker_input_radio, ticker_sp500_input, value, purchase_date, source):
        if ticker_input_radio == "SP500":
            ticker = ticker_sp500_input
        else:
            ticker = ticker_input

        if not portfolio or not ticker or not value or not purchase_date:
            return "All fields must be filled in", "danger", True
        purchase_datetime = datetime.strptime(purchase_date, '%Y-%m-%d')
        user_name = session.get('user_name', None)
        user = User.query.filter_by(user_name=user_name).one_or_none()
        portfolio = Portfolio.query.filter_by(user_id = user.id, name=portfolio).one_or_none()

        purchase_internal = False
        if source == 'External Funds':
            purchase_internal = False
        elif source == 'Internal Funds':
            purchase_internal = True
            all_trades = Trade.query.filter_by(portfolio_id=portfolio.id).all()
            # all_cash = Dollar.query.filter_by(portfolio_id=portfolio.id).all()
            if not all_trades:
                return "No cash is currently in the portfolio.  Sell portfolio or add more", "danger", True

            cash = 0
            for trade in all_trades:
                if trade.sell_date:
                    if trade.sell_date <= purchase_datetime:
                        cash += trade.sell_value
                if trade.purchase_date <= purchase_datetime:
                    if trade.purchase_internal:
                        cash += -1 * trade.purchase_value

            print(cash)
            if cash < value:
                return "Only ${:.2f} cash.  Please add more funds.".format(cash), "danger", True

        trade = Trade(portfolio_id=portfolio.id,
                      security=ticker,
                      purchase_value=value,
                      purchase_date=purchase_datetime,
                      purchase_internal=purchase_internal)
        db.session.add(trade)
        db.session.commit()
        return "Portfolio Updated", "success", True

    @app.callback([Output('delete_alert', 'children'),
                   Output('delete_alert', 'color'),
                   Output('delete_alert', 'is_open')],
                  [Input('delete_input', 'n_clicks')],
                  [State('portfolio_entries', 'data'),
                   State('portfolio_entries', 'selected_rows'),
                   State('portfolio_input', 'value')])
    def delete_from_portfolio(n_input, data, selected_rows, portfolio_name):

        if selected_rows is None:
            return "Select a row to delete", "danger", True

        del_row = data[selected_rows[0]]

        trade = Trade.query.filter_by(id=del_row['id']).one_or_none()
        db.session.delete(trade)
        db.session.commit()
        return "Trade Deleted", "success", True

    @app.callback([Output('sell_alert', 'children'),
                   Output('sell_alert', 'color'),
                   Output('sell_alert','is_open')],
                  [Input('sell_input', 'n_clicks')],
                  [State('sell_date', 'date'),
                   State('portfolio_entries', 'data'),
                   State('portfolio_entries', 'selected_rows'),
                   State('portfolio_input', 'value')])
    def sell_from_portfolio(n_input, sell_date, data, selected_rows, portfolio_name):

        if sell_date is None:
            return "Select a date of sale", "danger", True

        if datetime.strptime(sell_date, '%Y-%m-%d') > datetime.now():
            return "Sell date cannot be in the future", "danger", True

        if selected_rows is None:
            return "Select a row to sell", "danger", True

        sell_row = data[selected_rows[0]]

        if sell_row['purchase_date'] >= sell_date:
            return "The sell date must be after the purchase date", "danger", True

        trade = Trade.query.filter_by(id=sell_row['id']).one_or_none()

        if trade.sell_date is not None:
            return "The Stock has already been sold", "danger", True

        trade.sell_date = datetime.strptime(sell_date, '%Y-%m-%d')

        df = stock_calculations.get_yahoo_stock_data([trade.security], trade.purchase_date, trade.sell_date+timedelta(days=1))
        print(df)
        value_factor = float(trade.purchase_value) / df['Close'][0]
        sell_value = df['Close'][-1] * value_factor

        trade.sell_value = sell_value
        print(sell_value)

        db.session.commit()
        return "Stock Sold", "success", True

    @app.callback([Output('strategy_alert', 'children'),
                   Output('strategy_alert', 'color'),
                   Output('strategy_alert', 'is_open')],
                  [Input('strategy_input', 'n_clicks')],
                  [State('strategy_dropdown', 'value'),
                   State('portfolio_entries', 'data'),
                   State('portfolio_entries', 'selected_rows')]
                  )
    def update_strategy(n_input, strategy, data, selected_rows):

        if selected_rows is None:
            return "Select a row to Update the Strategy", "danger", True

        sell_row = data[selected_rows[0]]
        if sell_row['purchase_internal']:
            return "Strategies can only track stocks purchased with external funds", "danger", True
        trade = Trade.query.filter_by(id=sell_row['id']).one_or_none()
        trade.strategy = strategy
        db.session.commit()
        return "Strategy Updated", "success", True

    @app.callback([Output('delete-portfolio-alert', 'children'),
                   Output('delete-portfolio-alert', 'color'),
                   Output('delete-portfolio-alert', 'is_open')],
                  [Input('delete-portfolio-button', 'n_clicks')],
                  [State('portfolio_input', 'value')]
                  )
    def delete_portfolio(n_clicks, portfolio_name):
        if n_clicks:
            if portfolio_name is None:
                return "Select a portfolio to delete", "danger", True

            user_name = session.get('user_name', None)
            user = User.query.filter_by(user_name=user_name).one_or_none()
            is_portfolio = Portfolio.query.filter_by(user_id=user.id, name=portfolio_name).one_or_none()
            if is_portfolio:
                # delete all existing trades
                trades_list = Trade.query.filter_by(portfolio_id=is_portfolio.id).all()
                if trades_list:
                    for trade in trades_list:
                        db.session.delete(trade)
                db.session.delete(is_portfolio)
                db.session.commit()
                return "Portfolio Removed!", "success", True
            return "Portfolio Not Found", "danger", True
        return "", "danger", False

    @app.callback([Output('new-portfolio-alert', 'children'),
                   Output('new-portfolio-alert', 'color'),
                   Output('new-portfolio-alert', 'is_open')],
                  [Input('new-portfolio-button', 'n_clicks')],
                  [State('new-portfolio-input', 'value')])
    def create_portfolio(_, name):
        if not _:
            return "", "danger", False

        user_name = session.get('user_name', None)
        user = User.query.filter_by(user_name=user_name).one_or_none()
        is_portfolio = Portfolio.query.filter_by(user_id= user.id, name=name).one_or_none()
        if is_portfolio:
            return "Please select a new Portfolio Name.  This one already exists.", "danger", True

        portfolio = Portfolio(
            user_id=user.id,
            name=name)
        db.session.add(portfolio)
        db.session.commit()
        return "Portfolio Created!", "success", True

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
