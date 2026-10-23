"""Bonsai species specifications dictionary."""
from vimgarden.models import PlantType

PLANTS: dict[str, PlantType] = {
    "juniper": PlantType(
        id="juniper",
        name="Juniper Bonsai",
        seed_price=20,
        sell_price=35,
        growth_duration=90.0,
        thirst_threshold=45.0,
        wilt_threshold=135.0,
        death_threshold=270.0,
    ),
    "sakura": PlantType(
        id="sakura",
        name="Sakura Bonsai",
        seed_price=50,
        sell_price=90,
        growth_duration=180.0,
        thirst_threshold=60.0,
        wilt_threshold=180.0,
        death_threshold=360.0,
    ),
    "maple": PlantType(
        id="maple",
        name="Japanese Maple",
        seed_price=90,
        sell_price=175,
        growth_duration=300.0,
        thirst_threshold=90.0,
        wilt_threshold=270.0,
        death_threshold=540.0,
    ),
    "pine": PlantType(
        id="pine",
        name="Black Pine Bonsai",
        seed_price=160,
        sell_price=340,
        growth_duration=600.0,
        thirst_threshold=150.0,
        wilt_threshold=450.0,
        death_threshold=900.0,
    ),
}

SHOP_ITEMS: dict[str, dict[str, str | int]] = {
    "fertilizer": {
        "id": "fertilizer",
        "name": "Organic Fertilizer",
        "price": 15,
        "type": "supply",
        "desc": "+50% growth speed for 90s",
    },
    "copper_wire": {
        "id": "copper_wire",
        "name": "Copper Bonsai Wire",
        "price": 25,
        "type": "tool",
        "desc": "Shape style ('c' to cycle)",
    },
    "pot_slot": {
        "id": "pot_slot",
        "name": "Tokonoma Pot Slot",
        "price": 75,
        "type": "upgrade",
        "desc": "+1 shelf pot capacity",
    },
    "toro_lantern": {
        "id": "toro_lantern",
        "name": "Toro Stone Lantern",
        "price": 120,
        "type": "decor",
        "desc": "+20% Zen Coins bonus",
    },
    "furin_chime": {
        "id": "furin_chime",
        "name": "Furin Wind Chime",
        "price": 60,
        "type": "decor",
        "desc": "+15% growth speed",
    },
}


def get_shop_items() -> list[str]:
    """Return unified ordered list of all purchasable nursery items and saplings."""
    return list(PLANTS.keys()) + list(SHOP_ITEMS.keys())

