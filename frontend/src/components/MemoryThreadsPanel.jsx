/**
 * MemoryThreadsPanel — admin MEMORY · THREADS tab.
 *
 * Per-topic workflow memory:
 *   • Threads scoped by (thread_type, thread_key): load / customer / issue
 *   • Distilled facts ledger (HAPPENED · DECIDED · OPEN QUESTIONS · RISKS · NEXT ACTIONS)
 *   • Raw transcript timeline
 *   • Force-distill + close/archive controls
 */
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "./Brackets";
import { JadeWorking } from "./JadeAvatar";

const TYPE_LABELS = {
    load: "LOAD / SHIPMENT",
    customer: "CUSTOMER / SHIPPER",
    issue: "ISSUE / CLAIM",
};
const TYPE_COLORS = { load: "#ccff00", customer: "#00ffff", issue: "#ff3b8a" };
const CAT_LABELS = {
    happened: "HAPPENED",
    decided: "DECIDED",
    open_question: "OPEN QUESTIONS",
    risk: "RISKS",
    next_action: "NEXT ACTIONS",
};
const CAT_COLORS = {
    happened: "#ccff00",
    decided: "#00ffff",
    open_question: "#ffce4f",
    risk: "#ff3b8a",
    next_action: "#7c5cff",
};

function NewThreadForm({ onCreated }) {
    const [type, setType] = useState("load");
    const [key, setKey] = useState("");
    const [title, setTitle] = useState("");
    const [busy, setBusy] = useState(false);

    const submit = async (e) => {
        e.preventDefault();
        if (!key.trim()) return;
        setBusy(true);
        try {
            const { data } = await api.post("/memory/threads", { thread_type: type, thread_key: key.trim(), title: title.trim() || null });
            toast.success("Thread opened.");
            setKey(""); setTitle("");
            onCreated(data);
        } catch { toast.error("Could not open thread."); }
        finally { setBusy(false); }
    };

    return (
        <form onSubmit={submit} className="grid sm:grid-cols-[140px_1fr_1fr_140px] gap-2 items-end p-4 border-b border-white/10 bg-[#06081a]" data-testid="memory-new-thread">
            <div>
                <label className="mono-label text-[9px] text-white/55">TYPE</label>
                <select value={type} onChange={(e) => setType(e.target.value)} className="input-tech text-xs w-full mt-1" data-testid="memory-thread-type">
                    <option value="load">LOAD</option>
                    <option value="customer">CUSTOMER</option>
                    <option value="issue">ISSUE / CLAIM</option>
                </select>
            </div>
            <div>
                <label className="mono-label text-[9px] text-white/55">KEY · LOAD_ID · COMPANY · ISSUE_ID</label>
                <input data-testid="memory-thread-key" value={key} onChange={(e) => setKey(e.target.value)} required className="input-tech text-xs w-full mt-1" placeholder="LD-2026-00481" />
            </div>
            <div>
                <label className="mono-label text-[9px] text-white/55">TITLE · OPTIONAL</label>
                <input data-testid="memory-thread-title" value={title} onChange={(e) => setTitle(e.target.value)} className="input-tech text-xs w-full mt-1" placeholder="Acme reefer · MN→TX" />
            </div>
            <button data-testid="memory-thread-create" disabled={busy} className="btn-jade text-xs disabled:opacity-50">+ OPEN THREAD</button>
        </form>
    );
}

function TurnComposer({ threadId, onAppend }) {
    const [role, setRole] = useState("operator");
    const [content, setContent] = useState("");
    const [busy, setBusy] = useState(false);

    const submit = async (e) => {
        e.preventDefault();
        if (!content.trim()) return;
        setBusy(true);
        try {
            await api.post(`/memory/threads/${threadId}/turns`, { role, content });
            setContent("");
            onAppend();
        } catch { toast.error("Append failed."); }
        finally { setBusy(false); }
    };

    return (
        <form onSubmit={submit} className="grid sm:grid-cols-[140px_1fr_120px] gap-2 items-end p-4 border-t border-white/10 bg-[#06081a]" data-testid="memory-turn-composer">
            <select value={role} onChange={(e) => setRole(e.target.value)} className="input-tech text-xs" data-testid="memory-turn-role">
                <option value="operator">OPERATOR</option>
                <option value="agent_action">AGENT ACTION</option>
                <option value="user">USER</option>
                <option value="assistant">ASSISTANT</option>
                <option value="system">SYSTEM</option>
            </select>
            <input data-testid="memory-turn-content" value={content} onChange={(e) => setContent(e.target.value)} placeholder="add a turn…" className="input-tech text-xs" required />
            <button data-testid="memory-turn-append" disabled={busy} className="btn-jade text-xs disabled:opacity-50">+ APPEND</button>
        </form>
    );
}

function FactsLedger({ facts }) {
    const grouped = useMemo(() => {
        const g = { happened: [], decided: [], open_question: [], risk: [], next_action: [] };
        for (const f of facts || []) {
            (g[f.category] || (g[f.category] = [])).push(f.text);
        }
        return g;
    }, [facts]);

    return (
        <div className="grid lg:grid-cols-5 gap-3" data-testid="facts-ledger">
            {["happened", "decided", "open_question", "risk", "next_action"].map((cat) => (
                <div key={cat} className="border p-3" style={{ borderColor: `${CAT_COLORS[cat]}44`, background: `${CAT_COLORS[cat]}08` }} data-testid={`facts-${cat}`}>
                    <div className="mono-label text-[10px]" style={{ color: CAT_COLORS[cat] }}>{CAT_LABELS[cat]} · {grouped[cat]?.length || 0}</div>
                    <ul className="space-y-1.5 mt-2">
                        {(grouped[cat] || []).map((t, i) => (
                            <li key={i} className="font-mono-tech text-[10.5px] text-white/85 leading-snug flex gap-1.5"><span style={{ color: CAT_COLORS[cat] }}>·</span>{t}</li>
                        ))}
                        {(!grouped[cat] || grouped[cat].length === 0) && <li className="font-mono-tech text-[10px] text-white/30">// none</li>}
                    </ul>
                </div>
            ))}
        </div>
    );
}

function ThreadDetail({ threadId, onClose, onChanged }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [distilling, setDistilling] = useState(false);

    const load = async () => {
        try {
            const { data } = await api.get(`/memory/threads/${threadId}`);
            setData(data);
        } catch { toast.error("Failed to load thread."); }
        finally { setLoading(false); }
    };

    useEffect(() => { setLoading(true); load(); }, [threadId]);

    const forceDistill = async () => {
        setDistilling(true);
        try {
            await api.post(`/memory/threads/${threadId}/distill`);
            toast.success("Distillation complete.");
            await load(); onChanged?.();
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Distill failed.");
        } finally { setDistilling(false); }
    };

    const setStatus = async (status) => {
        try {
            await api.patch(`/memory/threads/${threadId}`, null, { params: { status } });
            toast.success(`Status → ${status}`);
            await load(); onChanged?.();
        } catch { toast.error("Status update failed."); }
    };

    if (loading) return <div className="deck-card p-12 flex justify-center"><JadeWorking verb="loading thread" size={56} /></div>;
    if (!data) return null;

    const t = data.thread;
    const c = TYPE_COLORS[t.thread_type] || "#ccff00";

    return (
        <div className="space-y-4" data-testid="thread-detail">
            <div className="deck-card relative p-5" style={{ borderColor: `${c}55` }}>
                <CornerBrackets />
                <div className="flex items-baseline justify-between gap-3 flex-wrap">
                    <div>
                        <span className="mono-label text-[10px]" style={{ color: c }}>{TYPE_LABELS[t.thread_type]} · {t.thread_key}</span>
                        <div className="font-display font-black text-white text-2xl mt-1">{t.title}</div>
                        <div className="font-mono-tech text-[10px] text-white/55 mt-1">
                            {data.turns.length} turn(s) · distilled at turn {t.last_distilled_at_turn} of {t.turn_count} · status <span className="text-[#ccff00]">{t.status.toUpperCase()}</span>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button data-testid="thread-distill-btn" onClick={forceDistill} disabled={distilling} className="btn-jade text-xs disabled:opacity-50">
                            {distilling ? "DISTILLING…" : "↻ DISTILL"}
                        </button>
                        {t.status !== "closed" && <button data-testid="thread-close-btn" onClick={() => setStatus("closed")} className="btn-ghost text-xs">CLOSE</button>}
                        {t.status !== "archived" && <button data-testid="thread-archive-btn" onClick={() => setStatus("archived")} className="btn-ghost text-xs">ARCHIVE</button>}
                        <button data-testid="thread-back-btn" onClick={onClose} className="btn-ghost text-xs">← BACK</button>
                    </div>
                </div>
            </div>

            <FactsLedger facts={t.facts} />

            <div className="deck-card relative" data-testid="thread-transcript">
                <CornerBrackets />
                <div className="px-6 py-4 border-b border-white/10">
                    <div className="mono-label text-[#7c5cff]">TRANSCRIPT · {data.turns.length} TURNS</div>
                </div>
                <div className="divide-y divide-white/5 max-h-[420px] overflow-y-auto">
                    {data.turns.length === 0 ? (
                        <div className="p-8 font-mono-tech text-xs text-white/40 text-center">// no turns yet</div>
                    ) : data.turns.map((turn) => (
                        <div key={turn.id} className="p-3 grid grid-cols-[140px_1fr_180px] gap-3 items-start" data-testid={`turn-${turn.id}`}>
                            <span className="mono-label text-[10px]" style={{
                                color: turn.role === "user" || turn.role === "operator" ? "#ccff00" :
                                       turn.role === "assistant" ? "#00ffff" :
                                       turn.role === "agent_action" ? "#7c5cff" : "#ffce4f",
                            }}>{turn.role.toUpperCase()}</span>
                            <div className="font-mono-tech text-[11px] text-white/85 whitespace-pre-wrap leading-snug">{turn.content}</div>
                            <span className="font-mono-tech text-[10px] text-white/35 text-right">{new Date(turn.created_at).toLocaleString()}</span>
                        </div>
                    ))}
                </div>
                <TurnComposer threadId={threadId} onAppend={() => { load(); onChanged?.(); }} />
            </div>
        </div>
    );
}

export default function MemoryThreadsPanel() {
    const [threads, setThreads] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedId, setSelectedId] = useState(null);
    const [filterType, setFilterType] = useState("");

    const load = async () => {
        try {
            const { data } = await api.get("/memory/threads", { params: filterType ? { thread_type: filterType } : {} });
            setThreads(data.threads);
        } catch { toast.error("Failed to load threads."); }
        finally { setLoading(false); }
    };

    useEffect(() => { setLoading(true); load(); }, [filterType]);

    if (loading) return <div className="deck-card p-12 flex justify-center"><JadeWorking verb="loading memory" size={72} /></div>;

    if (selectedId) {
        return <ThreadDetail threadId={selectedId} onClose={() => setSelectedId(null)} onChanged={load} />;
    }

    return (
        <div className="space-y-6" data-testid="memory-panel">
            <div className="deck-card p-6 relative">
                <CornerBrackets />
                <SectionLabel idx={0} color="#7c5cff">MEMORY · THREADS</SectionLabel>
                <h2 className="font-display font-black text-white text-4xl tracking-tighter mt-2">
                    Workflow memory. <span className="accent-cyan">Per topic.</span>
                </h2>
                <p className="text-white/65 text-sm mt-3 max-w-2xl leading-relaxed">
                    Per-load, per-customer, per-issue threads. Every operator + agent turn lands here.
                    JADE auto-distills the transcript into a five-category fact ledger so the next agent call recalls the whole story.
                </p>
                <div className="grid sm:grid-cols-4 gap-3 mt-5">
                    <Stat k="THREADS" v={threads.length} c="#ccff00" />
                    <Stat k="LOADS" v={threads.filter((t) => t.thread_type === "load").length} c="#ccff00" />
                    <Stat k="CUSTOMERS" v={threads.filter((t) => t.thread_type === "customer").length} c="#00ffff" />
                    <Stat k="ISSUES" v={threads.filter((t) => t.thread_type === "issue").length} c="#ff3b8a" />
                </div>
            </div>

            <div className="deck-card relative">
                <CornerBrackets />
                <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between flex-wrap gap-2">
                    <div className="mono-label text-[#ccff00]">ACTIVE THREADS</div>
                    <div className="flex gap-2">
                        {["", "load", "customer", "issue"].map((f) => (
                            <button key={f || "all"} onClick={() => setFilterType(f)} data-testid={`filter-${f || "all"}`}
                                className="px-3 py-1.5 mono-label text-[10px]"
                                style={{
                                    border: `1px solid ${filterType === f ? "#ccff00" : "rgba(255,255,255,0.10)"}`,
                                    color: filterType === f ? "#ccff00" : "rgba(255,255,255,0.55)",
                                    background: filterType === f ? "#ccff0011" : "transparent",
                                }}>{f.toUpperCase() || "ALL"}</button>
                        ))}
                    </div>
                </div>
                <NewThreadForm onCreated={(t) => { setSelectedId(t.id); load(); }} />
                {threads.length === 0 ? (
                    <div className="px-6 py-12 text-center font-mono-tech text-xs text-white/40">// no threads · open one above //</div>
                ) : (
                    <div className="divide-y divide-white/5">
                        {threads.map((t) => (
                            <button key={t.id} onClick={() => setSelectedId(t.id)} data-testid={`thread-row-${t.id}`}
                                className="w-full text-left px-6 py-4 grid grid-cols-[140px_1fr_120px_120px_140px] gap-3 items-center hover:bg-white/5 transition">
                                <span className="mono-label text-[10px]" style={{ color: TYPE_COLORS[t.thread_type] }}>● {TYPE_LABELS[t.thread_type]}</span>
                                <div>
                                    <div className="font-display font-bold text-white text-sm">{t.title}</div>
                                    <div className="font-mono-tech text-[10px] text-white/55">{t.thread_key}</div>
                                </div>
                                <div className="font-mono-tech text-[10px]">
                                    <span className="text-[#ccff00]">{t.turn_count}</span> turns
                                </div>
                                <div className="font-mono-tech text-[10px]">
                                    <span className="text-[#00ffff]">{(t.facts || []).length}</span> facts
                                </div>
                                <span className="font-mono-tech text-[10px] text-white/35 text-right">{new Date(t.updated_at).toLocaleString()}</span>
                            </button>
                        ))}
                    </div>
                )}
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
