from datetime import date

from app.services.utils import parse_input_date
from app.services.cache import delete_old_cache, get_cached_menu, save_menu
from app.services.scraper import fetch_page_text
from app.services.llm_client import call_openai_menu


def handle_menu_request(
    url: str | None,
    date_str: str | None,
    is_testing: bool = False,
) -> tuple[dict, int]:

    if not url:
        return {"error": "Missing 'url' in JSON payload."}, 400

    today = date.today()
    today_iso = today.isoformat()

    try:
        target_date = parse_input_date(date_str)
    except ValueError:
        return {
            "error": "Invalid 'date' format. Use YYYY-MM-DD, DD.MM.YYYY or DD.MM."
        }, 400

    if target_date < today:
        return {"error": "Date cannot be in the past."}, 400

    target_iso = target_date.isoformat()

    delete_old_cache(today_iso)

    cached_menu = get_cached_menu(url, target_iso)
    if cached_menu is not None:
        cached_menu["cached"] = True
        return cached_menu, 200

    try:
        page_text = fetch_page_text(url)
    except Exception as e:
        return {"error": f"Failed to download page: {e}"}, 502

    try:
        menu = call_openai_menu(url, page_text, target_date, mode="strict")
    except Exception as e:
        return {"error": f"OpenAI API call failed: {e}"}, 500

    if "error" not in menu and not (menu.get("menu_items") or []):
        try:
            fallback = call_openai_menu(url, page_text, target_date, mode="loose")
        except Exception:
            fallback = None

        if fallback and "error" not in fallback and (fallback.get("menu_items") or []):
            menu = fallback

    if "error" in menu:
        return menu, 500

    items = menu.get("menu_items") or []

    if items:
        save_menu(url, target_iso, menu)

    menu["cached"] = False
    return menu, 200
