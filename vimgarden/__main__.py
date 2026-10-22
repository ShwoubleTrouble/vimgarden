"""Main entry point for vimgarden."""
import curses
import signal
import sys
import time
from types import FrameType
from typing import Optional

from vimgarden.config import AUTO_SAVE_INTERVAL, TICK_TIMEOUT_MS
from vimgarden.data.plants_data import PLANTS
from vimgarden.enums import GameMode, GrowthStage, HealthState
from vimgarden.input_fsm import InputFSM
from vimgarden.models import GameState, Plant, Plot
from vimgarden.simulation import (
    clear_dead_plot,
    prune_bonsai,
    update_simulation,
    water_plot,
)
from vimgarden.storage import load_game, save_game
from vimgarden.ui.renderer import Renderer

_GLOBAL_STATE: Optional[GameState] = None


def _signal_handler(signum: int, frame: Optional[FrameType]) -> None:
    """Ensure atomic save on termination signals."""
    if _GLOBAL_STATE is not None:
        save_game(_GLOBAL_STATE)
    sys.exit(0)


def main(stdscr: curses.window) -> None:
    global _GLOBAL_STATE
    state = load_game()
    _GLOBAL_STATE = state

    renderer = Renderer(stdscr)
    fsm = InputFSM()

    stdscr.timeout(TICK_TIMEOUT_MS)
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    running = True
    status_message = "Welcome to Bonsai Zen! Press ? for guide."
    last_auto_save = time.time()
    has_unsaved_changes = False

    grid_h = len(state.grid)
    grid_w = len(state.grid[0]) if grid_h > 0 else 0

    while running:
        curr_time = time.time()

        # 1. Update plant simulation
        update_simulation(state, current_time=curr_time)

        # 2. Check periodic auto-save
        if curr_time - last_auto_save >= AUTO_SAVE_INTERVAL:
            save_game(state)
            last_auto_save = curr_time
            has_unsaved_changes = False

        # 3. Handle user input
        try:
            key = stdscr.getch()
        except curses.error:
            key = -1

        if key != -1:
            available_seeds = [s for s, count in state.inventory.items() if count > 0]
            shop_items = list(PLANTS.keys())
            context = {
                "available_seeds": available_seeds,
                "shop_items": shop_items,
                "inventory_items": list(state.inventory.items()),
            }

            action = fsm.handle_key(key, context)
            if action:
                curr_plot: Optional[Plot] = None
                if 0 <= state.cursor_y < grid_h and 0 <= state.cursor_x < grid_w:
                    curr_plot = state.grid[state.cursor_y][state.cursor_x]

                if action.type == "MOVE":
                    dx, dy = action.payload
                    state.cursor_x = max(0, min(grid_w - 1, state.cursor_x + dx))
                    state.cursor_y = max(0, min(grid_h - 1, state.cursor_y + dy))
                    status_message = ""

                elif action.type == "WATER":
                    if curr_plot and curr_plot.plant:
                        if curr_plot.plant.health_state == HealthState.DEAD:
                            status_message = "Bonsai is dead. Press 'x' to clear pot."
                        else:
                            water_plot(curr_plot, curr_time)
                            has_unsaved_changes = True
                            status_message = "Watered your bonsai!"
                    else:
                        status_message = "Pot is empty. Plant a sapling first ('p')."

                elif action.type == "OPEN_SEED_SELECT":
                    if not curr_plot:
                        status_message = "Invalid pot."
                        fsm.mode = GameMode.NORMAL
                    elif curr_plot.plant is not None:
                        status_message = "Pot is already occupied! Prune ('x') or wait."
                        fsm.mode = GameMode.NORMAL
                    elif not available_seeds:
                        status_message = "No saplings! Press 's' to visit the Nursery."
                        fsm.mode = GameMode.NORMAL
                    else:
                        status_message = ""

                elif action.type == "PLANT":
                    seed_id = action.payload
                    if curr_plot and curr_plot.plant is None and state.inventory.get(seed_id, 0) > 0:
                        state.inventory[seed_id] -= 1
                        if state.inventory[seed_id] <= 0:
                            del state.inventory[seed_id]
                        curr_plot.plant = Plant(
                            type_id=seed_id,
                            planted_at=curr_time,
                            last_watered_at=curr_time,
                        )
                        has_unsaved_changes = True
                        pt = PLANTS.get(seed_id)
                        name = pt.name if pt else seed_id
                        status_message = f"Planted {name} in the pot!"
                    else:
                        status_message = "Could not plant sapling."

                elif action.type == "HARVEST_OR_CLEAR":
                    if not curr_plot or not curr_plot.plant:
                        status_message = "Pot is empty."
                    elif curr_plot.plant.health_state == HealthState.DEAD:
                        clear_dead_plot(curr_plot)
                        has_unsaved_changes = True
                        status_message = "Cleared dead bonsai from pot."
                    elif curr_plot.plant.growth_stage == GrowthStage.MATURE:
                        result = prune_bonsai(curr_plot)
                        if result:
                            type_id, sell_price = result
                            state.money += sell_price
                            has_unsaved_changes = True
                            pt = PLANTS.get(type_id)
                            name = pt.name if pt else type_id
                            status_message = f"Pruned {name}! Earned +${sell_price} Zen Coins."
                    else:
                        status_message = "Bonsai is still growing. Wait until Mature to prune!"

                elif action.type == "BUY":
                    item_id = action.payload
                    pt = PLANTS.get(item_id)
                    if pt:
                        if state.money >= pt.seed_price:
                            state.money -= pt.seed_price
                            state.inventory[item_id] = state.inventory.get(item_id, 0) + 1
                            has_unsaved_changes = True
                            status_message = f"Purchased 1 {pt.name} sapling for ${pt.seed_price}."
                        else:
                            status_message = f"Not enough Zen Coins for {pt.name} sapling!"

                elif action.type == "SAVE":
                    success = save_game(state)
                    last_auto_save = curr_time
                    has_unsaved_changes = False
                    status_message = "Bonsai state saved." if success else "Failed to save!"

                elif action.type == "QUIT":
                    force = action.payload
                    if has_unsaved_changes and not force:
                        status_message = "No write since last change (add ! to override)"
                    else:
                        running = False

                elif action.type == "SAVE_AND_QUIT":
                    save_game(state)
                    running = False

                elif action.type == "UNKNOWN_CMD":
                    status_message = f"Not an editor command: :{action.payload}"

                elif action.type in ("OPEN_SHOP", "OPEN_INVENTORY", "OPEN_HELP", "NONE"):
                    status_message = ""

        # 4. Render
        renderer.render(state, fsm, status_message)

    # Persist on normal exit
    save_game(state)


def cli() -> None:
    """Console script entry point."""
    curses.wrapper(main)


if __name__ == "__main__":
    cli()
