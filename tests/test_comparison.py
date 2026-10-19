import unittest
import sys
import os
import random
import time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.data_struct import TruckState, objectiveFunction
from src.algorithm import HillClimbing, StochasticHillClimbing, SimulatedAnnealing, SteepestHillClimbing, SidewaysHillClimbing,RandomRestartHillClimbing


def run_benchmark_for_file(input_path: str, iterations: int = 150, runs: int = 3, seed: int = 42) -> list[dict]:
    """
    Menjalankan benchmark perbandingan performa optimasi 3D Cargo Packing
    sebanyak 3x run untuk file input tertentu tanpa menghasilkan file visualisasi/gambar.
    """
    filename = os.path.basename(input_path)
    ts_base = TruckState.from_json(input_path)

    print("=" * 105)
    print(f" BENCHMARK OPTIMASI (3X RUN): {filename} | {len(ts_base.packages)} Kotak | Kapasitas: {ts_base.truck.maxCapacity} | Iterasi: {iterations}")
    print("=" * 105)

    configs = [
        ("Stochastic HC (T=0.1)", lambda ts: StochasticHillClimbing(ts, max_iterations=iterations, temperature=0.1, random_init=True)),
        ("Stochastic HC (T=1.0)", lambda ts: StochasticHillClimbing(ts, max_iterations=iterations, temperature=1.0, random_init=True)),
        ("Stochastic HC (T=5.0)", lambda ts: StochasticHillClimbing(ts, max_iterations=iterations, temperature=5.0, random_init=True)),

        ("Simulated Annealing (T0=1000, alpha=0.95)", lambda ts: SimulatedAnnealing(
            ts, initial_temp=1000.0, cooling_rate=0.95, min_temp=0.01, max_iterations=iterations, cooling_schedule="geometric", random_init=True
        )),
        ("Simulated Annealing (T0=500, alpha=0.99)", lambda ts: SimulatedAnnealing(
            ts, initial_temp=500.0, cooling_rate=0.99, min_temp=0.01, max_iterations=iterations, cooling_schedule="geometric", random_init=True
        )),
        ("Simulated Annealing (T0=100, Linear)", lambda ts: SimulatedAnnealing(
            ts, initial_temp=100.0, cooling_rate=100.0 / iterations, min_temp=0.01, max_iterations=iterations, cooling_schedule="linear", random_init=True
        )),
        ("Simulated Annealing (T0=1000, Logarithmic)", lambda ts: SimulatedAnnealing(
            ts, initial_temp=1000.0, cooling_rate=1.0, min_temp=0.01, max_iterations=iterations, cooling_schedule="logarithmic", random_init=True
        )),

        ("Random Restart HC", lambda ts: RandomRestartHillClimbing(ts, max_restarts=10))

    ]

    results = []

    for name, algo_factory in configs:
        init_costs = []
        best_costs = []
        exec_times = []
        accepted_moves = []
        stuck_episodes_list = []
        rejection_rates = []

        for r in range(runs):
            random.seed(seed + r * 100)
            algo = algo_factory(ts_base)
            init_costs.append(objectiveFunction(algo.initial_state))
            best_st = algo.optimize()
            best_costs.append(objectiveFunction(best_st))
            exec_times.append(algo.execution_time)
            accepted_moves.append(algo.accepted_moves)

            if isinstance(algo, SimulatedAnnealing):
                stuck_data = algo.get_stuck_metrics(streak_threshold=5)
                stuck_episodes_list.append(stuck_data["stuck_episodes"])
                rejection_rates.append(stuck_data["rejection_rate"])

        avg_init = sum(init_costs) / runs
        avg_best = sum(best_costs) / runs
        max_best = max(best_costs)
        avg_imprv = avg_best - avg_init
        avg_time = sum(exec_times) / runs
        avg_acc = sum(accepted_moves) / runs

        sa_info_str = "-"
        if stuck_episodes_list:
            avg_stuck = sum(stuck_episodes_list) / len(stuck_episodes_list)
            avg_rej = sum(rejection_rates) / len(rejection_rates)
            sa_info_str = f"{avg_stuck:.1f} eps ({avg_rej:.1f}% rej)"

        results.append({
            "name": name,
            "avg_init": avg_init,
            "avg_best": avg_best,
            "max_best": max_best,
            "improvement": avg_imprv,
            "avg_time": avg_time,
            "avg_accepted": avg_acc,
            "sa_stuck_info": sa_info_str
        })

    # Header Tabel
    header = f"{'Algoritma':<42} | {'Avg Init':>9} | {'Avg Best':>9} | {'Max Best':>9} | {'Avg Imprv':>9} | {'Avg Acc':>7} | {'Avg Time':>9} | {'SA Stuck':>15}"
    print(header)
    print("-" * len(header))
    for res in results:
        print(
            f"{res['name']:<42} | {res['avg_init']:>9.2f} | {res['avg_best']:>9.2f} | {res['max_best']:>9.2f} | "
            f"{res['improvement']:>+9.2f} | {res['avg_accepted']:>7.1f} | {res['avg_time']:>8.4f}s | {res['sa_stuck_info']:>15}"
        )
    print("=" * len(header))
    print()
    return results


class TestComparison(unittest.TestCase):
    def test_run_benchmark_all_inputs(self):
        """Uji benchmark otomatis untuk seluruh input JSON di folder input/."""
        input_dir = os.path.join(os.path.dirname(__file__), "..", "input")
        input_files = sorted([f for f in os.listdir(input_dir) if f.endswith(".json")])
        self.assertGreater(len(input_files), 0)

        # Uji benchmark pada setidaknya testcase input1 dan input2
        for f in input_files[:2]:
            file_path = os.path.join(input_dir, f)
            results = run_benchmark_for_file(file_path, iterations=100, runs=3, seed=42)
            self.assertGreater(len(results), 0)
            for r in results:
                self.assertIsInstance(r["avg_best"], (int, float))
                self.assertGreaterEqual(r["avg_time"], 0.0)


if __name__ == "__main__":
    input_dir = os.path.join(os.path.dirname(__file__), "..", "input")
    for filename in sorted(os.listdir(input_dir)):
        if filename.endswith(".json"):
            run_benchmark_for_file(os.path.join(input_dir, filename), iterations=150, runs=3)
