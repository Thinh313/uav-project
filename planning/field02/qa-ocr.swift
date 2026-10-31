// Read-only screenshot OCR for ADB test navigation. Never controls any app.
import Foundation
import Vision
import AppKit
let url=URL(fileURLWithPath:CommandLine.arguments[1])
let image=NSImage(contentsOf:url)!
var box=NSRect(origin:.zero,size:image.size)
let cg=image.cgImage(forProposedRect:&box,context:nil,hints:nil)!
let request=VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false
request.recognitionLanguages = ["en-US","vi-VN"]
try VNImageRequestHandler(cgImage:cg,options:[:]).perform([request])
let rows=(request.results ?? []).compactMap { o -> [String:Any]? in
 guard let c=o.topCandidates(1).first else{return nil}
 let b=o.boundingBox
 return ["text":c.string,"confidence":c.confidence,"x":b.minX*Double(cg.width),"y":(1-b.maxY)*Double(cg.height),"width":b.width*Double(cg.width),"height":b.height*Double(cg.height)]
}
let data=try JSONSerialization.data(withJSONObject:rows,options:[.sortedKeys])
print(String(data:data,encoding:.utf8)!)
