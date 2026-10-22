"""Storage management for saving and loading game state atomically with backups."""
import json
import logging
import os
import shutil
import time
from typing import Any, Optional

from vimgarden.config import BACKUP_SAVE_FILE, DEFAULT_UNLOCKED_POTS, SAVE_DIR, SAVE_FILE
from vimgarden.enums import BonsaiStyle, Season, Weather
from vimgarden.models import GameState, Plant, Plot
from vimgarden.simulation import update_simulation


logger = logging.getLogger(__name__)


def create_default_state() -> GameState:
    """Create fresh game state with a 3-pot Tokonoma shelf and starter tree."""
    now = time.time()
    starter_plant = Plant(
        type_id="juniper",
        planted_at=now,
        last_watered_at=now,
        effective_growth_seconds=0.0,
    )
    grid = [[
        Plot(x=0, y=0, plant=starter_plant),
        Plot(x=1, y=0),
        Plot(x=2, y=0),
    ]]
    return GameState(
        version=2,
        money=50,
        inventory={"juniper": 1, "fertilizer": 2},
        grid=grid,
        cursor_x=0,
        cursor_y=0,
        last_update_at=now,
        season=Season.SPRING,
        weather=Weather.SUNNY,
    )


def state_to_dict(state: GameState) -> dict[str, Any]:
    """Serialize GameState to dict."""
    plots_data = []
    for row in state.grid:
        for plot in row:
            p_data: dict[str, Any] = {
                "x": plot.x,
                "y": plot.y,
                "is_unlocked": plot.is_unlocked,
                "plant": None,
            }
            if plot.plant:
                p_data["plant"] = {
                    "type_id": plot.plant.type_id,
                    "planted_at": plot.plant.planted_at,
                    "last_watered_at": plot.plant.last_watered_at,
                    "effective_growth_seconds": plot.plant.effective_growth_seconds,
                    "fertilized_remaining_seconds": plot.plant.fertilized_remaining_seconds,
                    "style": plot.plant.style.value,
                }
            plots_data.append(p_data)

    return {
        "version": state.version,
        "saved_at": time.time(),
        "player": {
            "money": state.money,
            "inventory": dict(state.inventory),
        },
        "environment": {
            "season": state.season.value,
            "weather": state.weather.value,
            "season_timer": state.season_timer,
            "weather_timer": state.weather_timer,
            "decorations": list(state.decorations),
        },
        "grid": {
            "width": len(state.grid[0]) if state.grid else DEFAULT_UNLOCKED_POTS,
            "height": len(state.grid),
            "cursor": [state.cursor_x, state.cursor_y],
            "plots": plots_data,
        },
    }


def dict_to_state(data: dict[str, Any]) -> GameState:
    """Deserialize dict to GameState."""
    version = data.get("version", 2)
    player_data = data.get("player", {})
    money = player_data.get("money", 50)
    inventory = player_data.get("inventory", {})

    # Migrate legacy inventory
    if "carrot" in inventory:
        count = inventory.pop("carrot")
        inventory["juniper"] = inventory.get("juniper", 0) + count
    if not inventory:
        inventory = {"juniper": 1, "fertilizer": 2}

    env_data = data.get("environment", {})
    season_raw = env_data.get("season", Season.SPRING.value)
    weather_raw = env_data.get("weather", Weather.SUNNY.value)

    try:
        season = Season(season_raw)
    except (ValueError, KeyError):
        season = Season.SPRING

    try:
        weather = Weather(weather_raw)
    except (ValueError, KeyError):
        weather = Weather.SUNNY

    season_timer = float(env_data.get("season_timer", 0.0))
    weather_timer = float(env_data.get("weather_timer", 0.0))
    decorations = list(env_data.get("decorations", []))

    grid_data = data.get("grid", {})
    cursor = grid_data.get("cursor", [0, 0])
    cursor_x = cursor[0] if len(cursor) > 0 else 0
    cursor_y = cursor[1] if len(cursor) > 1 else 0

    plots_raw = grid_data.get("plots", [])
    plot_map: dict[tuple[int, int], Plot] = {}
    for pr in plots_raw:
        x, y = pr["x"], pr["y"]
        plant_obj: Optional[Plant] = None
        if pr.get("plant"):
            p_dict = pr["plant"]
            raw_type = p_dict["type_id"]
            if raw_type not in ("juniper", "sakura", "maple", "pine"):
                raw_type = "juniper"

            style_val = p_dict.get("style", BonsaiStyle.MOYOGI.value)
            try:
                style = BonsaiStyle(style_val)
            except (ValueError, KeyError):
                style = BonsaiStyle.MOYOGI

            plant_obj = Plant(
                type_id=raw_type,
                planted_at=p_dict["planted_at"],
                last_watered_at=p_dict["last_watered_at"],
                effective_growth_seconds=p_dict.get("effective_growth_seconds", 0.0),
                fertilized_remaining_seconds=p_dict.get("fertilized_remaining_seconds", 0.0),
                style=style,
            )
        plot_map[(x, y)] = Plot(
            x=x,
            y=y,
            plant=plant_obj,
            is_unlocked=pr.get("is_unlocked", True),
        )

    # Reconstruct 1D shelf row [0][0..N]
    row_plots = [plot_map[(x, 0)] for x in sorted([p[0] for p in plot_map if p[1] == 0])]
    if not row_plots:
        # Fallback to default 3 pots
        row_plots = [
            plot_map.get((0, 0), Plot(x=0, y=0)),
            Plot(x=1, y=0),
            Plot(x=2, y=0),
        ]
    elif len(row_plots) < DEFAULT_UNLOCKED_POTS:
        # Ensure at least 3 pots on shelf
        while len(row_plots) < DEFAULT_UNLOCKED_POTS:
            row_plots.append(Plot(x=len(row_plots), y=0))

    grid = [row_plots]
    cursor_x = max(0, min(len(grid[0]) - 1, cursor_x))
    cursor_y = 0

    saved_at = data.get("saved_at", time.time())
    return GameState(
        version=version,
        money=money,
        inventory=inventory,
        grid=grid,
        cursor_x=cursor_x,
        cursor_y=cursor_y,
        last_update_at=saved_at,
        season=season,
        weather=weather,
        season_timer=season_timer,
        weather_timer=weather_timer,
        decorations=decorations,
    )


def save_game(state: GameState) -> bool:
    """Atomically save game state to SAVE_FILE with backup copy."""
    try:
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        data = state_to_dict(state)
        tmp_file = SAVE_DIR / f"save.json.tmp.{os.getpid()}"

        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        # If current save file exists, back it up first
        if SAVE_FILE.exists():
            try:
                shutil.copy2(SAVE_FILE, BACKUP_SAVE_FILE)
            except OSError:
                pass

        # Atomic replacement
        os.replace(tmp_file, SAVE_FILE)
        return True
    except Exception as exc:
        logger.error("Failed to save game: %s", exc)
        return False


def load_game() -> GameState:
    """Load game state from SAVE_FILE or BACKUP_SAVE_FILE, or return default state."""
    state: Optional[GameState] = None

    for target_path in (SAVE_FILE, BACKUP_SAVE_FILE):
        if target_path.exists():
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                state = dict_to_state(data)
                break
            except Exception as exc:
                logger.warning("Failed to load %s: %s", target_path, exc)

    if state is None:
        state = create_default_state()
    else:
        # Run offline catchup immediately
        update_simulation(state, current_time=time.time(), is_offline_catchup=True)

    return state
