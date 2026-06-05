import { CornerBrackets } from "../components/Brackets";

/* ============================================================
 *  THE OPERATOR'S PLAYBOOK
 *  Admin-only tab. Founder-grade implementation + ops + risk analysis.
 *  All static content — single source of truth for "what we do and when".
 * ============================================================ */

const PHASES = [
  {
    n: "00", t: "PRE-LAUNCH · WEEK -2 to 0", c: "#7c5cff",
    objective: "Sharpen the pitch, lock the rolodex, ship 1 perfect demo before talking to anyone.",
    tasks: [
      "Lock the lighthouse landing page copy — kill any phrase a CFO would roll eyes at",
      "Run the demo reel end-to-end on YOUR data for each of your top-5 target verticals",
      "Pull your LinkedIn rolodex — tag every contact by industry, role, decision authority",
      "Set up a Twilio number (+1 763 area code preferred for MSP locality)",
      "Wire Stripe to production keys (not test) once you have your first verbal yes",
      "Record a 90-second Loom of JADE handling a freight load posting end-to-end",
      "Build the one-pager PDF — print 50 copies for in-person drops",
    ],
    metric: "5 perfect demos rehearsed. 100 contacts tagged. 0 typos on the landing page.",
  },
  {
    n: "01", t: "LIGHTHOUSE HUNT · MONTH 1", c: "#ccff00",
    objective: "Convert 5 lighthouse design partners. Focus over breadth.",
    tasks: [
      "Hand-pick 30 prospects from your rolodex matching ICP (11-500 emp, decision-maker, MSP-based)",
      "Drop in-person at 10 MSP offices in week 1 — coffee, one-pager, leave the demo URL",
      "Send 50 personalized cold emails using /launch templates (line 1 must be personal)",
      "Make 20 LinkedIn DMs to ops directors at top-50 MSP companies",
      "Attend 2 MSP industry events (TIA chapter, MN Trucking Assoc, MN HIMSS, MSP SaaS meetup)",
      "Score every inbound application live with /lighthouse — only meet hot/warm",
      "Sign 2 design partners by week 4 (half-price pilot, NDA, 30-day shippable scope)",
    ],
    metric: "5 lighthouse applications received. 2 design partners signed. $5k MRR locked.",
  },
  {
    n: "02", t: "FIRST PILOTS · MONTH 2", c: "#00ffff",
    objective: "Ship 2 production agents. Prove the moat with real data.",
    tasks: [
      "Day 1: 3-hour scoping workshop with each design partner — identify ONE killer workflow",
      "Day 2-7: build the custom playbook in /playbooks/new — chain 2-3 steps",
      "Day 8-14: integrate via webhook (Slack channel for output approval is the fastest path)",
      "Week 3: human-in-the-loop production — every JADE output approved before send",
      "Week 4: measure baseline vs. JADE — hours saved, errors avoided, response time delta",
      "Daily 15-min Slack check-in. Weekly 30-min ops review.",
      "Onboard 3 more lighthouse partners (different verticals — diversify case study portfolio)",
    ],
    metric: "2 pilots in production · 5 total lighthouse seats filled · $12.5k MRR · 3 measured wins",
  },
  {
    n: "03", t: "CASE STUDIES · MONTH 3", c: "#ff3b8a",
    objective: "Publish 3 cross-vertical case studies. Stop selling, start citing.",
    tasks: [
      "Interview each design partner — 30 min recording, transcribed by JADE",
      "Pull metrics from /admin/agent-runs and the partner's own systems",
      "Draft case study using the existing /cases template (problem → solution → results → quote)",
      "Get logo + quote + metrics consent in writing (the lighthouse program already collected this)",
      "Publish to /cases · share on LinkedIn · email to your top-200 list",
      "Convert design partners from half-price to lighthouse pricing (50% off LIFE — locked)",
      "Open Stripe checkout on /billing — start taking real subscriptions",
    ],
    metric: "3 case studies live · 5 paying customers · $20k MRR · LTV:CAC tracking 10:1",
  },
  {
    n: "04", t: "REPEATABLE SALES · MONTHS 4-6", c: "#ccff00",
    objective: "Sales without the founder in every meeting. Document the motion.",
    tasks: [
      "Hire 1 forward-deployed engineer (M4) — pay from MRR, not savings",
      "Write the playbook: 20-min discovery → 60-min scoping → 30-day pilot → conversion",
      "Cold outbound to 400 mid-market companies across all 10 verticals using case studies",
      "Build 5 industry-specific landing variants (onejades.com/freight, /healthcare, /saas, etc.)",
      "Add ~$15k/mo paid LinkedIn spend targeting Ops Directors at ICP companies",
      "Quarterly ops review with every Fleet customer — drive expansion to multi-agent",
      "Start the partner channel: reach out to 5 MSP consultancies for 20% rev-share resale",
    ],
    metric: "Month 6: 14 paid customers · $53.2k MRR · $638k ARR run-rate · 1 channel partner signed",
  },
  {
    n: "05", t: "SCALE + MOAT DEEPENING · MONTHS 6-12", c: "#00ffff",
    objective: "Compound the moat. Customer corrections → schema improvements → faster pilots.",
    tasks: [
      "Encourage every customer to use /playbooks/new — their playbooks live in YOUR DB forever",
      "Surface schema corrections from customers — increment correction_count, refine prompts quarterly",
      "Hire customer success lead (M9) — runs quarterly ops reviews, drives expansion + retention",
      "Add Sora 2 video generation for case-study video (1 per customer)",
      "Build a Stripe-hosted customer portal for self-serve plan changes (already wired)",
      "Tune model routing quarterly as LLM prices shift — silent margin defense",
      "Strategic angel conversation ($100-250k) ONLY if cash-flow positive — keep optionality",
    ],
    metric: "Month 12: 28 paid · $114.8k MRR · $1.38M ARR · positive cash flow · 5 schemas tuned by customers",
  },
];

const OPS = [
  {
    n: "01", t: "DAILY · 30 minutes", c: "#ccff00",
    tasks: [
      "Open /admin → check new lighthouse applications · respond to hot tier within 4 hours",
      "Review /admin/agent-runs for the last 24h · flag any errors or low-confidence outputs",
      "Reply to Slack channels for each lighthouse customer · target < 4-hour first response",
      "Update Stripe MRR tracker (just a Google sheet for now)",
    ],
  },
  {
    n: "02", t: "WEEKLY · 4 hours", c: "#00ffff",
    tasks: [
      "Friday: 30-min ops review with each lighthouse customer · capture wins + blockers in /admin/notes",
      "Pull /admin/stats → email yourself: MRR, runs, schema corrections, top 3 prospects",
      "Refresh /launch outreach assets with 1 new case-study quote · re-share on LinkedIn",
      "20 fresh cold-email touches Mon morning · use /launch templates · personalize line 1 only",
    ],
  },
  {
    n: "03", t: "MONTHLY · 1 day", c: "#7c5cff",
    tasks: [
      "Run the full demo reel against all 5 industries · verify no LLM regressions",
      "Backup MongoDB to S3 (mongodump + lifecycle policy)",
      "Review LLM token usage per customer · enforce caps with /api/orgs/budget",
      "Publish 1 new case study OR 1 new blog post · cross-post on LinkedIn",
      "Reconcile Stripe payouts · invoice anyone outside Stripe (Vault tier)",
    ],
  },
  {
    n: "04", t: "QUARTERLY · 2 days", c: "#ff3b8a",
    tasks: [
      "Refresh schemas with accumulated customer corrections · bump version",
      "A/B test 2 new prompt variants in /api/prompts · measure conversion lift",
      "Renegotiate LLM costs · update MODEL_ROUTING with cheaper variants if pricing drops",
      "Quarterly business review (QBR) with every Fleet customer · drive expansion to multi-agent",
      "Forecast next quarter MRR · adjust hiring plan accordingly",
    ],
  },
];

const REQUIREMENTS = [
  { c: "#ccff00", t: "TECH STACK", items: [
    "Emergent Universal LLM Key (already wired — Claude Sonnet 4.5 + GPT-5.2)",
    "Stripe live keys (test keys active in dev; flip to live on first verbal yes)",
    "Twilio account · MSP-area-code number · $20/mo + per-message",
    "MongoDB Atlas M10 cluster ($60/mo) once you outgrow dev (~200 active customers)",
    "Domain: onejades.com (yours) · SSL auto-managed by Emergent",
    "Email: cummins_oliver@yahoo.com (current) · upgrade to ops@onejades.com when budget allows",
  ]},
  { c: "#00ffff", t: "PEOPLE", items: [
    "Founder (you) · sales + implementation + everything · M0-M3",
    "Forward-deployed engineer · M4 hire · paid from MRR · TMS/CRM/EMR integration specialist",
    "Customer success lead · M9 hire · onboarding + QBR + retention",
    "Fractional CPA · file LLC + S-corp election + quarterly estimated taxes",
    "Fractional GTM advisor · 1 hour/week · pay $200/session ideally a freight or healthcare ops exec",
  ]},
  { c: "#7c5cff", t: "LEGAL · CONTRACTS", items: [
    "Master Services Agreement template (lawyer cost ~$1.5k one-time)",
    "Per-customer SOW · 1-page · scope + fee + termination + data handling",
    "HIPAA BAA template for healthcare customers (do NOT take healthcare $$ without one signed)",
    "NDA template for design-partner conversations",
    "Lighthouse program agreement · case-study consent + 50%-off-for-life clause locked in writing",
  ]},
  { c: "#ff3b8a", t: "FINANCIAL", items: [
    "Bootstrap runway: 6 months at $7k/mo personal burn = $42k starting cash",
    "Track in a simple Google Sheet: MRR, COGS, CAC, runway · update weekly",
    "Stripe payouts every 2 days · target net 90 days of cash on hand at all times",
    "Hire only when next-12-month MRR covers 2x the salary",
    "Tax escrow: 30% of every Stripe payout in a separate account",
  ]},
];

const RISKS = [
  { c: "#ff3b8a", t: "FOUNDER BURNOUT (HIGH)", desc: "Selling + implementing + supporting + bookkeeping at the same time will break you by month 4 if unmanaged.",
    mitigation: [
      "Hard rule: no sales calls before 10am or after 5pm",
      "1 full day off every week — no email, no Slack",
      "Hire forward engineer at month 4 even if it dips runway",
      "Therapist + 3x/week workout · non-negotiable",
    ]},
  { c: "#ff3b8a", t: "DEMO-WARE TRAP (HIGH)", desc: "Beautiful demos that don't translate to production at customer sites. You ship a Loom, customer signs, then integration takes 6 weeks.",
    mitigation: [
      "Lighthouse program is the antidote — only signs partners who'll commit to 30-day pilot",
      "Build the integration in week 1 with them in the room, not after handoff",
      "Slack-as-integration is your shortcut · no TMS/CRM rebuild required for pilot",
      "Decline customers asking for >30-day scope until M6+",
    ]},
  { c: "#ccff00", t: "MARGIN COMPRESSION (MEDIUM)", desc: "Anthropic raises Claude prices 30% in Q3. Your blended margin drops from 93% to 65%. CFOs notice.",
    mitigation: [
      "Model routing is live (/api/moat MODEL_ROUTING) — re-tier silently to Haiku for fast tasks",
      "Negotiate annual contracts with prepay — lock customer pricing while costs float",
      "Per-customer token budgets enforced via /api/orgs/budget — hard cap risk",
      "Watch Gemini 3 Flash, Mistral · be ready to add a 3rd provider option in 2 weeks",
    ]},
  { c: "#ccff00", t: "HYPERSCALER COPY (MEDIUM)", desc: "OpenAI or Microsoft ships a freight-vertical agent. SMBs default to whoever's name is on the invoice they already pay.",
    mitigation: [
      "Own the dispatcher/operator relationship — be in their Slack daily",
      "Deepen the moat: customer-specific schemas, playbooks, prompt corrections",
      "Compete on time-to-value (30 days), not feature parity",
      "Lock multi-year contracts before they ship · use lighthouse pricing as bait",
    ]},
  { c: "#7c5cff", t: "SALES CYCLE INFLATION (MEDIUM)", desc: "Healthcare and legal customers take 6 months to sign. You burn runway courting deals that won't close.",
    mitigation: [
      "Don't sell healthcare seriously until month 9 — keep freight + SaaS as cash engine",
      "60-day no-sign rule: if a prospect hasn't signed in 60 days, deprioritize and move on",
      "Run /api/agent/qualify-lead on EVERY prospect monthly — let JADE flag rotting deals",
      "Build a 'parking lot' Trello list of long-cycle deals · check quarterly, not weekly",
    ]},
  { c: "#7c5cff", t: "DATA / COMPLIANCE INCIDENT (MEDIUM-LOW)", desc: "A healthcare customer's PHI leaks via an agent log. Lawsuit. Reputation gone overnight.",
    mitigation: [
      "PHI redaction is already baked into the healthcare schema (redact:true fields → ***)",
      "Zero data retention is the default · don't log raw inputs for regulated customers",
      "Sign BAA before any healthcare data touches the system · period",
      "Quarterly external security audit (~$3k) once at 10+ customers",
      "Cyber liability insurance ($1.5k/year) starting at $50k MRR",
    ]},
  { c: "#7c5cff", t: "CHANNEL CONFLICT (LOW)", desc: "Once you sign consulting partners for 20% rev-share, they compete with your direct sales motion.",
    mitigation: [
      "Geographic carve-outs — partners get accounts outside MSP, you keep MSP",
      "Vertical carve-outs — partners get verticals you don't pursue yet (e.g. legal, real estate)",
      "Quarterly partner review · pull partners under-performing for 2 consecutive quarters",
    ]},
];

const SUCCESS_SIGNALS = [
  { c: "#ccff00", k: "WEEK 4", v: "2+ design partners signed", desc: "If you can't get 2 lighthouse partners in 30 days from a 100-contact rolodex — the offer or the pitch is wrong. Stop and fix it before scaling outreach." },
  { c: "#00ffff", k: "MONTH 3", v: "$15k+ MRR · 1 published case study", desc: "If you're still selling cold without proof by month 3 — your design partners aren't seeing wins, OR you're not asking them to publish. Either is fatal." },
  { c: "#7c5cff", k: "MONTH 6", v: "$50k+ MRR · 60%+ gross margin · founder still healthy", desc: "If you're at $50k MRR but burnt out — the founder will break before the company scales. Hire forward engineer NOW, not at $80k MRR." },
  { c: "#ff3b8a", k: "MONTH 12", v: "$100k+ MRR · positive cash flow · 1 channel partner producing", desc: "If you're profitable but channel hasn't produced a single deal by M12 — kill the channel motion. Direct sales is your moat. Don't dilute it." },
];

const FAILURE_SIGNALS = [
  { c: "#ff3b8a", k: "RED FLAG 01", v: "All 5 lighthouse partners are in the same industry", desc: "Concentration risk. One industry downturn kills all your case studies simultaneously. Diversify ≥ 3 industries by month 3." },
  { c: "#ff3b8a", k: "RED FLAG 02", v: "Average sales cycle > 45 days for SMB", desc: "Your demo isn't closing or your scope is too big. Reset: 20-min demo, single workflow, fixed price, 30-day pilot. If still > 45 days — pricing is off." },
  { c: "#ff3b8a", k: "RED FLAG 03", v: "Customer keeps approving every JADE output without edits", desc: "Sounds good, but it means they're not really reviewing — or the job is too easy and someone smarter could automate it for $20/mo. Increase output complexity OR raise price." },
  { c: "#ff3b8a", k: "RED FLAG 04", v: "Token costs > 15% of revenue per customer", desc: "Your prompts are bloated or you're not routing to cheaper models for cheap tasks. Refactor the playbook and/or push the customer to Fleet tier where overage applies." },
  { c: "#ff3b8a", k: "RED FLAG 05", v: "No customer has built their own playbook by month 6", desc: "The moat isn't compounding. Either the builder is too hard OR customers don't perceive it as their work. Add in-product nudges + a quarterly 'build-your-own-playbook' workshop." },
];

export default function PlaybookPanel() {
  return (
    <div className="space-y-10">
      {/* Hero */}
      <div className="deck-card p-8 relative" data-testid="playbook-hero">
        <CornerBrackets />
        <div className="mono-label text-[#ccff00] mb-3">OPERATOR'S PLAYBOOK · ADMIN ONLY</div>
        <h2 className="font-display font-black text-white text-4xl lg:text-5xl tracking-tighter">
          The 12-month plan.<br /><span className="accent-cyan">Step by step.</span>
        </h2>
        <p className="text-white/65 max-w-2xl mt-4 leading-relaxed">
          Implementation phases · operational requirements · success and failure analysis.
          Internal-only. This is your founder's map — open it every Monday.
        </p>
      </div>

      {/* Phases */}
      <Block label="IMPLEMENTATION PHASES" color="#ccff00" testId="phases">
        <div className="grid lg:grid-cols-2 gap-5">
          {PHASES.map((p) => (
            <div key={p.n} data-testid={`phase-${p.n}`} className="deck-card p-7 relative">
              <CornerBrackets />
              <div className="flex items-baseline gap-4 mb-4">
                <span className="font-display font-black text-[44px] leading-none" style={{ color: p.c }}>{p.n}</span>
                <div>
                  <div className="mono-label text-white/40">PHASE</div>
                  <h3 className="font-display font-bold text-white text-xl tracking-tight">{p.t}</h3>
                </div>
              </div>
              <p className="text-sm text-white/65 italic mb-5">{p.objective}</p>
              <ul className="space-y-2 mb-5">
                {p.tasks.map((t, i) => (
                  <li key={i} className="text-xs text-white/80 flex gap-2 leading-relaxed">
                    <span className="font-mono-tech mt-0.5" style={{ color: p.c }}>{String(i + 1).padStart(2, "0")}</span>
                    {t}
                  </li>
                ))}
              </ul>
              <div className="border-t border-white/10 pt-3">
                <div className="mono-label text-white/40 mb-1">SUCCESS METRIC</div>
                <p className="text-sm" style={{ color: p.c }}>{p.metric}</p>
              </div>
            </div>
          ))}
        </div>
      </Block>

      {/* Operational cadence */}
      <Block label="OPERATIONAL CADENCE · NEVER BREAK THE RHYTHM" color="#00ffff" testId="ops">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {OPS.map((o) => (
            <div key={o.n} data-testid={`ops-${o.n}`} className="deck-card p-6 relative">
              <CornerBrackets />
              <div className="mono-label" style={{ color: o.c }}>{o.n} · {o.t}</div>
              <ul className="mt-4 space-y-2">
                {o.tasks.map((t, i) => (
                  <li key={i} className="text-xs text-white/75 flex gap-2 leading-relaxed"><span style={{ color: o.c }}>▸</span>{t}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Block>

      {/* Requirements */}
      <Block label="OPERATIONAL REQUIREMENTS · WHAT YOU NEED ON DAY ONE" color="#7c5cff" testId="requirements">
        <div className="grid sm:grid-cols-2 gap-5">
          {REQUIREMENTS.map((r) => (
            <div key={r.t} data-testid={`req-${r.t.toLowerCase().replace(/\s/g,'-')}`} className="deck-card p-6 relative">
              <CornerBrackets />
              <div className="mono-label" style={{ color: r.c }}>{r.t}</div>
              <ul className="mt-4 space-y-2">
                {r.items.map((it, i) => (
                  <li key={i} className="text-xs text-white/80 flex gap-2 leading-relaxed"><span style={{ color: r.c }}>▸</span>{it}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Block>

      {/* Success signals */}
      <Block label="SUCCESS SIGNALS · WHAT TO CELEBRATE" color="#ccff00" testId="success">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {SUCCESS_SIGNALS.map((s) => (
            <div key={s.k} data-testid={`success-${s.k.toLowerCase().replace(/\s/g,'-')}`} className="border-l-2 pl-5 py-2" style={{ borderColor: s.c }}>
              <div className="mono-label text-white/40">{s.k}</div>
              <div className="font-display font-bold mt-2" style={{ color: s.c }}>{s.v}</div>
              <p className="text-xs text-white/65 mt-3 leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
      </Block>

      {/* Failure signals */}
      <Block label="FAILURE SIGNALS · WHAT TO KILL FAST" color="#ff3b8a" testId="failure">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {FAILURE_SIGNALS.map((f) => (
            <div key={f.k} data-testid={`failure-${f.k.toLowerCase().replace(/\s/g,'-')}`} className="deck-card p-5 relative">
              <CornerBrackets />
              <div className="mono-label text-[#ff3b8a]">{f.k}</div>
              <div className="font-display font-bold text-white text-sm mt-3 leading-snug">{f.v}</div>
              <p className="text-xs text-white/65 mt-3 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </Block>

      {/* Risks */}
      <Block label="RISK REGISTER · KNOWN ENEMIES" color="#ff3b8a" testId="risks">
        <div className="space-y-4">
          {RISKS.map((r) => (
            <div key={r.t} data-testid={`risk-${r.t.toLowerCase().replace(/\s/g,'-').replace(/[()]/g,'')}`} className="deck-card p-6 relative">
              <CornerBrackets />
              <div className="grid lg:grid-cols-[1fr_2fr] gap-6">
                <div>
                  <div className="mono-label" style={{ color: r.c }}>{r.t}</div>
                  <p className="text-sm text-white/75 mt-3 leading-relaxed">{r.desc}</p>
                </div>
                <div>
                  <div className="mono-label text-[#ccff00] mb-2">MITIGATION</div>
                  <ul className="space-y-1.5">
                    {r.mitigation.map((m, i) => (
                      <li key={i} className="text-xs text-white/80 flex gap-2 leading-relaxed"><span className="text-[#ccff00]">▸</span>{m}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Block>

      {/* Final mandate */}
      <div className="deck-card p-8 relative" data-testid="mandate">
        <CornerBrackets />
        <div className="mono-label text-[#ccff00] mb-3">THE ONE-LINE MANDATE</div>
        <p className="font-display font-bold text-white text-3xl lg:text-4xl leading-tight tracking-tight">
          Ship <span className="accent-cyan">five lighthouse customers</span> in ninety days.<br />
          Everything else is a distraction.
        </p>
        <p className="text-sm text-white/60 mt-6 max-w-2xl leading-relaxed">
          If a task on your calendar this week doesn't directly contribute to closing or supporting a lighthouse partner — kill it.
          The plan above is the map. The above sentence is the compass. Don't confuse the two.
        </p>
      </div>
    </div>
  );
}

function Block({ label, color, children, testId }) {
  return (
    <section data-testid={`playbook-block-${testId}`}>
      <div className="flex items-center gap-3 mb-6">
        <span className="mono-label" style={{ color }}>{label}</span>
        <span className="h-px flex-1 bg-white/5" />
      </div>
      {children}
    </section>
  );
}
