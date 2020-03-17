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
    from . import dash_layouts

    external_stylesheets = [dbc.themes.BOOTSTRAP]

    app = dash.Dash(__name__,
                    server=server,
                    url_base_pathname='/dash/portfolio/',
                    external_stylesheets=external_stylesheets,
                    suppress_callback_exceptions=True)

    protect_dash_route(app)
    app.layout = html.Div([
        dcc.Location(id='url', refresh=False, pathname='/manage/'),
        html.Div(id='page_content')
    ])

    #TODO:  Make the chosen portfolio part of the header...header div does not change.
    @app.callback(Output('portfolio_graph', 'figure'),
                  [Input('security_input', 'value')])
    def update_graph(security_list):
        if not security_list:
            return px.line()
        ticker_list = []
        start_dates = []
        value_list = []
        for security in security_list:
            stock_info = security.split(", ")
            print(stock_info)
            ticker_list.append(stock_info[0])
            start_dates.append(stock_info[1])
            value_list.append(stock_info[2])
        print(start_dates)
        now_time = datetime.strftime(datetime.now(), '%Y-%m-%d')
        security_graph = stock_calculations.plot_stocks(ticker_list, value_list, start_dates[-1], now_time)
        return security_graph

    @app.callback(Output('portfolio_entries', 'data'),
                  [Input('portfolio_input', 'value')])
    def update_list(portfolio_name):
        print(portfolio_name)
        from trades.models import User, Trade, Portfolio
        if not portfolio_name:
            return []
        user_name = session.get('user_name', None)
        user = User.query.filter_by(user_name=user_name).one_or_none()
        portfolio = Portfolio.query.filter_by(user_id = user.id, name=portfolio_name).one_or_none()
        trades = Trade.query.filter_by(portfolio_id = portfolio.id).all()
        data = []
        for trade in trades:
            data.append({'portfolio': portfolio.name,
                         'security': trade.security,
                         'value': trade.value,
                         'purchase_date': datetime.strftime(trade.purchase_date, '%Y-%m-%d')})

        return data

    @app.callback([Output('manage_alert', 'children'),
                   Output('manage_alert', 'color')],
                  [Input('submit_input', 'n_clicks')],
                  [State('portfolio_input', 'value'),
                   State('security_input', 'value'),
                   State('value_input', 'value'),
                   State('purchase_date_input', 'date')])
    def add_to_portfolio(_, portfolio, security, value, purchase_date):
        from trades.models import User, Trade, Portfolio
        if not portfolio or not security or not value or not purchase_date:
            return "All fields must be filled in", "danger"

        print(purchase_date)
        purchase_datetime = datetime.strptime(purchase_date,'%Y-%m-%d')
        print(purchase_datetime)
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

        print(name)
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
        trade_list = []
        if user:
            portfolio_list = Portfolio.query.filter_by(user_id = user.id).all()
        # data = []
        # for trade in trade_list:
        #     data.append({'user': trade.user_id,
        #                  'security': trade.security,
        #                  'value': trade.value,
        #                  'purchase_date': datetime.strftime(trade.purchase_date, '%Y-%m-%d')})

        if pathname == "/manage/":
            return dash_layouts.make_manage_layout("Manage Portfolio", portfolio_list)
        elif pathname == "/list/":
            return dash_layouts.make_list_layout("List Portfolio", portfolio_list)
        elif pathname == '/graph/':
            return dash_layouts.make_graph_layout('Graph Portfolio', portfolio_list)
        elif pathname == '/create/':
            return dash_layouts.make_create_layout("Create Portfolio")


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
