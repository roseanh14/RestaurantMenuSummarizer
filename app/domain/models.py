from typing import List, Optional
from pydantic import BaseModel, Field


class MenuItem(BaseModel):
    category: Optional[str] = None
    name: str
    price: Optional[float] = None
    allergens: List[str] = Field(default_factory=list)
    weight: Optional[str] = None


class MenuResponse(BaseModel):
    restaurant_name: Optional[str] = None
    date: str
    day_of_week: str
    menu_items: List[MenuItem]
    daily_menu: bool = True
    source_url: str
