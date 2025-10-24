#!/bin/bash
# Benchmark runner for Metal 4 Mandelbrot implementation

echo "=== Metal 4 Mandelbrot Benchmark ==="
echo ""
echo "Configuration:"
echo "  Resolution: 1400x800"
echo "  Max Iterations: 256"
echo "  Platform: macOS Metal 4"
echo ""

# Run the benchmark
swift metal4brot.swift benchmark
swift metal4brot_optimized.swift benchmark
python3 opencl4brot.py benchmark

echo ""
echo "Benchmark complete! Check metal4brot.png for output."
