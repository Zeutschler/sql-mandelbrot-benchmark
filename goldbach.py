"""
Goldbach Conjecture Implementation using DuckDB

This implementation computes Goldbach pairs (representing even numbers as sum of two primes)
using DuckDB in plain SQL — no loops, no procedural code, just pure SQL.



Author: Thomas Zeutschler
"""
from datetime import datetime
import duckdb


def run_goldbach(max_iterations):
    """
    Compute Goldbach

    Args:
        max_iterations: Maximum iterations per pixel

    Returns:
        2D numpy array of iteration counts
    """
    # Build the SQL query
    mandelbrot_query = f"""
-- Goldbach bis MAX_N in DuckDB, vektorisiert & ohne Rekursion
WITH
params AS (
  SELECT {max_iterations}::BIGINT AS max_n
),

-- 1) Zahlen 2..MAX_N
nums(n) AS (
  SELECT n
  FROM generate_series(2, (SELECT max_n FROM params)) AS gs(n)
),

-- 2) Faktoren 2..floor(sqrt(MAX_N))
factors(d) AS (
  SELECT d
  FROM generate_series(
         2,
         CAST(floor(sqrt((SELECT max_n FROM params))) AS BIGINT)
       ) AS gs(d)
),

-- 3) Alle Kompositzahlen als d * k (k beginnt bei 2 bis MAX_N/d)
composites(n) AS (
  SELECT f.d * k AS n
  FROM factors f
  CROSS JOIN LATERAL generate_series(
           2,
           CAST((SELECT max_n FROM params) / f.d AS BIGINT)
       ) AS ks(k)
),

-- 4) Primzahlen = alle minus Kompositzahlen
primes(p) AS (
  SELECT n FROM nums
  EXCEPT
  SELECT n FROM composites
),

-- 5) Gerade N (>= 4)
evens(n) AS (
  SELECT n FROM generate_series(4, (SELECT max_n FROM params), 2) AS gs(n)
),

-- 6) Goldbach-Paare (nur kleinstes p je N)
pairs AS (
  SELECT
    e.n,
    p1.p AS p,
    (e.n - p1.p) AS q,
    ROW_NUMBER() OVER (PARTITION BY e.n ORDER BY p1.p) AS rn
  FROM evens e
  JOIN primes p1
    ON p1.p <= e.n / 2
  JOIN primes p2
    ON p2.p = e.n - p1.p
)

-- 7) Ergebnis: pro N das erste (kleinste) Paar, plus Hook für T(p,q,N)
SELECT
  n         AS even_n,
  p,
  q,
  /* TODO: Formel für T(p,q,N) hier als SQL-Ausdruck einsetzen */
  NULL::DOUBLE AS T_placeholder
FROM pairs
WHERE rn = 1
ORDER BY even_n;
"""

    # Execute query
    conn = duckdb.connect()
    start = datetime.now()
    result = conn.execute(mandelbrot_query).fetchall()
    duration = datetime.now() - start
    print(f"Query took {duration.total_seconds():.4f} seconds")
    return result



if __name__ == "__main__":
    # Standalone execution
    MAX_ITERATIONS = 100_000

    print(f"Computing Goldbach Conjecture with {MAX_ITERATIONS} iterations...")
    result = run_goldbach(MAX_ITERATIONS)
    print(f"Found {len(result)} Goldbach pairs")
