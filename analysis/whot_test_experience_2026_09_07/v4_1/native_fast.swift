// Persistent local JSONL worker. Uses visible window pixels, never browser internals.
import Foundation
import AppKit
import Vision
import ImageIO
import UniformTypeIdentifiers
import ScreenCaptureKit
import CoreImage
import CryptoKit

enum Fault: Error { case invalid(String) }

final class WindowFrames: NSObject, SCStreamOutput {
    private var stream: SCStream?
    private var windowID: UInt32?
    private let lock=NSLock()
    private var latest: CVPixelBuffer?
    private var timestamp: UInt64=0
    private var seq=0
    private let context=CIContext()
    private let queue=DispatchQueue(label:"whot.frames")
    func stream(_ stream:SCStream,didOutputSampleBuffer sampleBuffer:CMSampleBuffer,of type:SCStreamOutputType) {
        guard type == .screen, CMSampleBufferIsValid(sampleBuffer) else {return}
        if let attachments=CMSampleBufferGetSampleAttachmentsArray(sampleBuffer,createIfNecessary:false) as? [[SCStreamFrameInfo:Any]],
           let raw=attachments.first?[.status] as? Int,let status=SCFrameStatus(rawValue:raw) {
            if status == .idle {
                lock.lock();if latest != nil {timestamp=DispatchTime.now().uptimeNanoseconds;seq+=1};lock.unlock();return
            }
            guard status == .complete else{return}
        }
        guard let buffer=CMSampleBufferGetImageBuffer(sampleBuffer) else {return}
        lock.lock();latest=buffer;timestamp=DispatchTime.now().uptimeNanoseconds;seq+=1;lock.unlock()
    }
    private func start(_ id:UInt32)throws {
        guard CGPreflightScreenCaptureAccess() else {throw Fault.invalid("capture_permission_missing")}
        if let old=stream {old.stopCapture(completionHandler:nil)}
        lock.lock();latest=nil;timestamp=0;lock.unlock()
        let ready=DispatchSemaphore(value:0)
        var failure:Error?
        SCShareableContent.getExcludingDesktopWindows(true,onScreenWindowsOnly:true) { content,error in
            defer {ready.signal()}
            if let error=error {failure=error;return}
            guard let window=content?.windows.first(where:{$0.windowID==id && $0.owningApplication?.bundleIdentifier=="com.google.Chrome"}) else {failure=Fault.invalid("window_unavailable");return}
            let config=SCStreamConfiguration()
            config.width=Int(window.frame.width*2);config.height=Int(window.frame.height*2)
            config.minimumFrameInterval=CMTime(value:1,timescale:8)
            config.queueDepth=3;config.showsCursor=false;config.capturesAudio=false
            let next=SCStream(filter:SCContentFilter(desktopIndependentWindow:window),configuration:config,delegate:nil)
            do {try next.addStreamOutput(self,type:.screen,sampleHandlerQueue:self.queue)}
            catch {failure=error;return}
            self.stream=next
            next.startCapture {error in if error != nil {self.lock.lock();self.latest=nil;self.lock.unlock(); fputs("capture_start_failed\n",stderr)}}
        }
        guard ready.wait(timeout:.now()+3) == .success else {throw Fault.invalid("capture_start_timeout")}
        if let error=failure {throw error}
        windowID=id
    }
    func frame(windowID id:UInt32)throws -> (CGImage,Double,Int) {
        if windowID != id {try start(id)}
        let deadline=DispatchTime.now().uptimeNanoseconds+2_000_000_000
        while true {
            lock.lock();let buffer=latest;let at=timestamp;let number=seq;lock.unlock()
            if let buffer=buffer {
                let age=Double(DispatchTime.now().uptimeNanoseconds-at)/1e6
                if age>500 {
                    // Do not accept stale pixels. Allow the existing live stream
                    // a bounded chance to deliver a fresh frame after slow OCR.
                    if DispatchTime.now().uptimeNanoseconds>deadline {throw Fault.invalid("capture_stream_stale")}
                    Thread.sleep(forTimeInterval:0.01)
                    continue
                }
                let ci=CIImage(cvPixelBuffer:buffer)
                guard let image=context.createCGImage(ci,from:ci.extent) else {throw Fault.invalid("capture_image_failed")}
                return (image,age,number)
            }
            if DispatchTime.now().uptimeNanoseconds>deadline {throw Fault.invalid("capture_frame_timeout")}
            Thread.sleep(forTimeInterval:0.01)
        }
    }
}

let digitBankPath=URL(fileURLWithPath:#filePath).deletingLastPathComponent().deletingLastPathComponent().appendingPathComponent("v3/visual_assets/card_digits.json").path
let inputEnabled=CommandLine.arguments.contains("--allow-input")
let captureStream=WindowFrames()
struct Witness {
    let windowID:Int;let seq:Int;let at:UInt64;let rect:[Double]
    let regions:[String:[Double]];let hashes:[String:String]
    let analysisRegions:[String:[Double]];let semantics:[String:Any]
}
var witness:Witness?=nil
func pixelHash(_ image:CGImage)throws->String {
    let w=image.width,h=image.height
    var bytes=[UInt8](repeating:0,count:w*h*4)
    guard let ctx=CGContext(data:&bytes,width:w,height:h,bitsPerComponent:8,bytesPerRow:w*4,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue) else {throw Fault.invalid("witness_context")}
    ctx.draw(image,in:CGRect(x:0,y:0,width:w,height:h))
    return SHA256.hash(data:Data(bytes)).map{String(format:"%02x",$0)}.joined()
}
func verifyWitness(_ q:[String:Any],_ id:Int,_ b:[String:Double])throws->Double {
    guard let old=witness,old.windowID==id,q["expected_capture_seq"] as? Int==old.seq,
          let rect=q["canvas_screen"] as? [Double],rect==old.rect,
          Double(DispatchTime.now().uptimeNanoseconds-old.at)/1e6<=2000 else {throw Fault.invalid("witness_expired")}
    let fresh=try captureStream.frame(windowID:UInt32(id))
    let relative=[(rect[0]-b["X"]!)/b["Width"]!, (rect[1]-b["Y"]!)/b["Height"]!,rect[2]/b["Width"]!,rect[3]/b["Height"]!]
    let image=try crop(fresh.0,relative)
    var pixelsEqual=true
    for (name,box) in old.regions {if try pixelHash(crop(image,box)) != old.hashes[name] {pixelsEqual=false;break}}
    if !pixelsEqual {
        let current=try analyze(image,old.analysisRegions)
        guard sameSemantic(old.semantics,current) else {throw Fault.invalid("witness_changed")}
    }
    return fresh.1
}
func normalizedText(_ r:[String:Any],digits:Bool)->[String] {
    let texts=r["text"] as? [[String:Any]] ?? []
    let keepDigits=digits || texts.contains{($0["value"] as? String ?? "").uppercased().contains("PICK")}
    return texts.compactMap { item -> String? in
        guard let text=item["value"] as? String else{return nil}
        let value=String(text.uppercased().filter{ $0.isLetter || (keepDigits && $0.isNumber) })
        return value.isEmpty ? nil:value
    }.sorted()
}
func sameSemantic(_ old:[String:Any],_ fresh:[String:Any])->Bool {
    for name in ["hand","table","raised"] {
        let a=old[name] as? [String:Any] ?? [:],b=fresh[name] as? [String:Any] ?? [:]
        let aa=a["cards"] as? [[String:Any]] ?? [],bb=b["cards"] as? [[String:Any]] ?? []
        if name=="raised" && aa.isEmpty {continue}
        guard aa.count==bb.count,a["number_group_count"] as? Int==b["number_group_count"] as? Int else{return false}
        for (x,y) in zip(aa,bb) {
            let evidence=y["shape_evidence"] as? [String:Any] ?? [:]
            guard (y["rank_score"] as? Double ?? 0)>=0.82,
                  ["circle","square","triangle","cross","star","wild"].contains(y["shape"] as? String ?? ""),
                  y["rank"] as? Int==20 || evidence["marker_consistent"] as? Bool==true else{return false}
            guard x["rank"] as? Int==y["rank"] as? Int,x["shape"] as? String==y["shape"] as? String,
                  let p=x["box"] as? [Double],let q=y["box"] as? [Double],p.count==4,q.count==4,
                  zip(p,q).allSatisfy({abs($0-$1)<=0.001}) else{return false}
            if name=="hand" && ((x["ink_red"] as? Double ?? 0)>=210) != ((y["ink_red"] as? Double ?? 0)>=210) {return false}
        }
    }
    for name in ["turn","effect","title","bet"] {
        guard normalizedText(old[name] as? [String:Any] ?? [:],digits:name=="bet") == normalizedText(fresh[name] as? [String:Any] ?? [:],digits:name=="bet") else{return false}
    }
    if (old["draw_prompt"] as? [String:Any])?["verified"] as? Bool != (fresh["draw_prompt"] as? [String:Any])?["verified"] as? Bool {return false}
    for name in ["pick_cross","pick_triangle","pick_star"] {
        if (old[name] as? [String:Any])?["shape"] as? String != (fresh[name] as? [String:Any])?["shape"] as? String {return false}
    }
    let effectWords=normalizedText(old["effect"] as? [String:Any] ?? [:],digits:false).joined()
    if !effectWords.contains("MATCHSYMBOL") {return true}
    let a=(old["indicator"] as? [String:Any])?["shape_evidence"] as? [String:Any]
    let b=(fresh["indicator"] as? [String:Any])?["shape_evidence"] as? [String:Any]
    return a?["shape"] as? String == b?["shape"] as? String
}
var digitBankCache:[String:[[Double]]]?=nil
func glyphs(_ image:CGImage,rankBand:Bool=false)throws->[[String:Any]] {
    let w=image.width,h=image.height;var px=[UInt8](repeating:0,count:w*h*4)
    guard let ctx=CGContext(data:&px,width:w,height:h,bitsPerComponent:8,bytesPerRow:w*4,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue) else {throw Fault.invalid("glyph_context")}
    ctx.draw(image,in:CGRect(x:0,y:0,width:w,height:h))
    var mask=[Bool](repeating:false,count:w*h),seen=[Bool](repeating:false,count:w*h)
    for i in 0..<w*h {let r=Double(px[i*4]),g=Double(px[i*4+1]),b=Double(px[i*4+2]);mask[i]=r>35 && r>1.2*g && g>1.12*b}
    var blobs=[(Int,Int,Int,Int,[Int])]()
    for start in 0..<w*h where mask[start] && !seen[start] {
        var queue=[start],cursor=0;seen[start]=true
        var x0=start%w,x1=x0,y0=start/w,y1=y0
        while cursor<queue.count {
            let i=queue[cursor];cursor+=1;let x=i%w,y=i/w
            x0=min(x0,x);x1=max(x1,x);y0=min(y0,y);y1=max(y1,y)
            for dy in -1...1 {for dx in -1...1 {
                let xx=x+dx,yy=y+dy
                if xx>=0 && xx<w && yy>=0 && yy<h {let j=yy*w+xx;if mask[j] && !seen[j]{seen[j]=true;queue.append(j)}}
            }}
        }
        let bw=x1-x0+1,bh=y1-y0+1
        if bh>=6 && bw>=2 && Double(bw)/Double(bh)>0.22 && Double(bw)/Double(bh)<1.4 && queue.count>=12 {blobs.append((x0,y0,bw,bh,queue))}
    }
    let maxH=blobs.map{$0.3}.max() ?? 0
    return blobs.filter{
        if rankBand {return Double($0.3)>=Double(h)*0.42 && Double($0.3)<=Double(h)*0.85}
        return Double($0.3)>=Double(maxH)*0.65
    }.sorted{$0.0<$1.0}.map { x,y,bw,bh,cells in
        let set=Set(cells);var signature=[Double]()
        for yy in 0..<28 {for xx in 0..<20 {let sx=x+min(bw-1,Int((Double(xx)+0.5)*Double(bw)/20));let sy=y+min(bh-1,Int((Double(yy)+0.5)*Double(bh)/28));signature.append(set.contains(sy*w+sx) ? 1:0)}}
        let inkRed=cells.map{Double(px[$0*4])}.reduce(0,+)/Double(cells.count)
        return ["box":[Double(x),Double(y),Double(bw),Double(bh)],"signature":signature,"ink_red":inkRed]
    }
}
func enclosedHoles(_ signature:[Double])->Int {
    guard signature.count==560 else{return -1}
    var seen=Set<Int>(),holes=0
    for start in 0..<560 where signature[start]==0 && !seen.contains(start) {
        var queue=[start],cursor=0,edge=false;seen.insert(start)
        while cursor<queue.count {
            let p=queue[cursor];cursor+=1;let x=p%20,y=p/20
            if x==0 || x==19 || y==0 || y==27 {edge=true}
            for (a,b) in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)] where a>=0 && a<20 && b>=0 && b<28 {
                let q=b*20+a;if signature[q]==0 && !seen.contains(q){seen.insert(q);queue.append(q)}
            }
        }
        if !edge {holes+=1}
    }
    return holes
}
func templateNumbers(_ image:CGImage,_ roi:[Double])throws->[[String:Any]] {
    if digitBankCache==nil,let data=try? Data(contentsOf:URL(fileURLWithPath:digitBankPath)){digitBankCache=try? JSONSerialization.jsonObject(with:data) as? [String:[[Double]]]}
    guard let bank=digitBankCache else {return []}
    let band=[roi[0],roi[1],roi[2],roi[3]*0.24];let cut=try crop(image,band)
    let pieces=try glyphs(cut,rankBand:true);var out=[[String:Any]]();var group=[(String,[Double],Double,Double)]()
    func flush(){
        guard !group.isEmpty else{return}
        let text=group.map{$0.0}.joined();let first=group.first!.1,last=group.last!.1
        let rank=Int(text)
        let valid=rank.map{(1...14).contains($0) || $0==20} ?? false
        out.append(["rank":valid ? rank! as Any:NSNull(),"box":[band[0]+first[0]/Double(image.width),band[1]+first[1]/Double(image.height),(last[0]+last[2]-first[0])/Double(image.width),first[3]/Double(image.height)],"confidence":valid ? group.map{$0.2}.min()!:0,"ink_red":group.map{$0.3}.min() ?? 0,"method":"glyph_template_topology_checked"])
        group=[]
    }
    for piece in pieces {
        let b=piece["box"] as! [Double],sig=piece["signature"] as! [Double]
        let scores=bank.map{ label,refs -> (String,Double) in
            let distances=refs.filter{$0.count==sig.count}.map{ ref in zip(ref,sig).map{abs($0-$1)}.reduce(0,+)/Double(sig.count)}
            return (label,distances.min() ?? 1)
        }.sorted{$0.1<$1.1}
        if let last=group.last, b[0]-(last.1[0]+last.1[2])>min(b[3],last.1[3])*0.4 {flush()}
        let inkRed=piece["ink_red"] as? Double ?? 0
        guard scores.count>1 else {group.append(("?",b,0,inkRed));continue}
        var chosen=scores[0];var separated=scores[1].1-scores[0].1>0.025
        if !separated && Set(scores.prefix(2).map{$0.0})==Set(["0","8"]) {
            let holes=enclosedHoles(sig);let label=holes==1 ? "0":(holes==2 ? "8":"")
            if let candidate=scores.prefix(2).first(where:{$0.0==label}) {chosen=candidate;separated=true}
        }
        guard separated,chosen.1<0.18 else {group.append(("?",b,0,inkRed));continue}
        group.append((chosen.0,b,1-chosen.1,inkRed))
    }
    flush();return out
}
func axValue(_ e: AXUIElement, _ key: String) -> CFTypeRef? {
    var value:CFTypeRef?;return AXUIElementCopyAttributeValue(e,key as CFString,&value) == .success ? value:nil
}
func frontPID()->pid_t? {
    guard let raw=axValue(AXUIElementCreateSystemWide(),kAXFocusedApplicationAttribute) else{return nil}
    var pid:pid_t=0
    guard AXUIElementGetPid(raw as! AXUIElement,&pid) == .success else{return nil}
    return pid
}
func chromeInFront()->Bool {
    guard let pid=frontPID() else{return false}
    return NSRunningApplication(processIdentifier:pid)?.bundleIdentifier=="com.google.Chrome"
}
func visibleURL(_ element:AXUIElement, _ depth:Int=0) -> String? {
    if depth>18{return nil}
    // Only the browser address field is authoritative. AXURL on a child may
    // belong to an iframe or unrelated link and is never a navigation proof.
    let desc=axValue(element,kAXDescriptionAttribute) as? String ?? ""
    if ["地址和搜索栏","Address and search bar"].contains(desc),let v=axValue(element,kAXValueAttribute) as? String {
        return v.hasPrefix("http") ? v : "https://"+v
    }
    for child in axValue(element,kAXChildrenAttribute) as? [AXUIElement] ?? [] {
        if let url=visibleURL(child,depth+1){return url}
    }
    return nil
}
func webBounds(_ e:AXUIElement,_ depth:Int=0)->[Double]? {
    if depth>18{return nil}
    if (axValue(e,kAXRoleAttribute) as? String)=="AXWebArea",
       let p=axValue(e,kAXPositionAttribute),let s=axValue(e,kAXSizeAttribute),
       CFGetTypeID(p)==AXValueGetTypeID(),CFGetTypeID(s)==AXValueGetTypeID() {
        var pos=CGPoint.zero;var size=CGSize.zero
        if AXValueGetValue(p as! AXValue,.cgPoint,&pos),AXValueGetValue(s as! AXValue,.cgSize,&size),size.width>300,size.height>300 {
            return [Double(pos.x),Double(pos.y),Double(size.width),Double(size.height)]
        }
    }
    for child in axValue(e,kAXChildrenAttribute) as? [AXUIElement] ?? [] {
        if let box=webBounds(child,depth+1){return box}
    }
    return nil
}
func windows() -> [[String:Any]] {
    let all = CGWindowListCopyWindowInfo([.optionOnScreenOnly,.excludeDesktopElements], kCGNullWindowID) as? [[String:Any]] ?? []
    return all.filter { ($0[kCGWindowOwnerName as String] as? String) == "Google Chrome" && ($0[kCGWindowLayer as String] as? Int) == 0 }
        .map { ["id":$0[kCGWindowNumber as String]!, "pid":$0[kCGWindowOwnerPID as String]!, "bounds":$0[kCGWindowBounds as String]!] }
}
func axBounds(_ element: AXUIElement) -> [String:Double]? {
    guard let p=axValue(element,kAXPositionAttribute),let s=axValue(element,kAXSizeAttribute),
          CFGetTypeID(p)==AXValueGetTypeID(),CFGetTypeID(s)==AXValueGetTypeID() else {return nil}
    var pos=CGPoint.zero
    var size=CGSize.zero
    guard AXValueGetValue(p as! AXValue,.cgPoint,&pos),AXValueGetValue(s as! AXValue,.cgSize,&size) else {return nil}
    return ["X":Double(pos.x),"Y":Double(pos.y),"Width":Double(size.width),"Height":Double(size.height)]
}
func focusedChromeWindowID() -> Int? {
    guard let pid=frontPID(),let app=NSRunningApplication(processIdentifier:pid),
          app.bundleIdentifier=="com.google.Chrome" else {return nil}
    let appElement=AXUIElementCreateApplication(app.processIdentifier)
    guard let raw=axValue(appElement,kAXFocusedWindowAttribute) else {return nil}
    let focused=raw as! AXUIElement
    guard let fb=axBounds(focused) else {return nil}
    return windows().first { item in
        guard let b=item["bounds"] as? [String:Double] else {return false}
        return ["X","Y","Width","Height"].allSatisfy { key in abs((b[key] ?? .nan)-(fb[key] ?? .nan)) < 1.0 }
    }?["id"] as? Int
}
func exactAXWindow(_ pid:Int,_ id:Int)->AXUIElement? {
    guard let wanted=windows().first(where:{($0["id"] as? Int)==id && ($0["pid"] as? Int)==pid}),
          let bounds=wanted["bounds"] as? [String:Double] else{return nil}
    let list=axValue(AXUIElementCreateApplication(pid_t(pid)),kAXWindowsAttribute) as? [AXUIElement] ?? []
    return list.first { e in
        guard let b=axBounds(e) else{return false}
        return ["X","Y","Width","Height"].allSatisfy{abs((b[$0] ?? .nan)-(bounds[$0] ?? .nan))<1}
    }
}
func crop(_ image: CGImage, _ a: [Double]) throws -> CGImage {
    guard a.count == 4, a.allSatisfy({$0.isFinite && $0 >= 0}), a[2] > 0, a[3] > 0, a[0]+a[2] <= 1.001, a[1]+a[3] <= 1.001 else { throw Fault.invalid("invalid_crop") }
    let r=CGRect(x:a[0]*Double(image.width),y:a[1]*Double(image.height),width:a[2]*Double(image.width),height:a[3]*Double(image.height)).integral
    guard let c=image.cropping(to:r) else { throw Fault.invalid("crop_failed") }; return c
}
func readImage(_ path: String) throws -> CGImage {
    guard let s=CGImageSourceCreateWithURL(URL(fileURLWithPath:path) as CFURL,nil), let i=CGImageSourceCreateImageAtIndex(s,0,nil) else { throw Fault.invalid("image_unavailable") }; return i
}
func writeImage(_ image: CGImage, _ path: String) throws {
    guard let d=CGImageDestinationCreateWithURL(URL(fileURLWithPath:path) as CFURL,UTType.png.identifier as CFString,1,nil) else { throw Fault.invalid("write_failed") }
    CGImageDestinationAddImage(d,image,nil)
    guard CGImageDestinationFinalize(d) else { throw Fault.invalid("write_failed") }
}
func feature(_ image: CGImage) throws -> [Double] {
    var px=[UInt8](repeating:0,count:24*24)
    guard let ctx=CGContext(data:&px,width:24,height:24,bitsPerComponent:8,bytesPerRow:24,space:CGColorSpaceCreateDeviceGray(),bitmapInfo:0) else { throw Fault.invalid("context_failed") }
    ctx.interpolationQuality = .high
    ctx.draw(image,in:CGRect(x:0,y:0,width:24,height:24))
    let v=px.map{Double($0)/255}; let mean=v.reduce(0,+)/Double(v.count)
    let scale=sqrt(v.map{($0-mean)*($0-mean)}.reduce(0,+)/Double(v.count))
    return v.map{($0-mean)/max(scale,0.01)}
}
func iconShape(_ image:CGImage)->[String:Any] {
    let w=image.width,h=image.height
    var px=[UInt8](repeating:0,count:w*h*4)
    guard let c=CGContext(data:&px,width:w,height:h,bitsPerComponent:8,bytesPerRow:w*4,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue) else {return ["shape":"unknown"]}
    c.draw(image,in:CGRect(x:0,y:0,width:w,height:h))
    var coords=[(Int,Int)]()
    for y in 0..<h {for x in 0..<w {let j=(y*w+x)*4
        let r=Double(px[j]),g=Double(px[j+1]),b=Double(px[j+2])
        if r>35 && r>1.2*g && g>1.12*b {coords.append((x,y))}
    }}
    guard coords.count>=8 else {return ["shape":"unknown","fill":0]}
    // Select one connected orange component so an overlapping neighbour card
    // cannot change the geometry of the symbol being classified.
    let all=Set(coords.map { $0.1*w + $0.0 })
    var seen=Set<Int>(),best=[(Int,Int)]()
    for (sx,sy) in coords {
        let seed=sy*w+sx; if seen.contains(seed){continue}
        var queue=[seed],component=[(Int,Int)]();seen.insert(seed);var qi=0
        while qi<queue.count {
            let id=queue[qi];qi += 1;let x=id%w,y=id/w;component.append((x,y))
            for dy in -1...1 {for dx in -1...1 where dx != 0 || dy != 0 {
                let nx=x+dx,ny=y+dy;guard nx>=0 && nx<w && ny>=0 && ny<h else {continue}
                let nid=ny*w+nx;if all.contains(nid) && !seen.contains(nid){seen.insert(nid);queue.append(nid)}
            }}
        }
        if component.count>best.count {best=component}
    }
    let shapeCoords=best.count>=8 ? best : coords
    let minX=shapeCoords.map{$0.0}.min()!,maxX=shapeCoords.map{$0.0}.max()!,minY=shapeCoords.map{$0.1}.min()!,maxY=shapeCoords.map{$0.1}.max()!
    let bw=maxX-minX+1,bh=maxY-minY+1
    let fill=Double(shapeCoords.count)/Double(bw*bh)
    let mid=shapeCoords.filter{$0.1>=minY+bh/3 && $0.1<=minY+2*bh/3}.count
    let centerFill=Double(mid)/Double(bw*(2*bh/3-bh/3+1))
    // Solid upward-pointing triangles have a distinctive monotone row-width
    // profile (narrow at the top, widest at the bottom). This survives card
    // overlap better than a global fill threshold, which can make a triangle
    // look like a circle when the crop includes a little background.
    var rowWidths=[Int](repeating:0,count:bh)
    for (_,y) in shapeCoords { rowWidths[y-minY] += 1 }
    let edge=max(1,bh/8)
    let topWidth=Double(rowWidths.prefix(edge).reduce(0,+))/Double(edge)
    let bottomWidth=Double(rowWidths.suffix(edge).reduce(0,+))/Double(edge)
    let meanWidth=Double(rowWidths.reduce(0,+))/Double(max(1,bh))
    let centerStart=bh/3,centerEnd=max(centerStart+1,(2*bh)/3)
    let rowCenter=Double(rowWidths[centerStart..<centerEnd].reduce(0,+))/Double(max(1,centerEnd-centerStart))
    let rowEdge=(topWidth+bottomWidth)/2
    var colWidths=[Int](repeating:0,count:bw)
    for (x,_) in shapeCoords { colWidths[x-minX] += 1 }
    let colEdgeN=max(1,bw/8)
    let leftWidth=Double(colWidths.prefix(colEdgeN).reduce(0,+))/Double(colEdgeN)
    let rightWidth=Double(colWidths.suffix(colEdgeN).reduce(0,+))/Double(colEdgeN)
    let colCenter=Double(colWidths[ bw/3..<max(bw/3+1,(2*bw)/3) ].reduce(0,+))/Double(max(1,(2*bw)/3-bw/3))
    let colEdge=(leftWidth+rightWidth)/2
    let yMean=(Double(bh)-1)/2
    var cov=0.0,varianceY=0.0,varianceW=0.0
    for (i,v) in rowWidths.enumerated() { let yi=Double(i)-yMean;let wi=Double(v)-meanWidth;cov += yi*wi;varianceY += yi*yi;varianceW += wi*wi }
    let rowR2 = varianceY>0 && varianceW>0 ? (cov*cov)/(varianceY*varianceW) : 0
    let triangleLike = topWidth < bottomWidth*0.58 && bottomWidth > Double(bw)*0.50 && rowR2 > 0.35
    let rowJump=zip(rowWidths.dropFirst(),rowWidths).map{abs($0-$1)}.max() ?? 0
    let colJump=zip(colWidths.dropFirst(),colWidths).map{abs($0-$1)}.max() ?? 0
    let steppedCross=Double(rowJump)/Double(bw)>0.25 && Double(colJump)/Double(bh)>0.25 && rowCenter/Double(bw)>0.8 && colCenter/Double(bh)>0.8 && rowEdge/Double(bw)<0.55 && colEdge/Double(bh)<0.55
    var name="unknown"
    if fill>0.92 {name="square"}
    else if triangleLike && rowR2>0.6 {name="triangle"}
    else if steppedCross && fill>0.32 && fill<0.80 {name="cross"}
    else if fill>0.68 && fill<0.90 && Double(bw)/Double(bh)>0.75 && Double(bw)/Double(bh)<1.33 {name="circle"}
    else if fill>0.15 && fill<0.55 && rowCenter/Double(bw)<0.78 && colCenter/Double(bh)<0.78 {name="star"}
    else if fill>0.32 && fill<0.68 && rowCenter/Double(bw)>0.8 && colCenter/Double(bh)>0.8 {name="cross"}
    return ["shape":name,"fill":fill,"center_fill":centerFill,"row_r2":rowR2,
            "bbox_w":bw,"bbox_h":bh,
            "top_width":topWidth,"bottom_width":bottomWidth,"row_center":rowCenter,
            "row_edge":rowEdge,"col_center":colCenter,"col_edge":colEdge,
            "row_profile":rowWidths,"col_profile":colWidths,
            "method":"geometry_unverified"]
}
func drawPrompt(_ image:CGImage)->[String:Any] {
    let w=image.width,h=image.height;var bytes=[UInt8](repeating:0,count:w*h*4)
    guard let ctx=CGContext(data:&bytes,width:w,height:h,bitsPerComponent:8,bytesPerRow:w*4,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue) else{return ["verified":false]}
    ctx.draw(image,in:CGRect(x:0,y:0,width:w,height:h))
    var xs=[Int](),ys=[Int]()
    for y in 0..<h {for x in 0..<w {let i=(y*w+x)*4;if bytes[i]>210 && bytes[i+1]>180 && bytes[i+2]<180 {xs.append(x);ys.append(y)}}}
    let foreground=Set(zip(xs,ys).map{$0+$1*w});var visited=Set<Int>(),largest=[Int]()
    for start in foreground where !visited.contains(start) {
        var queue=[start],cursor=0;visited.insert(start)
        while cursor<queue.count {
            let p=queue[cursor];cursor+=1;let x=p%w,y=p/w
            for (a,b) in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)] where a>=0 && a<w && b>=0 && b<h {
                let q=b*w+a;if foreground.contains(q) && !visited.contains(q){visited.insert(q);queue.append(q)}
            }
        }
        if queue.count>largest.count{largest=queue}
    }
    xs=largest.map{$0%w};ys=largest.map{$0/w}
    guard xs.count>200,let x0=xs.min(),let x1=xs.max(),let y0=ys.min(),let y1=ys.max(),y1-y0>15 else{return ["verified":false]}
    let bw=x1-x0+1,bh=y1-y0+1;var rows=[Double](repeating:0,count:bh)
    for y in ys {rows[y-y0]+=1}
    let n=max(1,bh/6),top=rows.prefix(n).reduce(0,+)/Double(n),bottom=rows.suffix(n).reduce(0,+)/Double(n)
    let mean=rows.reduce(0,+)/Double(bh),mid=Double(bh-1)/2
    var cov=0.0,vy=0.0,vw=0.0
    for (i,width) in rows.enumerated(){let a=Double(i)-mid,b=width-mean;cov+=a*b;vy+=a*a;vw+=b*b}
    let r2=vy*vw>0 ? cov*cov/(vy*vw):0,fill=Double(xs.count)/Double(bw*bh)
    return ["verified":cov<0 && r2>0.7 && top>bottom*1.7 && fill>0.35 && fill<0.8,"row_r2":r2,"fill":fill,"width":bw,"height":bh]
}
func analyze(_ image: CGImage, _ regions:[String:[Double]]) throws -> [String:Any] {
    var out=[String:Any]()
    let scale=min(1.0,1600.0/Double(image.width))
    let width=Int(Double(image.width)*scale),height=Int(Double(image.height)*scale)
    guard let ctx=CGContext(data:nil,width:width,height:height,bitsPerComponent:8,bytesPerRow:0,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue) else {throw Fault.invalid("ocr_context")}
    ctx.setFillColor(NSColor.black.cgColor);ctx.fill(CGRect(x:0,y:0,width:width,height:height))
    for (name,box) in regions {
        let cut=try crop(image,box)
        if !["hand","raised","table","indicator","effect","draw_prompt"].contains(name) {
            ctx.draw(cut,in:CGRect(x:box[0]*Double(width),y:(1-box[1]-box[3])*Double(height),width:box[2]*Double(width),height:box[3]*Double(height)))
        }
        out[name] = ["text":[[String:Any]](),"numbers":[[String:Any]](),"feature":try feature(cut)]
    }
    guard let masked=ctx.makeImage() else {throw Fault.invalid("ocr_image")}
    let r=VNRecognizeTextRequest();r.recognitionLevel = .accurate;r.usesLanguageCorrection = false;r.minimumTextHeight=0.006
    try VNImageRequestHandler(cgImage:masked,options:[:]).perform([r])
    let regex=try NSRegularExpression(pattern:"(?<![0-9])[0-9]+(?![0-9])")
    for ob in r.results ?? [] {
        guard let c=ob.topCandidates(1).first else {continue}
        let b=ob.boundingBox;let cx=Double(b.midX),cy=Double(1-b.midY)
        for (name,box) in regions where cx>=box[0] && cx<=box[0]+box[2] && cy>=box[1] && cy<=box[1]+box[3] {
            var item=out[name] as! [String:Any];var texts=item["text"] as! [[String:Any]]
            texts.append(["value":c.string,"confidence":Double(c.confidence),"box":[Double(b.minX),Double(1-b.maxY),Double(b.width),Double(b.height)]])
            var numbers=item["numbers"] as! [[String:Any]]
            for match in regex.matches(in:c.string,range:NSRange(c.string.startIndex...,in:c.string)) {
                if let range=Range(match.range,in:c.string),let tokenBox=try? c.boundingBox(for:range),let rank=Int(c.string[range]) {
                    let n=tokenBox.boundingBox
                    numbers.append(["rank":rank,"box":[Double(n.minX),Double(1-n.maxY),Double(n.width),Double(n.height)],"confidence":Double(c.confidence)])
                }
            }
            item["text"]=texts;item["numbers"]=numbers;out[name]=item
        }
    }
    if let roi=regions["effect"] {
        let request=VNRecognizeTextRequest();request.recognitionLevel = .accurate;request.usesLanguageCorrection=false
        try VNImageRequestHandler(cgImage:crop(image,roi),options:[:]).perform([request])
        var item=out["effect"] as! [String:Any]
        item["text"]=(request.results ?? []).compactMap{ob -> [String:Any]? in
            guard let c=ob.topCandidates(1).first else{return nil}
            return ["value":c.string,"confidence":Double(c.confidence)]
        };out["effect"]=item
    }
    if let roi=regions["indicator"] {
        var item=out["indicator"] as! [String:Any];item["shape_evidence"]=iconShape(try crop(image,roi));out["indicator"]=item
    }
    if let roi=regions["draw_prompt"] {out["draw_prompt"]=drawPrompt(try crop(image,roi))}
    for name in ["pick_cross","pick_triangle","pick_star"] {
        if let roi=regions[name] {out[name]=iconShape(try crop(image,roi))}
    }
    // Calibration-only card candidates. Positions and shape thresholds must pass real-image replay before formal use.
    for name in ["hand","table","raised"] {
        guard var item=out[name] as? [String:Any],let roi=regions[name] else {continue}
        let templated=try templateNumbers(image,roi)
        // Calibration uses the visible digit template bank. No duplicate OCR
        // pass and no guessed OCR fallback when the template rejects a glyph.
        item["numbers"]=templated;item["number_group_count"]=templated.count;item["text"]=[[String:Any]]()
        let numbers=item["numbers"] as? [[String:Any]] ?? []
        var cards=[[String:Any]]()
        for n in numbers {
            guard let rank=n["rank"] as? Int, (1...14).contains(rank) || rank==20,let b=n["box"] as? [Double],let region=regions[name],b[1]<region[1]+region[3]*0.45 else {continue}
            // Card symbols sit below the rank; use a card-body ROI rather than
            // the tiny rank glyph. Hand cards overlap, so the body width is
            // capped to one slot; table cards get a wider visible body.
            // Hand symbols are wider than the rank glyph and sit in a
            // relatively shallow band below it.  The old narrow/tall ROI
            // frequently clipped triangles (classifying them as star or
            // unknown); use a calibrated body band that also works for the
            // overlapping hand-card layout.
            let bodyWidth = name == "table" ? 0.055 : 0.060
            let bodyHeight = name == "table" ? 0.12 : 0.075
            let bodyOffset = name == "table" ? 1.8 : 2.0
            let box=[b[0]+0.020,b[1]+b[3]*bodyOffset,bodyWidth,bodyHeight]
            guard let cut=try? crop(image,box) else {continue}
            var shape=iconShape(cut)
            if rank==20 {
                shape=["shape":"wild","method":"rank20_observed"]
            } else if name == "hand" || name == "table" || name == "raised" {
                // The small shape glyph under each rank remains visible even
                // when adjacent hand cards overlap. Vote over a short range of
                // horizontal offsets; the modal label is more reliable than
                // a single clipped body crop.
                var votes=[String:Int]()
                let hp=b[3]*Double(image.height)/Double(image.width)
                for dx in [-0.15,-0.10,-0.05] {
                    let marker=[b[0]+dx*hp,b[1]+b[3]*1.02,hp*0.95,b[3]*0.90]
                    if let m=try? iconShape(crop(image,marker)),let label=m["shape"] as? String,
                       ["circle","square","triangle","star","cross"].contains(label) {
                        votes[label,default:0] += 1
                    }
                }
                if let best=votes.max(by:{a,b in a.value==b.value ? a.key>b.key : a.value<b.value}),best.value>=3 {
                    shape["shape"]=best.key;shape["marker_votes"]=votes
                    shape["marker_consistent"]=votes.count==1
                } else {
                    shape["shape"]="unknown";shape["marker_votes"]=votes
                }
            }
            var card=n;card["rank_score"]=n["confidence"];card["confidence"]=0.0;card["shape_score"]=NSNull();card["shape"]=shape["shape"];card["shape_evidence"]=shape
            card["point"]=[b[0]+0.013,min(b[1]+0.1,0.98)]
            cards.append(card)
        }
        item["cards"]=cards.sorted{(($0["box"] as! [Double])[0]) < (($1["box"] as! [Double])[0])};out[name]=item
    }
    return out
}
func handle(_ q:[String:Any]) throws -> [String:Any] {
    // Deliver activation notifications in this persistent command-line process.
    RunLoop.current.run(until:Date(timeIntervalSinceNow:0.01))
    let op=q["op"] as? String ?? "status"
    if op == "status" {
        var result:[String:Any] = ["input_enabled":inputEnabled,"windows":windows(),
            "foreground_chrome":chromeInFront(),
            "screen_permission":CGPreflightScreenCaptureAccess(),"accessibility_permission":AXIsProcessTrusted()]
        result["focused_window_id"] = focusedChromeWindowID() ?? NSNull()
        return result
    }
    if op == "inspect" {
        guard let pid=q["pid"] as? Int,windows().contains(where:{($0["pid"] as? Int)==pid}) else {throw Fault.invalid("pid_not_visible_chrome")}
        let app=AXUIElementCreateApplication(pid_t(pid))
        let focused=axValue(app,kAXFocusedWindowAttribute)
        let wins:[AXUIElement]
        if let id=q["window_id"] as? Int {wins=exactAXWindow(pid,id).map{[$0]} ?? []}
        else {wins=focused.map { [$0 as! AXUIElement] } ?? []}
        guard let raw=wins.compactMap({visibleURL($0)}).first,let url=URLComponents(string:raw) else {throw Fault.invalid("visible_url_unavailable")}
        return ["origin":(url.scheme ?? "")+"://"+(url.host ?? ""),"path":url.path,
                "content_bounds":wins.compactMap({webBounds($0)}).first as Any? ?? NSNull(),
                "standalone":url.queryItems?.contains(where:{$0.name=="ux_mode" && $0.value=="standalone"}) ?? false,
                "foreground":frontPID()==pid_t(pid),
                "foreground_app_bundle":frontPID().flatMap{NSRunningApplication(processIdentifier:$0)?.bundleIdentifier} as Any? ?? NSNull(),
                "window_focused":(q["window_id"] as? Int).map{$0 == focusedChromeWindowID()} ?? false]
    }
    if op == "focus_test_window" {
        guard inputEnabled,let pid=q["pid"] as? Int,
          windows().contains(where:{($0["pid"] as? Int)==pid}),
          let id=q["window_id"] as? Int,let win=exactAXWindow(pid,id),
          let raw=visibleURL(win),let url=URLComponents(string:raw),
          url.scheme=="https",url.host=="test-h5.wajetan.com",["","/","/game/6001-whot"].contains(url.path),
          let app=NSRunningApplication(processIdentifier:pid_t(pid)),app.bundleIdentifier=="com.google.Chrome"
        else {throw Fault.invalid("focus_scope_denied")}
        let activated=app.activate(options:[])
        AXUIElementPerformAction(win,kAXRaiseAction as CFString)
        AXUIElementSetAttributeValue(AXUIElementCreateApplication(pid_t(pid)),kAXFocusedWindowAttribute as CFString,win)
        let deadline=Date(timeIntervalSinceNow:0.3)
        while Date() < deadline && focusedChromeWindowID() != id {RunLoop.current.run(until:Date(timeIntervalSinceNow:0.01))}
        guard focusedChromeWindowID() == id else {throw Fault.invalid("focus_not_confirmed")}
        return ["activation_requested":activated,"foreground_confirmed":true]
    }
    if op == "calibration_window_size" {
        guard inputEnabled,let pid=q["pid"] as? Int,let id=q["window_id"] as? Int,
              let win=exactAXWindow(pid,id),let raw=visibleURL(win),let url=URLComponents(string:raw),
              url.scheme=="https",url.host=="test-h5.wajetan.com",url.path=="/game/6001-whot",
              let old=axBounds(win),let content=webBounds(win),abs((old["Width"] ?? 0)-1470)<1 else{throw Fault.invalid("resize_scope_denied")}
        let outerHeight=865+(old["Height"] ?? 0)-content[3]
        guard outerHeight>=865 && outerHeight<=1100 else{throw Fault.invalid("resize_geometry_invalid")}
        var size=CGSize(width:1470,height:outerHeight)
        guard let value=AXValueCreate(.cgSize,&size),AXUIElementSetAttributeValue(win,kAXSizeAttribute as CFString,value) == .success else{throw Fault.invalid("resize_failed")}
        RunLoop.current.run(until:Date(timeIntervalSinceNow:0.1))
        return ["old_bounds":old,"requested_height":outerHeight,"new_bounds":axBounds(win) as Any? ?? NSNull(),"content_bounds":webBounds(win) as Any? ?? NSNull()]
    }
    if op == "analyze" {
        guard let p=q["path"] as? String else {throw Fault.invalid("path_missing")}
        let i=try readImage(p)
        return ["regions":try analyze(i,q["regions"] as? [String:[Double]] ?? [:]),"width":i.width,"height":i.height]
    }
    if op == "compare_replay" {
        guard let a=q["before"] as? String,let b=q["after"] as? String else{throw Fault.invalid("replay_paths_missing")}
        let regions=q["regions"] as? [String:[Double]] ?? [:]
        return ["same_semantic":sameSemantic(try analyze(readImage(a),regions),try analyze(readImage(b),regions))]
    }
    if op == "glyphs" {
        guard let path=q["path"] as? String,let roi=q["crop"] as? [Double] else {throw Fault.invalid("glyph_input")}
        return ["glyphs":try glyphs(crop(readImage(path),roi))]
    }
    if op == "shape" {
        guard let path=q["path"] as? String,let roi=q["crop"] as? [Double],roi.count==4 else {throw Fault.invalid("shape_input")}
        return try iconShape(crop(readImage(path),roi))
    }
    guard let id=q["window_id"] as? Int, let w=windows().first(where:{($0["id"] as? Int)==id}), let b=w["bounds"] as? [String:Double], let expected=q["bounds"] as? [String:Double],b==expected else {throw Fault.invalid("window_changed")}
    if op == "validate_frame" {return ["verified":true,"fresh_frame_age_ms":try verifyWitness(q,id,b)]}
    if op == "type_text" || op == "press_return" {
        guard chromeInFront(),focusedChromeWindowID()==id,inputEnabled,
              let pid=w["pid"] as? Int,frontPID()==pid_t(pid),
              let expectedOrigin=q["expected_origin"] as? String,
              let expectedURL=URLComponents(string:expectedOrigin),
              let expectedPath=q["expected_path"] as? String,
              let appWindow=axValue(AXUIElementCreateApplication(pid_t(pid)),kAXFocusedWindowAttribute),
              let raw=visibleURL(appWindow as! AXUIElement),let url=URLComponents(string:raw),
              url.scheme==expectedURL.scheme,url.host==expectedURL.host,url.port==expectedURL.port,url.path==expectedPath,
              !(url.queryItems?.contains(where:{$0.name=="ux_mode" && $0.value=="standalone"}) ?? false),
              AXIsProcessTrusted() else {throw Fault.invalid("text_input_surface_not_verified")}
        let src=CGEventSource(stateID:.hidSystemState)
        if op == "press_return" {
            guard let down=CGEvent(keyboardEventSource:src,virtualKey:36,keyDown:true),let up=CGEvent(keyboardEventSource:src,virtualKey:36,keyDown:false) else {throw Fault.invalid("return_key_failed")}
            down.post(tap:.cghidEventTap);Thread.sleep(forTimeInterval:0.02);up.post(tap:.cghidEventTap)
            return ["typed":true,"key":"Return"]
        }
        guard let text=q["text"] as? String else {throw Fault.invalid("text_missing")}
        for scalar in text {
            let units=Array(String(scalar).utf16)
            guard let down=CGEvent(keyboardEventSource:src,virtualKey:0,keyDown:true),let up=CGEvent(keyboardEventSource:src,virtualKey:0,keyDown:false) else {throw Fault.invalid("text_key_failed")}
            units.withUnsafeBufferPointer {ptr in
                down.keyboardSetUnicodeString(stringLength:ptr.count,unicodeString:ptr.baseAddress)
                up.keyboardSetUnicodeString(stringLength:ptr.count,unicodeString:ptr.baseAddress)
            }
            down.post(tap:.cghidEventTap);Thread.sleep(forTimeInterval:0.012);up.post(tap:.cghidEventTap)
        }
        return ["typed":true,"text_length":text.count]
    }
    if op == "click_recovery" {
        guard chromeInFront(),focusedChromeWindowID()==id,inputEnabled,
              let pid=w["pid"] as? Int,frontPID()==pid_t(pid),
              let expectedOrigin=q["expected_origin"] as? String,
              let expectedURL=URLComponents(string:expectedOrigin),
              let expectedPath=q["expected_path"] as? String,
              let appWindow=axValue(AXUIElementCreateApplication(pid_t(pid)),kAXFocusedWindowAttribute),
              let raw=visibleURL(appWindow as! AXUIElement),let url=URLComponents(string:raw),
              url.scheme==expectedURL.scheme,url.host==expectedURL.host,url.port==expectedURL.port,url.path==expectedPath,
              !(url.queryItems?.contains(where:{$0.name=="ux_mode" && $0.value=="standalone"}) ?? false),
              AXIsProcessTrusted(),let xy=q["point"] as? [Double],xy.count==2,xy.allSatisfy({$0.isFinite}),
              let roi=q["canvas_screen"] as? [Double],roi.count==4 else {throw Fault.invalid("recovery_click_surface_not_verified")}
        guard xy[0]>=roi[0],xy[0]<=roi[0]+roi[2],xy[1]>=roi[1],xy[1]<=roi[1]+roi[3],roi[0]>=b["X"]!,roi[1]>=b["Y"]!,roi[0]+roi[2]<=b["X"]!+b["Width"]!,roi[1]+roi[3]<=b["Y"]!+b["Height"]! else {throw Fault.invalid("recovery_click_outside_canvas")}
        let clickedAt=Double(DispatchTime.now().uptimeNanoseconds)/1e6;let p=CGPoint(x:xy[0],y:xy[1]);let src=CGEventSource(stateID:.hidSystemState)
        CGEvent(mouseEventSource:src,mouseType:.mouseMoved,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cghidEventTap)
        CGEvent(mouseEventSource:src,mouseType:.leftMouseDown,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cghidEventTap);Thread.sleep(forTimeInterval:0.035)
        CGEvent(mouseEventSource:src,mouseType:.leftMouseUp,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cghidEventTap)
        return ["clicked":true,"acknowledged":false,"clicked_at_ms":clickedAt,"recovery_mode":true]
    }
    if op == "click" {
        guard chromeInFront() else {throw Fault.invalid("chrome_not_foreground")}
        guard focusedChromeWindowID()==id else {throw Fault.invalid("focused_window_changed")}
        guard inputEnabled else {throw Fault.invalid("input_capability_denied")}
        guard let pid=w["pid"] as? Int,frontPID()==pid_t(pid),
              let expectedOrigin=q["expected_origin"] as? String,
              let expectedURL=URLComponents(string:expectedOrigin),
              let expectedPath=q["expected_path"] as? String,
              let appWindow=axValue(AXUIElementCreateApplication(pid_t(pid)),kAXFocusedWindowAttribute),
              let raw=visibleURL(appWindow as! AXUIElement),let url=URLComponents(string:raw),
              url.scheme==expectedURL.scheme,url.host==expectedURL.host,url.port==expectedURL.port,
              url.path==expectedPath,
              !(url.queryItems?.contains(where:{$0.name=="ux_mode" && $0.value=="standalone"}) ?? false)
        else {throw Fault.invalid("click_surface_not_verified")}
        guard AXIsProcessTrusted(), let xy=q["point"] as? [Double],xy.count==2,xy.allSatisfy({$0.isFinite}),let roi=q["canvas_screen"] as? [Double],roi.count==4 else {throw Fault.invalid("click_configuration")}
        guard xy[0]>=roi[0],xy[0]<=roi[0]+roi[2],xy[1]>=roi[1],xy[1]<=roi[1]+roi[3],roi[0]>=b["X"]!,roi[1]>=b["Y"]!,roi[0]+roi[2]<=b["X"]!+b["Width"]!,roi[1]+roi[3]<=b["Y"]!+b["Height"]! else {throw Fault.invalid("click_outside_canvas")}
        let verifiedAge=try verifyWitness(q,id,b)
        let clickedAt=Double(DispatchTime.now().uptimeNanoseconds)/1e6
        let p=CGPoint(x:xy[0],y:xy[1]);let src=CGEventSource(stateID:.hidSystemState)
        CGEvent(mouseEventSource:src,mouseType:.mouseMoved,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cghidEventTap)
        CGEvent(mouseEventSource:src,mouseType:.leftMouseDown,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cghidEventTap)
        Thread.sleep(forTimeInterval:0.035)
        CGEvent(mouseEventSource:src,mouseType:.leftMouseUp,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cghidEventTap)
        return ["clicked":true,"acknowledged":false,"fresh_frame_age_ms":verifiedAge,"clicked_at_ms":clickedAt]
    }
    guard op == "capture", q["allow_background_capture"] as? Bool == true,
          CGPreflightScreenCaptureAccess(), let roi=q["crop"] as? [Double] else {throw Fault.invalid("capture_not_ready")}
    let sampled=try captureStream.frame(windowID:UInt32(id))
    guard let rect=q["screen_rect"] as? [Double],rect.count==4,b["Width"]!>0,b["Height"]!>0 else {throw Fault.invalid("capture_rect_missing")}
    let relative=[(rect[0]-b["X"]!)/b["Width"]!, (rect[1]-b["Y"]!)/b["Height"]!,rect[2]/b["Width"]!,rect[3]/b["Height"]!]
    let i=try crop(crop(sampled.0,relative),roi)
    let at=DispatchTime.now().uptimeNanoseconds
    let analysisRegions=q["regions"] as? [String:[Double]] ?? [:]
    let analyzed=try analyze(i,analysisRegions)
    let titleWords=normalizedText(analyzed["title"] as? [String:Any] ?? [:],digits:false).joined()
    let isTerminal=titleWords.contains("VICTORY") || titleWords.contains("LOSE") || titleWords.contains("DEFEAT")
    let liveCards=((analyzed["hand"] as? [String:Any])?["cards"] as? [[String:Any]] ?? []).count>0
    if let prefix=q["save_prefix"] as? String {
        let base="/Users/robin/Documents/wajetan_analyst/analysis/whot_test_experience_2026_09_07/v3_1/captures/"
        guard prefix.hasPrefix(base),!prefix.contains("..") else {throw Fault.invalid("capture_path_not_allowed")}
        let regionMap=q["regions"] as? [String:[Double]] ?? [:]
        // Save each explicitly selected ROI separately; whole account/name regions are excluded by the caller's profile.
        let saveNames=q["save_regions"] as? [String] ?? Array(regionMap.keys)
        for (name,box) in regionMap where saveNames.contains(name) {
            // Wide effect/picker crops overlap player-name columns at settlement.
            if ["effect","picker"].contains(name) && (isTerminal || !liveCards) {continue}
            guard name.range(of:"^[a-z0-9_]+$",options:.regularExpression) != nil else {throw Fault.invalid("invalid_region_name")}
            let dest=prefix+"-"+name+".png"
            try FileManager.default.createDirectory(at:URL(fileURLWithPath:dest).deletingLastPathComponent(),withIntermediateDirectories:true)
            guard !FileManager.default.fileExists(atPath:dest) else {throw Fault.invalid("capture_would_overwrite")}
            try writeImage(crop(i,box),dest)
        }
    }
    let checked=(q["regions"] as? [String:[Double]] ?? [:]).filter{["hand","raised","table","turn","effect","bet","draw_prompt","pick_cross","pick_triangle","pick_star"].contains($0.key)}
    var hashes=[String:String]()
    for (name,box) in checked {hashes[name]=try pixelHash(crop(i,box))}
    witness=Witness(windowID:id,seq:sampled.2,at:at,rect:rect,regions:checked,hashes:hashes,analysisRegions:analysisRegions,semantics:analyzed)
    // Only calibrated regions reach OCR; no account chrome or whole-window output is retained.
    return ["regions":analyzed,"width":i.width,"height":i.height,"frame_age_ms":sampled.1,"capture_seq":sampled.2]
}
while let line=readLine() {
    let start=DispatchTime.now().uptimeNanoseconds
    var result:[String:Any]
    do {
        guard let data=line.data(using:.utf8),let q=try JSONSerialization.jsonObject(with:data) as? [String:Any] else {throw Fault.invalid("invalid_json")}
        result=try handle(q);result["status"]="ok";result["request_id"]=q["request_id"]
    } catch {result=["status":"error","reason":String(describing:error)]}
    result["native_ms"]=Double(DispatchTime.now().uptimeNanoseconds-start)/1e6
    let data=try! JSONSerialization.data(withJSONObject:result,options:[.sortedKeys])
    FileHandle.standardOutput.write(data);FileHandle.standardOutput.write(Data([10]))
}
