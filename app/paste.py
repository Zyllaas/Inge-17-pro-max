import asyncio
import random
import time
from pynput.keyboard import Controller

from .config import Config


class TypewriterManager:
    def __init__(self, config: Config):
        self.config = config
        self.controller = Controller()
        self.cancel_event = asyncio.Event()
        self.is_typing = False

    def cancel(self) -> None:
        """Cancel current typing operation."""
        if self.is_typing:
            self.cancel_event.set()
            print("Typing cancelled")

    async def typewrite(self, text: str) -> None:
        """Type text with human-like cadence, cancelable."""
        if self.is_typing:
            print("Already typing, ignoring new request")
            return

        self.is_typing = True
        self.cancel_event.clear()
        
        try:
            punctuation = ".,!?;:"
            cps = random.uniform(self.config.min_cps, self.config.max_cps)
            char_count = 0

            print(f"Starting typewriter with {len(text)} characters")
            
            for i, char in enumerate(text):
                # Check for cancellation
                if self.cancel_event.is_set():
                    print(f"Typing cancelled at character {i}")
                    break

                # Type the character
                self.controller.type(char)
                char_count += 1

                # Change CPS every ~12 chars for variation
                if char_count % 12 == 0:
                    cps = random.uniform(self.config.min_cps, self.config.max_cps)

                # Calculate base delay
                delay = 1.0 / cps
                
                # Add jitter
                jitter = random.uniform(0, self.config.jitter_ms / 1000.0)
                delay += jitter

                # Wait for the base delay
                await asyncio.sleep(delay)

                # Extra pauses for punctuation and newlines
                if char in punctuation:
                    await asyncio.sleep(self.config.punct_pause_ms / 1000.0)
                elif char == "\n":
                    await asyncio.sleep(self.config.newline_pause_ms / 1000.0)

            if not self.cancel_event.is_set():
                print(f"Finished typing {len(text)} characters")
            
        except Exception as e:
            print(f"Error during typing: {e}")
        finally:
            self.is_typing = False
            self.cancel_event.clear()