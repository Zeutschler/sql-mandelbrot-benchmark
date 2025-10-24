"""
PyBrot - Pure Python Mandelbrot Set Computation

This is a reference implementation in pure Python (no shortcuts like NumPy)
to compare against the SQL-based DuckBrot benchmark. It computes the same
Mandelbrot set using traditional procedural code.

Author: Ulrich Ludmann
License: MIT
GitHub: https://github.com/Zeutschler/sql-mandelbrot-benchmark
"""

from utils import save_mandelbrot_image


def mandelbrot_iteration(cx, cy, max_iterations):
    """
    Calculate the number of iterations for a single point in the complex plane.

    Args:
        cx: Real part of complex number c
        cy: Imaginary part of complex number c
        max_iterations: Maximum number of iterations to test

    Returns:
        Number of iterations before escape (or max_iterations if bounded)
    """
    zx = 0.0
    zy = 0.0
    for i in range(max_iterations):
        zx_squared = zx * zx
        zy_squared = zy * zy
        if zx_squared + zy_squared > 4.0:
            return i
        zx, zy = zx_squared - zy_squared + cx, 2.0 * zx * zy + cy
    return max_iterations


def compute_mandelbrot(width, height, max_iterations):
    """
    Compute the Mandelbrot set for the entire image.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        max_iterations: Maximum iterations per pixel

    Returns:
        2D list of iteration counts (height x width)
    """
    # Initialize result array
    width_1 = width - 1
    height_1 = height - 1
    return [
        [
            mandelbrot_iteration(
                -2.5 + x * 3.5 / width_1, -1.0 + y * 2.0 / height_1, max_iterations
            )
            for x in range(width)
        ]
        for y in range(height)
    ]


def run_pybrot(width, height, max_iterations):
    """
    Compute Mandelbrot set using pure Python (no shortcuts).

    Args:
        width: Image width in pixels
        height: Image height in pixels
        max_iterations: Maximum iterations per pixel

    Returns:
        2D list of iteration counts
    """
    return compute_mandelbrot(width, height, max_iterations)


if __name__ == "__main__":
    # Standalone execution
    WIDTH = 1400
    HEIGHT = 800
    MAX_ITERATIONS = 256

    print(
        f"Computing Mandelbrot set ({WIDTH}x{HEIGHT}, max {MAX_ITERATIONS} iterations)..."
    )
    result = run_pybrot(WIDTH, HEIGHT, MAX_ITERATIONS)
    save_mandelbrot_image(result, MAX_ITERATIONS, "pybrot.png")
