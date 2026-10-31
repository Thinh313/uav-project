// QA-only accurate English Vision OCR of an existing screenshot. No UI/app control.
import Foundation
import Vision
import AppKit
let a=CommandLine.arguments
if a.count != 2 && a.count != 6 { fputs("IMAGE [CROP_X CROP_Y CROP_WIDTH CROP_HEIGHT]\n",stderr);exit(2) }
let url=URL(fileURLWithPath:a[1]);guard let image=NSImage(contentsOf:url)else{exit(3)}
var imageBox=NSRect(origin:.zero,size:image.size)
guard let full=image.cgImage(forProposedRect:&imageBox,context:nil,hints:nil)else{exit(4)}
var x=0,y=0,w=full.width,h=full.height
if a.count==6{guard let xx=Int(a[2]),let yy=Int(a[3]),let ww=Int(a[4]),let hh=Int(a[5]),xx>=0,yy>=0,ww>0,hh>0,xx+ww<=full.width,yy+hh<=full.height else{exit(5)};x=xx;y=yy;w=ww;h=hh}
guard let cg=full.cropping(to:CGRect(x:x,y:y,width:w,height:h))else{exit(6)}
let request=VNRecognizeTextRequest();request.recognitionLevel = .accurate;request.usesLanguageCorrection=false;request.recognitionLanguages=["en-US"]
try VNImageRequestHandler(cgImage:cg,options:[:]).perform([request])
let rows=(request.results ?? []).compactMap{o->[String:Any]? in
 guard let c=o.topCandidates(1).first else{return nil};let b=o.boundingBox
 return["text":c.string,"confidence":c.confidence,"x":Double(x)+b.minX*Double(cg.width),"y":Double(y)+(1-b.maxY)*Double(cg.height),"width":b.width*Double(cg.width),"height":b.height*Double(cg.height)]
}
print(String(data:try JSONSerialization.data(withJSONObject:rows,options:[.sortedKeys]),encoding:.utf8)!)
