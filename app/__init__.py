from flask import Flask
from app.api.routes import register_routes


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="../static",
        static_url_path="",
    )

    register_routes(app)
    return app
