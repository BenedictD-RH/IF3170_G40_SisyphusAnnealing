import time
import math
import random
import copy
from typing import Callable, Optional, Union
from data_struct import TruckState, objectiveFunction
from .stochastic_hill_climbing import StochasticHillClimbing


class SimulatedAnnealing(StochasticHillClimbing):
    def __init__(self, 
                 initial_state: TruckState, 
                 initial_temp: float = 1000.0, 
                 cooling_rate: float = 0.995, 
                 min_temp: float = 0.001, 
                 max_iterations: int = 1000,
                 steps_per_temp: int = 1,
                 cooling_schedule: Union[str, Callable[[float, int], float]] = "geometric",
                 step_size: int = 2,
                 random_init: bool = True):
        super().__init__(initial_state=initial_state, max_iterations=max_iterations, step_size=step_size, random_init=random_init)
        self.initial_temp = float(initial_temp)
        self.temp = float(initial_temp)
        self.cooling_rate = float(cooling_rate)
        self.min_temp = float(min_temp)
        self.steps_per_temp = max(1, int(steps_per_temp))
        self.cooling_schedule = cooling_schedule

        # Metrics tracking
        self.accepted_better_moves: int = 0
        self.accepted_worse_moves: int = 0
        self.rejected_moves: int = 0
        self.temperatures: list[float] = []
        self.costs: list[float] = []

    # Parameter Setters
    def set_temperature(self, temp: float) -> None:
        self.temp = max(0.0, float(temp))

    def set_initial_temp(self, temp: float) -> None:
        self.initial_temp = max(0.0, float(temp))
        self.temp = self.initial_temp

    def set_cooling_rate(self, cooling_rate: float) -> None:
        self.cooling_rate = float(cooling_rate)

    def set_min_temp(self, min_temp: float) -> None:
        self.min_temp = max(0.0, float(min_temp))

    def set_cooling_schedule(self, schedule: Union[str, Callable[[float, int], float]]) -> None:
        self.cooling_schedule = schedule

    def set_steps_per_temp(self, steps: int) -> None:
        self.steps_per_temp = max(1, int(steps))

    def compute_next_temp(self, current_temp: float, iteration: int) -> float:
        if callable(self.cooling_schedule):
            return max(0.0, self.cooling_schedule(current_temp, iteration))

        schedule = str(self.cooling_schedule).lower()
        if schedule in ("geometric", "exponential"):
            return current_temp * self.cooling_rate
        elif schedule == "linear":
            return max(self.min_temp, current_temp - self.cooling_rate)
        elif schedule == "logarithmic":
            # T_k = T_0 / (1 + cooling_rate * ln(1 + k))
            return self.initial_temp / (1.0 + self.cooling_rate * math.log(1.0 + iteration))
        elif schedule == "cosine":
            # T_k = min_temp + 0.5 * (T_0 - min_temp) * (1 + cos(pi * k / K_max))
            progress = min(1.0, iteration / max(1, self.max_iterations))
            return self.min_temp + 0.5 * (self.initial_temp - self.min_temp) * (1.0 + math.cos(math.pi * progress))
        else:
            # Default fallback to geometric
            return current_temp * self.cooling_rate

    def acceptance_probability(self, delta: float, temp: float) -> float:
        """
        Menghitung probabilitas penerimaan Boltzmann P = exp(delta / T).
        - delta > 0  : Selalu return 1.0 (langkah perbaikan).
        - temp <= 0  : Mode GREEDY -> return 1.0 jika delta > 0, return 0.0 jika delta <= 0.
        - temp -> inf: Mode RANDOM WALK -> return 1.0 untuk semua langkah (karena delta/T -> 0, exp(0) = 1).
        - delta <= 0 : return exp(delta / temp) dalam rentang (0.0, 1.0].
        """
        if delta > 0:
            return 1.0

        if temp <= 0.0:
            # Pada suhu 0 (nol mutlak), tidak ada toleransi langkah buruk -> Greedy
            return 0.0

        if math.isinf(temp) or temp >= 1e12:
            # Pada suhu sangat tinggi / maksimum, semua langkah diterima -> Pure Random Walk
            return 1.0

        exponent = delta / temp
        if exponent < -700:
            return 0.0
        elif exponent > 0:
            return 1.0

        return math.exp(exponent)

    def should_accept(self, current_cost: float, neighbor_cost: float, temp: Optional[float] = None) -> tuple[bool, float]:
        """
        Menentukan apakah tetangga diterima berdasarkan probabilitas Boltzmann.
        - Saat suhu T <= 0: Berperilaku murni GREEDY (hanya menerima jika neighbor_cost > current_cost).
        - Saat suhu T > 0 : Menerima 100% jika neighbor_cost > current_cost, dan menerima probabilistik jika lebih buruk.
        """
        if temp is None:
            temp = self.temp

        delta = neighbor_cost - current_cost
        # greedy pas suhu 0
        if temp <= 0.0:
            accepted = neighbor_cost > current_cost
            prob = 1.0 if accepted else 0.0
            return accepted, prob

        if neighbor_cost > current_cost:
            return True, 1.0

        prob = self.acceptance_probability(delta, temp)
        accepted = random.random() < prob
        return accepted, prob


    def optimize(self) -> TruckState:
        start_time = time.time()
        self.temp = self.initial_temp
        current_cost = objectiveFunction(self.current_state)
        best_cost = current_cost
        self.best_state = copy.deepcopy(self.current_state)

        # Reset metrik
        self.accepted_moves = 0
        self.accepted_better_moves = 0
        self.accepted_worse_moves = 0
        self.rejected_moves = 0
        self.temperatures = [self.temp]
        self.costs = [current_cost]
        self.history = [{
            "iteration": 0,
            "temperature": self.temp,
            "current_cost": current_cost,
            "neighbor_cost": current_cost,
            "best_cost": best_cost,
            "accepted": True,
            "delta": 0.0,
            "probability": 1.0
        }]

        iteration = 0
        step_counter = 0

        while self.temp > self.min_temp and iteration < self.max_iterations:
            iteration += 1
            step_counter += 1

            neighbor = self.get_neighbor(self.current_state)
            neighbor_cost = objectiveFunction(neighbor)
            delta = neighbor_cost - current_cost

            accepted, prob = self.should_accept(current_cost, neighbor_cost, self.temp)

            if accepted:
                self.current_state = neighbor
                current_cost = neighbor_cost
                self.accepted_moves += 1

                if delta > 0:
                    self.accepted_better_moves += 1
                else:
                    self.accepted_worse_moves += 1

                if current_cost > best_cost:
                    self.best_state = copy.deepcopy(self.current_state)
                    best_cost = current_cost
            else:
                self.rejected_moves += 1

            self.temperatures.append(self.temp)
            self.costs.append(current_cost)
            self.history.append({
                "iteration": iteration,
                "temperature": self.temp,
                "current_cost": current_cost,
                "neighbor_cost": neighbor_cost,
                "best_cost": best_cost,
                "accepted": accepted,
                "delta": delta,
                "probability": prob
            })

            # Update temperature after every steps_per_temp iterations
            if step_counter >= self.steps_per_temp:
                self.temp = self.compute_next_temp(self.temp, iteration)
                step_counter = 0

        self.total_iterations = iteration
        self.execution_time = time.time() - start_time
        return self.best_state

    def get_stuck_metrics(self, streak_threshold: int = 5) -> dict:
        rejections = [1 if not h.get("accepted", False) else 0 for h in self.history[1:]]
        total_steps = len(rejections)
        if total_steps == 0:
            return {
                "rejected_moves": 0,
                "rejection_rate": 0.0,
                "stuck_episodes": 0,
                "max_consecutive_stuck": 0,
                "total_stuck_iterations": 0,
                "stuck_percentage": 0.0
            }

        cur_streak = 0
        max_streak = 0
        stuck_episodes = 0
        total_stuck_iterations = 0

        for r in rejections:
            if r == 1:
                cur_streak += 1
                max_streak = max(max_streak, cur_streak)
                if cur_streak == streak_threshold:
                    stuck_episodes += 1
                if cur_streak >= streak_threshold:
                    total_stuck_iterations += 1
            else:
                cur_streak = 0

        rejection_rate = (self.rejected_moves / total_steps) * 100.0 if total_steps > 0 else 0.0
        stuck_pct = (total_stuck_iterations / total_steps) * 100.0 if total_steps > 0 else 0.0

        return {
            "rejected_moves": self.rejected_moves,
            "rejection_rate": round(rejection_rate, 2),
            "stuck_episodes": stuck_episodes,
            "max_consecutive_stuck": max_streak,
            "total_stuck_iterations": total_stuck_iterations,
            "stuck_percentage": round(stuck_pct, 2)
        }

    def get_acceptance_probabilities(self) -> list[float]:
        """Mengambil deret probabilitas e^(delta / T) untuk seluruh iterasi."""
        return [h.get("probability", 1.0) for h in self.history]

