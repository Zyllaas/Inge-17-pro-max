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