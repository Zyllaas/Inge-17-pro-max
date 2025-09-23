import os
from dataclasses import dataclass
from pathlib import Path
import tomli as tomllib
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
    blocked_patterns: list[str]

    # Environment
    api_base: str
    api_key: str
    model: str


def load_config() -> Config:
    appdata_dir = Path(os.environ.get('APPDATA', '')) / 'ClipboardAI'
    appdata_dir.mkdir(parents=True, exist_ok=True)

    # Load config.toml
    config_path = appdata_dir / 'config.toml'
    if not config_path.exists():
        config_path = Path(resource_path('config.toml'))

    with open(config_path, 'rb') as f:
        config_data = tomllib.load(f)

    # Load .env
    env_path = appdata_dir / '.env'
    if not env_path.exists():
        env_path = Path(resource_path('.env.example'))

    load_dotenv(env_path)

    api_key_env = os.getenv('API_KEY') or os.getenv('GROQ_API_KEY')
    api_key = api_key_env if api_key_env else ''
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


def save_env(api_key: str, model: str) -> None:
    appdata_dir = Path(os.environ.get('APPDATA', '')) / 'ClipboardAI'
    appdata_dir.mkdir(parents=True, exist_ok=True)
    env_path = appdata_dir / '.env'
    with open(env_path, 'w') as f:
        f.write(f'API_KEY={api_key}\n')
        f.write(f'MODEL={model}\n')
        f.write('API_BASE=https://api.groq.com/openai/v1\n')