import json
from datetime import date
import os

import pytest
import main


@pytest.fixture
def test_client(tmp_path, monkeypatch):
    test_db = tmp_path / "test_menu_cache.db"
    monkeypatch.setattr(main, "DB_PATH", str(test_db))
    main.init_db()

    def fake_fetch_page_text(url: str) -> str:
        return "Fake page text with some menu"

    monkeypatch.setattr(main, "fetch_page_text", fake_fetch_page_text)

    with main.app.test_client() as client:
        yield client


def test_api_menu_caching_flow(test_client, monkeypatch):
    call_count = {"count": 0}

    def fake_call_openai_menu(url, page_text, target_date: date):
        call_count["count"] += 1
        return {
            "restaurant_name": "Test Restaurant",
            "date": target_date.isoformat(),
            "day_of_week": target_date.strftime("%A"),
            "menu_items": [
                {
                    "category": "main",
                    "name": "Fake Schnitzel",
                    "price": 150,
                    "allergens": ["1", "3", "7"],
                    "weight": "150g",
                }
            ],
            "daily_menu": True,
            "source_url": url,
        }

    monkeypatch.setattr(main, "call_openai_menu", fake_call_openai_menu)

    payload = {
        "url": "https://example.com/menu",
        "date": "2030-01-01",
    }

    resp1 = test_client.post("/api/menu", json=payload)
    assert resp1.status_code == 200
    data1 = resp1.get_json()
    assert data1["restaurant_name"] == "Test Restaurant"
    assert data1["cached"] is False
    assert call_count["count"] == 1

    resp2 = test_client.post("/api/menu", json=payload)
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2["restaurant_name"] == "Test Restaurant"
    assert data2["cached"] is True
    assert call_count["count"] == 1
