import re


def is_blocked(text: str, patterns: list[str]) -> bool:
    """Check if text matches any blocked patterns."""
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False
