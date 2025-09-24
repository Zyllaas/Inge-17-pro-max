# Clipboard-AI: Complete Recreation Guide

A Windows desktop application that integrates AI clipboard processing with global hotkeys for seamless text enhancement and translation.

## Overview

Clipboard-AI is a Python-based Windows application that monitors clipboard content and provides AI-powered text processing through global hotkeys. It features human-like typing simulation, privacy filtering, and template-based prompts.

## Features

- **Global Hotkeys**: Process clipboard content with customizable keyboard shortcuts
- **AI Integration**: Groq API integration with multiple model support
- **Human-like Typing**: Realistic typing simulation with configurable speed and pauses
- **Privacy Protection**: Automatic filtering of sensitive information
- **Template System**: Jinja2-based prompt templates for different use cases
- **System Tray**: Background operation with tray icon
- **Comprehensive Diagnostics**: Built-in health checking and troubleshooting

## Requirements

- **Python**: 3.9 or higher
- **Windows**: 10/11 (64-bit)
- **API Key**: Groq API key (https://console.groq.com/)

## Project Structure

```
clipboard-ai/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main application entry point
│   ├── ai_client.py         # Groq API client
│   ├── config.py            # Configuration management
│   ├── clipboard.py         # Clipboard operations
│   ├── health.py            # Diagnostics and health checks
│   ├── hotkeys.py           # Global hotkey management
│   ├── paste.py             # Typewriter simulation
│   ├── prompts.py           # Template management
│   ├── secrets_filter.py    # Privacy filtering
│   └── utils/
│       └── paths.py         # Path utilities for PyInstaller
├── templates/
│   ├── default.j2           # Default processing template
│   └── translate_es.j2      # Spanish translation template
├── tests/
│   ├── setup.py
│   └── tests_comprehensive.py
├── config.toml              # Application configuration
├── requirements.txt         # Python dependencies
├── build.bat               # Build script
├── installer.iss           # Inno Setup installer script
├── .env.example            # Environment variables template
├── .gitignore
└── README.md
```

## Installation & Setup

### 1. Create Project Directory

```bash
mkdir clipboard-ai
cd clipboard-ai
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

Create `requirements.txt`:

```
httpx[http2]==0.27.2
pyperclip==1.8.2
pynput==1.7.7
Jinja2==3.1.4
python-dotenv==1.0.1
tenacity==9.0.0
rich==13.8.0
tomli==2.0.1
pillow==10.0.1
```

Install dependencies:

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 4. Create Application Directory Structure

```bash
mkdir app
mkdir app\utils
mkdir templates
mkdir tests
```

## Source Code Files

### app/__init__.py

```python
# Empty init file
```

### app/main.py

```python
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
```

### app/ai_client.py

```python
import asyncio
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List

from .config import Config


class GroqClient:
    def __init__(self, config: Config):
        self.config = config
        self.timeout = httpx.Timeout(config.timeout_seconds)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=6),
        reraise=True,
    )
    async def list_models(self) -> List[str]:
        """Get list of available models from Groq API."""
        url = f"{self.config.api_base}/models"
        headers = {"Authorization": f"Bearer {self.config.api_key}"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return [model["id"] for model in data["data"]]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=6),
        reraise=True,
    )
    async def complete(self, prompt: str) -> str:
        """Get completion from Groq API."""
        url = f"{self.config.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        body = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": "You are a helpful, concise assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=6),
        reraise=True,
    )
    async def test_completion(self, test_prompt: str = "Respond exactly: pong: ok") -> tuple[str, int]:
        """Test completion with latency measurement."""
        import time
        start_time = time.time()
        response = await self.complete(test_prompt)
        latency_ms = int((time.time() - start_time) * 1000)
        return response, latency_ms
```

### app/config.py

```python
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List
import tomllib
from dotenv import load_dotenv

from .utils.paths import resource_path


@dataclass
class Config:
    # App hotkeys
    hotkey_send: str
    hotkey_cancel: str
    hotkey_list_models: str
    hotkey_diagnostics: str
    hotkey_template_default: str
    hotkey_template_translate: str
    autopaste: bool

    # Typewriter settings
    min_cps: int
    max_cps: int
    jitter_ms: int
    punct_pause_ms: int
    newline_pause_ms: int
    preserve_clipboard: bool

    # API settings
    timeout_seconds: int
    max_retries: int

    # Privacy
    blocked_patterns: List[str]

    # Environment
    api_base: str
    api_key: str
    model: str


def get_appdata_dir() -> Path:
    """Get the application data directory."""
    appdata = os.environ.get('APPDATA', str(Path.home() / 'AppData' / 'Roaming'))
    return Path(appdata) / 'ClipboardAI'


def load_config() -> Config:
    """Load configuration from TOML and environment files."""
    appdata_dir = get_appdata_dir()
    appdata_dir.mkdir(parents=True, exist_ok=True)

    # Load config.toml (prefer user's copy, fallback to bundled)
    config_path = appdata_dir / 'config.toml'
    if not config_path.exists():
        bundled_config = Path(resource_path('config.toml'))
        if bundled_config.exists():
            import shutil
            shutil.copy2(bundled_config, config_path)
        else:
            config_path = bundled_config

    with open(config_path, 'rb') as f:
        config_data = tomllib.load(f)

    # Load .env (prefer user's copy, fallback to bundled)
    env_path = appdata_dir / '.env'
    if not env_path.exists():
        bundled_env = Path(resource_path('.env.example'))
        if bundled_env.exists():
            import shutil
            shutil.copy2(bundled_env, env_path)
        else:
            env_path = bundled_env

    load_dotenv(env_path)

    # Get environment variables
    api_key = os.getenv('API_KEY') or os.getenv('GROQ_API_KEY') or ''
    api_base = os.getenv('API_BASE', 'https://api.groq.com/openai/v1')
    model = os.getenv('MODEL', 'llama-3.1-8b-instant')

    return Config(
        hotkey_send=config_data['app']['hotkey_send'],
        hotkey_cancel=config_data['app']['hotkey_cancel'],
        hotkey_list_models=config_data['app']['hotkey_list_models'],
        hotkey_diagnostics=config_data['app']['hotkey_diagnostics'],
        hotkey_template_default=config_data['app']['hotkey_template_default'],
        hotkey_template_translate=config_data['app']['hotkey_template_translate'],
        autopaste=config_data['app']['autopaste'],
        min_cps=config_data['typewriter']['min_cps'],
        max_cps=config_data['typewriter']['max_cps'],
        jitter_ms=config_data['typewriter']['jitter_ms'],
        punct_pause_ms=config_data['typewriter']['punct_pause_ms'],
        newline_pause_ms=config_data['typewriter']['newline_pause_ms'],
        preserve_clipboard=config_data['typewriter']['preserve_clipboard'],
        timeout_seconds=config_data['api']['timeout_seconds'],
        max_retries=config_data['api']['max_retries'],
        blocked_patterns=config_data['privacy']['blocked_patterns'],
        api_base=api_base,
        api_key=api_key,
        model=model,
    )


def save_env_file(api_key: str, model: str, api_base: str = None) -> None:
    """Save environment variables to .env file."""
    appdata_dir = get_appdata_dir()
    appdata_dir.mkdir(parents=True, exist_ok=True)

    env_path = appdata_dir / '.env'

    if api_base is None:
        api_base = 'https://api.groq.com/openai/v1'

    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(f'API_BASE={api_base}\n')
        f.write(f'GROQ_API_KEY={api_key}\n')
        f.write(f'MODEL={model}\n')
```

### app/clipboard.py

```python
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
```

### app/health.py

```python
import asyncio
import socket
from urllib.parse import urlparse
import httpx

from .ai_client import GroqClient
from .config import Config


async def run_health_check(config: Config, client: GroqClient) -> str:
    """Run comprehensive diagnostics and return formatted report."""
    report_lines = []
    overall_status = "OK"
    warnings = []
    failures = []

    # Helper function to add check result
    def add_check(name: str, status: str, details: str = ""):
        nonlocal overall_status
        result = f"{name}: {status}"
        if details:
            result += f" - {details}"
        report_lines.append(result)

        if status == "FAIL":
            failures.append(name)
            overall_status = "FAIL"
        elif status == "WARN":
            warnings.append(name)
            if overall_status == "OK":
                overall_status = "WARN"

    # 1. ENV Check
    try:
        if config.api_key:
            add_check("ENV", "OK", "API key present")
        else:
            add_check("ENV", "FAIL", "No API key found")
    except Exception as e:
        add_check("ENV", "FAIL", str(e))

    # 2. API_BASE Check
    try:
        parsed_url = urlparse(config.api_base)
        if parsed_url.scheme == "https" and parsed_url.netloc:
            # Test DNS resolution
            socket.gethostbyname(parsed_url.netloc)
            add_check("API_BASE", "OK", f"{config.api_base}")
        else:
            add_check("API_BASE", "FAIL", "Invalid URL format")
    except socket.gaierror:
        add_check("API_BASE", "FAIL", "DNS resolution failed")
    except Exception as e:
        add_check("API_BASE", "FAIL", str(e))

    # 3. AUTH Check (implicit with models call)
    auth_status = "PENDING"

    # 4. MODELS Check
    models = []
    try:
        models = await client.list_models()
        if models:
            add_check("MODELS", "OK", f"Found {len(models)} models")
            auth_status = "OK"
        else:
            add_check("MODELS", "FAIL", "No models returned")
            auth_status = "FAIL"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            add_check("MODELS", "FAIL", "Authentication failed")
            auth_status = "FAIL"
        elif e.response.status_code == 429:
            add_check("MODELS", "WARN", "Rate limited")
            auth_status = "WARN"
        elif 500 <= e.response.status_code < 600:
            add_check("MODELS", "WARN", f"Server error {e.response.status_code}")
            auth_status = "WARN"
        else:
            add_check("MODELS", "FAIL", f"HTTP {e.response.status_code}")
            auth_status = "FAIL"
    except Exception as e:
        add_check("MODELS", "FAIL", str(e))
        auth_status = "FAIL"

    # Add AUTH check result
    add_check("AUTH", auth_status)

    # 5. MODEL ACTIVE Check
    if models and config.model in models:
        add_check("MODEL ACTIVE", "OK", config.model)
    elif models:
        add_check("MODEL ACTIVE", "WARN", f"{config.model} not in available models")
    else:
        add_check("MODEL ACTIVE", "FAIL", "Cannot verify - no models available")

    # 6. COMPLETION Check
    completion_status = "FAIL"
    latency_ms = 0
    try:
        response, latency_ms = await client.test_completion()
        if "pong: ok" in response.lower():
            add_check("COMPLETION", "OK", f"{latency_ms}ms")
        else:
            add_check("COMPLETION", "FAIL", f"Invalid response: {response[:50]}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            add_check("COMPLETION", "WARN", "Rate limited")
        elif 500 <= e.response.status_code < 600:
            add_check("COMPLETION", "WARN", f"Server error {e.response.status_code}")
        else:
            add_check("COMPLETION", "FAIL", f"HTTP {e.response.status_code}")
    except Exception as e:
        add_check("COMPLETION", "FAIL", str(e))

    # 7. RATE-LIMIT Check (based on previous calls)
    rate_limit_issues = any("Rate limited" in line for line in report_lines)
    if rate_limit_issues:
        add_check("RATE-LIMIT", "WARN", "Rate limiting detected")
    else:
        add_check("RATE-LIMIT", "OK")

    # 8. SERVER Check (based on previous calls)
    server_issues = any("Server error" in line for line in report_lines)
    if server_issues:
        add_check("SERVER", "WARN", "Server issues detected")
    else:
        add_check("SERVER", "OK")

    # Final HEALTH summary
    report_lines.append("-" * 50)
    if overall_status == "FAIL":
        add_check("HEALTH", "FAIL", f"Critical issues: {', '.join(failures)}")
    elif overall_status == "WARN":
        add_check("HEALTH", "WARN", f"Warnings: {', '.join(warnings)}")
    else:
        add_check("HEALTH", "OK", "All systems operational")

    # Add summary
    report_lines.append("")
    report_lines.append(f"Config: {config.model} @ {config.api_base}")
    if latency_ms > 0:
        report_lines.append(f"Response time: {latency_ms}ms")

    return "\n".join(report_lines)
```

### app/hotkeys.py

```python
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
```

### app/paste.py

```python
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
```

### app/prompts.py

```python
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from pathlib import Path

from .utils.paths import resource_path


class TemplateManager:
    def __init__(self):
        self.templates_dir = resource_path("templates")
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))

    def render_template(self, template_name: str, content: str) -> str:
        """Render the prompt using the specified Jinja2 template."""
        try:
            template_file = f"{template_name}.j2"
            template = self.env.get_template(template_file)
            return template.render(content=content)
        except TemplateNotFound:
            print(f"Template {template_name}.j2 not found, using content as-is")
            return content
        except Exception as e:
            print(f"Error rendering template {template_name}: {e}")
            return content

    def list_templates(self) -> list[str]:
        """List available templates."""
        try:
            templates_path = Path(self.templates_dir)
            if templates_path.exists():
                return [f.stem for f in templates_path.glob("*.j2")]
            return []
        except Exception as e:
            print(f"Error listing templates: {e}")
            return []

    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists."""
        try:
            template_file = f"{template_name}.j2"
            self.env.get_template(template_file)
            return True
        except TemplateNotFound:
            return False
        except Exception:
            return False
```

### app/secrets_filter.py

```python
import re
from typing import List


def is_blocked(text: str, patterns: List[str]) -> bool:
    """
    Check if text matches any blocked patterns.

    Args:
        text: The text to check
        patterns: List of regex patterns to match against

    Returns:
        True if text should be blocked, False otherwise
    """
    if not text or not patterns:
        return False

    try:
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    except re.error as e:
        print(f"Invalid regex pattern in blocked_patterns: {e}")
        return False


def get_matched_pattern(text: str, patterns: List[str]) -> str:
    """
    Get the first pattern that matches the text.

    Args:
        text: The text to check
        patterns: List of regex patterns to match against

    Returns:
        The matched pattern, or empty string if no match
    """
    if not text or not patterns:
        return ""

    try:
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return pattern
        return ""
    except re.error as e:
        print(f"Invalid regex pattern in blocked_patterns: {e}")
        return ""


def validate_patterns(patterns: List[str]) -> List[str]:
    """
    Validate regex patterns and return only valid ones.

    Args:
        patterns: List of regex patterns to validate

    Returns:
        List of valid regex patterns
    """
    valid_patterns = []
    for pattern in patterns:
        try:
            re.compile(pattern)
            valid_patterns.append(pattern)
        except re.error as e:
            print(f"Invalid regex pattern '{pattern}': {e}")

    return valid_patterns


# Common sensitive patterns for reference
DEFAULT_BLOCKED_PATTERNS = [
    r"sk-[A-Za-z0-9]{20,}",  # OpenAI API keys
    r"password\s*=\s*\S+",   # Password assignments
    r"Authorization:\s*Bearer\s+\S+",  # Bearer tokens
    r"api_key\s*=\s*\S+",    # API key assignments
    r"secret\s*=\s*\S+",     # Secret assignments
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email addresses (optional)
    r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # Credit card numbers (basic pattern)
]
```

### app/utils/paths.py

```python
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
```

## Configuration Files

### config.toml

```toml
[app]
hotkey_send = "ctrl+alt+enter"
hotkey_cancel = "ctrl+alt+backspace"
hotkey_list_models = "ctrl+alt+f8"
hotkey_diagnostics = "ctrl+alt+f9"
hotkey_template_default = "ctrl+alt+1"
hotkey_template_translate = "ctrl+alt+2"
autopaste = true

[typewriter]
min_cps = 8
max_cps = 15
jitter_ms = 50
punct_pause_ms = 200
newline_pause_ms = 300
preserve_clipboard = true

[api]
timeout_seconds = 30
max_retries = 3

[privacy]
blocked_patterns = [
    "sk-[A-Za-z0-9]{20,}",
    "password\\s*=\\s*\\S+", 
    "Authorization:\\s*Bearer\\s+\\S+",
    "api_key\\s*=\\s*\\S+",
    "secret\\s*=\\s*\\S+"
]
```

### .env.example

```
API_BASE=https://api.groq.com/openai/v1
GROQ_API_KEY=your_groq_api_key_here
MODEL=llama-3.1-8b-instant
```

## Template Files

### templates/default.j2

```
Please improve and enhance the following text while maintaining its original meaning and intent:

{{ content }}

Make it more professional, clear, and well-structured. Keep the same language and tone.
```

### templates/translate_es.j2

```
Please translate the following text to Spanish, maintaining a natural and fluent translation:

{{ content }}

Provide only the translated text without any additional comments or explanations.
```

## Build Scripts

### build.bat

```batch
@echo off
echo Building Clipboard-AI...

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade pip and dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

REM Build the executable
echo Building executable...
pyinstaller ^
    --name ClipboardAI ^
    --onefile ^
    --noconsole ^
    --add-data "templates;templates" ^
    --add-data "config.toml;." ^
    --add-data ".env.example;." ^
    --distpath dist ^
    --workpath build ^
    app/main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build completed successfully!
    echo Executable: dist\ClipboardAI.exe
    echo.
    if exist dist\ClipboardAI.exe (
        echo File size: 
        dir dist\ClipboardAI.exe | findstr ClipboardAI.exe
    )
) else (
    echo.
    echo Build failed with error code %ERRORLEVEL%
)
```

## Additional Files

### .gitignore

```
# Virtual environment
venv/
env/

# Build artifacts
build/
dist/
*.spec

# Python cache
__pycache__/
*.pyc
*.pyo

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# User data (should be in %APPDATA%)
ClipboardAI/
```

### installer.iss (Inno Setup Script)

```iss
[Setup]
AppName=Clipboard-AI
AppVersion=1.0.0
DefaultDirName={pf}\Clipboard-AI
DefaultGroupName=Clipboard-AI
OutputDir=installer
OutputBaseFilename=ClipboardAI_Installer
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\ClipboardAI.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.toml"; DestDir: "{app}"; Flags: ignoreversion
Source: ".env.example"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Clipboard-AI"; Filename: "{app}\ClipboardAI.exe"
Name: "{group}\Uninstall Clipboard-AI"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\ClipboardAI.exe"; Description: "Launch Clipboard-AI"; Flags: nowait postinstall skipifsilent
```

## Usage Instructions

### 1. Setup API Key

1. Get a Groq API key from https://console.groq.com/
2. Create `%APPDATA%\ClipboardAI\.env` file
3. Add your API key: `GROQ_API_KEY=your_key_here`

### 2. Configure Hotkeys (Optional)

Edit `%APPDATA%\ClipboardAI\config.toml` to customize hotkeys and settings.

### 3. Run the Application

```bash
# From source
python app/main.py

# Or run the built executable
ClipboardAI.exe
```

### 4. Using the App

- **Copy text** to clipboard
- Press `Ctrl+Alt+Enter` to send to AI for processing
- The enhanced text will be typed automatically
- Press `Ctrl+Alt+Backspace` to cancel typing
- Press `Ctrl+Alt+F8` to list available models
- Press `Ctrl+Alt+F9` for diagnostics
- Press `Ctrl+Alt+1` for default template
- Press `Ctrl+Alt+2` for translation template

## Testing

### Run Tests

```bash
python -m pytest tests/
```

### Manual Testing

1. Run diagnostics: `Ctrl+Alt+F9`
2. Test model listing: `Ctrl+Alt+F8`
3. Test text processing with various inputs
4. Test cancellation during typing

## Troubleshooting

### Common Issues

1. **No API key found**: Ensure `.env` file exists in `%APPDATA%\ClipboardAI\` with `GROQ_API_KEY=your_key`
2. **Hotkeys not working**: Check if another application is using the same hotkeys
3. **Typing too fast/slow**: Adjust `min_cps` and `max_cps` in config.toml
4. **Privacy filter blocking content**: Check blocked_patterns in config.toml

### Logs

Check logs at `%APPDATA%\ClipboardAI\logs.txt` for debugging information.

## Development Notes

- The app uses asyncio for async operations
- Hotkey listening runs in a separate thread
- Configuration is loaded from user directory with bundled fallbacks
- PyInstaller is used for building standalone executables
- Jinja2 templates allow for flexible prompt customization

This comprehensive guide contains everything needed to recreate the Clipboard-AI application from scratch.