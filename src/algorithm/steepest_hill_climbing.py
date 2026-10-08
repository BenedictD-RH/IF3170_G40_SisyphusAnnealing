from .hill_climbing import HillClimbing, TruckState
from data_struct import objectiveFunction, TruckState
import math
import time
import copy


class SteepestHillClimbing(HillClimbing):
    def __init__(self, initial_state: TruckState, max_iterations: int = 1000, step_size: int = 2, temperature: float = 1.0, random_init: bool = True):
        super().__init__(initial_state=initial_state, max_iterations=max_iterations, step_size=step_size, random_init=random_init)
        self.temperature = float(temperature)

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
                neighbors = self.get_all_neighbors(self.current_state)
                best_neighbor = -1
                best_neighbor_val = current_cost
                for i in range(len(neighbors)) :
                        
                    neighbor_cost = objectiveFunction(neighbors[i])
                    
                    if  neighbor_cost > best_neighbor_val :
                        best_neighbor = i
                        best_neighbor_val = neighbor_cost
    
                accepted = best_neighbor != -1
                if accepted:
                    self.current_state = neighbors[best_neighbor]
                    current_cost = objectiveFunction(self.current_state)
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
                print(current_cost)
                
    
            self.execution_time = time.time() - start_time
            return self.best_state