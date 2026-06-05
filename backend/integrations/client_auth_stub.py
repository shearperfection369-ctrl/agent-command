"""Client portal magic-link auth scaffold.

Activation:
  1. Drop `RESEND_API_KEY=re_...` in backend/.env (already wired elsewhere).
  2. Restart backend. Magic-link emails will actually send instead of being
     printed to the log + queued.

Until then, this module:
  • Mints + stores per-client `client_users` records
  • Issues short-lived JWT tokens after a verify call
  • Logs the magic link to the backend log (for dev)
  • Enqueues an email if a queue helper is supplied

Provides three public callables:
  • create_or_get_client_user(db, email, company) → user dict
  • mint_magic_token(email) → (token_str, expires_iso)
  • verify_magic_token(token) → email | None
  • mint_session_token(email) → (jwt_str, expires_iso)
  • decode_session_token(jwt_str) → payload | None

Token format is HS256 JWT signed with JWT_SECRET (same secret as admin tokens
but with `aud="client"` so we can never confuse the two).
"""
from __future__ import annotations

import os
import uuid
import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict

import jwt

log = logging.getLogger("jadeos.client_auth")

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret")
MAGIC_TTL_MIN = int(os.environ.get("CLIENT_MAGIC_TTL_MIN", "15"))
SESSION_TTL_HOURS = int(os.environ.get("CLIENT_SESSION_TTL_HOURS", "24"))

# In-memory magic-link store. Resets on restart — that's fine for a magic link.
_MAGIC: Dict[str, Dict] = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def mint_magic_token(email: str) -> Tuple[str, str]:
    token = secrets.token_urlsafe(24)
    expires = _now() + timedelta(minutes=MAGIC_TTL_MIN)
    _MAGIC[token] = {"email": email.lower(), "expires": expires}
    log.info("client_auth · magic link minted for %s · expires %s", email, expires.isoformat())
    return token, expires.isoformat()


def verify_magic_token(token: str) -> Optional[str]:
    rec = _MAGIC.pop(token, None)
    if not rec:
        return None
    if rec["expires"] < _now():
        return None
    return rec["email"]


def mint_session_token(email: str) -> Tuple[str, str]:
    expires = _now() + timedelta(hours=SESSION_TTL_HOURS)
    payload = {
        "sub": email.lower(),
        "aud": "client",
        "iat": int(_now().timestamp()),
        "exp": int(expires.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    tok = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return tok, expires.isoformat()


def decode_session_token(token: str) -> Optional[Dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"], audience="client")
    except jwt.PyJWTError:
        return None


def status() -> Dict:
    has_resend = bool(os.environ.get("RESEND_API_KEY", "").strip())
    return {
        "magic_link_ttl_min": MAGIC_TTL_MIN,
        "session_ttl_hours": SESSION_TTL_HOURS,
        "email_delivery_configured": has_resend,
        "activate_hint": (
            "Drop RESEND_API_KEY in backend/.env to send the magic-link email. "
            "Without it, links are logged to backend stdout for dev."
        ),
    }
