"""Renderer coordinating curses drawing for single Bonsai tree."""
import curses
from typing import Optional

from vimgarden.config import MIN_COLS, MIN_LINES
from vimgarden.data.plants_data import PLANTS, get_shop_items
from vimgarden.enums import GameMode
from vimgarden.input_fsm import InputFSM
from vimgarden.models import GameState, Plot
from vimgarden.ui.components import (
    draw_bonsai_pot,
    draw_footer,
    draw_header,
    draw_help_modal,
    draw_inventory_modal,
    draw_seed_select_modal,
    draw_shelf_bar,
    draw_shop_modal,
)
from vimgarden.ui.layout import calculate_layout



class Renderer:
    def __init__(self, stdscr: curses.window) -> None:
        self.stdscr = stdscr
        self._init_colors()

    def _init_colors(self) -> None:
        """Initialize curses color pairs."""
        try:
            curses.curs_set(0)
        except curses.error:
            pass

        if curses.has_colors():
            curses.use_default_colors()
            try:
                curses.init_pair(1, curses.COLOR_GREEN, -1)
                curses.init_pair(2, curses.COLOR_YELLOW, -1)
                curses.init_pair(3, curses.COLOR_RED, -1)
                curses.init_pair(4, curses.COLOR_CYAN, -1)
                curses.init_pair(5, curses.COLOR_MAGENTA, -1)
                curses.init_pair(6, curses.COLOR_WHITE, -1)
            except curses.error:
                curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
                curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
                curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
                curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
                curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
                curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)

    def render(self, state: GameState, fsm: InputFSM, status_message: str = "") -> None:
        """Draw full screen frame."""
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()

        if h < MIN_LINES or w < MIN_COLS:
            msg1 = "Terminal too small!"
            msg2 = f"Required: at least {MIN_COLS} columns x {MIN_LINES} lines"
            msg3 = f"Current:  {w} columns x {h} lines"
            msg4 = "Please enlarge your terminal window."

            mid_y = h // 2
            try:
                self.stdscr.addstr(mid_y - 2, max(0, (w - len(msg1)) // 2), msg1, curses.A_BOLD)
                self.stdscr.addstr(mid_y - 1, max(0, (w - len(msg2)) // 2), msg2)
                self.stdscr.addstr(mid_y, max(0, (w - len(msg3)) // 2), msg3, curses.color_pair(2))
                self.stdscr.addstr(mid_y + 2, max(0, (w - len(msg4)) // 2), msg4, curses.color_pair(6))
                self.stdscr.noutrefresh()
                curses.doupdate()
            except curses.error:
                pass
            return

        layout = calculate_layout(h, w)

        # 1. Header & Tokonoma Shelf
        draw_header(self.stdscr, state, w)
        draw_shelf_bar(self.stdscr, state, layout.shelf_y + 1, w)

        # 2. Central Active Bonsai Pot
        active_x = max(0, min(len(state.grid[0]) - 1, state.cursor_x)) if state.grid and state.grid[0] else 0
        plot: Plot = state.grid[0][active_x] if state.grid and state.grid[0] else Plot(x=0, y=0)
        draw_bonsai_pot(self.stdscr, plot, layout.pot_start_y, layout.pot_start_x)

        # 3. Modals
        if fsm.mode == GameMode.SEED_SELECT:
            available_seeds = [s for s, count in state.inventory.items() if count > 0 and s in PLANTS]
            draw_seed_select_modal(self.stdscr, available_seeds, fsm.selected_index, h, w)
        elif fsm.mode == GameMode.SHOP:
            shop_items = get_shop_items()
            draw_shop_modal(self.stdscr, shop_items, state.money, fsm.selected_index, h, w)

        elif fsm.mode == GameMode.INVENTORY:
            draw_inventory_modal(self.stdscr, state.inventory, fsm.selected_index, h, w)
        elif fsm.mode == GameMode.HELP:
            draw_help_modal(self.stdscr, h, w)

        # 4. Footer
        cmd_buff: Optional[str] = fsm.cmd_buffer if fsm.mode == GameMode.COMMAND else None
        draw_footer(
            self.stdscr,
            y=h - 1,
            width=w,
            mode_name=fsm.mode.name,
            message=status_message,
            hint=fsm.hint,
            cmd_buffer=cmd_buff,
        )

        self.stdscr.noutrefresh()
        curses.doupdate()
