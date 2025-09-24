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