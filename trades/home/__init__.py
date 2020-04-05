from dash import dash

import dash_html_components as html
import dash_bootstrap_components as dbc


def register_home_dashapp(server):
    external_stylesheets = [dbc.themes.LUX]

    app = dash.Dash(__name__,
                    server=server,
                    url_base_pathname='/dash/home/',
                    external_stylesheets=external_stylesheets)

    photo_card = dbc.Card(
        [
            dbc.CardImg(src="/static/images/IMG_0590.JPG", top=True),
            dbc.CardBody(
                [
                    html.H4("Photography", className="card-title"),
                    html.P("View Photographs", className="card-text"),
                    dbc.Button("Photos", color="primary", href='/photography', external_link=True, target='_top'),
                ]
            ),
        ],
        style={"margin-right": "5px", "margin-left": "5px"},
    )

    travel_card = dbc.Card(
        [
            dbc.CardImg(src="/static/images/IMG_0589.JPG", top=True),
            dbc.CardBody(
                [
                    html.H4("Travels", className="card-title"),
                    html.P("View Travel Log", className="card-text"),
                    dbc.Button("Travel Log", color="primary", href='/travel', external_link=True, target='_top'),
                ]
            ),
        ],
        style={"margin-right": "5px", "margin-left": "5px"},
    )

    stock_card = dbc.Card(
        [
            dbc.CardImg(src="/static/images/Stocks5.png", top=True),
            dbc.CardBody(
                [
                    html.H4("Stocks", className="card-title"),
                    html.P("View Stock Analytics", className="card-text"),
                    dbc.Button("Analytics", color="primary", href='/stocks', external_link = True, target='_top'),
                ]
            ),
        ],
        style={"margin-right": "5px", "margin-left": "5px"},
    )

    home_cards = dbc.CardGroup([
                photo_card,
                travel_card,
                stock_card,
    ])

    app.layout = html.Div([
        home_cards,
        html.A(id='name', style={'display': 'None'})
    ])
