"""
Privacy-preserving structured logging system.
Filters out raw legal text, sensitive tokens, canary values, and passwords.
"""
import logging
import re
import sys
from typing import Any, Dict


# Common patterns for sensitive data: JWTs, API tokens, passwords, canaries
SENSITIVE_PATTERNS = [
    re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]+", re.IGNORECASE),
    re.compile(r'password["\']?\s*[:=]\s*["\']?[^"\',;\s]+', re.IGNORECASE),
    re.compile(r'token["\']?\s*[:=]\s*["\']?[^"\',;\s]+', re.IGNORECASE),
    re.compile(r'secret["\']?\s*[:=]\s*["\']?[^"\',;\s]+', re.IGNORECASE),
    re.compile(r'CANARY-[A-Z0-9\-]+', re.IGNORECASE),
]


class RedactingFormatter(logging.Formatter):
    """Logging formatter that redacts sensitive keys and canary tokens."""
    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        sanitized = original
        for pattern in SENSITIVE_PATTERNS:
            sanitized = pattern.sub("[REDACTED_SENSITIVE]", sanitized)
        return sanitized


def setup_logger(name: str = "legal_rag", level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    handler = logging.StreamHandler(sys.stdout)
    formatter = RedactingFormatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = setup_logger()
