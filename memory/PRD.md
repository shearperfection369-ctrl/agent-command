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
- **THE MOAT (Round 4)** — customer-locking IP layers that turn JADE from "thin LLM wrapper" into a defensible product:
    - **Schema Library** — 4 seeded versioned extraction schemas (freight_bol, healthcare_intake, saas_order_form, manufacturing_po). Customer corrections increment `correction_count` → our schemas improve from THEIR data.
    - **Prompt Library** — 3 seeded named/versioned prompts with A/B variants. `/api/prompts/run` interpolates `{{vars}}` and routes through `_route_model`.
    - **Playbooks** — multi-step workflows orchestrated as code (not Zapier-able). 3 seeded: freight_load_intake (extract→outreach), healthcare_intake_triage (extract→triage), saas_inbound_lead (qualify→outreach). Verified end-to-end run: 12.8s, 2 steps, both green.
    - **Model Router** — `MODEL_ROUTING` dict with 3 profiles (fast/default/smart). Customer code never changes when prices shift.
    - **Moat Analytics** — `/api/moat/stats` (public) + `/api/moat/admin` (auth) surface the accumulating IP.
- **LIGHTHOUSE CUSTOMER PROGRAM (Round 4)** — `/lighthouse` dedicated landing with multi-section application form. Applications auto-scored by JADE's own lead-qualification agent (dogfooding). Hot applicants auto-advance to 'screening' status. 5-seat cap with public counter. Admin dashboard has a new Lighthouse tab sorted by JADE score, expandable rows with rationale + flags + status workflow (new → screening → interview_scheduled → selected → pilot_live → case_published).
- **Public**: + Lighthouse band on landing page driving CTR to /lighthouse.
- **Backend**: **86/86 tests passing** across 3 iterations.
- Admin credentials in `/app/memory/test_credentials.md`.

## Backlog
- **P2**: Twilio voice/SMS agent · Stripe-hosted customer portal · per-customer hard token caps.
- **P3**: Vector DB upgrade for KB · embed-anywhere reel widget · multi-user org roles · public playbook builder.
