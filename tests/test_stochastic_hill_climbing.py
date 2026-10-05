import unittest
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.data_struct import TruckState, objectiveFunction
from src.algorithm.stochastic_hill_climbing import StochasticHillClimbing


class TestStochasticHillClimbing(unittest.TestCase):
    def setUp(self):
        input_path = os.path.join(os.path.dirname(__file__), "..", "input", "input1.json")
        self.initial_state = TruckState.from_json(input_path)

    def test_initialization_and_manual_temp(self):
        """Uji inisialisasi dan pengaturan manual parameter suhu (temperature)."""
        # Manual input temperature = 25.5
        shc = StochasticHillClimbing(self.initial_state, max_iterations=200, temperature=25.5, random_init=False)
        self.assertEqual(shc.temperature, 25.5)
        self.assertEqual(shc.max_iterations, 200)

        # Ubah temperatur secara dinamis
        shc.temperature = 5.0
        self.assertEqual(shc.temperature, 5.0)

    def test_random_initial_state(self):
        """Uji eksekusi dengan random initial state."""
        shc_rand = StochasticHillClimbing(self.initial_state, max_iterations=50, temperature=2.0, random_init=True)
        self.assertIsNotNone(shc_rand.current_state)
        best_state = shc_rand.optimize()
        self.assertIsNotNone(best_state)

    def test_rejection_of_worse_or_equal_moves(self):
        """Uji penolakan mutlak untuk gerakan bernilai lebih buruk atau sama."""
        shc = StochasticHillClimbing(self.initial_state, temperature=1.0)
        self.assertFalse(shc.should_accept(current_cost=50.0, neighbor_cost=50.0))
        self.assertFalse(shc.should_accept(current_cost=50.0, neighbor_cost=40.0))

    def test_probabilistic_acceptance_of_better_moves(self):
        """Uji penerimaan probabilistik terhadap gerakan bernilai lebih baik."""
        shc = StochasticHillClimbing(self.initial_state, temperature=1.0)
        # Peningkatan delta besar (+90) hampir pasti diterima (prob ~ 1.0)
        accepted_count = sum(shc.should_accept(current_cost=10.0, neighbor_cost=100.0) for _ in range(50))
        self.assertEqual(accepted_count, 50)

    def test_zero_temperature_greedy_behavior(self):
        """Uji bahwa pada T <= 0, Stochastic Hill Climbing berperilaku murni Greedy."""
        shc_zero = StochasticHillClimbing(self.initial_state, temperature=0.0)
        # Pada T = 0, delta > 0 harus 100% diterima
        self.assertTrue(shc_zero.should_accept(current_cost=10.0, neighbor_cost=10.1))
        # delta <= 0 harus 100% ditolak
        self.assertFalse(shc_zero.should_accept(current_cost=10.0, neighbor_cost=10.0))
        self.assertFalse(shc_zero.should_accept(current_cost=10.0, neighbor_cost=9.9))


    def test_optimization_run(self):
        """Uji eksekusi optimasi Stochastic Hill Climbing."""
        shc = StochasticHillClimbing(self.initial_state, max_iterations=50, temperature=2.0)
        best_state = shc.optimize()
        best_cost = objectiveFunction(best_state)

        self.assertIsInstance(best_cost, (int, float))
        self.assertGreater(len(shc.history), 0)
        self.assertGreaterEqual(shc.execution_time, 0.0)


if __name__ == "__main__":
    unittest.main()
