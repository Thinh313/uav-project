import Foundation
import CoreGraphics
import CoreVideo
import CoreMedia
import VideoToolbox
import CoreText
import Darwin

// Persistent, synthetic live H.264 producer. Source timestamp is a caller PTS,
// not a camera exposure time. DispatchTime values below are durations only.
let width = 1280, height = 720
func ns() -> UInt64 { DispatchTime.now().uptimeNanoseconds }
func ms(_ a: UInt64, _ b: UInt64) -> Double { Double(b - a) / 1_000_000 }
let output = FileHandle.standardOutput
func packet(_ object: [String: Any], _ data: Data = Data()) {
    do {
        let json = try JSONSerialization.data(withJSONObject: object, options: [.sortedKeys])
        guard json.count <= 65536 && data.count <= 2 * 1024 * 1024 else { exit(3) }
        var j = UInt32(json.count).bigEndian, d = UInt32(data.count).bigEndian
        var bytes = Data(bytes: &j, count: 4); bytes.append(Data(bytes: &d, count: 4))
        bytes.append(json); bytes.append(data); output.write(bytes)
    } catch { exit(3) }
}
func fatal(_ reason: String, _ status: OSStatus? = nil) -> Never {
    var item: [String:Any] = ["kind":"error", "error": reason, "sourceKind":"SYNTHETIC"]
    if let status = status { item["osStatus"] = status }
    packet(item); exit(2)
}
final class FrameResult {
    let semaphore = DispatchSemaphore(value: 0)
    var status: OSStatus = noErr
    var data = Data()
    var key = false
    var callbackNs: UInt64 = 0
    var error: String? = nil
}
let callback: VTCompressionOutputCallback = { _, reference, status, _, sample in
    guard let reference = reference else { return }
    let result = Unmanaged<FrameResult>.fromOpaque(reference).takeRetainedValue()
    defer { result.callbackNs = ns(); result.semaphore.signal() }
    result.status = status
    guard status == noErr, let sample = sample, CMSampleBufferDataIsReady(sample) else {
        result.error = "ENCODE_CALLBACK_STATUS_OR_SAMPLE"; return
    }
    let attachments = CMSampleBufferGetSampleAttachmentsArray(sample, createIfNecessary: false) as? [[CFString: Any]]
    result.key = (attachments?.first?[kCMSampleAttachmentKey_NotSync] as? Bool) != true
    let start: [UInt8] = [0, 0, 0, 1]
    if result.key {
        guard let format = CMSampleBufferGetFormatDescription(sample) else { result.error = "FORMAT"; return }
        var count = 0, nalLength: Int32 = 0
        let first = CMVideoFormatDescriptionGetH264ParameterSetAtIndex(format, parameterSetIndex: 0, parameterSetPointerOut: nil, parameterSetSizeOut: nil, parameterSetCountOut: &count, nalUnitHeaderLengthOut: &nalLength)
        guard first == noErr, nalLength == 4, count >= 2 && count <= 8 else { result.error = "PARAMETER_SETS"; return }
        for index in 0..<count {
            var pointer: UnsafePointer<UInt8>?, length = 0
            let code = CMVideoFormatDescriptionGetH264ParameterSetAtIndex(format, parameterSetIndex: index, parameterSetPointerOut: &pointer, parameterSetSizeOut: &length, parameterSetCountOut: nil, nalUnitHeaderLengthOut: nil)
            guard code == noErr, let pointer = pointer, length > 0 && length <= 65536 else { result.error = "PARAMETER_SET_BOUND"; return }
            result.data.append(contentsOf: start); result.data.append(pointer, count: length)
        }
    }
    guard let block = CMSampleBufferGetDataBuffer(sample) else { result.error = "DATA_BUFFER"; return }
    let length = CMBlockBufferGetDataLength(block)
    guard length > 0 && length <= 2 * 1024 * 1024 else { result.error = "ENCODED_BOUND"; return }
    var bytes = [UInt8](repeating: 0, count: length)
    let code = CMBlockBufferCopyDataBytes(block, atOffset: 0, dataLength: length, destination: &bytes)
    guard code == kCMBlockBufferNoErr else { result.error = "BLOCK_COPY"; return }
    var offset = 0
    while offset < length {
        guard offset + 4 <= length else { result.error = "NAL_HEADER"; return }
        let size = Int(bytes[offset]) << 24 | Int(bytes[offset+1]) << 16 | Int(bytes[offset+2]) << 8 | Int(bytes[offset+3])
        offset += 4
        guard size > 0 && offset + size <= length else { result.error = "NAL_BOUND"; return }
        result.data.append(contentsOf: start); result.data.append(contentsOf: bytes[offset..<(offset+size)])
        offset += size
    }
}
var session: VTCompressionSession?
let attrs: [CFString: Any] = [kCVPixelBufferPixelFormatTypeKey: kCVPixelFormatType_32BGRA, kCVPixelBufferWidthKey: width, kCVPixelBufferHeightKey: height, kCVPixelBufferIOSurfacePropertiesKey: [:]]
let creation = VTCompressionSessionCreate(allocator: kCFAllocatorDefault, width: Int32(width), height: Int32(height), codecType: kCMVideoCodecType_H264, encoderSpecification: nil, imageBufferAttributes: attrs as CFDictionary, compressedDataAllocator: nil, outputCallback: callback, refcon: nil, compressionSessionOut: &session)
guard creation == noErr, let encoder = session else { fatal("SESSION_CREATE", creation) }
func set(_ key: CFString, _ value: CFTypeRef) {
    let code = VTSessionSetProperty(encoder, key: key, value: value)
    guard code == noErr else { fatal("PROPERTY_\(key)", code) }
}
set(kVTCompressionPropertyKey_RealTime, kCFBooleanTrue)
set(kVTCompressionPropertyKey_AllowFrameReordering, kCFBooleanFalse)
set(kVTCompressionPropertyKey_ProfileLevel, kVTProfileLevel_H264_Baseline_3_1)
set(kVTCompressionPropertyKey_AverageBitRate, NSNumber(value: 4_000_000))
set(kVTCompressionPropertyKey_ExpectedFrameRate, NSNumber(value: 30))
set(kVTCompressionPropertyKey_MaxKeyFrameInterval, NSNumber(value: 30))
set(kVTCompressionPropertyKey_MaxKeyFrameIntervalDuration, NSNumber(value: 1.0))
let preparation = VTCompressionSessionPrepareToEncodeFrames(encoder)
guard preparation == noErr else { fatal("PREPARE", preparation) }
let hardwarePointer = UnsafeMutablePointer<CFTypeRef?>.allocate(capacity:1)
hardwarePointer.initialize(to:nil)
let hardwareStatus = VTSessionCopyProperty(encoder, key: kVTCompressionPropertyKey_UsingHardwareAcceleratedVideoEncoder, allocator: kCFAllocatorDefault, valueOut: hardwarePointer)
let hardwareValue: Any = hardwareStatus == noErr ? ((hardwarePointer.pointee as? NSNumber)?.boolValue as Any? ?? NSNull()) : NSNull()
hardwarePointer.deinitialize(count:1);hardwarePointer.deallocate()
guard let pool = VTCompressionSessionGetPixelBufferPool(encoder) else { fatal("PIXEL_POOL") }
packet(["kind":"hello", "version":1, "sourceKind":"SYNTHETIC", "codec":"avc1.42001f", "annexb":true, "width":width, "height":height, "fps":30, "bitrate":4_000_000, "hardwareAccelerated":hardwareValue, "hardwarePropertyOSStatus":hardwareStatus, "timestampClaim":"CALLER_PTS_NOT_EXPOSURE", "clock":"DISPATCH_UPTIME_DURATIONS_ONLY"])

func text(_ ctx: CGContext, _ value: String, _ x: Double, _ y: Double, _ size: Double, _ color: CGColor) {
    let font = CTFontCreateWithName("Helvetica-Bold" as CFString, size, nil)
    let string = NSAttributedString(string: value, attributes: [NSAttributedString.Key(kCTFontAttributeName as String):font, NSAttributedString.Key(kCTForegroundColorAttributeName as String):color])
    ctx.textPosition = CGPoint(x:x, y:y); CTLineDraw(CTLineCreateWithAttributedString(string), ctx)
}
func render(_ buffer: CVPixelBuffer, _ id: Int) -> Bool {
    CVPixelBufferLockBaseAddress(buffer, []); defer { CVPixelBufferUnlockBaseAddress(buffer, []) }
    guard let base = CVPixelBufferGetBaseAddress(buffer), let ctx = CGContext(data: base, width: width, height: height, bitsPerComponent: 8, bytesPerRow: CVPixelBufferGetBytesPerRow(buffer), space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue) else { return false }
    let t = Double(id) / 30.0
    ctx.setFillColor(red:0.14, green:0.22, blue:0.24, alpha:1); ctx.fill(CGRect(x:0,y:0,width:width,height:height))
    // A generated moving inspection scene, deliberately labelled synthetic.
    for row in 0..<12 {
        for column in 0..<23 {
            let movement = (t * 18).truncatingRemainder(dividingBy: 85)
            let x = Double(column * 65 - 80) + movement, y = Double(row * 70 - 50)
            let shade = Double((column * 17 + row * 11) % 19) / 100
            ctx.setFillColor(red:0.13 + shade, green:0.23 + shade, blue:0.14 + shade/2, alpha:1)
            ctx.fillEllipse(in: CGRect(x:x,y:y,width:75,height:95))
        }
    }
    ctx.saveGState(); ctx.translateBy(x:640,y:360); ctx.rotate(by:0.28 + sin(t/15)*0.015)
    ctx.setFillColor(red:0.37,green:0.38,blue:0.36,alpha:1);ctx.fill(CGRect(x:-45,y:-600,width:90,height:1200))
    ctx.setStrokeColor(red:0.84,green:0.82,blue:0.66,alpha:1);ctx.setLineWidth(3);ctx.setLineDash(phase:t*15,lengths:[30,25]);ctx.move(to:CGPoint(x:0,y:-600));ctx.addLine(to:CGPoint(x:0,y:600));ctx.strokePath();ctx.restoreGState()
    ctx.setStrokeColor(red:0.8,green:0.83,blue:0.82,alpha:1);ctx.setLineWidth(6)
    for dx in [-230.0, 230.0] {
        ctx.move(to:CGPoint(x:640+dx,y:80));ctx.addLine(to:CGPoint(x:640+dx-30,y:600));ctx.addLine(to:CGPoint(x:640+dx+30,y:600));ctx.closePath();ctx.strokePath()
        for n in 0..<7 {let y=120.0+Double(n)*60;ctx.move(to:CGPoint(x:640+dx-25,y:y));ctx.addLine(to:CGPoint(x:640+dx+25,y:y+45));ctx.strokePath()}
        for y in [460.0,520.0,580.0] {ctx.move(to:CGPoint(x:640+dx-90,y:y));ctx.addLine(to:CGPoint(x:640+dx+90,y:y));ctx.strokePath()}
    }
    ctx.setStrokeColor(red:1,green:1,blue:1,alpha:0.8);ctx.setLineWidth(1)
    ctx.stroke(CGRect(x:610,y:330,width:60,height:60));ctx.move(to:CGPoint(x:580,y:360));ctx.addLine(to:CGPoint(x:700,y:360));ctx.move(to:CGPoint(x:640,y:300));ctx.addLine(to:CGPoint(x:640,y:420));ctx.strokePath()
    ctx.setFillColor(red:0,green:0,blue:0,alpha:0.72);ctx.fill(CGRect(x:24,y:height-80,width:520,height:52))
    text(ctx,"AERIS / SYNTHETIC LIVE / \(id)",40,Double(height-61),22,CGColor(gray:1,alpha:1))
    return true
}
var priorId = -1, priorTimestamp: Int64 = -1, total = 0
var requestBuffer = Data()
func nextLine() -> String? {
    while true {
        if let end = requestBuffer.firstIndex(of:10) {
            let line = requestBuffer[..<end];guard line.count<=4096 else{fatal("REQUEST_BOUND")}
            requestBuffer.removeSubrange(...end)
            guard let text=String(data:line,encoding:.utf8) else{fatal("REQUEST_UTF8")}
            return text
        }
        if requestBuffer.count>4096 {fatal("REQUEST_BOUND")}
        var bytes=[UInt8](repeating:0,count:4096)
        let amount=Darwin.read(STDIN_FILENO,&bytes,4096)
        if amount<0 {if errno==EINTR {continue};fatal("REQUEST_IO")}
        if amount==0 {if !requestBuffer.isEmpty {fatal("REQUEST_TRUNCATED")};return nil}
        requestBuffer.append(contentsOf:bytes.prefix(amount))
    }
}
while let line = nextLine() {
    if line.utf8.count > 4096 { fatal("REQUEST_BOUND") }
    guard let data = line.data(using:.utf8), let item = (try? JSONSerialization.jsonObject(with:data)) as? [String:Any], Set(item.keys).isSubset(of:["frameId","timestampUs","forceKey"]), let idNum = item["frameId"] as? NSNumber, CFGetTypeID(idNum) != CFBooleanGetTypeID(), let timeNum = item["timestampUs"] as? NSNumber, CFGetTypeID(timeNum) != CFBooleanGetTypeID() else { fatal("REQUEST_SCHEMA") }
    let id = idNum.intValue, timestamp = timeNum.int64Value
    guard idNum.doubleValue == Double(id), timeNum.doubleValue == Double(timestamp), id >= 0 && id <= 100_000_000 && id > priorId, timestamp >= 0 && timestamp <= 9_000_000_000_000 && timestamp > priorTimestamp, total < 150_000 else { fatal("REQUEST_ORDER_OR_BOUND") }
    if let force = item["forceKey"] {guard let number=force as? NSNumber,CFGetTypeID(number)==CFBooleanGetTypeID() else{fatal("FORCE_KEY_TYPE")}}
    let force = item["forceKey"] as? Bool ?? false
    let started = ns(); var image: CVPixelBuffer?
    let code = CVPixelBufferPoolCreatePixelBuffer(kCFAllocatorDefault,pool,&image)
    guard code == kCVReturnSuccess, let image = image else { fatal("POOL_ALLOC",code) }
    guard render(image,id) else { fatal("RENDER") }
    let rendered = ns(), result = FrameResult(), retained = Unmanaged.passRetained(result).toOpaque()
    let options: CFDictionary? = force ? [kVTEncodeFrameOptionKey_ForceKeyFrame:true] as CFDictionary : nil
    let encoding = VTCompressionSessionEncodeFrame(encoder,imageBuffer:image,presentationTimeStamp:CMTime(value:timestamp,timescale:1_000_000),duration:CMTime(value:1,timescale:30),frameProperties:options,sourceFrameRefcon:retained,infoFlagsOut:nil)
    guard encoding == noErr else { Unmanaged<FrameResult>.fromOpaque(retained).release(); fatal("ENCODE_SUBMIT",encoding) }
    guard result.semaphore.wait(timeout:.now()+2) == .success else { fatal("ENCODE_CALLBACK_TIMEOUT_2S") }
    guard result.status == noErr, result.error == nil, !result.data.isEmpty else { fatal(result.error ?? "EMPTY_ENCODE",result.status) }
    let completed = ns()
    packet(["kind":"frame","frameId":id,"timestampUs":timestamp,"type":result.key ? "key":"delta","renderMs":ms(started,rendered),"encodeMs":ms(rendered,result.callbackNs),"nativeTotalMs":ms(started,completed),"sourceKind":"SYNTHETIC","hardwareAccelerated":hardwareValue],result.data)
    priorId=id;priorTimestamp=timestamp;total+=1
}
VTCompressionSessionInvalidate(encoder)
