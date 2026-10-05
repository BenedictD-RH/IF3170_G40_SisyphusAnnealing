#!/usr/bin/env python3
"""
Script untuk menjalankan seluruh unit test dan benchmark algoritma optimasi 3D Cargo Packing.

Penggunaan:
    1. Menjalankan seluruh test suite:
        python3 tests/run_all_tests.py

    2. Menjalankan test suite + benchmark penuh pada seluruh testcase:
        python3 tests/run_all_tests.py --benchmark
"""
import unittest
import sys
import os
import argparse

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def run_unit_tests():
    print("=" * 80)
    print(" MENJALANKAN SELURUH UNIT TEST SUITE (IF3170_G40_SisyphusAnnealing)")
    print("=" * 80)

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=os.path.join(BASE_DIR, "tests"), pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print(" SEMUA TEST BERHASIL LULUS! (ALL TESTS PASSED)")
    else:
        print(f" TEST GAGAL: {len(result.failures)} Failures, {len(result.errors)} Errors")
    print("=" * 80)

    return result.wasSuccessful()


def main():
    parser = argparse.ArgumentParser(description="Test Suite Runner & Pure Benchmark")
    parser.add_argument("--benchmark", action="store_true", help="Jalankan benchmark perbandingan 3x run untuk seluruh file testcase")
    parser.add_argument("--iterations", "-n", type=int, default=150, help="Jumlah iterasi per run (default: 150)")
    parser.add_argument("--runs", "-r", type=int, default=3, help="Jumlah run per algoritma (default: 3)")

    args = parser.parse_args()

    success = run_unit_tests()
    if not success:
        return 1

    if args.benchmark:
        print("\n" + "=" * 80)
        print(" MENJALANKAN BENCHMARK LENGKAP PADA SELURUH TESTCASES (3X RUN)")
        print("=" * 80)
        from tests.test_comparison import run_benchmark_for_file
        input_dir = os.path.join(BASE_DIR, "input")
        input_files = sorted([f for f in os.listdir(input_dir) if f.endswith(".json")])
        for f in input_files:
            run_benchmark_for_file(os.path.join(input_dir, f), iterations=args.iterations, runs=args.runs)

    return 0


if __name__ == "__main__":
    sys.exit(main())
