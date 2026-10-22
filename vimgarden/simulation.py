"""Simulation engine for vimgarden.
Handles growth, thirst, withering, and offline catch-up.
"""
from typing import Optional

from vimgarden.config import MAX_OFFLINE_SECONDS, WILT_GRACE_BUFFER_SECONDS
from vimgarden.data.plants_data import PLANTS
from vimgarden.enums import GrowthStage, HealthState
from vimgarden.models import GameState, Plant, PlantType, Plot


def _interval_overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    return max(0.0, end - start)


def update_plant(
    plant: Plant,
    plant_type: PlantType,
    t_from: float,
    t_to: float,
    is_offline_catchup: bool = False,
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
    
    # Healthy grows at 1.0x, thirsty at 0.25x, wilting/dead at 0.0x
    gained_growth = healthy_time * 1.0 + thirsty_time * 0.25
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

    for row in state.grid:
        for plot in row:
            if plot.plant is not None:
                plant_type = PLANTS.get(plot.plant.type_id)
                if plant_type:
                    update_plant(plot.plant, plant_type, t_from, t_to, is_offline_catchup)

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


def prune_bonsai(plot: Plot) -> Optional[tuple[str, int]]:
    """Prune mature bonsai tree: yields Zen coins without destroying tree,

    rolling growth back to ADULT stage so it can grow and bloom again.
    """
    if not plot.plant or plot.plant.growth_stage != GrowthStage.MATURE:
        return None
    if plot.plant.health_state == HealthState.DEAD:
        return None
    plant_type = PLANTS.get(plot.plant.type_id)
    sell_price = plant_type.sell_price if plant_type else 0
    type_id = plot.plant.type_id
    if plant_type:
        plot.plant.effective_growth_seconds = 0.70 * plant_type.growth_duration
        plot.plant.growth_stage = GrowthStage.ADULT
    return type_id, sell_price


def clear_dead_plot(plot: Plot) -> bool:
    """Remove a dead plant from the plot."""
    if plot.plant and plot.plant.health_state == HealthState.DEAD:
        plot.plant = None
        return True
    return False
