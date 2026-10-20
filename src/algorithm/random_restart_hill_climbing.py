from .hill_climbing import HillClimbing, TruckState
try:
    from src.data_struct import objectiveFunction, TruckState
except ImportError:
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
        return self.initial_state.generate_random_state()

    def optimize(self) -> TruckState:
        start_time = time.time()
        best_state = copy.deepcopy(self.current_state)
        best_cost = objectiveFunction(best_state)
        self.accepted_moves = 0
        self.history = [{
            "iteration": 0,
            "current_cost": best_cost,
            "best_cost": best_cost,
            "accepted": True
        }]

        total_steps = 0
        for restart in range(self.max_restarts):
            if restart == 0 and not getattr(self, 'random_init', True):
                self.current_state = copy.deepcopy(self.initial_state)
            else:
                self.current_state = self.random_initial_state()
            current_cost = objectiveFunction(self.current_state)

            if current_cost > best_cost:
                best_state = copy.deepcopy(self.current_state)
                best_cost = current_cost

            for _ in range(self.max_iterations):
                total_steps += 1
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
                self.accepted_moves += 1

                if current_cost > best_cost:
                    best_state = copy.deepcopy(self.current_state)
                    best_cost = current_cost

                self.history.append({
                    "iteration": total_steps,
                    "current_cost": current_cost,
                    "best_cost": best_cost,
                    "accepted": True
                })

        self.execution_time = time.time() - start_time
        self.best_state = best_state
        return best_state

    

    