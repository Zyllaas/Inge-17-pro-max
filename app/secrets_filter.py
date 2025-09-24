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
