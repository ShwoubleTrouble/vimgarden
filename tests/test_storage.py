"""Unit tests for storage serialization, backup, and atomic writing."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vimgarden.models import GameState, Plant, Plot
from vimgarden.storage import dict_to_state, load_game, save_game, state_to_dict


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
        with patch("vimgarden.storage.SAVE_DIR", self.test_dir), \
             patch("vimgarden.storage.SAVE_FILE", self.save_file), \
             patch("vimgarden.storage.BACKUP_SAVE_FILE", self.backup_file):
            
            # Write good backup
            valid_state = GameState(money=77)
            with open(self.backup_file, "w") as f:
                json.dump(state_to_dict(valid_state), f)

            # Corrupt primary file
            with open(self.save_file, "w") as f:
                f.write("corrupted json {{{{")

            loaded = load_game()
            self.assertEqual(loaded.money, 77)


if __name__ == "__main__":
    unittest.main()
