import sys
import ctypes
from ctypes import wintypes
from typing import Optional, Dict, Tuple

from PySide6.QtCore import QObject, Signal, QAbstractNativeEventFilter, QCoreApplication
from PySide6.QtWidgets import QApplication

from .config import ConfigManager

# Win32 Constants
WM_HOTKEY = 0x0312

MOD_ALT      = 0x0001
MOD_CONTROL  = 0x0002
MOD_SHIFT    = 0x0004
MOD_WIN      = 0x0008
MOD_NOREPEAT = 0x4000

# Virtual Key Mappings
VK_MAP = {
    "esc": 0x1B, "escape": 0x1B,
    "tab": 0x09,
    "enter": 0x0D, "return": 0x0D,
    "space": 0x20,
    "backspace": 0x08,
    "delete": 0x2E, "del": 0x2E,
    "insert": 0x2D, "ins": 0x2D,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21, "pgup": 0x21,
    "pagedown": 0x22, "pgdn": 0x22,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    "f13": 0x7C, "f14": 0x7D, "f15": 0x7E, "f16": 0x7F,
    "numpad0": 0x60, "numpad1": 0x61, "numpad2": 0x62, "numpad3": 0x63,
    "numpad4": 0x64, "numpad5": 0x65, "numpad6": 0x66, "numpad7": 0x67,
    "numpad8": 0x68, "numpad9": 0x69,
    "multiply": 0x6A, "add": 0x6B, "subtract": 0x6D,
    "decimal": 0x6E, "divide": 0x6F,
    "capslock": 0x14, "numlock": 0x90, "scrolllock": 0x91,
    "printscreen": 0x2C, "prtsc": 0x2C,
    "pause": 0x13,
    "semicolon": 0xBA, "equal": 0xBB, "comma": 0xBC,
    "minus": 0xBD, "period": 0xBE, "slash": 0xBF,
    "backtick": 0xC0, "grave": 0xC0,
    "lbracket": 0xDB, "backslash": 0xDC, "rbracket": 0xDD,
    "quote": 0xDE, "apostrophe": 0xDE,
}

# Win32 error code → human readable (common ones)
_WIN32_ERRORS = {
    1409: "Hotkey already registered by another application",
    5: "Access denied — try running as Administrator",
    87: "Invalid hotkey combination",
}


def parse_hotkey_combo(combo_str: str) -> Optional[Tuple[int, int]]:
    """
    Parses a hotkey string like 'ctrl+alt+s', 'f9', 'esc' into (modifiers, vk_code).
    Returns None if the combo is invalid or has no recognizable key.
    """
    if not combo_str or not combo_str.strip():
        return None

    parts = [p.strip().lower() for p in combo_str.split("+") if p.strip()]
    if not parts:
        return None

    modifiers = MOD_NOREPEAT
    vk_code = None

    for part in parts:
        if part in ("ctrl", "control"):
            modifiers |= MOD_CONTROL
        elif part == "alt":
            modifiers |= MOD_ALT
        elif part == "shift":
            modifiers |= MOD_SHIFT
        elif part in ("win", "cmd", "super"):
            modifiers |= MOD_WIN
        elif part in VK_MAP:
            vk_code = VK_MAP[part]
        elif len(part) == 1:
            char = part.upper()
            vk_code = ord(char)
        else:
            print(f"[Hotkey] Unrecognized key part: '{part}'")

    if vk_code is None:
        return None

    return modifiers, vk_code


class WinNativeEventFilter(QAbstractNativeEventFilter):
    def __init__(self, hotkey_manager: "GlobalHotkeyManager"):
        super().__init__()
        self.mgr = hotkey_manager

    def nativeEventFilter(self, eventType, message):
        if eventType in (b"windows_generic_MSG", "windows_generic_MSG"):
            try:
                msg_ptr = message.__int__()
                msg = wintypes.MSG.from_address(msg_ptr)
                if msg.message == WM_HOTKEY:
                    hotkey_id = msg.wParam
                    self.mgr._dispatch_hotkey(hotkey_id)
                    return True, 0
            except Exception:
                pass
        return False, 0


class GlobalHotkeyManager(QObject):
    scan_requested     = Signal()
    panic_requested    = Signal()
    settings_requested = Signal()
    repeat_requested   = Signal()

    def __init__(self, config_mgr: ConfigManager, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.config = config_mgr
        self._user32 = ctypes.windll.user32 if sys.platform == "win32" else None
        self._filter: Optional[WinNativeEventFilter] = None
        self._registered_ids: Dict[int, Signal] = {}
        self._next_id = 1000

        q_app = QApplication.instance()
        if q_app and self._user32:
            self._filter = WinNativeEventFilter(self)
            q_app.installNativeEventFilter(self._filter)

    def start(self):
        self.register_all()

    def stop(self):
        self.unregister_all()

    def _dispatch_hotkey(self, hotkey_id: int):
        if hotkey_id in self._registered_ids:
            sig = self._registered_ids[hotkey_id]
            sig.emit()

    def _register_one(self, combo_str: str, signal: Signal) -> bool:
        """
        Register a single hotkey combo.
        Returns True on success, False on failure.
        On failure, retries once without MOD_NOREPEAT flag.
        """
        if not self._user32:
            return False

        parsed = parse_hotkey_combo(combo_str)
        if not parsed:
            print(f"[Hotkey] Could not parse combo: '{combo_str}'")
            return False

        mods, vk = parsed

        # Attempt 1: with MOD_NOREPEAT
        hk_id = self._next_id
        self._next_id += 1
        res = self._user32.RegisterHotKey(None, hk_id, mods, vk)
        if res:
            self._registered_ids[hk_id] = signal
            print(f"[Hotkey] ✓ Registered '{combo_str}' → ID {hk_id}")
            return True

        err = ctypes.GetLastError()
        err_msg = _WIN32_ERRORS.get(err, f"Win32 error code {err}")
        print(f"[Hotkey] ✗ Failed '{combo_str}' with MOD_NOREPEAT: {err_msg}. Retrying without...")

        # Attempt 2: without MOD_NOREPEAT (plain registration)
        mods_no_nr = mods & ~MOD_NOREPEAT
        hk_id2 = self._next_id
        self._next_id += 1
        res2 = self._user32.RegisterHotKey(None, hk_id2, mods_no_nr, vk)
        if res2:
            self._registered_ids[hk_id2] = signal
            print(f"[Hotkey] ✓ Registered '{combo_str}' without MOD_NOREPEAT → ID {hk_id2}")
            return True

        err2 = ctypes.GetLastError()
        err2_msg = _WIN32_ERRORS.get(err2, f"Win32 error code {err2}")
        print(f"[Hotkey] ✗ Both attempts failed for '{combo_str}': {err2_msg}")
        return False

    def register_all(self):
        self.unregister_all()
        if not self._user32:
            return

        hk_scan     = self.config.get("hotkey_scan",       "ctrl+alt+s")
        hk_quick    = self.config.get("hotkey_quick_scan", "f9")
        hk_panic    = self.config.get("hotkey_panic",      "esc")
        hk_settings = self.config.get("hotkey_settings",   "ctrl+alt+o")
        hk_repeat   = self.config.get("hotkey_repeat",     "ctrl+alt+r")

        self._register_one(hk_scan,     self.scan_requested)
        self._register_one(hk_quick,    self.scan_requested)
        self._register_one(hk_panic,    self.panic_requested)
        self._register_one(hk_settings, self.settings_requested)
        self._register_one(hk_repeat,   self.repeat_requested)

    def unregister_all(self):
        if not self._user32:
            return
        for hk_id in list(self._registered_ids.keys()):
            try:
                self._user32.UnregisterHotKey(None, hk_id)
            except Exception:
                pass
        self._registered_ids.clear()
