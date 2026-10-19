import unittest
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.data_struct import TruckState, objectiveFunction
from src.algorithm.sideways_hill_climbing import SidewaysHillClimbing

class TestSidewaysHillClimbing(unittest.TestCase):
    def setUp(self):
        input_path = os.path.join(os.path.dirname(__file__), "..", "input", "input1.json")
        self.initial_state = TruckState.from_json(input_path)

    def test_sideways_moves_limit(self):
        """Uji batas maksimum gerakan sideways."""
        shc = SidewaysHillClimbing(self.initial_state, max_sideways_moves=5)
        best_state = shc.optimize()
        self.assertIsNotNone(best_state)

    def test_objective_function_improvement(self):
        """Uji apakah fungsi objektif meningkat setelah optimisasi."""
        shc = SidewaysHillClimbing(self.initial_state, max_sideways_moves=5)
        best_state = shc.optimize()
        self.assertGreaterEqual(objectiveFunction(best_state), objectiveFunction(self.initial_state))
    
if __name__ == "__main__":
    unittest.main()