import Foundation
import CoreGraphics
import AppKit

// hid: drive the real mouse and keyboard (OS-level events), like a person would. Needs Accessibility permission (already granted to the parent process).
let src = CGEventSource(stateID: .hidSystemState)
func pos() -> CGPoint { return CGEvent(source: nil)!.location }
func post(_ e: CGEvent?) { e?.post(tap: .cghidEventTap) }
func sleepMs(_ ms: Double) { usleep(UInt32(max(0, ms) * 1000)) }
func ease(_ t: Double) -> Double { return t < 0.5 ? 2*t*t : 1 - pow(-2*t + 2, 2) / 2 }

func move(to: CGPoint, ms: Double) {
    let from = pos(); let steps = max(8, Int(ms / 8))
    let dx = to.x - from.x, dy = to.y - from.y
    let dist = hypot(dx, dy); let bow = min(40.0, dist * 0.06) * (Bool.random() ? 1 : -1)   // a slight arc, like a hand
    for i in 1...steps {
        let t = ease(Double(i) / Double(steps))
        let off = sin(t * Double.pi) * bow
        let p = CGPoint(x: from.x + dx * t - dy / max(dist, 1) * off, y: from.y + dy * t + dx / max(dist, 1) * off)
        post(CGEvent(mouseEventSource: src, mouseType: .mouseMoved, mouseCursorPosition: p, mouseButton: .left))
        sleepMs(ms / Double(steps))
    }
    post(CGEvent(mouseEventSource: src, mouseType: .mouseMoved, mouseCursorPosition: to, mouseButton: .left))
}
func click(double: Bool = false, right: Bool = false) {
    let p = pos(); let (d, u, b): (CGEventType, CGEventType, CGMouseButton) = right ? (.rightMouseDown, .rightMouseUp, .right) : (.leftMouseDown, .leftMouseUp, .left)
    for n in 1...(double ? 2 : 1) {
        let down = CGEvent(mouseEventSource: src, mouseType: d, mouseCursorPosition: p, mouseButton: b); down?.setIntegerValueField(.mouseEventClickState, value: Int64(n)); down?.flags = CGEventFlags(rawValue: 0); post(down)
        sleepMs(70 + Double.random(in: 0...40))
        let up = CGEvent(mouseEventSource: src, mouseType: u, mouseCursorPosition: p, mouseButton: b); up?.setIntegerValueField(.mouseEventClickState, value: Int64(n)); up?.flags = CGEventFlags(rawValue: 0); post(up)
        sleepMs(90)
    }
}
func typeText(_ s: String, cps: Double) {
    for ch in s {
        let u = Array(String(ch).utf16)
        let d = CGEvent(keyboardEventSource: src, virtualKey: 0, keyDown: true); d?.keyboardSetUnicodeString(stringLength: u.count, unicodeString: u); d?.flags = CGEventFlags(rawValue: 0); post(d)
        let up = CGEvent(keyboardEventSource: src, virtualKey: 0, keyDown: false); up?.keyboardSetUnicodeString(stringLength: u.count, unicodeString: u); up?.flags = CGEventFlags(rawValue: 0); post(up)
        var wait = 1000.0 / cps * Double.random(in: 0.6...1.5); if ch == " " { wait *= 1.3 }; if ".,?;:".contains(ch) { wait *= 1.8 }
        sleepMs(wait)
    }
}
let codes: [String: CGKeyCode] = ["a":0,"s":1,"d":2,"f":3,"h":4,"g":5,"z":6,"x":7,"c":8,"v":9,"b":11,"q":12,"w":13,"e":14,"r":15,"y":16,"t":17,"1":18,"2":19,"3":20,"4":21,"6":22,"5":23,"=":24,"9":25,"7":26,"-":27,"8":28,"0":29,"]":30,"o":31,"u":32,"[":33,"i":34,"p":35,"return":36,"l":37,"j":38,"'":39,"k":40,";":41,"\\":42,",":43,"/":44,"n":45,"m":46,".":47,"tab":48,"space":49,"`":50,"delete":51,"esc":53,"left":123,"right":124,"down":125,"up":126]
func key(_ combo: String) {
    var flags = CGEventFlags(); var k: CGKeyCode = 0
    for part in combo.lowercased().split(separator: "+").map(String.init) {
        switch part { case "cmd": flags.insert(.maskCommand); case "shift": flags.insert(.maskShift); case "alt", "opt": flags.insert(.maskAlternate); case "ctrl": flags.insert(.maskControl); default: k = codes[part] ?? 0 }
    }
    let d = CGEvent(keyboardEventSource: src, virtualKey: k, keyDown: true); d?.flags = flags; post(d)
    sleepMs(60)
    let u = CGEvent(keyboardEventSource: src, virtualKey: k, keyDown: false); u?.flags = flags; post(u)
    sleepMs(40); resetMods()
}
func resetMods() {
    for kc in [CGKeyCode(55), CGKeyCode(56), CGKeyCode(58), CGKeyCode(59)] {   // cmd, shift, alt, ctrl
        let e = CGEvent(keyboardEventSource: src, virtualKey: kc, keyDown: false); e?.type = .flagsChanged; e?.flags = CGEventFlags(rawValue: 0); post(e); sleepMs(15)
    }
}
func scroll(_ dy: Int32) {
    var left = dy; let step: Int32 = dy > 0 ? 4 : -4
    while abs(left) > 0 { let s = abs(left) < abs(step) ? left : step; post(CGEvent(scrollWheelEvent2Source: src, units: .pixel, wheelCount: 1, wheel1: s, wheel2: 0, wheel3: 0)); left -= s; sleepMs(12) }
}
let a = CommandLine.arguments
switch a.count > 1 ? a[1] : "" {
case "flags": print(String(CGEventSource.flagsState(.combinedSessionState).rawValue, radix: 16))
case "reset": resetMods(); print(String(CGEventSource.flagsState(.combinedSessionState).rawValue, radix: 16))
case "pos": let p = pos(); print("\(Int(p.x)) \(Int(p.y))")
case "move": move(to: CGPoint(x: Double(a[2])!, y: Double(a[3])!), ms: a.count > 4 ? Double(a[4])! : 600)
case "click": click(double: a.count > 2 && a[2] == "double", right: a.count > 2 && a[2] == "right")
case "type": typeText(a[2], cps: a.count > 3 ? Double(a[3])! : 11)
case "key": key(a[2])
case "scroll": scroll(Int32(a[2])!)
default: print("usage: hid pos | move x y [ms] | click [double|right] | type \"text\" [cps] | key cmd+t | scroll dy")
}
