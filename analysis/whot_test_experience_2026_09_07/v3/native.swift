// Persistent local JSONL worker. Uses visible window pixels, never browser internals.
import Foundation
import AppKit
import Vision
import ImageIO
import UniformTypeIdentifiers

enum Fault: Error { case invalid(String) }
let digitBankPath="/Users/robin/Documents/wajetan_analyst/analysis/whot_test_experience_2026_09_07/v3/visual_assets/card_digits.json"
var digitBankCache:[String:[[Double]]]?=nil
func glyphs(_ image:CGImage)throws->[[String:Any]] {
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
    return blobs.filter{Double($0.3)>=Double(maxH)*0.65}.sorted{$0.0<$1.0}.map { x,y,bw,bh,cells in
        let set=Set(cells);var signature=[Double]()
        for yy in 0..<28 {for xx in 0..<20 {let sx=x+min(bw-1,Int((Double(xx)+0.5)*Double(bw)/20));let sy=y+min(bh-1,Int((Double(yy)+0.5)*Double(bh)/28));signature.append(set.contains(sy*w+sx) ? 1:0)}}
        return ["box":[Double(x),Double(y),Double(bw),Double(bh)],"signature":signature]
    }
}
func templateNumbers(_ image:CGImage,_ roi:[Double])throws->[[String:Any]] {
    if digitBankCache==nil,let data=try? Data(contentsOf:URL(fileURLWithPath:digitBankPath)){digitBankCache=try? JSONSerialization.jsonObject(with:data) as? [String:[[Double]]]}
    guard let bank=digitBankCache else {return []}
    let band=[roi[0],roi[1],roi[2],roi[3]*0.24];let cut=try crop(image,band)
    let pieces=try glyphs(cut);var out=[[String:Any]]();var group=[(String,[Double],Double)]()
    func flush(){
        guard !group.isEmpty else{return}
        let text=group.map{$0.0}.joined();let first=group.first!.1,last=group.last!.1
        if let rank=Int(text), (1...14).contains(rank) || rank==20 {
            out.append(["rank":rank,"box":[band[0]+first[0]/Double(image.width),band[1]+first[1]/Double(image.height),(last[0]+last[2]-first[0])/Double(image.width),first[3]/Double(image.height)],"confidence":group.map{$0.2}.min()!,"method":"visible_glyph_template"])
        }
        group=[]
    }
    for piece in pieces {
        let b=piece["box"] as! [Double],sig=piece["signature"] as! [Double]
        let scores=bank.map{ label,refs -> (String,Double) in
            let distances=refs.filter{$0.count==sig.count}.map{ ref in zip(ref,sig).map{abs($0-$1)}.reduce(0,+)/Double(sig.count)}
            return (label,distances.min() ?? 1)
        }.sorted{$0.1<$1.1}
        guard scores.count>1,scores[0].1<0.18,scores[1].1-scores[0].1>0.025 else {flush();continue}
        if let last=group.last, b[0]-(last.1[0]+last.1[2])>min(b[3],last.1[3])*0.7 {flush()}
        group.append((scores[0].0,b,1-scores[0].1/10))
    }
    flush();return out
}
func axValue(_ e: AXUIElement, _ key: String) -> CFTypeRef? {
    var value:CFTypeRef?;return AXUIElementCopyAttributeValue(e,key as CFString,&value) == .success ? value:nil
}
func visibleURL(_ element:AXUIElement, _ depth:Int=0) -> String? {
    if depth>18{return nil}
    if let url=axValue(element,"AXURL") as? URL,url.scheme=="https" {return url.absoluteString}
    if let url=axValue(element,"AXURL") as? String,url.hasPrefix("https://") {return url}
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
    let crossLike = rowCenter > Double(bw)*0.72 && colCenter > Double(bh)*0.72 && rowEdge < Double(bw)*0.46 && colEdge < Double(bh)*0.46
    var name="unknown"
    if fill>0.92 {name="square"}
    else if (fill>=0.32 && fill<0.52 && centerFill>0.25) || crossLike {name="cross"}
    else if triangleLike {name="triangle"}
    else if fill>0.68 && fill<=0.96 {name="circle"}
    else if fill>0.43 && fill<0.63 {name=centerFill>0.86 ? "cross":"triangle"}
    else if fill>0.15 && fill<0.4 {name="star"}
    return ["shape":name,"fill":fill,"center_fill":centerFill,"row_r2":rowR2,
            "bbox_w":bw,"bbox_h":bh,
            "top_width":topWidth,"bottom_width":bottomWidth,"row_center":rowCenter,
            "row_edge":rowEdge,"col_center":colCenter,"col_edge":colEdge,
            "row_profile":rowWidths,"col_profile":colWidths,
            "method":"geometry_unverified"]
}
func analyze(_ image: CGImage, _ regions:[String:[Double]]) throws -> [String:Any] {
    var out=[String:Any]()
    let scale=min(1.0,1600.0/Double(image.width))
    let width=Int(Double(image.width)*scale),height=Int(Double(image.height)*scale)
    guard let ctx=CGContext(data:nil,width:width,height:height,bitsPerComponent:8,bytesPerRow:0,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue) else {throw Fault.invalid("ocr_context")}
    ctx.setFillColor(NSColor.black.cgColor);ctx.fill(CGRect(x:0,y:0,width:width,height:height))
    for (name,box) in regions {
        let cut=try crop(image,box)
        ctx.draw(cut,in:CGRect(x:box[0]*Double(width),y:(1-box[1]-box[3])*Double(height),width:box[2]*Double(width),height:box[3]*Double(height)))
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
    // Calibration-only card candidates. Positions and shape thresholds must pass real-image replay before formal use.
    for name in ["hand","table"] {
        guard var item=out[name] as? [String:Any],let roi=regions[name] else {continue}
        let cardRequest=VNRecognizeTextRequest();cardRequest.recognitionLevel = .accurate
        cardRequest.usesLanguageCorrection=false;cardRequest.minimumTextHeight=0.005
        cardRequest.customWords=(1...14).map{String($0)}+["20"]
        try VNImageRequestHandler(cgImage:crop(image,roi),options:[:]).perform([cardRequest])
        var directNumbers=[[String:Any]](),directTexts=[[String:Any]]()
        for ob in cardRequest.results ?? [] {
            guard let c=ob.topCandidates(1).first else {continue}
            directTexts.append(["value":c.string,"confidence":Double(c.confidence)])
            for match in regex.matches(in:c.string,range:NSRange(c.string.startIndex...,in:c.string)) {
                if let range=Range(match.range,in:c.string),let tokenBox=try? c.boundingBox(for:range),let rank=Int(c.string[range]) {
                    let n=tokenBox.boundingBox
                    directNumbers.append(["rank":rank,"box":[roi[0]+Double(n.minX)*roi[2],roi[1]+Double(1-n.maxY)*roi[3],Double(n.width)*roi[2],Double(n.height)*roi[3]],"confidence":Double(c.confidence)])
                }
            }
        }
        item["numbers"]=directNumbers;item["text"]=directTexts
        let templated=try templateNumbers(image,roi)
        if !templated.isEmpty {item["numbers"]=templated}
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
            } else if name == "hand" {
                // The small shape glyph under each rank remains visible even
                // when adjacent hand cards overlap. Vote over a short range of
                // horizontal offsets; the modal label is more reliable than
                // a single clipped body crop.
                var votes=[String:Int]();let markerY=b[1]+0.027
                for dx in stride(from:-0.040,through:-0.010,by:0.005) {
                    let marker=[b[0]+dx,markerY,0.045,0.030]
                    if let m=try? iconShape(crop(image,marker)),let label=m["shape"] as? String,
                       ["circle","square","triangle","star","cross"].contains(label) {
                        votes[label,default:0] += 1
                    }
                }
                if let best=votes.max(by:{a,b in a.value==b.value ? a.key>b.key : a.value<b.value}),best.value>=3 {
                    shape["shape"]=best.key;shape["marker_votes"]=votes
                }
            }
            var card=n;card["shape"]=shape["shape"];card["shape_evidence"]=shape
            card["point"]=[b[0]+0.013,min(b[1]+0.1,0.98)]
            cards.append(card)
        }
        item["cards"]=cards.sorted{(($0["box"] as! [Double])[0]) < (($1["box"] as! [Double])[0])};out[name]=item
    }
    return out
}
func handle(_ q:[String:Any]) throws -> [String:Any] {
    let op=q["op"] as? String ?? "status"
    if op == "status" { return ["windows":windows(),"foreground_chrome":NSWorkspace.shared.frontmostApplication?.bundleIdentifier == "com.google.Chrome", "screen_permission":CGPreflightScreenCaptureAccess(),"accessibility_permission":AXIsProcessTrusted()] }
    // Bring a visible Chrome process to the foreground without navigating or
    // changing any tab.  Tab selection is still performed by the browser UI
    // and is verified by a subsequent inspect call.
    if op == "activate_process" {
        guard let pid=q["pid"] as? Int,windows().contains(where:{($0["pid"] as? Int)==pid}) else {throw Fault.invalid("pid_not_visible_chrome")}
        guard NSRunningApplication(processIdentifier:pid_t(pid))?.activate(options:[.activateAllWindows,.activateIgnoringOtherApps]) == true else {throw Fault.invalid("activate_failed")}
        return ["activated":true,"pid":pid]
    }
    // Select an already-open tab through Chrome's tab strip. This deliberately
    // accepts only a point in the top chrome strip (never the page/canvas),
    // activates the existing process and posts one click atomically.
    if op == "tab_click" {
        guard let pid=q["pid"] as? Int,
              let id=q["window_id"] as? Int,
              let w=windows().first(where:{($0["id"] as? Int)==id}),
              let b=w["bounds"] as? [String:Double],
              let xy=q["point"] as? [Double],xy.count==2,xy.allSatisfy({$0.isFinite}) else {throw Fault.invalid("tab_click_configuration")}
        guard xy[0]>=b["X"]!,xy[0]<=b["X"]!+b["Width"]!,xy[1]>=b["Y"]!,xy[1]<=b["Y"]!+92 else {throw Fault.invalid("tab_click_outside_chrome_strip")}
        guard NSRunningApplication(processIdentifier:pid_t(pid))?.activate(options:[.activateAllWindows,.activateIgnoringOtherApps]) == true else {throw Fault.invalid("activate_failed")}
        Thread.sleep(forTimeInterval:0.12)
        let p=CGPoint(x:xy[0],y:xy[1]);let src=CGEventSource(stateID:.hidSystemState)
        CGEvent(mouseEventSource:src,mouseType:.mouseMoved,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cghidEventTap)
        CGEvent(mouseEventSource:src,mouseType:.leftMouseDown,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cghidEventTap)
        Thread.sleep(forTimeInterval:0.035)
        CGEvent(mouseEventSource:src,mouseType:.leftMouseUp,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cghidEventTap)
        return ["clicked":true,"point":xy,"window_id":id]
    }
    // Atomic foreground + page click for a verified existing test page. The
    // caller supplies the current window bounds and an explicit content ROI;
    // this keeps a focus change from racing the click while still preventing
    // clicks in the browser chrome or outside the page.
    if op == "page_click" {
        guard let pid=q["pid"] as? Int,
              let id=q["window_id"] as? Int,
              let w=windows().first(where:{($0["id"] as? Int)==id}),
              let b=w["bounds"] as? [String:Double],
              let xy=q["point"] as? [Double],xy.count==2,xy.allSatisfy({$0.isFinite}),
              let roi=q["content_screen"] as? [Double],roi.count==4,roi.allSatisfy({$0.isFinite}) else {throw Fault.invalid("page_click_configuration")}
        guard xy[0]>=roi[0],xy[0]<=roi[0]+roi[2],xy[1]>=roi[1],xy[1]<=roi[1]+roi[3],
              roi[0]>=b["X"]!,roi[1]>=b["Y"]!,roi[0]+roi[2]<=b["X"]!+b["Width"]!,roi[1]+roi[3]<=b["Y"]!+b["Height"]! else {throw Fault.invalid("page_click_outside_content")}
        guard NSRunningApplication(processIdentifier:pid_t(pid))?.activate(options:[.activateAllWindows,.activateIgnoringOtherApps]) == true else {throw Fault.invalid("activate_failed")}
        Thread.sleep(forTimeInterval:0.12)
        let p=CGPoint(x:xy[0],y:xy[1]);let src=CGEventSource(stateID:.hidSystemState)
        CGEvent(mouseEventSource:src,mouseType:.mouseMoved,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cghidEventTap)
        CGEvent(mouseEventSource:src,mouseType:.leftMouseDown,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cghidEventTap)
        Thread.sleep(forTimeInterval:0.035)
        CGEvent(mouseEventSource:src,mouseType:.leftMouseUp,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cghidEventTap)
        return ["clicked":true,"point":xy,"window_id":id]
    }
    if op == "inspect" || op == "activate" {
        guard let pid=q["pid"] as? Int,windows().contains(where:{($0["pid"] as? Int)==pid}) else {throw Fault.invalid("pid_not_visible_chrome")}
        let app=AXUIElementCreateApplication(pid_t(pid))
        let wins=axValue(app,kAXWindowsAttribute) as? [AXUIElement] ?? []
        guard let raw=wins.compactMap({visibleURL($0)}).first,let url=URLComponents(string:raw) else {throw Fault.invalid("visible_url_unavailable")}
        if op == "activate" {
            guard url.scheme=="https",url.host=="test-h5.wajew.com",["/game/6001-whot"].contains(url.path) else {throw Fault.invalid("activate_route_not_verified")}
            NSRunningApplication(processIdentifier:pid_t(pid))?.activate(options:[])
        }
        return ["origin":(url.scheme ?? "")+"://"+(url.host ?? ""),"path":url.path,
                "content_bounds":wins.compactMap({webBounds($0)}).first as Any? ?? NSNull(),
                "standalone":url.queryItems?.contains(where:{$0.name=="ux_mode" && $0.value=="standalone"}) ?? false,
                "foreground":NSWorkspace.shared.frontmostApplication?.processIdentifier==pid_t(pid)]
    }
    if op == "analyze" {
        guard let p=q["path"] as? String else {throw Fault.invalid("path_missing")}
        let i=try readImage(p)
        return ["regions":try analyze(i,q["regions"] as? [String:[Double]] ?? [:]),"width":i.width,"height":i.height]
    }
    if op == "glyphs" {
        guard let path=q["path"] as? String,let roi=q["crop"] as? [Double] else {throw Fault.invalid("glyph_input")}
        return ["glyphs":try glyphs(crop(readImage(path),roi))]
    }
    if op == "shape" {
        guard let path=q["path"] as? String,let roi=q["crop"] as? [Double],roi.count==4 else {throw Fault.invalid("shape_input")}
        return try iconShape(crop(readImage(path),roi))
    }
    guard NSWorkspace.shared.frontmostApplication?.bundleIdentifier == "com.google.Chrome" else {throw Fault.invalid("chrome_not_foreground")}
    guard let id=q["window_id"] as? Int, let w=windows().first(where:{($0["id"] as? Int)==id}), let b=w["bounds"] as? [String:Double], let expected=q["bounds"] as? [String:Double],b==expected else {throw Fault.invalid("window_changed")}
    if op == "click" {
        guard AXIsProcessTrusted(), let xy=q["point"] as? [Double],xy.count==2,xy.allSatisfy({$0.isFinite}),let roi=q["canvas_screen"] as? [Double],roi.count==4 else {throw Fault.invalid("click_configuration")}
        guard xy[0]>=roi[0],xy[0]<=roi[0]+roi[2],xy[1]>=roi[1],xy[1]<=roi[1]+roi[3],roi[0]>=b["X"]!,roi[1]>=b["Y"]!,roi[0]+roi[2]<=b["X"]!+b["Width"]!,roi[1]+roi[3]<=b["Y"]!+b["Height"]! else {throw Fault.invalid("click_outside_canvas")}
        let p=CGPoint(x:xy[0],y:xy[1]);let src=CGEventSource(stateID:.hidSystemState)
        CGEvent(mouseEventSource:src,mouseType:.mouseMoved,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cghidEventTap)
        CGEvent(mouseEventSource:src,mouseType:.leftMouseDown,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cghidEventTap)
        Thread.sleep(forTimeInterval:0.035)
        CGEvent(mouseEventSource:src,mouseType:.leftMouseUp,mouseCursorPosition:p,mouseButton:.left)?.post(tap:.cghidEventTap)
        return ["clicked":true,"acknowledged":false]
    }
    guard op == "capture", CGPreflightScreenCaptureAccess(), let roi=q["crop"] as? [Double] else {throw Fault.invalid("capture_not_ready")}
    let p=FileManager.default.temporaryDirectory.appendingPathComponent("whot-frame-"+UUID().uuidString+".png").path
    defer { try? FileManager.default.removeItem(atPath:p) }
    let task=Process();task.executableURL=URL(fileURLWithPath:"/usr/sbin/screencapture")
    if let rect=q["screen_rect"] as? [Double] {
        guard rect.count==4,rect.allSatisfy({$0.isFinite}),rect[2]>0,rect[3]>0,rect[0]>=b["X"]!,rect[1]>=b["Y"]!,rect[0]+rect[2]<=b["X"]!+b["Width"]!,rect[1]+rect[3]<=b["Y"]!+b["Height"]! else {throw Fault.invalid("capture_outside_window")}
        task.arguments=["-x","-R"+rect.map{String(Int($0))}.joined(separator:","),p]
    } else {task.arguments=["-x","-o","-l",String(id),p]}
    task.standardError=Pipe();try task.run();task.waitUntilExit()
    guard task.terminationStatus==0 else {throw Fault.invalid("capture_failed")}
    let i=try crop(readImage(p),roi)
    if let prefix=q["save_prefix"] as? String {
        let base="/Users/robin/Documents/wajetan_analyst/analysis/whot_test_experience_2026_09_07/v3/captures/"
        guard prefix.hasPrefix(base),!prefix.contains("..") else {throw Fault.invalid("capture_path_not_allowed")}
        let regionMap=q["regions"] as? [String:[Double]] ?? [:]
        // Save each explicitly selected ROI separately; whole account/name regions are excluded by the caller's profile.
        let saveNames=q["save_regions"] as? [String] ?? Array(regionMap.keys)
        for (name,box) in regionMap where saveNames.contains(name) {
            guard name.range(of:"^[a-z0-9_]+$",options:.regularExpression) != nil else {throw Fault.invalid("invalid_region_name")}
            let dest=prefix+"-"+name+".png"
            try FileManager.default.createDirectory(at:URL(fileURLWithPath:dest).deletingLastPathComponent(),withIntermediateDirectories:true)
            guard !FileManager.default.fileExists(atPath:dest) else {throw Fault.invalid("capture_would_overwrite")}
            try writeImage(crop(i,box),dest)
        }
    }
    // Only calibrated regions reach OCR; no account chrome or whole-window output is retained.
    return ["regions":try analyze(i,q["regions"] as? [String:[Double]] ?? [:]),"width":i.width,"height":i.height]
}
while let line=readLine() {
    let start=DispatchTime.now().uptimeNanoseconds
    var result:[String:Any]
    do {
        guard let data=line.data(using:.utf8),let q=try JSONSerialization.jsonObject(with:data) as? [String:Any] else {throw Fault.invalid("invalid_json")}
        result=try handle(q);result["status"]="ok"
    } catch {result=["status":"error","reason":String(describing:error)]}
    result["native_ms"]=Double(DispatchTime.now().uptimeNanoseconds-start)/1e6
    let data=try! JSONSerialization.data(withJSONObject:result,options:[.sortedKeys])
    FileHandle.standardOutput.write(data);FileHandle.standardOutput.write(Data([10]))
}
