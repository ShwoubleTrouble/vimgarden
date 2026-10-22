"""Unit tests for bonsai simulation logic and offline catch-up."""
import unittest

from vimgarden.data.plants_data import PLANTS
from vimgarden.enums import GrowthStage, HealthState
from vimgarden.models import GameState, Plant, Plot
from vimgarden.simulation import (
    clear_dead_plot,
    prune_bonsai,
    update_plant,
    update_simulation,
    water_plot,
)


class TestSimulation(unittest.TestCase):
    def setUp(self):
        self.juniper_type = PLANTS["juniper"]  # 90s growth, 45s thirst, 135s wilt, 270s death

    def test_plant_linear_growth_healthy(self):
        plant = Plant(
            type_id="juniper",
            planted_at=1000.0,
            last_watered_at=1000.0,
            effective_growth_seconds=0.0,
        )
        # Advance 20 seconds (all within healthy threshold 45s, < 0.25*90=22.5s -> SEED/SPROUT)
        update_plant(plant, self.juniper_type, t_from=1000.0, t_to=1020.0)
        self.assertEqual(plant.effective_growth_seconds, 20.0)
        self.assertEqual(plant.health_state, HealthState.HEALTHY)
        self.assertEqual(plant.growth_stage, GrowthStage.SEED)

    def test_stage_progression(self):
        plant = Plant(
            type_id="juniper",
            planted_at=1000.0,
            last_watered_at=1000.0,
            effective_growth_seconds=0.0,
        )
        # 20s: Seed (< 22.5s)
        update_plant(plant, self.juniper_type, 1000.0, 1020.0)
        self.assertEqual(plant.growth_stage, GrowthStage.SEED)

        # 40s: Sprout/Sapling (22.5s .. 63s)
        plant.last_watered_at = 1020.0
        update_plant(plant, self.juniper_type, 1020.0, 1040.0)
        self.assertEqual(plant.growth_stage, GrowthStage.SPROUT)

        # 70s: Adult/Branched (63s .. 90s)
        plant.last_watered_at = 1040.0
        update_plant(plant, self.juniper_type, 1040.0, 1070.0)
        self.assertEqual(plant.growth_stage, GrowthStage.ADULT)

        # 95s: Mature (>= 90s)
        plant.last_watered_at = 1070.0
        update_plant(plant, self.juniper_type, 1070.0, 1095.0)
        self.assertEqual(plant.growth_stage, GrowthStage.MATURE)

    def test_thirst_slows_growth(self):
        plant = Plant(
            type_id="juniper",
            planted_at=1000.0,
            last_watered_at=1000.0,
            effective_growth_seconds=0.0,
        )
        # Thirst threshold = 45s, Wilt threshold = 135s
        # Interval from 0 to 65s:
        # Healthy: [0, 45] = 45s * 1.0 = 45.0
        # Thirsty: [45, 65] = 20s * 0.25 = 5.0
        # Total growth = 50.0
        update_plant(plant, self.juniper_type, 1000.0, 1065.0)
        self.assertAlmostEqual(plant.effective_growth_seconds, 50.0)
        self.assertEqual(plant.health_state, HealthState.THIRSTY)

    def test_wilting_halts_growth(self):
        plant = Plant(
            type_id="juniper",
            planted_at=1000.0,
            last_watered_at=1000.0,
            effective_growth_seconds=0.0,
        )
        # Healthy: [0, 45] = 45.0
        # Thirsty: [45, 135] = 90 * 0.25 = 22.5
        # Wilting: [135, 160] = 25 * 0.0 = 0.0
        # Total growth = 67.5
        update_plant(plant, self.juniper_type, 1000.0, 1160.0)
        self.assertAlmostEqual(plant.effective_growth_seconds, 67.5)
        self.assertEqual(plant.health_state, HealthState.WILTING)

    def test_death_without_offline_protection(self):
        plant = Plant(
            type_id="juniper",
            planted_at=1000.0,
            last_watered_at=1000.0,
            effective_growth_seconds=0.0,
        )
        # 280s > death_threshold (270s)
        update_plant(plant, self.juniper_type, 1000.0, 1280.0, is_offline_catchup=False)
        self.assertEqual(plant.health_state, HealthState.DEAD)

    def test_offline_catchup_grace_protection(self):
        plant = Plant(
            type_id="juniper",
            planted_at=1000.0,
            last_watered_at=1000.0,
            effective_growth_seconds=0.0,
        )
        # Long offline absence: 10000 seconds
        update_plant(plant, self.juniper_type, 1000.0, 11000.0, is_offline_catchup=True)
        self.assertEqual(plant.health_state, HealthState.WILTING)

    def test_water_and_prune(self):
        plot = Plot(
            x=0,
            y=0,
            plant=Plant(
                type_id="juniper",
                planted_at=1000.0,
                last_watered_at=1000.0,
                effective_growth_seconds=90.0,
                growth_stage=GrowthStage.MATURE,
            ),
        )
        # Watering
        res = water_plot(plot, current_time=1050.0)
        self.assertTrue(res)
        self.assertEqual(plot.plant.last_watered_at, 1050.0)

        # Pruning mature tree gives coins and rolls back to ADULT without deleting tree
        prune_res = prune_bonsai(plot)
        self.assertIsNotNone(prune_res)
        type_id, sell_price = prune_res
        self.assertEqual(type_id, "juniper")
        self.assertEqual(sell_price, self.juniper_type.sell_price)
        self.assertIsNotNone(plot.plant)
        self.assertEqual(plot.plant.growth_stage, GrowthStage.ADULT)


if __name__ == "__main__":
    unittest.main()
