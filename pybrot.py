"""
PyBrot - Pure Python Mandelbrot Set Computation

This is a reference implementation in pure Python (no shortcuts like NumPy)
to compare against the SQL-based DuckBrot benchmark. It computes the same
Mandelbrot set using traditional procedural code.

Author: Thomas Zeutschler
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
    iteration = 0

    while iteration < max_iterations:
        # Check if point has escaped (magnitude > 2, or magnitude² > 4)
        if (zx * zx + zy * zy) > 4.0:
            break

        # Compute next iteration: z = z² + c
        zx_new = zx * zx - zy * zy + cx
        zy_new = 2.0 * zx * zy + cy

        zx = zx_new
        zy = zy_new
        iteration += 1

    return iteration


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
    mandelbrot = [[0 for _ in range(width)] for _ in range(height)]

    # Compute complex coordinates for each pixel
    for y in range(height):
        for x in range(width):
            # Map pixel coordinates to complex plane
            # Standard Mandelbrot view: real [-2.5, 1.0], imaginary [-1.0, 1.0]
            cx = -2.5 + (x * 3.5 / (width - 1))
            cy = -1.0 + (y * 2.0 / (height - 1))

            # Compute iterations for this point
            mandelbrot[y][x] = mandelbrot_iteration(cx, cy, max_iterations)

    return mandelbrot


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

    print(f"Computing Mandelbrot set ({WIDTH}x{HEIGHT}, max {MAX_ITERATIONS} iterations)...")
    result = run_pybrot(WIDTH, HEIGHT, MAX_ITERATIONS)
    save_mandelbrot_image(result, MAX_ITERATIONS, 'pybrot.png')
