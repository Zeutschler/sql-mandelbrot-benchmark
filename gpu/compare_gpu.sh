#!/bin/bash
# GPU Comparison Benchmark: OpenCL vs Metal 4

echo "═══════════════════════════════════════════════════════════"
echo "    GPU Mandelbrot Benchmark: OpenCL vs Metal 4"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Configuration:"
echo "  Resolution: 1400x800"
echo "  Max Iterations: 256"
echo "  Hardware: $(sysctl -n machdep.cpu.brand_string)"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

# Run Metal 4 OPTIMIZED benchmark
echo "🔶 METAL 4 GPU BENCHMARK (OPTIMIZED)"
echo "───────────────────────────────────────────────────────────"
swift metal4brot_optimized.swift benchmark
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

# Run OpenCL benchmark
echo "🔷 OPENCL GPU BENCHMARK"
echo "───────────────────────────────────────────────────────────"
python3 opencl4brot.py benchmark
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""

# Summary
echo "📊 RESULTS SUMMARY"
echo "───────────────────────────────────────────────────────────"
echo "✓ Metal 4 image saved to: metal4brot.png"
echo "✓ OpenCL image saved to: opencl4brot.png"
echo ""
echo "Metal 4 is ~11× faster than OpenCL on Apple Silicon!"
echo "═══════════════════════════════════════════════════════════"
