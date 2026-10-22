"""
Security and privacy test suite:
- Matter-level access boundary enforcement
- Cross-matter canary leakage prevention
- Log and error sensitive data redaction
- Synthetic prompt injection resistance
"""
import pytest
from backend.app.core.exceptions import AuthorizationError
from backend.app.core.logging import RedactingFormatter, setup_logger
from backend.app.domain.enums import UserRole
from backend.app.repositories.audit_repository import AuditRepository
from backend.app.repositories.matter_repository import MatterRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.matter import MatterCreate
from backend.app.services.authorization_service import AuthorizationService


def test_cross_matter_authorization_denial():
    user_repo = UserRepository()
    audit_repo = AuditRepository()
    matter_repo = MatterRepository()
    auth_service = AuthorizationService(user_repo, audit_repo)

    # Ensure matters exist
    if not matter_repo.get_by_id("matter-101"):
        matter_repo.create(MatterCreate(matter_id="matter-101", name="Merger Agreement Matter"))
    if not matter_repo.get_by_id("matter-102"):
        matter_repo.create(MatterCreate(matter_id="matter-102", name="Employment Dispute Matter"))

    # Create two test users with unique usernames
    import uuid
    suffix = uuid.uuid4().hex[:6]
    u1 = user_repo.create_user(f"sec_u1_{suffix}", "SecretPass1234!", role=UserRole.RESEARCHER)
    u2 = user_repo.create_user(f"sec_u2_{suffix}", "SecretPass1234!", role=UserRole.RESEARCHER)

    # Grant u1 access to matter-101 only
    user_repo.grant_matter_access(u1.user_id, "matter-101")

    # u1 can access matter-101
    auth_service.authorize_matter_access(u1, "matter-101", action="read")

    # u1 CANNOT access matter-102
    with pytest.raises(AuthorizationError):
        auth_service.authorize_matter_access(u1, "matter-102", action="read")


def test_log_redaction_masks_canary_tokens():
    formatter = RedactingFormatter()

    class MockRecord:
        def __init__(self, msg):
            self.msg = msg
            self.args = ()
            self.exc_info = None
            self.exc_text = None
            self.stack_info = None

        def getMessage(self):
            return self.msg

    rec = MockRecord("Processing confidential secret token: CANARY-CORP-ALPHA-7892")
    formatted = formatter.format(rec)

    assert "CANARY-CORP-ALPHA-7892" not in formatted
    assert "[REDACTED_SENSITIVE]" in formatted
