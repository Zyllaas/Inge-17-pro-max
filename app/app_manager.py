import asyncio
import threading
import logging
from typing import Optional
import signal
import sys

from .config import Config
from .ai_client import GroqClient
from .hotkeys import HotkeyManager
from .paste import TypewriterManager
from .prompts import TemplateManager
from .clipboard import get_clipboard_text, set_clipboard_text
from .secrets_filter import is_blocked
from .health import run_health_check


class AppManager:
    """Manages the core application logic separate from GUI."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger("ClipboardAI.Core")
        
        # Core components
        self.client = GroqClient(config)
        self.hotkey_manager = HotkeyManager()
        self.typewriter = TypewriterManager(config)
        self.template_manager = TemplateManager()
        
        # State
        self.current_template = "default"
        self.running = False
        self.hotkey_thread: Optional[threading.Thread] = None
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None

    async def send_flow(self):
        """Handle the send hotkey flow."""
        try:
            self.logger.info("Send hotkey activated")
            
            # Get clipboard text
            text = get_clipboard_text()
            if not text:
                self.logger.warning("Clipboard is empty")
                return
            
            self.logger.info(f"Clipboard text: {text[:50]}...")
            
            # Check privacy filters
            if is_blocked(text, self.config.blocked_patterns):
                self.logger.warning("Content blocked by privacy filter")
                return
            
            # Render template
            prompt = self.template_manager.render_template(self.current_template, text)
            self.logger.info(f"Using template: {self.current_template}")
            
            # Get AI response
            self.logger.info("Sending request to Groq...")
            response = await self.client.complete(prompt)
            self.logger.info(f"Response received: {len(response)} characters")
            
            # Handle response based on autopaste setting
            if not self.config.autopaste:
                set_clipboard_text(response)
                self.logger.info("Response copied to clipboard")
            else:
                # Start typewriting
                await self.typewriter.typewrite(response)
                
        except Exception as e:
            self.logger.error(f"Error in send flow: {e}")

    async def cancel_flow(self):
        """Handle the cancel hotkey flow."""
        self.logger.info("Cancel hotkey activated")
        self.typewriter.cancel()

    async def list_models_flow(self):
        """Handle the list models hotkey flow."""
        try:
            self.logger.info("Listing models...")
            models = await self.client.list_models()
            models_text = "\n".join(models)
            print("Available models:")
            print(models_text)
            set_clipboard_text(models_text)
            self.logger.info(f"Found {len(models)} models, copied to clipboard")
        except Exception as e:
            self.logger.error(f"Error listing models: {e}")

    async def diagnostics_flow(self):
        """Handle the diagnostics hotkey flow."""
        try:
            self.logger.info("Running diagnostics...")
            report = await run_health_check(self.config, self.client)
            print(report)
            set_clipboard_text(report)
            self.logger.info("Diagnostics report copied to clipboard")
        except Exception as e:
            self.logger.error(f"Error in diagnostics: {e}")

    def set_template_default(self):
        """Switch to default template."""
        self.current_template = "default"
        self.logger.info("Switched to default template")

    def set_template_translate(self):
        """Switch to translate template."""
        self.current_template = "translate_es"
        self.logger.info("Switched to translate_es template")

    def setup_hotkeys(self):
        """Register all hotkeys with async wrappers."""
        def async_wrapper(coro_func):
            """Wrapper to run async functions in the event loop."""
            def wrapper():
                if self.event_loop and self.running:
                    asyncio.run_coroutine_threadsafe(coro_func(), self.event_loop)
            return wrapper

        # Register hotkeys
        self.hotkey_manager.register(
            self.config.hotkey_send,
            async_wrapper(self.send_flow)
        )
        self.hotkey_manager.register(
            self.config.hotkey_cancel,
            async_wrapper(self.cancel_flow)
        )
        self.hotkey_manager.register(
            self.config.hotkey_list_models,
            async_wrapper(self.list_models_flow)
        )
        self.hotkey_manager.register(
            self.config.hotkey_diagnostics,
            async_wrapper(self.diagnostics_flow)
        )
        self.hotkey_manager.register(
            self.config.hotkey_template_default,
            self.set_template_default
        )
        self.hotkey_manager.register(
            self.config.hotkey_template_translate,
            self.set_template_translate
        )

    def start_hotkey_listener(self):
        """Start hotkey listener in a separate thread."""
        def hotkey_worker():
            try:
                self.logger.info("Starting hotkey listener...")
                self.hotkey_manager.start_listening()
            except Exception as e:
                self.logger.error(f"Hotkey listener error: {e}")

        self.hotkey_thread = threading.Thread(target=hotkey_worker, daemon=True)
        self.hotkey_thread.start()

    async def start_async(self):
        """Start the async components."""
        self.running = True
        self.event_loop = asyncio.get_running_loop()
        
        # Setup and start hotkeys
        self.setup_hotkeys()
        self.start_hotkey_listener()
        
        self.logger.info("Clipboard-AI core started")
        self.logger.info(f"Send: {self.config.hotkey_send}")
        self.logger.info(f"Cancel: {self.config.hotkey_cancel}")
        self.logger.info(f"List Models: {self.config.hotkey_list_models}")
        self.logger.info(f"Diagnostics: {self.config.hotkey_diagnostics}")
        
        # Keep running
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            self.logger.info("Async loop cancelled")

    def stop(self):
        """Stop the application."""
        self.logger.info("Stopping Clipboard-AI...")
        self.running = False
        
        # Stop typewriter
        self.typewriter.cancel()
        
        # Stop hotkey listener
        if self.hotkey_manager:
            self.hotkey_manager.stop_listening()
        
        self.logger.info("Clipboard-AI stopped")

    def get_status(self) -> dict:
        """Get current application status."""
        return {
            "running": self.running,
            "current_template": self.current_template,
            "api_key_set": bool(self.config.api_key),
            "model": self.config.model,
            "autopaste": self.config.autopaste,
            "hotkeys_active": self.hotkey_thread and self.hotkey_thread.is_alive() if self.hotkey_thread else False
        }

    async def test_connection(self) -> tuple[bool, str]:
        """Test API connection and return status."""
        try:
            models = await self.client.list_models()
            if models:
                return True, f"Connected - {len(models)} models available"
            else:
                return False, "No models available"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    async def get_models(self) -> list[str]:
        """Get available models."""
        try:
            return await self.client.list_models()
        except Exception as e:
            self.logger.error(f"Failed to get models: {e}")
            return []

    async def run_health_check(self) -> str:
        """Run and return health check report."""
        try:
            return await run_health_check(self.config, self.client)
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return f"Health check failed: {str(e)}"

    def update_config(self, new_config: Config):
        """Update configuration and reinitialize components."""
        self.config = new_config
        self.client = GroqClient(new_config)
        self.typewriter = TypewriterManager(new_config)
        self.logger.info("Configuration updated")