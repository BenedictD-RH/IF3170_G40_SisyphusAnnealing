from .hill_climbing import HillClimbing, TruckState
import math
import random
import copy


class StochasticHillClimbing(HillClimbing):
    """
    Stochastic Hill Climbing.
    - Pada T > 0: Menerima langkah perbaikan (delta > 0) secara probabilistik menggunakan fungsi logistic: P = 1 / (1 + exp(-delta/T)).
    - Pada T <= 0: Berperilaku murni GREEDY (hanya menerima jika delta > 0 dengan kepastian 100%).
    - Langkah delta <= 0 selalu ditolak.
    """
    def __init__(self, initial_state: TruckState, max_iterations: int = 1000, step_size: int = 2, temperature: float = 1.0, random_init: bool = True):
        super().__init__(initial_state=initial_state, max_iterations=max_iterations, step_size=step_size, random_init=random_init)
        self.temperature = float(temperature)

    def should_accept(self, current_cost: float, neighbor_cost: float) -> bool:
        # Penolakan mutlak untuk state yang lebih buruk atau sama
        if neighbor_cost <= current_cost:
            return False

        delta = neighbor_cost - current_cost

        # Handler saat suhu 0 atau mendekati 0: Berperilaku murni GREEDY (100% terima jika delta > 0)
        if self.temperature <= 0.0:
            return True

        scaled_delta = delta / self.temperature

        # Hindari math overflow / underflow pada exp
        if scaled_delta > 700:
            return True
        elif scaled_delta < -700:
            return False

        probability = 1.0 / (1.0 + math.exp(-scaled_delta))
        return random.random() < probability