import unittest
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.data_struct import TruckState, objectiveFunction
from src.algorithm.steepest_hill_climbing import SteepestHillClimbing

class TestSteepestHillClimbing(unittest.TestCase):
    def setUp(self):
        input_path = os.path.join(os.path.dirname(__file__), "..", "input", "input1.json")
        self.initial_state = TruckState.from_json(input_path)

    def test_steepest_hill_climbing(self):
        """Uji eksekusi Steepest Hill Climbing."""
        shc = SteepestHillClimbing(self.initial_state)
        best_state = shc.optimize()
        self.assertIsNotNone(best_state)
        

if __name__ == "__main__":
    unittest.main()