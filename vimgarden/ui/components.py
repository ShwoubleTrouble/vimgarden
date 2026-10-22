"""UI components for single central Bonsai pot, modals, and status bars."""
import curses
import datetime
from typing import Optional

from vimgarden import get_version_string
from vimgarden.data.ascii_art import EMPTY_POT, get_plant_art
from vimgarden.data.plants_data import PLANTS, SHOP_ITEMS
from vimgarden.enums import GrowthStage, HealthState, Season, Weather
from vimgarden.models import GameState, Plot

STAGE_NAMES: dict[GrowthStage, str] = {
    GrowthStage.SEED: "Sprout",
    GrowthStage.SPROUT: "Sapling",
    GrowthStage.ADULT: "Branched",
    GrowthStage.MATURE: "Mature",
}

HEALTH_BADGES: dict[HealthState, tuple[str, int]] = {
    HealthState.HEALTHY: ("[Healthy]", 1),   # Green
    HealthState.THIRSTY: ("[Thirsty]", 2),   # Yellow
    HealthState.WILTING: ("[Wilting]", 3),   # Red
    HealthState.DEAD:    ("[Dead]", 6),      # Dim
}

SEASON_SYMBOLS: dict[Season, str] = {
    Season.SPRING: "🌸 Spring",
    Season.SUMMER: "☀️ Summer",
    Season.AUTUMN: "🍁 Autumn",
    Season.WINTER: "❄️ Winter",
}

WEATHER_SYMBOLS: dict[Weather, str] = {
    Weather.SUNNY: "Sunny",
    Weather.RAINY: "🌧 Rain (Auto-Water)",
    Weather.MISTY: "🌫 Mist",
    Weather.WINDY: "💨 Breeze",
}


def draw_header(stdscr: curses.window, state: GameState, width: int) -> None:
    """Draw top status bar with season, weather, coins, and active pot."""
    season_str = SEASON_SYMBOLS.get(state.season, state.season.value)
    weather_str = WEATHER_SYMBOLS.get(state.weather, state.weather.value)
    pots_count = len(state.grid[0]) if state.grid and state.grid[0] else 1

    left_str = f" ${state.money} Zen Coins | {season_str} | {weather_str}"
    right_str = f"Pot [{state.cursor_x + 1}/{pots_count}] | vimgarden {get_version_string()} "


    pad = max(0, width - len(left_str) - len(right_str))
    full_str = (left_str + (" " * pad) + right_str)[:width]

    try:
        stdscr.attron(curses.A_REVERSE)
        stdscr.addstr(0, 0, full_str)
        stdscr.attroff(curses.A_REVERSE)
    except curses.error:
        pass


def draw_shelf_bar(stdscr: curses.window, state: GameState, y: int, width: int) -> None:
    """Draw horizontal tokonoma shelf with pot indicators."""
    row = state.grid[0] if state.grid and state.grid[0] else []
    items: list[str] = []

    for idx, plot in enumerate(row):
        is_active = idx == state.cursor_x
        if plot.plant:
            pt = PLANTS.get(plot.plant.type_id)
            name = pt.name.split()[0] if pt else plot.plant.type_id.capitalize()
            stage = STAGE_NAMES.get(plot.plant.growth_stage, "")
            label = f"{name} ({stage})"
        else:
            label = "Empty Pot"

        if is_active:
            items.append(f">[{idx + 1}: {label}]<")
        else:
            items.append(f"[{idx + 1}: {label}]")

    shelf_content = "  ".join(items)
    shelf_start_x = max(0, (width - len(shelf_content)) // 2)

    try:
        stdscr.addstr(y, 0, "─" * width, curses.color_pair(4))
        for idx, plot in enumerate(row):
            is_active = idx == state.cursor_x
            if plot.plant:
                pt = PLANTS.get(plot.plant.type_id)
                name = pt.name.split()[0] if pt else plot.plant.type_id.capitalize()
                stage = STAGE_NAMES.get(plot.plant.growth_stage, "")
                label = f"{name} ({stage})"
            else:
                label = "Empty Pot"

            txt = f">[{idx + 1}: {label}]<" if is_active else f"[{idx + 1}: {label}]"
            # find start position
            pos = shelf_content.find(txt)
            if pos != -1 and (shelf_start_x + pos + len(txt)) < width:
                attr = curses.color_pair(1) | curses.A_BOLD if is_active else curses.color_pair(6)
                stdscr.addstr(y, shelf_start_x + pos, txt, attr)
        stdscr.addstr(y + 1, 0, "─" * width, curses.color_pair(4))
    except curses.error:
        pass



def draw_footer(
    stdscr: curses.window,
    y: int,
    width: int,
    mode_name: str,
    message: str,
    hint: str,
    cmd_buffer: Optional[str] = None,
) -> None:
    """Draw bottom status bar and hotkey hints."""
    try:
        stdscr.addstr(y - 1, 0, "─" * width, curses.color_pair(4))

        if cmd_buffer is not None:
            left_str = f" :{cmd_buffer}"
        elif message:
            left_str = f" [{mode_name}] {message}"
        else:
            left_str = f" [{mode_name}]"

        hint_str = f"{hint} "
        pad = max(0, width - len(left_str) - len(hint_str))
        full_line = (left_str + (" " * pad) + hint_str)[:width]

        stdscr.attron(curses.A_REVERSE)
        stdscr.addstr(y, 0, full_line)
        stdscr.attroff(curses.A_REVERSE)
    except curses.error:
        pass


def draw_bonsai_pot(
    stdscr: curses.window,
    plot: Plot,
    y: int,
    x: int,
) -> None:
    """Draw large 31x15 bonsai pot with 2 lines of status labels below."""
    top_border = "╔" + "═" * 29 + "╗"
    bot_border = "╚" + "═" * 29 + "╝"
    border_attr = curses.color_pair(4)

    if plot.plant:
        art_lines = get_plant_art(plot.plant.type_id, plot.plant.growth_stage, plot.plant.health_state)
        badge_text, badge_color = HEALTH_BADGES.get(plot.plant.health_state, ("[?]", 0))
        plant_type = PLANTS.get(plot.plant.type_id)
        plant_name = plant_type.name if plant_type else plot.plant.type_id.capitalize()
        stage_name = STAGE_NAMES.get(plot.plant.growth_stage, "Sprout")

        if plot.plant.growth_stage == GrowthStage.MATURE:
            line1 = f"{plant_name} — {stage_name} (Ready to Prune!)"
            art_color = curses.color_pair(1) | curses.A_BOLD
        else:
            line1 = f"{plant_name} — {stage_name}"
            art_color = curses.color_pair(badge_color)

        if plot.plant.health_state == HealthState.HEALTHY:
            line2 = f"Health: {badge_text}  |  Water: OK"
        elif plot.plant.health_state == HealthState.THIRSTY:
            line2 = f"Health: {badge_text}  |  Needs Water (w)"
        elif plot.plant.health_state == HealthState.WILTING:
            line2 = f"Health: {badge_text}  |  Urgent Water (w)"
        else:
            line2 = f"Health: {badge_text}  |  Press 'x' to clear"

        if plot.plant.fertilized_remaining_seconds > 0.0:
            line2 += f" | ⚡+{int(plot.plant.fertilized_remaining_seconds)}s"

    else:
        art_lines = EMPTY_POT
        line1 = "Empty Ceramic Bonsai Pot"
        line2 = "Press 'p' to plant a sapling"
        art_color = curses.color_pair(6)

    try:
        stdscr.addstr(y, x, top_border, border_attr)
        for i, line in enumerate(art_lines):
            stdscr.addstr(y + 1 + i, x, "║", border_attr)
            stdscr.addstr(y + 1 + i, x + 1, line, art_color)
            stdscr.addstr(y + 1 + i, x + 30, "║", border_attr)
        stdscr.addstr(y + 14, x, bot_border, border_attr)

        # Status lines below pot
        l1_centered = f"{line1:^31}"
        l2_centered = f"{line2:^31}"
        stdscr.addstr(y + 15, x, l1_centered, curses.A_BOLD)
        stdscr.addstr(y + 16, x, l2_centered, curses.color_pair(art_color & 0xFF))
    except curses.error:
        pass


def draw_modal_box(stdscr: curses.window, y: int, x: int, h: int, w: int, title: str) -> None:
    """Draw frame for modal overlay."""
    try:
        for r in range(h):
            stdscr.addstr(y + r, x, " " * w, curses.A_NORMAL)

        stdscr.addstr(y, x, "┌" + "─" * (w - 2) + "┐", curses.color_pair(4))
        for r in range(1, h - 1):
            stdscr.addstr(y + r, x, "│", curses.color_pair(4))
            stdscr.addstr(y + r, x + w - 1, "│", curses.color_pair(4))
        stdscr.addstr(y + h - 1, x, "└" + "─" * (w - 2) + "┘", curses.color_pair(4))

        title_text = f" {title} "
        stdscr.addstr(y, x + max(2, (w - len(title_text)) // 2), title_text, curses.A_BOLD)
    except curses.error:
        pass


def draw_seed_select_modal(
    stdscr: curses.window,
    seeds: list[str],
    selected_idx: int,
    screen_h: int,
    screen_w: int,
) -> None:
    """Draw sapling selection modal."""
    h = max(7, len(seeds) + 4)
    w = 42
    y = max(2, (screen_h - h) // 2)
    x = max(2, (screen_w - w) // 2)

    draw_modal_box(stdscr, y, x, h, w, "Select Bonsai to Plant")

    if not seeds:
        stdscr.addstr(y + 2, x + 4, "No saplings in inventory!", curses.color_pair(3))
        stdscr.addstr(y + 4, x + 4, "Press 's' to visit the Nursery", curses.color_pair(6))
        return

    for idx, seed_id in enumerate(seeds):
        plant_type = PLANTS.get(seed_id)
        name = plant_type.name if plant_type else seed_id.capitalize()
        grow_m = int((plant_type.growth_duration if plant_type else 60) // 60)
        grow_s = int((plant_type.growth_duration if plant_type else 60) % 60)
        time_str = f"{grow_m}m{grow_s}s" if grow_m else f"{grow_s}s"
        line = f"{name:<18} (Cycle: {time_str:>4})"

        is_sel = idx == selected_idx
        prefix = " > " if is_sel else "   "
        attr = curses.A_REVERSE if is_sel else curses.A_NORMAL

        stdscr.addstr(y + 2 + idx, x + 2, (prefix + line)[: w - 4], attr)


def draw_shop_modal(
    stdscr: curses.window,
    shop_items: list[str],
    money: int,
    selected_idx: int,
    screen_h: int,
    screen_w: int,
) -> None:
    """Draw bonsai nursery & supplies shop modal."""
    h = min(screen_h - 4, max(10, len(shop_items) + 6))
    w = 62
    y = max(2, (screen_h - h) // 2)
    x = max(2, (screen_w - w) // 2)

    draw_modal_box(stdscr, y, x, h, w, "Bonsai Nursery & Zen Supplies")

    stdscr.addstr(y + 2, x + 3, f"Zen Balance: ${money}", curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(y + 3, x + 3, "Item/Species          Price   Category   Details", curses.color_pair(6))

    for idx, item_id in enumerate(shop_items):
        if idx >= h - 6:
            break
        pt = PLANTS.get(item_id)
        si = SHOP_ITEMS.get(item_id)
        if pt:
            line = f"{pt.name:<20}  ${pt.seed_price:<6}  Sapling    Yield: +${pt.sell_price}"
        elif si:
            name = str(si.get("name", item_id))
            price = str(si.get("price", 0))
            itype = str(si.get("type", "supply")).capitalize()
            desc = str(si.get("desc", ""))
            line = f"{name:<20}  ${price:<6}  {itype:<9}  {desc[:16]}"
        else:
            line = f"{item_id:<20}"

        is_sel = idx == selected_idx
        prefix = "> " if is_sel else "  "
        attr = curses.A_REVERSE if is_sel else curses.A_NORMAL

        stdscr.addstr(y + 4 + idx, x + 2, (prefix + line)[: w - 4], attr)

    stdscr.addstr(y + h - 2, x + 3, "Press 'b' to purchase | jk:Scroll | Esc:Back", curses.color_pair(4))


def draw_inventory_modal(
    stdscr: curses.window,
    inventory: dict[str, int],
    screen_h: int,
    screen_w: int,
) -> None:
    """Draw inventory modal."""
    items = list(inventory.items())
    h = max(8, len(items) + 5)
    w = 52
    y = max(2, (screen_h - h) // 2)
    x = max(2, (screen_w - w) // 2)

    draw_modal_box(stdscr, y, x, h, w, "Bonsai Supplies & Saplings")

    if not items:
        stdscr.addstr(y + 2, x + 4, "Your inventory is empty.", curses.color_pair(6))
        return

    stdscr.addstr(y + 2, x + 4, "Item / Species                  Quantity", curses.color_pair(6))
    for idx, (item_id, count) in enumerate(items):
        pt = PLANTS.get(item_id)
        si = SHOP_ITEMS.get(item_id)
        if pt:
            name = pt.name
        elif si:
            name = str(si.get("name", item_id))
        else:
            name = item_id.capitalize()
        line = f"{name:<30} x{count}"
        stdscr.addstr(y + 3 + idx, x + 4, line[: w - 8], curses.A_NORMAL)


def draw_help_modal(stdscr: curses.window, screen_h: int, screen_w: int) -> None:
    """Draw help screen overlay."""
    lines = [
        "VIM-LIKE BONSAI CONTROLS",
        "",
        "  h / l (←/→)  Switch active pot on the Tokonoma shelf",
        "  w            Water active bonsai tree (resets thirst)",
        "  f            Apply organic fertilizer (+50% growth speed)",
        "  x            Prune mature tree (+Zen Coins) / clear dead",
        "  p            Plant a sapling into empty pot",
        "  s            Visit Nursery & Zen Supply Shop",
        "  i            Inspect saplings & supplies inventory",
        "  ?            Open / close this guide",
        "",
        "SEASONS & DYNAMIC WEATHER",
        "  - 🌸 Spring : Sakura blooms faster (+35% growth)",
        "  - ☀️ Summer : Juniper flourishes (+20% growth)",
        "  - 🍁 Autumn : Japanese Maple gives +35% Zen Coins",
        "  - ❄️ Winter : Black Pine withstands the cold",
        "  - 🌧 Rain   : Automatically waters all bonsai trees!",
        "",
        "COMMAND MODE (press ':')",
        "  :w           Save garden state",
        "  :q           Quit game (:q! to force)",
        "  :wq / :x     Save and quit",
        "",
        "Press Esc or q to return",
    ]
    h = len(lines) + 4
    w = 62
    y = max(1, (screen_h - h) // 2)
    x = max(2, (screen_w - w) // 2)

    draw_modal_box(stdscr, y, x, h, w, "Bonsai Zen Guide")
    for idx, line in enumerate(lines):
        attr = curses.A_BOLD if idx == 0 else curses.A_NORMAL
        stdscr.addstr(y + 2 + idx, x + 3, line[: w - 6], attr)

