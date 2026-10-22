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
