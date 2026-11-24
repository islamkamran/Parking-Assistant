import hashlib
import hmac

from fastapi import Header, HTTPException, status

from app.config import settings


def require_api_key(x_api_key: str = Header(..., description="API key for the agent")) -> None:
    """Dependency for agent-facing endpoints. compare_digest avoids leaking the key via timing."""
    if not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def sign(body: bytes) -> str:
    """HMAC-SHA256 of the raw body: what a real gateway puts in its signature header."""
    return hmac.new(settings.webhook_secret.encode(), body, hashlib.sha256).hexdigest()


def verify_signature(body: bytes, signature: str) -> bool:
    return hmac.compare_digest(signature or "", sign(body))
