import pytest
from main import MenuItem, MenuResponse


def test_menu_response_valid():
    data = {
        "restaurant_name": "Test Restaurant",
        "date": "2030-01-01",
        "day_of_week": "Tuesday",
        "menu_items": [
            {
                "category": "main",
                "name": "Test Food",
                "price": 150,
                "allergens": ["1", "3"],
                "weight": "150g",
            }
        ],
        "daily_menu": True,
        "source_url": "https://example.com/menu",
    }

    menu = MenuResponse(**data)
    assert menu.restaurant_name == "Test Restaurant"
    assert menu.menu_items[0].name == "Test Food"
    assert menu.menu_items[0].price == 150


def test_menu_item_missing_name_raises():
    bad_item = {
        "category": "main",
        "price": 150,
        "allergens": [],
        "weight": "150g",
    }

    with pytest.raises(Exception):
        MenuItem(**bad_item)
