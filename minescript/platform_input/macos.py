from __future__ import annotations
import os
import subprocess
import threading
import time
from .base import InputCapabilities, MinecraftTarget, TargetedInputBackend, TargetedInputError

try:
    import Quartz
except Exception:
    Quartz=None

KEYCODES={
    "a":0,"s":1,"d":2,"f":3,"h":4,"g":5,"z":6,"x":7,"c":8,"v":9,"b":11,
    "q":12,"w":13,"e":14,"r":15,"y":16,"t":17,"1":18,"2":19,"3":20,"4":21,"6":22,
    "5":23,"=":24,"9":25,"7":26,"-":27,"8":28,"0":29,"]":30,"o":31,"u":32,"[":33,
    "i":34,"p":35,"enter":36,"l":37,"j":38,"'":39,"k":40,";":41,"\\":42,",":43,"/":44,
    "n":45,"m":46,".":47,"tab":48,"space":49,"esc":53,"ctrl":59,"shift":56,"alt":58,
    "f1":122,"f2":120,"f3":99,"f4":118,"f5":96,"f6":97,"f7":98,"f8":100,"f9":101,"f10":109,"f11":103,"f12":111,
}


def list_minecraft_targets(title_hint: str="Minecraft") -> list[MinecraftTarget]:
    hint=(title_hint or "Minecraft").lower(); out=[]
    if Quartz is not None:
        try:
            windows=Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionAll,Quartz.kCGNullWindowID) or []
            for info in windows:
                owner=str(info.get(Quartz.kCGWindowOwnerName,"") or "")
                title=str(info.get(Quartz.kCGWindowName,"") or "")
                low=(owner+" "+title).lower()
                if "minecraft" not in low and hint not in low and not ("java" in owner.lower() and "minecraft" in low):
                    continue
                pid=int(info.get(Quartz.kCGWindowOwnerPID,0) or 0)
                wid=int(info.get(Quartz.kCGWindowNumber,0) or 0)
                if pid<=0:continue
                label=title.strip() or (owner.strip()+" — Minecraft")
                out.append(MinecraftTarget(
                    key=f"pid:{pid}:window:{wid}",title=label,pid=pid,native_id=pid,
                    platform="macOS",session="Quartz",minimized=None,
                    details=f"{owner}; Quartz window {wid}".strip("; "),
                ))
        except Exception:
            pass
    if not out:
        try:
            text=subprocess.check_output(["ps","-axo","pid=,command="],text=True,errors="replace",timeout=5)
            for line in text.splitlines():
                parts=line.strip().split(None,1)
                if len(parts)!=2:continue
                try:pid=int(parts[0])
                except ValueError:continue
                cmd=parts[1]; low=cmd.lower()
                if "java" in low and ("minecraft" in low or hint in low):
                    out.append(MinecraftTarget(key=f"pid:{pid}",title="Minecraft Java",pid=pid,native_id=pid,platform="macOS",session="process",minimized=None,details=cmd[:220]))
        except Exception:pass
    dedup={}
    for t in out:dedup.setdefault(t.pid,t)
    return list(dedup.values())


class MacOSTargetedInput(TargetedInputBackend):
    capabilities=InputCapabilities(
        name="macOS background link", targeted_keyboard=True,targeted_mouse_buttons=True,
        targeted_relative_mouse=False,unfocused=True,minimized=True,focus_switch=True,
        relative_requires_focus=True,session="Quartz",
        background_label="Process-targeted Quartz input",
        minimized_label="Best effort while minimized/hidden",
        notes="Quartz CGEventPostToPid targets the linked Java process. Accessibility/Input Monitoring permission is required. Minecraft may ignore some mouse behavior while hidden; camera turns use approved focus switching.",
    )
    def __init__(self,title_hint="Minecraft",target_id=None):
        super().__init__(title_hint,target_id)
        if Quartz is None:raise TargetedInputError("PyObjC Quartz is required for macOS background input.")
        self._held_keys=set();self._held_buttons=set();self._lock=threading.RLock()
    def find_target(self):
        found=list_minecraft_targets(self.title_hint);return found[0].pid if found else None
    def _post(self,event):
        pid=int(self.ensure_target());fn=getattr(Quartz,"CGEventPostToPid",None)
        if fn is None:raise TargetedInputError("CGEventPostToPid is unavailable on this macOS/PyObjC build.")
        fn(pid,event)
    def _keycode(self,name):
        n=str(name).lower()
        if n not in KEYCODES:raise TargetedInputError(f"Unsupported key: {name}")
        return KEYCODES[n]
    def key_down(self,name):
        with self._lock:self._post(Quartz.CGEventCreateKeyboardEvent(None,self._keycode(name),True));self._held_keys.add(str(name).lower())
    def key_up(self,name):
        with self._lock:self._post(Quartz.CGEventCreateKeyboardEvent(None,self._keycode(name),False));self._held_keys.discard(str(name).lower())
    def tap(self,name,hold=.05):self.key_down(name);time.sleep(hold);self.key_up(name)
    def chord(self,*names,hold=.04):
        for n in names:self.key_down(n)
        time.sleep(hold)
        for n in reversed(names):self.key_up(n)
    def _mouse_event(self,button,down):
        loc=Quartz.CGEventGetLocation(Quartz.CGEventCreate(None));b=str(button).lower()
        if b=="left":typ=Quartz.kCGEventLeftMouseDown if down else Quartz.kCGEventLeftMouseUp;qbtn=Quartz.kCGMouseButtonLeft
        elif b=="right":typ=Quartz.kCGEventRightMouseDown if down else Quartz.kCGEventRightMouseUp;qbtn=Quartz.kCGMouseButtonRight
        else:raise TargetedInputError(f"Unsupported mouse button: {button}")
        return Quartz.CGEventCreateMouseEvent(None,typ,loc,qbtn)
    def mouse_down(self,b):self._post(self._mouse_event(b,True));self._held_buttons.add(str(b).lower())
    def mouse_up(self,b):self._post(self._mouse_event(b,False));self._held_buttons.discard(str(b).lower())
    def click(self,b,hold=.05):self.mouse_down(b);time.sleep(hold);self.mouse_up(b)
    def release_all(self):
        for b in list(self._held_buttons):
            try:self.mouse_up(b)
            except Exception:pass
        for k in list(self._held_keys):
            try:self.key_up(k)
            except Exception:pass
        self._held_buttons.clear();self._held_keys.clear()


class MacOSFocusController:
    name="macOS process focus switch"
    available=True
    def _run(self,script):
        return subprocess.run(["osascript","-e",script],capture_output=True,text=True,timeout=8)
    def capture_current(self):
        p=self._run('tell application "System Events" to get unix id of first application process whose frontmost is true')
        try:return int(p.stdout.strip()) if p.returncode==0 else None
        except ValueError:return None
    def focus(self,target: MinecraftTarget)->bool:
        if not target.pid:return False
        script=f'tell application "System Events" to set frontmost of first application process whose unix id is {int(target.pid)} to true'
        return self._run(script).returncode==0
    def restore(self,token)->bool:
        if not token:return False
        script=f'tell application "System Events" to set frontmost of first application process whose unix id is {int(token)} to true'
        return self._run(script).returncode==0
