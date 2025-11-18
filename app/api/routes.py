from flask import Flask, request, jsonify
from app.config import API_KEY
from app.services.menu_service import handle_menu_request


def register_routes(app: Flask) -> None:
    @app.route("/api/menu", methods=["POST"])
    def api_menu():
        if API_KEY and not app.testing:
            client_key = request.headers.get("X-API-Key")
            if client_key is not None and client_key != API_KEY:
                return jsonify({"error": "Invalid API key"}), 401

        payload = request.get_json(silent=True) or {}
        url = payload.get("url")
        date_str = payload.get("date")

        body, status = handle_menu_request(
            url=url,
            date_str=date_str,
            is_testing=app.testing,
        )
        return jsonify(body), status

    @app.route("/")
    def index():
        return app.send_static_file("index.html")
