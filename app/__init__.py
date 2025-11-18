# app/__init__.py
from flask import Flask

from app.route.routes import register_routes
from app.config import AUTH_TOKEN
from app.middleware.auth import register_auth_middleware


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="../static",
        static_url_path="",
    )

    if AUTH_TOKEN:
        app.config["AUTH_TOKEN"] = AUTH_TOKEN

    register_routes(app)
    register_auth_middleware(app)

    return app
