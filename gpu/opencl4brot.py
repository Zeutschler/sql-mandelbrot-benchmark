#!/usr/bin/env python3
"""
OpenCL-accelerated Mandelbrot set computation
Comparison implementation to Metal 4 version
"""

import numpy as np
import shutil
import subprocess
import sys

def install_with_uv_or_pip(package: str) -> bool:
    """
    Try to install a Python package using 'uv' if available, otherwise fallback to pip.
    Returns True on success, False on failure.
    """
    uv_cmd = shutil.which("uv")
    if uv_cmd:
        # try common uv commands
        for cmd in ([uv_cmd, "install", package], [uv_cmd, "add", package]):
            try:
                subprocess.check_call(cmd)
                return True
            except Exception:
                pass
    # fallback to pip
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except Exception:
        return False

try:
    import pyopencl as cl
    OPENCL_AVAILABLE = True
except ImportError:
    if install_with_uv_or_pip("pyopencl"):
        try:
            import pyopencl as cl
            OPENCL_AVAILABLE = True
        except Exception:
            OPENCL_AVAILABLE = False
    else:
        OPENCL_AVAILABLE = False

if not OPENCL_AVAILABLE:
    print("Warning: PyOpenCL not available. Install with: uv install pyopencl or pip install pyopencl")

def run_opencl4brot(width, height, max_iterations):
    """
    Compute Mandelbrot set using OpenCL GPU acceleration
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        max_iterations: Maximum number of iterations
        
    Returns:
        2D numpy array of iteration counts
    """
    if not OPENCL_AVAILABLE:
        raise RuntimeError("PyOpenCL is not installed. Install with: uv install pyopencl (or: pip install pyopencl)")

    # OpenCL kernel source
    kernel_source = """
    __kernel void mandelbrot(__global ushort *output,
                            const int width,
                            const int height,
                            const int maxIterations)
    {
        int x = get_global_id(0);
        int y = get_global_id(1);
        
        if (x >= width || y >= height) return;
        
        float cx = -2.5f + ((float)x * 3.5f / (float)(width - 1));
        float cy = -1.0f + ((float)y * 2.0f / (float)(height - 1));
        
        float zx = 0.0f;
        float zy = 0.0f;
        int iteration = 0;
        
        while (iteration < maxIterations && (zx * zx + zy * zy) <= 4.0f) {
            float xtemp = zx * zx - zy * zy + cx;
            zy = 2.0f * zx * zy + cy;
            zx = xtemp;
            iteration++;
        }
        
        output[y * width + x] = (ushort)iteration;
    }
    """
    
    # Initialize OpenCL
    platforms = cl.get_platforms()
    if not platforms:
        raise RuntimeError("No OpenCL platforms found")
    
    # Try to find GPU device, fall back to any device
    ctx = None
    for platform in platforms:
        try:
            ctx = cl.Context(dev_type=cl.device_type.GPU, properties=[(cl.context_properties.PLATFORM, platform)])
            break
        except:
            pass
    
    if ctx is None:
        # Fall back to any available device
        ctx = cl.create_some_context(interactive=False)
    
    queue = cl.CommandQueue(ctx)
    
    # Build program
    prg = cl.Program(ctx, kernel_source).build()
    
    # Create output buffer
    output = np.zeros(width * height, dtype=np.uint16)
    output_buf = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, output.nbytes)
    
    # Execute kernel
    global_size = (width, height)
    local_size = None  # Let OpenCL choose optimal local size
    
    prg.mandelbrot(queue, global_size, local_size,
                   output_buf,
                   np.int32(width),
                   np.int32(height),
                   np.int32(max_iterations))
    
    # Read results
    cl.enqueue_copy(queue, output, output_buf).wait()
    
    # Reshape to 2D array
    result = output.reshape(height, width)
    
    return result.tolist()

def save_image(data, filename="opencl4brot.png"):
    """Save iteration data as PNG image"""
    # try to import Pillow, attempt install via uv/pip if missing
    try:
        from PIL import Image
    except ImportError:
        if install_with_uv_or_pip("pillow"):
            try:
                from PIL import Image
            except Exception:
                print("Warning: PIL not available after installation attempt. Install with: uv install pillow or pip install pillow")
                return
        else:
            print("Warning: PIL not available. Install with: uv install pillow or pip install pillow")
            return

    data_array = np.array(data, dtype=np.uint16)
    height, width = data_array.shape
    max_iter = data_array.max()

    # Create RGB image with color gradient
    img = Image.new('RGB', (width, height))
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            iteration = data_array[y, x]
            if iteration == max_iter:
                # Black for points in the set
                pixels[x, y] = (0, 0, 0)
            else:
                # Color gradient for points outside
                hue = int(255 * iteration / max_iter)
                r = (hue * 9) % 256
                g = (hue * 7) % 256
                b = (hue * 5) % 256
                pixels[x, y] = (r, g, b)

    img.save(filename)
    print(f"Saved image to {filename}")

def benchmark():
    """Run benchmark test"""
    import time

    if not OPENCL_AVAILABLE:
        print("ERROR: PyOpenCL not available!")
        print("Install with: uv install pyopencl or pip install pyopencl")
        return

    width = 1400
    height = 800
    max_iterations = 256
    
    print(f"OpenCL Mandelbrot Benchmark")
    print(f"Resolution: {width}x{height}")
    print(f"Max iterations: {max_iterations}")
    print()
    
    # Warm-up run
    print("Warm-up run...")
    result = run_opencl4brot(width, height, max_iterations)
    
    # Benchmark runs
    times = []
    num_runs = 5
    
    print(f"\nRunning {num_runs} benchmark iterations...")
    for i in range(num_runs):
        start = time.perf_counter()
        result = run_opencl4brot(width, height, max_iterations)
        end = time.perf_counter()
        
        elapsed_ms = (end - start) * 1000
        times.append(elapsed_ms)
        print(f"Run {i+1}: {elapsed_ms:.2f} ms")
    
    print()
    print(f"Best time: {min(times):.2f} ms")
    print(f"Average: {np.mean(times):.2f} ms")
    print(f"Median: {np.median(times):.2f} ms")
    print(f"Throughput: {(width * height / min(times) * 1000 / 1e6):.2f} Mpixels/s")
    
    # Save image
    print("\nGenerating image...")
    save_image(result, "opencl4brot.png")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "benchmark":
        benchmark()
    elif len(sys.argv) > 1 and sys.argv[1] == "generate":
        # Just generate image
        width = 1400
        height = 800
        max_iterations = 256
        print(f"Generating OpenCL Mandelbrot image ({width}x{height})...")
        print("Tip: if you're using uv, install dependencies with: uv install pyopencl pillow")
        print("Fallback: pip install pyopencl pillow")
        result = run_opencl4brot(width, height, max_iterations)
        save_image(result, "opencl4brot.png")
        # explicitní echo (save_image již vypisuje uložení)
        print("Image saved to opencl4brot.png")
    else:
        print("Usage: python opencl4brot.py [benchmark|generate]")
        print("Tip: pro rychlou instalaci závislostí použijte 'uv' pokud jej máte:")
        print("  uv install pyopencl pillow")
        print("Fallback pomocí pip:")
        print("  pip install pyopencl pillow")
