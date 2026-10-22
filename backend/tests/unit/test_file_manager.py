"""
Unit tests for safe filesystem operations and path traversal defenses.
"""
from pathlib import Path
import pytest
from backend.app.core.config import settings
from backend.app.core.exceptions import InvalidRequestError
from backend.app.infrastructure.filesystem.file_manager import SafeFileManager


def test_sanitize_filename():
    dangerous = "../../malicious/test..exe"
    sanitized = SafeFileManager.sanitize_filename(dangerous)
    assert "/" not in sanitized
    assert "\\" not in sanitized
    assert ".." not in sanitized


def test_validate_file_path_traversal():
    allowed_root = settings.originals_path
    traversal_path = allowed_root / ".." / ".." / "secret.txt"

    with pytest.raises(InvalidRequestError):
        SafeFileManager.validate_file_path(traversal_path, allowed_root)


def test_sha256_computation():
    data = b"Confidential Legal Agreement"
    hash1 = SafeFileManager.compute_sha256(data)
    hash2 = SafeFileManager.compute_sha256(data)
    assert hash1 == hash2
    assert len(hash1) == 64
