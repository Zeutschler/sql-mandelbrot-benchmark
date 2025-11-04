"""
ClickBrot - ClickHouse Mandelbrot Set Computation in Plain SQL

This is an implementation of the sql-mandelbrot-benchmark using ClickHouse.
It computes the classic Mandelbrot set in plain SQL — no loops, no procedural code, just pure SQL.

Author: Alexey Milovidov
License: MIT
GitHub: https://github.com/Zeutschler/sql-mandelbrot-benchmark
"""

import chdb
import numpy as np
import pyarrow
from utils import save_mandelbrot_image


def run_clickbrot(width, height, max_iterations):
    """
    Compute Mandelbrot set using ClickHouse SQL with recursive CTEs.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        max_iterations: Maximum iterations per pixel

    Returns:
        2D numpy array of iteration counts
    """
    # Build the SQL query
    mandelbrot_query = f"""
    WITH RECURSIVE
      -- Generate pixel grid and map to complex plane
      pixels AS (
        SELECT
          arrayJoin(range({width})) AS x,
          arrayJoin(range({height})) AS y,
          -2.5 + (x * 3.5 / {width - 1}) AS cx,
          -1.0 + (y * 2.0 / {height - 1}) AS cy
      ),
      -- Recursively iterate z = z² + c
      mandelbrot_iterations AS (
        SELECT x, y, cx, cy, 0.0 AS zx, 0.0 AS zy, 0::UInt32 AS iteration
        FROM pixels

        UNION ALL

        SELECT
          x, y, cx, cy,
          zx * zx - zy * zy + cx,
          2.0 * zx * zy + cy,
          iteration + 1
        FROM mandelbrot_iterations
        WHERE iteration < {max_iterations}
          AND (zx * zx + zy * zy) <= 4.0
      )
    SELECT MAX(iteration) AS depth
    FROM mandelbrot_iterations
    GROUP BY x, y ORDER BY y, x
    """

    # Execute query
    result = chdb.query(mandelbrot_query, output_format="ArrowTable")

    # Convert to numpy array
    mandelbrot = result['depth'].to_numpy().reshape(height, width)

    return mandelbrot


if __name__ == "__main__":
    # Standalone execution
    WIDTH = 1400
    HEIGHT = 800
    MAX_ITERATIONS = 256

    print(f"Computing Mandelbrot set ({WIDTH}x{HEIGHT}, max {MAX_ITERATIONS} iterations)...")
    result = run_clickbrot(WIDTH, HEIGHT, MAX_ITERATIONS)
    save_mandelbrot_image(result, MAX_ITERATIONS, 'clickbrot.png')
