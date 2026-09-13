import Foundation
import ImageIO
import CoreGraphics

let input = FileHandle.standardInput.readDataToEndOfFile()
guard let source = CGImageSourceCreateWithData(input as CFData, nil),
      let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
    fputs("{\"status\":\"decode_failed\"}\n", stderr)
    exit(2)
}

let width = image.width
let height = image.height
let colorSpace = CGColorSpaceCreateDeviceRGB()
var pixels = [UInt8](repeating: 0, count: width * height * 4)
guard let context = CGContext(
    data: &pixels,
    width: width,
    height: height,
    bitsPerComponent: 8,
    bytesPerRow: width * 4,
    space: colorSpace,
    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
) else {
    fputs("{\"status\":\"context_failed\"}\n", stderr)
    exit(3)
}
context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))

func clamp(_ value: Int, _ lower: Int, _ upper: Int) -> Int {
    min(max(value, lower), upper)
}

func luminance(_ r: UInt8, _ g: UInt8, _ b: UInt8) -> Double {
    (0.2126 * Double(r) + 0.7152 * Double(g) + 0.0722 * Double(b)) / 255.0
}

func average(x: Int, y: Int, w: Int, h: Int) -> Double {
    let x0 = clamp(x, 0, width - 1)
    let y0 = clamp(y, 0, height - 1)
    let x1 = clamp(x + max(w, 1), x0 + 1, width)
    let y1 = clamp(y + max(h, 1), y0 + 1, height)
    var total = 0.0
    var count = 0
    for yy in y0..<y1 {
        for xx in x0..<x1 {
            let offset = (yy * width + xx) * 4
            total += luminance(pixels[offset], pixels[offset + 1], pixels[offset + 2])
            count += 1
        }
    }
    return count == 0 ? 0 : total / Double(count)
}

// Hand cards occupy the lower quarter of the WHOT canvas. Return a compact
// brightness profile so the controller can distinguish highlighted legal cards
// from dimmed illegal cards without reading hidden game state.
var rows: [[Double]] = []
for fraction in [0.74, 0.80, 0.86, 0.92] {
    let y = Int(Double(height) * fraction)
    var row: [Double] = []
    for index in 0..<16 {
        let x = Int(Double(width) * Double(index) / 16.0)
        row.append(average(x: x, y: y, w: max(width / 32, 8), h: max(height / 40, 8)))
    }
    rows.append(row)
}

let result: [String: Any] = [
    "status": "ok",
    "width": width,
    "height": height,
    "brightness_rows": rows
]
let json = try! JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
FileHandle.standardOutput.write(json)
FileHandle.standardOutput.write(Data([10]))
