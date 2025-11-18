import json
from datetime import date
from typing import List, Optional

import requests
from pydantic import ValidationError

from app.config import OPENAI_API_KEY
from app.domain.models import MenuResponse
from app.services.prompts import build_system_message, build_user_message_strict


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
    target_iso = target_date.isoformat()
    weekday = target_date.strftime("%A")

    system_msg = build_system_message()

    if mode == "strict":
        user_msg = build_user_message_strict(url=url, target_date=target_date)

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
