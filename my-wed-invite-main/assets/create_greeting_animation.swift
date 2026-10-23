import CoreGraphics
import Foundation
import ImageIO
import UniformTypeIdentifiers

let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let sourceURL = root.appendingPathComponent("assets/namaskaram-couple.png")
let outputURL = root.appendingPathComponent("assets/namaskaram-greeting.gif")
try? FileManager.default.removeItem(at: outputURL)
let width = 450
let height = 675
let fps = 15
let frameCount = 36

guard let source = CGImageSourceCreateWithURL(sourceURL as CFURL, nil),
      let portrait = CGImageSourceCreateImageAtIndex(source, 0, nil),
      let destination = CGImageDestinationCreateWithURL(outputURL as CFURL, UTType.gif.identifier as CFString, frameCount, nil) else {
    fatalError("Could not load the couple artwork or create the greeting animation")
}
let loop: [CFString: Any] = [kCGImagePropertyGIFLoopCount: 0]
CGImageDestinationSetProperties(destination, [kCGImagePropertyGIFDictionary: loop] as CFDictionary)

let petals: [(CGFloat, CGFloat, CGFloat, CGFloat, CGFloat)] = (0..<18).map { i in
    let n = CGFloat(i)
    return (CGFloat((i * 53 + 19) % width), CGFloat((i * 97 + 47) % height),
            CGFloat((i * 41 + 23) % 90) / 100 + 0.12, CGFloat((i * 13) % 6 + 2), n * 0.73)
}

for frame in 0..<frameCount {
    let phase = CGFloat(frame) / CGFloat(frameCount) * 2 * .pi
    let context = CGContext(data: nil, width: width, height: height, bitsPerComponent: 8, bytesPerRow: width * 4,
                            space: CGColorSpaceCreateDeviceRGB(),
                            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
    context.clear(CGRect(x: 0, y: 0, width: width, height: height))
    let scale = min(CGFloat(width) / CGFloat(portrait.width), CGFloat(height) / CGFloat(portrait.height)) * (1.015 + 0.012 * sin(phase))
    let imageW = CGFloat(portrait.width) * scale
    let imageH = CGFloat(portrait.height) * scale
    context.saveGState()
    context.setShadow(offset: CGSize(width: 0, height: -6), blur: 24, color: CGColor(gray: 0, alpha: 0.44))
    context.draw(portrait, in: CGRect(x: (CGFloat(width) - imageW) / 2,
                                     y: (CGFloat(height) - imageH) / 2 + 3 * sin(phase),
                                     width: imageW, height: imageH))
    context.restoreGState()

    for (x, y, speed, size, offset) in petals {
        let py = (y + CGFloat(frame) * speed * 4 + offset).truncatingRemainder(dividingBy: CGFloat(height))
        context.saveGState()
        context.translateBy(x: x + 8 * sin(phase + offset), y: py)
        context.rotate(by: phase + offset)
        context.setFillColor(CGColor(red: 1, green: 0.73, blue: 0.18, alpha: 0.72))
        context.fillEllipse(in: CGRect(x: -size * 0.55, y: -size * 0.28, width: size * 1.1, height: size * 0.56))
        context.restoreGState()
    }

    guard let image = context.makeImage() else { fatalError("Could not render animation frame") }
    let frameProperties: [CFString: Any] = [kCGImagePropertyGIFDictionary: [kCGImagePropertyGIFDelayTime: 1.0 / Double(fps)]]
    CGImageDestinationAddImage(destination, image, frameProperties as CFDictionary)
}

guard CGImageDestinationFinalize(destination) else { fatalError("Could not write the greeting animation") }
print("Created \(outputURL.path)")
