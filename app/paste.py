import random
import threading
import time
from pynput.keyboard import Controller

from .config import Config


def typewrite(text: str, config: Config, cancel_event: threading.Event) -> None:
    """Type text with human-like cadence, cancelable."""
    controller = Controller()
    punctuation = ".,!?;:"
    cps = random.uniform(config.min_cps, config.max_cps)
    char_count = 0

    for char in text:
        if cancel_event.is_set():
            break

        controller.type(char)
        char_count += 1

        # Change CPS every ~12 chars
        if char_count % 12 == 0:
            cps = random.uniform(config.min_cps, config.max_cps)

        # Base delay
        delay = 1 / cps
        # Add jitter
        delay += random.uniform(0, config.jitter_ms / 1000)
        time.sleep(delay)

        # Extra pauses
        if char in punctuation:
            time.sleep(config.punct_pause_ms / 1000)
        elif char == "\n":
            time.sleep(config.newline_pause_ms / 1000)

    # If preserve_clipboard, but since typing doesn't affect clipboard, maybe not needed
    # Perhaps it's for if we copy the response first, but spec says optional copy
    pass
