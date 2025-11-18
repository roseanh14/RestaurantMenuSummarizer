# app/route/routes.py
from flask import Flask, request, jsonify

from app.services.menu_service import handle_menu_request


def register_routes(app: Flask) -> None:
    @app.route("/api/menu", methods=["POST"])
    def api_menu():
        payload = request.get_json(silent=True) or {}
        url = payload.get("url")
        date_str = payload.get("date")

        body, status = handle_menu_request(
            url=url,
            date_str=date_str,
            is_testing=app.testing,
        )
        return jsonify(body), status

    @app.route("/api/health", methods=["GET"])
    def health():
        """Simple health-check endpoint used mainly for tooling (Insomnia, monitoring)."""
        return (
            jsonify(
                {
                    "status": "ok",
                    "service": "restaurant-menu-summarizer",
                }
            ),
            200,
        )

    @app.route("/")
    def index():
        return app.send_static_file("index.html")
