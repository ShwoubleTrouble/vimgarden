"""Simulation engine for vimgarden.
Handles growth, thirst, withering, and offline catch-up.
"""
import random
from typing import Optional

from vimgarden.config import (
    FERTILIZER_BOOST_SECONDS,
    FERTILIZER_SPEED_MULT,
    MAX_OFFLINE_SECONDS,
    SEASON_DURATION,
    WEATHER_DURATION,
    WILT_GRACE_BUFFER_SECONDS,
)
from vimgarden.data.plants_data import PLANTS
from vimgarden.enums import BonsaiStyle, GrowthStage, HealthState, Season, Weather
from vimgarden.models import GameState, Plant, PlantType, Plot

SEASONS_CYCLE = [Season.SPRING, Season.SUMMER, Season.AUTUMN, Season.WINTER]

WEATHER_POOLS = {
    Season.SPRING: [Weather.SUNNY, Weather.RAINY, Weather.MISTY, Weather.WINDY],
    Season.SUMMER: [Weather.SUNNY, Weather.SUNNY, Weather.WINDY, Weather.RAINY],
    Season.AUTUMN: [Weather.WINDY, Weather.MISTY, Weather.RAINY, Weather.SUNNY],
    Season.WINTER: [Weather.MISTY, Weather.WINDY, Weather.SUNNY, Weather.RAINY],
}



def _interval_overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    return max(0.0, end - start)


def update_weather_and_seasons(state: GameState, delta: float, current_time: float) -> None:
    """Cycle seasons and weather over time; rain auto-waters all living bonsai."""
    state.season_timer += delta
    if state.season_timer >= SEASON_DURATION:
        curr_idx = SEASONS_CYCLE.index(state.season) if state.season in SEASONS_CYCLE else 0
        state.season = SEASONS_CYCLE[(curr_idx + 1) % len(SEASONS_CYCLE)]
        state.season_timer = 0.0

    state.weather_timer += delta
    if state.weather_timer >= WEATHER_DURATION:
        pool = WEATHER_POOLS.get(state.season, [Weather.SUNNY])
        state.weather = random.choice(pool)
        state.weather_timer = 0.0

    if state.weather == Weather.RAINY:
        for row in state.grid:
            for plot in row:
                if plot.plant and plot.plant.health_state != HealthState.DEAD:
                    plot.plant.last_watered_at = current_time
                    plot.plant.health_state = HealthState.HEALTHY


def update_plant(
    plant: Plant,
    plant_type: PlantType,
    t_from: float,
    t_to: float,
    is_offline_catchup: bool = False,
    season: Season = Season.SPRING,
) -> None:
    """Advance single plant state from t_from to t_to."""
    if plant.health_state == HealthState.DEAD:
        return

    # Dry durations at interval start and end
    d0 = max(0.0, t_from - plant.last_watered_at)
    d1 = max(0.0, t_to - plant.last_watered_at)

    if d1 < d0:
        d1 = d0

    # Growth gained during [d0, d1]
    healthy_time = _interval_overlap(d0, d1, 0.0, plant_type.thirst_threshold)
    thirsty_time = _interval_overlap(d0, d1, plant_type.thirst_threshold, plant_type.wilt_threshold)

    # Seasonal affinity multiplier
    speed_mult = 1.0
    if season == Season.SPRING and plant.type_id == "sakura":
        speed_mult += 0.35
    elif season == Season.SUMMER and plant.type_id == "juniper":
        speed_mult += 0.20
    elif season == Season.AUTUMN and plant.type_id == "maple":
        speed_mult += 0.25
    elif season == Season.WINTER and plant.type_id == "pine":
        speed_mult += 0.20

    # Fertilizer boost
    dt = max(0.0, t_to - t_from)
    if plant.fertilized_remaining_seconds > 0.0 and dt > 0.0:
        boosted_time = min(dt, plant.fertilized_remaining_seconds)
        plant.fertilized_remaining_seconds = max(0.0, plant.fertilized_remaining_seconds - dt)
        speed_mult += (boosted_time / dt) * (FERTILIZER_SPEED_MULT - 1.0)

    # Healthy grows at 1.0x, thirsty at 0.25x, wilting/dead at 0.0x
    gained_growth = (healthy_time * 1.0 + thirsty_time * 0.25) * speed_mult
    plant.effective_growth_seconds = min(
        plant_type.growth_duration,
        plant.effective_growth_seconds + gained_growth,
    )


    # Determine health state at t_to
    current_dry = t_to - plant.last_watered_at

    if is_offline_catchup and current_dry >= plant_type.death_threshold:
        # Offline grace protection: don't kill, hold at WILTING with buffer before death
        grace_start_dry = max(plant_type.wilt_threshold, plant_type.death_threshold - WILT_GRACE_BUFFER_SECONDS)
        plant.last_watered_at = t_to - grace_start_dry
        current_dry = grace_start_dry

    if current_dry < plant_type.thirst_threshold:
        plant.health_state = HealthState.HEALTHY
    elif current_dry < plant_type.wilt_threshold:
        plant.health_state = HealthState.THIRSTY
    elif current_dry < plant_type.death_threshold:
        plant.health_state = HealthState.WILTING
    else:
        plant.health_state = HealthState.DEAD

    # Determine growth stage
    dur = plant_type.growth_duration
    eff = plant.effective_growth_seconds
    if eff < 0.25 * dur:
        plant.growth_stage = GrowthStage.SEED
    elif eff < 0.70 * dur:
        plant.growth_stage = GrowthStage.SPROUT
    elif eff < dur:
        plant.growth_stage = GrowthStage.ADULT
    else:
        plant.growth_stage = GrowthStage.MATURE


def update_simulation(state: GameState, current_time: float, is_offline_catchup: bool = False) -> None:
    """Advance simulation for all plots in the grid."""
    if state.last_update_at <= 0.0:
        state.last_update_at = current_time
        return

    delta = current_time - state.last_update_at
    if delta < 0.0:
        # Clock rollback or timezone switch: clamp time and do not penalize
        state.last_update_at = current_time
        return

    if delta > MAX_OFFLINE_SECONDS:
        delta = MAX_OFFLINE_SECONDS
        t_from = current_time - delta
    else:
        t_from = state.last_update_at

    t_to = current_time

    # 1. Update weather and seasons
    update_weather_and_seasons(state, delta, current_time)

    # 2. Update all plants
    for row in state.grid:
        for plot in row:
            if plot.plant is not None:
                plant_type = PLANTS.get(plot.plant.type_id)
                if plant_type:
                    update_plant(
                        plot.plant,
                        plant_type,
                        t_from,
                        t_to,
                        is_offline_catchup,
                        season=state.season,
                    )

    state.last_update_at = current_time


def water_plot(plot: Plot, current_time: float) -> bool:
    """Water the plant on the plot, resetting its dry timer to 0."""
    if not plot.plant or plot.plant.health_state == HealthState.DEAD:
        return False
    plot.plant.last_watered_at = current_time
    plot.plant.health_state = HealthState.HEALTHY
    return True


def harvest_plot(plot: Plot) -> Optional[tuple[str, int]]:
    """Harvest/prune mature bonsai tree."""
    return prune_bonsai(plot)


def prune_bonsai(
    plot: Plot,
    season: Optional[Season] = None,
    decorations: Optional[list[str]] = None,
    current_time: Optional[float] = None,
) -> Optional[tuple[str, int]]:
    """Prune mature bonsai tree: yields Zen coins without destroying tree,

    rolling growth back to ADULT stage so it can grow and bloom again.
    Applies seasonal bonuses, decor buffs, style refinement, and tree age multipliers.
    """
    if not plot.plant or plot.plant.growth_stage != GrowthStage.MATURE:
        return None
    if plot.plant.health_state == HealthState.DEAD:
        return None
    plant_type = PLANTS.get(plot.plant.type_id)
    sell_price = plant_type.sell_price if plant_type else 0
    type_id = plot.plant.type_id

    # Seasonal bonus
    if season == Season.AUTUMN and type_id == "maple":
        sell_price = int(sell_price * 1.35)

    # Decor bonus
    if decorations and "toro_lantern" in decorations:
        sell_price = int(sell_price * 1.20)

    # Bonsai training style bonus
    if plot.plant.style == BonsaiStyle.KENGAI:
        sell_price = int(sell_price * 1.25)
    elif plot.plant.style == BonsaiStyle.CHOKKAN:
        sell_price = int(sell_price * 1.15)

    # Tree Age multiplier (older trees are more valuable)
    if current_time and plot.plant.planted_at > 0.0:
        elapsed = max(0.0, current_time - plot.plant.planted_at)
        days = elapsed / 86400.0
        # +5% bonus per real-world day of care, capped at +100%
        age_multiplier = 1.0 + min(1.0, days * 0.05)
        sell_price = int(sell_price * age_multiplier)

    if plant_type:
        plot.plant.effective_growth_seconds = 0.70 * plant_type.growth_duration
        plot.plant.growth_stage = GrowthStage.ADULT
    return type_id, sell_price


def format_tree_age(planted_at: float, current_time: float) -> str:
    """Format real-world elapsed tree age (e.g. '15m', '10h', '3d', '2mo', '1y')."""
    if planted_at <= 0.0:
        return "new"
    delta = max(0.0, current_time - planted_at)
    if delta < 60.0:
        return f"{int(delta)}s"
    elif delta < 3600.0:
        return f"{int(delta // 60)}m"
    elif delta < 86400.0:
        return f"{int(delta // 3600)}h"
    elif delta < 86400.0 * 30:
        return f"{int(delta // 86400)}d"
    elif delta < 86400.0 * 365:
        return f"{int(delta // (86400 * 30))}mo"
    else:
        return f"{int(delta // (86400 * 365))}y"




def fertilize_plot(plot: Plot, duration: float = FERTILIZER_BOOST_SECONDS) -> bool:
    """Apply organic fertilizer to accelerate growth for the given duration."""
    if not plot.plant or plot.plant.health_state == HealthState.DEAD:
        return False
    plot.plant.fertilized_remaining_seconds += duration
    return True



def clear_dead_plot(plot: Plot) -> bool:
    """Remove a dead plant from the plot."""
    if plot.plant and plot.plant.health_state == HealthState.DEAD:
        plot.plant = None
        return True
    return False
