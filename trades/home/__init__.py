from dash import dash
from flask import session
from trades import db
from trades.models import User, Trade, Portfolio, Dollar

import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input, State


from trades.portfolio import manual_layouts


def get_dashboard_layout(content_div):

    view_portfolio_div = html.Div([
        dbc.Row([
            dbc.Col([
                content_div
            ],
                style={'display': 'flex', 'justify-content': 'center'})
        ])
    ])

    return view_portfolio_div


def make_about_layout():

    jumbotron = dbc.Jumbotron(
        [
            html.H1("Ryan Sanders", className='display-3'),
            html.P(
                "I am a data scientist who likes to find"
                " creative ways to collect and visualize data.  "
                "I use this website to explore and demonstrate new technologies.  Most recently "
                "I have been exploring the google cloud (GC) Machine Learning APIs ",
                className="lead",
            ),
        ]
    )

    algo_rhythm = dbc.Card([
        html.A(
            dbc.CardBody([
                html.H4("Algo-Rhythm", className='card-title'),
                html.P("Basic data science toolbox for trading stocks.  ", className='card-text')

            ]), href='http://algo-rhythm.money', target='_blank'
        )
    ], color='primary', inverse=True)

    handwriting = dbc.Card([
        html.A(
            dbc.CardBody([
                html.H4("Handwriting Parser", className='card-title'),
                html.P("Send images of handwriting to Google API for interpretation.  ", className='card-text')

            ]), href='/handwriting/', target='_blank'
        )
    ], color='primary', inverse=True)

    portfolio_tracker = dbc.Card([
        html.A(
            dbc.CardBody([
                html.H4("Portfolio Tracker", className='card-title'),
                html.P("Simple toolbox for visualizing multiple portfolios.  ",
                       className='card-text')

            ]), href='/portfolio/', target='_blank'
        ),
    ], color='primary', inverse=True)

    about_layout = html.Div([
        dbc.Row([
            dbc.Col([
                jumbotron
            ])
        ]),
        dbc.Row([
            dbc.Col([
                handwriting
            ])
        ],style = {"margin": "25px"}),
        # dbc.Row([
        #     dbc.Col([
        #         portfolio_tracker
        #     ])
        # ],style = {"margin": "25px"})
    ])

    return about_layout


def register_home_dashapp(server):
    external_stylesheets = [dbc.themes.FLATLY]

    app = dash.Dash(__name__,
                    server=server,
                    url_base_pathname='/dash/home/',
                    external_stylesheets=external_stylesheets)

    app.layout = html.Div([
        make_about_layout()
        ])

