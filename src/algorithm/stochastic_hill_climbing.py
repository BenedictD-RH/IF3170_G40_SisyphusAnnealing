from .hill_climbing import HillClimbing, TruckState
import math
import random
import copy


class StochasticHillClimbing(HillClimbing):
    def __init__(self, initial_state: TruckState, max_iterations: int = 1000, step_size: int = 2, temperature: float = 1.0, random_init: bool = True):
        super().__init__(initial_state=initial_state, max_iterations=max_iterations, step_size=step_size, random_init=random_init)
        self.temperature = max(1e-8, float(temperature))

    def should_accept(self, current_cost: float, neighbor_cost: float) -> bool:
        if neighbor_cost <= current_cost:
            return False
        
        delta = neighbor_cost - current_cost
        scaled_delta = delta / self.temperature
        
        # Hindari math overflow pada exp
        if scaled_delta > 700:
            return True
        elif scaled_delta < -700:
            return False

        probability = 1.0 / (1.0 + math.exp(-scaled_delta))
        return random.random() < probability