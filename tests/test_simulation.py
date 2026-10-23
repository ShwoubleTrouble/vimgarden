"""Unit tests for bonsai simulation logic and offline catch-up."""
import unittest

from vimgarden.data.plants_data import PLANTS
from vimgarden.enums import BonsaiStyle, GrowthStage, HealthState, Season, Weather
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

    def test_rain_auto_waters_plots(self):
        plant = Plant(
            type_id="juniper",
            planted_at=1000.0,
            last_watered_at=1000.0,
            health_state=HealthState.THIRSTY,
        )
        state = GameState(
            grid=[[Plot(x=0, y=0, plant=plant)]],
            last_update_at=1000.0,
            weather=Weather.SUNNY,
        )
        # Advance simulation and set weather to RAINY
        state.weather = Weather.RAINY
        update_simulation(state, current_time=1050.0)
        self.assertEqual(plant.last_watered_at, 1050.0)
        self.assertEqual(plant.health_state, HealthState.HEALTHY)

    def test_fertilizer_boost(self):
        plant_normal = Plant(
            type_id="juniper",
            planted_at=1000.0,
            last_watered_at=1000.0,
            effective_growth_seconds=0.0,
        )
        plant_fertilized = Plant(
            type_id="juniper",
            planted_at=1000.0,
            last_watered_at=1000.0,
            effective_growth_seconds=0.0,
            fertilized_remaining_seconds=60.0,
        )
        update_plant(plant_normal, self.juniper_type, 1000.0, 1020.0)
        update_plant(plant_fertilized, self.juniper_type, 1000.0, 1020.0)
        self.assertGreater(plant_fertilized.effective_growth_seconds, plant_normal.effective_growth_seconds)

    def test_prune_seasonal_and_decor_bonuses(self):
        maple_type = PLANTS["maple"]
        plot = Plot(
            x=0,
            y=0,
            plant=Plant(
                type_id="maple",
                planted_at=1000.0,
                last_watered_at=1000.0,
                effective_growth_seconds=300.0,
                growth_stage=GrowthStage.MATURE,
            ),
        )
        # Normal prune in Spring
        _, normal_price = prune_bonsai(plot, season=Season.SPRING)
        self.assertEqual(normal_price, maple_type.sell_price)

        # Autumn bonus (+35%) + Toro Lantern (+20%)
        plot.plant.growth_stage = GrowthStage.MATURE
        _, buffed_price = prune_bonsai(plot, season=Season.AUTUMN, decorations=["toro_lantern"])
        expected = int(int(maple_type.sell_price * 1.35) * 1.20)
        self.assertEqual(buffed_price, expected)

    def test_tree_age_and_style_bonuses(self):
        juniper_type = PLANTS["juniper"]
        plot = Plot(
            x=0,
            y=0,
            plant=Plant(
                type_id="juniper",
                planted_at=1000.0,
                last_watered_at=1000.0,
                effective_growth_seconds=90.0,
                growth_stage=GrowthStage.MATURE,
                style=BonsaiStyle.KENGAI,
            ),
        )
        # Base sell_price = 35. KENGAI (+25%) -> 43.
        # After 10 days (864000s) -> +50% -> int(43 * 1.50) = 64
        _, price = prune_bonsai(plot, current_time=1000.0 + 864000.0)
        self.assertEqual(price, 64)

    def test_format_tree_age(self):
        from vimgarden.simulation import format_tree_age
        self.assertEqual(format_tree_age(100.0, 130.0), "30s")
        self.assertEqual(format_tree_age(100.0, 700.0), "10m")
        self.assertEqual(format_tree_age(100.0, 100.0 + 3600.0 * 5), "5h")
        self.assertEqual(format_tree_age(100.0, 100.0 + 86400.0 * 3), "3d")
        self.assertEqual(format_tree_age(100.0, 100.0 + 86400.0 * 45), "1mo")
        self.assertEqual(format_tree_age(100.0, 100.0 + 86400.0 * 400), "1y")

    def test_furin_chime_growth_bonus(self):
        plant_normal = Plant(
            type_id="juniper",
            planted_at=1000.0,
            last_watered_at=1000.0,
            effective_growth_seconds=0.0,
        )
        plant_buffed = Plant(
            type_id="juniper",
            planted_at=1000.0,
            last_watered_at=1000.0,
            effective_growth_seconds=0.0,
        )
        update_plant(plant_normal, self.juniper_type, 1000.0, 1020.0, decorations=[])
        update_plant(plant_buffed, self.juniper_type, 1000.0, 1020.0, decorations=["furin_chime"])
        self.assertAlmostEqual(plant_normal.effective_growth_seconds, 20.0)
        self.assertAlmostEqual(plant_buffed.effective_growth_seconds, 20.0 * 1.15)



if __name__ == "__main__":
    unittest.main()


