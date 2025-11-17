from datetime import date


def build_system_message() -> str:
    return (
        "You are an assistant that EXTRACTS a restaurant LUNCH MENU "
        "from raw webpage text. "
        "You must respond ONLY with final JSON that matches the requested schema. "
        "If you need to convert messy price strings like '145,- Kc' to numeric values, "
        "you MUST call the 'normalize_prices' tool."
    )


def build_user_message_strict(
    url: str,
    target_date: date,
) -> str:
    target_iso = target_date.isoformat()
    weekday = target_date.strftime("%A")

    return f"""
Requested date (ISO): {target_iso}
Requested weekday (English): {weekday}
Page URL: {url}

You receive raw text of a restaurant webpage.

Your task is to EXTRACT THE FULL LUNCH MENU for the requested date, not a summary.

VERY IMPORTANT RULES (STRICT MODE):

1. Find the section that corresponds to the requested date (for example
   a heading like "STŘEDA 19.11.2025"). Treat ALL dishes listed under this heading
   until the next date/heading as part of the lunch menu for that day.

2. You MUST return ALL individual dishes as separate items in menu_items.
   Do NOT summarise multiple dishes into a single item. If there are 5 main dishes,
   there must be 5 separate objects in the menu_items array (plus soups, desserts, etc.).

3. Include at least:
   - every soup with a price,
   - every main course with a price,
   - any visible dessert or speciality with a price.
   Even if the menu looks long, list all items.

4. When extracting dishes, if prices appear in formats like "145,-", "145 Kč", "145 CZK",
   collect these raw price strings and call the 'normalize_prices' tool with an array
   of them to get numeric values in CZK. Then fill the numeric 'price' field
   in the final JSON (or null if unknown).

5. Guess the category based on the words:
   - if the name contains "polévka", "krém" → category = "soup"
   - sweet dishes / desserts → category = "dessert"
   - everything else → category = "main" or "speciality" as appropriate.

You should return an EMPTY menu_items array ONLY if the page clearly does not contain
any lunch menu or explicitly says the restaurant is closed.

Return ONLY JSON in this exact structure:

{{
  "restaurant_name": "restaurant name or null",
  "date": "{target_iso}",
  "day_of_week": "{weekday}",
  "menu_items": [
    {{
      "category": "soup / main / dessert / drink / other",
      "name": "dish name",
      "price": 145,
      "allergens": ["1", "3", "7"],
      "weight": "150g"
    }}
  ],
  "daily_menu": true,
  "source_url": "{url}"
}}
"""
