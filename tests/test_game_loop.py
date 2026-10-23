"""Unit tests for game action handlers and loop logic."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vimgarden.__main__ import (
    dispatch_action,
    handle_buy,
    handle_fertilize,
    handle_harvest_or_clear,
    handle_move,
    handle_open_seed_select,
    handle_plant,
    handle_quit,
    handle_save,
    handle_select_pot,
    handle_water,
    handle_wire_style,
    init_save_snapshot,
    reset_globals,
    revert_to_last_save,
    _signal_handler,
)
from vimgarden.config import MAX_POTS
from vimgarden.data.plants_data import PLANTS, SHOP_ITEMS, get_shop_items
from vimgarden.enums import BonsaiStyle, GameMode, GrowthStage, HealthState
from vimgarden.input_fsm import Action, InputFSM
from vimgarden.models import GameState, Plant, Plot
from vimgarden.storage import revert_save, state_to_dict


class TestGameLoopHandlers(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.save_file = self.test_dir / "save.json"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        reset_globals()

    def test_handle_move(self):
        state = GameState(cursor_x=1, cursor_y=0, grid=[[Plot(x=0, y=0), Plot(x=1, y=0), Plot(x=2, y=0)]])
        # Move right
        msg, changed = handle_move(state, dx=1, dy=0)
        self.assertEqual(state.cursor_x, 2)
        self.assertFalse(changed)

        # Move right beyond bound (clamped)
        handle_move(state, dx=1, dy=0)
        self.assertEqual(state.cursor_x, 2)

        # Move left
        handle_move(state, dx=-2, dy=0)
        self.assertEqual(state.cursor_x, 0)

    def test_handle_select_pot(self):
        state = GameState(cursor_x=0, grid=[[Plot(x=0, y=0), Plot(x=1, y=0), Plot(x=2, y=0)]])
        handle_select_pot(state, 2)
        self.assertEqual(state.cursor_x, 2)

        # Invalid index ignored
        handle_select_pot(state, 10)
        self.assertEqual(state.cursor_x, 2)

    def test_handle_water(self):
        # Empty plot
        empty_plot = Plot(x=0, y=0)
        msg, changed = handle_water(empty_plot, 100.0)
        self.assertFalse(changed)
        self.assertIn("empty", msg)

        # Dead plant
        dead_plot = Plot(x=0, y=0, plant=Plant(type_id="juniper", planted_at=50.0, last_watered_at=50.0, health_state=HealthState.DEAD))
        msg, changed = handle_water(dead_plot, 100.0)
        self.assertFalse(changed)
        self.assertIn("dead", msg)

        # Living plant
        live_plot = Plot(x=0, y=0, plant=Plant(type_id="juniper", planted_at=50.0, last_watered_at=50.0, health_state=HealthState.THIRSTY))
        msg, changed = handle_water(live_plot, 100.0)
        self.assertTrue(changed)
        self.assertEqual(live_plot.plant.last_watered_at, 100.0)
        self.assertEqual(live_plot.plant.health_state, HealthState.HEALTHY)

    def test_handle_fertilize(self):
        plot = Plot(x=0, y=0, plant=Plant(type_id="juniper", planted_at=50.0, last_watered_at=50.0))
        state = GameState(inventory={"fertilizer": 1})

        # Success
        msg, changed = handle_fertilize(state, plot)
        self.assertTrue(changed)
        self.assertNotIn("fertilizer", state.inventory)
        self.assertGreater(plot.plant.fertilized_remaining_seconds, 0)

        # Out of fertilizer
        msg, changed = handle_fertilize(state, plot)
        self.assertFalse(changed)
        self.assertIn("No fertilizer", msg)

        # Mature tree cannot be fertilized
        state.inventory["fertilizer"] = 1
        mature_plot = Plot(x=0, y=0, plant=Plant(type_id="juniper", planted_at=50.0, last_watered_at=50.0, growth_stage=GrowthStage.MATURE))
        msg, changed = handle_fertilize(state, mature_plot)
        self.assertFalse(changed)
        self.assertIn("mature", msg)
        self.assertEqual(state.inventory["fertilizer"], 1)

    def test_handle_wire_style(self):
        plot = Plot(x=0, y=0, plant=Plant(type_id="juniper", planted_at=50.0, last_watered_at=50.0, style=BonsaiStyle.MOYOGI))
        state = GameState(inventory={"copper_wire": 1})

        msg, changed = handle_wire_style(state, plot)
        self.assertTrue(changed)
        self.assertEqual(plot.plant.style, BonsaiStyle.KENGAI)
        self.assertNotIn("copper_wire", state.inventory)

        # Out of wire
        msg, changed = handle_wire_style(state, plot)
        self.assertFalse(changed)
        self.assertIn("Need Copper Wire", msg)

    def test_handle_open_seed_select(self):
        fsm = InputFSM()
        empty_plot = Plot(x=0, y=0)
        occupied_plot = Plot(x=0, y=0, plant=Plant(type_id="juniper", planted_at=50.0, last_watered_at=50.0))

        # Occupied pot
        msg = handle_open_seed_select(fsm, occupied_plot, ["juniper"])
        self.assertIn("occupied", msg)

        # No seeds available
        msg = handle_open_seed_select(fsm, empty_plot, [])
        self.assertIn("No saplings", msg)

        # Valid
        msg = handle_open_seed_select(fsm, empty_plot, ["juniper"])
        self.assertEqual(msg, "")

    def test_handle_plant(self):
        plot = Plot(x=0, y=0)
        state = GameState(inventory={"sakura": 2})

        msg, changed = handle_plant(state, plot, "sakura", 100.0)
        self.assertTrue(changed)
        self.assertEqual(state.inventory["sakura"], 1)
        self.assertIsNotNone(plot.plant)
        self.assertEqual(plot.plant.type_id, "sakura")

        # Planting into occupied plot fails
        msg, changed = handle_plant(state, plot, "sakura", 105.0)
        self.assertFalse(changed)

    def test_handle_harvest_or_clear(self):
        state = GameState(money=0)
        # 1. Clear dead tree
        dead_plot = Plot(x=0, y=0, plant=Plant(type_id="juniper", planted_at=50.0, last_watered_at=50.0, health_state=HealthState.DEAD))
        msg, changed = handle_harvest_or_clear(state, dead_plot, 100.0)
        self.assertTrue(changed)
        self.assertIsNone(dead_plot.plant)

        # 2. Prune mature tree
        mature_plot = Plot(
            x=0,
            y=0,
            plant=Plant(
                type_id="juniper",
                planted_at=50.0,
                last_watered_at=50.0,
                growth_stage=GrowthStage.MATURE,
                health_state=HealthState.HEALTHY,
                effective_growth_seconds=90.0,
            ),
        )
        msg, changed = handle_harvest_or_clear(state, mature_plot, 100.0)
        self.assertTrue(changed)
        self.assertGreater(state.money, 0)
        self.assertEqual(mature_plot.plant.growth_stage, GrowthStage.ADULT)

        # 3. Growing tree cannot be pruned
        growing_plot = Plot(x=0, y=0, plant=Plant(type_id="juniper", planted_at=50.0, last_watered_at=50.0, growth_stage=GrowthStage.SPROUT))
        msg, changed = handle_harvest_or_clear(state, growing_plot, 100.0)
        self.assertFalse(changed)
        self.assertIn("Wait until Mature", msg)

    def test_handle_buy(self):
        state = GameState(money=500, inventory={}, grid=[[Plot(x=0, y=0), Plot(x=1, y=0)]])

        # Buy sapling
        msg, changed = handle_buy(state, "juniper")
        self.assertTrue(changed)
        self.assertEqual(state.inventory["juniper"], 1)
        self.assertEqual(state.money, 500 - 20)

        # Buy pot slot expansion
        msg, changed = handle_buy(state, "pot_slot")
        self.assertTrue(changed)
        self.assertEqual(len(state.grid[0]), 3)

        # Buy decor
        msg, changed = handle_buy(state, "furin_chime")
        self.assertTrue(changed)
        self.assertIn("furin_chime", state.decorations)

        # Buy duplicate decor fails
        msg, changed = handle_buy(state, "furin_chime")
        self.assertFalse(changed)
        self.assertIn("already placed", msg)

        # Insufficient money
        state.money = 0
        msg, changed = handle_buy(state, "pine")
        self.assertFalse(changed)
        self.assertIn("Not enough", msg)

    def test_handle_quit_and_force_quit_semantics(self):
        # 1. Dirty without force -> blocks quit
        msg, should_quit, should_save = handle_quit(has_unsaved_changes=True, force=False)
        self.assertFalse(should_quit)
        self.assertIn("No write since last change", msg)

        # 2. Dirty with force (:q!) -> allows quit, signals NOT to save
        msg, should_quit, should_save = handle_quit(has_unsaved_changes=True, force=True)
        self.assertTrue(should_quit)
        self.assertFalse(should_save)

        # 3. Clean without force (:q) -> allows quit, signals safe to save
        msg, should_quit, should_save = handle_quit(has_unsaved_changes=False, force=False)
        self.assertTrue(should_quit)
        self.assertTrue(should_save)

    def test_force_quit_discards_changes_to_save_file(self):
        with patch("vimgarden.__main__.SAVE_DIR", self.test_dir), \
             patch("vimgarden.__main__.SAVE_FILE", self.save_file), \
             patch("vimgarden.storage.SAVE_DIR", self.test_dir), \
             patch("vimgarden.storage.SAVE_FILE", self.save_file):

            # Initial saved state has $100
            init_state = GameState(money=100)
            self.save_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.save_file, "w") as f:
                json.dump(state_to_dict(init_state), f)

            # Session begins: load and init snapshot
            state = GameState(money=100)
            init_save_snapshot(state)

            fsm = InputFSM()
            # Player buys something dirty: $100 -> $80
            state.money = 80
            has_unsaved_changes = True

            # Player does :q!
            action = Action(type="QUIT", payload=True)
            msg, dirty, running, save_flag = dispatch_action(
                action, state, fsm, curr_time=100.0, has_unsaved_changes=has_unsaved_changes, available_seeds=[]
            )
            self.assertFalse(running)
            self.assertFalse(save_flag)

            # Check that save.json still has the initial $100
            with open(self.save_file, "r") as f:
                saved = json.load(f)
            self.assertEqual(saved["player"]["money"], 100)

    def test_get_shop_items_synchronization(self):
        items = get_shop_items()
        self.assertEqual(items, list(PLANTS.keys()) + list(SHOP_ITEMS.keys()))
        state = GameState(money=1000, grid=[[Plot(x=0, y=0)]])
        for item_id in items:
            msg, success = handle_buy(state, item_id)
            self.assertTrue(success, f"Failed to buy item {item_id}: {msg}")

    def test_save_and_quit_success_and_failure(self):
        state = GameState(money=100)
        fsm = InputFSM()
        action = Action(type="SAVE_AND_QUIT")

        # Success case: saves cleanly and exits, save_flag is False (already saved)
        with patch("vimgarden.__main__.handle_save", return_value=("Saved", True)):
            msg, dirty, running, save_flag = dispatch_action(
                action, state, fsm, curr_time=100.0, has_unsaved_changes=True, available_seeds=[]
            )
            self.assertEqual(msg, "Saved")
            self.assertFalse(dirty)
            self.assertFalse(running)
            self.assertFalse(save_flag)

        # Failure case: does not quit, retains unsaved changes
        with patch("vimgarden.__main__.handle_save", return_value=("Failed to save!", False)):
            msg, dirty, running, save_flag = dispatch_action(
                action, state, fsm, curr_time=100.0, has_unsaved_changes=True, available_seeds=[]
            )
            self.assertEqual(msg, "Failed to save!")
            self.assertTrue(dirty)
            self.assertTrue(running)

    def test_signal_handler_saves_state(self):
        saved_state = None

        def fake_save(st):
            nonlocal saved_state
            saved_state = st
            return True

        with patch("vimgarden.__main__.save_game", side_effect=fake_save), \
             patch("sys.exit") as mock_exit:
            test_state = GameState(money=777)
            import vimgarden.__main__ as main_mod
            main_mod._GLOBAL_STATE = test_state
            _signal_handler(15, None)
            mock_exit.assert_called_once_with(0)
            self.assertEqual(saved_state, test_state)


    def test_cli_flags(self):
        from vimgarden.__main__ import cli
        import io
        import sys

        # Test --help
        with patch.object(sys, "argv", ["vimgarden", "--help"]), \
             patch("sys.stdout", new=io.StringIO()) as fake_out:
            with self.assertRaises(SystemExit) as cm:
                cli()
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("Usage: vimgarden", fake_out.getvalue())

        # Test --version
        with patch.object(sys, "argv", ["vimgarden", "--version"]), \
             patch("sys.stdout", new=io.StringIO()) as fake_out:
            with self.assertRaises(SystemExit) as cm:
                cli()
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("vimgarden", fake_out.getvalue())


if __name__ == "__main__":
    unittest.main()
