"""JADE OS · Integrations scaffolding.

Each module in this package is a *wire-in stub* — it exposes the same surface area
that the production integration will, but no-ops (or returns clearly-marked stub
data) until the corresponding API key / DSN is dropped into `backend/.env`.

This lets the rest of the codebase call into integrations today and have them
"come alive" the moment the operator provides credentials, with zero refactor.

Integrations scaffolded here:
  • sentry_stub        — error monitoring (set SENTRY_DSN)
  • rag_store          — per-tenant vector RAG (set VECTOR_STORE_PROVIDER + provider keys)
  • client_auth_stub   — operator-facing client portal magic-link auth (set RESEND_API_KEY)
"""
