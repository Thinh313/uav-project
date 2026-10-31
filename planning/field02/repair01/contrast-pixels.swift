import AppKit
import CoreText
let input=URL(fileURLWithPath:CommandLine.arguments[1]),output=URL(fileURLWithPath:CommandLine.arguments[2])
let config=try JSONSerialization.jsonObject(with:Data(contentsOf:input)) as! [[String:Any]]
let fontURL=URL(fileURLWithPath:FileManager.default.currentDirectoryPath+"/native/crew02/assets/fonts/Barlow-Medium.ttf")
CTFontManagerRegisterFontsForURL(fontURL as CFURL,.process,nil)
let image=NSImage(size:NSSize(width:900,height:Double(config.count)*84));image.lockFocus()
func color(_ a:[Double])->NSColor{return NSColor(calibratedRed:a[0]/255,green:a[1]/255,blue:a[2]/255,alpha:a.count>3 ? a[3]:1)}
for (i,row) in config.enumerated(){let y=Double(i*84);color(row["scene"]as![Double]).setFill();NSBezierPath(rect:NSRect(x:0,y:y,width:900,height:84)).fill();color(row["plate"]as![Double]).setFill();NSBezierPath(rect:NSRect(x:0,y:y,width:900,height:84)).fill();let text=(row["label"]as!String)+" · Tuổi video 37 ms · Mất nguồn, chưa xác nhận";let attrs:[NSAttributedString.Key:Any]=[.font:NSFont(name:"Barlow-Medium",size:24) ?? NSFont.systemFont(ofSize:24,weight:.medium),.foregroundColor:color(row["foreground"]as![Double])];(text as NSString).draw(at:NSPoint(x:18,y:y+28),withAttributes:attrs)}
image.unlockFocus();let rep=NSBitmapImageRep(data:image.tiffRepresentation!)!;let data=rep.representation(using:.png,properties:[:])!;try data.write(to:output,options:.withoutOverwriting)
var results=[[String:Any]]()
func lum(_ c:[Double])->Double{let l=c.map{v->Double in let n=v/255;return n<=0.04045 ? n/12.92:pow((n+0.055)/1.055,2.4)};return 0.2126*l[0]+0.7152*l[1]+0.0722*l[2]}
for(i,row) in config.enumerated(){let centerY=rep.pixelsHigh-(i*84+20);let bg=rep.colorAt(x:5,y:centerY)!.usingColorSpace(.deviceRGB)!;let b=[Double(bg.redComponent)*255,Double(bg.greenComponent)*255,Double(bg.blueComponent)*255],fg=row["foreground"]as![Double];let ratio=(max(lum(b),lum(fg))+0.05)/(min(lum(b),lum(fg))+0.05);var best=999.0;for x in 18..<850{for yy in (i*84+26)..<(i*84+62){let c=rep.colorAt(x:x,y:rep.pixelsHigh-1-yy)!.usingColorSpace(.deviceRGB)!;let values=[Double(c.redComponent)*255,Double(c.greenComponent)*255,Double(c.blueComponent)*255];best=min(best,zip(values,fg).map{abs($0-$1)}.max()!)}};results.append(["label":row["label"]!,"compositedBackgroundRGB":b,"foregroundRGB":fg,"contrastRatio":ratio,"closestRasterizedGlyphDelta":best,"pass":ratio>=4.5 && best<=3.0])}
let result=try JSONSerialization.data(withJSONObject:["scope":"APPKIT_RASTER_MOCK_GLASS_EXTREME_SCENES_NOT_BROWSER_ANDROID_PIXELS","results":results,"passed":results.filter{$0["pass"]as!Bool}.count],options:[.prettyPrinted,.sortedKeys]);print(String(data:result,encoding:.utf8)!)
