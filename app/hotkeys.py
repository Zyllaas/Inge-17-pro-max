import re
from typing import Dict, Callable
from pynput import keyboard


class HotkeyManager:
    def __init__(self):
        self.hotkeys: Dict[str, Callable] = {}
        self.listener = None

    def _parse_hotkey(self, hotkey_str: str) -> str:
        """Convert 'ctrl+alt+enter' to pynput format '<ctrl>+<alt>+<enter>'."""
        # Normalize the hotkey string
        hotkey_str = hotkey_str.lower().strip()
        parts = [part.strip() for part in hotkey_str.split("+")]
        
        parsed_parts = []
        for part in parts:
            # Handle special keys
            if part in ["ctrl", "alt", "shift"]:
                parsed_parts.append(f"<{part}>")
            elif part == "enter":
                parsed_parts.append("<enter>")
            elif part == "backspace":
                parsed_parts.append("<backspace>")
            elif part == "`":
                parsed_parts.append("`")
            elif part.startswith("f") and part[1:].isdigit():  # Function keys
                parsed_parts.append(f"<{part}>")
            elif len(part) == 1:  # Single character
                parsed_parts.append(part)
            else:
                # For other special keys, wrap in brackets
                parsed_parts.append(f"<{part}>")
        
        return "+".join(parsed_parts)

    def register(self, hotkey_str: str, callback: Callable) -> None:
        """Register a global hotkey with callback."""
        try:
            parsed = self._parse_hotkey(hotkey_str)
            self.hotkeys[parsed] = callback
            print(f"Registered hotkey: {hotkey_str} -> {parsed}")
        except Exception as e:
            print(f"Failed to register hotkey {hotkey_str}: {e}")

    def start_listening(self) -> None:
        """Start listening for registered hotkeys. This blocks."""
        if not self.hotkeys:
            print("No hotkeys registered")
            return
        
        try:
            print(f"Starting hotkey listener with {len(self.hotkeys)} hotkeys")
            with keyboard.GlobalHotKeys(self.hotkeys) as listener:
                self.listener = listener
                listener.join()
        except Exception as e:
            print(f"Error starting hotkey listener: {e}")

    def stop_listening(self) -> None:
        """Stop the hotkey listener."""
        if self.listener:
            self.listener.stop()