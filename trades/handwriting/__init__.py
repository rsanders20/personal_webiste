from dash import dash

import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

from dash.dependencies import Output, Input, State

import base64
import io
import binascii

from . import detect_handwriting


def register_handwriting_dashapp(server):
    external_stylesheets = [dbc.themes.FLATLY]

    app = dash.Dash(__name__,
                    server=server,
                    url_base_pathname='/dash/handwriting/',
                    external_stylesheets=external_stylesheets)

    app.layout = html.Div([
        make_handwriting_layout()
        ])

    @app.callback(Output('output-data-upload', 'children'),
                  [Input('upload-data', 'contents')]
                  )
    def update_output(contents):
        if contents is not None:
            return parse_contents(contents)

    @app.callback(Output('output-data-text', 'children'),
                  [Input('convert_button', 'n_clicks')],
                  [State('upload-data', 'contents')]
                  )
    def call_google_vision_api(_, contents):
        if contents is not None:
            return detect_handwriting.detect_document(contents)


def parse_contents(contents):
    return html.Div([
        # HTML images accept base64 encoded strings in the same format
        # that is supplied by the upload
        html.Img(src=contents, style={'height':'50%', 'width':'50%'}),
    ])


def make_handwriting_layout():

    jumbotron = dbc.Jumbotron(
        [
            html.H1("Handwriting Parser", className='display-3'),
            html.P(
                "Drag and drop an image file (*.PNG or *.JPG) to the upload zone.  "
                "Once the image has been uploaded, it will be sent to Google AI for interpretation."
                "If the results are acceptable, download the file as text :)",
                className="lead",
            ),
        ],
        style={
            'width': '100%',
            'margin': '10px'
        },
    )

    upload = html.Div([
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or click to ',
                html.A('Select Files')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            }
        )
    ])

    starting_image =html.Div([
        html.Div(id='output-data-upload'),
    ])

    results = html.Div([
        html.Div(id='output-data-text')
    ])

    convert_button = dbc.Button('Convert Handwriting', id='convert_button', color='primary',block=True, n_clicks=0)

    handwriting_layout = html.Div([
        dbc.Row([
            dbc.Col([
                jumbotron
            ])
        ]),
        dbc.Row([
            dbc.Col([
                upload
            ])
        ]),
        dbc.Row([
            dbc.Col([
                starting_image
            ]),
            dbc.Col([
                results
            ])
        ]),
        dbc.Row([
            dbc.Col([
                convert_button
            ])
        ])
    ])

    return handwriting_layout
