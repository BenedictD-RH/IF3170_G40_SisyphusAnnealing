import unittest
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from src.data_struct import (
    Truck,
    Package,
    PackageState,
    TruckState,
    objectiveFunction,
    intersectingArea,
    isIntersecting,
    isStackedOn
)


class TestDataStruct(unittest.TestCase):
    def setUp(self):
        self.input1_path = os.path.join(os.path.dirname(__file__), "..", "input", "input1.json")

    def test_truck_and_package_creation(self):
        truck = Truck(dimensions={"w": 10, "l": 20, "h": 5}, maxCapacity=10)
        self.assertEqual(truck.dimensions["w"], 10)
        self.assertEqual(truck.maxCapacity, 10)

        pkg = Package(id="P1", dimensions={"w": 3, "l": 4, "h": 1}, value=60, weight=5, isFragile=False, eta=3)
        self.assertEqual(pkg.getVolume(), 12)
        self.assertEqual(pkg.getValuePerUnit(), 5.0)

    def test_package_state_bounding_box(self):
        pkg = Package(id="P1", dimensions={"w": 3, "l": 4, "h": 1}, value=60, weight=5, isFragile=False, eta=3)
        ps = PackageState(pkg, coordinates={"x": 1, "y": 2, "z": 0}, orientation={"x": "w", "y": "l", "z": "h"})
        bb = ps.getAbsoluteBB()
        self.assertEqual(bb, (1, 2, 0, 4, 6, 1))

    def test_truck_state_load_from_json(self):
        ts = TruckState.from_json(self.input1_path)
        self.assertEqual(len(ts.packages), 2)
        self.assertEqual(ts.truck.dimensions["w"], 10)
        val = objectiveFunction(ts)
        self.assertIsInstance(val, (int, float))

    def test_intersection_and_overflow(self):
        p1 = PackageState(
            Package("P1", {"w": 2, "l": 2, "h": 2}, 10, 2, False, 1),
            {"x": 0, "y": 0, "z": 0},
            {"x": "w", "y": "l", "z": "h"}
        )
        p2 = PackageState(
            Package("P2", {"w": 2, "l": 2, "h": 2}, 10, 2, False, 1),
            {"x": 1, "y": 1, "z": 0},
            {"x": "w", "y": "l", "z": "h"}
        )
        p3 = PackageState(
            Package("P3", {"w": 2, "l": 2, "h": 2}, 10, 2, False, 1),
            {"x": 5, "y": 5, "z": 0},
            {"x": "w", "y": "l", "z": "h"}
        )
        self.assertTrue(isIntersecting(p1, p2))
        self.assertFalse(isIntersecting(p1, p3))


if __name__ == "__main__":
    unittest.main()
