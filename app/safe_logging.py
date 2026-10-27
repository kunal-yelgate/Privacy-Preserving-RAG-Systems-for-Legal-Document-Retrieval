import logging
from typing import Any


class SafeFormatter(logging.Formatter):
    """Formats only structured security-safe fields; callers must pass identifiers, not text."""

    def format(self, record: logging.LogRecord) -> str:
        fields = getattr(record, "safe_fields", {})
        return f"{record.levelname} {record.name} {fields}"


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(SafeFormatter())
    root = logging.getLogger("legal_rag")
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def safe_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    logger.info(event, extra={"safe_fields": {"event": event, **fields}})
