"""
REREAL - Spitit: Global hotkey controller.
Supports hold-to-talk and toggle-to-talk modes with custom key combos.
"""

import threading
import time


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


class HotkeyController:
    """
    Global hotkey controller supporting hold-to-talk and toggle-to-talk modes.
    
    Usage:
        controller = HotkeyController(
            hold_combo="alt+left shift",
            toggle_combo="alt+left shift+space",
            mode="hold",
            on_start=start_recording,
            on_stop=stop_recording,
        )
        controller.start()
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
        self._active = False
        self._toggle_recording = False
        self._hold_pressed = False
        self._hooks = []
        self._running = False
        self._lock = threading.Lock()

    def start(self):
        """Register global hotkey hooks."""
        import keyboard

        self._running = True
        self._register_hooks()

    def stop(self):
        """Unregister all hotkey hooks."""
        import keyboard

        self._running = False
        for hook in self._hooks:
            try:
                keyboard.unhook(hook)
            except Exception:
                pass
        self._hooks = []
        self._toggle_recording = False
        self._hold_pressed = False

    def update_combos(self, hold_combo: str, toggle_combo: str, mode: str):
        """Update hotkey combos and mode. Re-registers hooks."""
        was_running = self._running
        if was_running:
            self.stop()
        self.hold_combo = hold_combo
        self.toggle_combo = toggle_combo
        self.mode = mode
        if was_running:
            self.start()

    def _register_hooks(self):
        """Set up keyboard hooks for the current mode."""
        import keyboard

        if self.mode == "hold":
            # Hold mode: record while keys are held, stop on release
            hook = keyboard.on_press_key(
                self.hold_combo.split("+")[-1].strip(),
                self._on_hold_press,
                suppress=False,
            )
            self._hooks.append(hook)

            # Use add_hotkey for the full combo
            keyboard.add_hotkey(
                self.hold_combo,
                self._on_hold_start,
                suppress=False,
                trigger_on_release=False,
            )

            # Detect release of any key in the combo
            for key in self.hold_combo.split("+"):
                key = key.strip()
                hook = keyboard.on_release_key(
                    key,
                    self._on_hold_release,
                    suppress=False,
                )
                self._hooks.append(hook)

        elif self.mode == "toggle":
            # Toggle mode: press combo to start, press again to stop
            keyboard.add_hotkey(
                self.toggle_combo,
                self._on_toggle,
                suppress=False,
                trigger_on_release=False,
            )

    def _on_hold_start(self):
        """Called when hold combo is pressed."""
        with self._lock:
            if self._hold_pressed:
                # Double-tap: cancel recording
                self._hold_pressed = False
                if self.on_stop:
                    self.on_stop()
                return

            self._hold_pressed = True

        if self.on_start:
            self.on_start()

    def _on_hold_press(self, event):
        """Track key press for hold mode."""
        pass  # Handled by add_hotkey

    def _on_hold_release(self, event):
        """Called when any key in the hold combo is released."""
        with self._lock:
            if not self._hold_pressed:
                return
            self._hold_pressed = False

        if self.on_stop:
            self.on_stop()

    def _on_toggle(self):
        """Called when toggle combo is pressed."""
        with self._lock:
            self._toggle_recording = not self._toggle_recording
            is_recording = self._toggle_recording

        if is_recording:
            if self.on_start:
                self.on_start()
        else:
            if self.on_stop:
                self.on_stop()


class HotkeyRecorder:
    """
    Records a hotkey combo from the user.
    Used in the settings UI for custom hotkey assignment.
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
        """
        Start recording a hotkey combo.
        on_complete(combo_str): called when combo is finalized.
        on_update(display_str): called on each key change for live display.
        """
        import keyboard

        self._pressed_keys = set()
        self._combo = ""
        self._recording = True
        self._on_complete = on_complete
        self._on_update = on_update

        self._hook = keyboard.hook(self._on_key_event, suppress=True)

    def stop(self):
        """Stop recording."""
        import keyboard

        self._recording = False
        if self._hook:
            try:
                keyboard.unhook(self._hook)
            except Exception:
                pass
            self._hook = None

    def cancel(self):
        """Cancel recording without saving."""
        self.stop()
        self._combo = ""

    def _on_key_event(self, event):
        """Process keyboard events during recording."""
        import keyboard as kb

        if event.name == "escape":
            self.cancel()
            if self._on_complete:
                self._on_complete(None)  # None = cancelled
            return

        if event.event_type == "down":
            self._pressed_keys.add(event.name.lower())

            # Build display string
            mods = sorted(
                [k for k in self._pressed_keys if k in MODIFIERS],
                key=lambda x: ("ctrl" in x, "alt" in x, "shift" in x, "win" in x),
            )
            non_mods = sorted([k for k in self._pressed_keys if k not in MODIFIERS])

            display_parts = [KEY_DISPLAY.get(k, k.capitalize()) for k in mods + non_mods]
            display = " + ".join(display_parts)

            if self._on_update:
                self._on_update(display)

            # If we have a modifier + a non-modifier key, finalize
            has_mod = any(k in MODIFIERS for k in self._pressed_keys)
            has_non_mod = any(k not in MODIFIERS for k in self._pressed_keys)

            if has_mod and has_non_mod:
                self._combo = "+".join(sorted(self._pressed_keys))
                self.stop()
                if self._on_complete:
                    self._on_complete(self._combo)

        elif event.event_type == "up":
            key = event.name.lower()

            # If only modifiers are held and one is released, finalize with modifiers only
            if key in self._pressed_keys:
                has_non_mod = any(k not in MODIFIERS for k in self._pressed_keys)
                if not has_non_mod and len(self._pressed_keys) >= 2:
                    # All modifiers — finalize when one is released
                    all_mods = all(k in MODIFIERS for k in self._pressed_keys)
                    if all_mods:
                        self._combo = "+".join(sorted(self._pressed_keys))
                        self.stop()
                        if self._on_complete:
                            self._on_complete(self._combo)
                        return

                self._pressed_keys.discard(key)
