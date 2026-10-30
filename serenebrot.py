"""
SereneBrot - SereneDB Mandelbrot Set Computation in Plain SQL

This is an implementation of the sql-mandelbrot-benchmark using SereneDB.
It computes the classic Mandelbrot set in plain SQL — no loops, no procedural code, just pure SQL.

SereneDB's query engine is a fork of DuckDB, so it runs the DuckDB reference query unchanged.
It is a server that speaks the PostgreSQL wire protocol, so we connect with psycopg.

Run SereneDB with Docker:
    docker run --rm -p 7890:7890 -e POSTGRES_PASSWORD=postgres serenedb/serenedb:latest

SereneDB: https://github.com/serenedb/serenedb

Author: Valerii Mironov
License: MIT
GitHub: https://github.com/Zeutschler/sql-mandelbrot-benchmark
"""

import io

import numpy as np
import psycopg
import pyarrow.parquet as pq
from utils import save_mandelbrot_image


def run_serenebrot(width: int, height: int, max_iterations: int) -> np.ndarray:
    """
    Compute Mandelbrot set using SereneDB SQL with recursive CTEs.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        max_iterations: Maximum iterations per pixel

    Returns:
        2D numpy array of iteration counts
    """
    # Build the SQL query: the DuckDB reference query
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
    GROUP BY x, y;
    """
    # No ORDER BY: the result is scattered into the image by (x, y) below, so sorting
    # server-side would only add work.

    conn_str = "host=localhost port=7890 dbname=postgres user=postgres password=postgres"

    # Execute query: the result comes back as one Parquet file over COPY TO STDOUT, so the
    # client reads columns instead of a million rows one by one.
    buf = io.BytesIO()
    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            copy_query = f"COPY ({mandelbrot_query.strip().rstrip(';')}) TO STDOUT (FORMAT parquet)"
            with cur.copy(copy_query) as copy:
                for chunk in copy:
                    buf.write(chunk)
    buf.seek(0)
    table = pq.read_table(buf)

    # Scatter the depths into the image grid
    mandelbrot = np.zeros((height, width), dtype=np.uint16)
    mandelbrot[table['y'].to_numpy(), table['x'].to_numpy()] = table['depth'].to_numpy()

    return mandelbrot


if __name__ == "__main__":
    # Standalone execution
    WIDTH = 1400
    HEIGHT = 800
    MAX_ITERATIONS = 256

    print(f"Computing Mandelbrot set ({WIDTH}x{HEIGHT}, max {MAX_ITERATIONS} iterations)...")
    result = run_serenebrot(WIDTH, HEIGHT, MAX_ITERATIONS)
    save_mandelbrot_image(result, MAX_ITERATIONS, 'serenebrot.png')
