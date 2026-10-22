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


if __name__ == "__main__":
    unittest.main()
