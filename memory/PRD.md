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
- **PROMO REEL V2 (2026-02-04)** — regenerated via **sora-2-pro** (premium model), 12s · 1280×720 · 7.57 MB. New beat-structured prompt features: (1) matte-black titanium Quanta keyfob with lime-LED edges + circuit-board windows + fingerprint scanner (animated, pulses, projects hologram), (2) JADE OS wordmark holographic projection, (3) four orbiting UI cards showing real ops scenes — `EMAIL · AUTO-SORTED · 184 TODAY` (Outlook-style chaos → folder routing), `TICKETS · TRIAGED · 38s AVG`, `LEADS · SCORED · 1.2k MTD`, `DOCS · EXTRACTED · 2.4k MTD`, (4) industry sigil montage (truck/stethoscope/gear/gavel/document/dollar) orbiting Quanta, (5) wordmark reveal with `AI AGENTS FOR THE OPERATOR · ONEJADES.COM`. Backend endpoints `/api/promo/video` and `/api/promo/meta` now support `?v=1|2` version pinning and default to newest. Admin PROMO REEL tab shows V2/V1 toggle. Production script: `backend/scripts/generate_promo_video_v2.py`.
- **PROSPECTS UI (2026-02-04)** — wired into Leads tab. AI generates MSP-area B2B prospects per industry (LLM-synthesized via Claude with industry-specific MSP geographic hints), filterable, with one-click "DRAFT EMAIL" that opens a tailored solicitation package modal (subject + 90-140 word operator-grade body + 3 talking points + PS) and a single OPEN IN EMAIL CLIENT button that fires `mailto:` with subject/body pre-filled — auto-marks contacted on click. COPY SUBJECT / BODY / ALL also available. Backend endpoints already shipped: `/prospects/generate`, `/prospects`, `/prospects/{id}/email-draft`, `/prospects/{id}/contacted`, DELETE.
- **PROMO REEL · Sora 2 (2026-02-04)** — Sora 2-generated 12s · 1280×720 high-tech promotional video clip with full JADE OS branding (lime/cyan/violet on console black, holographic interface, industry sigils orbiting bracketed monogram, wordmark reveal). Saved to `/app/static/jadeos_promo.mp4` (9.06 MB · rendered in 169s). Backend: `GET /api/promo/video` (FileResponse) + `GET /api/promo/meta`. New `PROMO REEL` tab in admin with embedded player, one-click DOWNLOAD MP4 / COPY PUBLIC URL / COPY SOCIAL CAPTION, platform-routing tips, and the raw Sora 2 prompt for re-rendering. Production script: `backend/scripts/generate_promo_video.py`.
- **LIGHTHOUSE CRASH FIX (2026-02-04)** — `<Stat>` component was referenced in `LighthousePanel` but never defined → `ReferenceError` crashed the entire admin Lighthouse tab. Added the `Stat` helper alongside `SummaryStat`. Tab now renders cleanly.
- **P0 AUTH GATES (2026-02-04)** — `POST /api/billing/portal-session` and `POST /api/playbooks/customer` now require `require_admin` (returns 401 unauthenticated). Closes the P0 surface flagged in iteration 3.
- **PROSPECTS · backend (2026-02-04)** — LLM-generates realistic Minneapolis-area B2B prospects per industry (`POST /api/prospects/generate`), lists/deletes/marks-contacted, and drafts tailored solicitation email packages (`POST /api/prospects/{id}/email-draft`). Frontend wiring still pending.
- **ADMIN SELF-TEST (Round 5 · 2026-02-04)** — new `SELF-TEST` tab in admin/console runs a battery of 21 checks across every major feature (auth, leads, lighthouse, MOAT schemas/prompts/playbooks, KB, webhooks, billing/Stripe, Twilio SDK + config, LLM key, Claude chat round-trip, Claude extract+JSON, agent_runs ledger, case studies, pypdf, Mongo ping). Each check returns `{name, category, status, latency_ms, message, details}`. `?deep=true` toggles LLM round-trips (cost-gated). UI: per-category result groups with PASS/FAIL/SKIP counters, expandable rows showing raw JSON, summary cards. Backend endpoint: `GET /api/admin/self-test` (admin-gated). Regression: `backend/tests/test_self_test.py` (2/2 passing).
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
