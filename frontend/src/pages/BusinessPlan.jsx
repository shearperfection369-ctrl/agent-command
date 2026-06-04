import { jsPDF } from "jspdf";
import { toast } from "sonner";
import { CornerBrackets, SectionLabel } from "../components/Brackets";
import { DownloadSimple, ChartBar, Flag, Users, CurrencyDollar, MapTrifold } from "@phosphor-icons/react";

const PLAN_SECTIONS = [
  {
    n: "01", t: "EXECUTIVE SUMMARY", c: "#ccff00",
    paragraphs: [
      "JADE OS is a productized AI-agent studio for Minneapolis operators — freight brokers, 3PLs, manufacturers, healthcare and SaaS ops teams. We wrap Claude Sonnet 4.5 and GPT-5.2 in vertical-tuned agents that handle Tier-1 support, sales qualification, document extraction, ops workflows, and outbound content.",
      "We launch narrow: freight brokers and 3PLs in MSP, the founder's home vertical. One killer agent — load matching + carrier outreach — sold to 5 design partners at $3–4.5k/mo MRR inside 90 days. Then expand horizontally into adjacent verticals using the case studies as social proof.",
      "Target: $500k ARR by month 18, profitability by month 12, with a 3-person founding team and zero outside capital.",
    ],
  },
  {
    n: "02", t: "MARKET · WHY MINNEAPOLIS", c: "#00ffff",
    paragraphs: [
      "Minneapolis-St. Paul is the freight capital of the upper Midwest — home to C.H. Robinson (largest 3PL in NA), Coyote (UPS), Bay & Bay, and ~300 small-to-mid brokers. Freight brokerage is structurally under-automated and margin-pressured (avg net margin 2–3%). Even a 5% utilization lift is meaningful.",
      "Adjacent industrial buyers (Pentair, Emerson, Donaldson, Polaris, 3M, Cargill, Hormel, Ecolab) sit within a 30-minute drive. Healthcare giants (UnitedHealth/Optum, Allina, HealthPartners) and Mayo Clinic in Rochester are an hour away — administrative automation is a 9-figure opportunity.",
      "Buyer profile: pragmatic operators in their 40s–60s, ROI-driven, skeptical of west-coast AI hype. We sell with a one-pager, a live demo on their data, and a 30-day pilot — not a SaaS portal.",
    ],
  },
  {
    n: "03", t: "PRODUCT · THE FLEET", c: "#7c5cff",
    paragraphs: [
      "Six agents, one console. Each agent is a system-prompted Claude/GPT model wrapped in JADE's freight-trained context, with structured outputs, audit logs, and human-in-the-loop approvals.",
      "Freight Broker Co-Pilot (flagship): paste a load posting → extract structured data → match to carrier list → draft outreach email → log everything. Replaces 2–4 hours/day of dispatcher email.",
      "Other agents: Tier-1 Support, Sales Qualification, Document Extraction (BOL/invoice/intake), Operations Automation, Outbound Content Generation. All built on the same console and pricing.",
    ],
  },
  {
    n: "04", t: "GO-TO-MARKET", c: "#ff3b8a",
    paragraphs: [
      "Phase 1 (Months 0–3): 5 freight broker design partners at half price, in-person sales. Founder works the room — TIA, MSP logistics networking, LinkedIn outbound to MC-authority holders in MN/WI/IA.",
      "Phase 2 (Months 3–6): convert design partners to full price, collect 3 published case studies (\"dispatcher hours reclaimed\", \"utilization +4.2%\", \"DSO −8 days\"). Use case studies for cold outreach to 200 brokers.",
      "Phase 3 (Months 6–12): horizontal expansion. Adapt freight playbook for manufacturing intake, healthcare insurance verification, SaaS ticket triage. Same console, swapped system prompts.",
    ],
  },
  {
    n: "05", t: "PRICING + UNIT ECONOMICS", c: "#ccff00",
    paragraphs: [
      "Three tiers: Dispatch ($1,500/mo · 1 agent), Fleet ($4,500/mo · 3 agents · most popular), Vault (custom · unlimited + on-prem). Implementation fee waived for design partners.",
      "Cost structure per Fleet customer/month: ~$180 LLM tokens (Claude Sonnet 4.5 + GPT-5.2 mix at Emergent universal-key rates), $80 hosting/observability, $40 customer-success allocation = $300 COGS. Gross margin ~93%.",
      "Payback period: 0.7 months on Fleet (assuming $2k blended CAC via founder-led sales). LTV:CAC tracking to 15:1 by month 12.",
    ],
  },
  {
    n: "06", t: "FINANCIALS · 18 MONTHS", c: "#00ffff",
    paragraphs: [
      "Month 3: 5 design partners @ avg $2,500/mo = $12.5k MRR.",
      "Month 6: 12 paid @ avg $3,800/mo = $45.6k MRR / $547k ARR run-rate.",
      "Month 12: 24 paid @ avg $4,100/mo = $98.4k MRR / $1.18M ARR run-rate · positive cash flow.",
      "Month 18: 40 paid @ avg $4,400/mo = $176k MRR / $2.1M ARR. Hire 1 customer success + 1 forward-deployed engineer.",
      "Operating expenses Y1: $42k founder cash draw, ~$22k tooling (LLM + observability + CRM), ~$15k T&E/MSP networking. Net: profitable in month 11.",
    ],
  },
  {
    n: "07", t: "RISKS · MITIGATION", c: "#7c5cff",
    paragraphs: [
      "Risk: hyperscalers ship freight-vertical agents. Mitigation: own the integration layer + last-mile dispatcher relationship. Stay 6 months ahead on workflow depth.",
      "Risk: LLM cost spikes. Mitigation: token budgets per customer, automatic model routing (Sonnet → Haiku for cheap tasks), Emergent universal key gives multi-provider pricing leverage.",
      "Risk: long enterprise sales cycle on healthcare. Mitigation: don't sell healthcare until month 9 — keep freight as the cash engine until then.",
    ],
  },
  {
    n: "08", t: "TEAM + ASK", c: "#ff3b8a",
    paragraphs: [
      "Founder: 10+ years in freight ops / 3PL operations. Holds the rolodex. Sells. Implements.",
      "Co-founder (forward-deployed engineer): integrates agents with customer TMS/CRM. Hired month 4 from MRR.",
      "Customer success lead: hired month 9. Onboards new Fleet customers and runs quarterly ops reviews.",
      "We are bootstrapping — no outside capital. Open to a single strategic angel ($100–250k) from a Minneapolis logistics operator who wants to ride the wave.",
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
                <span className="accent-cyan text-5xl sm:text-7xl">Eighteen months. Two million ARR.</span>
              </h1>
              <p className="mt-6 text-white/65 max-w-2xl leading-relaxed">
                A complete operator's playbook for JADE OS: market, product, GTM, pricing, financials, risks, and the ask. Read it on the page or grab the PDF.
              </p>
            </div>
            <div className="flex flex-col gap-3">
              <button data-testid="plan-download-btn" onClick={downloadPDF} className="btn-jade inline-flex items-center justify-center gap-2">
                <DownloadSimple size={16} weight="bold" /> DOWNLOAD PDF
              </button>
              <div className="grid grid-cols-2 gap-3">
                <KPI k="ARR · M18" v="$2.1M" c="#ccff00" />
                <KPI k="GM" v="93%" c="#00ffff" />
                <KPI k="CASH BREAK" v="M11" c="#7c5cff" />
                <KPI k="DESIGN PARTNERS" v="5" c="#ff3b8a" />
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
