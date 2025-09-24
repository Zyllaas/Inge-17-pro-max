import os
import sys
from pathlib import Path


def resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    
    When running from source, returns path relative to current directory.
    When running from PyInstaller bundle, returns path from temporary directory.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS  # type: ignore
        return os.path.join(base_path, relative_path)
    except AttributeError:
        # Running from source
        return os.path.join(os.path.abspath("."), relative_path)


def get_app_dir() -> Path:
    """Get the application directory for storing user data."""
    if os.name == 'nt':  # Windows
        appdata = os.environ.get('APPDATA')
        if appdata:
            return Path(appdata) / 'ClipboardAI'
        else:
            return Path.home() / 'AppData' / 'Roaming' / 'ClipboardAI'
    else:
        # Unix-like systems
        return Path.home() / '.clipboardai'


def ensure_app_dir() -> Path:
    """Ensure the application directory exists and return it."""
    app_dir = get_app_dir()
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_bundled_file(filename: str) -> Path:
    """Get path to a bundled file."""
    return Path(resource_path(filename))


def file_exists(path: str) -> bool:
    """Check if a file exists."""
    try:
        return Path(path).exists()
    except Exception:
        return False
