/**
 * DesignPartnersPanel — admin DESIGN PARTNERS tab.
 *
 * CRM-lite kanban view for tracking mid-market / enterprise pipeline.
 * Stages: identified → researched → pitched → committed → live → case_published
 *
 * Endpoints:
 *   GET    /api/admin/design-partners
 *   POST   /api/admin/design-partners
 *   PATCH  /api/admin/design-partners/{id}
 *   DELETE /api/admin/design-partners/{id}
 *   POST   /api/admin/design-partners/{id}/case-study/generate
 */
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "./Brackets";
import { JadeWorking } from "./JadeAvatar";
import { SaveActions } from "./SaveActions";

const STAGE_LABEL = {
    identified: "IDENTIFIED",
    researched: "RESEARCHED",
    pitched: "PITCHED",
    committed: "COMMITTED",
    live: "LIVE",
    case_published: "PUBLISHED",
};
const STAGE_COLOR = {
    identified: "#7c5cff",
    researched: "#00ffff",
    pitched: "#ffce4f",
    committed: "#ccff00",
    live: "#ff3b8a",
    case_published: "#ffffff",
};
const TIER_COLOR = {
    operator: "#7c5cff",
    fleet: "#00ffff",
    enterprise: "#ccff00",
};
const READINESS_COLOR = { low: "#ff3b8a", med: "#ffce4f", high: "#ccff00" };

function PartnerCard({ p, onUpdate, onDelete, onGenerate }) {
    const [busy, setBusy] = useState(false);

    const move = async (newStage) => {
        setBusy(true);
        try {
            await api.patch(`/admin/design-partners/${p.id}`, null, { params: { stage: newStage } });
            toast.success(`${p.company} → ${STAGE_LABEL[newStage]}`);
            onUpdate();
        } catch { toast.error("Move failed"); } finally { setBusy(false); }
    };

    const stageIndex = ["identified", "researched", "pitched", "committed", "live", "case_published"].indexOf(p.stage);
    const nextStage = ["researched", "pitched", "committed", "live", "case_published"][stageIndex];

    return (
        <div
            data-testid={`partner-card-${p.id}`}
            className="border p-3 bg-[#06081a] space-y-2"
            style={{ borderColor: `${TIER_COLOR[p.tier] || "#7c5cff"}55` }}
        >
            <div className="flex items-start justify-between gap-2">
                <div className="font-display font-bold text-white text-sm leading-tight truncate" title={p.company}>{p.company}</div>
                <span className="mono-label text-[9px]" style={{ color: TIER_COLOR[p.tier] }}>{p.tier?.toUpperCase()}</span>
            </div>
            <div className="font-mono-tech text-[10px] text-white/55 truncate">{p.city || "—"} · {p.size || "—"}</div>

            <div className="flex items-center justify-between gap-2 pt-1">
                <span className="font-display font-bold text-sm" style={{ color: TIER_COLOR[p.tier] }}>
                    ${(p.pilot_value_usd || 0).toLocaleString()}<span className="text-white/40 text-[9px]">/mo</span>
                </span>
                <span
                    className="mono-label text-[8px] px-1.5 py-0.5 border"
                    style={{ color: READINESS_COLOR[p.ai_readiness], borderColor: `${READINESS_COLOR[p.ai_readiness]}55` }}
                >AI · {p.ai_readiness?.toUpperCase()}</span>
            </div>

            {p.notes && (
                <div className="font-mono-tech text-[10px] text-white/50 leading-snug line-clamp-2" title={p.notes}>{p.notes}</div>
            )}

            <div className="flex items-center gap-1 pt-1 border-t border-white/5">
                {nextStage && (
                    <button
                        data-testid={`move-partner-${p.id}`}
                        disabled={busy}
                        onClick={() => move(nextStage)}
                        className="mono-label text-[9px] px-2 py-1 border border-[#ccff00]/40 text-[#ccff00] hover:bg-[#ccff00]/10 disabled:opacity-40"
                        title={`Move to ${STAGE_LABEL[nextStage]}`}
                    >→ {STAGE_LABEL[nextStage]}</button>
                )}
                {p.stage === "live" && (
                    <button
                        data-testid={`generate-case-${p.id}`}
                        disabled={busy}
                        onClick={() => onGenerate(p)}
                        className="mono-label text-[9px] px-2 py-1 border border-[#ff3b8a]/40 text-[#ff3b8a] hover:bg-[#ff3b8a]/10"
                    >+ CASE STUDY</button>
                )}
                <button
                    data-testid={`delete-partner-${p.id}`}
                    onClick={() => onDelete(p)}
                    className="ml-auto mono-label text-[9px] text-white/35 hover:text-[#ff3b8a]"
                >✕</button>
            </div>
        </div>
    );
}

function StageColumn({ stage, partners, onUpdate, onDelete, onGenerate }) {
    const c = STAGE_COLOR[stage];
    const total = partners.reduce((s, p) => s + (p.pilot_value_usd || 0), 0);
    return (
        <div
            data-testid={`stage-column-${stage}`}
            className="flex flex-col gap-3 min-w-[280px] bg-[#02030a] border border-white/5 p-3"
        >
            <div className="flex items-center justify-between sticky top-0 bg-[#02030a] pb-2 border-b border-white/5">
                <span className="mono-label text-[10px]" style={{ color: c }}>● {STAGE_LABEL[stage]} · {partners.length}</span>
                <span className="font-mono-tech text-[10px] text-white/50">${(total / 1000).toFixed(0)}k</span>
            </div>
            <div className="space-y-2 overflow-y-auto max-h-[600px]">
                {partners.map((p) => <PartnerCard key={p.id} p={p} onUpdate={onUpdate} onDelete={onDelete} onGenerate={onGenerate} />)}
                {partners.length === 0 && (
                    <div className="font-mono-tech text-[10px] text-white/35 italic p-4 text-center">// empty</div>
                )}
            </div>
        </div>
    );
}

function CaseStudyModal({ partner, onClose, onSaved }) {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [problem, setProblem] = useState("inbox triage chaos · BOL re-keying · slow follow-up");
    const [metrics, setMetrics] = useState("");
    const [quote, setQuote] = useState("");
    const [activeView, setActiveView] = useState("standard");

    const generate = async () => {
        setLoading(true); setResult(null);
        try {
            const { data } = await api.post(`/admin/design-partners/${partner.id}/case-study/generate`, {
                problem_summary: problem,
                metrics_snapshot: metrics,
                quote: quote || undefined,
            });
            setResult(data);
            if (data.parse_error) {
                toast.warning("Generated but JSON didn't parse cleanly — raw output shown");
            } else {
                toast.success("Case study drafted in both formats");
            }
            onSaved && onSaved();
        } catch (e) {
            if (!e?.isLlmBudget) toast.error("Case study generation failed");
        } finally { setLoading(false); }
    };

    return (
        <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/85 p-4" data-testid="case-study-modal">
            <div className="bg-[#02030a] border border-[#ff3b8a]/40 w-full max-w-3xl max-h-[92vh] overflow-y-auto">
                <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
                    <div>
                        <div className="mono-label text-[#ff3b8a]">CASE STUDY · {partner.company.toUpperCase()}</div>
                        <div className="font-display font-bold text-white text-lg mt-1">Generate · Both Formats</div>
                    </div>
                    <button onClick={onClose} className="btn-ghost text-xs px-3" data-testid="case-study-close">✕ CLOSE</button>
                </div>

                {!result && (
                    <div className="p-6 space-y-4">
                        <div>
                            <label className="mono-label text-white/55 text-[10px] block mb-2">PROBLEM SUMMARY</label>
                            <textarea
                                data-testid="case-study-problem"
                                rows={2}
                                value={problem}
                                onChange={(e) => setProblem(e.target.value)}
                                className="input-tech w-full text-sm"
                            />
                        </div>
                        <div>
                            <label className="mono-label text-white/55 text-[10px] block mb-2">METRICS SNAPSHOT · OPTIONAL</label>
                            <input
                                data-testid="case-study-metrics"
                                value={metrics}
                                onChange={(e) => setMetrics(e.target.value)}
                                placeholder="184 emails/day · 38s avg triage · 97.4% extract accuracy"
                                className="input-tech w-full text-sm"
                            />
                        </div>
                        <div>
                            <label className="mono-label text-white/55 text-[10px] block mb-2">RAW QUOTE · OPTIONAL</label>
                            <textarea
                                data-testid="case-study-quote"
                                rows={2}
                                value={quote}
                                onChange={(e) => setQuote(e.target.value)}
                                placeholder="JADE shaved 4 hours off my Tuesday — and I haven't touched the inbox since."
                                className="input-tech w-full text-sm"
                            />
                        </div>
                        <button
                            data-testid="case-study-generate-btn"
                            onClick={generate}
                            disabled={loading}
                            className="btn-jade w-full"
                        >
                            {loading ? "DRAFTING…" : "▶ GENERATE BOTH FORMATS"}
                        </button>
                    </div>
                )}

                {loading && !result && (
                    <div className="p-12 flex justify-center"><JadeWorking verb="drafting case study" size={64} /></div>
                )}

                {result && (
                    <div className="p-6 space-y-4" data-testid="case-study-result">
                        <div className="flex items-center gap-2">
                            <button
                                data-testid="case-study-view-standard"
                                onClick={() => setActiveView("standard")}
                                className="mono-label text-[10px] px-3 py-1.5 border"
                                style={{
                                    color: activeView === "standard" ? "#ccff00" : "rgba(255,255,255,0.55)",
                                    borderColor: activeView === "standard" ? "#ccff00" : "rgba(255,255,255,0.12)",
                                }}
                            >FORMAT A · STANDARD</button>
                            <button
                                data-testid="case-study-view-before-after"
                                onClick={() => setActiveView("before_after")}
                                className="mono-label text-[10px] px-3 py-1.5 border"
                                style={{
                                    color: activeView === "before_after" ? "#00ffff" : "rgba(255,255,255,0.55)",
                                    borderColor: activeView === "before_after" ? "#00ffff" : "rgba(255,255,255,0.12)",
                                }}
                            >FORMAT B · BEFORE / AFTER</button>
                            <div className="ml-auto"><SaveActions data={result} kind="json" filename={`case-${partner.company.replace(/\s+/g, "_")}`} /></div>
                        </div>

                        {result.parse_error && (
                            <pre className="bg-[#06081a] border border-[#ff3b8a]/30 p-3 font-mono-tech text-[11px] text-white/75 whitespace-pre-wrap">{result.raw}</pre>
                        )}

                        {activeView === "standard" && result.standard && !result.parse_error && (
                            <div className="space-y-3">
                                <div className="font-display font-black text-white text-xl">{result.standard.headline}</div>
                                <Section title="PROBLEM" color="#ff3b8a">{result.standard.problem}</Section>
                                <Section title="SOLUTION" color="#00ffff">{result.standard.solution}</Section>
                                <div>
                                    <div className="mono-label text-[#ccff00] mb-2">RESULTS</div>
                                    <ul className="space-y-1.5">
                                        {result.standard.results?.map((r, i) => (
                                            <li key={i} className="font-mono-tech text-xs text-white/85 leading-relaxed flex gap-2">
                                                <span className="text-[#ccff00]">▸</span>{r}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                                {result.standard.quote && (
                                    <blockquote className="border-l-2 border-[#7c5cff] pl-3 text-white/85 italic font-mono-tech text-sm">"{result.standard.quote}"</blockquote>
                                )}
                                {result.standard.cta && (
                                    <div className="mono-label text-[#ccff00] pt-2 border-t border-white/10">CTA · {result.standard.cta}</div>
                                )}
                            </div>
                        )}

                        {activeView === "before_after" && result.before_after && !result.parse_error && (
                            <div className="space-y-3">
                                <div className="font-display font-black text-white text-xl">{result.before_after.headline}</div>
                                <div className="grid sm:grid-cols-2 gap-3">
                                    <div className="border border-[#ff3b8a]/40 p-3 bg-[#06081a]">
                                        <div className="mono-label text-[#ff3b8a] mb-2">BEFORE</div>
                                        <ul className="space-y-1.5">
                                            {result.before_after.before?.map((b, i) => (
                                                <li key={i} className="font-mono-tech text-[11px] text-white/75 leading-snug">· {b}</li>
                                            ))}
                                        </ul>
                                    </div>
                                    <div className="border border-[#ccff00]/40 p-3 bg-[#06081a]">
                                        <div className="mono-label text-[#ccff00] mb-2">AFTER</div>
                                        <ul className="space-y-1.5">
                                            {result.before_after.after?.map((a, i) => (
                                                <li key={i} className="font-mono-tech text-[11px] text-white/75 leading-snug">· {a}</li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                                {result.before_after.quote && (
                                    <blockquote className="border-l-2 border-[#7c5cff] pl-3 text-white/85 italic font-mono-tech text-sm">"{result.before_after.quote}"</blockquote>
                                )}
                                {result.before_after.cta && (
                                    <div className="mono-label text-[#00ffff] pt-2 border-t border-white/10">CTA · {result.before_after.cta}</div>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

function Section({ title, color, children }) {
    return (
        <div>
            <div className="mono-label mb-1" style={{ color }}>{title}</div>
            <div className="font-mono-tech text-xs text-white/85 leading-relaxed">{children}</div>
        </div>
    );
}

function AddPartnerForm({ onAdded, onClose }) {
    const [company, setCompany] = useState("");
    const [city, setCity] = useState("");
    const [tier, setTier] = useState("operator");
    const [value, setValue] = useState(3000);
    const [busy, setBusy] = useState(false);

    const submit = async (e) => {
        e.preventDefault();
        if (!company.trim()) return;
        setBusy(true);
        try {
            await api.post("/admin/design-partners", {
                company: company.trim(),
                city: city.trim() || null,
                tier,
                pilot_value_usd: Number(value) || 3000,
            });
            toast.success(`Added ${company}`);
            setCompany(""); setCity(""); setValue(3000);
            onAdded();
            onClose && onClose();
        } catch { toast.error("Failed to add partner"); } finally { setBusy(false); }
    };

    return (
        <form onSubmit={submit} className="grid sm:grid-cols-4 gap-3 items-end p-4 border border-white/10 bg-[#06081a]" data-testid="add-partner-form">
            <div>
                <label className="mono-label text-[9px] text-white/55 block mb-1">COMPANY</label>
                <input data-testid="add-partner-company" value={company} onChange={(e) => setCompany(e.target.value)} className="input-tech w-full text-xs" required />
            </div>
            <div>
                <label className="mono-label text-[9px] text-white/55 block mb-1">CITY</label>
                <input data-testid="add-partner-city" value={city} onChange={(e) => setCity(e.target.value)} className="input-tech w-full text-xs" />
            </div>
            <div>
                <label className="mono-label text-[9px] text-white/55 block mb-1">TIER</label>
                <select data-testid="add-partner-tier" value={tier} onChange={(e) => setTier(e.target.value)} className="input-tech w-full text-xs">
                    <option value="operator">OPERATOR · $3k</option>
                    <option value="fleet">FLEET · $10k</option>
                    <option value="enterprise">ENTERPRISE · $25k</option>
                </select>
            </div>
            <div className="flex gap-2 items-end">
                <input data-testid="add-partner-value" type="number" value={value} onChange={(e) => setValue(e.target.value)} className="input-tech w-full text-xs" />
                <button data-testid="add-partner-submit" disabled={busy} className="btn-jade text-xs whitespace-nowrap px-4">+ ADD</button>
            </div>
        </form>
    );
}

export default function DesignPartnersPanel() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [showAdd, setShowAdd] = useState(false);
    const [caseFor, setCaseFor] = useState(null);

    const load = async () => {
        setLoading(true);
        try {
            const { data } = await api.get("/admin/design-partners");
            setData(data);
        } catch { toast.error("Failed to load design partners"); }
        finally { setLoading(false); }
    };

    useEffect(() => { load(); }, []);

    const remove = async (p) => {
        if (!confirm(`Remove ${p.company} from pipeline?`)) return;
        try {
            await api.delete(`/admin/design-partners/${p.id}`);
            toast.success(`Removed ${p.company}`);
            load();
        } catch { toast.error("Delete failed"); }
    };

    if (loading) {
        return <div className="deck-card p-12 flex justify-center"><JadeWorking verb="loading design partners" size={72} /></div>;
    }
    if (!data) return null;

    return (
        <div className="space-y-6" data-testid="design-partners-panel">
            <div className="deck-card p-6 relative" data-testid="dp-hero">
                <CornerBrackets />
                <SectionLabel idx={0} color="#ccff00">DESIGN PARTNERS · PIPELINE</SectionLabel>
                <div className="flex items-start justify-between gap-4 flex-wrap mt-2">
                    <div>
                        <h2 className="font-display font-black text-white text-4xl tracking-tighter">
                            Land <span className="accent-lime">{data.total}</span> design partners.
                            <span className="text-white/35"> Build the case studies. Compound.</span>
                        </h2>
                        <p className="text-white/65 text-sm mt-3 max-w-2xl leading-relaxed">
                            Mid-market + enterprise pipeline. Move accounts left-to-right. Land a Live partner, drop a Case Study, post it everywhere.
                        </p>
                    </div>
                    <button
                        data-testid="dp-toggle-add"
                        onClick={() => setShowAdd((v) => !v)}
                        className="btn-jade text-xs px-4"
                    >{showAdd ? "✕ CANCEL" : "+ ADD ACCOUNT"}</button>
                </div>

                <div className="grid sm:grid-cols-4 gap-4 mt-6">
                    <Stat k="ACCOUNTS" v={data.total} c="#fff" />
                    <Stat k="PIPELINE VALUE" v={`$${(data.total_pipeline_value / 1000).toFixed(0)}k/mo`} c="#ccff00" />
                    <Stat k="COMMITTED+" v={`$${(data.committed_or_live_value / 1000).toFixed(0)}k/mo`} c="#00ffff" />
                    <Stat k="ARR @ 100% CLOSE" v={`$${((data.total_pipeline_value * 12) / 1_000_000).toFixed(1)}M`} c="#ff3b8a" />
                </div>
            </div>

            {showAdd && <AddPartnerForm onAdded={load} onClose={() => setShowAdd(false)} />}

            <div className="overflow-x-auto pb-2">
                <div className="grid grid-cols-6 gap-3 min-w-[1700px]" data-testid="kanban">
                    {data.stages.map((s) => (
                        <StageColumn
                            key={s}
                            stage={s}
                            partners={data.by_stage[s] || []}
                            onUpdate={load}
                            onDelete={remove}
                            onGenerate={setCaseFor}
                        />
                    ))}
                </div>
            </div>

            {caseFor && (
                <CaseStudyModal
                    partner={caseFor}
                    onClose={() => setCaseFor(null)}
                    onSaved={load}
                />
            )}
        </div>
    );
}

function Stat({ k, v, c }) {
    return (
        <div className="border px-4 py-3" style={{ borderColor: `${c}33`, background: `${c}08` }}>
            <div className="mono-label text-[10px]" style={{ color: c }}>{k}</div>
            <div className="font-display font-black text-2xl mt-1" style={{ color: c }}>{v}</div>
        </div>
    );
}
