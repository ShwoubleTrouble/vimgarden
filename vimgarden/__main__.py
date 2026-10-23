"""Main entry point for vimgarden."""
import curses
import json
import signal
import sys
import time
from types import FrameType
from typing import Optional

from vimgarden.config import AUTO_SAVE_INTERVAL, MAX_POTS, SAVE_DIR, SAVE_FILE, TICK_TIMEOUT_MS
from vimgarden.data.plants_data import PLANTS, SHOP_ITEMS
from vimgarden.enums import BonsaiStyle, GameMode, GrowthStage, HealthState
from vimgarden.input_fsm import Action, InputFSM
from vimgarden.models import GameState, Plant, Plot
from vimgarden.simulation import (
    clear_dead_plot,
    fertilize_plot,
    prune_bonsai,
    update_simulation,
    water_plot,
)
from vimgarden.storage import load_game, save_game, state_to_dict
from vimgarden.ui.renderer import Renderer

_GLOBAL_STATE: Optional[GameState] = None
_HAS_UNSAVED_CHANGES: bool = False
_INITIAL_SAVE_DATA: Optional[dict] = None


def init_save_snapshot(state: GameState) -> None:
    """Store snapshot of save data as it was at session start."""
    global _INITIAL_SAVE_DATA
    if SAVE_FILE.exists():
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                _INITIAL_SAVE_DATA = json.load(f)
        except Exception:
            _INITIAL_SAVE_DATA = state_to_dict(state)
    else:
        _INITIAL_SAVE_DATA = None


def update_save_snapshot(state: GameState) -> None:
    """Update snapshot when state is explicitly saved."""
    global _INITIAL_SAVE_DATA
    _INITIAL_SAVE_DATA = state_to_dict(state)


def revert_to_last_save() -> None:
    """Revert SAVE_FILE to the snapshot from last explicit save (or session start)."""
    global _INITIAL_SAVE_DATA
    if _INITIAL_SAVE_DATA is not None:
        try:
            SAVE_DIR.mkdir(parents=True, exist_ok=True)
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(_INITIAL_SAVE_DATA, f, indent=2)
        except OSError:
            pass
    elif SAVE_FILE.exists():
        try:
            SAVE_FILE.unlink()
        except OSError:
            pass


def _signal_handler(signum: int, frame: Optional[FrameType]) -> None:
    """Ensure atomic save on termination signals without clobbering dirty state."""
    global _GLOBAL_STATE, _HAS_UNSAVED_CHANGES
    if _HAS_UNSAVED_CHANGES:
        revert_to_last_save()
    elif _GLOBAL_STATE is not None:
        save_game(_GLOBAL_STATE)
    sys.exit(0)


def handle_move(state: GameState, dx: int, dy: int) -> tuple[str, bool]:
    """Handle cursor movement."""
    grid_h = len(state.grid)
    grid_w = len(state.grid[0]) if grid_h > 0 else 0
    if grid_w > 0:
        state.cursor_x = max(0, min(grid_w - 1, state.cursor_x + dx))
    if grid_h > 0:
        state.cursor_y = max(0, min(grid_h - 1, state.cursor_y + dy))
    return "", False


def handle_select_pot(state: GameState, target_idx: int) -> tuple[str, bool]:
    """Directly select pot index."""
    grid_w = len(state.grid[0]) if state.grid else 0
    if 0 <= target_idx < grid_w:
        state.cursor_x = target_idx
    return "", False


def handle_water(curr_plot: Optional[Plot], curr_time: float) -> tuple[str, bool]:
    """Water active pot."""
    if curr_plot and curr_plot.plant:
        if curr_plot.plant.health_state == HealthState.DEAD:
            return "Bonsai is dead. Press 'x' to clear pot.", False
        water_plot(curr_plot, curr_time)
        return "Watered your bonsai!", True
    return "Pot is empty. Plant a sapling first ('p').", False


def handle_fertilize(state: GameState, curr_plot: Optional[Plot]) -> tuple[str, bool]:
    """Apply fertilizer to active pot."""
    if state.inventory.get("fertilizer", 0) <= 0:
        return "No fertilizer! Visit Nursery Shop ('s') to buy supplies.", False
    if not curr_plot or not curr_plot.plant:
        return "No tree in this pot to fertilize.", False
    if curr_plot.plant.health_state == HealthState.DEAD:
        return "Cannot fertilize a dead tree.", False
    fertilize_plot(curr_plot)
    state.inventory["fertilizer"] -= 1
    if state.inventory["fertilizer"] <= 0:
        del state.inventory["fertilizer"]
    return "Applied Organic Fertilizer (+50% growth speed)!", True


def handle_wire_style(state: GameState, curr_plot: Optional[Plot]) -> tuple[str, bool]:
    """Shape tree with bonsai wire."""
    if not curr_plot or not curr_plot.plant:
        return "No bonsai in this pot to shape.", False
    if curr_plot.plant.health_state == HealthState.DEAD:
        return "Cannot shape a dead bonsai.", False
    if state.inventory.get("copper_wire", 0) <= 0:
        return "Need Copper Wire! Buy in Nursery Shop ('s').", False
    style_cycle = [BonsaiStyle.MOYOGI, BonsaiStyle.KENGAI, BonsaiStyle.CHOKKAN]
    curr_idx = style_cycle.index(curr_plot.plant.style) if curr_plot.plant.style in style_cycle else 0
    new_style = style_cycle[(curr_idx + 1) % len(style_cycle)]
    curr_plot.plant.style = new_style
    state.inventory["copper_wire"] -= 1
    if state.inventory["copper_wire"] <= 0:
        del state.inventory["copper_wire"]
    return f"Wired branch into {new_style.value} style!", True


def handle_open_seed_select(fsm: InputFSM, curr_plot: Optional[Plot], available_seeds: list[str]) -> str:
    """Validate prerequisites before entering seed selection modal."""
    if not curr_plot:
        fsm.mode = GameMode.NORMAL
        return "Invalid pot."
    if curr_plot.plant is not None:
        fsm.mode = GameMode.NORMAL
        return "Pot is already occupied! Prune ('x') or wait."
    if not available_seeds:
        fsm.mode = GameMode.NORMAL
        return "No saplings! Press 's' to visit the Nursery."
    return ""


def handle_plant(state: GameState, curr_plot: Optional[Plot], seed_id: str, curr_time: float) -> tuple[str, bool]:
    """Plant sapling into empty pot."""
    if curr_plot and curr_plot.plant is None and state.inventory.get(seed_id, 0) > 0:
        state.inventory[seed_id] -= 1
        if state.inventory[seed_id] <= 0:
            del state.inventory[seed_id]
        curr_plot.plant = Plant(
            type_id=seed_id,
            planted_at=curr_time,
            last_watered_at=curr_time,
        )
        pt = PLANTS.get(seed_id)
        name = pt.name if pt else seed_id
        return f"Planted {name} in the pot!", True
    return "Could not plant sapling.", False


def handle_harvest_or_clear(state: GameState, curr_plot: Optional[Plot], curr_time: float) -> tuple[str, bool]:
    """Prune mature bonsai or clear dead tree."""
    if not curr_plot or not curr_plot.plant:
        return "Pot is empty.", False
    if curr_plot.plant.health_state == HealthState.DEAD:
        clear_dead_plot(curr_plot)
        return "Cleared dead bonsai from pot.", True
    if curr_plot.plant.growth_stage == GrowthStage.MATURE:
        result = prune_bonsai(
            curr_plot,
            season=state.season,
            decorations=state.decorations,
            current_time=curr_time,
        )
        if result:
            type_id, sell_price = result
            state.money += sell_price
            pt = PLANTS.get(type_id)
            name = pt.name if pt else type_id
            return f"Pruned {name}! Earned +${sell_price} Zen Coins.", True
    return "Bonsai is still growing. Wait until Mature to prune!", False


def handle_buy(state: GameState, item_id: str) -> tuple[str, bool]:
    """Purchase seed, tool, upgrade, or decor from nursery."""
    pt = PLANTS.get(item_id)
    si = SHOP_ITEMS.get(item_id)
    if pt:
        if state.money >= pt.seed_price:
            state.money -= pt.seed_price
            state.inventory[item_id] = state.inventory.get(item_id, 0) + 1
            return f"Purchased 1 {pt.name} sapling for ${pt.seed_price}.", True
        return f"Not enough Zen Coins for {pt.name} sapling!", False
    if si:
        price = int(si.get("price", 0))
        name = str(si.get("name", item_id))
        itype = si.get("type", "supply")
        if state.money < price:
            return f"Not enough Zen Coins for {name}!", False
        if itype == "upgrade" and item_id == "pot_slot":
            if len(state.grid[0]) >= MAX_POTS:
                return f"Tokonoma shelf is at max capacity ({MAX_POTS} pots)!", False
            state.money -= price
            new_x = len(state.grid[0])
            state.grid[0].append(Plot(x=new_x, y=0))
            grid_w = len(state.grid[0])
            return f"Expanded Tokonoma shelf! Now has {grid_w} pots.", True
        if itype == "decor":
            if item_id in state.decorations:
                return f"You already placed a {name} in your garden!", False
            state.money -= price
            state.decorations.append(item_id)
            return f"Placed {name} in your garden! (+Zen Buff active)", True
        state.money -= price
        state.inventory[item_id] = state.inventory.get(item_id, 0) + 1
        return f"Purchased 1 {name} for ${price}.", True
    return "Unknown item.", False


def handle_save(state: GameState) -> tuple[str, bool]:
    """Explicitly save game state to disk."""
    success = save_game(state)
    if success:
        update_save_snapshot(state)
        return "Bonsai state saved.", True
    return "Failed to save!", False


def handle_quit(has_unsaved_changes: bool, force: bool) -> tuple[str, bool, bool]:
    """Handle quit command. Returns (status_message, should_exit, should_save)."""
    if has_unsaved_changes and not force:
        return "No write since last change (add ! to override)", False, True
    if force:
        return "", True, False
    return "", True, True


def dispatch_action(
    action: Action,
    state: GameState,
    fsm: InputFSM,
    curr_time: float,
    has_unsaved_changes: bool,
    available_seeds: list[str],
) -> tuple[str, bool, bool, bool]:
    """Dispatch action to specific handler.

    Returns:
        (status_message, new_has_unsaved_changes, running, should_save_on_exit)
    """
    grid_h = len(state.grid)
    grid_w = len(state.grid[0]) if grid_h > 0 else 0
    curr_plot: Optional[Plot] = None
    if 0 <= state.cursor_y < grid_h and 0 <= state.cursor_x < grid_w:
        curr_plot = state.grid[state.cursor_y][state.cursor_x]

    if action.type == "MOVE":
        dx, dy = action.payload
        msg, changed = handle_move(state, dx, dy)
        return msg, has_unsaved_changes or changed, True, True

    elif action.type == "SELECT_POT":
        target_idx = action.payload
        msg, changed = handle_select_pot(state, target_idx)
        return msg, has_unsaved_changes or changed, True, True

    elif action.type == "WATER":
        msg, changed = handle_water(curr_plot, curr_time)
        return msg, has_unsaved_changes or changed, True, True

    elif action.type == "FERTILIZE":
        msg, changed = handle_fertilize(state, curr_plot)
        return msg, has_unsaved_changes or changed, True, True

    elif action.type == "WIRE_STYLE":
        msg, changed = handle_wire_style(state, curr_plot)
        return msg, has_unsaved_changes or changed, True, True

    elif action.type == "OPEN_SEED_SELECT":
        msg = handle_open_seed_select(fsm, curr_plot, available_seeds)
        return msg, has_unsaved_changes, True, True

    elif action.type == "PLANT":
        seed_id = action.payload
        msg, changed = handle_plant(state, curr_plot, seed_id, curr_time)
        return msg, has_unsaved_changes or changed, True, True

    elif action.type == "HARVEST_OR_CLEAR":
        msg, changed = handle_harvest_or_clear(state, curr_plot, curr_time)
        return msg, has_unsaved_changes or changed, True, True

    elif action.type == "BUY":
        item_id = action.payload
        msg, changed = handle_buy(state, item_id)
        return msg, has_unsaved_changes or changed, True, True

    elif action.type == "SAVE":
        msg, success = handle_save(state)
        new_dirty = False if success else has_unsaved_changes
        return msg, new_dirty, True, True

    elif action.type == "QUIT":
        force = bool(action.payload)
        msg, should_quit, should_save = handle_quit(has_unsaved_changes, force)
        if should_quit and not should_save:
            revert_to_last_save()
        return msg, has_unsaved_changes, not should_quit, should_save

    elif action.type == "SAVE_AND_QUIT":
        handle_save(state)
        return "", False, False, True

    elif action.type == "UNKNOWN_CMD":
        return f"Not an editor command: :{action.payload}", has_unsaved_changes, True, True

    elif action.type in ("OPEN_SHOP", "OPEN_INVENTORY", "OPEN_HELP", "NONE"):
        return "", has_unsaved_changes, True, True

    return "", has_unsaved_changes, True, True


def main(stdscr: curses.window) -> None:
    global _GLOBAL_STATE, _HAS_UNSAVED_CHANGES
    state = load_game()
    init_save_snapshot(state)
    _GLOBAL_STATE = state
    _HAS_UNSAVED_CHANGES = False

    renderer = Renderer(stdscr)
    fsm = InputFSM()

    stdscr.timeout(TICK_TIMEOUT_MS)
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    running = True
    should_save_on_exit = True
    status_message = "Welcome to Bonsai Zen! Press ? for guide."
    last_auto_save = time.time()
    has_unsaved_changes = False

    while running:
        curr_time = time.time()

        # 1. Update plant simulation
        update_simulation(state, current_time=curr_time)

        # 2. Check periodic auto-save (only if clean)
        if curr_time - last_auto_save >= AUTO_SAVE_INTERVAL:
            if not has_unsaved_changes:
                save_game(state)
                update_save_snapshot(state)
            last_auto_save = curr_time

        # 3. Handle user input
        try:
            key = stdscr.getch()
        except curses.error:
            key = -1

        if key != -1:
            available_seeds = [s for s, count in state.inventory.items() if count > 0 and s in PLANTS]
            context = {
                "available_seeds": available_seeds,
                "shop_items": list(SHOP_ITEMS.keys()),
                "inventory_items": list(state.inventory.items()),
            }

            action = fsm.handle_key(key, context)
            if action:
                msg, dirty, is_running, save_flag = dispatch_action(
                    action,
                    state,
                    fsm,
                    curr_time,
                    has_unsaved_changes,
                    available_seeds,
                )
                status_message = msg
                has_unsaved_changes = dirty
                _HAS_UNSAVED_CHANGES = has_unsaved_changes
                running = is_running
                if not save_flag:
                    should_save_on_exit = False

        # 4. Render
        renderer.render(state, fsm, status_message)

    # Persist on normal exit (unless forced quit with :q!)
    if should_save_on_exit:
        save_game(state)


def cli() -> None:
    """Console script entry point."""
    if len(sys.argv) > 1 and sys.argv[1] in ("--version", "-v"):
        from vimgarden import get_version_string
        print(f"vimgarden {get_version_string()}")
        sys.exit(0)
    curses.wrapper(main)


if __name__ == "__main__":
    cli()
