from .hill_climbing import HillClimbing, TruckState
from data_struct import objectiveFunction, TruckState
import math
import time
import copy

class RandomRestartHillClimbing(HillClimbing):
    def __init__(self, initial_state: TruckState, max_iterations: int = 1000, step_size: int = 2, random_init: bool = True, max_restarts: int = 10):
        super().__init__(initial_state=initial_state, max_iterations=max_iterations, step_size=step_size, random_init=random_init)
        self.max_restarts = max_restarts
    def random_initial_state(self) -> TruckState:
        """Generate a random initial state."""
        # Implement the logic to generate a random TruckState
        # For example, you can randomly assign values to the attributes of TruckState
        # This is a placeholder implementation; replace it with your actual logic
        random_state = copy.deepcopy(self.current_state)
        # Randomize the state attributes here
        return random_state

    def optimize(self) -> TruckState:
        best_state = self.current_state
        best_cost = objectiveFunction(best_state)

        for restart in range(self.max_restarts):
            self.current_state = self.random_initial_state()
            current_cost = objectiveFunction(self.current_state)

            while True:
                neighbors = self.get_all_neighbors(self.current_state)
                best_neighbor = -1
                best_neighbor_val = current_cost

                for i in range(len(neighbors)):
                    neighbor_cost = objectiveFunction(neighbors[i])

                    if neighbor_cost > best_neighbor_val:
                        best_neighbor = i
                        best_neighbor_val = neighbor_cost

                if best_neighbor == -1:
                    break  # No better neighbor found, exit the loop

                self.current_state = neighbors[best_neighbor]
                current_cost = objectiveFunction(self.current_state)

            if current_cost > best_cost:
                best_state = copy.deepcopy(self.current_state)
                best_cost = current_cost

        return best_state

    

    