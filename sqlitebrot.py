"""
SQLiteBrot - SQLite Mandelbrot Set Computation in Plain SQL

This is a SQLite implementation of the sql-mandelbrot-benchmark.
It computes the classic Mandelbrot set in plain SQL using recursive CTEs.

SQLite pioneered recursive CTEs and has excellent support for them!

Author: Thomas Zeutschler
License: MIT
GitHub: https://github.com/Zeutschler/sql-mandelbrot-benchmark
"""

import sqlite3
import numpy as np
from utils import save_mandelbrot_image


def run_sqlitebrot(width, height, max_iterations):
    """
    Compute Mandelbrot set using SQLite with recursive CTEs.

    Uses in-memory database for maximum performance.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        max_iterations: Maximum iterations per pixel

    Returns:
        2D numpy array of iteration counts
    """
    # Connect to in-memory SQLite database
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Calculate step sizes
    x_step = 3.5 / (width - 1)
    y_step = 2.0 / (height - 1)

    # Build the SQL query - SQLite has excellent recursive CTE support
    mandelbrot_query = f"""
    WITH RECURSIVE
      -- Generate x-axis coordinates
      xaxis(x, ix) AS (
        SELECT -2.5, 0
        UNION ALL
        SELECT x + {x_step}, ix + 1
        FROM xaxis
        WHERE ix < {width - 1}
      ),
      -- Generate y-axis coordinates
      yaxis(y, iy) AS (
        SELECT -1.0, 0
        UNION ALL
        SELECT y + {y_step}, iy + 1
        FROM yaxis
        WHERE iy < {height - 1}
      ),
      -- Mandelbrot iteration
      mandelbrot_iterations(iter, ix, iy, cx, cy, zx, zy) AS (
        SELECT 0, ix, iy, x, y, 0.0, 0.0
        FROM xaxis, yaxis

        UNION ALL

        SELECT
          iter + 1,
          ix,
          iy,
          cx,
          cy,
          zx * zx - zy * zy + cx,
          2.0 * zx * zy + cy
        FROM mandelbrot_iterations
        WHERE (zx * zx + zy * zy) < 4.0
          AND iter < {max_iterations}
      ),
      -- Get max iteration for each pixel
      pixel_depths AS (
        SELECT ix, iy, MAX(iter) AS depth
        FROM mandelbrot_iterations
        GROUP BY ix, iy
      )
    SELECT ix, iy, depth
    FROM pixel_depths
    ORDER BY iy, ix;
    """

    try:
        cursor.execute(mandelbrot_query)
        result = cursor.fetchall()
        cursor.close()
        conn.close()

        # Convert to numpy array
        mandelbrot = np.zeros((height, width), dtype=np.uint16)
        for ix, iy, depth in result:
            mandelbrot[iy, ix] = depth

        return mandelbrot

    except sqlite3.Error as e:
        print(f"SQLite query error: {e}")
        conn.close()
        raise


if __name__ == "__main__":
    # Standalone execution
    WIDTH = 1400
    HEIGHT = 800
    MAX_ITERATIONS = 256

    print(f"Computing Mandelbrot set ({WIDTH}x{HEIGHT}, max {MAX_ITERATIONS} iterations)...")
    print("Using in-memory SQLite database...")

    try:
        result = run_sqlitebrot(WIDTH, HEIGHT, MAX_ITERATIONS)
        save_mandelbrot_image(result, MAX_ITERATIONS, 'sqlitebrot.png')
    except Exception as e:
        print(f"Failed to run SQLite benchmark: {e}")
        print("\nNote: SQLite is built into Python, so this should work out of the box!")
