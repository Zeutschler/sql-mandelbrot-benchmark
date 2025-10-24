"""
NumPyBrot - Highly Optimized Mandelbrot Set Computation using NumPy

This implementation uses loop unrolling and vectorized operations for maximum
performance. It processes 4 iterations per loop cycle, uses separate real/imaginary
arrays for better SIMD performance, and leverages CPU instruction-level parallelism.

Author: Thomas Zeutschler
License: MIT
GitHub: https://github.com/Zeutschler/sql-mandelbrot-benchmark
"""

import numpy as np
from utils import save_mandelbrot_image


def compute_mandelbrot_unrolled(width, height, max_iterations):
    """
    Compute Mandelbrot set using manual loop unrolling for better performance.

    This processes multiple iterations per loop cycle, reducing loop overhead
    and allowing better CPU pipelining and instruction-level parallelism.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        max_iterations: Maximum iterations per pixel

    Returns:
        2D NumPy array of iteration counts (height x width)
    """
    # Create coordinate arrays
    x = np.linspace(-2.5, 1.0, width, dtype=np.float64)
    y = np.linspace(-1.0, 1.0, height, dtype=np.float64)
    cx, cy = np.meshgrid(x, y)
    c = cx + 1j * cy

    # Use separate real and imaginary arrays for better performance
    zr = np.zeros(c.shape, dtype=np.float64)
    zi = np.zeros(c.shape, dtype=np.float64)
    cr = c.real
    ci = c.imag

    iterations = np.full(c.shape, max_iterations, dtype=np.uint16)
    mask = np.ones(c.shape, dtype=bool)

    # Suppress overflow warnings (expected for escaped points)
    with np.errstate(over='ignore', invalid='ignore'):
        # Unroll 4 iterations at a time
        unroll_factor = 4
        for i in range(0, max_iterations, unroll_factor):
            if not mask.any():
                break

            # Iteration 1
            if i < max_iterations:
                zr2 = zr * zr
                zi2 = zi * zi
                zi = 2.0 * zr * zi + ci
                zr = zr2 - zi2 + cr

                mag2 = zr * zr + zi * zi
                escaped = mag2 > 4.0
                newly_escaped = escaped & mask
                iterations[newly_escaped] = i
                mask &= ~escaped

            # Iteration 2
            if i + 1 < max_iterations and mask.any():
                zr2 = zr * zr
                zi2 = zi * zi
                zi = 2.0 * zr * zi + ci
                zr = zr2 - zi2 + cr

                mag2 = zr * zr + zi * zi
                escaped = mag2 > 4.0
                newly_escaped = escaped & mask
                iterations[newly_escaped] = i + 1
                mask &= ~escaped

            # Iteration 3
            if i + 2 < max_iterations and mask.any():
                zr2 = zr * zr
                zi2 = zi * zi
                zi = 2.0 * zr * zi + ci
                zr = zr2 - zi2 + cr

                mag2 = zr * zr + zi * zi
                escaped = mag2 > 4.0
                newly_escaped = escaped & mask
                iterations[newly_escaped] = i + 2
                mask &= ~escaped

            # Iteration 4
            if i + 3 < max_iterations and mask.any():
                zr2 = zr * zr
                zi2 = zi * zi
                zi = 2.0 * zr * zi + ci
                zr = zr2 - zi2 + cr

                mag2 = zr * zr + zi * zi
                escaped = mag2 > 4.0
                newly_escaped = escaped & mask
                iterations[newly_escaped] = i + 3
                mask &= ~escaped

    return iterations


def run_numpybrot(width, height, max_iterations):
    """
    Compute Mandelbrot set using highly optimized NumPy operations.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        max_iterations: Maximum iterations per pixel

    Returns:
        2D NumPy array of iteration counts
    """
    return compute_mandelbrot_unrolled(width, height, max_iterations)


if __name__ == "__main__":
    # Standalone execution
    WIDTH = 1400
    HEIGHT = 800
    MAX_ITERATIONS = 256

    print(f"Computing Mandelbrot set ({WIDTH}x{HEIGHT}, max {MAX_ITERATIONS} iterations)...")
    result = run_numpybrot(WIDTH, HEIGHT, MAX_ITERATIONS)
    save_mandelbrot_image(result, MAX_ITERATIONS, 'numpybrot.png')
