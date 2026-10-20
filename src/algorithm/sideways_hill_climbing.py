from .hill_climbing import HillClimbing, TruckState
from data_struct import objectiveFunction, TruckState
import math
import time
import copy


class SidewaysHillClimbing(HillClimbing):
    def __init__(self, initial_state: TruckState, max_iterations: int = 1000, step_size: int = 2, random_init: bool = True, max_sideways_moves: int = 100):
        super().__init__(initial_state=initial_state, max_iterations=max_iterations, step_size=step_size, random_init=random_init)
        self.max_sideways_moves = max_sideways_moves

    def optimize(self) -> TruckState:
        start_time = time.time()
        current_cost = objectiveFunction(self.current_state)
        best_cost = current_cost
        sideways_moves = 0

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
            neighbors = self.get_all_neighbors(self.current_state)
            best_neighbor = -1
            best_neighbor_val = current_cost

            for j in range(len(neighbors)):
                neighbor_cost = objectiveFunction(neighbors[j])

                if neighbor_cost > best_neighbor_val:
                    best_neighbor = j
                    best_neighbor_val = neighbor_cost
                elif (neighbor_cost == current_cost 
                      and best_neighbor == -1
                      and sideways_moves < self.max_sideways_moves):
                    best_neighbor = j

            accepted = best_neighbor != -1

            if accepted:
                if best_neighbor_val == current_cost:
                    sideways_moves += 1
                else:
                    sideways_moves = 0

                self.current_state = neighbors[best_neighbor]
                current_cost = best_neighbor_val
                self.accepted_moves += 1

                if current_cost > best_cost:
                    self.best_state = copy.deepcopy(self.current_state)
                    best_cost = current_cost
            else:
                break

            self.history.append({
                "iteration": i,
                "current_cost": current_cost,
                "best_cost": best_cost,
                "accepted": accepted
            })

            if sideways_moves >= self.max_sideways_moves:
                break
            
        self.execution_time = time.time() - start_time
        return self.best_state
    