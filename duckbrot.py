"""
DuckBrot - DuckDB Mandelbrot Set Computation in Plain SQL

This is a reference implementation of the sql-mandelbrot-benchmark using DuckDB.
It computes the classic Mandelbrot set in plain SQL — no loops, no procedural code, just pure SQL.

Author: Thomas Zeutschler
License: MIT
GitHub: https://github.com/Zeutschler/sql-mandelbrot-benchmark
"""

import duckdb
import numpy as np
from utils import save_mandelbrot_image


def run_duckbrot(width, height, max_iterations):
    """
    Compute Mandelbrot set using DuckDB SQL with recursive CTEs.

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
      pixels AS (
        SELECT
          x::INTEGER AS x,
          y::INTEGER AS y,
          -2.5 + (x::DOUBLE * 3.5 / {width - 1}.0) AS cx,
          -1.0 + (y::DOUBLE * 2.0 / {height - 1}.0) AS cy
        FROM
          generate_series(0, {width - 1}) AS t1(x),
          generate_series(0, {height - 1}) AS t2(y)
      ),
      mandelbrot_iterations AS (
        SELECT
          x, y, cx, cy,
          0.0::DOUBLE AS zx,
          0.0::DOUBLE AS zy,
          0 AS iteration
        FROM pixels

        UNION ALL

        SELECT
          m.x,
          m.y,
          m.cx,
          m.cy,
          (m.zx * m.zx - m.zy * m.zy + m.cx)::DOUBLE AS zx,
          (2.0 * m.zx * m.zy + m.cy)::DOUBLE AS zy,
          m.iteration + 1 AS iteration
        FROM mandelbrot_iterations m
        WHERE
          m.iteration < {max_iterations}
          AND (m.zx * m.zx + m.zy * m.zy) <= 4.0
      )
    SELECT
      x,
      y,
      MAX(iteration) AS depth
    FROM mandelbrot_iterations
    GROUP BY x, y
    ORDER BY y, x;
    """

    # Execute query
    conn = duckdb.connect()
    result = conn.execute(mandelbrot_query).fetchall()

    # Convert to numpy array
    mandelbrot = np.zeros((height, width), dtype=np.uint16)
    for x, y, depth in result:
        mandelbrot[y, x] = depth

    return mandelbrot


if __name__ == "__main__":
    # Standalone execution
    WIDTH = 1400
    HEIGHT = 800
    MAX_ITERATIONS = 256

    print(f"Computing Mandelbrot set ({WIDTH}x{HEIGHT}, max {MAX_ITERATIONS} iterations)...")
    result = run_duckbrot(WIDTH, HEIGHT, MAX_ITERATIONS)
    save_mandelbrot_image(result, MAX_ITERATIONS, 'duckbrot.png')
