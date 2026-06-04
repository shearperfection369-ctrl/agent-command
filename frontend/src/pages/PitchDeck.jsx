import { useEffect, useState } from "react";
import { jsPDF } from "jspdf";
import { toast } from "sonner";
import { CornerBrackets } from "../components/Brackets";
import { ArrowRight, ArrowLeft, DownloadSimple, CaretLeft, CaretRight, PresentationChart } from "@/lib/icons";

/* Slide deck — designed for SMB → mid-market → enterprise pitch reuse */
const SLIDES = [
  {
    id: 1, kind: "cover",
    eyebrow: "JADE OS · PITCH DECK · 2026",
    title: "AI agents that run\nthe business.",
    sub: "Every team. Every industry. One console.",
    mono: "MINNEAPOLIS · BUILT FOR OPERATORS",
  },
  {
    id: 2, kind: "stat",
    eyebrow: "01 · THE PROBLEM",
    title: "Operators are drowning in repetitive work.",
    bullets: [
      "Support queues take 11+ hours to first response in B2B SaaS.",
      "Manufacturers manually key 60% of POs and intake forms.",
      "Freight brokers lose 2–4 dispatcher hours/day to carrier email.",
      "Healthcare admins backlog 1,800 intake forms by Friday.",
      "Sales teams chase tire-kickers because they can't score leads fast enough.",
    ],
    foot: "EVERY INDUSTRY HAS THE SAME 6 BOTTLENECKS",
  },
  {
    id: 3, kind: "diagonal",
    eyebrow: "02 · THE TAM",
    title: "Operations is a $480B market.\nAI agents will eat 15% by 2030.",
    grid: [
      { k: "GLOBAL OPS LABOR", v: "$3.4T", c: "#ccff00" },
      { k: "AUTOMATABLE TODAY", v: "30%", c: "#00ffff" },
      { k: "EARLY ADOPTERS · MID-MKT", v: "12k FIRMS", c: "#7c5cff" },
      { k: "MSP TARGET MARKET", v: "$1.8B ARR", c: "#ff3b8a" },
    ],
  },
  {
    id: 4, kind: "split",
    eyebrow: "03 · THE INSIGHT",
    title: "Vertical AI startups all\nrebuild the same 6 agents.",
    body: "Support · Sales-qual · Data extraction · Ops automation · Outreach · Co-pilot. Every vertical needs them. Every vertical-specific player rebuilds them.\n\nJADE OS ships ONE engine, tuned for ANY industry. Lower COGS. Faster case-study velocity. Cross-sell inside enterprise accounts.",
    side: {
      label: "WHY WE WIN",
      items: ["Horizontal engine", "Vertical tuning out-of-the-box", "30-day pilots, not 9-month integrations", "Operator voice, not SaaS-speak"],
    },
  },
  {
    id: 5, kind: "agents",
    eyebrow: "04 · THE PRODUCT",
    title: "Six agents.\nOne console.",
    agents: [
      { n: "01", t: "TIER-1 SUPPORT", c: "#ccff00", b: "Triage tickets, route, draft responses." },
      { n: "02", t: "SALES QUALIFICATION", c: "#00ffff", b: "Score 0-100, tier hot/warm/cold, book meetings." },
      { n: "03", t: "DATA EXTRACTION", c: "#7c5cff", b: "BOL, PO, EOB, intake, contracts → clean JSON." },
      { n: "04", t: "OPS AUTOMATION", c: "#ff3b8a", b: "Monitor, trigger, escalate. Walk the decision tree." },
      { n: "05", t: "OUTREACH · CONTENT", c: "#ccff00", b: "Personalized email at scale, in your voice." },
      { n: "06", t: "OPS CO-PILOT", c: "#00ffff", b: "On-call AI ops lead. 24/7. Trained on your vertical." },
    ],
  },
  {
    id: 6, kind: "verticals",
    eyebrow: "05 · WHO WE SERVE",
    title: "11 industries, day one.",
    verticals: [
      { n: "FREIGHT · 3PL", c: "#ccff00", who: "C.H. Robinson, Coyote, Bay & Bay" },
      { n: "MANUFACTURING", c: "#00ffff", who: "3M, Pentair, Donaldson, Polaris" },
      { n: "HEALTHCARE", c: "#7c5cff", who: "UnitedHealth, Allina, Mayo Clinic" },
      { n: "SAAS · TECH", c: "#ff3b8a", who: "Best Buy, Securian, Code42" },
      { n: "E-COMMERCE", c: "#ccff00", who: "Target.com, Faribault Mill" },
      { n: "INSURANCE", c: "#00ffff", who: "Securian, Travelers, Allianz" },
      { n: "LEGAL", c: "#7c5cff", who: "Faegre Drinker, Robins Kaplan" },
      { n: "REAL ESTATE", c: "#ff3b8a", who: "Cushman, Colliers, Ryan" },
    ],
  },
  {
    id: 7, kind: "diagonal",
    eyebrow: "06 · PROOF",
    title: "Three design partners.\nThree real wins.",
    grid: [
      { k: "FREIGHT", v: "4.2 H/DAY SAVED", c: "#ccff00" },
      { k: "HEALTHCARE", v: "96% EXTRACT", c: "#00ffff" },
      { k: "SAAS SUPPORT", v: "+18 CSAT", c: "#7c5cff" },
      { k: "RUNS LOGGED", v: "6,300+", c: "#ff3b8a" },
    ],
    foot: "FULL FIELD REPORTS AT JADEOS.AI/CASES",
  },
  {
    id: 8, kind: "tiers",
    eyebrow: "07 · PRICING",
    title: "Three tiers. Operator-clean.",
    tiers: [
      { n: "DISPATCH", p: "$1,500", per: "/MO", c: "#ccff00", who: "Small teams · 1 agent · 500 runs" },
      { n: "FLEET", p: "$4,500", per: "/MO", c: "#00ffff", who: "Mid-market · 3 agents · 5,000 runs · webhooks" },
      { n: "VAULT", p: "Custom", per: "ANNUAL", c: "#7c5cff", who: "Enterprise · unlimited · on-prem · BAA" },
    ],
  },
  {
    id: 9, kind: "diagonal",
    eyebrow: "08 · UNIT ECONOMICS",
    title: "93% gross margin.\n0.7 month payback.",
    grid: [
      { k: "GROSS MARGIN", v: "93%", c: "#ccff00" },
      { k: "PAYBACK · FLEET", v: "0.7 MO", c: "#00ffff" },
      { k: "LTV : CAC", v: "15 : 1", c: "#7c5cff" },
      { k: "COGS · FLEET", v: "$300/MO", c: "#ff3b8a" },
    ],
  },
  {
    id: 10, kind: "gtm",
    eyebrow: "09 · GO-TO-MARKET",
    title: "Three phases. Eighteen months.",
    phases: [
      { n: "P1 · MO 0-3", c: "#ccff00", t: "DESIGN PARTNERS", b: "5 partners across 3 verticals. Half-price pilots. Founder sells." },
      { n: "P2 · MO 3-6", c: "#00ffff", t: "CASE STUDIES", b: "Convert to full price. Publish 3 cross-vertical case studies. Cold outbound to 400." },
      { n: "P3 · MO 6-12", c: "#7c5cff", t: "PARTNER CHANNEL", b: "Local consulting + RPA firms resell. 20% rev-share. Cross-sell in enterprise." },
    ],
  },
  {
    id: 11, kind: "growth",
    eyebrow: "10 · FINANCIALS",
    title: "$2.5M ARR by month 18.",
    rows: [
      { mo: "M3",  paid: "5",  mrr: "$12.5K",  arr: "$150K" },
      { mo: "M6",  paid: "14", mrr: "$53.2K",  arr: "$638K" },
      { mo: "M12", paid: "28", mrr: "$114.8K", arr: "$1.38M" },
      { mo: "M18", paid: "48", mrr: "$211K",   arr: "$2.53M" },
    ],
    foot: "PROFITABLE MONTH 11 · ZERO OUTSIDE CAPITAL REQUIRED",
  },
  {
    id: 12, kind: "team",
    eyebrow: "11 · TEAM",
    title: "Three operators.\nOne console.",
    members: [
      { role: "FOUNDER · CEO", note: "10+ years freight ops / 3PL. Holds the rolodex. Sells. Implements.", c: "#ccff00" },
      { role: "FORWARD ENGINEER · M4", note: "Integrates with customer TMS/CRM/EMR/helpdesk. Hired from MRR.", c: "#00ffff" },
      { role: "CUSTOMER SUCCESS · M9", note: "Onboards Fleet customers. Quarterly ops reviews. Cross-vertical playbook.", c: "#7c5cff" },
    ],
  },
  {
    id: 13, kind: "ask",
    eyebrow: "12 · THE ASK",
    title: "Two ways to ride.",
    options: [
      { c: "#ccff00", t: "BECOME A CUSTOMER", b: "20-minute live demo on your data. NDA available. Pilot at half price for the first 5 MSP partners." },
      { c: "#00ffff", t: "BECOME AN ANGEL", b: "$100-250k strategic angel from a Minneapolis operator. We're bootstrapping — no full round required." },
    ],
    foot: "ONEJADES.COM · CUMMINS_OLIVER@YAHOO.COM · +1 (763) 443-4459 · OLIVER CUMMINS",
  },
];

export default function PitchDeck() {
  const [i, setI] = useState(0);
  const total = SLIDES.length;
  const slide = SLIDES[i];

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "ArrowRight" || e.key === " ") setI((x) => Math.min(total - 1, x + 1));
      if (e.key === "ArrowLeft") setI((x) => Math.max(0, x - 1));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [total]);

  const downloadPDF = () => {
    const doc = new jsPDF({ unit: "pt", format: [792, 612], orientation: "landscape" });
    const W = 792, H = 612, M = 48;
    SLIDES.forEach((s, idx) => {
      if (idx > 0) doc.addPage([792, 612], "landscape");
      doc.setFillColor(2, 3, 10);
      doc.rect(0, 0, W, H, "F");
      doc.setTextColor(204, 255, 0);
      doc.setFontSize(9);
      doc.text(s.eyebrow || "", M, M);
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(s.kind === "cover" ? 56 : 38);
      doc.setFont("helvetica", "bold");
      const titleLines = doc.splitTextToSize(s.title || "", W - M * 2);
      doc.text(titleLines, M, M + 70);

      doc.setFont("helvetica", "normal");
      doc.setFontSize(13);
      doc.setTextColor(220, 220, 230);
      let y = M + 70 + titleLines.length * 44 + 24;

      if (s.sub) {
        doc.setTextColor(0, 255, 255);
        const sub = doc.splitTextToSize(s.sub, W - M * 2);
        doc.text(sub, M, y);
        y += sub.length * 18 + 12;
      }
      if (s.bullets) {
        doc.setTextColor(220, 220, 230);
        s.bullets.forEach((b) => {
          const ln = doc.splitTextToSize(`▸ ${b}`, W - M * 2);
          doc.text(ln, M, y);
          y += ln.length * 16 + 4;
        });
      }
      if (s.body) {
        doc.setTextColor(220, 220, 230);
        const ln = doc.splitTextToSize(s.body, W - M * 2);
        doc.text(ln, M, y);
        y += ln.length * 16;
      }
      if (s.grid) {
        s.grid.forEach((g, gi) => {
          const x = M + (gi % 4) * ((W - M * 2) / 4);
          const yy = y + Math.floor(gi / 4) * 80;
          doc.setTextColor(150, 150, 160);
          doc.setFontSize(8);
          doc.text(g.k, x, yy);
          doc.setTextColor(204, 255, 0);
          doc.setFontSize(28);
          doc.setFont("helvetica", "bold");
          doc.text(g.v, x, yy + 32);
          doc.setFont("helvetica", "normal");
        });
      }
      if (s.foot) {
        doc.setFontSize(8);
        doc.setTextColor(0, 255, 255);
        doc.text(s.foot, M, H - M);
      }
      // page number
      doc.setFontSize(9);
      doc.setTextColor(120, 120, 130);
      doc.text(`${idx + 1} / ${SLIDES.length}`, W - M - 30, H - M);
    });
    doc.save("JADE-OS-pitch-deck.pdf");
    toast.success("Deck downloaded.");
  };

  return (
    <div className="bg-console min-h-screen">
      <div className="max-w-[1400px] mx-auto px-6 lg:px-10 py-8 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <PresentationChart size={20} className="text-[#ccff00]" weight="bold" />
          <span className="mono-label text-[#ccff00]">PITCH DECK · {i + 1} / {total}</span>
        </div>
        <div className="flex items-center gap-3">
          <button data-testid="deck-download-btn" onClick={downloadPDF} className="btn-ghost inline-flex items-center gap-2 text-xs">
            <DownloadSimple size={14} weight="bold" /> DOWNLOAD PDF
          </button>
          <div className="flex gap-1">
            <button data-testid="deck-prev-btn" onClick={() => setI((x) => Math.max(0, x - 1))} disabled={i === 0}
              className="btn-ghost text-xs px-3"><CaretLeft size={14} weight="bold" /></button>
            <button data-testid="deck-next-btn" onClick={() => setI((x) => Math.min(total - 1, x + 1))} disabled={i === total - 1}
              className="btn-jade text-xs px-3"><CaretRight size={14} weight="bold" /></button>
          </div>
        </div>
      </div>

      <div className="max-w-[1400px] mx-auto px-6 lg:px-10 pb-16">
        <div className="aspect-[16/9] deck-card relative grid-bg-tight overflow-hidden" data-testid={`slide-${slide.id}`}>
          <CornerBrackets />
          <Slide slide={slide} idx={i} total={total} />
        </div>

        {/* Thumbnails */}
        <div className="mt-6 grid grid-cols-7 sm:grid-cols-13 gap-1.5">
          {SLIDES.map((s, idx) => (
            <button key={s.id} data-testid={`deck-thumb-${s.id}`} onClick={() => setI(idx)}
              className={`aspect-[16/9] text-left p-2 font-mono-tech text-[9px] transition ${idx === i ? "border-[#ccff00] text-[#ccff00]" : "border-white/10 text-white/40"}`}
              style={{ border: `1px solid`, background: idx === i ? "#0a0c18" : "#02030a" }}>
              <div>{String(idx + 1).padStart(2, "0")}</div>
              <div className="truncate text-[8px] text-white/40">{s.eyebrow?.split("·").pop()?.trim() || s.kind}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function Slide({ slide: s, idx, total }) {
  return (
    <div className="absolute inset-0 p-10 lg:p-16 flex flex-col reveal">
      <div className="flex items-center justify-between">
        <span className="mono-label text-[#ccff00]">{s.eyebrow}</span>
        <span className="mono-label text-white/30">{String(idx + 1).padStart(2, "0")} / {String(total).padStart(2, "0")}</span>
      </div>
      <div className="flex-1 mt-8 grid items-center">
        {s.kind === "cover" && (
          <div>
            <h1 className="font-display font-black text-white text-6xl sm:text-8xl tracking-tighter leading-[0.85] glow-lime whitespace-pre-line">{s.title}</h1>
            <p className="mt-8 accent-cyan text-2xl sm:text-3xl font-display">{s.sub}</p>
            <div className="mt-12 mono-label text-white/40">{s.mono}</div>
          </div>
        )}
        {s.kind === "stat" && (
          <div className="grid lg:grid-cols-5 gap-8">
            <h2 className="lg:col-span-2 font-display font-bold text-white text-4xl lg:text-5xl tracking-tight leading-tight whitespace-pre-line">{s.title}</h2>
            <ul className="lg:col-span-3 space-y-3">
              {s.bullets.map((b, i) => (
                <li key={i} className="flex gap-3 text-white/85 text-lg leading-snug border-b border-white/5 pb-3">
                  <span className="font-mono-tech text-[#ccff00]">{String(i + 1).padStart(2, "0")}</span>
                  {b}
                </li>
              ))}
            </ul>
          </div>
        )}
        {s.kind === "diagonal" && (
          <div>
            <h2 className="font-display font-bold text-white text-5xl tracking-tight leading-tight whitespace-pre-line">{s.title}</h2>
            <div className="mt-12 grid grid-cols-2 lg:grid-cols-4 gap-6">
              {s.grid.map((g) => (
                <div key={g.k} className="border-l-2 pl-5" style={{ borderColor: g.c }}>
                  <div className="mono-label text-white/40 mb-2">{g.k}</div>
                  <div className="font-display font-black text-4xl glow-lime" style={{ color: g.c, textShadow: `0 0 22px ${g.c}55` }}>{g.v}</div>
                </div>
              ))}
            </div>
          </div>
        )}
        {s.kind === "split" && (
          <div className="grid lg:grid-cols-3 gap-10">
            <div className="lg:col-span-2">
              <h2 className="font-display font-bold text-white text-5xl tracking-tight leading-tight whitespace-pre-line">{s.title}</h2>
              <p className="mt-6 text-white/75 text-lg leading-relaxed whitespace-pre-line">{s.body}</p>
            </div>
            <div className="border border-white/10 p-6 bg-[#06081a] self-start">
              <div className="mono-label text-[#ccff00] mb-4">{s.side.label}</div>
              <ul className="space-y-3">
                {s.side.items.map((it) => (
                  <li key={it} className="font-mono-tech text-sm text-white/80 flex gap-2"><span className="text-[#00ffff]">▸</span>{it}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
        {s.kind === "agents" && (
          <div>
            <h2 className="font-display font-bold text-white text-5xl tracking-tight leading-tight whitespace-pre-line">{s.title}</h2>
            <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {s.agents.map((a) => (
                <div key={a.n} className="border border-white/10 p-5 bg-[#06081a]">
                  <div className="font-display font-black text-3xl" style={{ color: a.c }}>{a.n}</div>
                  <div className="mono-label mt-3" style={{ color: a.c }}>{a.t}</div>
                  <p className="text-sm text-white/70 mt-2 leading-relaxed">{a.b}</p>
                </div>
              ))}
            </div>
          </div>
        )}
        {s.kind === "verticals" && (
          <div>
            <h2 className="font-display font-bold text-white text-5xl tracking-tight">{s.title}</h2>
            <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {s.verticals.map((v) => (
                <div key={v.n} className="border border-white/10 p-4 bg-[#06081a]">
                  <div className="mono-label" style={{ color: v.c }}>{v.n}</div>
                  <div className="mt-3 font-mono-tech text-xs text-white/60 leading-relaxed">{v.who}</div>
                </div>
              ))}
            </div>
          </div>
        )}
        {s.kind === "tiers" && (
          <div>
            <h2 className="font-display font-bold text-white text-5xl tracking-tight">{s.title}</h2>
            <div className="mt-10 grid lg:grid-cols-3 gap-6">
              {s.tiers.map((t) => (
                <div key={t.n} className="border p-6 bg-[#06081a]" style={{ borderColor: t.c }}>
                  <div className="mono-label" style={{ color: t.c }}>{t.n}</div>
                  <div className="mt-4 flex items-baseline gap-2">
                    <span className="font-display font-black text-white text-4xl">{t.p}</span>
                    <span className="mono-label text-white/40">{t.per}</span>
                  </div>
                  <p className="text-sm text-white/65 mt-4 leading-relaxed">{t.who}</p>
                </div>
              ))}
            </div>
          </div>
        )}
        {s.kind === "gtm" && (
          <div>
            <h2 className="font-display font-bold text-white text-5xl tracking-tight">{s.title}</h2>
            <div className="mt-10 grid lg:grid-cols-3 gap-5">
              {s.phases.map((p) => (
                <div key={p.n} className="border-l-2 pl-5 py-3" style={{ borderColor: p.c }}>
                  <div className="mono-label text-white/40">{p.n}</div>
                  <div className="font-display font-bold text-white text-2xl mt-2">{p.t}</div>
                  <p className="text-sm text-white/70 mt-3 leading-relaxed">{p.b}</p>
                </div>
              ))}
            </div>
          </div>
        )}
        {s.kind === "growth" && (
          <div>
            <h2 className="font-display font-bold text-white text-5xl tracking-tight">{s.title}</h2>
            <table className="w-full mt-10">
              <thead>
                <tr className="border-b border-white/10">
                  {["MONTH","PAID CUSTOMERS","MRR","ARR"].map((h) => (
                    <th key={h} className="mono-label text-white/40 text-left p-4">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {s.rows.map((r) => (
                  <tr key={r.mo} className="border-b border-white/5">
                    <td className="p-4 mono-label text-[#ccff00]">{r.mo}</td>
                    <td className="p-4 font-display text-white text-2xl">{r.paid}</td>
                    <td className="p-4 font-display text-[#00ffff] text-2xl">{r.mrr}</td>
                    <td className="p-4 font-display text-[#7c5cff] text-2xl">{r.arr}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {s.kind === "team" && (
          <div>
            <h2 className="font-display font-bold text-white text-5xl tracking-tight whitespace-pre-line">{s.title}</h2>
            <div className="mt-10 grid lg:grid-cols-3 gap-5">
              {s.members.map((m) => (
                <div key={m.role} className="border border-white/10 p-6 bg-[#06081a]">
                  <div className="mono-label" style={{ color: m.c }}>{m.role}</div>
                  <p className="mt-4 text-white/75 leading-relaxed text-sm">{m.note}</p>
                </div>
              ))}
            </div>
          </div>
        )}
        {s.kind === "ask" && (
          <div>
            <h2 className="font-display font-bold text-white text-5xl tracking-tight">{s.title}</h2>
            <div className="mt-10 grid lg:grid-cols-2 gap-6">
              {s.options.map((o) => (
                <div key={o.t} className="border p-7 bg-[#06081a]" style={{ borderColor: o.c }}>
                  <div className="mono-label" style={{ color: o.c }}>{o.t}</div>
                  <p className="text-white/80 leading-relaxed mt-4 text-lg">{o.b}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      {s.foot && <div className="mono-label text-[#00ffff]">{s.foot}</div>}
    </div>
  );
}
