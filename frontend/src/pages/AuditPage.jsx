/**
 * AuditPage · JadeOS AI Readiness Audit
 *
 * Three modes on one route:
 *   /audit            → start screen (company + industry)
 *   /audit/:id        → wizard while status !== 'analyzed', results dashboard otherwise
 *
 * Backend lives in /app/backend/consulting_audit.py
 */
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { CornerBrackets } from "../components/Brackets";
import { toast } from "sonner";

const ACCENT = {
    jade: "#ccff00",
    cyan: "#00ffff",
    violet: "#7c5cff",
    magenta: "#ff3b8a",
    amber: "#ffce4f",
};

// Mirror industries.js but use backend IDs (saas_tech, e_commerce)
const INDUSTRY_OPTIONS = [
    { id: "freight_brokerage",     label: "FREIGHT · 3PL" },
    { id: "logistics",             label: "LOGISTICS" },
    { id: "manufacturing",         label: "MANUFACTURING" },
    { id: "healthcare",            label: "HEALTHCARE" },
    { id: "saas_tech",             label: "SAAS · TECH" },
    { id: "e_commerce",            label: "E-COMMERCE" },
    { id: "insurance",             label: "INSURANCE" },
    { id: "legal",                 label: "LEGAL" },
    { id: "real_estate",           label: "REAL ESTATE" },
    { id: "professional_services", label: "PROFESSIONAL SERVICES" },
    { id: "general",               label: "GENERAL · OTHER" },
];

const TIER_COLOR = { PIONEER: ACCENT.jade, BUILDER: ACCENT.cyan, CURIOUS: ACCENT.violet, LEARNING: ACCENT.amber };

export default function AuditPage() {
    const { id } = useParams();
    return id ? <AuditRunOrResults id={id} /> : <AuditStart />;
}

/* =================================== START =================================== */
function AuditStart() {
    const nav = useNavigate();
    const [form, setForm] = useState({
        company_name: "", industry: "freight_brokerage",
        operator_name: "", operator_email: "", fleet_or_team_size: "",
    });
    const [busy, setBusy] = useState(false);
    const [source, setSource] = useState("admin");

    const start = async () => {
        if (!form.company_name.trim()) { toast.error("Company name required."); return; }
        setBusy(true);
        try {
            const { data } = await api.post("/audit/start", { ...form, source });
            toast.success(`Audit created · ${data.id.slice(0, 8)}…`);
            nav(`/audit/${data.id}`);
        } catch {
            toast.error("Could not start audit.");
        } finally { setBusy(false); }
    };

    return (
        <div className="min-h-[80vh] py-12 px-6" data-testid="audit-start-page">
            <div className="max-w-5xl mx-auto">
                <div className="mono-label text-[10px] text-[#ccff00]">JADEOS · AI READINESS AUDIT</div>
                <h1 className="font-display font-black text-white text-4xl sm:text-5xl mt-2 tracking-tight">
                    Run a 30-question audit.<br />
                    <span style={{ color: ACCENT.cyan }}>Walk out with the 12-page deck.</span>
                </h1>
                <p className="font-mono-tech text-[13px] text-white/65 mt-4 max-w-2xl leading-relaxed">
                    Six dimensions · industry-specific KPIs · LLM synthesis on top of deterministic
                    scoring. Each audit produces an AI Readiness Score (0–100), recommended JadeOS
                    agents, a 90-day pilot proposal with success metrics, and an annual savings
                    estimate. Final output is a downloadable PowerPoint-style PDF you hand
                    to the client.
                </p>

                <div className="grid lg:grid-cols-[1.3fr_1fr] gap-6 mt-10">
                    {/* Form */}
                    <div className="relative border border-white/10 p-6 bg-[#0a0c18]">
                        <CornerBrackets />
                        <div className="mono-label text-[10px] text-[#ccff00] mb-5">NEW AUDIT</div>

                        <Field label="COMPANY NAME">
                            <input data-testid="audit-company-name" className="input-tech" value={form.company_name}
                                   onChange={(e) => setForm({ ...form, company_name: e.target.value })}
                                   placeholder="e.g. Acme Freight" />
                        </Field>

                        <Field label="INDUSTRY">
                            <select data-testid="audit-industry" className="input-tech" value={form.industry}
                                    onChange={(e) => setForm({ ...form, industry: e.target.value })}>
                                {INDUSTRY_OPTIONS.map((i) => <option key={i.id} value={i.id}>{i.label}</option>)}
                            </select>
                        </Field>

                        <div className="grid sm:grid-cols-2 gap-4">
                            <Field label="OPERATOR NAME · OPTIONAL">
                                <input data-testid="audit-operator-name" className="input-tech" value={form.operator_name}
                                       onChange={(e) => setForm({ ...form, operator_name: e.target.value })}
                                       placeholder="Your name or theirs" />
                            </Field>
                            <Field label="OPERATOR EMAIL · OPTIONAL">
                                <input data-testid="audit-operator-email" className="input-tech" value={form.operator_email}
                                       onChange={(e) => setForm({ ...form, operator_email: e.target.value })}
                                       placeholder="email@example.com" />
                            </Field>
                        </div>

                        <Field label="FLEET / TEAM SIZE · USED FOR ROI ESTIMATE">
                            <input data-testid="audit-team-size" className="input-tech" value={form.fleet_or_team_size}
                                   onChange={(e) => setForm({ ...form, fleet_or_team_size: e.target.value })}
                                   placeholder="e.g. 40 trucks · 25 staff · 200 seats" />
                        </Field>

                        <div className="mt-4">
                            <div className="mono-label text-[9.5px] text-white/55 mb-2">MODE</div>
                            <div className="flex gap-2">
                                {[
                                    { id: "admin",       label: "OPERATOR-LED",  c: ACCENT.jade },
                                    { id: "self_serve",  label: "SELF-SERVE",    c: ACCENT.cyan },
                                ].map((m) => (
                                    <button key={m.id} data-testid={`audit-mode-${m.id}`}
                                            onClick={() => setSource(m.id)}
                                            className="px-3 py-1.5 mono-label text-[10px] transition"
                                            style={{
                                                border: `1px solid ${source === m.id ? m.c : "rgba(255,255,255,0.12)"}`,
                                                color: source === m.id ? m.c : "rgba(255,255,255,0.65)",
                                                background: source === m.id ? `${m.c}11` : "transparent",
                                            }}>
                                        {m.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <button data-testid="audit-start-btn" onClick={start} disabled={busy}
                                className="btn-jade text-sm mt-6 w-full disabled:opacity-50"
                                style={{ background: ACCENT.jade, color: "#02030a" }}>
                            {busy ? "STARTING…" : "▶ START AUDIT"}
                        </button>
                    </div>

                    {/* Sidebar · what's in the audit */}
                    <div className="relative border border-[#7c5cff44] p-6 bg-[#7c5cff08]">
                        <CornerBrackets />
                        <div className="mono-label text-[10px] text-[#7c5cff] mb-4">WHAT&apos;S MEASURED</div>
                        {[
                            { id: "DATA", label: "Data Maturity", c: ACCENT.cyan },
                            { id: "PROCESS", label: "Process Density", c: ACCENT.jade },
                            { id: "TOOLS", label: "Tools & Integrations", c: ACCENT.violet },
                            { id: "CHANGE", label: "Change Capacity", c: ACCENT.magenta },
                            { id: "ROI", label: "ROI Signal", c: ACCENT.amber },
                            { id: "TECH", label: "Technical Maturity", c: ACCENT.jade },
                        ].map((d) => (
                            <div key={d.id} className="flex items-center gap-3 py-1.5 border-b border-white/5 last:border-b-0">
                                <span className="w-2 h-2 inline-block" style={{ background: d.c }} />
                                <span className="font-mono-tech text-[11.5px] text-white/85">{d.label}</span>
                            </div>
                        ))}
                        <div className="font-mono-tech text-[10px] text-white/45 mt-4 leading-relaxed">
                            + 5-6 industry-specific KPIs scored alongside the universal six.
                            Total: ~29 questions, ~10-12 minutes to run.
                        </div>
                        <div className="mt-5 pt-4 border-t border-white/5">
                            <Link to="/admin?tab=audits" data-testid="audit-admin-link"
                                  className="mono-label text-[10px] text-[#ccff00] hover:underline">
                                ▸ View past audits in admin
                            </Link>
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

/* =================================== RUN / RESULTS =================================== */
function AuditRunOrResults({ id }) {
    const [audit, setAudit] = useState(null);
    const [questions, setQuestions] = useState(null);
    const [err, setErr] = useState(null);
    const [reloadKey, setReloadKey] = useState(0);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const { data: a } = await api.get(`/audit/${id}`);
                if (cancelled) return;
                setAudit(a);
                if (a.status !== "analyzed") {
                    const { data: q } = await api.get(`/audit/${id}/questions`);
                    if (cancelled) return;
                    setQuestions(q);
                }
            } catch {
                if (!cancelled) setErr("Audit not found.");
            }
        })();
        return () => { cancelled = true; };
    }, [id, reloadKey]);

    const reload = () => setReloadKey((k) => k + 1);

    if (err) return <Centered>{err}</Centered>;
    if (!audit) return <Centered>// loading audit…</Centered>;

    if (audit.status === "analyzed" && audit.analysis) {
        return <ResultsDashboard audit={audit} onRefresh={reload} />;
    }
    if (!questions) return <Centered>// loading questions…</Centered>;
    return <Wizard audit={audit} questions={questions} onAnalyzed={reload} />;
}

function Centered({ children }) {
    return (
        <div className="min-h-[70vh] flex items-center justify-center px-6">
            <div className="font-mono-tech text-white/55">{children}</div>
        </div>
    );
}

/* =================================== WIZARD =================================== */
function Wizard({ audit, questions, onAnalyzed }) {
    const [step, setStep] = useState(0);
    const [responses, setResponses] = useState(audit.responses || {});
    const [analyzing, setAnalyzing] = useState(false);
    const section = questions.sections[step];

    const allAnswered = questions.sections.every((s) =>
        s.questions.every((q) => responses[q.id] !== undefined)
    );
    const sectionAnswered = section.questions.every((q) => responses[q.id] !== undefined);
    const answered = Object.keys(responses).length;

    const saveBatch = async (extra = {}) => {
        const merged = { ...responses, ...extra };
        setResponses(merged);
        try { await api.post(`/audit/${audit.id}/respond`, { responses: merged }); } catch { /* silent */ }
    };

    const score = (qid, v) => {
        const merged = { ...responses, [qid]: v };
        setResponses(merged);
        // Save on every click (cheap, debounce-light)
        api.post(`/audit/${audit.id}/respond`, { responses: { [qid]: v } }).catch(() => {});
    };

    const analyze = async () => {
        setAnalyzing(true);
        try {
            await saveBatch();
            await api.post(`/audit/${audit.id}/analyze`);
            toast.success("Audit analyzed.");
            onAnalyzed();
        } catch {
            toast.error("Analysis failed. Try again.");
        } finally { setAnalyzing(false); }
    };

    return (
        <div className="min-h-[80vh] py-10 px-6" data-testid="audit-wizard">
            <div className="max-w-5xl mx-auto">
                <div className="flex items-center justify-between flex-wrap gap-3">
                    <div>
                        <div className="mono-label text-[10px]" style={{ color: section.color }}>
                            JADEOS AUDIT · {questions.industry.replace("_", " ").toUpperCase()}
                        </div>
                        <h2 className="font-display font-black text-white text-2xl mt-1">
                            {questions.company_name}
                        </h2>
                    </div>
                    <div className="font-mono-tech text-[11px] text-white/55">
                        {answered} / {questions.total_questions} answered
                    </div>
                </div>

                {/* Progress bar */}
                <div className="relative h-2 bg-[#0a0c18] mt-4 border border-white/5">
                    <div className="absolute inset-y-0 left-0"
                         style={{
                             width: `${(answered / questions.total_questions) * 100}%`,
                             background: `linear-gradient(90deg, ${ACCENT.jade}, ${ACCENT.cyan})`,
                             transition: "width 0.4s ease",
                         }} />
                </div>

                {/* Section tabs */}
                <div className="flex flex-wrap gap-2 mt-6">
                    {questions.sections.map((s, i) => {
                        const done = s.questions.every((q) => responses[q.id] !== undefined);
                        const active = i === step;
                        return (
                            <button key={s.id}
                                    data-testid={`audit-section-${s.id}`}
                                    onClick={() => setStep(i)}
                                    className="px-3 py-1.5 mono-label text-[10px] transition flex items-center gap-2"
                                    style={{
                                        border: `1px solid ${active ? s.color : (done ? "#444" : "rgba(255,255,255,0.10)")}`,
                                        color: active ? s.color : (done ? s.color : "rgba(255,255,255,0.65)"),
                                        background: active ? `${s.color}11` : "transparent",
                                    }}>
                                {done && "● "}{s.label}
                            </button>
                        );
                    })}
                </div>

                {/* Current section */}
                <div className="relative border p-6 mt-6 bg-[#0a0c18]" style={{ borderColor: `${section.color}44` }}>
                    <CornerBrackets />
                    <div className="font-mono-tech text-[11px] text-white/55 mb-4">{section.blurb}</div>
                    <div className="space-y-5">
                        {section.questions.map((q) => (
                            <QuestionRow key={q.id} q={q} color={section.color}
                                         value={responses[q.id]} onChange={(v) => score(q.id, v)} />
                        ))}
                    </div>
                </div>

                {/* Nav */}
                <div className="flex items-center justify-between mt-6 gap-3 flex-wrap">
                    <button data-testid="audit-prev-btn"
                            disabled={step === 0}
                            onClick={() => setStep((s) => Math.max(0, s - 1))}
                            className="btn-jade text-xs disabled:opacity-30"
                            style={{ background: "transparent", color: "white", border: "1px solid rgba(255,255,255,0.15)" }}>
                        ◀ PREV
                    </button>
                    {step < questions.sections.length - 1 ? (
                        <button data-testid="audit-next-btn"
                                onClick={() => setStep((s) => s + 1)}
                                disabled={!sectionAnswered}
                                className="btn-jade text-xs disabled:opacity-40"
                                style={{ background: ACCENT.cyan, color: "#02030a" }}>
                            NEXT ▶
                        </button>
                    ) : (
                        <button data-testid="audit-analyze-btn"
                                onClick={analyze}
                                disabled={!allAnswered || analyzing}
                                className="btn-jade text-xs disabled:opacity-40"
                                style={{ background: ACCENT.jade, color: "#02030a" }}>
                            {analyzing ? "SYNTHESIZING…" : "▶ RUN ANALYSIS"}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

function QuestionRow({ q, value, color, onChange }) {
    return (
        <div className="border-l-2 pl-4" style={{ borderColor: `${color}55` }}>
            <div className="font-mono-tech text-[12.5px] text-white/85 mb-2">{q.text}</div>
            <div className="flex items-center gap-2 flex-wrap">
                {[1, 2, 3, 4, 5].map((v) => {
                    const active = value === v;
                    return (
                        <button key={v}
                                data-testid={`audit-score-${q.id}-${v}`}
                                onClick={() => onChange(v)}
                                className="w-10 h-10 mono-label text-[12px] font-bold transition"
                                style={{
                                    border: `1px solid ${active ? color : "rgba(255,255,255,0.12)"}`,
                                    color: active ? "#02030a" : "rgba(255,255,255,0.75)",
                                    background: active ? color : "transparent",
                                }}>
                            {v}
                        </button>
                    );
                })}
                <div className="font-mono-tech text-[10px] text-white/45 ml-2 flex gap-3">
                    <span><span style={{ color }}>1</span> {q.low}</span>
                    <span><span style={{ color }}>5</span> {q.high}</span>
                </div>
            </div>
        </div>
    );
}

/* =================================== RESULTS =================================== */
function ResultsDashboard({ audit }) {
    const a = audit.analysis;
    const s = a.scores;
    const sav = a.savings;
    const n = a.narrative;
    const tierColor = s.tier_color || TIER_COLOR[s.tier] || ACCENT.jade;

    const dimensions = useMemo(() => ([
        { id: "DATA", label: "Data Maturity", c: ACCENT.cyan },
        { id: "PROCESS", label: "Process Density", c: ACCENT.jade },
        { id: "TOOLS", label: "Tools & Integrations", c: ACCENT.violet },
        { id: "CHANGE", label: "Change Capacity", c: ACCENT.magenta },
        { id: "ROI", label: "ROI Signal", c: ACCENT.amber },
        { id: "TECH", label: "Technical Maturity", c: ACCENT.jade },
    ]), []);

    return (
        <div className="min-h-[80vh] py-10 px-6" data-testid="audit-results">
            <div className="max-w-6xl mx-auto space-y-6">
                {/* HERO */}
                <div className="relative border p-6 sm:p-8 bg-gradient-to-br from-[#0a0c18] to-[#15102a]"
                     style={{ borderColor: `${tierColor}55` }}>
                    <CornerBrackets />
                    <div className="grid lg:grid-cols-[1.4fr_1fr] gap-6 items-start">
                        <div>
                            <div className="mono-label text-[10px]" style={{ color: tierColor }}>
                                JADEOS AI READINESS AUDIT · {audit.industry.replace("_", " ").toUpperCase()}
                            </div>
                            <h1 className="font-display font-black text-white text-3xl sm:text-4xl mt-2 tracking-tight">
                                {audit.company_name}
                            </h1>
                            <p className="font-mono-tech text-[12px] text-white/70 mt-4 leading-relaxed max-w-3xl">
                                {n.executive_summary}
                            </p>
                            <p className="font-display font-bold mt-4 text-lg" style={{ color: tierColor }}>
                                &ldquo;{n.callout}&rdquo;
                            </p>
                        </div>
                        <div className="text-center sm:text-right">
                            <div className="mono-label text-[10px] text-white/45 mb-1">OVERALL SCORE</div>
                            <div className="font-display font-black leading-none"
                                 style={{ color: tierColor, fontSize: "clamp(5rem, 14vw, 9rem)" }}
                                 data-testid="audit-overall-score">
                                {Math.round(s.overall_score)}
                            </div>
                            <div className="mono-label text-[14px] mt-1" style={{ color: tierColor }}>
                                TIER · {s.tier}
                            </div>
                            <div className="font-mono-tech text-[10.5px] text-white/55 mt-2 max-w-xs ml-auto">
                                {s.tier_blurb}
                            </div>
                            <div className="flex gap-2 mt-5 justify-center sm:justify-end">
                                <a data-testid="audit-pdf-download"
                                   href={`${process.env.REACT_APP_BACKEND_URL}/api/audit/${audit.id}/report.pdf`}
                                   target="_blank" rel="noreferrer"
                                   className="btn-jade text-xs"
                                   style={{ background: tierColor, color: "#02030a" }}>
                                    ↓ DOWNLOAD 12-PAGE PDF
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                {/* DIMENSION RADAR (SVG) + bars */}
                <div className="grid lg:grid-cols-[1fr_1fr] gap-6">
                    <div className="relative border border-white/10 p-6 bg-[#0a0c18]">
                        <CornerBrackets />
                        <div className="mono-label text-[10px] text-[#7c5cff] mb-4">RADAR · 6 DIMENSIONS</div>
                        <RadarChart scores={s.dimension_scores} dimensions={dimensions} />
                    </div>
                    <div className="relative border border-white/10 p-6 bg-[#0a0c18]">
                        <CornerBrackets />
                        <div className="mono-label text-[10px] text-[#ccff00] mb-4">BREAKDOWN</div>
                        <div className="space-y-3">
                            {dimensions.map((d) => {
                                const v = s.dimension_scores[d.id] ?? 0;
                                return (
                                    <div key={d.id} className="grid grid-cols-[140px_1fr_50px] items-center gap-3">
                                        <span className="font-mono-tech text-[11.5px] text-white/85">{d.label}</span>
                                        <div className="h-3 bg-[#1a1d2e] relative overflow-hidden">
                                            <div className="absolute inset-y-0 left-0 transition-all"
                                                 style={{ width: `${v}%`, background: d.c }} />
                                        </div>
                                        <span className="font-display font-bold text-right" style={{ color: d.c }}>
                                            {Math.round(v)}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>

                {/* STRENGTHS / GAPS / RECOMMENDED AGENTS */}
                <div className="grid lg:grid-cols-3 gap-4">
                    <ListBlock title="STRENGTHS"   items={n.strengths}   color={ACCENT.jade}   icon="●" testid="audit-strengths" />
                    <ListBlock title="GAPS"        items={n.gaps}        color={ACCENT.magenta} icon="◐" testid="audit-gaps" />
                    <div className="relative border border-white/10 p-5 bg-[#0a0c18]" data-testid="audit-recommended-agents">
                        <CornerBrackets />
                        <div className="mono-label text-[10px] text-[#7c5cff] mb-3">RECOMMENDED AGENTS</div>
                        <div className="space-y-2.5">
                            {a.recommended_agents.map((r) => (
                                <div key={r.id} className="border-l-2 pl-3" style={{ borderColor: ACCENT.violet }}>
                                    <div className="font-display font-bold text-white text-[13px]">
                                        <span className="font-mono-tech text-[10px] text-white/55 mr-1.5">{r.id}</span>
                                        {r.name}
                                    </div>
                                    <div className="font-mono-tech text-[10px] text-white/55 mt-1">{r.rationale}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* PILOT + ROI */}
                <div className="grid lg:grid-cols-[1.3fr_1fr] gap-4">
                    <div className="relative border border-[#7c5cff44] p-6 bg-[#7c5cff08]" data-testid="audit-pilot-proposal">
                        <CornerBrackets />
                        <div className="mono-label text-[10px] text-[#7c5cff]">90-DAY PILOT PROPOSAL</div>
                        <div className="grid sm:grid-cols-3 gap-3 mt-3">
                            <Metric label="DURATION" value={`${n.pilot_proposal.duration_days} days`} c={ACCENT.cyan} />
                            <Metric label="INVESTMENT" value={`$${n.pilot_proposal.investment_usd.toLocaleString()}`} c={ACCENT.violet} />
                            <Metric label="TEAM" value="Sponsor + ops + IT" c={ACCENT.amber} />
                        </div>
                        <div className="font-mono-tech text-[11.5px] text-white/75 mt-4 leading-relaxed">
                            {n.pilot_proposal.scope}
                        </div>
                        <div className="mono-label text-[10px] text-[#ccff00] mt-5 mb-2">SUCCESS METRICS</div>
                        <ul className="space-y-1.5">
                            {n.pilot_proposal.success_metrics.map((m, i) => (
                                <li key={i} className="font-mono-tech text-[11px] text-white/80 flex gap-2">
                                    <span style={{ color: ACCENT.jade }}>▸</span>{m}
                                </li>
                            ))}
                        </ul>
                        <div className="font-mono-tech text-[10px] text-white/55 mt-4 pt-3 border-t border-white/5">
                            {n.pilot_proposal.team_required}
                        </div>
                    </div>
                    <div className="relative border border-[#ccff0044] p-6 bg-[#ccff0008]" data-testid="audit-savings">
                        <CornerBrackets />
                        <div className="mono-label text-[10px] text-[#ccff00]">ESTIMATED ANNUAL SAVINGS</div>
                        <div className="font-display font-black text-white mt-3"
                             style={{ fontSize: "clamp(2.2rem, 4vw, 3.2rem)", color: ACCENT.jade }}>
                            ${(sav.annual_savings_central_usd / 1000).toFixed(0)}k
                        </div>
                        <div className="font-mono-tech text-[11px] text-white/55 mt-1">
                            range: ${(sav.annual_savings_low_usd / 1000).toFixed(0)}k – ${(sav.annual_savings_high_usd / 1000).toFixed(0)}k
                        </div>
                        <div className="grid grid-cols-2 gap-2 mt-5">
                            <Metric label="PAYBACK" value={`~${sav.payback_months_estimate} mo`} c={ACCENT.cyan} />
                            <Metric label="BASIS (SEATS)" value={`${sav.size_used}`} c={ACCENT.violet} />
                        </div>
                    </div>
                </div>

                {/* RISKS */}
                <div className="relative border border-white/10 p-6 bg-[#0a0c18]" data-testid="audit-risks">
                    <CornerBrackets />
                    <div className="mono-label text-[10px] text-[#ffce4f] mb-4">RISK REGISTER</div>
                    <div className="space-y-3">
                        {n.risks.map((r, i) => {
                            const sevC = { high: ACCENT.magenta, med: ACCENT.amber, low: ACCENT.jade }[r.severity] || ACCENT.amber;
                            return (
                                <div key={i} className="grid grid-cols-[80px_1fr] gap-3 items-start py-2 border-b border-white/5 last:border-b-0">
                                    <span className="mono-label text-[10px] font-bold" style={{ color: sevC }}>
                                        [{r.severity.toUpperCase()}]
                                    </span>
                                    <div>
                                        <div className="font-mono-tech text-[12px] text-white">{r.risk}</div>
                                        <div className="font-mono-tech text-[10.5px] text-white/55 mt-1">
                                            <span style={{ color: sevC }}>mitigation · </span>{r.mitigation}
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* NEXT 30 DAYS */}
                <div className="relative border border-[#00ffff44] p-6 bg-[#00ffff08]" data-testid="audit-next-30">
                    <CornerBrackets />
                    <div className="mono-label text-[10px] text-[#00ffff] mb-4">NEXT 30 DAYS · STARTING MONDAY</div>
                    <ol className="space-y-2">
                        {n.next_30_days.map((x, i) => (
                            <li key={i} className="grid grid-cols-[30px_1fr] items-start gap-2">
                                <span className="font-display font-black text-[#00ffff] text-lg leading-none">{i + 1}</span>
                                <span className="font-mono-tech text-[12px] text-white/85 leading-relaxed">{x}</span>
                            </li>
                        ))}
                    </ol>
                </div>

                <div className="flex justify-between items-center pt-4 border-t border-white/5">
                    <Link to="/audit" data-testid="audit-new-link"
                          className="mono-label text-[10px] text-white/55 hover:text-[#ccff00]">
                        ◀ START NEW AUDIT
                    </Link>
                    <Link to="/admin?tab=audits" data-testid="audit-admin-link"
                          className="mono-label text-[10px] text-[#7c5cff] hover:underline">
                        VIEW ALL AUDITS · ADMIN ▸
                    </Link>
                </div>
            </div>
        </div>
    );
}

function Metric({ label, value, c }) {
    return (
        <div className="border-l-2 pl-3" style={{ borderColor: c }}>
            <div className="mono-label text-[9.5px] text-white/45">{label}</div>
            <div className="font-display font-bold text-white text-[14px] mt-0.5">{value}</div>
        </div>
    );
}

function ListBlock({ title, items, color, icon, testid }) {
    return (
        <div className="relative border border-white/10 p-5 bg-[#0a0c18]" data-testid={testid}>
            <CornerBrackets />
            <div className="mono-label text-[10px] mb-3" style={{ color }}>{title}</div>
            <ul className="space-y-1.5">
                {items.map((x, i) => (
                    <li key={i} className="font-mono-tech text-[11.5px] text-white/85 flex gap-2 leading-relaxed">
                        <span style={{ color }}>{icon}</span>{x}
                    </li>
                ))}
            </ul>
        </div>
    );
}

/* =================================== RADAR =================================== */
function RadarChart({ scores, dimensions }) {
    const SIZE = 320;
    const cx = SIZE / 2;
    const cy = SIZE / 2;
    const r = SIZE / 2 - 35;
    const n = dimensions.length;

    // Polar to cartesian
    const pt = (i, v) => {
        const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
        const rad = r * (v / 100);
        return [cx + rad * Math.cos(angle), cy + rad * Math.sin(angle)];
    };
    const labelPt = (i) => {
        const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
        return [cx + (r + 22) * Math.cos(angle), cy + (r + 22) * Math.sin(angle)];
    };

    const polygon = dimensions
        .map((d, i) => pt(i, scores[d.id] ?? 0).join(","))
        .join(" ");

    const rings = [25, 50, 75, 100];

    return (
        <div className="flex justify-center">
            <svg width={SIZE} height={SIZE} className="overflow-visible">
                {/* Rings */}
                {rings.map((rv) => (
                    <polygon key={rv}
                             points={dimensions.map((_, i) => pt(i, rv).join(",")).join(" ")}
                             fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
                ))}
                {/* Axes */}
                {dimensions.map((d, i) => {
                    const [x, y] = pt(i, 100);
                    return <line key={d.id} x1={cx} y1={cy} x2={x} y2={y}
                                 stroke="rgba(255,255,255,0.10)" strokeWidth="1" />;
                })}
                {/* Filled polygon */}
                <polygon points={polygon} fill="rgba(204,255,0,0.18)" stroke={ACCENT.jade} strokeWidth="2" />
                {/* Vertex dots */}
                {dimensions.map((d, i) => {
                    const v = scores[d.id] ?? 0;
                    const [x, y] = pt(i, v);
                    return <circle key={d.id} cx={x} cy={y} r="4" fill={d.c} />;
                })}
                {/* Labels */}
                {dimensions.map((d, i) => {
                    const [lx, ly] = labelPt(i);
                    return (
                        <text key={d.id} x={lx} y={ly} textAnchor="middle"
                              fill="rgba(255,255,255,0.7)" fontSize="10"
                              fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">
                            {d.id} · {Math.round(scores[d.id] ?? 0)}
                        </text>
                    );
                })}
            </svg>
        </div>
    );
}
