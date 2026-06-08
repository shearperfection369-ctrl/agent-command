/**
 * LighthouseAuditLanding · /lighthouse/audit
 *
 * Public landing for Lighthouse program members to start their own audit.
 * Industry-agnostic (any of 11 verticals). On submit, creates an audit with
 * lead_magnet="lighthouse_member" and routes to the audit wizard. After
 * analysis, the user lands on the Lighthouse Member Dashboard.
 */
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { CornerBrackets } from "../components/Brackets";
import { toast } from "sonner";

const ACCENT = { jade: "#ccff00", cyan: "#00ffff", violet: "#7c5cff", amber: "#ffce4f" };

const INDUSTRIES = [
    { id: "freight_brokerage",     label: "Freight · 3PL" },
    { id: "logistics",             label: "Logistics" },
    { id: "manufacturing",         label: "Manufacturing" },
    { id: "healthcare",            label: "Healthcare" },
    { id: "saas_tech",             label: "SaaS · Tech" },
    { id: "e_commerce",            label: "E-Commerce" },
    { id: "insurance",             label: "Insurance" },
    { id: "legal",                 label: "Legal" },
    { id: "real_estate",           label: "Real Estate" },
    { id: "professional_services", label: "Professional Services" },
    { id: "general",               label: "Other · General" },
];

const PERKS = [
    { label: "Founding-Customer Pricing", body: "50% off list · locked for life of contract." },
    { label: "Direct Founder Access",     body: "Slack channel · weekly 30-min sync · roadmap vote." },
    { label: "Co-Marketing",              body: "Logo on onejades.com + case study co-authorship." },
    { label: "Design-Partner Equity",     body: "Nominal grant on signature · standard SAFE." },
    { label: "Roadmap Influence",         body: "Top 3 asks in a dedicated quarterly swim lane." },
    { label: "Migration Concierge",       body: "Founder-led data audit, schema mapping, agent calibration." },
];

export default function LighthouseAuditLanding() {
    const nav = useNavigate();
    const [busy, setBusy] = useState(false);
    const [form, setForm] = useState({
        company_name: "",
        industry: "freight_brokerage",
        operator_name: "",
        operator_email: "",
        role: "",
        fleet_or_team_size: "",
        referral_source: "",
    });

    const start = async () => {
        if (!form.company_name.trim() || !form.operator_email.trim()) {
            toast.error("Company + email required."); return;
        }
        if (!form.operator_email.includes("@")) {
            toast.error("Please enter a valid email."); return;
        }
        setBusy(true);
        try {
            const { data } = await api.post("/audit/lighthouse/start", {
                company_name: form.company_name,
                industry: form.industry,
                operator_name: form.operator_name || undefined,
                operator_email: form.operator_email,
                role: form.role || undefined,
                fleet_or_team_size: form.fleet_or_team_size || undefined,
                referral_source: form.referral_source || undefined,
            });
            toast.success("Audit unlocked. Walking you in.");
            // Stash the dashboard URL so we can route back here after analyze
            try { localStorage.setItem(`jadeos_lighthouse_member_${data.id}`, "1"); } catch (_e) { /* ignore */ }
            nav(`/audit/${data.id}`);
        } catch {
            toast.error("Could not start audit. Try again.");
        } finally { setBusy(false); }
    };

    return (
        <div className="min-h-[80vh] py-12 px-6" data-testid="lighthouse-audit-landing">
            <div className="max-w-6xl mx-auto">
                {/* HERO */}
                <div className="relative border border-[#ccff0044] p-8 sm:p-12 bg-gradient-to-br from-[#0a0c18] to-[#15102a]">
                    <CornerBrackets />
                    <div className="grid lg:grid-cols-[1.4fr_1fr] gap-10 items-start">
                        <div>
                            <div className="mono-label text-[10px] text-[#ccff00]">
                                LIGHTHOUSE PROGRAM · 5 SEATS · FOUNDING-CUSTOMER COHORT
                            </div>
                            <h1 className="font-display font-black text-white text-4xl sm:text-5xl lg:text-6xl mt-3 tracking-tighter leading-[0.95]">
                                Run your <span style={{ color: ACCENT.jade }}>JadeOS</span> readiness audit.
                            </h1>
                            <p className="font-mono-tech text-[14px] text-white/75 mt-5 leading-relaxed max-w-2xl">
                                30 questions across 6 dimensions + your industry KPIs. 25 minutes. You walk out with a
                                <span className="text-white"> 14-page operator-grade report </span>
                                tuned to your company, a tier classification, and personalized 90-day pilot terms
                                locked at the founding-customer rate.
                            </p>
                            <div className="flex flex-wrap gap-2 mt-6">
                                <span className="chip">14-PAGE PDF · YOURS TO KEEP</span>
                                <span className="chip chip-cyan">11 INDUSTRIES TUNED</span>
                                <span className="chip chip-violet">FOUNDER-LED ANALYSIS</span>
                            </div>
                            <div className="mt-6 font-mono-tech text-[11px] text-white/55">
                                Already running an audit?{" "}
                                <Link to="/audit" data-testid="lighthouse-audit-resume-link"
                                      className="text-[#00ffff] hover:underline">
                                    Resume an existing audit
                                </Link>
                            </div>
                        </div>

                        {/* FORM */}
                        <div className="border border-white/10 bg-[#06070d] p-6 space-y-4">
                            <div className="mono-label text-[10px] text-[#ccff00]">
                                UNLOCK YOUR AUDIT
                            </div>
                            <label className="block">
                                <span className="mono-label text-white/45 block mb-1.5">COMPANY *</span>
                                <input data-testid="lh-audit-company" required type="text" className="input-tech"
                                       value={form.company_name}
                                       onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                                       placeholder="Acme Logistics" />
                            </label>
                            <label className="block">
                                <span className="mono-label text-white/45 block mb-1.5">INDUSTRY *</span>
                                <select data-testid="lh-audit-industry" className="input-tech"
                                        value={form.industry}
                                        onChange={(e) => setForm({ ...form, industry: e.target.value })}>
                                    {INDUSTRIES.map((i) => (
                                        <option key={i.id} value={i.id}>{i.label}</option>
                                    ))}
                                </select>
                            </label>
                            <div className="grid grid-cols-2 gap-3">
                                <label className="block">
                                    <span className="mono-label text-white/45 block mb-1.5">YOUR NAME</span>
                                    <input data-testid="lh-audit-name" type="text" className="input-tech"
                                           value={form.operator_name}
                                           onChange={(e) => setForm({ ...form, operator_name: e.target.value })}
                                           placeholder="First Last" />
                                </label>
                                <label className="block">
                                    <span className="mono-label text-white/45 block mb-1.5">ROLE</span>
                                    <input data-testid="lh-audit-role" type="text" className="input-tech"
                                           value={form.role}
                                           onChange={(e) => setForm({ ...form, role: e.target.value })}
                                           placeholder="COO · Ops Lead" />
                                </label>
                            </div>
                            <label className="block">
                                <span className="mono-label text-white/45 block mb-1.5">EMAIL *</span>
                                <input data-testid="lh-audit-email" required type="email" className="input-tech"
                                       value={form.operator_email}
                                       onChange={(e) => setForm({ ...form, operator_email: e.target.value })}
                                       placeholder="you@company.com" />
                            </label>
                            <div className="grid grid-cols-2 gap-3">
                                <label className="block">
                                    <span className="mono-label text-white/45 block mb-1.5">TEAM SIZE</span>
                                    <input data-testid="lh-audit-team" type="text" className="input-tech"
                                           value={form.fleet_or_team_size}
                                           onChange={(e) => setForm({ ...form, fleet_or_team_size: e.target.value })}
                                           placeholder="e.g. 24" />
                                </label>
                                <label className="block">
                                    <span className="mono-label text-white/45 block mb-1.5">HEARD VIA</span>
                                    <input data-testid="lh-audit-referral" type="text" className="input-tech"
                                           value={form.referral_source}
                                           onChange={(e) => setForm({ ...form, referral_source: e.target.value })}
                                           placeholder="LinkedIn · referral · X" />
                                </label>
                            </div>
                            <button data-testid="lh-audit-start-btn" disabled={busy}
                                    onClick={start} className="btn-jade w-full mt-2">
                                {busy ? "UNLOCKING…" : "START LIGHTHOUSE AUDIT →"}
                            </button>
                            <p className="font-mono-tech text-[10px] text-white/45 leading-relaxed">
                                We store your responses encrypted. The audit_id we issue is your private share token —
                                bookmark it. Never sold or shared.
                            </p>
                        </div>
                    </div>
                </div>

                {/* WHAT YOU GET */}
                <div className="mt-12 grid lg:grid-cols-3 gap-6">
                    <Card title="14-page tailored report"  body="Tier classification, 6-dimension breakdown, industry KPIs, 4 recommended agents, 90-day pilot terms personalized to YOUR score, risk register, and a 30-day starter list." c={ACCENT.jade}    />
                    <Card title="Founder-led pilot"        body="Founding-customer rate ($17.5k vs $35k list). Direct Slack channel. Weekly 30-min sync. Roadmap influence vote on every quarter."                                                                                  c={ACCENT.cyan}    />
                    <Card title="Membership perks"        body="Logo on onejades.com after pilot. Case-study co-authorship. Nominal equity grant on signature (standard SAFE). White-glove migration concierge."                                                                       c={ACCENT.violet}  />
                </div>

                {/* PERKS */}
                <div className="mt-16">
                    <div className="mono-label text-[10px] text-[#ccff00] mb-2">FOUNDING-CUSTOMER PERKS · LOCKED IN AT SIGNATURE</div>
                    <h2 className="font-display font-black text-white text-3xl sm:text-4xl tracking-tight">
                        Why join the Lighthouse cohort.
                    </h2>
                    <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {PERKS.map((p) => (
                            <div key={p.label} className="border border-white/10 p-5 bg-[#06070d]">
                                <div className="mono-label text-[10px] text-[#ccff00] mb-2">{p.label.toUpperCase()}</div>
                                <p className="font-mono-tech text-[12px] text-white/85 leading-relaxed">{p.body}</p>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="mt-12 text-center font-mono-tech text-[11px] text-white/45">
                    Questions? <a href="mailto:founder@jadeos.ai" className="text-[#00ffff] hover:underline">founder@jadeos.ai</a>
                </div>
            </div>
        </div>
    );
}

function Card({ title, body, c }) {
    return (
        <div className="relative border border-white/10 p-6 bg-[#0a0c18]">
            <CornerBrackets />
            <div className="mono-label text-[10px]" style={{ color: c }}>{title.toUpperCase()}</div>
            <p className="font-mono-tech text-[12px] text-white/80 mt-3 leading-relaxed">{body}</p>
        </div>
    );
}
