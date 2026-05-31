"""
REREAL - Spitit: Global hotkey controller.
Supports hold-to-talk and toggle-to-talk modes with custom key combos.
Uses a single keyboard hook, 30-second watchdog timer, and sleep/wake monitor.
"""

import threading
import time
import ctypes
from ctypes import wintypes

# Key name normalization: keyboard library names → display names
KEY_DISPLAY = {
    "left shift": "LShift",
    "right shift": "RShift",
    "left alt": "LAlt",
    "right alt": "RAlt",
    "left ctrl": "LCtrl",
    "right ctrl": "RCtrl",
    "left windows": "Win",
    "right windows": "Win",
    "space": "Space",
    "tab": "Tab",
    "enter": "Enter",
    "backspace": "Backspace",
    "delete": "Delete",
    "escape": "Esc",
    "insert": "Insert",
    "home": "Home",
    "end": "End",
    "page up": "PgUp",
    "page down": "PgDn",
    "up": "↑",
    "down": "↓",
    "left": "←",
    "right": "→",
    "caps lock": "CapsLock",
    "num lock": "NumLock",
    "scroll lock": "ScrollLock",
    "print screen": "PrtSc",
    "pause": "Pause",
    "f1": "F1", "f2": "F2", "f3": "F3", "f4": "F4",
    "f5": "F5", "f6": "F6", "f7": "F7", "f8": "F8",
    "f9": "F9", "f10": "F10", "f11": "F11", "f12": "F12",
}

# Modifier keys
MODIFIERS = {
    "left shift", "right shift", "shift",
    "left alt", "right alt", "alt",
    "left ctrl", "right ctrl", "ctrl",
    "left windows", "right windows",
}

# Windows reserved hotkeys that cannot be intercepted
BLOCKED_COMBOS = {
    frozenset(["ctrl", "alt", "delete"]),
    frozenset(["alt", "f4"]),
}

BLOCKED_WIN_COMBOS = {
    frozenset(["left windows", "l"]),
    frozenset(["left windows", "d"]),
    frozenset(["left windows", "e"]),
    frozenset(["left windows", "r"]),
    frozenset(["left windows", "s"]),
    frozenset(["left windows", "tab"]),
    frozenset(["left windows", "x"]),
    frozenset(["right windows", "l"]),
    frozenset(["right windows", "d"]),
    frozenset(["right windows", "e"]),
    frozenset(["right windows", "r"]),
    frozenset(["right windows", "s"]),
    frozenset(["right windows", "tab"]),
    frozenset(["right windows", "x"]),
}

# Common app shortcuts to warn about
WARN_COMBOS = {
    frozenset(["ctrl", "c"]),
    frozenset(["ctrl", "v"]),
    frozenset(["ctrl", "z"]),
    frozenset(["ctrl", "x"]),
    frozenset(["ctrl", "a"]),
}

# Modifier name normalization aliases
MODIFIER_ALIASES = {
    "left shift": "shift",
    "right shift": "shift",
    "left alt": "alt",
    "right alt": "alt",
    "left ctrl": "ctrl",
    "right ctrl": "ctrl",
    "left windows": "win",
    "right windows": "win",
    "win": "win",
}


def format_combo(combo_str: str) -> str:
    """Format a combo string for display. E.g. 'alt+left shift' → 'Alt + LShift'"""
    parts = combo_str.lower().split("+")
    display_parts = []
    for p in parts:
        p = p.strip()
        if p in KEY_DISPLAY:
            display_parts.append(KEY_DISPLAY[p])
        else:
            display_parts.append(p.capitalize())
    return " + ".join(display_parts)


def validate_combo(combo_str: str) -> tuple[bool, str]:
    """
    Validate a hotkey combo string.
    Returns (valid: bool, message: str).
    """
    parts = [p.strip().lower() for p in combo_str.split("+")]
    key_set = frozenset(parts)

    # Must have at least one modifier
    has_modifier = any(p in MODIFIERS for p in parts)
    if not has_modifier:
        return False, "Hotkey must include at least one modifier (Ctrl, Alt, Shift, or Win)."

    # Check blocked combos
    if key_set in BLOCKED_COMBOS:
        return False, f"'{format_combo(combo_str)}' is reserved by Windows and cannot be used."

    if key_set in BLOCKED_WIN_COMBOS:
        return False, f"'{format_combo(combo_str)}' is reserved by Windows and cannot be used."

    # Blocked single keys
    blocked_singles = {"print screen", "pause", "scroll lock"}
    non_mod_keys = [p for p in parts if p not in MODIFIERS]
    if len(non_mod_keys) == 1 and non_mod_keys[0] in blocked_singles:
        if len(parts) == 1:
            return False, f"'{non_mod_keys[0]}' cannot be used alone as a hotkey."

    # Warn about common shortcuts
    if key_set in WARN_COMBOS:
        return True, f"Warning: '{format_combo(combo_str)}' conflicts with a common shortcut."

    return True, ""


def get_key_variations(key: str) -> set[str]:
    """Get all representation variations of a key (e.g. 'left shift' -> {'left shift', 'shift'})."""
    variations = {key}
    alias = MODIFIER_ALIASES.get(key)
    if alias:
        variations.add(alias)
    if key == "shift":
        variations.update({"left shift", "right shift"})
    elif key == "alt":
        variations.update({"left alt", "right alt"})
    elif key == "ctrl":
        variations.update({"left ctrl", "right ctrl"})
    elif key == "win":
        variations.update({"left windows", "right windows"})
    return variations


# Win32 Power Broadcast Definitions
WM_POWERBROADCAST = 0x0218
PBT_APMRESUMESUSPEND = 0x0007
PBT_APMRESUMEAUTOMATIC = 0x0012

WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_int64, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM)


class WNDCLASSEX(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("style", ctypes.c_uint),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HCURSOR),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
    ]


class PowerMonitor(threading.Thread):
    """
    Win32 power monitor that registers a hidden message-only window and listens for
    WM_POWERBROADCAST to detect wake from sleep.
    """
    def __init__(self, callback):
        super().__init__(daemon=True)
        self.callback = callback
        self.hwnd = None
        self._running = True
        self._wnd_proc = None

    def run(self):
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            def wnd_proc(hwnd, msg, wparam, lparam):
                if msg == WM_POWERBROADCAST:
                    if wparam in (PBT_APMRESUMESUSPEND, PBT_APMRESUMEAUTOMATIC):
                        try:
                            self.callback()
                        except Exception as e:
                            print(f"[PowerMonitor] Callback error: {e}")
                return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

            self._wnd_proc = WNDPROC(wnd_proc)
            hinstance = kernel32.GetModuleHandleW(None)

            wndclass = WNDCLASSEX()
            wndclass.cbSize = ctypes.sizeof(WNDCLASSEX)
            wndclass.style = 0
            wndclass.lpfnWndProc = self._wnd_proc
            wndclass.cbClsExtra = 0
            wndclass.cbWndExtra = 0
            wndclass.hInstance = hinstance
            wndclass.hIcon = 0
            wndclass.hCursor = 0
            wndclass.hbrBackground = 0
            wndclass.lpszMenuName = None
            wndclass.lpszClassName = "SpititPowerMonitorClass"
            wndclass.hIconSm = 0

            user32.RegisterClassExW(ctypes.byref(wndclass))

            HWND_MESSAGE = -3
            self.hwnd = user32.CreateWindowExW(
                0,
                wndclass.lpszClassName,
                "SpititPowerMonitorWindow",
                0, 0, 0, 0, 0,
                HWND_MESSAGE,
                0,
                hinstance,
                None
            )

            if not self.hwnd:
                return

            msg = wintypes.MSG()
            while self._running:
                ret = user32.GetMessageW(ctypes.byref(msg), 0, 0, 0)
                if ret == 0 or ret == -1:
                    break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except Exception as e:
            print(f"[PowerMonitor] Error: {e}")

    def stop(self):
        self._running = False
        if self.hwnd:
            try:
                ctypes.windll.user32.PostMessageW(self.hwnd, 0x0012, 0, 0)  # WM_QUIT = 0x0012
            except Exception:
                pass


class HotkeyController:
    """
    Global hotkey controller using a single hook, watchdog timer, and sleep/wake monitor.
    """

    def __init__(
        self,
        hold_combo: str = "alt+left shift",
        toggle_combo: str = "alt+left shift+space",
        mode: str = "hold",
        on_start=None,
        on_stop=None,
    ):
        self.hold_combo = hold_combo
        self.toggle_combo = toggle_combo
        self.mode = mode
        self.on_start = on_start
        self.on_stop = on_stop

        self._running = False
        self._pressed_keys = set()
        self._hold_pressed = False
        self._toggle_pressed = False
        self._toggle_recording = False

        self._hook = None
        self._watchdog = None
        self._power_monitor = None
        self._lock = threading.Lock()

    def start(self):
        """Register keyboard hook and start background monitors."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._pressed_keys = set()
            self._hold_pressed = False
            self._toggle_pressed = False
            self._toggle_recording = False

            # Hook keyboard events
            import keyboard
            try:
                self._hook = keyboard.hook(self._on_key_event, suppress=False)
            except Exception as e:
                print(f"[Hotkey] Initial hook failed: {e}")

            # Start background watchdog & power monitors
            self._start_watchdog()
            try:
                self._power_monitor = PowerMonitor(self._on_wake_detected)
                self._power_monitor.start()
            except Exception as e:
                print(f"[Hotkey] Failed to start power monitor: {e}")

    def stop(self):
        """Unregister hook and stop background monitors."""
        with self._lock:
            self._running = False

            # Stop watchdog
            self._stop_watchdog()

            # Stop power monitor
            if self._power_monitor:
                try:
                    self._power_monitor.stop()
                except Exception:
                    pass
                self._power_monitor = None

            # Unhook keyboard listener
            if self._hook:
                import keyboard
                try:
                    keyboard.unhook(self._hook)
                except Exception:
                    pass
                self._hook = None

            self._pressed_keys = set()
            self._hold_pressed = False
            self._toggle_pressed = False
            self._toggle_recording = False

    def update_combos(self, hold_combo: str, toggle_combo: str, mode: str):
        """Update hotkey settings and trigger hotkey re-registration."""
        was_running = False
        with self._lock:
            was_running = self._running

        if was_running:
            self.stop()

        self.hold_combo = hold_combo
        self.toggle_combo = toggle_combo
        self.mode = mode

        if was_running:
            self.start()

    def _start_watchdog(self):
        """Set up the 30-second watchdog timer to refresh hooks."""
        self._stop_watchdog()
        if self._running:
            self._watchdog = threading.Timer(30.0, self._reregister)
            self._watchdog.daemon = True
            self._watchdog.start()

    def _stop_watchdog(self):
        """Cancel the watchdog timer."""
        if self._watchdog:
            self._watchdog.cancel()
            self._watchdog = None

    def _reregister(self):
        """Safely re-hook to bypass Windows hook invalidations/timeouts."""
        with self._lock:
            if not self._running:
                return

            import keyboard
            if self._hook:
                try:
                    keyboard.unhook(self._hook)
                except Exception:
                    pass
                self._hook = None

            try:
                self._hook = keyboard.hook(self._on_key_event, suppress=False)
            except Exception as e:
                print(f"[Hotkey] Hook re-registration failed: {e}")

            # Restart watchdog
            self._start_watchdog()

    def _on_wake_detected(self):
        """Immediately re-register hook 1.5 seconds after Windows resumes from sleep."""
        print("[Hotkey] System wake detected. Re-registering hook...")
        time.sleep(1.5)
        self._reregister()

    def is_combo_active(self, combo_set: set[str]) -> bool:
        """Verify if all keys in a combo are physically pressed using cache & direct state."""
        if not combo_set:
            return False
        import keyboard
        for k in combo_set:
            variations = get_key_variations(k)
            # Check cached press event states
            pressed = any(v in self._pressed_keys for v in variations)
            if not pressed:
                # System query fallback
                pressed = any(keyboard.is_pressed(v) for v in variations if v)
            if not pressed:
                return False
        return True

    def _on_key_event(self, event):
        """Track down/up events and process state-machine transitions."""
        if not self._running or not event.name:
            return

        key_name = event.name.lower()

        with self._lock:
            if event.event_type == "down":
                self._pressed_keys.add(key_name)
            else:
                self._pressed_keys.discard(key_name)

            # Extract keys
            hold_set = {k.strip().lower() for k in self.hold_combo.split("+")}
            toggle_set = {k.strip().lower() for k in self.toggle_combo.split("+")}

            hold_active = self.is_combo_active(hold_set)
            toggle_active = self.is_combo_active(toggle_set)

            if self.mode == "hold":
                if hold_active:
                    if not self._hold_pressed:
                        self._hold_pressed = True
                        if self.on_start:
                            self.on_start()
                else:
                    if self._hold_pressed:
                        self._hold_pressed = False
                        if self.on_stop:
                            self.on_stop()

            elif self.mode == "toggle":
                if toggle_active:
                    if not self._toggle_pressed:
                        self._toggle_pressed = True
                        self._toggle_recording = not self._toggle_recording
                        if self._toggle_recording:
                            if self.on_start:
                                self.on_start()
                        else:
                            if self.on_stop:
                                self.on_stop()
                else:
                    self._toggle_pressed = False


class HotkeyRecorder:
    """
    Records a custom hotkey combo from the settings UI.
    """

    def __init__(self):
        self._pressed_keys = set()
        self._combo = ""
        self._recording = False
        self._hook = None
        self._on_complete = None
        self._on_update = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self, on_complete=None, on_update=None):
        """Start listening to keyboard inputs for the custom combo."""
        import keyboard

        self._pressed_keys = set()
        self._combo = ""
        self._recording = True
        self._on_complete = on_complete
        self._on_update = on_update

        self._hook = keyboard.hook(self._on_key_event, suppress=True)

    def stop(self):
        """Unregister recorder listener."""
        import keyboard

        self._recording = False
        if self._hook:
            try:
                keyboard.unhook(self._hook)
            except Exception:
                pass
            self._hook = None

    def cancel(self):
        """Cancel recording."""
        self.stop()
        self._combo = ""

    def _on_key_event(self, event):
        """Process keyboard events during recording."""
        if event.name == "escape":
            self.cancel()
            if self._on_complete:
                self._on_complete(None)
            return

        key_name = event.name.lower() if event.name else ""
        if not key_name:
            return

        if event.event_type == "down":
            self._pressed_keys.add(key_name)

            # Build display sequence
            mods = sorted(
                [k for k in self._pressed_keys if k in MODIFIERS],
                key=lambda x: ("ctrl" in x, "alt" in x, "shift" in x, "win" in x),
            )
            non_mods = sorted([k for k in self._pressed_keys if k not in MODIFIERS])

            display_parts = [KEY_DISPLAY.get(k, k.capitalize()) for k in mods + non_mods]
            display = " + ".join(display_parts)

            if self._on_update:
                self._on_update(display)

            # Complete registration if we have modifier + non-modifier
            has_mod = any(k in MODIFIERS for k in self._pressed_keys)
            has_non_mod = any(k not in MODIFIERS for k in self._pressed_keys)

            if has_mod and has_non_mod:
                self._combo = "+".join(sorted(self._pressed_keys))
                self.stop()
                if self._on_complete:
                    self._on_complete(self._combo)

        elif event.event_type == "up":
            if key_name in self._pressed_keys:
                has_non_mod = any(k not in MODIFIERS for k in self._pressed_keys)
                if not has_non_mod and len(self._pressed_keys) >= 2:
                    # Finalize when modifier is released
                    all_mods = all(k in MODIFIERS for k in self._pressed_keys)
                    if all_mods:
                        self._combo = "+".join(sorted(self._pressed_keys))
                        self.stop()
                        if self._on_complete:
                            self._on_complete(self._combo)
                        return

                self._pressed_keys.discard(key_name)
