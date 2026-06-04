import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { ArrowRight, Truck, Lightning, Brain, Files, EnvelopeSimple, GearSix, Headset, Target, MapPin, ChartLineUp, Lock, Check, Code } from "@phosphor-icons/react";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "../components/Brackets";

const AGENTS = [
  { id: "support", label: "TIER-1 SUPPORT", color: "#ccff00", icon: Headset, title: "Customer Support Agent", body: "Tier-1 ticket triage, FAQ routing, escalation logic. Drains the queue while your humans sleep." },
  { id: "sales", label: "LEAD QUAL", color: "#00ffff", icon: Target, title: "Sales Qualification Agent", body: "Auto-score by firmographics + behavior. Routes hot leads. Books meetings. Kills cold ones." },
  { id: "extract", label: "DATA EXTRACTION", color: "#7c5cff", icon: Files, title: "Document & Data Extraction", body: "BOLs, rate cons, invoices, manifests, intake forms — into clean structured JSON. PDF or paste." },
  { id: "ops", label: "OPS AUTOMATION", color: "#ff3b8a", icon: GearSix, title: "Operations & Workflow Agent", body: "Watches systems. Triggers actions. Walks decision trees. Production scheduling, order routing, defect calls." },
  { id: "content", label: "OUTREACH", color: "#ccff00", icon: EnvelopeSimple, title: "Outreach & Content Agent", body: "Personalized follow-ups, carrier emails, product copy. Hits the inbox in your voice, not ChatGPT's." },
  { id: "freight", label: "FLAGSHIP · MPLS", color: "#00ffff", icon: Truck, title: "Freight Broker Co-Pilot", body: "Load matching, carrier comms, lane analytics. Built for 3PLs and brokers in the upper Midwest." },
];

const TARGETS = [
  { vertical: "FREIGHT & 3PL", names: ["C.H. Robinson", "Coyote", "Werner", "Bay & Bay", "Forward Air", "Allen Lund"] },
  { vertical: "TECH & SAAS", names: ["Securian", "Ecolab", "Best Buy", "Hormel", "Cargill"] },
  { vertical: "HEALTHCARE", names: ["UnitedHealth · Optum", "Allina", "HealthPartners", "Mayo (Rochester)"] },
  { vertical: "MANUFACTURING", names: ["Pentair", "Emerson", "3M", "Donaldson", "Polaris"] },
];

export default function Landing() {
  const [form, setForm] = useState({
    name: "", email: "", company: "", phone: "", vertical: "freight_brokerage", use_case: "", monthly_volume: ""
  });
  const [submitting, setSubmitting] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.company) {
      toast.error("Name, work email, and company required, operator.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/leads", form);
      toast.success("Locked in. We'll be in touch inside 24 hours.");
      setForm({ name: "", email: "", company: "", phone: "", vertical: "freight_brokerage", use_case: "", monthly_volume: "" });
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not submit. Try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      {/* ============== HERO ============== */}
      <section className="relative overflow-hidden bg-console">
        <div className="absolute inset-0 grid-bg pointer-events-none" />
        <div className="absolute inset-0 scanlines pointer-events-none" />
        {/* Lime curtain on the right like the brand poster */}
        <div
          className="absolute top-0 bottom-0 right-0 w-[42%] hidden lg:block opacity-95"
          style={{
            background: "linear-gradient(110deg, transparent 0%, rgba(204,255,0,0.55) 35%, #b5e600 100%)",
          }}
        />
        <div className="absolute top-0 bottom-0 right-0 w-[42%] hidden lg:block grid-bg-tight pointer-events-none" />

        <div className="relative max-w-[1400px] mx-auto px-6 lg:px-10 pt-20 lg:pt-32 pb-24 lg:pb-40">
          <div className="bracket-frame p-6 lg:p-10 max-w-3xl reveal">
            <div className="flex items-center gap-3 mb-8">
              <span className="dot" />
              <span className="mono-label text-[#ccff00]">SYSTEM ONLINE · MINNEAPOLIS NODE</span>
            </div>
            <h1 className="font-display font-black text-white text-[64px] sm:text-[88px] lg:text-[120px] leading-[0.85] tracking-tighter glow-lime">
              JADE<br />OS.
            </h1>
            <p className="mt-8 text-xl sm:text-2xl text-white/85 max-w-xl font-display tracking-tight">
              AI agents that <span className="accent-cyan">run the dock door</span> — freight, support, ops, sales.
            </p>
            <p className="mt-4 text-sm text-white/55 max-w-lg leading-relaxed">
              Production-grade agents for Minneapolis operators. Built on Claude, GPT, and a freight-trained playbook. No demo theater. Real loads. Real tickets. Real revenue.
            </p>
            <div className="mt-10 flex flex-wrap gap-3">
              <Link to="/demo" data-testid="hero-cta-demo" className="btn-jade inline-flex items-center gap-2">
                PASTE A LOAD · WATCH JADE WORK <ArrowRight size={16} weight="bold" />
              </Link>
              <a href="#book" data-testid="hero-cta-book" className="btn-ghost">BOOK A 20-MIN OPS REVIEW</a>
            </div>

            <div className="mt-12 flex flex-wrap gap-2">
              <span className="chip" data-testid="hero-chip-1">AGENTIC · CLAUDE 4.5</span>
              <span className="chip chip-cyan" data-testid="hero-chip-2">FREIGHT · 3PL · MFG · HEALTH</span>
              <span className="chip chip-violet" data-testid="hero-chip-3">SOC2 · OPS-GRADE</span>
            </div>
          </div>

          {/* Diagonal data line — purely decorative */}
          <svg className="hidden lg:block absolute right-[6%] bottom-[12%] w-[420px]" viewBox="0 0 420 180" fill="none">
            <polyline points="0,140 80,90 160,120 240,40 320,80 420,20" stroke="#02030a" strokeWidth="2" strokeOpacity="0.6" />
            {[[0,140],[80,90],[160,120],[240,40],[320,80],[420,20]].map(([x,y], i) => (
              <circle key={i} cx={x} cy={y} r="4" fill="#02030a" />
            ))}
          </svg>
        </div>

        {/* Ticker */}
        <div className="relative border-y border-white/5 bg-[#06081a] py-4 overflow-hidden">
          <div className="ticker-track mono-label text-white/40 whitespace-nowrap">
            {[...Array(2)].map((_, k) => (
              <div key={k} className="flex gap-14">
                <span className="text-[#ccff00]">▲ LOAD MATCH 99.2%</span>
                <span>CARRIERS RESPONDED · 1,418</span>
                <span className="text-[#00ffff]">▲ DISPATCHER HOURS RECLAIMED · 3,902</span>
                <span>BOLS PARSED · 21,604</span>
                <span className="text-[#7c5cff]">▲ TICKETS RESOLVED · 6,330</span>
                <span>AVG TIER-1 RESOLUTION · 38s</span>
                <span className="text-[#ff3b8a]">▲ LEADS SCORED · 1,121</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============== AGENT BENTO ============== */}
      <section className="relative bg-console-2 py-24 lg:py-32 px-6 lg:px-10">
        <div className="max-w-[1400px] mx-auto">
          <SectionLabel idx={1} color="#ccff00">THE FLEET</SectionLabel>
          <div className="grid lg:grid-cols-2 gap-10 mb-12">
            <h2 className="font-display font-bold text-white text-4xl sm:text-5xl tracking-tight">
              Six agents.<br />One operator console.
            </h2>
            <p className="text-white/65 leading-relaxed mt-2 max-w-xl">
              JADE OS wraps Claude Sonnet 4.5, GPT-5.2, and a freight-trained system prompt into agents your dispatchers, ops leads, and revenue team actually use. <span className="accent-cyan">No prompt engineering required.</span>
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {AGENTS.map((a) => {
              const Icon = a.icon;
              return (
                <div key={a.id} data-testid={`agent-card-${a.id}`} className="deck-card p-7 relative">
                  <CornerBrackets />
                  <div className="flex items-start justify-between mb-6">
                    <Icon size={28} weight="bold" style={{ color: a.color }} />
                    <span className="mono-label" style={{ color: a.color }}>{a.label}</span>
                  </div>
                  <h3 className="font-display font-bold text-white text-xl mb-2">{a.title}</h3>
                  <p className="text-sm text-white/60 leading-relaxed">{a.body}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ============== TARGET ACCOUNTS ============== */}
      <section className="relative bg-console py-24 lg:py-32 px-6 lg:px-10 border-t border-white/5">
        <div className="max-w-[1400px] mx-auto">
          <SectionLabel idx={2} color="#00ffff">TARGET MAP · MSP</SectionLabel>
          <div className="grid lg:grid-cols-3 gap-12">
            <div className="lg:col-span-1">
              <h2 className="font-display font-bold text-white text-4xl tracking-tight mb-4">
                Built for the<br />
                <span className="accent-cyan text-4xl">Twin Cities ledger.</span>
              </h2>
              <p className="text-white/60 text-sm leading-relaxed">
                Minneapolis runs on freight, healthcare, and quiet midwest manufacturers. JADE OS is calibrated for the workflows of operators here — not silicon-valley vibes.
              </p>
              <div className="mt-8 flex items-center gap-2 text-[#ccff00]">
                <MapPin size={18} weight="bold" />
                <span className="mono-label">44.97° N · 93.26° W</span>
              </div>
            </div>
            <div className="lg:col-span-2 grid sm:grid-cols-2 gap-4">
              {TARGETS.map((t, i) => (
                <div key={t.vertical} data-testid={`target-${i}`} className="deck-card p-6 relative">
                  <div className="mono-label text-[#ccff00] mb-4">{t.vertical}</div>
                  <ul className="space-y-2">
                    {t.names.map((n) => (
                      <li key={n} className="font-mono-tech text-sm text-white/75 flex items-center gap-2">
                        <span className="text-[#7c5cff]">▶</span> {n}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ============== HOW IT WORKS ============== */}
      <section className="relative bg-console-2 py-24 lg:py-32 px-6 lg:px-10 border-t border-white/5">
        <div className="max-w-[1400px] mx-auto">
          <SectionLabel idx={3} color="#7c5cff">DEPLOYMENT TAPE</SectionLabel>
          <div className="grid lg:grid-cols-4 gap-6">
            {[
              { n: "01", t: "PASTE", c: "#ccff00", b: "Drop a load posting, BOL, ticket, or lead form. JADE reads it raw — PDF, plain text, copy-paste from your TMS." },
              { n: "02", t: "DECODE", c: "#00ffff", b: "Agents extract structured fields, score the lead, or draft the carrier outreach. You see the work as it runs." },
              { n: "03", t: "REVIEW", c: "#7c5cff", b: "Human-in-the-loop approve / edit / kill. Confidence scores on every action. No silent rogue agents." },
              { n: "04", t: "FIRE", c: "#ff3b8a", b: "Approved actions hit your email, CRM, TMS via webhook. JADE logs every move for audit." },
            ].map((s) => (
              <div key={s.n} className="deck-card p-7 relative">
                <CornerBrackets />
                <div className="font-display font-black text-[64px] leading-none" style={{ color: s.c }}>{s.n}</div>
                <div className="mt-3 mono-label text-white/40">PHASE</div>
                <h3 className="mt-1 font-display font-bold text-white text-xl">{s.t}</h3>
                <p className="text-sm text-white/60 leading-relaxed mt-3">{s.b}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============== PRICING ============== */}
      <section className="relative bg-console py-24 lg:py-32 px-6 lg:px-10 border-t border-white/5">
        <div className="max-w-[1400px] mx-auto">
          <SectionLabel idx={4} color="#ccff00">VAULT TIERS</SectionLabel>
          <h2 className="font-display font-bold text-white text-4xl sm:text-5xl tracking-tight mb-12 max-w-2xl">
            Pricing that reads like a <span className="accent-cyan">rate confirmation.</span>
          </h2>
          <div className="grid md:grid-cols-3 gap-5">
            {[
              { name: "DISPATCH", price: "$1,500", per: "/MO", c: "#ccff00",
                feats: ["1 agent · Freight Co-Pilot OR Tier-1 Support", "Up to 500 runs / mo", "Slack + email delivery", "Email support · 1 business day"] },
              { name: "FLEET", price: "$4,500", per: "/MO", c: "#00ffff", featured: true,
                feats: ["3 agents · pick any from the deck", "Up to 5,000 runs / mo", "Native CRM + TMS webhooks", "Dedicated Slack channel · same-day"] },
              { name: "VAULT", price: "Custom", per: "ANNUAL", c: "#7c5cff",
                feats: ["Unlimited agents + custom builds", "On-prem / VPC deployment available", "SOC2 + BAA for healthcare", "Quarterly ops review · named engineer"] },
            ].map((t) => (
              <div
                key={t.name}
                data-testid={`pricing-${t.name.toLowerCase()}`}
                className={`relative p-8 ${t.featured ? "bg-[#0a0c18]" : "bg-[#06081a]"}`}
                style={{ border: `1px solid ${t.featured ? t.c : "rgba(255,255,255,0.08)"}` }}
              >
                {t.featured && <div className="absolute -top-3 left-6 px-2 py-1 bg-[#00ffff] text-[#02030a] mono-label font-bold">MOST FLEETS</div>}
                <div className="mono-label" style={{ color: t.c }}>{t.name}</div>
                <div className="mt-4 flex items-baseline gap-2">
                  <span className="font-display font-black text-white text-5xl">{t.price}</span>
                  <span className="mono-label text-white/40">{t.per}</span>
                </div>
                <ul className="mt-8 space-y-3 text-sm text-white/70">
                  {t.feats.map((f) => (
                    <li key={f} className="flex gap-3"><Check size={16} className="mt-0.5" style={{ color: t.c }} weight="bold" />{f}</li>
                  ))}
                </ul>
                <a href="#book" data-testid={`pricing-cta-${t.name.toLowerCase()}`} className={t.featured ? "btn-jade mt-8 block text-center" : "btn-ghost mt-8 block text-center"}>BOOK · {t.name}</a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============== BOOK A DEMO FORM ============== */}
      <section id="book" className="relative bg-console-2 py-24 lg:py-32 px-6 lg:px-10 border-t border-white/5">
        <div className="max-w-[1400px] mx-auto grid lg:grid-cols-5 gap-12">
          <div className="lg:col-span-2">
            <SectionLabel idx={5} color="#00ffff">CAPTURE</SectionLabel>
            <h2 className="font-display font-bold text-white text-4xl sm:text-5xl tracking-tight">
              Book a<br />
              <span className="accent-cyan">20-minute</span><br />
              ops review.
            </h2>
            <p className="mt-6 text-white/60 leading-relaxed max-w-md">
              Tell us where your team bleeds hours. We come back inside 24 hours with a one-pager: which agent we'd ship first, expected ROI, and a fixed price.
            </p>
            <div className="mt-8 space-y-3 text-sm text-white/60">
              <div className="flex items-center gap-3"><Lightning size={16} className="text-[#ccff00]" weight="bold" /><span>Live demo on YOUR data</span></div>
              <div className="flex items-center gap-3"><Lock size={16} className="text-[#ccff00]" weight="bold" /><span>NDA available · zero data retention</span></div>
              <div className="flex items-center gap-3"><ChartLineUp size={16} className="text-[#ccff00]" weight="bold" /><span>ROI estimate inside 24h</span></div>
            </div>
          </div>

          <form onSubmit={submit} className="lg:col-span-3 deck-card p-8 lg:p-10 relative" data-testid="lead-form">
            <CornerBrackets />
            <div className="grid sm:grid-cols-2 gap-5">
              <Field label="OPERATOR · NAME" testid="lead-name">
                <input data-testid="lead-input-name" className="input-tech" placeholder="Dana Bjornson"
                  value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </Field>
              <Field label="WORK · EMAIL" testid="lead-email">
                <input data-testid="lead-input-email" type="email" className="input-tech" placeholder="dana@northstarbroker.com"
                  value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </Field>
              <Field label="COMPANY" testid="lead-company">
                <input data-testid="lead-input-company" className="input-tech" placeholder="Northstar Broker"
                  value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
              </Field>
              <Field label="PHONE · OPTIONAL" testid="lead-phone">
                <input data-testid="lead-input-phone" className="input-tech" placeholder="(612) 555-0117"
                  value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              </Field>
              <Field label="VERTICAL" testid="lead-vertical">
                <select data-testid="lead-input-vertical" className="input-tech"
                  value={form.vertical} onChange={(e) => setForm({ ...form, vertical: e.target.value })}>
                  <option value="freight_brokerage">Freight Brokerage / 3PL</option>
                  <option value="logistics">Logistics / Carrier</option>
                  <option value="manufacturing">Manufacturing</option>
                  <option value="healthcare">Healthcare</option>
                  <option value="saas">SaaS / Tech</option>
                  <option value="real_estate">Real Estate / Property Mgmt</option>
                  <option value="other">Other</option>
                </select>
              </Field>
              <Field label="MONTHLY VOLUME" testid="lead-volume">
                <input data-testid="lead-input-volume" className="input-tech" placeholder="~500 loads / mo · 1k tickets · etc."
                  value={form.monthly_volume} onChange={(e) => setForm({ ...form, monthly_volume: e.target.value })} />
              </Field>
              <div className="sm:col-span-2">
                <Field label="USE CASE · WHERE YOU'RE BLEEDING HOURS" testid="lead-use-case">
                  <textarea data-testid="lead-input-use-case" rows="4" className="input-tech"
                    placeholder="Carrier outreach takes 2 dispatchers all day. BOL data entry is killing margin. Tier-1 ticket flood."
                    value={form.use_case} onChange={(e) => setForm({ ...form, use_case: e.target.value })} />
                </Field>
              </div>
            </div>
            <div className="mt-7 flex flex-wrap items-center gap-4">
              <button data-testid="lead-submit-btn" disabled={submitting} className="btn-jade inline-flex items-center gap-2">
                {submitting ? "COMPILING…" : <>LOCK IT IN <ArrowRight size={16} weight="bold" /></>}
              </button>
              <span className="mono-label text-white/35">RESPONSE · {"<"} 24H</span>
            </div>
          </form>
        </div>
      </section>
    </div>
  );
}

function Field({ label, children, testid }) {
  return (
    <label className="block" data-testid={testid && `${testid}-label`}>
      <span className="mono-label text-white/45 block mb-2">{label}</span>
      {children}
    </label>
  );
}
