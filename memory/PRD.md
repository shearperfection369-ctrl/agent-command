# JADE OS — PRD

## Original problem statement
Build an AI agent platform to sell to companies in the Minneapolis area, with a full business plan and launch package to court existing businesses. Six agent types (customer service / Tier-1 support, sales qualification & lead scoring, data extraction & processing, ops / workflow automation, content / email generation, on-call ops co-pilot) wrapping Claude / GPT.

After 1st pivot: app must be **universal** — not freight-only. Agents must serve any industry (freight, logistics, manufacturing, healthcare, SaaS, e-commerce, insurance, legal, real estate, professional services, general) and tailor lexicon + schema + tone per industry.

## Architecture
- **Frontend**: React (CRA + craco), Tailwind, shadcn/ui, JADE OS brand (Space Grotesk + Inter + JetBrains Mono, Jade Lime / Quantum Cyan / Vault Violet on Console Black).
- **Backend**: FastAPI + Motor (MongoDB). All routes prefixed `/api`. JWT admin auth (bcrypt + PyJWT).
- **LLM**: Claude Sonnet 4.5 + GPT-5.2 via `emergentintegrations.LlmChat` with Emergent Universal Key. Streaming SSE on chat.
- **Industry-aware system prompts**: `_system_for(industry, role_hint)` builds prompts using an `INDUSTRY_LEXICON` dict.

## User personas
- Operator (ops director, dispatcher, CS lead, COO) at MSP-area SMB/mid-market across any of 11 industries.
- Admin (JADE founder) — reviews leads, watches agent run tape.

## What's implemented (2026-02)
- **Public**: Landing (universal hero + 6-agent bento + 8-vertical grid + 4-phase deployment + 3-tier pricing + lead capture). Demo Reel (5 scenes, autoplay, live LLM streaming). Console / Agent Demo (5 agent tabs × 11 industries × 2 providers + PDF upload). Pitch Deck (13-slide interactive deck + PDF download). Business Plan + Launch Kit (rendered + PDF). Case Studies (3 seeded, public, slug-routed). Customer Portal preview (read-only by email). Billing/Stripe Checkout (3 tiers, success page polls until paid).
- **Admin**: JWT login → Mission Control dashboard with 5 tabs (Leads · Agent Runs · Orgs · Webhooks · Knowledge Base). Stats cards (leads, runs, paid orgs, est. tokens). Webhook register/test/delete (Slack + CRM + generic). KB doc CRUD powering /api/kb/ask RAG. Org registry + usage analytics.
- **Backend**: 30 (iter-1) + 26 (iter-2) = **56 tests passing**. New endpoints: `/api/agent/extract-pdf` (pypdf), `/api/kb/docs`, `/api/kb/ask` (RAG-lite), `/api/webhooks*` + `/api/webhooks/{id}/dispatch` (httpx delivery + log), `/api/billing/checkout` + `/api/billing/status/{sid}` + `/api/webhook/stripe`, `/api/orgs` + `/api/orgs/usage`, `/api/case-studies` (+ slug), `/api/portal/preview`. Three case studies auto-seeded on startup.
- Admin credentials in `/app/memory/test_credentials.md`.

## Backlog
- **P2**: Voice agent (Twilio + Whisper). Stripe customer portal link for self-serve subscription mgmt. SSO for the customer portal. Per-customer LLM token budgets with hard caps.
- **P3**: Vector-DB upgrade for the KB (currently keyword/full-text). Webhook delivery retry queue. ICP-templated case-study generation. Embed-anywhere widget for the Demo Reel.
