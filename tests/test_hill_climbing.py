import unittest
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from src.data_struct import TruckState, objectiveFunction
from src.algorithm.hill_climbing import HillClimbing


class TestHillClimbing(unittest.TestCase):
    def setUp(self):
        input_path = os.path.join(os.path.dirname(__file__), "..", "input", "input1.json")
        self.initial_state = TruckState.from_json(input_path)

    def test_initialization(self):
        hc = HillClimbing(self.initial_state, max_iterations=100, step_size=3)
        self.assertEqual(hc.max_iterations, 100)
        self.assertEqual(hc.step_size, 3)

    def test_neighbor_generation(self):
        hc = HillClimbing(self.initial_state, max_iterations=10)
        neighbor = hc.get_neighbor(self.initial_state)
        self.assertIsNotNone(neighbor)
        self.assertEqual(len(neighbor.packages), len(self.initial_state.packages))
        # Ensure objective function can compute neighbor without error
        cost = objectiveFunction(neighbor)
        self.assertIsInstance(cost, (int, float))

    def test_strictly_better_acceptance(self):
        hc = HillClimbing(self.initial_state)
        self.assertTrue(hc.should_accept(current_cost=50.0, neighbor_cost=55.0))
        self.assertFalse(hc.should_accept(current_cost=50.0, neighbor_cost=50.0))
        self.assertFalse(hc.should_accept(current_cost=50.0, neighbor_cost=45.0))

    def test_optimization_run(self):
        initial_cost = objectiveFunction(self.initial_state)
        hc = HillClimbing(self.initial_state, max_iterations=50)
        best_state = hc.optimize()
        best_cost = objectiveFunction(best_state)

        # Best cost should be >= initial cost for Hill Climbing
        self.assertGreaterEqual(best_cost, initial_cost)
        self.assertGreater(len(hc.history), 0)
        self.assertGreaterEqual(hc.execution_time, 0.0)


if __name__ == "__main__":
    unittest.main()
