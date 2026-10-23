"""UI components for single central Bonsai pot, modals, and status bars."""
import curses
import datetime
import unicodedata
from typing import Optional

from vimgarden import get_version_string
from vimgarden.data.ascii_art import EMPTY_POT, get_plant_art
from vimgarden.data.plants_data import PLANTS, SHOP_ITEMS
from vimgarden.enums import GrowthStage, HealthState, Season, Weather
from vimgarden.models import GameState, Plot
from vimgarden.simulation import format_tree_age

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


def str_cell_width(s: str) -> int:
    """Calculate visible monospace column width accounting for wide emoji characters."""
    w = 0
    for ch in s:
        cat = unicodedata.category(ch)
        if cat in ("Mn", "Me"):
            continue
        eaw = unicodedata.east_asian_width(ch)
        if eaw in ("W", "F") or cat in ("So", "Sk") or ord(ch) >= 0x1F300:
            w += 2
        else:
            w += 1
    return w


def draw_header(stdscr: curses.window, state: GameState, width: int) -> None:
    """Draw top status bar with season, weather, coins, and active pot."""
    season_str = SEASON_SYMBOLS.get(state.season, state.season.value)
    weather_str = WEATHER_SYMBOLS.get(state.weather, state.weather.value)
    pots_count = len(state.grid[0]) if state.grid and state.grid[0] else 1

    left_str = f" ${state.money} Zen Coins | {season_str} | {weather_str}"
    right_str = f"Pot [{state.cursor_x + 1}/{pots_count}] | vimgarden {get_version_string()} "

    safe_w = max(1, width - 1)
    left_w = str_cell_width(left_str)
    right_w = str_cell_width(right_str)
    pad = max(0, safe_w - left_w - right_w)
    full_str = left_str + (" " * pad) + right_str
    while full_str and str_cell_width(full_str) > safe_w:
        full_str = full_str[:-1]

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
            label = f"{name} ({stage})" if is_active else name
        else:
            label = "Empty"

        if is_active:
            items.append(f">[{idx + 1}: {label}]<")
        else:
            items.append(f"[{idx + 1}: {label}]")

    shelf_content = "  ".join(items)
    shelf_w = len(shelf_content)
    safe_w = max(1, width - 1)

    try:
        stdscr.addstr(y, 0, "─" * safe_w, curses.color_pair(4))

        if shelf_w <= safe_w:
            shelf_start_x = max(0, (safe_w - shelf_w) // 2)
            cur_x = shelf_start_x
            for idx, item_str in enumerate(items):
                is_active = idx == state.cursor_x
                attr = curses.color_pair(1) | curses.A_BOLD if is_active else curses.color_pair(6)
                if cur_x + len(item_str) <= safe_w:
                    stdscr.addstr(y, cur_x, item_str, attr)
                cur_x += len(item_str) + 2
        else:
            item_positions = []
            cx = 0
            for item_str in items:
                item_positions.append(cx)
                cx += len(item_str) + 2

            act_x = item_positions[state.cursor_x] + len(items[state.cursor_x]) // 2
            offset = max(0, min(act_x - safe_w // 2, max(0, shelf_w - safe_w)))

            for idx, item_str in enumerate(items):
                is_active = idx == state.cursor_x
                attr = curses.color_pair(1) | curses.A_BOLD if is_active else curses.color_pair(6)
                ix = item_positions[idx] - offset
                if 0 <= ix and ix + len(item_str) <= safe_w:
                    stdscr.addstr(y, ix, item_str, attr)

        stdscr.addstr(y + 1, 0, "─" * safe_w, curses.color_pair(4))
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
        safe_w = max(1, width - 1)
        stdscr.addstr(y - 1, 0, "─" * safe_w, curses.color_pair(4))

        if cmd_buffer is not None:
            left_str = f" :{cmd_buffer}"
        elif message:
            left_str = f" [{mode_name}] {message}"
        else:
            left_str = f" [{mode_name}]"

        hint_str = f"{hint} "
        pad = max(0, safe_w - len(left_str) - len(hint_str))
        full_line = (left_str + (" " * pad) + hint_str)[:safe_w]

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

        # Real-world tree age calculation (minutes, hours, days, months, years)
        now_ts = datetime.datetime.now().timestamp()
        age_str = format_tree_age(plot.plant.planted_at, now_ts)
        style_short = plot.plant.style.value.split()[0]


        if plot.plant.growth_stage == GrowthStage.MATURE:
            line1 = f"{plant_name} — {stage_name} [{style_short}, {age_str}] (Prune!)"
            art_color = curses.color_pair(1) | curses.A_BOLD
        else:
            line1 = f"{plant_name} — {stage_name} [{style_short}, {age_str}]"
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

        # Status lines centered below pot
        center_x = x + 15
        l1_x = max(0, center_x - len(line1) // 2)
        l2_x = max(0, center_x - len(line2) // 2)
        l2_color = curses.color_pair(badge_color) if plot.plant else curses.color_pair(6)
        stdscr.addstr(y + 15, l1_x, line1, curses.A_BOLD)
        stdscr.addstr(y + 16, l2_x, line2, l2_color)
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
    try:
        h = max(7, len(seeds) + 5)
        w = 46
        y = max(2, (screen_h - h) // 2)
        x = max(2, (screen_w - w) // 2)

        draw_modal_box(stdscr, y, x, h, w, "Select Bonsai to Plant")

        if not seeds:
            stdscr.addstr(y + 2, x + 4, "No saplings in inventory!", curses.color_pair(3))
            stdscr.addstr(y + 4, x + 4, "Press 's' to visit the Nursery", curses.color_pair(6))
            stdscr.addstr(y + h - 2, x + 3, "Esc: Back", curses.color_pair(4))
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

        stdscr.addstr(y + h - 2, x + 3, "Enter:Plant | jk:Select | Esc:Back", curses.color_pair(4))
    except curses.error:
        pass


def draw_shop_modal(
    stdscr: curses.window,
    shop_items: list[str],
    money: int,
    selected_idx: int,
    screen_h: int,
    screen_w: int,
) -> None:
    """Draw bonsai nursery & supplies shop modal."""
    try:
        h = min(screen_h - 4, max(10, len(shop_items) + 6))
        w = min(screen_w - 4, 78)
        y = max(2, (screen_h - h) // 2)
        x = max(2, (screen_w - w) // 2)

        draw_modal_box(stdscr, y, x, h, w, "Bonsai Nursery & Zen Supplies")

        stdscr.addstr(y + 2, x + 3, f"Zen Balance: ${money}", curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(y + 3, x + 3, "  Item/Species        Price  Category  Details", curses.color_pair(6))

        max_visible = max(1, h - 6)
        if len(shop_items) <= max_visible:
            start_idx = 0
        else:
            start_idx = max(0, min(selected_idx - max_visible // 2, len(shop_items) - max_visible))

        for row_offset, idx in enumerate(range(start_idx, min(len(shop_items), start_idx + max_visible))):
            item_id = shop_items[idx]
            pt = PLANTS.get(item_id)
            si = SHOP_ITEMS.get(item_id)
            if pt:
                line = f"{pt.name:<18}  ${pt.seed_price:<5}  Sapling   Yield: +${pt.sell_price}"
            elif si:
                name = str(si.get("name", item_id))
                price = str(si.get("price", 0))
                itype = str(si.get("type", "supply")).capitalize()
                desc = str(si.get("desc", ""))
                line = f"{name:<18}  ${price:<5}  {itype:<8}  {desc}"
            else:
                line = f"{item_id:<18}"

            is_sel = idx == selected_idx
            prefix = "> " if is_sel else "  "
            attr = curses.A_REVERSE if is_sel else curses.A_NORMAL

            stdscr.addstr(y + 4 + row_offset, x + 2, (prefix + line)[: w - 4], attr)

        stdscr.addstr(y + h - 2, x + 3, "b / Enter: Buy | jk:Scroll | Esc / s:Back", curses.color_pair(4))
    except curses.error:
        pass


def draw_inventory_modal(
    stdscr: curses.window,
    inventory: dict[str, int],
    selected_idx: int = 0,
    screen_h: int = 24,
    screen_w: int = 80,
) -> None:
    """Draw inventory modal."""
    try:
        items = list(inventory.items())
        h = min(screen_h - 4, max(8, len(items) + 6))
        w = min(screen_w - 4, 56)
        y = max(2, (screen_h - h) // 2)
        x = max(2, (screen_w - w) // 2)

        draw_modal_box(stdscr, y, x, h, w, "Bonsai Supplies & Saplings")

        if not items:
            stdscr.addstr(y + 2, x + 4, "Your inventory is empty.", curses.color_pair(6))
            stdscr.addstr(y + h - 2, x + 3, "Esc / q: Back", curses.color_pair(4))
            return

        stdscr.addstr(y + 2, x + 3, "  Item / Species                  Quantity", curses.color_pair(6))

        max_visible = max(1, h - 5)
        if len(items) <= max_visible:
            start_idx = 0
        else:
            start_idx = max(0, min(selected_idx - max_visible // 2, len(items) - max_visible))

        for row_offset, idx in enumerate(range(start_idx, min(len(items), start_idx + max_visible))):
            item_id, count = items[idx]
            pt = PLANTS.get(item_id)
            si = SHOP_ITEMS.get(item_id)
            if pt:
                name = pt.name
            elif si:
                name = str(si.get("name", item_id))
            else:
                name = item_id.capitalize()
            line = f"{name:<30} x{count}"

            is_sel = idx == selected_idx
            prefix = "> " if is_sel else "  "
            attr = curses.A_REVERSE if is_sel else curses.A_NORMAL
            stdscr.addstr(y + 3 + row_offset, x + 2, (prefix + line)[: w - 4], attr)

        stdscr.addstr(y + h - 2, x + 3, "jk:Scroll | Esc:Back", curses.color_pair(4))
    except curses.error:
        pass


def draw_help_modal(stdscr: curses.window, screen_h: int, screen_w: int) -> None:
    """Draw help screen overlay."""
    try:
        w = min(screen_w - 4, 76)
        h = min(screen_h - 2, 19)
        y = max(1, (screen_h - h) // 2)
        x = max(2, (screen_w - w) // 2)

        draw_modal_box(stdscr, y, x, h, w, "Bonsai Zen Guide")

        left_col = [
            ("BONSAI CONTROLS", True),
            ("h/l : Switch active shelf pot", False),
            ("w   : Water tree (resets thirst)", False),
            ("f   : Fertilizer (+50% speed)", False),
            ("c   : Wire branch (cycle style)", False),
            ("x   : Prune mature / clear dead", False),
            ("p   : Plant sapling in pot", False),
            ("s   : Nursery & Zen shop", False),
            ("i   : Inventory supplies", False),
            ("?   : Toggle this guide", False),
            ("", False),
            ("STYLING & MATURITY", True),
            ("Age : Up to +100% coin reward", False),
            ("Wire: Formal, Informal, Cascade", False),
        ]

        right_col = [
            ("COMMAND MODE (':')", True),
            (":w       Save garden state", False),
            (":q       Quit (:q! force)", False),
            (":wq / :x Save and quit", False),
            ("", False),
            ("SEASONS & WEATHER", True),
            ("🌸 Spring: Sakura +35% growth", False),
            ("☀️ Summer: Juniper +20% growth", False),
            ("🍁 Autumn: Maple +35% coins", False),
            ("❄️ Winter: Pine resists cold", False),
            ("🌧 Rain  : Auto-waters trees!", False),
            ("", False),
            ("Press Esc or q to return", False),
        ]

        for idx, (line, is_bold) in enumerate(left_col):
            if y + 2 + idx < y + h - 1:
                attr = curses.A_BOLD if is_bold else curses.A_NORMAL
                stdscr.addstr(y + 2 + idx, x + 3, line[:33], attr)

        rx = x + 38
        avail_rw = max(10, w - (rx - x) - 3)
        for idx, (line, is_bold) in enumerate(right_col):
            if y + 2 + idx < y + h - 1:
                attr = curses.A_BOLD if is_bold else curses.A_NORMAL
                stdscr.addstr(y + 2 + idx, rx, line[:avail_rw], attr)
    except curses.error:
        pass

