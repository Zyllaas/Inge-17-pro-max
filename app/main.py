import argparse
import asyncio
import os
import sys
import threading
import time
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
import logging

from app.ai_client import GroqClient
from app.clipboard import get_clipboard_text, set_clipboard_text
from app.config import load_config
from app.health import run_health_check
from app.hotkeys import HotkeyManager
from app.paste import TypewriterManager
from app.prompts import TemplateManager
from app.secrets_filter import is_blocked


def setup_logging(noconsole: bool = False):
    """Setup logging with rich formatting."""
    if noconsole:
        log_path = Path.home() / "AppData" / "Roaming" / "ClipboardAI" / "logs.txt"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_path)]
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(rich_tracebacks=True)]
        )
    
    return logging.getLogger("ClipboardAI")


class ClipboardAI:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.client = GroqClient(config)
        self.hotkey_manager = HotkeyManager()
        self.typewriter = TypewriterManager(config)
        self.template_manager = TemplateManager()
        self.current_template = "default"
        self.running = True

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
            
            # Optionally copy to clipboard if autopaste is false
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
        """Register all hotkeys."""
        self.hotkey_manager.register(
            self.config.hotkey_send,
            lambda: asyncio.create_task(self.send_flow())
        )
        self.hotkey_manager.register(
            self.config.hotkey_cancel,
            lambda: asyncio.create_task(self.cancel_flow())
        )
        self.hotkey_manager.register(
            self.config.hotkey_list_models,
            lambda: asyncio.create_task(self.list_models_flow())
        )
        self.hotkey_manager.register(
            self.config.hotkey_diagnostics,
            lambda: asyncio.create_task(self.diagnostics_flow())
        )
        self.hotkey_manager.register(
            self.config.hotkey_template_default,
            self.set_template_default
        )
        self.hotkey_manager.register(
            self.config.hotkey_template_translate,
            self.set_template_translate
        )

    async def run(self):
        """Main application loop."""
        self.setup_hotkeys()
        self.logger.info("Clipboard-AI started. Listening for hotkeys...")
        self.logger.info(f"Send: {self.config.hotkey_send}")
        self.logger.info(f"Cancel: {self.config.hotkey_cancel}")
        self.logger.info(f"List Models: {self.config.hotkey_list_models}")
        self.logger.info(f"Diagnostics: {self.config.hotkey_diagnostics}")
        
        # Start hotkey listener in background thread
        hotkey_thread = threading.Thread(target=self.hotkey_manager.start_listening, daemon=True)
        hotkey_thread.start()
        
        # Keep the main loop running
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Shutting down...")
            self.running = False


async def main():
    parser = argparse.ArgumentParser(description="Clipboard-AI: AI-powered clipboard integration")
    parser.add_argument("--noconsole", action="store_true", help="Log to file instead of console")
    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.noconsole)
    
    try:
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Validate API key
        if not config.api_key:
            logger.error("No API key found. Please set GROQ_API_KEY or API_KEY in %APPDATA%\\ClipboardAI\\.env")
            return
        
        # Create and run the application
        app = ClipboardAI(config, logger)
        await app.run()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())