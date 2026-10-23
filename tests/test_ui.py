"""Unit tests for UI layout calculation."""
import unittest

from vimgarden.config import MIN_COLS, MIN_LINES
from vimgarden.ui.layout import calculate_layout


class TestUILayout(unittest.TestCase):
    def test_small_terminal_detection(self):
        info = calculate_layout(23, 80)
        self.assertFalse(info.is_valid_size)

        info = calculate_layout(24, 79)
        self.assertFalse(info.is_valid_size)

    def test_valid_terminal_layout(self):
        info = calculate_layout(MIN_LINES, MIN_COLS)
        self.assertTrue(info.is_valid_size)
        self.assertGreaterEqual(info.pot_start_y, 2)
        self.assertGreaterEqual(info.pot_start_x, 0)
        # Total height: pot_h (15) + 2 labels = 17
        self.assertLessEqual(info.pot_start_y + info.pot_h + 2, MIN_LINES - 2)


    def test_modal_draw_boundaries_on_min_screen(self):
        from unittest.mock import MagicMock, patch
        from vimgarden.ui.components import draw_footer, draw_help_modal, draw_inventory_modal

        mock_stdscr = MagicMock()
        with patch("curses.color_pair", return_value=0):
            # Ensure 24x80 minimum boundary does not throw or crash
            draw_footer(mock_stdscr, y=23, width=80, mode_name="NORMAL", message="Ready", hint="?:Help")
            self.assertTrue(mock_stdscr.addstr.called)

            mock_stdscr.reset_mock()
            draw_help_modal(mock_stdscr, screen_h=24, screen_w=80)
            self.assertTrue(mock_stdscr.addstr.called)

            mock_stdscr.reset_mock()
            inventory = {"juniper": 2, "sakura": 1, "fertilizer": 5}
            draw_inventory_modal(mock_stdscr, inventory, selected_idx=1, screen_h=24, screen_w=80)
            self.assertTrue(mock_stdscr.addstr.called)

            mock_stdscr.reset_mock()
            from vimgarden.models import GameState, Plot, Plant
            from vimgarden.ui.components import draw_header, draw_shelf_bar, draw_bonsai_pot
            five_pots = [Plot(x=i, y=0, plant=Plant("juniper", 1.0, 1.0)) for i in range(5)]
            state = GameState(grid=[five_pots], cursor_x=4)
            draw_header(mock_stdscr, state, width=80)
            self.assertTrue(mock_stdscr.addstr.called)

            mock_stdscr.reset_mock()
            draw_shelf_bar(mock_stdscr, state, y=2, width=80)
            self.assertTrue(mock_stdscr.addstr.called)

            mock_stdscr.reset_mock()
            draw_bonsai_pot(mock_stdscr, five_pots[0], y=4, x=20)
            self.assertTrue(mock_stdscr.addstr.called)

            mock_stdscr.reset_mock()
            from vimgarden.ui.components import draw_shop_modal, draw_seed_select_modal
            draw_shop_modal(mock_stdscr, ["juniper", "sakura"], money=100, selected_idx=0, screen_h=24, screen_w=80)
            self.assertTrue(mock_stdscr.addstr.called)

            mock_stdscr.reset_mock()
            draw_seed_select_modal(mock_stdscr, ["juniper"], selected_idx=0, screen_h=24, screen_w=80)
            self.assertTrue(mock_stdscr.addstr.called)


if __name__ == "__main__":
    unittest.main()
