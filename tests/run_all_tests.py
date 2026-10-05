#!/usr/bin/env python3
"""
Script untuk menjalankan seluruh unit test dan benchmark perbandingan algoritma.
Dapat dijalankan langsung dengan:
    python3 tests/run_all_tests.py
atau
    python3 -m unittest discover tests
"""
import unittest
import sys
import os

# Pastikan root workspace ada di sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def main():
    print("=" * 70)
    print("MENJALANKAN SELURUH TEST SUITE (IF3170_G40_SisyphusAnnealing)")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=os.path.join(BASE_DIR, "tests"), pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("SEMUA TEST BERHASIL LULUS! (ALL TESTS PASSED)")
    else:
        print(f"TEST GAGAL: {len(result.failures)} Failures, {len(result.errors)} Errors")
    print("=" * 70)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
