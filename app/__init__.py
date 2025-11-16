import os
from flask import Flask
from .cache import init_db
from .routes import register_routes


def create_app() -> Flask:
    base_dir = os.path.dirname(os.path.dirname(__file__))
    static_dir = os.path.join(base_dir, "static")

    app = Flask(__name__, static_folder=static_dir, static_url_path="")

    init_db()
    register_routes(app)

    return app
