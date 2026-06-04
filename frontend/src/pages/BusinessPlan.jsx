import { jsPDF } from "jspdf";
import { toast } from "sonner";
import { CornerBrackets, SectionLabel } from "../components/Brackets";
import { DownloadSimple, ChartBar, Flag, Users, CurrencyDollar, MapTrifold } from "@phosphor-icons/react";

const PLAN_SECTIONS = [
  {
    n: "01", t: "EXECUTIVE SUMMARY", c: "#ccff00",
    paragraphs: [
      "JADE OS is a universal AI-agent platform for Minneapolis operators across freight, logistics, manufacturing, healthcare, SaaS, e-commerce, insurance, legal, real estate, and professional services. We wrap Claude Sonnet 4.5 and GPT-5.2 in six vertical-tuned agents that handle Tier-1 support, sales qualification, document extraction, ops workflows, outbound content, and on-call ops co-piloting.",
      "We go to market with a horizontal product but a vertical sales motion: each industry buyer sees a tuned demo, a tuned schema, and a tuned voice on day one. We launch design partners in three verticals simultaneously — freight brokerage, healthcare admin, and SaaS support — picking up case studies in parallel so we never depend on any one industry's sales cycle.",
      "Target: $750k ARR by month 12, $2.5M by month 18, profitability by month 11, with a 3-person founding team and zero outside capital required.",
    ],
  },
  {
    n: "02", t: "MARKET · WHY MINNEAPOLIS, WHY UNIVERSAL", c: "#00ffff",
    paragraphs: [
      "Minneapolis-St. Paul is the rare metro that has a top-5 player in nearly every industry we serve: freight (C.H. Robinson, Coyote/UPS), healthcare (UnitedHealth/Optum, Allina, HealthPartners), manufacturing (3M, Pentair, Donaldson, Polaris), retail (Best Buy, Target), insurance (Securian, Travelers), and law (Faegre Drinker, Robins Kaplan). Every industry has a 9-figure operations budget within a 30-minute drive.",
      "Buyer profile across verticals: pragmatic operators in their 40s–60s, ROI-driven, skeptical of west-coast AI hype, allergic to bloated SaaS. We win by selling outcomes (hours reclaimed, tickets deflected, docs parsed) — not by selling 'a platform'.",
      "Why universal beats vertical-only: every vertical-specific AI startup has to rebuild the same 6 agents. By sharing one core engine across industries, our COGS drops, our case-study velocity goes up, and we can cross-sell within enterprise accounts (Best Buy alone has freight, e-commerce, and support teams).",
    ],
  },
  {
    n: "03", t: "PRODUCT · THE FLEET", c: "#7c5cff",
    paragraphs: [
      "Six agents, one console. Each agent is a system-prompted Claude/GPT model wrapped in JADE's vertical-tuned context, with structured outputs, audit logs, and human-in-the-loop approvals.",
      "Tier-1 Support · Sales Qualification · Document & Data Extraction · Operations Automation · Outreach & Content · On-Call Ops Co-Pilot. Each ships with 11 industry profiles out of the box, loading the right lexicon (BOL/MC# vs ICD-10/CPT vs MRR/ARR), the right schema, and the right tone (operator-blunt vs healthcare-courteous).",
      "Customers don't pick agents — they pick outcomes. We map outcomes to agents during the 20-minute ops review and ship in 30 days.",
    ],
  },
  {
    n: "04", t: "GO-TO-MARKET", c: "#ff3b8a",
    paragraphs: [
      "Phase 1 (Months 0–3): 5 design partners across 3 verticals (2 freight, 2 healthcare admin, 1 SaaS support) at half price. Founder works the room — TIA, MN HIMSS, MSP SaaS meetup, LinkedIn outbound to ops directors.",
      "Phase 2 (Months 3–6): convert design partners to full price. Publish 3 cross-vertical case studies (\"hours reclaimed\" universal headline). Cold outbound to 400 mid-market companies across all 10 verticals.",
      "Phase 3 (Months 6–12): partner channel. Local consulting + RPA firms (Accenture MSP, Slalom, Ardalyst) resell JADE OS to their existing book. Channel partners receive 20% rev-share on first year.",
    ],
  },
  {
    n: "05", t: "PRICING + UNIT ECONOMICS", c: "#ccff00",
    paragraphs: [
      "Three tiers: Dispatch ($1,500/mo · 1 agent · any vertical), Fleet ($4,500/mo · 3 agents · any verticals · most popular), Vault (custom · unlimited + on-prem). Implementation fee waived for design partners.",
      "Cost structure per Fleet customer/month: ~$180 LLM tokens (Claude Sonnet 4.5 + GPT-5.2 mix at Emergent universal-key rates), $80 hosting/observability, $40 customer-success allocation = $300 COGS. Gross margin ~93%.",
      "Payback period: 0.7 months on Fleet (assuming $2k blended CAC via founder-led sales). LTV:CAC tracking to 15:1 by month 12.",
    ],
  },
  {
    n: "06", t: "FINANCIALS · 18 MONTHS", c: "#00ffff",
    paragraphs: [
      "Month 3: 5 design partners @ avg $2,500/mo = $12.5k MRR.",
      "Month 6: 14 paid @ avg $3,800/mo = $53.2k MRR / $638k ARR run-rate.",
      "Month 12: 28 paid @ avg $4,100/mo = $114.8k MRR / $1.38M ARR · positive cash flow.",
      "Month 18: 48 paid @ avg $4,400/mo = $211k MRR / $2.53M ARR. Hire 1 customer success + 1 forward-deployed engineer + 1 vertical SDR.",
      "Operating expenses Y1: $42k founder cash draw, ~$26k tooling (LLM + observability + CRM), ~$18k T&E/MSP networking. Net: profitable in month 11.",
    ],
  },
  {
    n: "07", t: "RISKS · MITIGATION", c: "#7c5cff",
    paragraphs: [
      "Risk: hyperscalers ship industry-specific agents. Mitigation: own the integration layer + last-mile operator relationships in MSP. Stay 6 months ahead on workflow depth and per-industry tuning.",
      "Risk: LLM cost spikes. Mitigation: token budgets per customer, automatic model routing (Sonnet → Haiku for cheap tasks), Emergent universal key gives multi-provider pricing leverage.",
      "Risk: enterprise compliance friction in healthcare/legal/finance. Mitigation: don't take regulated workloads until month 6+; for early healthcare deals, scope to non-PHI use cases only until BAA is in place.",
    ],
  },
  {
    n: "08", t: "TEAM + ASK", c: "#ff3b8a",
    paragraphs: [
      "Founder: 10+ years in freight ops / 3PL operations. Holds the MSP rolodex. Sells. Implements.",
      "Co-founder (forward-deployed engineer): integrates agents with customer TMS/CRM/EMR/helpdesk. Hired month 4 from MRR.",
      "Customer success lead: hired month 9. Onboards new Fleet customers and runs quarterly ops reviews across all verticals.",
      "We are bootstrapping — no outside capital required. Open to a single strategic angel ($100–250k) from a Minneapolis operator who wants to ride the wave.",
    ],
  },
];

export default function BusinessPlan() {
  const downloadPDF = () => {
    const doc = new jsPDF({ unit: "pt", format: "letter" });
    const margin = 54;
    const w = 612 - margin * 2;
    let y = margin;

    doc.setFillColor(2, 3, 10);
    doc.rect(0, 0, 612, 792, "F");
    doc.setTextColor(204, 255, 0);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(36);
    doc.text("JADE OS", margin, 100);
    doc.setFontSize(11);
    doc.setTextColor(0, 255, 255);
    doc.text("BUSINESS PLAN · MINNEAPOLIS · 2026", margin, 120);

    doc.setTextColor(255, 255, 255);
    doc.setFontSize(14);
    doc.setFont("helvetica", "normal");
    doc.text("AI agents that run the dock door — freight, support, ops, sales.", margin, 160, { maxWidth: w });

    y = 220;
    PLAN_SECTIONS.forEach((s) => {
      if (y > 700) { doc.addPage(); doc.setFillColor(2,3,10); doc.rect(0,0,612,792,"F"); y = margin; }
      doc.setTextColor(204, 255, 0);
      doc.setFontSize(9);
      doc.text(`${s.n} · ${s.t}`, margin, y);
      y += 18;
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(11);
      s.paragraphs.forEach((p) => {
        const lines = doc.splitTextToSize(p, w);
        if (y + lines.length * 14 > 740) { doc.addPage(); doc.setFillColor(2,3,10); doc.rect(0,0,612,792,"F"); y = margin; }
        doc.text(lines, margin, y);
        y += lines.length * 14 + 8;
      });
      y += 14;
    });

    doc.save("JADE-OS-business-plan.pdf");
    toast.success("Tape downloaded.");
  };

  return (
    <div className="bg-console min-h-screen">
      <section className="relative px-6 lg:px-10 py-16 lg:py-24 grid-bg-tight border-b border-white/5">
        <div className="max-w-[1400px] mx-auto">
          <SectionLabel idx={0} color="#ccff00">BUSINESS PLAN · INTERNAL TAPE</SectionLabel>
          <div className="grid lg:grid-cols-3 gap-10 items-end">
            <div className="lg:col-span-2">
              <h1 className="font-display font-black text-white text-5xl sm:text-7xl tracking-tighter glow-lime">
                The plan.<br />
                <span className="accent-cyan text-5xl sm:text-7xl">Eighteen months. $2.5M ARR. Every industry in MSP.</span>
              </h1>
              <p className="mt-6 text-white/65 max-w-2xl leading-relaxed">
                A complete operator's playbook for JADE OS: market, product, GTM across all 10 verticals, pricing, financials, risks, and the ask. Read it on the page or grab the PDF.
              </p>
            </div>
            <div className="flex flex-col gap-3">
              <button data-testid="plan-download-btn" onClick={downloadPDF} className="btn-jade inline-flex items-center justify-center gap-2">
                <DownloadSimple size={16} weight="bold" /> DOWNLOAD PDF
              </button>
              <div className="grid grid-cols-2 gap-3">
                <KPI k="ARR · M18" v="$2.5M" c="#ccff00" />
                <KPI k="GM" v="93%" c="#00ffff" />
                <KPI k="CASH BREAK" v="M11" c="#7c5cff" />
                <KPI k="VERTICALS" v="10+" c="#ff3b8a" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="px-6 lg:px-10 py-16">
        <div className="max-w-[1400px] mx-auto grid lg:grid-cols-4 gap-12">
          <aside className="lg:col-span-1 lg:sticky lg:top-24 self-start">
            <div className="mono-label text-[#00ffff] mb-4">CONTENTS</div>
            <ul className="space-y-2">
              {PLAN_SECTIONS.map((s) => (
                <li key={s.n}>
                  <a href={`#sec-${s.n}`} className="block py-2 border-l-2 border-white/5 hover:border-[#ccff00] hover:text-[#ccff00] pl-3 transition">
                    <span className="font-mono-tech text-xs text-white/40">{s.n}</span>
                    <div className="font-mono-tech text-xs text-white/70 mt-1">{s.t}</div>
                  </a>
                </li>
              ))}
            </ul>
          </aside>

          <article className="lg:col-span-3 space-y-16">
            {PLAN_SECTIONS.map((s) => (
              <section id={`sec-${s.n}`} key={s.n} className="deck-card p-8 lg:p-10 relative" data-testid={`plan-section-${s.n}`}>
                <CornerBrackets />
                <div className="flex items-baseline gap-4 mb-6">
                  <span className="font-display font-black text-[56px] leading-none" style={{ color: s.c }}>{s.n}</span>
                  <div>
                    <div className="mono-label text-white/40">SECTION</div>
                    <h2 className="font-display font-bold text-white text-3xl tracking-tight">{s.t}</h2>
                  </div>
                </div>
                <div className="space-y-4">
                  {s.paragraphs.map((p, i) => (
                    <p key={i} className="text-white/80 leading-relaxed text-[15px]">{p}</p>
                  ))}
                </div>
              </section>
            ))}
          </article>
        </div>
      </section>
    </div>
  );
}

function KPI({ k, v, c }) {
  return (
    <div className="border border-white/10 p-3 bg-[#06081a]">
      <div className="mono-label text-white/40">{k}</div>
      <div className="font-display font-bold text-2xl" style={{ color: c }}>{v}</div>
    </div>
  );
}
