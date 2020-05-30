import os

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

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

    from . import home
    home.register_home_dashapp(server)

    from . import strategy
    strategy.register_strategy(server)

    from . import manual
    manual.register_manual(server)

    from . import automatic
    automatic.register_automatic(server)

    return server


def protect_dash_route(app):
    from trades.routes import login_required

    for view_func in app.server.view_functions:
        if view_func.startswith(app.config.url_base_pathname):
            app.server.view_functions[view_func] = login_required(app.server.view_functions[view_func])
