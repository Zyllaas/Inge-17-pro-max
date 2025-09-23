from pynput import keyboard


_hotkeys = {}


def _parse_hotkey(hotkey_str: str) -> str:
    """Convert 'ctrl+alt+enter' to '<ctrl>+<alt>+<enter>'."""
    parts = hotkey_str.split("+")
    parsed_parts = []
    for part in parts:
        if part in ["ctrl", "alt", "shift"]:
            parsed_parts.append(f"<{part}>")
        else:
            parsed_parts.append(f"<{part}>")
    return "+".join(parsed_parts)


def register_hotkey(hotkey_str: str, callback) -> None:
    """Register a global hotkey with callback."""
    parsed = _parse_hotkey(hotkey_str)
    _hotkeys[parsed] = callback


def start_listening() -> None:
    """Start listening for registered hotkeys. Blocks."""
    with keyboard.GlobalHotKeys(_hotkeys) as h:
        h.join()
