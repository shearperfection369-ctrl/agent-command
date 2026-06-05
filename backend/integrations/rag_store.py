"""True-RAG per-tenant vector store scaffold.

This module defines the abstract `VectorStore` interface the rest of the app
already calls. Today it ships with a **MemoryVectorStore** that does
substring-similarity over per-tenant document buckets (deterministic, no key
required, suitable for demo + dev).

Activation path to production:
  1. Choose a provider: pgvector | pinecone | qdrant | weaviate
  2. Set in backend/.env:
       VECTOR_STORE_PROVIDER=pgvector
       OPENAI_API_KEY=sk-...           # for real embeddings
       PGVECTOR_URL=postgres://...     # provider-specific creds
  3. Implement the provider class against the same VectorStore interface.

All upstream calls already accept a `tenant_id` so isolation works on day one.
"""
from __future__ import annotations

import os
import re
import math
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import uuid

log = logging.getLogger("jadeos.rag")


@dataclass
class RagDoc:
    id: str
    tenant_id: str
    title: str
    content: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class RagHit:
    doc: RagDoc
    score: float


class VectorStore:
    """Per-tenant vector store interface. All concrete providers implement this."""

    provider_name = "abstract"

    async def upsert(self, doc: RagDoc) -> RagDoc: raise NotImplementedError
    async def delete(self, tenant_id: str, doc_id: str) -> bool: raise NotImplementedError
    async def query(self, tenant_id: str, query_text: str, k: int = 5) -> List[RagHit]: raise NotImplementedError
    async def list_for_tenant(self, tenant_id: str) -> List[RagDoc]: raise NotImplementedError
    async def stats(self) -> Dict: raise NotImplementedError


class MemoryVectorStore(VectorStore):
    """In-process per-tenant store. Substring + token-overlap scoring.

    Good enough to demo per-tenant isolation, RAG citations, and the API
    contract. Not durable; resets on backend restart.
    """

    provider_name = "memory"

    def __init__(self) -> None:
        self._by_tenant: Dict[str, Dict[str, RagDoc]] = defaultdict(dict)

    @staticmethod
    def _tokens(text: str) -> List[str]:
        return re.findall(r"[a-z0-9]{3,}", text.lower())

    def _score(self, qtokens: List[str], doc_text: str) -> float:
        if not qtokens:
            return 0.0
        dtokens = self._tokens(doc_text)
        if not dtokens:
            return 0.0
        overlap = len(set(qtokens) & set(dtokens))
        base = overlap / math.sqrt(len(set(qtokens)) * len(set(dtokens)))
        if any(q in doc_text.lower() for q in qtokens):
            base += 0.15
        return round(min(base, 1.0), 4)

    async def upsert(self, doc: RagDoc) -> RagDoc:
        if not doc.id:
            doc.id = str(uuid.uuid4())
        self._by_tenant[doc.tenant_id][doc.id] = doc
        return doc

    async def delete(self, tenant_id: str, doc_id: str) -> bool:
        bucket = self._by_tenant.get(tenant_id, {})
        return bucket.pop(doc_id, None) is not None

    async def query(self, tenant_id: str, query_text: str, k: int = 5) -> List[RagHit]:
        bucket = self._by_tenant.get(tenant_id, {})
        qtokens = self._tokens(query_text)
        hits = [RagHit(doc=d, score=self._score(qtokens, f"{d.title}\n{d.content}")) for d in bucket.values()]
        hits = [h for h in hits if h.score > 0]
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:k]

    async def list_for_tenant(self, tenant_id: str) -> List[RagDoc]:
        return list(self._by_tenant.get(tenant_id, {}).values())

    async def stats(self) -> Dict:
        per_tenant = {t: len(b) for t, b in self._by_tenant.items()}
        return {
            "provider": self.provider_name,
            "tenants": len(per_tenant),
            "docs_total": sum(per_tenant.values()),
            "docs_per_tenant": per_tenant,
            "durable": False,
        }


# --- Provider singletons -------------------------------------------------
_STORE: Optional[VectorStore] = None


def _build_store() -> VectorStore:
    provider = os.environ.get("VECTOR_STORE_PROVIDER", "memory").strip().lower()
    if provider == "memory":
        log.info("rag · using MemoryVectorStore (demo-grade · drop pgvector/pinecone DSN to upgrade)")
        return MemoryVectorStore()
    # Future providers wire in here. We fall back to memory but flag it.
    log.warning("rag · provider '%s' not yet implemented · falling back to MemoryVectorStore", provider)
    return MemoryVectorStore()


def get_store() -> VectorStore:
    global _STORE
    if _STORE is None:
        _STORE = _build_store()
    return _STORE


def status() -> Dict:
    provider = os.environ.get("VECTOR_STORE_PROVIDER", "memory")
    embeddings = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    return {
        "provider": provider,
        "embeddings_configured": embeddings,
        "real_embeddings": False,  # memory store uses token-overlap, not embeddings
        "activate_hint": (
            "Set VECTOR_STORE_PROVIDER=pgvector|pinecone|qdrant and OPENAI_API_KEY in backend/.env, "
            "then restart backend. Existing /api/rag/* contract is unchanged."
        ),
    }
