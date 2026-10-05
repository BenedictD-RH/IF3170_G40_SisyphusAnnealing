import time
import math
import random
import copy
from src.data_struct import Truck, TruckState, PackageState, Package, objectiveFunction


class HillClimbing:
    def __init__(self, initial_state: TruckState, max_iterations: int = 1000, step_size: int = 2):
        self.initial_state = copy.deepcopy(initial_state)
        self.current_state = copy.deepcopy(initial_state)
        self.best_state = copy.deepcopy(initial_state)
        self.max_iterations = max_iterations
        self.step_size = step_size
        self.history: list[dict] = []
        self.accepted_moves: int = 0
        self.total_iterations: int = 0
        self.execution_time: float = 0.0

    def get_neighbor(self, state: TruckState) -> TruckState:
        """Menghasilkan tetangga dengan menggeser, merotasi, atau melompatkan posisi salah satu paket."""
        neighbor = copy.deepcopy(state)
        if not neighbor.packages:
            return neighbor

        pkg_state = random.choice(neighbor.packages)
        action = random.choice(["move", "rotate", "jump"])

        if action == "move":
            step = self.step_size
            pkg_state.coordinates["x"] = max(0, pkg_state.coordinates["x"] + random.randint(-step, step))
            pkg_state.coordinates["y"] = max(0, pkg_state.coordinates["y"] + random.randint(-step, step))
            pkg_state.coordinates["z"] = max(0, pkg_state.coordinates["z"] + random.randint(-step, step))
        elif action == "rotate":
            dims = ["w", "l", "h"]
            random.shuffle(dims)
            pkg_state.orientation = {
                "x": dims[0],
                "y": dims[1],
                "z": dims[2]
            }
        elif action == "jump":
            truck_dim = neighbor.truck.dimensions
            pkg_state.coordinates["x"] = random.randint(0, max(0, truck_dim.get("w", 10) - 1))
            pkg_state.coordinates["y"] = random.randint(0, max(0, truck_dim.get("l", 10) - 1))
            pkg_state.coordinates["z"] = random.randint(0, max(0, truck_dim.get("h", 10) - 1))

        return neighbor

    def should_accept(self, current_cost: float, neighbor_cost: float) -> bool:
        """Hill Climbing standar: hanya terima jika Strictly Better."""
        return neighbor_cost > current_cost

    def optimize(self) -> TruckState:
        start_time = time.time()
        current_cost = objectiveFunction(self.current_state)
        best_cost = current_cost
        
        self.history = [{
            "iteration": 0,
            "current_cost": current_cost,
            "best_cost": best_cost,
            "accepted": True
        }]
        self.accepted_moves = 0
        self.total_iterations = 0

        for i in range(1, self.max_iterations + 1):
            self.total_iterations = i
            neighbor = self.get_neighbor(self.current_state)
            neighbor_cost = objectiveFunction(neighbor)

            accepted = self.should_accept(current_cost, neighbor_cost)
            if accepted:
                self.current_state = neighbor
                current_cost = neighbor_cost
                self.accepted_moves += 1

                if current_cost > best_cost:
                    self.best_state = copy.deepcopy(self.current_state)
                    best_cost = current_cost

            self.history.append({
                "iteration": i,
                "current_cost": current_cost,
                "best_cost": best_cost,
                "accepted": accepted
            })

        self.execution_time = time.time() - start_time
        return self.best_state