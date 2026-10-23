"""Unit tests for storage serialization, backup, and atomic writing."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vimgarden.models import GameState, Plant, Plot
from vimgarden.storage import dict_to_state, load_game, load_raw_save, revert_save, save_game, state_to_dict


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.save_file = self.test_dir / "save.json"
        self.backup_file = self.test_dir / "save.json.bak"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_state_dict_roundtrip(self):
        grid = [
            [
                Plot(x=0, y=0, plant=Plant(type_id="sakura", planted_at=100.0, last_watered_at=100.0, effective_growth_seconds=15.0)),
            ]
        ]
        state = GameState(
            version=2,
            money=120,
            inventory={"sakura": 2, "pine": 1},
            grid=grid,
            cursor_x=0,
            cursor_y=0,
            last_update_at=200.0,
        )

        data = state_to_dict(state)
        restored = dict_to_state(data)

        self.assertEqual(restored.version, state.version)
        self.assertEqual(restored.money, 120)
        self.assertEqual(restored.inventory, {"sakura": 2, "pine": 1})
        self.assertIsNotNone(restored.grid[0][0].plant)
        self.assertEqual(restored.grid[0][0].plant.type_id, "sakura")

    def test_dead_plant_serialization_and_catchup_preservation(self):
        from vimgarden.enums import GrowthStage, HealthState
        from vimgarden.simulation import update_simulation
        grid = [[Plot(x=0, y=0, plant=Plant(type_id="juniper", planted_at=100.0, last_watered_at=100.0, health_state=HealthState.DEAD, growth_stage=GrowthStage.MATURE))]]
        state = GameState(grid=grid, last_update_at=500.0)
        data = state_to_dict(state)
        restored = dict_to_state(data)
        self.assertEqual(restored.grid[0][0].plant.health_state, HealthState.DEAD)
        self.assertEqual(restored.grid[0][0].plant.growth_stage, GrowthStage.MATURE)

        # Offline catch-up must not resurrect dead plant
        update_simulation(restored, current_time=2000.0, is_offline_catchup=True)
        self.assertEqual(restored.grid[0][0].plant.health_state, HealthState.DEAD)

    def test_atomic_save_and_backup(self):
        with patch("vimgarden.storage.SAVE_DIR", self.test_dir), \
             patch("vimgarden.storage.SAVE_FILE", self.save_file), \
             patch("vimgarden.storage.BACKUP_SAVE_FILE", self.backup_file):
            
            state1 = GameState(money=50)
            res1 = save_game(state1)
            self.assertTrue(res1)
            self.assertTrue(self.save_file.exists())
            self.assertFalse(self.backup_file.exists())

            # Second save should create backup of first
            state2 = GameState(money=100)
            res2 = save_game(state2)
            self.assertTrue(res2)
            self.assertTrue(self.backup_file.exists())

            with open(self.backup_file, "r") as f:
                b_data = json.load(f)
            self.assertEqual(b_data["player"]["money"], 50)

            with open(self.save_file, "r") as f:
                s_data = json.load(f)
            self.assertEqual(s_data["player"]["money"], 100)

    def test_corrupted_save_fallback(self):
        corrupt_file = self.test_dir / "save.json.corrupt"
        with patch("vimgarden.storage.SAVE_DIR", self.test_dir), \
             patch("vimgarden.storage.SAVE_FILE", self.save_file), \
             patch("vimgarden.storage.BACKUP_SAVE_FILE", self.backup_file), \
             patch("vimgarden.storage.CORRUPT_SAVE_FILE", corrupt_file):
            
            # Write good backup
            valid_state = GameState(money=77)
            with open(self.backup_file, "w") as f:
                json.dump(state_to_dict(valid_state), f)

            # Corrupt primary file
            with open(self.save_file, "w") as f:
                f.write("corrupted json {{{{")

            loaded = load_game()
            self.assertEqual(loaded.money, 77)
            # Primary corrupted file should be safely preserved as .corrupt
            self.assertTrue(corrupt_file.exists())
            self.assertFalse(self.save_file.exists())

            # Next save should create a new save.json and not corrupt backup
            save_game(loaded)
            self.assertTrue(self.save_file.exists())
            with open(self.backup_file, "r") as f:
                b_data = json.load(f)
            self.assertEqual(b_data["player"]["money"], 77)


    def test_environment_and_legacy_carrot_migration(self):
        legacy_data = {
            "version": 1,
            "player": {"money": 40, "inventory": {"carrot": 5}},
            "grid": {"plots": [{"x": 0, "y": 0, "plant": {"type_id": "carrot", "planted_at": 1.0, "last_watered_at": 1.0}}]},
        }
        state = dict_to_state(legacy_data)
        # Carrot should be migrated to juniper
        self.assertNotIn("carrot", state.inventory)
        self.assertEqual(state.inventory.get("juniper"), 5)
        self.assertEqual(state.grid[0][0].plant.type_id, "juniper")
        # Should have at least 3 pots on the Tokonoma shelf
        self.assertGreaterEqual(len(state.grid[0]), 3)

    def test_load_raw_save_and_revert_save(self):
        with patch("vimgarden.storage.SAVE_DIR", self.test_dir), \
             patch("vimgarden.storage.SAVE_FILE", self.save_file):

            # Non-existent file
            self.assertIsNone(load_raw_save())

            # Revert with None when file doesn't exist -> success, file remains absent
            self.assertTrue(revert_save(None))
            self.assertFalse(self.save_file.exists())

            # Write initial save data
            initial_data = {"player": {"money": 50}}
            self.assertTrue(revert_save(initial_data))
            self.assertTrue(self.save_file.exists())
            loaded = load_raw_save()
            self.assertEqual(loaded["player"]["money"], 50)

            # Revert with None when file exists -> deletes file
            self.assertTrue(revert_save(None))
            self.assertFalse(self.save_file.exists())


if __name__ == "__main__":
    unittest.main()

