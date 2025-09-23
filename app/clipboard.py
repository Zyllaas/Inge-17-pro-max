import pyperclip


def get_clipboard_text() -> str:
    """Get text from clipboard."""
    return pyperclip.paste()


def set_clipboard_text(text: str) -> None:
    """Set text to clipboard."""
    pyperclip.copy(text)
