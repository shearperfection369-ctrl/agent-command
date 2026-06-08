/**
 * BrokerFreeAuditLanding · /audit/broker-free (and /free-audit alias)
 *
 * Lead-magnet landing page for freight brokers. Email-gate before questionnaire.
 * Headline: "Free AI Readiness Audit · For Freight Brokers"
 * CTA: collect email → /audit/start with lead_magnet:'free_90_day' → push to wizard.
 */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, API_BASE } from "../lib/api";
import { CornerBrackets } from "../components/Brackets";
import { toast } from "sonner";

const ACCENT = {
    jade: "#ccff00",
    cyan: "#00ffff",
    violet: "#7c5cff",
    magenta: "#ff3b8a",
    amber: "#ffce4f",
};

export default function BrokerFreeAuditLanding() {
    const nav = useNavigate();
    const [busy, setBusy] = useState(false);
    const [form, setForm] = useState({
        first_name: "",
        company_name: "",
        operator_email: "",
        fleet_or_team_size: "",
        phone: "",
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
            const { data } = await api.post("/audit/start", {
                company_name: form.company_name,
                industry: "freight_brokerage",
                operator_name: form.first_name || undefined,
                operator_email: form.operator_email,
                fleet_or_team_size: form.fleet_or_team_size || undefined,
                source: "self_serve",
                lead_magnet: "free_90_day",
            });
            toast.success("Audit unlocked. Walking you in.");
            nav(`/audit/${data.id}`);
        } catch {
            toast.error("Could not start audit. Try again.");
        } finally { setBusy(false); }
    };

    return (
        <div className="min-h-[80vh] py-12 px-6" data-testid="broker-free-audit-page">
            <div className="max-w-6xl mx-auto">
                {/* HERO */}
                <div className="text-center mb-12">
                    <div className="mono-label text-[10px] text-[#ccff00]">JADEOS · LIGHTHOUSE PROGRAM · LIMITED COHORT</div>
                    <h1 className="font-display font-black text-white tracking-tighter mt-3 leading-[0.95]"
                        style={{ fontSize: "clamp(2.5rem, 6vw, 5rem)" }}>
                        Free AI Readiness Audit.<br />
                        <span style={{ color: ACCENT.cyan }}>For Freight Brokers.</span>
                    </h1>
                    <p className="font-mono-tech text-[14px] text-white/70 mt-5 max-w-2xl mx-auto leading-relaxed">
                        Walk away with a 12-page PowerPoint-style report scored 0-100, a 90-day pilot
                        proposal with success metrics declared upfront, and an annual savings estimate.
                        <span className="text-[#ccff00]"> Cost: $0. No obligation.</span> Built by a 13-year freight operator.
                    </p>
                    <div className="flex gap-3 justify-center flex-wrap mt-6">
                        <a href={`${API_BASE}/audit/data-checklist.pdf`} target="_blank" rel="noreferrer"
                           data-testid="broker-checklist-pdf"
                           className="btn-jade text-xs"
                           style={{ background: "transparent", color: ACCENT.jade, border: `1px solid ${ACCENT.jade}55` }}>
                            ↓ DOWNLOAD DATA CHECKLIST (1-PAGER)
                        </a>
                        <a href="#start-form"
                           className="btn-jade text-xs"
                           style={{ background: ACCENT.jade, color: "#02030a" }}>
                            ▶ START FREE AUDIT
                        </a>
                    </div>
                </div>

                {/* WHY · 3 cards */}
                <div className="grid sm:grid-cols-3 gap-3 mb-10">
                    <ValueCard
                        eyebrow="WHAT YOU GET"
                        title="12-page report"
                        body="PowerPoint-style PDF. AI Readiness Score 0-100. Recommended agents. 90-day pilot proposal with named success metrics."
                        c={ACCENT.jade} />
                    <ValueCard
                        eyebrow="WHAT IT TAKES"
                        title="30 minutes"
                        body="29 questions across 6 dimensions of AI readiness + 5 freight-specific KPIs. Run it in one sitting."
                        c={ACCENT.cyan} />
                    <ValueCard
                        eyebrow="WHAT IT COSTS"
                        title="$0"
                        body="First 5 brokers per month. No obligation. Audit happens whether or not you pilot."
                        c={ACCENT.violet} />
                </div>

                <div className="grid lg:grid-cols-[1.3fr_1fr] gap-6" id="start-form">
                    {/* LEFT · Data checklist */}
                    <div className="relative border border-[#ccff0044] p-6 bg-[#ccff0008]">
                        <CornerBrackets />
                        <div className="mono-label text-[10px] text-[#ccff00] mb-4">WHAT WE NEED FROM YOU</div>
                        <p className="font-mono-tech text-[12px] text-white/65 mb-5 leading-relaxed">
                            We can run the audit on the 29 questions alone, but the strongest report happens
                            when you send the packet below. Any format you have — CSV, PDF export, screenshots.
                        </p>
                        <ul className="space-y-3">
                            {[
                                ["LOAD HISTORY",            "last 90 days · pickup, delivery, lane, miles, rate, carrier, cost, customer"],
                                ["CARRIER ROSTER",          "current active carriers with MC numbers + lanes covered"],
                                ["QUOTE LOGS",              "last 90 days · won/lost flag · booked rate vs ask rate"],
                                ["CUSTOMER LIST",           "top 25 by revenue · contact + monthly load count"],
                                ["OPS HEADCOUNT",           "roles, FTE count, hourly or salaried"],
                                ["CURRENT TOOLS / TMS",     "what software runs the desk today (TMS · CRM · accounting · phone)"],
                                ["MONTHLY P&L SUMMARY",     "last 3 months · gross margin, carrier pay, ops cost"],
                                ["3-SENTENCE PAIN",         "where is the team drowning right now?"],
                            ].map(([label, body], i) => (
                                <li key={label} className="grid grid-cols-[36px_1fr] gap-3">
                                    <span className="font-display font-black text-[#ccff00] text-lg leading-none">{i + 1}.</span>
                                    <div>
                                        <div className="font-display font-bold text-white text-[13px]">{label}</div>
                                        <div className="font-mono-tech text-[11px] text-white/60">{body}</div>
                                    </div>
                                </li>
                            ))}
                        </ul>
                        <div className="font-mono-tech text-[10.5px] text-white/55 mt-6 pt-4 border-t border-white/5 leading-relaxed">
                            Data encrypted at rest. Not shared with third parties. NDA on request.
                            Audit complete in 5-7 business days from receipt of the packet.
                        </div>
                    </div>

                    {/* RIGHT · Start form */}
                    <div className="relative border border-[#00ffff44] p-6 bg-[#0a0c18]">
                        <CornerBrackets />
                        <div className="mono-label text-[10px] text-[#00ffff] mb-4">START YOUR AUDIT</div>
                        <Field label="FIRST NAME">
                            <input data-testid="broker-first-name" className="input-tech"
                                   value={form.first_name}
                                   onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                                   placeholder="Dana" />
                        </Field>
                        <Field label="COMPANY NAME · REQUIRED">
                            <input data-testid="broker-company" className="input-tech"
                                   value={form.company_name}
                                   onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                                   placeholder="Bay & Bay Transportation" />
                        </Field>
                        <Field label="EMAIL · REQUIRED">
                            <input data-testid="broker-email" className="input-tech" type="email"
                                   value={form.operator_email}
                                   onChange={(e) => setForm({ ...form, operator_email: e.target.value })}
                                   placeholder="dana@bayandbay.com" />
                        </Field>
                        <Field label="FLEET SIZE · USED FOR ROI ESTIMATE">
                            <input data-testid="broker-fleet" className="input-tech"
                                   value={form.fleet_or_team_size}
                                   onChange={(e) => setForm({ ...form, fleet_or_team_size: e.target.value })}
                                   placeholder="40 trucks" />
                        </Field>
                        <button data-testid="broker-start-btn" onClick={start} disabled={busy}
                                className="btn-jade text-sm mt-3 w-full disabled:opacity-50"
                                style={{ background: ACCENT.cyan, color: "#02030a" }}>
                            {busy ? "UNLOCKING…" : "▶ UNLOCK MY FREE AUDIT"}
                        </button>
                        <div className="font-mono-tech text-[10px] text-white/45 mt-3 text-center leading-relaxed">
                            By starting you agree to receive the report by email.
                            We never share your data. Audit takes ~30 minutes.
                        </div>
                    </div>
                </div>

                {/* TRUST · Founder + trinity */}
                <div className="grid lg:grid-cols-2 gap-4 mt-10">
                    <div className="relative border border-white/10 p-6 bg-[#0a0c18]">
                        <CornerBrackets />
                        <div className="mono-label text-[10px] text-[#7c5cff] mb-3">WHO IS RUNNING THIS</div>
                        <h3 className="font-display font-black text-white text-xl">Oliver Cummins · Founder</h3>
                        <p className="font-mono-tech text-[12px] text-white/65 mt-2 leading-relaxed">
                            13 years inside the freight chair. Dispatcher → fleet manager → independent broker.
                            JadeOS is what I needed when I was inside the chair — operator-grade AI agents
                            purpose-built per vertical, with persistent memory and audit chain.
                        </p>
                        <div className="flex gap-3 mt-4">
                            <a href="https://www.linkedin.com/in/oliver-cummins-a27304a3/" target="_blank" rel="noreferrer"
                               className="mono-label text-[10px] text-[#00ffff] hover:underline">↗ LINKEDIN</a>
                            <a href="mailto:founder@jadeos.ai"
                               className="mono-label text-[10px] text-[#ccff00] hover:underline">✉ FOUNDER@JADEOS.AI</a>
                            <a href="/invite"
                               className="mono-label text-[10px] text-[#ff3b8a] hover:underline">↗ INVESTOR INVITE</a>
                        </div>
                    </div>
                    <div className="relative border border-[#7c5cff44] p-6 bg-[#7c5cff08]">
                        <CornerBrackets />
                        <div className="mono-label text-[10px] text-[#7c5cff] mb-3">WHAT WE BUILT</div>
                        <ul className="space-y-2">
                            {[
                                ["JadeOS Quantum AI",     "Flagship AI command center · 50+ modules · voice-first 'Hey Jade'"],
                                ["JadeOS-Agent Suite",    "Six freight-vertical agents · sits on top of any TMS"],
                                ["Hot Shot TMS",          "Operator-built system of record · underserved hot-shot segment"],
                            ].map(([t, b]) => (
                                <li key={t} className="border-l-2 pl-3" style={{ borderColor: ACCENT.violet }}>
                                    <div className="font-display font-bold text-white text-[13px]">{t}</div>
                                    <div className="font-mono-tech text-[10.5px] text-white/60">{b}</div>
                                </li>
                            ))}
                        </ul>
                        <div className="font-mono-tech text-[10px] text-white/45 mt-4">
                            All three fully developed · seeking lighthouse pilots + VC funding to launch in tandem.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function Field({ label, children }) {
    return (
        <div className="mb-4">
            <div className="mono-label text-[9.5px] text-white/55 mb-1.5">{label}</div>
            {children}
        </div>
    );
}

function ValueCard({ eyebrow, title, body, c }) {
    return (
        <div className="relative border p-5 bg-[#0a0c18]" style={{ borderColor: `${c}44` }}>
            <CornerBrackets />
            <div className="mono-label text-[10px]" style={{ color: c }}>{eyebrow}</div>
            <div className="font-display font-black text-white mt-1.5" style={{ fontSize: "1.6rem", color: c }}>
                {title}
            </div>
            <div className="font-mono-tech text-[11.5px] text-white/65 mt-2 leading-relaxed">{body}</div>
        </div>
    );
}
