"""Enumerations for game stages, health states, and input modes."""
from enum import Enum, IntEnum, auto


class GrowthStage(IntEnum):
    SEED = 0
    SPROUT = 1
    ADULT = 2
    MATURE = 3


class HealthState(IntEnum):
    HEALTHY = 0
    THIRSTY = 1
    WILTING = 2
    DEAD = 3


class GameMode(Enum):
    NORMAL = auto()
    SEED_SELECT = auto()
    SHOP = auto()
    INVENTORY = auto()
    COMMAND = auto()
    HELP = auto()


class Season(str, Enum):
    SPRING = "Spring"
    SUMMER = "Summer"
    AUTUMN = "Autumn"
    WINTER = "Winter"


class Weather(str, Enum):
    SUNNY = "Sunny"
    RAINY = "Rainy"
    MISTY = "Misty"
    WINDY = "Windy"


class BonsaiStyle(str, Enum):
    CHOKKAN = "Formal Upright"
    MOYOGI = "Informal Upright"
    KENGAI = "Cascade"

