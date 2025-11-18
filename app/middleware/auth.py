from flask import Flask, request, abort, current_app


def register_auth_middleware(app: Flask) -> None:
    @app.before_request
    def _check_auth():

        if app.testing:
            return

        if not request.path.startswith("/api/"):
            return

        expected = current_app.config.get("AUTH_TOKEN")
        if not expected:
            return

        token = request.headers.get("AUTH_TOKEN")
        if token != expected:
            abort(401, description="Invalid or missing AUTH_TOKEN")
