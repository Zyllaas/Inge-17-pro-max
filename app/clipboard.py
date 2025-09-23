import pyperclip
import time


def get_clipboard_text() -> str:
    """Get text from clipboard with error handling."""
    try:
        text = pyperclip.paste()
        return text if text else ""
    except Exception as e:
        print(f"Error reading clipboard: {e}")
        return ""


def set_clipboard_text(text: str) -> bool:
    """Set text to clipboard with error handling."""
    try:
        pyperclip.copy(text)
        # Brief delay to ensure clipboard is updated
        time.sleep(0.1)
        return True
    except Exception as e:
        print(f"Error writing to clipboard: {e}")
        return False


def clear_clipboard() -> bool:
    """Clear the clipboard."""
    return set_clipboard_text("")


def get_clipboard_size() -> int:
    """Get the size of clipboard content in characters."""
    try:
        text = get_clipboard_text()
        return len(text)
    except Exception:
        return 0