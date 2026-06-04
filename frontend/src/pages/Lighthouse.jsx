import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Link } from "react-router-dom";
import { ArrowRight, Check, Lock, Lightning, ChartLineUp, MapPin } from "@/lib/icons";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "../components/Brackets";

const PAIN_OPTIONS = [
  { id: "support_overflow", label: "Tier-1 support queue is drowning the team" },
  { id: "doc_overload", label: "Manual data entry from PDFs / forms is eating hours" },
  { id: "lead_chaos", label: "Sales team can't qualify inbound leads fast enough" },
  { id: "ops_drift", label: "Repetitive ops decisions / escalations slow us down" },
  { id: "content_grind", label: "Outbound email / content production is a grind" },
  { id: "other", label: "Other — I'll describe below" },
];

const INDUSTRIES = [
  "freight_brokerage","logistics","manufacturing","healthcare","saas",
  "ecommerce","insurance","legal","real_estate","professional_services","general",
];

const EMPTY = {
  name: "", title: "", email: "", phone: "",
  company: "", industry: "freight_brokerage", company_size: "11-50", website: "",
  primary_pain: "support_overflow", pain_detail: "", target_outcome: "",
  timeline: "30_days", decision_authority: "decision_maker", budget_band: "1500_4500",
  case_study_consent: false, logo_consent: false, quote_consent: false, metrics_consent: false,
};

export default function Lighthouse() {
  const [stats, setStats] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api.get("/lighthouse/stats").then((r) => setStats(r.data)).catch(() => {});
  }, []);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.company || !form.pain_detail || !form.target_outcome) {
      toast.error("Operator, name + email + company + pain + outcome required.");
      return;
    }
    if (!form.case_study_consent) {
      toast.error("The lighthouse program requires case-study consent. That's the deal.");
      return;
    }
    setSubmitting(true);
    try {
      const { data } = await api.post("/lighthouse/apply", form);
      setResult(data);
      toast.success("Application captured. JADE is scoring it now.");
      api.get("/lighthouse/stats").then((r) => setStats(r.data));
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Submit failed.");
    } finally { setSubmitting(false); }
  };

  return (
    <div className="bg-console min-h-screen">
      {/* HERO */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 grid-bg pointer-events-none" />
        <div className="absolute inset-0 scanlines pointer-events-none" />
        <div className="absolute top-0 bottom-0 right-0 w-[38%] hidden lg:block opacity-95"
          style={{ background: "linear-gradient(110deg, transparent 0%, rgba(0,255,255,0.45) 35%, #00e6e6 100%)" }} />
        <div className="relative max-w-[1400px] mx-auto px-6 lg:px-10 pt-16 lg:pt-24 pb-16">
          <div className="bracket-frame p-6 lg:p-10 max-w-3xl reveal">
            <div className="flex items-center gap-3 mb-6">
              <span className="dot" />
              <span className="mono-label text-[#00ffff]">LIGHTHOUSE PROGRAM · APPLICATIONS OPEN</span>
            </div>
            <h1 className="font-display font-black text-white text-[56px] sm:text-[80px] lg:text-[100px] leading-[0.85] tracking-tighter">
              FIVE<br />
              <span className="accent-cyan">LIGHTHOUSE</span><br />
              SEATS.
            </h1>
            <p className="mt-8 text-xl text-white/85 max-w-xl font-display tracking-tight">
              We're picking 5 companies to be the first JADE OS field reports — <span className="accent-cyan">at 50% off year one</span>.
            </p>
            <p className="mt-4 text-sm text-white/55 max-w-lg leading-relaxed">
              You give us a real workflow + permission to publish the results. We give you white-glove implementation, a named forward engineer, co-marketing, and locked-in lighthouse pricing for life. The deal is simple. The seats are not refilled.
            </p>

            {stats && (
              <div className="mt-8 flex flex-wrap gap-3" data-testid="lighthouse-counter">
                <div className="border border-[#ccff00] px-4 py-3">
                  <div className="mono-label text-[#ccff00]">SEATS REMAINING</div>
                  <div className="font-display font-black text-white text-3xl mt-1">{stats.slots_remaining} <span className="text-white/35 text-base font-mono-tech">/ {stats.slots_total}</span></div>
                </div>
                <div className="border border-[#00ffff] px-4 py-3">
                  <div className="mono-label text-[#00ffff]">APPLICATIONS IN</div>
                  <div className="font-display font-black text-white text-3xl mt-1">{stats.total_applications}</div>
                </div>
                <div className="border border-[#7c5cff] px-4 py-3">
                  <div className="mono-label text-[#7c5cff]">SELECTED · ACTIVE</div>
                  <div className="font-display font-black text-white text-3xl mt-1">{stats.selected_or_active}</div>
                </div>
              </div>
            )}

            <div className="mt-10 flex flex-wrap gap-3">
              <a href="#apply" data-testid="lh-cta-apply" className="btn-jade inline-flex items-center gap-2">
                APPLY FOR A LIGHTHOUSE SEAT <ArrowRight size={16} weight="bold" />
              </a>
              <Link to="/cases" data-testid="lh-cta-cases" className="btn-ghost">READ EXISTING FIELD REPORTS</Link>
            </div>
          </div>
        </div>
      </section>

      {/* THE DEAL */}
      <section className="bg-console-2 px-6 lg:px-10 py-20 border-t border-white/5">
        <div className="max-w-[1400px] mx-auto">
          <SectionLabel idx={1} color="#ccff00">THE DEAL</SectionLabel>
          <div className="grid lg:grid-cols-2 gap-12 mb-14">
            <h2 className="font-display font-bold text-white text-4xl sm:text-5xl tracking-tight">
              You give.<br /><span className="accent-cyan">We give.</span>
            </h2>
            <p className="text-white/65 leading-relaxed max-w-xl">
              Lighthouse partnerships are a 90-day handshake. We build the agent on your real workflow. You let us measure and publish what happened. Both sides win — or we both walk.
            </p>
          </div>
          <div className="grid lg:grid-cols-2 gap-6">
            <div className="deck-card p-7 relative" data-testid="deal-you">
              <CornerBrackets />
              <div className="mono-label text-[#ff3b8a] mb-4">YOU GIVE</div>
              <ul className="space-y-3 text-sm text-white/85">
                {[
                  "A real production workflow we can build for (not a hypothetical)",
                  "A weekly 30-min check-in for 90 days with a decision-maker",
                  "Permission to measure outcomes and publish a case study",
                  "Logo, quote, and metrics rights for marketing",
                  "Honest feedback — including 'this doesn't work'",
                ].map((x) => <li key={x} className="flex gap-3"><Check size={16} className="text-[#ff3b8a] mt-0.5" weight="bold" />{x}</li>)}
              </ul>
            </div>
            <div className="deck-card p-7 relative" data-testid="deal-we">
              <CornerBrackets />
              <div className="mono-label text-[#ccff00] mb-4">WE GIVE</div>
              <ul className="space-y-3 text-sm text-white/85">
                {[
                  "50% off year one — locked in for life as a lighthouse",
                  "White-glove implementation with a named forward engineer",
                  "Custom schema + playbook built for YOUR workflow",
                  "Slack channel · response within 4 business hours",
                  "Co-marketing: case study, joint webinar, conference shout-outs",
                  "Out-clause: 30 days notice, no termination fee, ever",
                ].map((x) => <li key={x} className="flex gap-3"><Check size={16} className="text-[#ccff00] mt-0.5" weight="bold" />{x}</li>)}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* IDEAL FIT */}
      <section className="bg-console px-6 lg:px-10 py-20 border-t border-white/5">
        <div className="max-w-[1400px] mx-auto">
          <SectionLabel idx={2} color="#00ffff">IDEAL FIT</SectionLabel>
          <h2 className="font-display font-bold text-white text-4xl sm:text-5xl tracking-tight mb-10">
            Who we're looking for.
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              { c: "#ccff00", t: "11-500 EMPLOYEES", b: "Mid-market sweet spot. Big enough to have real volume, small enough to ship in 30 days." },
              { c: "#00ffff", t: "DECISION-MAKER", b: "VP / Director / Founder who owns the budget and the workflow." },
              { c: "#7c5cff", t: "MEASURABLE PAIN", b: "Hours bleeding somewhere. You can articulate before/after in one sentence." },
              { c: "#ff3b8a", t: "30-DAY PILOT", b: "You can commit to a real pilot in the next 30 days. Not 'someday Q3'." },
            ].map((x) => (
              <div key={x.t} className="deck-card p-6 relative">
                <CornerBrackets />
                <div className="mono-label" style={{ color: x.c }}>{x.t}</div>
                <p className="text-sm text-white/65 mt-4 leading-relaxed">{x.b}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* APPLY */}
      <section id="apply" className="bg-console-2 px-6 lg:px-10 py-20 border-t border-white/5">
        <div className="max-w-[1400px] mx-auto grid lg:grid-cols-5 gap-12">
          <div className="lg:col-span-2">
            <SectionLabel idx={3} color="#ff3b8a">APPLY</SectionLabel>
            <h2 className="font-display font-bold text-white text-4xl sm:text-5xl tracking-tight">
              Throw your<br /><span className="accent-cyan">hat in.</span>
            </h2>
            <p className="mt-6 text-white/65 leading-relaxed max-w-md">
              JADE scores every application in seconds using the same lead-qualification agent we sell. Hot applicants get a 20-minute discovery call inside 48 hours. Cold ones get a polite pass.
            </p>
            <div className="mt-8 space-y-3 text-sm text-white/60">
              <Row icon={Lightning} c="#ccff00" t="Scored by JADE in real time" />
              <Row icon={Lock} c="#ccff00" t="NDA-friendly · zero data retention" />
              <Row icon={ChartLineUp} c="#ccff00" t="Hot applicants → 20-min call < 48h" />
              <Row icon={MapPin} c="#ccff00" t="Onsite preferred · MSP-based" />
            </div>
          </div>

          {!result && (
            <form onSubmit={submit} className="lg:col-span-3 deck-card p-8 lg:p-10 relative space-y-6" data-testid="lighthouse-form">
              <CornerBrackets />

              {/* Operator */}
              <Group label="01 · OPERATOR">
                <div className="grid sm:grid-cols-2 gap-4">
                  <Field label="NAME"><input data-testid="lh-name" className="input-tech" value={form.name} onChange={(e) => set("name", e.target.value)} /></Field>
                  <Field label="TITLE"><input data-testid="lh-title" className="input-tech" placeholder="VP Operations" value={form.title} onChange={(e) => set("title", e.target.value)} /></Field>
                  <Field label="WORK EMAIL"><input data-testid="lh-email" type="email" className="input-tech" value={form.email} onChange={(e) => set("email", e.target.value)} /></Field>
                  <Field label="PHONE · OPTIONAL"><input data-testid="lh-phone" className="input-tech" value={form.phone} onChange={(e) => set("phone", e.target.value)} /></Field>
                </div>
              </Group>

              {/* Company */}
              <Group label="02 · COMPANY">
                <div className="grid sm:grid-cols-2 gap-4">
                  <Field label="COMPANY NAME"><input data-testid="lh-company" className="input-tech" value={form.company} onChange={(e) => set("company", e.target.value)} /></Field>
                  <Field label="INDUSTRY">
                    <select data-testid="lh-industry" className="input-tech" value={form.industry} onChange={(e) => set("industry", e.target.value)}>
                      {INDUSTRIES.map((i) => <option key={i} value={i}>{i.replace(/_/g," ").toUpperCase()}</option>)}
                    </select>
                  </Field>
                  <Field label="COMPANY SIZE">
                    <select data-testid="lh-size" className="input-tech" value={form.company_size} onChange={(e) => set("company_size", e.target.value)}>
                      {["1-10","11-50","51-200","201-1000","1000+"].map((s) => <option key={s}>{s}</option>)}
                    </select>
                  </Field>
                  <Field label="WEBSITE"><input data-testid="lh-website" className="input-tech" placeholder="https://" value={form.website} onChange={(e) => set("website", e.target.value)} /></Field>
                </div>
              </Group>

              {/* Pain */}
              <Group label="03 · THE BLEED">
                <Field label="WHERE ARE YOU BLEEDING HOURS?">
                  <div className="grid gap-2">
                    {PAIN_OPTIONS.map((p) => (
                      <label key={p.id} className="flex items-center gap-3 cursor-pointer border border-white/10 px-4 py-3 hover:border-white/30"
                        style={{ borderColor: form.primary_pain === p.id ? "#ccff00" : undefined, background: form.primary_pain === p.id ? "#ccff0011" : undefined }}>
                        <input data-testid={`lh-pain-${p.id}`} type="radio" name="pain" checked={form.primary_pain === p.id} onChange={() => set("primary_pain", p.id)} className="accent-[#ccff00]" />
                        <span className="font-mono-tech text-xs text-white/80">{p.label}</span>
                      </label>
                    ))}
                  </div>
                </Field>
                <Field label="DESCRIBE THE WORKFLOW · WHAT'S BROKEN?">
                  <textarea data-testid="lh-pain-detail" className="input-tech" rows={4} placeholder="Our 6-person support team handles 3,200 tickets/month. 60% are FAQ-able. Tier-1 response time is 11 hours."
                    value={form.pain_detail} onChange={(e) => set("pain_detail", e.target.value)} />
                </Field>
                <Field label="TARGET OUTCOME · ONE SENTENCE">
                  <input data-testid="lh-outcome" className="input-tech" placeholder="Cut tier-1 first response from 11h to under 1h"
                    value={form.target_outcome} onChange={(e) => set("target_outcome", e.target.value)} />
                </Field>
              </Group>

              {/* Fit */}
              <Group label="04 · FIT">
                <div className="grid sm:grid-cols-3 gap-4">
                  <Field label="TIMELINE">
                    <select data-testid="lh-timeline" className="input-tech" value={form.timeline} onChange={(e) => set("timeline", e.target.value)}>
                      <option value="14_days">14 days</option>
                      <option value="30_days">30 days</option>
                      <option value="60_days">60 days</option>
                      <option value="90_plus">90+ days</option>
                    </select>
                  </Field>
                  <Field label="DECISION AUTHORITY">
                    <select data-testid="lh-authority" className="input-tech" value={form.decision_authority} onChange={(e) => set("decision_authority", e.target.value)}>
                      <option value="decision_maker">Decision-maker</option>
                      <option value="influencer">Influencer</option>
                      <option value="researcher">Researcher only</option>
                    </select>
                  </Field>
                  <Field label="BUDGET BAND">
                    <select data-testid="lh-budget" className="input-tech" value={form.budget_band} onChange={(e) => set("budget_band", e.target.value)}>
                      <option value="<1500">{"< $1,500/mo"}</option>
                      <option value="1500_4500">$1,500 – $4,500/mo</option>
                      <option value="4500_10000">$4,500 – $10k/mo</option>
                      <option value="10000+">$10k+ /mo</option>
                    </select>
                  </Field>
                </div>
              </Group>

              {/* Consent */}
              <Group label="05 · CASE STUDY CONSENT · THE DEAL">
                <p className="text-xs text-white/55 mb-3 leading-relaxed">
                  Lighthouse pricing is conditional on permission to publish what we built for you. Check what you'll allow.
                </p>
                <div className="grid sm:grid-cols-2 gap-2">
                  {[
                    { k: "case_study_consent", label: "Publish a written case study · REQUIRED", required: true },
                    { k: "logo_consent", label: "Use our logo on jadeos.ai" },
                    { k: "quote_consent", label: "Use a published quote from an operator" },
                    { k: "metrics_consent", label: "Publish before/after metrics" },
                  ].map((c) => (
                    <label key={c.k} className="flex items-start gap-3 cursor-pointer border border-white/10 p-3"
                      style={{ borderColor: form[c.k] ? "#ccff00" : undefined, background: form[c.k] ? "#ccff0011" : undefined }}>
                      <input data-testid={`lh-${c.k}`} type="checkbox" checked={form[c.k]} onChange={(e) => set(c.k, e.target.checked)} className="mt-0.5 accent-[#ccff00]" />
                      <span className="font-mono-tech text-xs text-white/80">{c.label}{c.required && <span className="text-[#ff3b8a]"> *</span>}</span>
                    </label>
                  ))}
                </div>
              </Group>

              <div className="flex flex-wrap items-center gap-4 pt-2">
                <button data-testid="lh-submit-btn" disabled={submitting} className="btn-jade inline-flex items-center gap-2">
                  {submitting ? "JADE IS SCORING…" : <>SUBMIT APPLICATION <ArrowRight size={16} weight="bold" /></>}
                </button>
                <span className="mono-label text-white/35">SCORED LIVE BY JADE</span>
              </div>
            </form>
          )}

          {result && <ResultPanel result={result} onReset={() => { setResult(null); setForm(EMPTY); }} />}
        </div>
      </section>
    </div>
  );
}

function Field({ label, children }) {
  return <label className="block"><span className="mono-label text-white/45 block mb-2">{label}</span>{children}</label>;
}
function Group({ label, children }) {
  return (
    <div className="space-y-4">
      <div className="mono-label text-[#00ffff]">{label}</div>
      {children}
      <div className="h-px bg-white/5" />
    </div>
  );
}
function Row({ icon: Icon, c, t }) {
  return <div className="flex items-center gap-3"><Icon size={16} className="text-[#ccff00]" weight="bold" /><span>{t}</span></div>;
}

function ResultPanel({ result, onReset }) {
  const hot = result.tier === "hot";
  const c = result.tier === "hot" ? "#ff3b8a" : result.tier === "warm" ? "#ccff00" : "#7c5cff";
  return (
    <div className="lg:col-span-3 deck-card p-8 lg:p-10 relative" data-testid="lh-result">
      <CornerBrackets />
      <div className="mono-label text-[#ccff00] mb-4">APPLICATION CAPTURED · JADE'S READ</div>
      <div className="flex items-end gap-8 mb-6">
        <div>
          <div className="mono-label text-white/45">SCORE</div>
          <div className="font-display font-black text-[#ccff00] text-7xl leading-none glow-lime">{result.score ?? "—"}</div>
        </div>
        <div className="pb-2">
          <div className="mono-label text-white/45">TIER</div>
          <div className="font-display font-bold text-2xl uppercase" style={{ color: c }}>{result.tier || "PENDING"}</div>
        </div>
        <div className="pb-2">
          <div className="mono-label text-white/45">STATUS</div>
          <div className="font-mono-tech text-sm text-white uppercase">{result.status}</div>
        </div>
      </div>
      {result.rationale && (
        <div className="mb-5">
          <div className="mono-label text-[#00ffff] mb-2">RATIONALE</div>
          <p className="text-white/80 leading-relaxed">{result.rationale}</p>
        </div>
      )}
      {result.next_action && (
        <div className="mb-5">
          <div className="mono-label text-[#ccff00] mb-2">NEXT ACTION</div>
          <p className="text-white/80 leading-relaxed">{result.next_action}</p>
        </div>
      )}
      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <div className="mono-label text-[#ccff00] mb-2">GREEN FLAGS</div>
          <ul className="space-y-1.5">
            {(result.green_flags || []).map((f, i) => <li key={i} className="font-mono-tech text-xs text-white/70 flex gap-2"><span className="text-[#ccff00]">▸</span>{f}</li>)}
            {(!result.green_flags || result.green_flags.length === 0) && <li className="font-mono-tech text-xs text-white/40">// none flagged</li>}
          </ul>
        </div>
        <div>
          <div className="mono-label text-[#ff3b8a] mb-2">RED FLAGS</div>
          <ul className="space-y-1.5">
            {(result.red_flags || []).map((f, i) => <li key={i} className="font-mono-tech text-xs text-white/70 flex gap-2"><span className="text-[#ff3b8a]">▸</span>{f}</li>)}
            {(!result.red_flags || result.red_flags.length === 0) && <li className="font-mono-tech text-xs text-white/40">// clean</li>}
          </ul>
        </div>
      </div>
      <div className="mt-8 flex gap-3">
        <button data-testid="lh-reset-btn" onClick={onReset} className="btn-ghost text-xs">SUBMIT ANOTHER</button>
        {hot && <span className="mono-label text-[#ff3b8a] self-center">▲ HOT · WE'LL REACH OUT WITHIN 48 HOURS</span>}
      </div>
    </div>
  );
}
