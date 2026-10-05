import unittest
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import random
import time
from src.data_struct import TruckState, objectiveFunction
from src.algorithm import HillClimbing, StochasticHillClimbing, SimulatedAnnealing


def run_benchmark(input_path: str, iterations: int = 300, runs: int = 3, seed: int = 42):
    """
    Menjalankan benchmark perbandingan antara Hill Climbing, Stochastic Hill Climbing,
    dan berbagai variasi konfigurasi Simulated Annealing.
    """
    print("=" * 88)
    print(f"BENCHMARK PERBANDINGAN ALGORITMA OPTIMASI (IF3170 - 3D Cargo Packing)")
    print(f"File Input     : {os.path.basename(input_path)}")
    print(f"Max Iterations : {iterations}")
    print(f"Jumlah Run     : {runs}")
    print("=" * 88)

    ts_base = TruckState.from_json(input_path)
    init_cost = objectiveFunction(ts_base)
    print(f"Initial State Cost: {init_cost:.2f}\n")

    configs = [
        ("Hill Climbing (Standard)", lambda ts: HillClimbing(ts, max_iterations=iterations, step_size=2)),
        ("Stochastic HC (T=1.0)", lambda ts: StochasticHillClimbing(ts, max_iterations=iterations, temperature=1.0)),
        ("Stochastic HC (T=10.0)", lambda ts: StochasticHillClimbing(ts, max_iterations=iterations, temperature=10.0)),
        ("Simulated Annealing (T0=1000, alpha=0.95)", lambda ts: SimulatedAnnealing(
            ts, initial_temp=1000.0, cooling_rate=0.95, min_temp=0.01, max_iterations=iterations, cooling_schedule="geometric"
        )),
        ("Simulated Annealing (T0=500, alpha=0.99)", lambda ts: SimulatedAnnealing(
            ts, initial_temp=500.0, cooling_rate=0.99, min_temp=0.01, max_iterations=iterations, cooling_schedule="geometric"
        )),
        ("Simulated Annealing (T0=100, Linear)", lambda ts: SimulatedAnnealing(
            ts, initial_temp=100.0, cooling_rate=100.0 / iterations, min_temp=0.01, max_iterations=iterations, cooling_schedule="linear"
        )),
        ("Simulated Annealing (T0=1000, Logarithmic)", lambda ts: SimulatedAnnealing(
            ts, initial_temp=1000.0, cooling_rate=1.0, min_temp=0.01, max_iterations=iterations, cooling_schedule="logarithmic"
        )),
    ]

    results = []

    for name, algo_factory in configs:
        best_costs = []
        exec_times = []
        accepted_counts = []
        better_counts = []
        worse_counts = []

        for r in range(runs):
            random.seed(seed + r * 100)
            algo = algo_factory(ts_base)
            best_state = algo.optimize()
            best_c = objectiveFunction(best_state)

            best_costs.append(best_c)
            exec_times.append(algo.execution_time)
            accepted_counts.append(algo.accepted_moves)
            better_counts.append(getattr(algo, "accepted_better_moves", algo.accepted_moves))
            worse_counts.append(getattr(algo, "accepted_worse_moves", 0))

        avg_best = sum(best_costs) / runs
        max_best = max(best_costs)
        avg_time = sum(exec_times) / runs
        avg_acc = sum(accepted_counts) / runs
        avg_worse = sum(worse_counts) / runs

        results.append({
            "name": name,
            "avg_best": avg_best,
            "max_best": max_best,
            "improvement": max_best - init_cost,
            "avg_time": avg_time,
            "avg_accepted": avg_acc,
            "avg_worse": avg_worse
        })

    # Print Table
    header = f"{'Algoritma':<44} | {'Avg Best':>10} | {'Max Best':>10} | {'Imprv':>8} | {'Avg Acc':>8} | {'Avg Time(s)':>11}"
    print(header)
    print("-" * len(header))
    for res in results:
        print(f"{res['name']:<44} | {res['avg_best']:>10.2f} | {res['max_best']:>10.2f} | {res['improvement']:>+8.2f} | {res['avg_accepted']:>8.1f} | {res['avg_time']:>10.4f}s")
    print("=" * len(header))
    print()
    return results


class TestComparison(unittest.TestCase):
    def test_run_benchmark(self):
        input1_path = os.path.join(os.path.dirname(__file__), "..", "input", "input1.json")
        results = run_benchmark(input1_path, iterations=150, runs=2, seed=123)
        self.assertGreater(len(results), 0)
        for res in results:
            self.assertGreaterEqual(res["max_best"], 0.0)


if __name__ == "__main__":
    input_dir = os.path.join(os.path.dirname(__file__), "..", "input")
    for f in sorted(os.listdir(input_dir)):
        if f.endswith(".json"):
            run_benchmark(os.path.join(input_dir, f), iterations=300, runs=3)
