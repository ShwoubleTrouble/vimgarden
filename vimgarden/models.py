"""Data models for vimgarden."""
from dataclasses import dataclass, field
from typing import Optional

from vimgarden.enums import BonsaiStyle, GrowthStage, HealthState, Season, Weather


@dataclass(frozen=True)
class PlantType:
    id: str
    name: str
    seed_price: int
    sell_price: int
    growth_duration: float
    thirst_threshold: float
    wilt_threshold: float
    death_threshold: float


@dataclass
class Plant:
    type_id: str
    planted_at: float
    last_watered_at: float
    effective_growth_seconds: float = 0.0
    health_state: HealthState = HealthState.HEALTHY
    growth_stage: GrowthStage = GrowthStage.SEED
    style: BonsaiStyle = BonsaiStyle.MOYOGI
    fertilized_remaining_seconds: float = 0.0


@dataclass
class Plot:
    x: int
    y: int
    plant: Optional[Plant] = None
    is_unlocked: bool = True


@dataclass
class GameState:
    version: int = 2
    money: int = 50
    inventory: dict[str, int] = field(default_factory=lambda: {"juniper": 1, "fertilizer": 2})
    grid: list[list[Plot]] = field(default_factory=list)
    cursor_x: int = 0
    cursor_y: int = 0
    last_update_at: float = 0.0
    season: Season = Season.SPRING
    weather: Weather = Weather.SUNNY
    season_timer: float = 0.0
    weather_timer: float = 0.0
    decorations: list[str] = field(default_factory=list)

