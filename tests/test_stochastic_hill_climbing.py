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

    def test_initialization(self):
        shc = StochasticHillClimbing(self.initial_state, max_iterations=200, temperature=5.0)
        self.assertEqual(shc.temperature, 5.0)
        self.assertEqual(shc.max_iterations, 200)

    def test_rejection_of_worse_or_equal_moves(self):
        shc = StochasticHillClimbing(self.initial_state, temperature=1.0)
        # Worse or equal moves should always be rejected
        self.assertFalse(shc.should_accept(current_cost=50.0, neighbor_cost=50.0))
        self.assertFalse(shc.should_accept(current_cost=50.0, neighbor_cost=40.0))

    def test_probabilistic_acceptance_of_better_moves(self):
        shc = StochasticHillClimbing(self.initial_state, temperature=1.0)
        # A huge improvement should almost always be accepted
        accepted_count = sum(shc.should_accept(current_cost=10.0, neighbor_cost=100.0) for _ in range(50))
        self.assertEqual(accepted_count, 50)

    def test_optimization_run(self):
        initial_cost = objectiveFunction(self.initial_state)
        shc = StochasticHillClimbing(self.initial_state, max_iterations=50, temperature=2.0)
        best_state = shc.optimize()
        best_cost = objectiveFunction(best_state)

        self.assertGreaterEqual(best_cost, initial_cost)
        self.assertGreater(len(shc.history), 0)


if __name__ == "__main__":
    unittest.main()
