import dash
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input, State
import dash_core_components as dcc
from flask import Blueprint

bp = Blueprint('auth', __name__, url_prefix='/auth/')


def create_login_app(server):

    login_app = dash.Dash(__name__,
                          server=server,
                          url_base_pathname='/auth/login/',
                          external_stylesheets=[dbc.themes.BOOTSTRAP])
    # Create the dash layout with Flask's "current_app"
    with server.app_context():
        navbar = navbar_layout()
        content_div = login_layout({'id': 'login', 'nice_name': "Login"})
        main_layout = make_global_layout(navbar, content_div)
        login_app.layout = main_layout

        # @login_app.callback(Output("location_div", "children"),
        #                     [Input('register', 'n_clicks')])
        # def register_user(n_clicks):
        #     return dcc.Location(id='force_refresh')

    return login_app


def create_register_app(server):
    register_app = dash.Dash(__name__,
                             server=server,
                             url_base_pathname='/auth/register/',
                             external_stylesheets=[dbc.themes.BOOTSTRAP])
    # Create the dash layout with Flask's "current_app"
    with server.app_context():
        navbar = navbar_layout()
        content_div = login_layout({'id': 'register', 'nice_name': "Register"})
        main_layout = make_global_layout(navbar, content_div)
        register_app.layout = main_layout

    return register_app


def navbar_layout():
    navbar = dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Login", href="/auth/login", external_link=True)),
            dbc.NavItem(dbc.NavLink("Register", href="/auth/register", external_link=True))],
        brand="Stock Trades",
        brand_href="#",
        color="primary",
        dark=True,
    )
    return navbar


def make_global_layout(navbar, content_div):
    global_layout = html.Div([
        dbc.Row(
            dbc.Col(navbar)
        ),
        dbc.Row([
            dbc.Col(width=1),
            dbc.Col(content_div, style={"marginTop": 25}),
            dbc.Col(width=1)
        ]),
        dbc.Row(
            dbc.Col(html.Div(id='location_div', style={'display': 'None'}))
        )
    ]
    )
    return global_layout


def login_layout(button_dict):
    user_name = dbc.FormGroup(
        [
            dbc.Label("User E-Mail"),
            dbc.Input(type="email",
                      id="user_name",
                      placeholder="Enter email"),
            dbc.FormText(
                "Please enter your e-mail",
                color="secondary",
            ),
        ]
    )

    password_input = dbc.FormGroup(
        [
            dbc.Label("Password"),
            dbc.Input(
                type="password",
                id="password",
                placeholder="Enter password",
            ),
            dbc.FormText(
                "Enter your password, or if you do not yet have an account go to the register page",
                color="secondary"
            ),
        ]
    )

    login_button = dbc.FormGroup(
        dbc.Button(button_dict['nice_name'], id=button_dict['id'])
    )

    form = dbc.Form([user_name, password_input, login_button])
    return form
