import os
from datetime import datetime

from dash import dash
from dash.dependencies import Output, Input, State
from flask import Flask, session
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import plotly.express as px

import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from trades import stock_calculations

db = SQLAlchemy()
migrate = Migrate()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DB_URI= 'sqlite:///'+os.path.join(PROJECT_ROOT, 'instance', 'test.db')
print(DB_URI)


# Implement the app factory
def create_app():
    # Create the flask app
    server = Flask(__name__, instance_relative_config=False)
    server.config.from_mapping(
        SECRET_KEY = 'dev',
        SQLALCHEMY_DATABASE_URI = DB_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS = False

    )

    from . import models

    db.init_app(server)
    migrate.init_app(server, db)

    from . import routes

    server.register_blueprint(routes.bp)

    register_portfolio_dashapp(server)

    return server


def register_portfolio_dashapp(server):
    # Add in the ability to visualize the sell date
    # Add in a plot of money added to the portfolio
    # Add in a way to specify if the purchase is from the portfolio or from cash
    # Add in USD to keep track of cash in and out of portfolio
    # Add in a way to track the total invested and total gains taken
    # Add in the ability to delete purchases or sales
    # Add in a way to track dividend payments
    from . import dash_layouts

    external_stylesheets = [dbc.themes.BOOTSTRAP]

    app = dash.Dash(__name__,
                    server=server,
                    url_base_pathname='/dash/portfolio/',
                    external_stylesheets=external_stylesheets,
                    suppress_callback_exceptions=True)

    protect_dash_route(app)
    app.layout = html.Div([
        dcc.Location(id='url', refresh=False, pathname='/visualize/'),
        html.Div(id='page_content')
    ])

    @app.callback(Output('security_input', 'options'),
                   [Input('portfolio_input', 'value')])
    def update_company_dd(portfolio_name):
        from trades.models import User, Trade, Portfolio
        if not portfolio_name:
            return []
        user_name = session.get('user_name', None)
        user = User.query.filter_by(user_name=user_name).one_or_none()
        portfolio = Portfolio.query.filter_by(user_id=user.id, name=portfolio_name).one_or_none()
        trades = Trade.query.filter_by(portfolio_id=portfolio.id).all()
        security_options = []
        for stock in trades:
            stock_string = stock.security + ", " + datetime.strftime(stock.purchase_date, '%Y-%m-%d') + ", " + str(stock.value)
            security_options.append({'label': stock_string, 'value': stock_string})

        return security_options

    # TODO:  Make the chosen portfolio part of the header...header div does not change.
    @app.callback(Output('portfolio_graph', 'figure'),
                  [Input('portfolio_entries', 'data'),
                   Input('portfolio_entries', 'selected_rows')])
    def update_graph( data, selected_rows):
        if not selected_rows:
            return px.line()
        print(selected_rows)
        ticker_list = []
        start_dates = []
        value_list = []
        for row in selected_rows:
            ticker_list.append(data[row]['security'])
            start_dates.append(data[row]['purchase_date'])
            value_list.append(data[row]['value'])
        now_time = datetime.strftime(datetime.now(), '%Y-%m-%d')

        security_graph = stock_calculations.plot_stocks(ticker_list, value_list, start_dates, now_time)
        return security_graph

    @app.callback(Output('portfolio_entries', 'data'),
                  [Input('portfolio_input', 'value'),
                   Input('sell_alert', 'children')])
    def update_list(portfolio_name, _):
        print(portfolio_name)
        from trades.models import User, Trade, Portfolio
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
            data.append({'id': trade.id,
                         'portfolio': portfolio.name,
                         'security': trade.security,
                         'value': trade.value,
                         'purchase_date': datetime.strftime(trade.purchase_date, '%Y-%m-%d'),
                         'sell_date': sell_date
                         })

        return data

    @app.callback([Output('manage_alert', 'children'),
                   Output('manage_alert', 'color')],
                  [Input('submit_input', 'n_clicks')],
                  [State('portfolio_input', 'value'),
                   State('manage_security_input', 'value'),
                   State('value_input', 'value'),
                   State('purchase_date_input', 'date')])
    def add_to_portfolio(_, portfolio, security, value, purchase_date):
        from trades.models import User, Trade, Portfolio
        if not portfolio or not security or not value or not purchase_date:
            return "All fields must be filled in", "danger"
        purchase_datetime = datetime.strptime(purchase_date, '%Y-%m-%d')
        user_name = session.get('user_name', None)
        user = User.query.filter_by(user_name=user_name).one_or_none()
        portfolio = Portfolio.query.filter_by(user_id = user.id, name=portfolio).one_or_none()
        trade = Trade(portfolio_id = portfolio.id,
                      security=security,
                      value=value,
                      purchase_date = purchase_datetime)
        db.session.add(trade)
        db.session.commit()
        return "Portfolio Updated", "success"

    @app.callback([Output('create_alert', 'children'),
                   Output('create_alert', 'color')],
                  [Input('create_input', 'n_clicks')],
                  [State('name_input', 'value'),
                   State('strategy_input', 'value')])
    def create_portfolio(_, name, strategy):
        from trades.models import User, Trade, Portfolio
        if not name or not strategy:
            return "All fields must be filled in", "danger"

        user_name = session.get('user_name', None)
        user = User.query.filter_by(user_name=user_name).one_or_none()
        portfolio = Portfolio(
            user_id=user.id,
            name=name,
            strategy = strategy)
        db.session.add(portfolio)
        db.session.commit()
        return "Portfolio Updated", "success"

    @app.callback(Output('page_content', 'children'),
                  [Input('url', 'pathname')])
    def display_page(pathname):
        from trades.models import User, Trade, Portfolio

        user_name = session.get('user_name', None)
        user = User.query.filter_by(user_name=user_name).one_or_none()
        portfolio_list = []
        if user:
            portfolio_list = Portfolio.query.filter_by(user_id = user.id).all()

        print(pathname)

        if pathname == "/purchase/":
            return dash_layouts.make_manage_layout("Purchase Securities", portfolio_list)
        elif pathname == "/sell/":
            return dash_layouts.make_sell_layout("Sell Securities", portfolio_list)
        elif pathname == '/visualize/':
            return dash_layouts.make_graph_layout('Visualize Portfolio', portfolio_list)
        elif pathname == '/create/':
            return dash_layouts.make_create_layout("Create Portfolio")

    @app.callback([Output('sell_alert', 'children'),
                   Output('sell_alert', 'color')],
                  [Input('sell_input', 'n_clicks'),
                   Input('delete_input', 'n_clicks')],
                  [State('sell_input', 'n_clicks_timestamp'),
                   State('delete_input', 'n_clicks_timestamp'),
                      State('sell_date', 'date'),
                   State('portfolio_entries', 'data'),
                   State('portfolio_entries', 'selected_rows')])
    def update_sell_list(n_input, n_delete, input_time, delete_time, sell_date, data, selected_rows):
        from trades.models import User, Trade, Portfolio
        if n_delete:
            if not input_time or delete_time > input_time:
                if selected_rows is None:
                    return "Select a row to delete", "danger"

                sell_row = data[selected_rows[0]]
                trade = Trade.query.filter_by(id=sell_row['id']).one_or_none()
                db.session.delete(trade)
                db.session.commit()
                return "Entry Deleted", "success"

        if sell_date is None:
            return "Select a date of sale", "danger"

        if datetime.strptime(sell_date, '%Y-%m-%d') > datetime.now():
            return "Sell date cannot be in the future", "danger"

        if selected_rows is None:
            return "Select a row to sell", "danger"

        sell_row = data[selected_rows[0]]

        if sell_row['purchase_date'] >= sell_date:
            return "The sell date must be after the purchase date", "danger"

        trade = Trade.query.filter_by(id=sell_row['id']).one_or_none()

        if trade.sell_date is not None:
            return "The Stock has already been sold", "danger"

        trade.sell_date = datetime.strptime(sell_date, '%Y-%m-%d')
        db.session.commit()

        return "Stock Sold", "success"


# def register_dashapp2(server):
#     external_stylesheets = [dbc.themes.BOOTSTRAP]
#
#     app = dash.Dash(__name__,
#                     server=server,
#                     url_base_pathname='/dash/home/',
#                     external_stylesheets=external_stylesheets)
#
#     protect_dash_route(app)
#     app.layout = html.Div([
#         html.A(id='welcome', children="Nice Stock Graph  "),
#         html.A(id='name')
#     ])
#
#     @app.callback(
#         Output('name', 'children'),
#         [Input('welcome', 'children')]
#     )
#     def get_names(_):
#         user_name = session.get('user_name', None)
#         return user_name


def protect_dash_route(app):
    from trades.routes import login_required

    for view_func in app.server.view_functions:
        if view_func.startswith(app.config.url_base_pathname):
            app.server.view_functions[view_func] = login_required(app.server.view_functions[view_func])
