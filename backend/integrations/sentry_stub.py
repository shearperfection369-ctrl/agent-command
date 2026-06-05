"""Sentry error-monitoring scaffold.

Activation:
  1. Drop a DSN into backend/.env as `SENTRY_DSN=https://...@sentry.io/...`
  2. (optional) `pip install sentry-sdk[fastapi]` — already on most modern envs
  3. Restart backend. Errors auto-flow to Sentry.

No DSN → init_sentry() returns False and the rest of the app continues unchanged.
"""
from __future__ import annotations

import os
import logging

log = logging.getLogger("jadeos.sentry")

_INITIALIZED = False


def is_configured() -> bool:
    return bool(os.environ.get("SENTRY_DSN", "").strip())


def init_sentry(service: str = "jadeos-backend") -> bool:
    """Initialize Sentry if SENTRY_DSN is set. Idempotent.

    Returns True iff Sentry was wired in this process.
    """
    global _INITIALIZED
    if _INITIALIZED:
        return True
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        log.info("sentry · scaffold present · DSN not set · skipping init")
        return False
    try:
        import sentry_sdk  # type: ignore
        from sentry_sdk.integrations.fastapi import FastApiIntegration  # type: ignore
        from sentry_sdk.integrations.starlette import StarletteIntegration  # type: ignore

        sentry_sdk.init(
            dsn=dsn,
            environment=os.environ.get("SENTRY_ENV", "preview"),
            release=os.environ.get("SENTRY_RELEASE", "jadeos@dev"),
            traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            send_default_pii=False,
            integrations=[FastApiIntegration(), StarletteIntegration()],
            server_name=service,
        )
        _INITIALIZED = True
        log.info("sentry · initialized · env=%s release=%s", os.environ.get("SENTRY_ENV", "preview"), os.environ.get("SENTRY_RELEASE", "jadeos@dev"))
        return True
    except ImportError:
        log.warning("sentry · DSN present but sentry-sdk not installed · run `pip install sentry-sdk[fastapi]`")
        return False
    except Exception as e:  # never let monitoring crash the app
        log.warning("sentry · init failed · %s", e)
        return False


def capture_exception(exc: BaseException) -> None:
    """Forward exception to Sentry if wired; otherwise log locally. Safe to call anywhere."""
    if not _INITIALIZED:
        log.exception("(local) exception", exc_info=exc)
        return
    try:
        import sentry_sdk  # type: ignore
        sentry_sdk.capture_exception(exc)
    except Exception:
        log.exception("sentry capture failed; original exc:", exc_info=exc)


def status() -> dict:
    return {
        "configured": is_configured(),
        "initialized": _INITIALIZED,
        "env": os.environ.get("SENTRY_ENV", "preview"),
        "release": os.environ.get("SENTRY_RELEASE", "jadeos@dev"),
        "activate_hint": "Drop SENTRY_DSN in backend/.env and restart backend.",
    }
