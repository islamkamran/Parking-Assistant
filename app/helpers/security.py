import hashlib
import hmac

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings

# Security schemes (not plain Header params) so that:
#   - /docs shows an "Authorize" button where you type the key once, and
#   - the OpenAPI file declares the key, which Power Platform custom connectors understand.
# auto_error=False: we raise our own 401 for a missing key instead of FastAPI's default 403.
# scheme_name must differ, or both schemes share the default name "APIKeyHeader" and one overwrites the other.
agent_key_scheme = APIKeyHeader(name="x-api-key", scheme_name="AgentKey",
                                description="API key for the agent", auto_error=False)
admin_key_scheme = APIKeyHeader(name="x-admin-key", scheme_name="AdminKey",
                                description="Admin key (staff only)", auto_error=False)


def require_api_key(x_api_key: str | None = Security(agent_key_scheme)) -> None:
    """Dependency for agent-facing endpoints. compare_digest avoids leaking the key via timing."""
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")


def require_admin_key(x_admin_key: str | None = Security(admin_key_scheme)) -> None:
    """Separate key for admin endpoints. The agent's key can't create or delete fines (least privilege)."""
    if not x_admin_key or not hmac.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing admin key")


def sign(body: bytes) -> str:
    """HMAC-SHA256 of the raw body: what a real gateway puts in its signature header."""
    return hmac.new(settings.webhook_secret.encode(), body, hashlib.sha256).hexdigest()


def verify_signature(body: bytes, signature: str) -> bool:
    return hmac.compare_digest(signature or "", sign(body))
