from datetime import date, datetime

from flask import Flask, request, jsonify

from .config import API_KEY
from .cache import delete_old_cache, get_cached_menu, save_cached_menu
from .scraper import fetch_page_text
from .llm_client import call_openai_menu


def parse_input_date(date_str: str | None) -> date:
    today = date.today()

    if not date_str:
        return today

    raw = date_str.strip()

    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        pass

    cleaned = raw.replace(" ", "")

    for fmt in ("%d.%m.%Y", "%d.%m.%Y."):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            pass

    if cleaned.endswith("."):
        cleaned_no_dot = cleaned[:-1]
    else:
        cleaned_no_dot = cleaned

    try:
        dt = datetime.strptime(cleaned_no_dot, "%d.%m").date()
        return dt.replace(year=today.year)
    except ValueError:
        pass

    raise ValueError("unrecognized")


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

        if not url:
            return jsonify({"error": "Missing 'url' in JSON payload."}), 400

        today = date.today()
        today_iso = today.isoformat()

        try:
            target_date = parse_input_date(date_str)
        except ValueError:
            return (
                jsonify(
                    {
                        "error": "Invalid 'date' format. Use YYYY-MM-DD, DD.MM.YYYY or DD.MM."
                    }
                ),
                400,
            )

        if target_date < today:
            return jsonify({"error": "Date cannot be in the past."}), 400

        target_iso = target_date.isoformat()

        delete_old_cache(today_iso)

        cached_menu = get_cached_menu(url, target_iso)
        if cached_menu is not None:
            cached_menu["cached"] = True
            return jsonify(cached_menu)

        try:
            page_text = fetch_page_text(url)
        except Exception as e:
            return jsonify({"error": f"Failed to download page: {e}"}), 502

        try:
            menu = call_openai_menu(url, page_text, target_date, mode="strict")
        except Exception as e:
            return jsonify({"error": f"OpenAI API call failed: {e}"}), 500

        if "error" not in menu and not (menu.get("menu_items") or []):
            try:
                fallback = call_openai_menu(url, page_text, target_date, mode="loose")
            except Exception:
                fallback = None

            if (
                fallback
                and "error" not in fallback
                and (fallback.get("menu_items") or [])
            ):
                menu = fallback

        if "error" in menu:
            return jsonify(menu), 500

        items = menu.get("menu_items") or []

        if items:
            save_cached_menu(url, target_iso, menu)

        menu["cached"] = False
        return jsonify(menu)

    @app.route("/")
    def index():
        return app.send_static_file("index.html")
