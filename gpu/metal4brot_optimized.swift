#!/usr/bin/env swift

import Foundation
import Metal
import CoreGraphics
import AppKit

// Global device and pipeline cache
var cachedDevice: MTLDevice?
var cachedPipeline: MTLComputePipelineState?
var cachedQueue: MTLCommandQueue?

func initializeMetal() {
    guard cachedDevice == nil else { return }
    
    guard let device = MTLCreateSystemDefaultDevice() else {
        fatalError("Metal is not supported on this device")
    }
    cachedDevice = device
    
    guard let commandQueue = device.makeCommandQueue() else {
        fatalError("Failed to create command queue")
    }
    cachedQueue = commandQueue
    
    let shaderSource = """
    #include <metal_stdlib>
    using namespace metal;
    
    kernel void mandelbrot(device uint16_t *output [[buffer(0)]],
                          constant int &width [[buffer(1)]],
                          constant int &height [[buffer(2)]],
                          constant int &maxIterations [[buffer(3)]],
                          uint2 gid [[thread_position_in_grid]])
    {
        int x = gid.x;
        int y = gid.y;
        
        if (x >= width || y >= height) return;
        
        float cx = -2.5 + (float(x) * 3.5 / float(width - 1));
        float cy = -1.0 + (float(y) * 2.0 / float(height - 1));
        
        float zx = 0.0;
        float zy = 0.0;
        int iteration = 0;
        
        while (iteration < maxIterations && (zx * zx + zy * zy) <= 4.0) {
            float xtemp = zx * zx - zy * zy + cx;
            zy = 2.0 * zx * zy + cy;
            zx = xtemp;
            iteration++;
        }
        
        output[y * width + x] = uint16_t(iteration);
    }
    """
    
    guard let library = try? device.makeLibrary(source: shaderSource, options: nil) else {
        fatalError("Failed to compile shader")
    }
    
    guard let kernelFunction = library.makeFunction(name: "mandelbrot") else {
        fatalError("Failed to find kernel function")
    }
    
    guard let pipelineState = try? device.makeComputePipelineState(function: kernelFunction) else {
        fatalError("Failed to create pipeline state")
    }
    cachedPipeline = pipelineState
}

func runMetal4brotOptimized(width: Int, height: Int, maxIterations: Int) -> Double {
    initializeMetal()
    
    guard let device = cachedDevice,
          let pipelineState = cachedPipeline,
          let commandQueue = cachedQueue else {
        fatalError("Metal not initialized")
    }
    
    let bufferSize = width * height * MemoryLayout<UInt16>.stride
    guard let outputBuffer = device.makeBuffer(length: bufferSize, options: .storageModeShared) else {
        fatalError("Failed to create output buffer")
    }
    
    var widthVar = Int32(width)
    var heightVar = Int32(height)
    var maxIterVar = Int32(maxIterations)
    
    guard let widthBuffer = device.makeBuffer(bytes: &widthVar, length: MemoryLayout<Int32>.stride, options: .storageModeShared),
          let heightBuffer = device.makeBuffer(bytes: &heightVar, length: MemoryLayout<Int32>.stride, options: .storageModeShared),
          let maxIterBuffer = device.makeBuffer(bytes: &maxIterVar, length: MemoryLayout<Int32>.stride, options: .storageModeShared) else {
        fatalError("Failed to create parameter buffers")
    }
    
    guard let commandBuffer = commandQueue.makeCommandBuffer(),
          let computeEncoder = commandBuffer.makeComputeCommandEncoder() else {
        fatalError("Failed to create command buffer or encoder")
    }
    
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
    
    let startTime = Date()
    
    computeEncoder.dispatchThreadgroups(numThreadgroups, threadsPerThreadgroup: threadsPerGroup)
    computeEncoder.endEncoding()
    
    commandBuffer.commit()
    commandBuffer.waitUntilCompleted()
    
    let elapsed = Date().timeIntervalSince(startTime) * 1000
    
    return elapsed
}

func runMetal4brot(width: Int, height: Int, maxIterations: Int) -> [[UInt16]] {
    initializeMetal()
    
    guard let device = cachedDevice,
          let pipelineState = cachedPipeline,
          let commandQueue = cachedQueue else {
        fatalError("Metal not initialized")
    }
    
    let bufferSize = width * height * MemoryLayout<UInt16>.stride
    guard let outputBuffer = device.makeBuffer(length: bufferSize, options: .storageModeShared) else {
        fatalError("Failed to create output buffer")
    }
    
    var widthVar = Int32(width)
    var heightVar = Int32(height)
    var maxIterVar = Int32(maxIterations)
    
    guard let widthBuffer = device.makeBuffer(bytes: &widthVar, length: MemoryLayout<Int32>.stride, options: .storageModeShared),
          let heightBuffer = device.makeBuffer(bytes: &heightVar, length: MemoryLayout<Int32>.stride, options: .storageModeShared),
          let maxIterBuffer = device.makeBuffer(bytes: &maxIterVar, length: MemoryLayout<Int32>.stride, options: .storageModeShared) else {
        fatalError("Failed to create parameter buffers")
    }
    
    guard let commandBuffer = commandQueue.makeCommandBuffer(),
          let computeEncoder = commandBuffer.makeComputeCommandEncoder() else {
        fatalError("Failed to create command buffer or encoder")
    }
    
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
    
    for y in 0..<height {
        for x in 0..<width {
            result[y][x] = outputPointer[y * width + x]
        }
    }
    
    return result
}

func saveMandelbrotImage(_ data: [[UInt16]], maxIterations: Int, filename: String) {
    let height = data.count
    let width = data[0].count
    
    let colorSpace = CGColorSpaceCreateDeviceRGB()
    let bitmapInfo = CGBitmapInfo(rawValue: CGImageAlphaInfo.noneSkipLast.rawValue)
    
    var imageData = [UInt8](repeating: 0, count: width * height * 4)
    
    for y in 0..<height {
        for x in 0..<width {
            let value = data[y][x]
            let offset = (y * width + x) * 4
            
            if value == maxIterations {
                imageData[offset] = 0
                imageData[offset + 1] = 0
                imageData[offset + 2] = 0
            } else {
                let t = Double(value) / Double(maxIterations)
                imageData[offset] = UInt8(min(255, 9 * (1 - t) * t * t * t * 255))
                imageData[offset + 1] = UInt8(min(255, 15 * (1 - t) * (1 - t) * t * t * 255))
                imageData[offset + 2] = UInt8(min(255, 8.5 * (1 - t) * (1 - t) * (1 - t) * t * 255))
            }
            imageData[offset + 3] = 255
        }
    }
    
    guard let context = CGContext(
        data: &imageData,
        width: width,
        height: height,
        bitsPerComponent: 8,
        bytesPerRow: width * 4,
        space: colorSpace,
        bitmapInfo: bitmapInfo.rawValue
    ) else {
        print("Failed to create CGContext")
        return
    }
    
    guard let cgImage = context.makeImage() else {
        print("Failed to create CGImage")
        return
    }
    
    let nsImage = NSImage(cgImage: cgImage, size: NSSize(width: width, height: height))
    guard let tiffData = nsImage.tiffRepresentation,
          let bitmapImage = NSBitmapImageRep(data: tiffData),
          let pngData = bitmapImage.representation(using: .png, properties: [:]) else {
        print("Failed to create PNG data")
        return
    }
    
    let url = URL(fileURLWithPath: filename)
    try? pngData.write(to: url)
    print("Image saved to \(filename)")
}

// Main execution
if CommandLine.arguments.count > 1 && CommandLine.arguments[1] == "benchmark" {
    let width = 1400
    let height = 800
    let maxIterations = 256
    
    print("Metal 4 Mandelbrot Benchmark (OPTIMIZED)")
    print("Resolution: \(width)x\(height)")
    print("Max iterations: \(maxIterations)")
    print()
    
    // Initialize (compile shader)
    print("Initializing Metal (compiling shader)...")
    initializeMetal()
    
    // Warm-up run
    print("Warm-up run...")
    _ = runMetal4brotOptimized(width: width, height: height, maxIterations: maxIterations)
    
    // Benchmark runs - pure GPU compute only
    var times: [Double] = []
    let numRuns = 5
    
    print("\nRunning \(numRuns) benchmark iterations (GPU compute only)...")
    for i in 1...numRuns {
        let elapsed = runMetal4brotOptimized(width: width, height: height, maxIterations: maxIterations)
        times.append(elapsed)
        print(String(format: "Run %d: %.2f ms", i, elapsed))
    }
    
    print()
    print(String(format: "Best time: %.2f ms", times.min()!))
    print(String(format: "Average: %.2f ms", times.reduce(0, +) / Double(times.count)))
    print(String(format: "Median: %.2f ms", times.sorted()[times.count / 2]))
    let throughput = Double(width * height) / (times.min()! / 1000.0) / 1_000_000.0
    print(String(format: "Throughput: %.2f Mpixels/s", throughput))
    
    // Generate image
    print("\nGenerating image...")
    let result = runMetal4brot(width: width, height: height, maxIterations: maxIterations)
    saveMandelbrotImage(result, maxIterations: maxIterations, filename: "metal4brot.png")
} else {
    print("Usage: swift metal4brot_optimized.swift benchmark")
}
