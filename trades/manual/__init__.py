from datetime import datetime, timedelta

from dash import dash
from dash.dependencies import Output, Input, State
from flask import session
import plotly.express as px

import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from trades import db
from trades.manual import manual_layouts, stock_calculations
from trades.models import User, Trade, Portfolio, Dollar

from trades import protect_dash_route
from trades.strategy import strategy_calculations


def get_manual_portfolios():
    user_name = session.get('user_name', None)
    user = User.query.filter_by(user_name=user_name).one_or_none()
    portfolio_list = []
    if user:
        portfolio_list = Portfolio.query.filter_by(user_id=user.id, strategy='Manual').all()

    return portfolio_list


def register_manual(server):
    # TODO:  Before Release:
        # 1)  Handle the zero and 1 stock case elegantly
            #) Enforce that internal trades are kept with "blank" strategy.
        # 2)  Add titles to all of the manual graphs
        # 3)  Rename Manual to just "portfolio"
        # 4)  Remove reference to "strategy" on the home page
            # clean up the code that is no longer used
    # TODO:  For next release
        # 5)  Put all of the strategy graphs on a tab.
            #  Make the historic alert part of the graph title
        # 6) Remove the optimize button from this release
        # 7) Consider removing "get data" method.
    # TODO:  Add vanguard funds, VWX, VIX, VTSAX  (Add custom dropdown)
    # TODO:  Add a footer, with copyright protection.
    # TODO:  Add in more than just the moving averages...alpha, beta, theta, etc.


    custom_css = r'/static/css/custom.css'
    external_stylesheets = [dbc.themes.FLATLY, custom_css]

    app = dash.Dash(__name__,
                    server=server,
                    url_base_pathname='/dash/manual/',
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
        portfolio_list = get_manual_portfolios()

        if pathname == "/purchase/":
            return manual_layouts.make_manual_dashboard(portfolio_list)

    @app.callback([Output('portfolio_input', 'options'),
                   Output('stock_navbar', 'brand'),
                   Output('portfolio_input', 'value')],
                  [Input('url', 'pathname')])
    def display_nav(pathname):
        portfolio_list = get_manual_portfolios()
        options = [{'label': i.name, 'value': i.name} for i in portfolio_list]
        brand_name = "Manual Portfolio"
        return options, brand_name, portfolio_list[-1].name

    # @app.callback(Output('security_input', 'options'),
    #                [Input('portfolio_input', 'value')])
    # def update_company_dd(portfolio_name):
    #     if not portfolio_name:
    #         return []
    #     user_name = session.get('user_name', None)
    #     user = User.query.filter_by(user_name=user_name).one_or_none()
    #     portfolio = Portfolio.query.filter_by(user_id=user.id, name=portfolio_name).one_or_none()
    #     trades = Trade.query.filter_by(portfolio_id=portfolio.id).all()
    #     security_options = []
    #     for stock in trades:
    #         stock_string = stock.security + ", " + datetime.strftime(stock.purchase_date, '%Y-%m-%d') + ", " + str(stock.value)
    #         security_options.append({'label': stock_string, 'value': stock_string})
    #
    #     return security_options

    # @app.callback(Output('portfolio_graph', 'figure'),
    #               [Input('manage_security_input', 'value'),
    #                Input('purchase_date_input', 'date')]
    #               )
    # def update_individual_graph(company_name, purchase_date):
    #     now_time = datetime.now()
    #     if not purchase_date:
    #         start_dates = []
    #     else:
    #         print(purchase_date)
    #         start_dates = [purchase_date]
    #         # start_dates = []
    #     print(start_dates)
    #     ticker_list = [company_name]
    #     sell_dates = [datetime.strftime(now_time, '%Y-%m-%d')]
    #
    #     security_graph = stock_calculations.plot_individual_stocks(ticker_list, start_dates, sell_dates)
    #     security_graph.update_layout(xaxis=dict(title='Date'),
    #                                  yaxis=dict(title='Closing Value ($)'),
    #                                  margin=dict(t=0, b=0),
    #                                  paper_bgcolor='#f9f9f9')
    #     return security_graph

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

        i_graph.update_layout(yaxis=dict(title='Individual Closing Value ($)'))
        t_graph.update_layout(yaxis=dict(title='Total Portfolio Closing Value ($)'))
        r_graph.update_layout(yaxis=dict(title='Return on Investment (ROI)'))

        i_graph.update_layout(margin=dict(r=0, l=0, b=0), paper_bgcolor='#f9f9f9')
        r_graph.update_layout(margin=dict(r=0, l=0, b=0), paper_bgcolor='#f9f9f9')
        t_graph.update_layout(margin=dict(r=0, l=0, b=0), paper_bgcolor='#f9f9f9')
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
                   State('manage_security_input', 'value'),
                   State('value_input', 'value'),
                   State('purchase_date_input', 'date'),
                   State('source_input', 'value')])
    def add_to_portfolio(_, portfolio, security, value, purchase_date, source):
        if not portfolio or not security or not value or not purchase_date:
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
                return "No cash is currently in the portfolio.  Sell manual or add more", "danger", True

            cash = 0
            for trade in all_trades:
                if trade.sell_date:
                    if trade.sell_date <= purchase_datetime:
                        cash += trade.sell_value
                if trade.purchase_date <= purchase_datetime:
                    if trade.purchase_internal:
                        cash += -1 * trade.purchase_value

            if cash < value:
                return "Only ${:.2f} cash.  Please add more funds.".format(cash), "danger", True

        trade = Trade(portfolio_id=portfolio.id,
                      security=security,
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
        trade = Trade.query.filter_by(id=sell_row['id']).one_or_none()
        trade.strategy = strategy
        db.session.commit()
        return "Strategy Updated", "success", True

