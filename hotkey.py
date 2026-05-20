"""Global hotkeys: hold Alt+Left Shift or toggle Alt+Left Shift+Space."""

from __future__ import annotations

import threading
from typing import Callable, Literal

import keyboard

Mode = Literal["hold", "toggle"]

_toggle_armed = False


class HotkeyController:
    def __init__(
        self,
        mode_getter: Callable[[], Mode],
        on_start: Callable[[], None],
        on_stop: Callable[[], None],
    ) -> None:
        self._mode_getter = mode_getter
        self._on_start = on_start
        self._on_stop = on_stop
        self._hook = None
        self._toggle_hotkey_handle = None
        self._recording = False
        self._hold_started = False
        self._lock = threading.Lock()

    def _set_recording(self, value: bool) -> None:
        with self._lock:
            self._recording = value

    def _is_recording(self) -> bool:
        with self._lock:
            return self._recording

    def _hold_keys_down(self) -> bool:
        return keyboard.is_pressed("left shift") and keyboard.is_pressed("left alt")

    def _on_key_event(self, e) -> None:
        mode = self._mode_getter()
        if mode != "hold":
            return
        if e.event_type == keyboard.KEY_DOWN:
            if self._hold_keys_down() and not self._is_recording():
                self._hold_started = True
                self._set_recording(True)
                self._on_start()
        elif e.event_type == keyboard.KEY_UP:
            if self._hold_started and self._is_recording() and not self._hold_keys_down():
                self._hold_started = False
                self._set_recording(False)
                self._on_stop()

    def _toggle_callback(self) -> None:
        global _toggle_armed
        if _toggle_armed:
            return
        _toggle_armed = True

        def release():
            global _toggle_armed
            _toggle_armed = False

        try:
            if self._mode_getter() != "toggle":
                return
            if not self._is_recording():
                self._set_recording(True)
                self._on_start()
            else:
                self._set_recording(False)
                self._on_stop()
        finally:
            threading.Timer(0.25, release).start()

    def start(self) -> None:
        self.stop()
        self._hook = keyboard.hook(self._on_key_event)
        self._toggle_hotkey_handle = keyboard.add_hotkey(
            "left alt+left shift+space",
            self._toggle_callback,
            suppress=False,
        )

    def stop(self) -> None:
        if self._toggle_hotkey_handle is not None:
            try:
                keyboard.remove_hotkey(self._toggle_hotkey_handle)
            except Exception:
                pass
            self._toggle_hotkey_handle = None
        if self._hook is not None:
            try:
                keyboard.unhook(self._hook)
            except Exception:
                pass
            self._hook = None
