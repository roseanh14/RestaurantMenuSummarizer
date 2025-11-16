import json
from datetime import date
from typing import List, Optional

import requests
from pydantic import ValidationError

from .config import OPENAI_API_KEY
from .models import MenuResponse


def normalize_prices_tool(prices: List[Optional[str]]) -> dict:
    import re

    normalized: List[Optional[float]] = []
    for raw in prices:
        if raw is None:
            normalized.append(None)
            continue

        s = str(raw)
        m = re.search(r"\d+([.,]\d+)?", s)
        if not m:
            normalized.append(None)
            continue

        num_str = m.group(0).replace(",", ".")
        try:
            val = float(num_str)
        except ValueError:
            normalized.append(None)
        else:
            normalized.append(val)

    return {"normalized": normalized}


def call_openai_menu(
    url: str, page_text: str, target_date: date, mode: str = "strict"
) -> dict:
    """
    Zavolá OpenAI /v1/chat/completions:
      - použije tool calling (normalize_prices),
      - vytáhne menu pro konkrétní den (strict) nebo obecné obědové menu (loose),
      - validuje strukturu přes Pydantic.
    mode:
      - "strict" = pokusí se opravdu respektovat datum
      - "loose"  = ignoruje rok i přesné datum, prostě vytáhne rozumné weekly/denní menu
    """
    target_iso = target_date.isoformat()
    weekday = target_date.strftime("%A")

    system_msg = (
        "You are an assistant that EXTRACTS a restaurant LUNCH MENU "
        "from raw webpage text. "
        "You must respond ONLY with final JSON that matches the requested schema. "
        "If you need to convert messy price strings like '145,- Kc' to numeric values, "
        "you MUST call the 'normalize_prices' tool."
    )

    if mode == "strict":
        user_msg = f"""
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

    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    tools = [
        {
            "type": "function",
            "function": {
                "name": "normalize_prices",
                "description": "Convert an array of raw price strings to numeric values in CZK.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prices": {
                            "type": "array",
                            "items": {"type": ["string", "null"]},
                        }
                    },
                    "required": ["prices"],
                },
            },
        }
    ]

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]

    payload = {
        "model": "gpt-4.1-mini",
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
    }

    resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    resp_json = resp.json()

    first_message = resp_json["choices"][0]["message"]
    tool_calls = first_message.get("tool_calls")

    if tool_calls:
        messages.append(
            {
                "role": "assistant",
                "content": first_message.get("content") or "",
                "tool_calls": tool_calls,
            }
        )

        for tool_call in tool_calls:
            func_name = tool_call["function"]["name"]
            args_str = tool_call["function"]["arguments"] or "{}"
            try:
                args = json.loads(args_str)
            except json.JSONDecodeError:
                args = {}

            if func_name == "normalize_prices":
                tool_result = normalize_prices_tool(args.get("prices", []))
            else:
                tool_result = {"error": f"Unknown tool {func_name}"}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": func_name,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                }
            )

        payload_final = {
            "model": "gpt-4.1-mini",
            "messages": messages,
        }
        resp2 = requests.post(api_url, headers=headers, json=payload_final, timeout=60)
        resp2.raise_for_status()
        final_message = resp2.json()["choices"][0]["message"]
        content = final_message["content"]
    else:
        content = first_message["content"]

    cleaned = (content or "").strip()
    if cleaned.startswith("```"):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]

    try:
        raw_data = json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "error": "Model did not return valid JSON.",
            "raw_response": cleaned,
        }

    try:
        menu_obj = MenuResponse(**raw_data)
    except ValidationError as e:
        return {
            "error": "Model JSON does not match expected schema.",
            "validation_errors": e.errors(),
            "raw_response": raw_data,
        }

    menu_obj.date = target_iso
    menu_obj.day_of_week = weekday
    menu_obj.source_url = url

    return json.loads(menu_obj.model_dump_json())
