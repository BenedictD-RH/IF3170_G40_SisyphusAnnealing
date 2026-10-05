from src.data_struct import Truck, TruckState,PackageState,Package,objectiveFunction
import math
import random
import copy


class HillClimbing:
    def __init__(self, initial_state: TruckState, max_iterations: int = 1000):
        self.current_state = initial_state
        self.best_state = copy.deepcopy(initial_state)
        self.max_iterations = max_iterations

    def get_neighbor(self, state: TruckState) -> TruckState:
        neighbor = copy.deepcopy(state)
        if not neighbor.packages:
            return neighbor

        pkg_state = random.choice(neighbor.packages)
        action = random.choice(["move", "rotate"])

        if action == "move":
            pkg_state.coordinates["x"] += random.randint(-2, 2)
            pkg_state.coordinates["y"] += random.randint(-2, 2)
            pkg_state.coordinates["z"] += random.randint(-2, 2)
        elif action == "rotate":
            axes = ["x", "y", "z"]
            random.shuffle(axes)
            pkg_state.orientation = {
                "x": axes[0],
                "y": axes[1],
                "z": axes[2]
            }

        return neighbor

    def should_accept(self, current_cost: float, neighbor_cost: float) -> bool:
        return neighbor_cost > current_cost

    def optimize(self) -> TruckState:
        current_cost = objectiveFunction(self.current_state)
        best_cost = current_cost

        for _ in range(self.max_iterations):
            neighbor = self.get_neighbor(self.current_state)
            neighbor_cost = objectiveFunction(neighbor)

            if self.should_accept(current_cost, neighbor_cost):
                self.current_state = neighbor
                current_cost = neighbor_cost

                if current_cost > best_cost:
                    self.best_state = copy.deepcopy(self.current_state)
                    best_cost = current_cost

        return self.best_state