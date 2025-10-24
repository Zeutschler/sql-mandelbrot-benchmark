"""
Metal4brot - Metal 4 GPU Mandelbrot Set Computation

This implementation uses Apple's Metal GPU framework to compute the Mandelbrot set
using parallel GPU compute shaders for maximum performance on Apple Silicon.

Author: Implementation for sql-mandelbrot-benchmark
License: MIT
"""

import subprocess
import numpy as np
import os
import tempfile
import json


def run_metal4brot(width, height, max_iterations):
    """
    Compute Mandelbrot set using Metal 4 GPU compute shaders.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        max_iterations: Maximum iterations per pixel

    Returns:
        2D numpy array of iteration counts
    """
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    metal_script = os.path.join(script_dir, "metal4brot", "metal4brot.swift")
    
    # Create Swift script that outputs JSON
    swift_code = f"""
import Foundation
import Metal

func runMetal4brot(width: Int, height: Int, maxIterations: Int) -> [[UInt16]] {{
    guard let device = MTLCreateSystemDefaultDevice() else {{
        fatalError("Metal is not supported on this device")
    }}
    
    guard let commandQueue = device.makeCommandQueue() else {{
        fatalError("Failed to create command queue")
    }}
    
    let shaderSource = \"\"\"
    #include <metal_stdlib>
    using namespace metal;
    
    kernel void mandelbrot(device uint16_t *output [[buffer(0)]],
                          constant int &width [[buffer(1)]],
                          constant int &height [[buffer(2)]],
                          constant int &maxIterations [[buffer(3)]],
                          uint2 gid [[thread_position_in_grid]])
    {{
        int x = gid.x;
        int y = gid.y;
        
        if (x >= width || y >= height) return;
        
        float cx = -2.5 + (float(x) * 3.5 / float(width - 1));
        float cy = -1.0 + (float(y) * 2.0 / float(height - 1));
        
        float zx = 0.0;
        float zy = 0.0;
        int iteration = 0;
        
        while (iteration < maxIterations && (zx * zx + zy * zy) <= 4.0) {{
            float xtemp = zx * zx - zy * zy + cx;
            zy = 2.0 * zx * zy + cy;
            zx = xtemp;
            iteration++;
        }}
        
        output[y * width + x] = uint16_t(iteration);
    }}
    \"\"\"
    
    guard let library = try? device.makeLibrary(source: shaderSource, options: nil) else {{
        fatalError("Failed to compile shader")
    }}
    
    guard let kernelFunction = library.makeFunction(name: "mandelbrot") else {{
        fatalError("Failed to find kernel function")
    }}
    
    guard let pipelineState = try? device.makeComputePipelineState(function: kernelFunction) else {{
        fatalError("Failed to create pipeline state")
    }}
    
    let bufferSize = width * height * MemoryLayout<UInt16>.stride
    guard let outputBuffer = device.makeBuffer(length: bufferSize, options: .storageModeShared) else {{
        fatalError("Failed to create output buffer")
    }}
    
    var widthVar = Int32(width)
    var heightVar = Int32(height)
    var maxIterVar = Int32(maxIterations)
    
    guard let widthBuffer = device.makeBuffer(bytes: &widthVar, length: MemoryLayout<Int32>.stride, options: .storageModeShared),
          let heightBuffer = device.makeBuffer(bytes: &heightVar, length: MemoryLayout<Int32>.stride, options: .storageModeShared),
          let maxIterBuffer = device.makeBuffer(bytes: &maxIterVar, length: MemoryLayout<Int32>.stride, options: .storageModeShared) else {{
        fatalError("Failed to create parameter buffers")
    }}
    
    guard let commandBuffer = commandQueue.makeCommandBuffer(),
          let computeEncoder = commandBuffer.makeComputeCommandEncoder() else {{
        fatalError("Failed to create command buffer or encoder")
    }}
    
    computeEncoder.setComputePipelineState(pipelineState)
    computeEncoder.setBuffer(outputBuffer, offset: 0, index: 0)
    computeEncoder.setBuffer(widthBuffer, offset: 0, index: 1)
    computeEncoder.setBuffer(heightBuffer, offset: 0, index: 2)
    computeEncoder.setBuffer(maxIterBuffer, offset: 0, index: 3)
    
    let threadsPerGroup = MTLSize(width: 16, height: 16, depth: 1)
    let numThreadgroups = MTLSize(
        width: (width + threadsPerGroup.width - 1) / threadsPerGroup.width,
        height: (height + threadsPerGroup.height - 1) / threadsPerGroup.height,
        depth: 1
    )
    
    computeEncoder.dispatchThreadgroups(numThreadgroups, threadsPerThreadgroup: threadsPerGroup)
    computeEncoder.endEncoding()
    
    commandBuffer.commit()
    commandBuffer.waitUntilCompleted()
    
    let outputPointer = outputBuffer.contents().bindMemory(to: UInt16.self, capacity: width * height)
    var result = [[UInt16]](repeating: [UInt16](repeating: 0, count: width), count: height)
    
    for y in 0..<height {{
        for x in 0..<width {{
            result[y][x] = outputPointer[y * width + x]
        }}
    }}
    
    return result
}}

let width = {width}
let height = {height}
let maxIterations = {max_iterations}

let result = runMetal4brot(width: width, height: height, maxIterations: maxIterations)

// Output as JSON
var output: [[UInt16]] = []
for row in result {{
    output.append(row)
}}

let jsonData = try! JSONSerialization.data(withJSONObject: output, options: [])
let jsonString = String(data: jsonData, encoding: .utf8)!
print(jsonString)
"""
    
    # Write Swift code to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.swift', delete=False) as f:
        temp_file = f.name
        f.write(swift_code)
    
    try:
        # Run Swift script
        result = subprocess.run(
            ['swift', temp_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Metal computation failed: {result.stderr}")
        
        # Parse JSON output
        data = json.loads(result.stdout)
        mandelbrot = np.array(data, dtype=np.uint16)
        
        return mandelbrot
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


if __name__ == "__main__":
    from utils import save_mandelbrot_image
    
    WIDTH = 1400
    HEIGHT = 800
    MAX_ITERATIONS = 256

    print(f"Computing Mandelbrot set with Metal 4 ({WIDTH}x{HEIGHT}, max {MAX_ITERATIONS} iterations)...")
    result = run_metal4brot(WIDTH, HEIGHT, MAX_ITERATIONS)
    save_mandelbrot_image(result, MAX_ITERATIONS, 'metal4brot.png')
