"""
Safe filesystem operations for storing, hashing, validating, and quarantining documents.
Prevents path traversal and unrestricted file access.
"""
import hashlib
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Tuple

from backend.app.core.config import settings
from backend.app.core.exceptions import InvalidRequestError, UnsupportedDocumentError
from backend.app.core.logging import logger


class SafeFileManager:
    """Manages secure file storage within authorized workspace roots."""

    SAFE_FILENAME_REGEX = re.compile(r"[^a-zA-Z0-9_\-\.]")

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Strips dangerous characters, consecutive dots, and directory separators from user-supplied filenames."""
        base_name = os.path.basename(filename)
        sanitized = cls.SAFE_FILENAME_REGEX.sub("_", base_name)
        # Collapse multiple consecutive dots into a single dot
        sanitized = re.sub(r"\.{2,}", ".", sanitized)
        # Prevent hidden files or empty filenames
        sanitized = sanitized.lstrip(".")
        if not sanitized:
            sanitized = f"doc_{uuid.uuid4().hex[:8]}"
        return sanitized[:120]

    @classmethod
    def validate_file_path(cls, file_path: Path, allowed_root: Path) -> Path:
        """
        Validates that a resolved file path is strictly located within the allowed root directory.
        Protects against Directory Traversal attacks (e.g., ../../etc/passwd).
        """
        resolved_target = file_path.resolve()
        resolved_root = allowed_root.resolve()
        if not str(resolved_target).startswith(str(resolved_root)):
            logger.warning(f"Path traversal attempt detected: {file_path}")
            raise InvalidRequestError("Invalid file path: Access outside authorized storage root is forbidden.")
        return resolved_target

    @classmethod
    def compute_sha256(cls, content: bytes) -> str:
        """Computes cryptographic SHA-256 hash for document integrity and duplicate detection."""
        return hashlib.sha256(content).hexdigest()

    @classmethod
    def save_original(cls, filename: str, content: bytes) -> Tuple[str, Path, str]:
        """
        Saves uploaded file to originals directory with a generated safe internal document ID.
        Returns: (document_id, saved_path, content_hash)
        """
        if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise InvalidRequestError(
                f"File size exceeds maximum permitted limit of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)} MB."
            )

        content_hash = cls.compute_sha256(content)
        document_id = f"doc_{uuid.uuid4().hex}"
        clean_name = cls.sanitize_filename(filename)
        internal_filename = f"{document_id}_{clean_name}"

        target_path = settings.originals_path / internal_filename
        cls.validate_file_path(target_path, settings.originals_path)

        target_path.write_bytes(content)
        logger.info(f"Safely stored original document {clean_name} (internal_id={document_id}, size={len(content)})")
        return document_id, target_path, content_hash

    @classmethod
    def quarantine_file(cls, original_path: Path, reason: str) -> Path:
        """Moves corrupted, malicious, or unreadable files to quarantine."""
        cls.validate_file_path(original_path, settings.originals_path)
        quarantine_target = settings.quarantine_path / original_path.name
        cls.validate_file_path(quarantine_target, settings.quarantine_path)

        if original_path.exists():
            shutil.move(str(original_path), str(quarantine_target))
            meta_path = quarantine_target.with_suffix(".quarantine_meta.txt")
            meta_path.write_text(f"Reason: {reason}\nTimestamp: {uuid.uuid4().hex}\n", encoding="utf-8")
            logger.warning(f"Quarantined document {original_path.name}: {reason}")
        return quarantine_target

    @classmethod
    def delete_document_file(cls, file_path: Path) -> bool:
        """Securely deletes a document file from storage."""
        cls.validate_file_path(file_path, settings.root_path)
        if file_path.exists():
            file_path.unlink()
            return True
        return False
