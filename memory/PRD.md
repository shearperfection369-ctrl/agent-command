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
- Landing page (hero, 6-agent bento, 8-vertical grid, 4-phase deployment, 3-tier pricing, lead-capture form).
- Interactive Agent Demo: 5 tabs (Chat / Extract / Outreach / Qualify / Support Triage) × 11 industries × 2 providers.
- Streaming SSE chat with industry-tuned prompts.
- Public lead capture; JWT-protected admin dashboard with leads queue + agent run tape + stats.
- Business Plan page (8 sections, rendered + downloadable PDF).
- Launch Kit page (5 outreach assets, 10-row cross-vertical target list, channel order-of-ops, downloadable PDF).
- Admin auth seeded from env on startup.
- 30/30 backend tests passing.

## Backlog
- **P1**: Voice / call center agent (Twilio + Whisper). CRM/Slack/email webhook delivery for approved actions. Multi-tenant org model (so customers can self-serve).
- **P1**: Per-industry sample document upload (PDF parsing — currently text only). Stripe billing on three pricing tiers.
- **P2**: Public case-study pages with metrics. Customer-portal preview (read-only run history). Multi-user roles inside an org.
- **P2**: Knowledge-base RAG for support agent (upload FAQ docs).
- **P2**: Per-customer LLM token budgets + automatic model routing (Sonnet → Haiku for cheap calls).
