import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import {
  ArrowRight, Lightning, Files, EnvelopeSimple, GearSix, Headset, Target,
  MapPin, Lock, Check, ChartLineUp, Robot, Briefcase, Truck, Heartbeat,
  Buildings, ShoppingBag, Stethoscope, Gavel, Wrench, Code,
} from "@/lib/icons";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "../components/Brackets";
import { JadeGenesisCard } from "../components/JadeGenesisCard";

const AGENTS = [
  { id: "support", label: "TIER-1 SUPPORT", color: "#ccff00", icon: Headset, title: "Customer Support Agent",
    body: "Auto-triage incoming tickets, route to the right team, draft responses in your brand voice. Sentiment + priority on every ticket.",
    useCase: "Drains the queue while your humans sleep." },
  { id: "sales", label: "LEAD QUALIFICATION", color: "#00ffff", icon: Target, title: "Sales Qualification Agent",
    body: "Score every inbound lead 0–100. Auto-tier hot / warm / cold. Recommend next action. Book the meeting.",
    useCase: "Your AE team stops wasting hours on tire-kickers." },
  { id: "extract", label: "DATA EXTRACTION", color: "#7c5cff", icon: Files, title: "Document & Data Extraction",
    body: "Parse BOLs, invoices, intake forms, EOBs, POs, contracts, claims into clean structured JSON. Detects document type automatically.",
    useCase: "Kill rekey errors. Eliminate the data-entry function." },
  { id: "ops", label: "OPS AUTOMATION", color: "#ff3b8a", icon: GearSix, title: "Operations & Workflow Agent",
    body: "Monitors systems. Triggers actions. Walks decision trees. Production scheduling, order routing, defect classification, escalations.",
    useCase: "Replaces the 'who-should-I-call-about-this' Slack thread." },
  { id: "content", label: "OUTREACH · CONTENT", color: "#ccff00", icon: EnvelopeSimple, title: "Outreach & Content Agent",
    body: "Personalized cold/follow-up emails, product copy, internal updates. Tone matches your industry — operator-blunt or healthcare-courteous.",
    useCase: "Hit the inbox in your voice. Not ChatGPT's." },
  { id: "chat", label: "OPS CO-PILOT", color: "#00ffff", icon: Robot, title: "On-Call Ops Co-Pilot",
    body: "A trained-on-your-vertical chat assistant for your team. Answers tier-1 questions, drafts plans, summarizes data, never sleeps.",
    useCase: "Like having a senior ops lead on Slack 24/7." },
];

const VERTICALS = [
  { id: "freight", icon: Truck, color: "#ccff00", name: "Freight & Logistics", who: "3PLs · Freight brokers · Carriers",
    examples: ["C.H. Robinson", "Coyote", "Bay & Bay", "Werner", "Forward Air"],
    wins: ["Carrier outreach auto-drafted", "BOL/load posting extraction", "Dispatch tier-1 triage"] },
  { id: "manufacturing", icon: Wrench, color: "#00ffff", name: "Manufacturing", who: "Industrial · OEMs · Job shops",
    examples: ["Pentair", "Emerson", "3M", "Donaldson", "Polaris"],
    wins: ["PO + work-order extraction", "Defect & line-down escalation", "Vendor follow-up automation"] },
  { id: "healthcare", icon: Stethoscope, color: "#7c5cff", name: "Healthcare", who: "Health systems · Clinics · Payers",
    examples: ["UnitedHealth · Optum", "Allina", "HealthPartners", "Mayo Clinic"],
    wins: ["Intake form + EOB parsing", "Appointment reminders + reroutes", "Patient inquiry triage · PHI-safe"] },
  { id: "saas", icon: Code, color: "#ff3b8a", name: "SaaS & Tech", who: "B2B SaaS · Platforms · Mid-market",
    examples: ["Securian", "Best Buy", "Bright Health", "Code42", "Jamf"],
    wins: ["Tier-1 support deflection", "Inbound lead scoring + routing", "Renewal + expansion outreach"] },
  { id: "ecommerce", icon: ShoppingBag, color: "#ccff00", name: "E-Commerce & Retail", who: "DTC · Marketplaces · Omnichannel",
    examples: ["Best Buy", "Target.com", "Faribault Mill", "Askov Finlayson"],
    wins: ["Order / return triage", "VIP win-back personalization", "Product copy at scale"] },
  { id: "insurance", icon: Briefcase, color: "#00ffff", name: "Insurance", who: "Carriers · MGAs · Agencies",
    examples: ["Securian", "Travelers · St. Paul", "Allianz Life", "Federated"],
    wins: ["FNOL / claim form extraction", "Reserve guidance assist", "Insured status updates"] },
  { id: "legal", icon: Gavel, color: "#7c5cff", name: "Legal & Compliance", who: "Firms · In-house · Boutiques",
    examples: ["Faegre Drinker", "Robins Kaplan", "Stinson", "Dorsey"],
    wins: ["Client intake + conflict check", "Discovery doc extraction", "Polite drafting in firm voice"] },
  { id: "real_estate", icon: Buildings, color: "#ff3b8a", name: "Real Estate", who: "CRE · Property mgmt · Brokerage",
    examples: ["Cushman & Wakefield · MSP", "Colliers · MSP", "Ryan Companies"],
    wins: ["Lease summary extraction", "Maintenance ticket triage", "Tenant communication drafts"] },
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
        {/* Right gutter — JADE OS quanta device w/ holographic console */}
        <div className="absolute top-0 bottom-0 right-0 w-[46%] hidden lg:block pointer-events-none overflow-hidden">
          <img
            src="https://customer-assets.emergentagent.com/job_mpls-automation-hub/artifacts/7atwkaoe_quanta-1779558560741.png"
            alt="JADE OS · quanta device projecting a holographic operator console"
            data-testid="hero-quanta-image"
            className="absolute inset-0 w-full h-full object-cover object-center"
            loading="eager"
            decoding="async"
          />
          {/* Console-black bleed on the inner edge so it dissolves into the left content */}
          <div
            className="absolute inset-y-0 left-0 w-[26%]"
            style={{ background: "linear-gradient(90deg, #04050d 0%, rgba(4,5,13,0.85) 35%, transparent 100%)" }}
          />
          {/* Subtle jade-lime corner glow to match brand grammar */}
          <div
            className="absolute -bottom-24 -right-24 w-[420px] h-[420px] rounded-full opacity-30"
            style={{ background: "radial-gradient(closest-side, #ccff00aa, transparent 70%)" }}
          />
        </div>
        <div className="absolute top-0 bottom-0 right-0 w-[46%] hidden lg:block grid-bg-tight pointer-events-none mix-blend-overlay opacity-30" />

        <div className="relative max-w-[1400px] mx-auto px-6 lg:px-10 pt-20 lg:pt-28 pb-24 lg:pb-32">
          <div className="bracket-frame p-6 lg:p-10 max-w-3xl reveal">
            <div className="flex items-center gap-3 mb-8">
              <span className="dot" />
              <span className="mono-label text-[#ccff00]">SYSTEM ONLINE · MINNEAPOLIS NODE</span>
            </div>
            <h1 className="font-display font-black text-white text-[64px] sm:text-[88px] lg:text-[120px] leading-[0.85] tracking-tighter glow-lime">
              JADE<br />OS.
            </h1>
            <p className="mt-8 text-xl sm:text-2xl text-white/85 max-w-2xl font-display tracking-tight">
              Universal AI agents that <span className="accent-cyan">run the business</span> — every industry, every team, one console.
            </p>
            <p className="mt-4 text-sm text-white/55 max-w-xl leading-relaxed">
              Six production-grade agents — support, sales-qual, data extraction, ops automation, outreach, and an ops co-pilot — tuned to your vertical out of the box. Built on Claude Sonnet 4.5 and GPT-5.2. No prompt engineering required.
            </p>
            <div className="mt-10 flex flex-wrap gap-3">
              <Link to="/reel" data-testid="hero-cta-reel" className="btn-jade inline-flex items-center gap-2">
                WATCH JADE HANDLE 5 REAL JOBS <ArrowRight size={16} weight="bold" />
              </Link>
              <Link to="/demo" data-testid="hero-cta-demo" className="btn-ghost">OPEN THE CONSOLE</Link>
              <a href="#book" data-testid="hero-cta-book" className="btn-ghost">BOOK A 20-MIN REVIEW</a>
            </div>

            <div className="mt-12 flex flex-wrap gap-2">
              <span className="chip" data-testid="hero-chip-1">10+ INDUSTRIES · TUNED</span>
              <span className="chip chip-cyan" data-testid="hero-chip-2">CLAUDE 4.5 + GPT-5.2</span>
              <span className="chip chip-violet" data-testid="hero-chip-3">SOC2 · HIPAA-READY</span>
            </div>
          </div>
        </div>

        {/* Ticker */}
        <div className="relative border-y border-white/5 bg-[#06081a] py-4 overflow-hidden">
          <div className="ticker-track mono-label text-white/40 whitespace-nowrap">
            {[...Array(2)].map((_, k) => (
              <div key={k} className="flex gap-14">
                <span className="text-[#ccff00]">▲ TICKETS RESOLVED · 6,330</span>
                <span>DOCS PARSED · 21,604</span>
                <span className="text-[#00ffff]">▲ LEADS SCORED · 1,121</span>
                <span>EMAILS DRAFTED · 4,902</span>
                <span className="text-[#7c5cff]">▲ HOURS RECLAIMED · 3,902</span>
                <span>INDUSTRIES SHIPPED · 11</span>
                <span className="text-[#ff3b8a]">▲ AVG TIER-1 RESOLUTION · 38s</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============== LIGHTHOUSE BAND ============== */}
      <section className="relative border-t border-b border-white/5">
        <div className="absolute inset-0 grid-bg-tight pointer-events-none" />
        <div className="relative max-w-[1400px] mx-auto px-6 lg:px-10 py-12 lg:py-16">
          <div className="grid lg:grid-cols-3 gap-10 items-center">
            <div className="lg:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <span className="dot" />
                <span className="mono-label text-[#ff3b8a]">LIGHTHOUSE PROGRAM · APPLICATIONS OPEN</span>
              </div>
              <h2 className="font-display font-bold text-white text-3xl sm:text-5xl tracking-tight leading-tight">
                Five lighthouse seats.<br />
                <span className="accent-cyan">50% off year one for life.</span>
              </h2>
              <p className="mt-4 text-white/65 max-w-2xl leading-relaxed">
                We're picking 5 companies to be the first published JADE OS field reports. White-glove implementation, named forward engineer, locked-in lighthouse pricing — in exchange for permission to publish what we built for you.
              </p>
            </div>
            <div className="flex flex-col gap-3">
              <Link to="/lighthouse" data-testid="lighthouse-band-cta" className="btn-jade inline-flex items-center justify-center gap-2">
                APPLY FOR A LIGHTHOUSE SEAT <ArrowRight size={16} weight="bold" />
              </Link>
              <Link to="/cases" className="btn-ghost text-center text-xs">SEE EXISTING FIELD REPORTS</Link>
            </div>
          </div>
        </div>
      </section>

      {/* ============== MEET JADE · GENESIS ============== */}
      <section className="relative bg-console py-24 lg:py-32 px-6 lg:px-10 border-t border-white/5" data-testid="landing-meet-jade">
        <div className="max-w-[1400px] mx-auto">
          <SectionLabel idx={1} color="#00ffff">MEET JADE</SectionLabel>
          <div className="mb-10 max-w-3xl">
            <h2 className="font-display font-bold text-white text-4xl sm:text-5xl tracking-tight leading-tight">
              This is <span className="accent-jade">Genesis.</span>
              <br />The first image Jade made of herself.
            </h2>
            <p className="mt-5 text-white/65 leading-relaxed text-lg">
              JADE is the AI doing the work. Genesis is the first portrait she generated when asked
              to picture herself — the operator who never sleeps, the one who sorts your inbox while
              you handle the customer, the one who triages the queue before the support team logs
              on. Talk to her below.
            </p>
          </div>
          <JadeGenesisCard />
        </div>
      </section>

      {/* ============== AGENT BENTO ============== */}
      <section className="relative bg-console-2 py-24 lg:py-32 px-6 lg:px-10">
        <div className="max-w-[1400px] mx-auto">
          <SectionLabel idx={1} color="#ccff00">THE FLEET</SectionLabel>
          <div className="grid lg:grid-cols-2 gap-10 mb-12">
            <h2 className="font-display font-bold text-white text-4xl sm:text-5xl tracking-tight">
              Six agents.<br />Any industry.<br /><span className="accent-cyan">One console.</span>
            </h2>
            <p className="text-white/65 leading-relaxed mt-2 max-w-xl">
              Every agent ships pre-tuned for freight, healthcare, SaaS, manufacturing, e-commerce, insurance, legal, real estate, and pro services. Same console — different lexicon, different playbooks, same operator-grade output.
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
                  <p className="text-sm text-white/65 leading-relaxed">{a.body}</p>
                  <div className="mt-5 pt-4 border-t border-white/5">
                    <div className="mono-label text-white/40 mb-1">RESULT</div>
                    <div className="accent-cyan text-sm">{a.useCase}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ============== INDUSTRIES (universal) ============== */}
      <section className="relative bg-console py-24 lg:py-32 px-6 lg:px-10 border-t border-white/5">
        <div className="max-w-[1400px] mx-auto">
          <SectionLabel idx={2} color="#00ffff">VERTICALS · TUNED OUT OF THE BOX</SectionLabel>
          <div className="grid lg:grid-cols-3 gap-12 mb-14">
            <div className="lg:col-span-2">
              <h2 className="font-display font-bold text-white text-4xl sm:text-5xl tracking-tight">
                One platform.<br />
                <span className="accent-cyan">Every industry in MSP.</span>
              </h2>
              <p className="mt-6 text-white/65 leading-relaxed max-w-2xl">
                JADE OS isn't a freight tool with a SaaS wrapper, and it isn't a generic ChatGPT skin. Each agent loads a vertical lexicon, a per-industry document schema, and a tone profile calibrated for that industry's buyer. Switch verticals on the fly.
              </p>
            </div>
            <div className="flex items-center gap-2 text-[#ccff00]">
              <MapPin size={18} weight="bold" />
              <span className="mono-label">44.97° N · 93.26° W</span>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {VERTICALS.map((v) => {
              const Icon = v.icon;
              return (
                <div key={v.id} data-testid={`vertical-${v.id}`} className="deck-card p-6 relative">
                  <CornerBrackets />
                  <div className="flex items-center justify-between mb-4">
                    <Icon size={26} weight="bold" style={{ color: v.color }} />
                    <span className="mono-label" style={{ color: v.color }}>0{VERTICALS.indexOf(v) + 1}</span>
                  </div>
                  <h3 className="font-display font-bold text-white text-lg leading-tight">{v.name}</h3>
                  <div className="mono-label text-white/40 mt-2">{v.who}</div>

                  <div className="mt-5">
                    <div className="mono-label text-white/45 mb-2">QUICK WINS</div>
                    <ul className="space-y-1.5">
                      {v.wins.map((w) => (
                        <li key={w} className="text-xs text-white/75 leading-snug flex gap-2">
                          <span style={{ color: v.color }}>▸</span>{w}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="mt-5 pt-4 border-t border-white/5">
                    <div className="mono-label text-white/40 mb-2">MSP TARGETS</div>
                    <div className="font-mono-tech text-[11px] text-white/60 leading-relaxed">{v.examples.join(" · ")}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ============== HOW IT WORKS ============== */}
      <section className="relative bg-console-2 py-24 lg:py-32 px-6 lg:px-10 border-t border-white/5">
        <div className="max-w-[1400px] mx-auto">
          <SectionLabel idx={3} color="#7c5cff">DEPLOYMENT TAPE</SectionLabel>
          <div className="grid lg:grid-cols-4 gap-6">
            {[
              { n: "01", t: "PICK", c: "#ccff00", b: "Select your vertical and the agents you want. We pre-load the lexicon, schemas, and tone profile. Zero config." },
              { n: "02", t: "FEED", c: "#00ffff", b: "Drop documents, tickets, leads, or transcripts. JADE reads raw — PDF, plain text, CSV, copy-paste from your stack." },
              { n: "03", t: "REVIEW", c: "#7c5cff", b: "Human-in-the-loop approve / edit / kill. Confidence scores on every action. Full audit trail. Zero rogue agents." },
              { n: "04", t: "FIRE", c: "#ff3b8a", b: "Approved actions hit your email, CRM, TMS, EMR, helpdesk via webhook. JADE logs every move. Ship today." },
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
                feats: ["1 agent · any vertical", "Up to 500 runs / mo", "Slack + email delivery", "Email support · 1 business day"] },
              { name: "FLEET", price: "$4,500", per: "/MO", c: "#00ffff", featured: true,
                feats: ["3 agents · any verticals", "Up to 5,000 runs / mo", "Native CRM / TMS / EMR webhooks", "Dedicated Slack channel · same-day"] },
              { name: "VAULT", price: "Custom", per: "ANNUAL", c: "#7c5cff",
                feats: ["Unlimited agents + custom builds", "On-prem / VPC deployment available", "SOC2 + BAA for healthcare", "Quarterly ops review · named engineer"] },
            ].map((t) => (
              <div key={t.name} data-testid={`pricing-${t.name.toLowerCase()}`}
                className={`relative p-8 ${t.featured ? "bg-[#0a0c18]" : "bg-[#06081a]"}`}
                style={{ border: `1px solid ${t.featured ? t.c : "rgba(255,255,255,0.08)"}` }}>
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
              Tell us where your team bleeds hours — in any industry. We come back inside 24 hours with a one-pager: which agent we'd ship first, expected ROI, and a fixed price.
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
              <Field label="OPERATOR · NAME">
                <input data-testid="lead-input-name" className="input-tech" placeholder="Dana Bjornson"
                  value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </Field>
              <Field label="WORK · EMAIL">
                <input data-testid="lead-input-email" type="email" className="input-tech" placeholder="dana@company.com"
                  value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
              </Field>
              <Field label="COMPANY">
                <input data-testid="lead-input-company" className="input-tech" placeholder="Acme Industries"
                  value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
              </Field>
              <Field label="PHONE · OPTIONAL">
                <input data-testid="lead-input-phone" className="input-tech" placeholder="(763) 443-4459"
                  value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              </Field>
              <Field label="INDUSTRY">
                <select data-testid="lead-input-vertical" className="input-tech"
                  value={form.vertical} onChange={(e) => setForm({ ...form, vertical: e.target.value })}>
                  <option value="freight_brokerage">Freight Brokerage / 3PL</option>
                  <option value="logistics">Logistics / Carrier</option>
                  <option value="manufacturing">Manufacturing</option>
                  <option value="healthcare">Healthcare</option>
                  <option value="saas">SaaS / Tech</option>
                  <option value="ecommerce">E-Commerce / Retail</option>
                  <option value="insurance">Insurance</option>
                  <option value="legal">Legal</option>
                  <option value="real_estate">Real Estate / Property Mgmt</option>
                  <option value="professional_services">Professional Services / Agencies</option>
                  <option value="general">Other / General</option>
                </select>
              </Field>
              <Field label="MONTHLY VOLUME">
                <input data-testid="lead-input-volume" className="input-tech" placeholder="~500 tickets · 1k docs · 200 leads"
                  value={form.monthly_volume} onChange={(e) => setForm({ ...form, monthly_volume: e.target.value })} />
              </Field>
              <div className="sm:col-span-2">
                <Field label="USE CASE · WHERE YOU'RE BLEEDING HOURS">
                  <textarea data-testid="lead-input-use-case" rows="4" className="input-tech"
                    placeholder="Support queue overflowing. Manual data entry from PDFs. AEs drowning in unqualified leads."
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

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="mono-label text-white/45 block mb-2">{label}</span>
      {children}
    </label>
  );
}
