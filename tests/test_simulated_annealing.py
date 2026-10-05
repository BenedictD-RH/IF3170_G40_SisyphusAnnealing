import unittest
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
import math
from src.data_struct import TruckState, objectiveFunction
from src.algorithm.simulated_annealing import SimulatedAnnealing
from src.algorithm.simulated_annaeling import SimulatedAnnealing as SA_Alias


class TestSimulatedAnnealing(unittest.TestCase):
    def setUp(self):
        input_path = os.path.join(os.path.dirname(__file__), "..", "input", "input1.json")
        self.initial_state = TruckState.from_json(input_path)

    def test_alias_import(self):
        """Pastikan import dari simulated_annaeling.py tetap berfungsi."""
        sa = SA_Alias(self.initial_state)
        self.assertIsInstance(sa, SimulatedAnnealing)

    def test_parameter_configuration_and_setters(self):
        """Menguji konfigurasi parameter awal dan metode setter."""
        sa = SimulatedAnnealing(
            self.initial_state,
            initial_temp=500.0,
            cooling_rate=0.98,
            min_temp=0.05,
            max_iterations=800,
            steps_per_temp=5,
            cooling_schedule="linear",
            step_size=3
        )

        self.assertEqual(sa.initial_temp, 500.0)
        self.assertEqual(sa.temp, 500.0)
        self.assertEqual(sa.cooling_rate, 0.98)
        self.assertEqual(sa.min_temp, 0.05)
        self.assertEqual(sa.max_iterations, 800)
        self.assertEqual(sa.steps_per_temp, 5)
        self.assertEqual(sa.cooling_schedule, "linear")
        self.assertEqual(sa.step_size, 3)

        # Uji setter
        sa.set_temperature(250.0)
        self.assertEqual(sa.temp, 250.0)

        sa.set_initial_temp(1000.0)
        self.assertEqual(sa.initial_temp, 1000.0)
        self.assertEqual(sa.temp, 1000.0)

        sa.set_cooling_rate(0.92)
        self.assertEqual(sa.cooling_rate, 0.92)

        sa.set_min_temp(0.0001)
        self.assertEqual(sa.min_temp, 0.0001)

        sa.set_cooling_schedule("logarithmic")
        self.assertEqual(sa.cooling_schedule, "logarithmic")

        sa.set_steps_per_temp(10)
        self.assertEqual(sa.steps_per_temp, 10)

    def test_acceptance_probability_behavior(self):
        """
        Menguji probabilitas penerimaan:
        - Better move (delta > 0) -> selalu probabilitas 1.0
        - Worse move pada T tinggi -> probabilitas tinggi mendekati 1
        - Worse move pada T mendekati 0 -> probabilitas mendekati 0
        """
        sa = SimulatedAnnealing(self.initial_state, initial_temp=1000.0)

        # Better move
        accepted, prob = sa.should_accept(current_cost=50.0, neighbor_cost=70.0, temp=100.0)
        self.assertTrue(accepted)
        self.assertEqual(prob, 1.0)

        # Worse move pada T sangat tinggi (10000.0) untuk delta kecil (-5)
        prob_high = sa.acceptance_probability(delta=-5.0, temp=10000.0)
        self.assertAlmostEqual(prob_high, math.exp(-5.0 / 10000.0), places=4)
        self.assertGreater(prob_high, 0.99)

        # Worse move pada T sangat rendah (0.001) untuk delta (-5)
        prob_low = sa.acceptance_probability(delta=-5.0, temp=0.001)
        self.assertEqual(prob_low, 0.0)

    def test_cooling_schedules(self):
        """Menguji berbagai macam cooling schedules."""
        sa = SimulatedAnnealing(self.initial_state, initial_temp=100.0, cooling_rate=0.9)

        # Geometric
        sa.set_cooling_schedule("geometric")
        next_t = sa.compute_next_temp(100.0, iteration=1)
        self.assertAlmostEqual(next_t, 90.0)

        # Linear
        sa.set_cooling_schedule("linear")
        sa.set_cooling_rate(5.0)
        next_t = sa.compute_next_temp(100.0, iteration=1)
        self.assertAlmostEqual(next_t, 95.0)

        # Logarithmic
        sa.set_cooling_schedule("logarithmic")
        sa.set_cooling_rate(1.0)
        next_t = sa.compute_next_temp(100.0, iteration=1)
        expected = 100.0 / (1.0 + 1.0 * math.log(2.0))
        self.assertAlmostEqual(next_t, expected)

        # Cosine
        sa.set_cooling_schedule("cosine")
        sa.max_iterations = 100
        sa.min_temp = 0.0
        sa.initial_temp = 100.0
        next_t = sa.compute_next_temp(100.0, iteration=50) # at halfway, cos(pi/2)=0 -> 50.0
        self.assertAlmostEqual(next_t, 50.0, delta=1.0)

        # Custom Callable
        sa.set_cooling_schedule(lambda t, it: t * 0.5)
        next_t = sa.compute_next_temp(100.0, iteration=1)
        self.assertEqual(next_t, 50.0)

    def test_optimization_and_metrics_tracking(self):
        """Menguji eksekusi optimasi lengkap dan metrik yang dicatat."""
        initial_cost = objectiveFunction(self.initial_state)
        sa = SimulatedAnnealing(
            self.initial_state,
            initial_temp=100.0,
            cooling_rate=0.9,
            min_temp=1.0,
            max_iterations=100,
            steps_per_temp=2
        )
        best_state = sa.optimize()
        best_cost = objectiveFunction(best_state)

        self.assertGreaterEqual(best_cost, initial_cost)
        self.assertGreater(sa.total_iterations, 0)
        self.assertGreater(len(sa.history), 0)
        self.assertGreater(len(sa.temperatures), 0)
        self.assertGreater(len(sa.costs), 0)
        self.assertGreaterEqual(sa.accepted_better_moves, 0)
        self.assertGreaterEqual(sa.accepted_worse_moves, 0)
        self.assertGreaterEqual(sa.rejected_moves, 0)


if __name__ == "__main__":
    unittest.main()
