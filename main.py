"""
Mandelbrot Set Benchmark Suite

A comprehensive benchmark comparing different approaches to computing
the Mandelbrot set. Tests SQL engines, programming languages, and
various optimization techniques.

Author: Thomas Zeutschler
License: MIT
GitHub: https://github.com/Zeutschler/sql-mandelbrot-benchmark
"""

from utils import run_benchmark, print_results, print_header


# Mandelbrot set configuration
WIDTH = 1400
HEIGHT = 800
MAX_ITERATIONS = 256

# Benchmark registry: (name, module, function)
BENCHMARKS = [
    ("DuckDB (SQL)", "duckbrot", "run_duckbrot"),
    ("Pure Python", "pybrot", "run_pybrot"),
    # Add more benchmarks here:
    # ("PostgreSQL", "postgresqlbrot", "run_postgresqlbrot"),
    # ("SQLite", "sqlitebrot", "run_sqlitebrot"),
]


def main():
    """Run all available benchmarks."""
    print_header(WIDTH, HEIGHT, MAX_ITERATIONS)

    results = []

    # Run all available benchmarks
    for name, module_name, func_name in BENCHMARKS:
        try:
            module = __import__(module_name)
            func = getattr(module, func_name)
            result, elapsed_ms = run_benchmark(name, func, WIDTH, HEIGHT, MAX_ITERATIONS)
            results.append((name, elapsed_ms))
        except ImportError as e:
            print(f"\n⊘ {name} benchmark not available: {e}")
        except AttributeError as e:
            print(f"\n⊘ {name} benchmark missing function: {e}")

    # Print summary
    print_results(results, WIDTH, HEIGHT, MAX_ITERATIONS)


if __name__ == "__main__":
    main()
