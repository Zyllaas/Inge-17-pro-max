import socket
import time
from urllib.parse import urlparse
import httpx

from .ai_client import GroqClient
from .config import Config


def run_health_check(config: Config, client: GroqClient) -> str:
    """Run diagnostics and return report string."""
    report_lines = []
    overall = "OK"
    rate_limit_warn = False
    server_warn = False
    model_active_warn = False

    # ENV
    env_status = "OK" if config.api_key else "FAIL"
    if env_status == "FAIL":
        overall = "FAIL"
    report_lines.append(f"ENV: {env_status}")

    # API_BASE
    api_base_status = "FAIL"
    try:
        parsed = urlparse(config.api_base)
        if parsed.scheme == "https" and parsed.netloc:
            socket.gethostbyname(parsed.netloc)
            api_base_status = "OK"
    except Exception:
        pass
    if api_base_status == "FAIL":
        overall = "FAIL"
    report_lines.append(f"API_BASE: {api_base_status}")

    # MODELS
    models_status = "FAIL"
    models = []
    try:
        models = client.list_models()
        if models:
            models_status = "OK"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            rate_limit_warn = True
        elif 500 <= e.response.status_code < 600:
            server_warn = True
    except Exception:
        pass
    if models_status == "FAIL":
        overall = "FAIL"
    report_lines.append(f"MODELS: {models_status}")

    # MODEL ACTIVE
    model_active_status = "WARN" if config.model not in models else "OK"
    if model_active_status == "WARN":
        model_active_warn = True
    report_lines.append(f"MODEL ACTIVE: {model_active_status}")

    # COMPLETION
    completion_status = "FAIL"
    latency = 0
    try:
        start = time.time()
        response = client.complete("Respond exactly: pong: ok")
        latency = int((time.time() - start) * 1000)
        if "pong: ok" in response:
            completion_status = "OK"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            rate_limit_warn = True
        elif 500 <= e.response.status_code < 600:
            server_warn = True
    except Exception:
        pass
    if completion_status == "FAIL":
        overall = "FAIL"
    report_lines.append(f"COMPLETION: {completion_status} ({latency}ms)")

    # RATE-LIMIT
    rate_limit_status = "WARN" if rate_limit_warn else "OK"
    report_lines.append(f"RATE-LIMIT: {rate_limit_status}")

    # SERVER
    server_status = "WARN" if server_warn else "OK"
    report_lines.append(f"SERVER: {server_status}")

    # Overall
    if overall == "OK" and (rate_limit_warn or server_warn or model_active_warn):
        overall = "WARN"
    report_lines.append(f"HEALTH: {overall}")

    return "\n".join(report_lines)
