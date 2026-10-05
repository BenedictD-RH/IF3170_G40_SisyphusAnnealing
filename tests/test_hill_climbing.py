import unittest
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.data_struct import TruckState, objectiveFunction
from src.algorithm.hill_climbing import HillClimbing


class DummyConcreteHC(HillClimbing):
    """Subclass dummy untuk menguji eksekusi base template HillClimbing."""
    def should_accept(self, current_cost: float, neighbor_cost: float) -> bool:
        return neighbor_cost >= current_cost


class TestHillClimbing(unittest.TestCase):
    def setUp(self):
        input_path = os.path.join(os.path.dirname(__file__), "..", "input", "input1.json")
        self.initial_state = TruckState.from_json(input_path)

    def test_initialization_and_random_init(self):
        """Uji inisialisasi deterministik dan random initial state."""
        # 1. Deterministic init
        hc = DummyConcreteHC(self.initial_state, max_iterations=100, step_size=3, random_init=False)
        self.assertEqual(hc.max_iterations, 100)
        self.assertEqual(hc.step_size, 3)
        self.assertEqual(hc.current_state.packages[0].coordinates, self.initial_state.packages[0].coordinates)

        # 2. Random initial state
        hc_rand = DummyConcreteHC(self.initial_state, max_iterations=100, random_init=True)
        self.assertIsNotNone(hc_rand.current_state)
        self.assertEqual(len(hc_rand.current_state.packages), len(self.initial_state.packages))

    def test_rotate_90_degrees(self):
        """Uji rotasi 90 derajat terhadap sumbu x, y, dan z."""
        hc = DummyConcreteHC(self.initial_state)
        ori = {"x": "w", "y": "l", "z": "h"}

        # Rotasi 90 thd sumbu x -> y dan z bertukar
        rot_x = hc.rotate_90(ori, "x")
        self.assertEqual(rot_x, {"x": "w", "y": "h", "z": "l"})

        # Rotasi 90 thd sumbu y -> x dan z bertukar
        rot_y = hc.rotate_90(ori, "y")
        self.assertEqual(rot_y, {"x": "h", "y": "l", "z": "w"})

        # Rotasi 90 thd sumbu z -> x dan y bertukar
        rot_z = hc.rotate_90(ori, "z")
        self.assertEqual(rot_z, {"x": "l", "y": "w", "z": "h"})

    def test_get_neighbor_single_sample(self):
        """Uji fungsi get_neighbor yang membangkitkan 1 tetangga acak."""
        hc = DummyConcreteHC(self.initial_state, max_iterations=10)
        for _ in range(30):
            neighbor = hc.get_neighbor(self.initial_state)
            self.assertIsNotNone(neighbor)
            self.assertEqual(len(neighbor.packages), len(self.initial_state.packages))
            for p in neighbor.packages:
                self.assertIsInstance(p.coordinates["x"], int)
                self.assertEqual(set(p.orientation.values()), {"w", "l", "h"})

            cost = objectiveFunction(neighbor)
            self.assertIsInstance(cost, (int, float))

    def test_get_all_neighbors(self):
        """Uji fungsi get_all_neighbors yang membangkitkan seluruh tetangga yang memungkinkan."""
        hc = DummyConcreteHC(self.initial_state, step_size=2)
        all_nbrs = hc.get_all_neighbors(self.initial_state)

        self.assertIsInstance(all_nbrs, list)
        self.assertGreater(len(all_nbrs), 0)
        for nbr in all_nbrs:
            self.assertEqual(len(nbr.packages), len(self.initial_state.packages))
            val = objectiveFunction(nbr)
            self.assertIsInstance(val, (int, float))

    def test_base_template_raises_not_implemented(self):
        """Pastikan base template HillClimbing tidak memiliki heuristik konkret (harus NotImplementedError)."""
        base_hc = HillClimbing(self.initial_state)
        with self.assertRaises(NotImplementedError):
            base_hc.should_accept(current_cost=50.0, neighbor_cost=60.0)

    def test_optimization_run(self):
        """Uji eksekusi optimasi dengan template HillClimbing."""
        initial_cost = objectiveFunction(self.initial_state)
        hc = DummyConcreteHC(self.initial_state, max_iterations=50, random_init=False)
        best_state = hc.optimize()
        best_cost = objectiveFunction(best_state)

        self.assertGreaterEqual(best_cost, initial_cost)
        self.assertGreater(len(hc.history), 0)
        self.assertGreaterEqual(hc.execution_time, 0.0)


if __name__ == "__main__":
    unittest.main()
