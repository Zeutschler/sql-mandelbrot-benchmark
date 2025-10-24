"""
Utility functions for Mandelbrot benchmark suite.

Author: Thomas Zeutschler
License: MIT
"""

import os
import time
import numpy as np
from PIL import Image
from matplotlib import colormaps


def save_mandelbrot_image(mandelbrot_data, max_iterations, filename='output.png'):
    """
    Save Mandelbrot set data as a colorized image with logarithmic scaling.

    Args:
        mandelbrot_data: 2D array of iteration counts (height x width)
        max_iterations: Maximum iteration value used in computation
        filename: Output filename (will be saved in 'images/' directory)
    """
    # Ensure images directory exists
    images_dir = 'images'
    os.makedirs(images_dir, exist_ok=True)

    # Prepend images directory to filename if not already there
    if not filename.startswith(images_dir + os.sep):
        filepath = os.path.join(images_dir, filename)
    else:
        filepath = filename

    # Convert to numpy array if needed
    if not isinstance(mandelbrot_data, np.ndarray):
        mandelbrot_data = np.array(mandelbrot_data, dtype=np.uint16)

    # Apply logarithmic scaling for better color distribution
    mandelbrot_scaled = mandelbrot_data.astype(np.float64)
    in_set_mask = (mandelbrot_data == max_iterations)
    escaped_mask = (mandelbrot_data < max_iterations)

    mandelbrot_color = np.zeros_like(mandelbrot_scaled)
    if np.any(escaped_mask):
        escaped_values = mandelbrot_scaled[escaped_mask]
        log_scaled = np.log(escaped_values + 1)
        if log_scaled.max() > 0:
            mandelbrot_color[escaped_mask] = log_scaled / log_scaled.max()

    mandelbrot_color[in_set_mask] = 0

    # Apply colormap and save
    cmap = colormaps.get_cmap('hot')
    colored = cmap(mandelbrot_color)
    img = Image.fromarray((colored[:, :, :3] * 255).astype(np.uint8))
    img.save(filepath)
    print(f"Saved to {filepath}")


def run_benchmark(name, compute_func, *args):
    """
    Run a single benchmark and return timing results.

    Args:
        name: Benchmark name
        compute_func: Function to execute
        *args: Arguments to pass to compute_func

    Returns:
        Tuple of (result, elapsed_ms)
    """
    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print(f"{'='*60}")

    start_time = time.time()
    try:
        result = compute_func(*args)
        elapsed_ms = (time.time() - start_time) * 1000
        print(f"✓ Completed in {elapsed_ms:.2f} ms")
        return result, elapsed_ms
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        print(f"✗ Failed after {elapsed_ms:.2f} ms: {e}")
        return None, None


def print_results(results, width, height, max_iterations):
    """
    Print formatted benchmark results.

    Args:
        results: List of (name, time_ms) tuples
        width: Image width
        height: Image height
        max_iterations: Maximum iterations used
    """
    print(f"\n{'='*60}")
    print("BENCHMARK RESULTS")
    print(f"{'='*60}")
    print(f"Configuration: {width}x{height} pixels, {max_iterations} max iterations")
    print(f"{'-'*60}")

    # Filter successful results
    successful = [(name, time_ms) for name, time_ms in results if time_ms is not None]

    if not successful:
        print("No successful benchmarks to report.")
        return

    # Find DuckDB result as baseline
    duckdb_time = None
    for name, time_ms in successful:
        if "DuckDB" in name:
            duckdb_time = time_ms
            break

    # If no DuckDB, fall back to fastest
    baseline_time = duckdb_time if duckdb_time else min(successful, key=lambda x: x[1])[1]

    # Find fastest
    fastest_name, fastest_time = min(successful, key=lambda x: x[1])

    # Print results table
    print(f"{'Benchmark':<30} {'Time (ms)':<15} {'Relative':<15}")
    print(f"{'-'*60}")

    for name, time_ms in successful:
        relative = time_ms / baseline_time
        marker = " ⭐" if time_ms == fastest_time else ""
        print(f"{name:<30} {time_ms:>10.2f}      {relative:>6.2f}x{marker}")

    print(f"{'-'*60}")
    baseline_name = "DuckDB (SQL)" if duckdb_time else fastest_name
    print(f"Baseline: {baseline_name} ({baseline_time:.2f} ms)")
    print(f"Fastest: {fastest_name} ({fastest_time:.2f} ms)")
    print(f"{'='*60}\n")


def print_header(width, height, max_iterations):
    """
    Print benchmark suite header.

    Args:
        width: Image width
        height: Image height
        max_iterations: Maximum iterations
    """
    print("\n" + "="*60)
    print("MANDELBROT SET BENCHMARK SUITE")
    print("="*60)
    print(f"Image size: {width}x{height} pixels")
    print(f"Max iterations: {max_iterations}")
    print("="*60)
