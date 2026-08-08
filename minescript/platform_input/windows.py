from __future__ import annotations
import ctypes
from ctypes import wintypes
import threading
import time
from .base import InputCapabilities, MinecraftTarget, TargetedInputBackend, TargetedInputError

user32 = ctypes.WinDLL("user32", use_last_error=True)

WM_KEYDOWN=0x0100; WM_KEYUP=0x0101; WM_SYSKEYDOWN=0x0104; WM_SYSKEYUP=0x0105
WM_LBUTTONDOWN=0x0201; WM_LBUTTONUP=0x0202; WM_RBUTTONDOWN=0x0204; WM_RBUTTONUP=0x0205
MK_LBUTTON=0x0001; MK_RBUTTON=0x0002
SW_RESTORE=9

VK={"shift":0x10,"ctrl":0x11,"alt":0x12,"space":0x20,"enter":0x0D,"tab":0x09,"esc":0x1B}
for i in range(1,13): VK[f"f{i}"]=0x6F+i

EnumWindowsProc=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
user32.EnumWindows.argtypes=[EnumWindowsProc,wintypes.LPARAM]; user32.EnumWindows.restype=wintypes.BOOL
user32.GetWindowTextLengthW.argtypes=[wintypes.HWND]; user32.GetWindowTextLengthW.restype=ctypes.c_int
user32.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]; user32.GetWindowTextW.restype=ctypes.c_int
user32.IsWindow.argtypes=[wintypes.HWND]; user32.IsWindow.restype=wintypes.BOOL
user32.IsWindowVisible.argtypes=[wintypes.HWND]; user32.IsWindowVisible.restype=wintypes.BOOL
user32.IsIconic.argtypes=[wintypes.HWND]; user32.IsIconic.restype=wintypes.BOOL
user32.PostMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]; user32.PostMessageW.restype=wintypes.BOOL
user32.MapVirtualKeyW.argtypes=[wintypes.UINT,wintypes.UINT]; user32.MapVirtualKeyW.restype=wintypes.UINT
user32.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]; user32.GetWindowThreadProcessId.restype=wintypes.DWORD
user32.GetForegroundWindow.restype=wintypes.HWND
user32.SetForegroundWindow.argtypes=[wintypes.HWND]; user32.SetForegroundWindow.restype=wintypes.BOOL
user32.ShowWindow.argtypes=[wintypes.HWND,ctypes.c_int]; user32.ShowWindow.restype=wintypes.BOOL
user32.BringWindowToTop.argtypes=[wintypes.HWND]; user32.BringWindowToTop.restype=wintypes.BOOL


def _window_title(hwnd) -> str:
    length=user32.GetWindowTextLengthW(hwnd)
    if length<=0:return ""
    buf=ctypes.create_unicode_buffer(length+1)
    user32.GetWindowTextW(hwnd,buf,len(buf))
    return buf.value


def list_minecraft_windows(title_hint: str="Minecraft") -> list[MinecraftTarget]:
    matches=[]; hint=(title_hint or "Minecraft").lower()
    @EnumWindowsProc
    def callback(hwnd,_):
        if not user32.IsWindowVisible(hwnd): return True
        title=_window_title(hwnd)
        low=title.lower()
        # Include normal Minecraft titles and Java windows matching the user's hint.
        if title and (hint in low or "minecraft" in low):
            pid=wintypes.DWORD(0); user32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
            matches.append(MinecraftTarget(
                key=f"hwnd:{int(hwnd)}", title=title, pid=int(pid.value) or None,
                native_id=int(hwnd), platform="Windows", session="Win32",
                minimized=bool(user32.IsIconic(hwnd)), details="Win32 top-level window",
            ))
        return True
    user32.EnumWindows(callback,0)
    matches.sort(key=lambda t:("minecraft" not in t.title.lower(),"java" not in t.title.lower(),len(t.title)))
    return matches


def _vk(name:str)->int:
    n=str(name).lower()
    if n in VK:return VK[n]
    if len(n)==1:
        code=user32.VkKeyScanW(ord(n))
        if code==-1:raise TargetedInputError(f"Unsupported key: {name}")
        return code & 0xFF
    raise TargetedInputError(f"Unsupported key: {name}")


def _key_lparam(vk:int,key_up:bool=False)->int:
    scan=user32.MapVirtualKeyW(vk,0); value=1|(scan<<16)
    if key_up:value|=(1<<30)|(1<<31)
    return value


class WindowsTargetedInput(TargetedInputBackend):
    capabilities=InputCapabilities(
        name="Windows background link", targeted_keyboard=True, targeted_mouse_buttons=True,
        targeted_relative_mouse=False, unfocused=True, minimized=True, focus_switch=True,
        relative_requires_focus=True, session="Win32",
        background_label="Targeted background input",
        minimized_label="Best effort while minimized",
        notes="Keyboard and mouse-button events are sent to the linked Minecraft HWND. Minecraft/GLFW may ignore some events while fully minimized; camera turns require temporary focus.",
    )
    def __init__(self,title_hint="Minecraft",target_id=None):
        super().__init__(title_hint,target_id); self._held_keys=set(); self._held_buttons=set(); self._lock=threading.RLock()
    def find_target(self):
        found=list_minecraft_windows(self.title_hint)
        return found[0].native_id if found else None
    def _post(self,msg,wparam,lparam=0):
        hwnd=self.ensure_target()
        if not user32.IsWindow(hwnd): self.target=self.find_target(); hwnd=self.ensure_target()
        if not user32.PostMessageW(hwnd,msg,wparam,lparam): raise TargetedInputError(f"PostMessage failed ({ctypes.get_last_error()}).")
    def key_down(self,name):
        with self._lock:
            vk=_vk(name); self._post(WM_SYSKEYDOWN if str(name).lower()=="alt" else WM_KEYDOWN,vk,_key_lparam(vk,False)); self._held_keys.add(str(name).lower())
    def key_up(self,name):
        with self._lock:
            vk=_vk(name); self._post(WM_SYSKEYUP if str(name).lower()=="alt" else WM_KEYUP,vk,_key_lparam(vk,True)); self._held_keys.discard(str(name).lower())
    def tap(self,name,hold=.05):self.key_down(name);time.sleep(hold);self.key_up(name)
    def chord(self,*names,hold=.04):
        for n in names:self.key_down(n)
        time.sleep(hold)
        for n in reversed(names):self.key_up(n)
    def mouse_down(self,button):
        b=str(button).lower()
        if b=="left":self._post(WM_LBUTTONDOWN,MK_LBUTTON,0)
        elif b=="right":self._post(WM_RBUTTONDOWN,MK_RBUTTON,0)
        else:raise TargetedInputError(f"Unsupported mouse button: {button}")
        self._held_buttons.add(b)
    def mouse_up(self,button):
        b=str(button).lower()
        if b=="left":self._post(WM_LBUTTONUP,0,0)
        elif b=="right":self._post(WM_RBUTTONUP,0,0)
        else:raise TargetedInputError(f"Unsupported mouse button: {button}")
        self._held_buttons.discard(b)
    def click(self,button,hold=.05):self.mouse_down(button);time.sleep(hold);self.mouse_up(button)
    def release_all(self):
        for b in list(self._held_buttons):
            try:self.mouse_up(b)
            except Exception:pass
        for k in list(self._held_keys):
            try:self.key_up(k)
            except Exception:pass
        self._held_buttons.clear();self._held_keys.clear()


class WindowsFocusController:
    name="Windows foreground switch"
    available=True
    def capture_current(self):
        hwnd=user32.GetForegroundWindow(); return int(hwnd) if hwnd else None
    def focus(self,target: MinecraftTarget)->bool:
        hwnd=int(target.native_id or 0)
        if not hwnd or not user32.IsWindow(hwnd):return False
        if user32.IsIconic(hwnd):user32.ShowWindow(hwnd,SW_RESTORE)
        user32.BringWindowToTop(hwnd)
        return bool(user32.SetForegroundWindow(hwnd))
    def restore(self,token)->bool:
        if not token:return False
        try:
            hwnd=int(token)
            if not user32.IsWindow(hwnd):return False
            user32.BringWindowToTop(hwnd); return bool(user32.SetForegroundWindow(hwnd))
        except Exception:return False
