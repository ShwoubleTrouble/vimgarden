"""Unit tests for input FSM and Vim key handling."""
import unittest

from vimgarden.enums import GameMode
from vimgarden.input_fsm import InputFSM


class TestInputFSM(unittest.TestCase):
    def setUp(self):
        self.fsm = InputFSM()

    def test_navigation_keys(self):
        context = {}
        # h (left)
        act = self.fsm.handle_key(ord("h"), context)
        self.assertEqual(act.type, "MOVE")
        self.assertEqual(act.payload, (-1, 0))

        # l (right)
        act = self.fsm.handle_key(ord("l"), context)
        self.assertEqual(act.type, "MOVE")
        self.assertEqual(act.payload, (1, 0))

        # k (up)
        act = self.fsm.handle_key(ord("k"), context)
        self.assertEqual(act.type, "MOVE")
        self.assertEqual(act.payload, (0, -1))

        # j (down)
        act = self.fsm.handle_key(ord("j"), context)
        self.assertEqual(act.type, "MOVE")
        self.assertEqual(act.payload, (0, 1))

    def test_mode_transitions(self):
        context = {"available_seeds": ["juniper"], "shop_items": ["juniper", "sakura"]}

        # Press 's' -> SHOP
        act = self.fsm.handle_key(ord("s"), context)
        self.assertEqual(self.fsm.mode, GameMode.SHOP)
        self.assertEqual(act.type, "OPEN_SHOP")

        # Esc in SHOP -> NORMAL
        self.fsm.handle_key(27, context)
        self.assertEqual(self.fsm.mode, GameMode.NORMAL)

        # Press 'p' -> SEED_SELECT
        act = self.fsm.handle_key(ord("p"), context)
        self.assertEqual(self.fsm.mode, GameMode.SEED_SELECT)

        # Press Enter -> PLANT
        act = self.fsm.handle_key(10, context)
        self.assertEqual(self.fsm.mode, GameMode.NORMAL)
        self.assertEqual(act.type, "PLANT")
        self.assertEqual(act.payload, "juniper")

    def test_command_mode(self):
        context = {}
        # Press ':'
        self.fsm.handle_key(ord(":"), context)
        self.assertEqual(self.fsm.mode, GameMode.COMMAND)

        # Type 'w'
        self.fsm.handle_key(ord("w"), context)
        self.assertEqual(self.fsm.cmd_buffer, "w")

        # Press Enter -> SAVE action
        act = self.fsm.handle_key(10, context)
        self.assertEqual(self.fsm.mode, GameMode.NORMAL)
        self.assertEqual(act.type, "SAVE")

        # Command :q
        self.fsm.handle_key(ord(":"), context)
        self.fsm.handle_key(ord("q"), context)
        act = self.fsm.handle_key(10, context)
        self.assertEqual(act.type, "QUIT")
        self.assertFalse(act.payload)  # not forced

        # Command :q!
        self.fsm.handle_key(ord(":"), context)
        self.fsm.handle_key(ord("q"), context)
        self.fsm.handle_key(ord("!"), context)
        act = self.fsm.handle_key(10, context)
        self.assertEqual(act.type, "QUIT")
        self.assertTrue(act.payload)  # forced

    def test_fertilize_and_pot_select_keys(self):
        context = {}
        # Press 'f' -> FERTILIZE
        act = self.fsm.handle_key(ord("f"), context)
        self.assertEqual(act.type, "FERTILIZE")

        # Press 'c' -> WIRE_STYLE
        act_c = self.fsm.handle_key(ord("c"), context)
        self.assertEqual(act_c.type, "WIRE_STYLE")

        # Press '1' .. '3' -> SELECT_POT
        act1 = self.fsm.handle_key(ord("1"), context)
        self.assertEqual(act1.type, "SELECT_POT")
        self.assertEqual(act1.payload, 0)

        act3 = self.fsm.handle_key(ord("3"), context)
        self.assertEqual(act3.type, "SELECT_POT")
        self.assertEqual(act3.payload, 2)


if __name__ == "__main__":
    unittest.main()

