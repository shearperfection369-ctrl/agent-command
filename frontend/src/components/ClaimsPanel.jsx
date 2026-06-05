/**
 * ClaimsPanel — admin CLAIMS · QUEUE tab.
 *
 * Cargo / detention / overage_shortage claims with mixed autonomy:
 *   • Low-dollar (≤ CLAIMS_AUTO_FILE_LIMIT_USD) → auto-file
 *   • Higher-value → queue as ready_for_review, operator clicks FILE
 *
 * Filing delivers to every active webhook with kind="claims".
 */
import { useEffect, useState, useMemo } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "./Brackets";
import { JadeWorking } from "./JadeAvatar";

const KIND_LABELS = {
    cargo: "CARGO · DAMAGE / LOSS",
    detention: "DETENTION · ACCESSORIAL",
    overage_shortage: "OS&D · OVERAGE / SHORTAGE",
};
const KIND_COLORS = { cargo: "#ff3b8a", detention: "#ffce4f", overage_shortage: "#7c5cff" };
const STATUS_COLORS = {
    draft: "#7c5cff", ready_for_review: "#ffce4f", filed: "#00ffff",
    acknowledged: "#ccff00", resolved: "#ccff00", denied: "#ff3b8a", withdrawn: "rgba(255,255,255,0.4)",
};

function DraftWizard({ threads, onCreated }) {
    const [kind, setKind] = useState("cargo");
    const [threadId, setThreadId] = useState("");
    const [context, setContext] = useState("");
    const [autoFile, setAutoFile] = useState(true);
    const [draft, setDraft] = useState(null);
    const [drafting, setDrafting] = useState(false);
    const [saving, setSaving] = useState(false);

    const runDraft = async () => {
        if (!threadId && !context.trim()) {
            toast.error("Pick a memory thread or paste context.");
            return;
        }
        setDrafting(true);
        try {
            const body = { kind, provider: "anthropic" };
            if (threadId) body.memory_thread_id = threadId;
            if (context.trim()) body.context_text = context.trim();
            const { data } = await api.post("/claims/draft", body);
            setDraft(data);
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Draft failed.");
        } finally { setDrafting(false); }
    };

    const persist = async () => {
        if (!draft) return;
        setSaving(true);
        try {
            const body = { ...draft, auto_file: autoFile };
            const { data } = await api.post("/claims", body);
            toast.success(`Claim ${data.claim_number} ${data.status === "filed" ? "auto-filed" : "queued for review"}`);
            setDraft(null); setContext(""); setThreadId("");
            onCreated();
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Save failed.");
        } finally { setSaving(false); }
    };

    return (
        <div className="deck-card relative" data-testid="claims-draft-wizard">
            <CornerBrackets />
            <div className="px-6 py-4 border-b border-white/10">
                <div className="mono-label text-[#ccff00]">DRAFT · LLM-PACKED CLAIM</div>
                <div className="font-mono-tech text-[10px] text-white/55 mt-1">
                    Pick a memory thread (recommended — agent grounds on the full fact ledger) or paste operator notes. Review before saving.
                </div>
            </div>
            <div className="grid lg:grid-cols-3 gap-4 p-5">
                <div>
                    <label className="mono-label text-[10px] text-white/55">CLAIM KIND</label>
                    <select value={kind} onChange={(e) => setKind(e.target.value)} className="input-tech text-xs w-full mt-1" data-testid="claim-draft-kind">
                        <option value="cargo">CARGO</option>
                        <option value="detention">DETENTION</option>
                        <option value="overage_shortage">OVERAGE / SHORTAGE</option>
                    </select>
                </div>
                <div className="lg:col-span-2">
                    <label className="mono-label text-[10px] text-white/55">MEMORY THREAD · OPTIONAL</label>
                    <select value={threadId} onChange={(e) => setThreadId(e.target.value)} className="input-tech text-xs w-full mt-1" data-testid="claim-draft-thread">
                        <option value="">— none — paste context below instead</option>
                        {threads.map((t) => <option key={t.id} value={t.id}>{t.thread_type.toUpperCase()} · {t.thread_key} · {t.title}</option>)}
                    </select>
                </div>
                <div className="lg:col-span-3">
                    <label className="mono-label text-[10px] text-white/55">OPERATOR CONTEXT · OPTIONAL · LAYERED ONTO MEMORY</label>
                    <textarea data-testid="claim-draft-context" rows={3} value={context} onChange={(e) => setContext(e.target.value)} placeholder="Driver arrived 0800 Acme Dallas; released 1330. 3h beyond 2h free time at $75/h." className="input-tech text-xs w-full mt-1 font-mono-tech" />
                </div>
                <div className="lg:col-span-3 flex flex-wrap items-center gap-3">
                    <label className="flex items-center gap-2 mono-label text-[10px] text-white/85 cursor-pointer">
                        <input data-testid="claim-draft-autofile" type="checkbox" checked={autoFile} onChange={(e) => setAutoFile(e.target.checked)} />
                        AUTO-FILE IF UNDER LIMIT
                    </label>
                    <button data-testid="claim-draft-btn" disabled={drafting} onClick={runDraft} className="btn-jade text-xs disabled:opacity-50">
                        {drafting ? "DRAFTING…" : "▶ DRAFT WITH JADE"}
                    </button>
                </div>
            </div>

            {draft && (
                <div className="border-t border-white/10 p-5 bg-[#06081a]" data-testid="claim-draft-result">
                    <div className="mono-label text-[10px] text-[#ccff00]">DRAFT · REVIEW</div>
                    <div className="font-display font-bold text-white text-base mt-2">{draft.title}</div>
                    <div className="font-mono-tech text-[11px] text-white/85 mt-2 leading-relaxed">{draft.summary}</div>
                    <div className="grid sm:grid-cols-3 gap-3 mt-4 text-[11px] font-mono-tech">
                        <Pill k="AMOUNT" v={`$${(draft.claim_amount_usd || 0).toLocaleString()}`} c="#ccff00" />
                        <Pill k="LOAD ID" v={draft.load_id || "—"} c="#00ffff" />
                        <Pill k="BOL" v={draft.bol_number || "—"} c="#7c5cff" />
                    </div>
                    {draft.facts?.length > 0 && (
                        <ul className="mt-3 space-y-1">
                            {draft.facts.map((f, i) => <li key={i} className="font-mono-tech text-[10.5px] text-white/85 flex gap-2"><span className="text-[#ccff00]">·</span>{f}</li>)}
                        </ul>
                    )}
                    {draft.requested_remedy && (
                        <div className="mt-3 pt-3 border-t border-white/5">
                            <span className="mono-label text-[10px] text-[#ffce4f]">REQUESTED REMEDY</span>
                            <div className="font-mono-tech text-[11px] text-white/85 mt-1">{draft.requested_remedy}</div>
                        </div>
                    )}
                    <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between gap-3 flex-wrap">
                        <div className="font-mono-tech text-[10px] text-white/55">
                            {draft.would_auto_file
                                ? <span className="text-[#ccff00]">≤ ${draft.auto_file_limit_usd} · will auto-file</span>
                                : <span className="text-[#ffce4f]">&gt; ${draft.auto_file_limit_usd} · queues for operator review</span>}
                        </div>
                        <div className="flex gap-2">
                            <button onClick={() => setDraft(null)} className="btn-ghost text-xs">DISCARD</button>
                            <button data-testid="claim-save-btn" disabled={saving} onClick={persist} className="btn-jade text-xs disabled:opacity-50">
                                {saving ? "SAVING…" : "✓ SAVE CLAIM"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function Pill({ k, v, c }) {
    return (
        <div className="border px-3 py-2" style={{ borderColor: `${c}33`, background: `${c}08` }}>
            <div className="mono-label text-[9px]" style={{ color: c }}>{k}</div>
            <div className="font-display font-bold text-sm mt-0.5" style={{ color: c }}>{v}</div>
        </div>
    );
}

function ClaimRow({ c, onFile, onDelete }) {
    return (
        <div className="px-6 py-4 grid grid-cols-[140px_1fr_140px_140px_180px_120px] gap-3 items-center border-b border-white/5" data-testid={`claim-row-${c.id}`}>
            <span className="mono-label text-[10px]" style={{ color: KIND_COLORS[c.kind] }}>● {KIND_LABELS[c.kind]?.split(" · ")[0]}</span>
            <div>
                <div className="font-display font-bold text-white text-sm">{c.title}</div>
                <div className="font-mono-tech text-[10px] text-white/55 mt-0.5">{c.claim_number} · {c.load_id || "no load id"}</div>
            </div>
            <div className="font-display font-black text-base text-[#ccff00]">${(c.claim_amount_usd || 0).toLocaleString()}</div>
            <span className="mono-label text-[10px]" style={{ color: STATUS_COLORS[c.status] }}>
                {c.status.toUpperCase().replace(/_/g, " ")}
                {c.auto_filed && <span className="ml-1 text-[8px] text-[#ccff00]">· AUTO</span>}
            </span>
            <span className="font-mono-tech text-[10px] text-white/40">{new Date(c.created_at).toLocaleString()}</span>
            <div className="flex gap-1 justify-end">
                {(c.status === "ready_for_review" || c.status === "draft") && (
                    <button data-testid={`claim-file-${c.id}`} onClick={() => onFile(c.id)} className="btn-jade text-[10px] px-2">FILE →</button>
                )}
                <button onClick={() => onDelete(c.id)} className="mono-label text-[10px] text-white/40 hover:text-[#ff3b8a]">✕</button>
            </div>
        </div>
    );
}

export default function ClaimsPanel() {
    const [claims, setClaims] = useState({ claims: [], count: 0, open: 0, filed: 0, total_amount_usd: 0, auto_file_limit_usd: 500 });
    const [threads, setThreads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filterKind, setFilterKind] = useState("");
    const [filterStatus, setFilterStatus] = useState("");

    const load = async () => {
        try {
            const params = {};
            if (filterKind) params.kind = filterKind;
            if (filterStatus) params.status = filterStatus;
            const [c, t] = await Promise.all([
                api.get("/claims", { params }),
                api.get("/memory/threads", { params: { limit: 50 } }),
            ]);
            setClaims(c.data);
            setThreads(t.data.threads || []);
        } catch { toast.error("Failed to load claims."); }
        finally { setLoading(false); }
    };

    useEffect(() => { setLoading(true); load(); }, [filterKind, filterStatus]);

    const fileClaim = async (id) => {
        try {
            const { data } = await api.post(`/claims/${id}/file`);
            const delivered = data.delivery?.delivered_count ?? 0;
            toast.success(delivered > 0 ? `Filed · delivered to ${delivered} webhook(s)` : "Filed · no claims webhook configured");
            load();
        } catch (e) {
            toast.error(e?.response?.data?.detail || "File failed.");
        }
    };

    const deleteClaim = async (id) => {
        if (!confirm("Delete this claim?")) return;
        try {
            await api.delete(`/claims/${id}`);
            toast.success("Deleted");
            load();
        } catch { toast.error("Delete failed."); }
    };

    const breakdown = useMemo(() => {
        const out = { cargo: 0, detention: 0, overage_shortage: 0 };
        for (const c of claims.claims) out[c.kind] = (out[c.kind] || 0) + 1;
        return out;
    }, [claims]);

    if (loading) return <div className="deck-card p-12 flex justify-center"><JadeWorking verb="loading claims" size={72} /></div>;

    return (
        <div className="space-y-6" data-testid="claims-panel">
            <div className="deck-card p-6 relative">
                <CornerBrackets />
                <SectionLabel idx={0} color="#ff3b8a">CLAIMS · QUEUE</SectionLabel>
                <h2 className="font-display font-black text-white text-4xl tracking-tighter mt-2">
                    Agent files claims. <span className="accent-pink">Operator approves.</span>
                </h2>
                <p className="text-white/65 text-sm mt-3 max-w-2xl leading-relaxed">
                    Cargo · detention · OS&amp;D. Low-dollar (≤ ${claims.auto_file_limit_usd}) auto-files; higher value queues for human review. Filing delivers to every active webhook with kind=&quot;claims&quot;.
                </p>
                <div className="grid sm:grid-cols-5 gap-3 mt-5">
                    <Stat k="TOTAL CLAIMS" v={claims.count} c="#ccff00" />
                    <Stat k="OPEN" v={claims.open} c="#ffce4f" />
                    <Stat k="FILED" v={claims.filed} c="#00ffff" />
                    <Stat k="TOTAL · USD" v={`$${(claims.total_amount_usd || 0).toLocaleString()}`} c="#ff3b8a" />
                    <Stat k="AUTO LIMIT" v={`$${claims.auto_file_limit_usd}`} c="#7c5cff" />
                </div>
                <div className="mt-4 grid sm:grid-cols-3 gap-2">
                    {Object.entries(KIND_LABELS).map(([k, label]) => (
                        <div key={k} className="border px-3 py-2" style={{ borderColor: `${KIND_COLORS[k]}33`, background: `${KIND_COLORS[k]}08` }}>
                            <div className="mono-label text-[10px]" style={{ color: KIND_COLORS[k] }}>{label}</div>
                            <div className="font-display font-black text-xl mt-0.5" style={{ color: KIND_COLORS[k] }}>{breakdown[k] || 0}</div>
                        </div>
                    ))}
                </div>
            </div>

            <DraftWizard threads={threads} onCreated={load} />

            <div className="deck-card relative" data-testid="claims-table">
                <CornerBrackets />
                <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between flex-wrap gap-2">
                    <div className="mono-label text-[#ff3b8a]">QUEUE</div>
                    <div className="flex gap-2 flex-wrap">
                        <select value={filterKind} onChange={(e) => setFilterKind(e.target.value)} className="input-tech text-[10px] py-1" data-testid="claims-filter-kind">
                            <option value="">ALL KINDS</option>
                            <option value="cargo">CARGO</option>
                            <option value="detention">DETENTION</option>
                            <option value="overage_shortage">OS&D</option>
                        </select>
                        <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="input-tech text-[10px] py-1" data-testid="claims-filter-status">
                            <option value="">ALL STATUS</option>
                            <option value="ready_for_review">READY FOR REVIEW</option>
                            <option value="filed">FILED</option>
                            <option value="resolved">RESOLVED</option>
                            <option value="denied">DENIED</option>
                        </select>
                    </div>
                </div>
                {claims.claims.length === 0 ? (
                    <div className="px-6 py-12 text-center font-mono-tech text-xs text-white/40">// queue clean · no claims //</div>
                ) : (
                    <div>
                        {claims.claims.map((c) => (
                            <ClaimRow key={c.id} c={c} onFile={fileClaim} onDelete={deleteClaim} />
                        ))}
                    </div>
                )}
            </div>

            <div className="font-mono-tech text-[10px] text-white/40 leading-relaxed">
                ▸ Configure delivery: <code className="text-[#00ffff]">/api/webhooks</code> → kind=&quot;claims&quot;. Tune the auto-file threshold via <code className="text-[#00ffff]">CLAIMS_AUTO_FILE_LIMIT_USD</code> in backend/.env.
            </div>
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
