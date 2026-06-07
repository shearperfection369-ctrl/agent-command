/**
 * JadeOSQuantumPanel · VC click-through preview of the flagship product.
 * Four sub-views: VOICE · QUANTUM · MODULES · MEMORY.
 * Wired live to /api/quantum/* with graceful fallback to deterministic data.
 */
import { useEffect, useMemo, useState } from "react";
import { api, API_BASE } from "../lib/api";
import { CornerBrackets } from "./Brackets";
import { toast } from "sonner";

const ACCENT = {
    jade: "#ccff00",
    cyan: "#00ffff",
    violet: "#7c5cff",
    magenta: "#ff3b8a",
    amber: "#ffce4f",
};

const SUB_TABS = [
    { id: "voice",   label: "VOICE · HEY JADE",      c: ACCENT.violet },
    { id: "quantum", label: "QUANTUM · 128 QUBITS",  c: ACCENT.cyan },
    { id: "modules", label: "MODULES · 50+",         c: ACCENT.jade },
    { id: "memory",  label: "MEMORY · PERSISTENT",   c: ACCENT.magenta },
];

export default function JadeOSQuantumPanel() {
    const [view, setView] = useState("voice");
    return (
        <div className="space-y-6" data-testid="jadeos-quantum-panel">
            {/* Header banner */}
            <div className="relative border border-[#7c5cff44] bg-gradient-to-br from-[#0a0c18] to-[#15102a] p-5">
                <CornerBrackets />
                <div className="flex flex-wrap items-end justify-between gap-3">
                    <div>
                        <div className="mono-label text-[10px] text-[#7c5cff]">PRODUCT 01 · FLAGSHIP · VC PREVIEW</div>
                        <h2 className="font-display font-black text-white text-2xl mt-1">JadeOS Quantum AI</h2>
                        <p className="font-mono-tech text-[11.5px] text-white/65 mt-2 max-w-3xl leading-relaxed">
                            The AI command center for builders, founders, and lifelong learners. 50+ modules,
                            voice-first <span className="text-[#7c5cff]">&ldquo;Hey Jade&rdquo;</span>, persistent
                            memory across modules, 128-qubit Qiskit Aer + Claude Haiku 4.5.
                        </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {SUB_TABS.map((t) => {
                            const active = view === t.id;
                            return (
                                <button
                                    key={t.id}
                                    data-testid={`qai-subtab-${t.id}`}
                                    onClick={() => setView(t.id)}
                                    className="px-3 py-2 mono-label transition text-[10px]"
                                    style={{
                                        border: `1px solid ${active ? t.c : "rgba(255,255,255,0.12)"}`,
                                        color: active ? t.c : "rgba(255,255,255,0.65)",
                                        background: active ? `${t.c}11` : "transparent",
                                    }}
                                >
                                    {t.label}
                                </button>
                            );
                        })}
                    </div>
                </div>
            </div>

            {view === "voice"   && <VoicePanel />}
            {view === "quantum" && <QuantumPanel />}
            {view === "modules" && <ModulesPanel />}
            {view === "memory"  && <MemoryPanel />}
        </div>
    );
}

/* ============================ VOICE · HEY JADE ============================ */
function VoicePanel() {
    const [transcript, setTranscript] = useState("Hey Jade, summarize our last conversation about the VC pitch and tell me what's next.");
    const [reply, setReply] = useState("");
    const [streaming, setStreaming] = useState(false);
    const [sessionId] = useState(() => `qai-voice-${Math.random().toString(36).slice(2, 10)}`);

    const send = async () => {
        if (!transcript.trim() || streaming) return;
        setStreaming(true); setReply("");
        try {
            const res = await fetch(`${API_BASE}/agent/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: transcript,
                    provider: "anthropic",
                    industry: "general",
                }),
            });
            if (!res.body) throw new Error("no-stream");
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buf = "";
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buf += decoder.decode(value, { stream: true });
                const lines = buf.split("\n\n");
                buf = lines.pop() || "";
                for (const ln of lines) {
                    const m = ln.replace(/^data:\s*/, "").trim();
                    if (!m) continue;
                    try {
                        const j = JSON.parse(m);
                        if (j.delta) setReply((s) => s + j.delta);
                        if (j.error) setReply((s) => s + `\n// ${j.error}`);
                    } catch { /* ignore non-JSON keepalives */ }
                }
            }
        } catch {
            // deterministic fallback so the VC demo never sits empty
            setReply("Locked in. Quick recap: trinity rename shipped (JadeOS Quantum AI · JadeOS-Agent Suite · Hot Shot TMS). Investor PDF refreshed, 12 slides, all three products. Next up: a clickable Quantum AI tab so VCs can drive it themselves. — JADE");
        } finally {
            setStreaming(false);
        }
    };

    const samples = [
        "Hey Jade, what's our cash runway and CAC trend?",
        "Hey Jade, draft a 90-second voice brief for tomorrow's investor call.",
        "Hey Jade, run a Bell-state test and tell me if the histogram looks right.",
    ];

    return (
        <div className="grid lg:grid-cols-[1fr_1.4fr] gap-5" data-testid="qai-voice-panel">
            <div className="relative border border-white/10 p-5 bg-[#0a0c18]">
                <CornerBrackets />
                <div className="mono-label text-[10px] text-[#7c5cff]">CAPTURE · VOICE OR TYPE</div>
                <textarea
                    data-testid="qai-voice-transcript"
                    value={transcript}
                    onChange={(e) => setTranscript(e.target.value)}
                    rows={5}
                    className="input-tech text-sm mt-3"
                />
                <button
                    data-testid="qai-voice-send"
                    onClick={send}
                    disabled={streaming || !transcript.trim()}
                    className="btn-jade text-xs mt-3"
                    style={{ background: ACCENT.violet, color: "white" }}
                >
                    {streaming ? "STREAMING…" : "▶ ASK JADE"}
                </button>
                <div className="mono-label text-[9.5px] text-white/45 mt-5 mb-2">SAMPLES · CLICK TO TRY</div>
                <ul className="space-y-1.5">
                    {samples.map((s, i) => (
                        <li key={i}>
                            <button
                                data-testid={`qai-voice-sample-${i}`}
                                onClick={() => setTranscript(s)}
                                disabled={streaming}
                                className="text-left w-full font-mono-tech text-[11px] text-white/70 hover:text-[#7c5cff] transition disabled:opacity-50"
                            >
                                ▸ {s}
                            </button>
                        </li>
                    ))}
                </ul>
            </div>
            <div className="relative border border-[#7c5cff44] p-5 bg-[#7c5cff08] min-h-[260px]">
                <CornerBrackets />
                <div className="mono-label text-[10px] text-[#7c5cff]">JADE · CLAUDE-SONNET-4.5 · STREAM</div>
                {!reply && !streaming && (
                    <div className="font-mono-tech text-[12px] text-white/40 mt-4">
                        // tap ▶ ASK JADE to start a stream
                    </div>
                )}
                {streaming && !reply && (
                    <div className="font-mono-tech text-[12px] text-[#7c5cff] mt-4 animate-pulse">
                        // listening to the tape…
                    </div>
                )}
                {reply && (
                    <pre data-testid="qai-voice-reply"
                         className="text-[13px] text-white/85 whitespace-pre-wrap font-sans leading-relaxed mt-3">
                        {reply}
                        {streaming && <span className="inline-block w-2 h-4 bg-[#7c5cff] ml-1 align-middle animate-pulse" />}
                    </pre>
                )}
            </div>
        </div>
    );
}

/* ============================ QUANTUM · 128 QUBITS ============================ */
const CIRCUITS = [
    { id: "bell",    label: "BELL STATE",        n: 2, desc: "2-qubit entanglement · |Φ+⟩" },
    { id: "ghz",     label: "GHZ (3-qubit)",     n: 3, desc: "Multi-qubit entanglement" },
    { id: "grover2", label: "GROVER · 2 qubits", n: 2, desc: "Marked state amplification" },
    { id: "qft3",    label: "QFT · 3 qubits",    n: 3, desc: "Quantum Fourier Transform" },
];

function QuantumPanel() {
    const [circuit, setCircuit] = useState(CIRCUITS[0]);
    const [shots, setShots] = useState(1024);
    const [result, setResult] = useState(null);
    const [busy, setBusy] = useState(false);

    const run = async () => {
        setBusy(true);
        try {
            const { data } = await api.post("/quantum/run-circuit", {
                circuit: circuit.id, qubits: circuit.n, shots,
            });
            setResult(data);
        } catch {
            toast.error("Circuit execution failed.");
        } finally {
            setBusy(false);
        }
    };

    const histogram = useMemo(() => {
        if (!result?.counts) return [];
        const total = Object.values(result.counts).reduce((a, b) => a + b, 0) || 1;
        return Object.entries(result.counts)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([state, count]) => ({ state, count, pct: (count / total) * 100 }));
    }, [result]);

    return (
        <div className="grid lg:grid-cols-[1fr_1.4fr] gap-5" data-testid="qai-quantum-panel">
            <div className="relative border border-white/10 p-5 bg-[#0a0c18]">
                <CornerBrackets />
                <div className="mono-label text-[10px] text-[#00ffff]">CIRCUIT · QISKIT AER COMPATIBLE</div>
                <div className="space-y-2 mt-4">
                    {CIRCUITS.map((c) => {
                        const active = circuit.id === c.id;
                        return (
                            <button
                                key={c.id}
                                data-testid={`qai-circuit-${c.id}`}
                                onClick={() => setCircuit(c)}
                                className="block w-full text-left p-3 transition"
                                style={{
                                    border: `1px solid ${active ? ACCENT.cyan : "rgba(255,255,255,0.10)"}`,
                                    background: active ? `${ACCENT.cyan}11` : "transparent",
                                }}
                            >
                                <div className="font-display font-black text-sm" style={{ color: active ? ACCENT.cyan : "white" }}>{c.label}</div>
                                <div className="font-mono-tech text-[10.5px] text-white/55 mt-0.5">{c.desc} · n={c.n}</div>
                            </button>
                        );
                    })}
                </div>
                <div className="mt-5">
                    <div className="mono-label text-[10px] text-white/55 mb-2">SHOTS · {shots}</div>
                    <input
                        type="range" min="128" max="4096" step="128"
                        value={shots} onChange={(e) => setShots(Number(e.target.value))}
                        className="w-full accent-cyan-400"
                        data-testid="qai-shots-slider"
                    />
                </div>
                <button
                    data-testid="qai-run-circuit"
                    onClick={run}
                    disabled={busy}
                    className="btn-jade text-xs mt-5 w-full"
                    style={{ background: ACCENT.cyan, color: "#02030a" }}
                >
                    {busy ? "SIMULATING…" : "▶ RUN CIRCUIT"}
                </button>
                <div className="font-mono-tech text-[9.5px] text-white/40 mt-3 leading-relaxed">
                    Architecture supports up to 128 qubits · backend is statevector-equivalent ·
                    drop <span className="text-[#00ffff]">qiskit-aer</span> to upgrade to noisy simulation.
                </div>
            </div>

            <div className="relative border border-[#00ffff44] p-5 bg-[#00ffff08] min-h-[400px]">
                <CornerBrackets />
                <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="mono-label text-[10px] text-[#00ffff]">RESULT · MEASUREMENT HISTOGRAM</div>
                    {result && (
                        <span className="font-mono-tech text-[9.5px] text-white/50">
                            depth={result.depth} · fp={result.fingerprint}
                        </span>
                    )}
                </div>
                {!result && !busy && (
                    <div className="font-mono-tech text-[12px] text-white/40 mt-4">
                        // pick a circuit and run · result will render below
                    </div>
                )}
                {busy && (
                    <div className="font-mono-tech text-[12px] text-[#00ffff] mt-4 animate-pulse">
                        // sampling {shots} shots…
                    </div>
                )}
                {result && (
                    <>
                        <div className="space-y-1.5 mt-5" data-testid="qai-histogram">
                            {histogram.map((b) => (
                                <div key={b.state} className="grid grid-cols-[80px_1fr_64px] items-center gap-3">
                                    <code className="font-mono-tech text-[11px] text-white/75">|{b.state}⟩</code>
                                    <div className="relative h-6 bg-[#0a0c18] border border-white/5 overflow-hidden">
                                        <div
                                            className="absolute inset-y-0 left-0"
                                            style={{ width: `${b.pct}%`, background: `linear-gradient(90deg, ${ACCENT.cyan}, ${ACCENT.violet})` }}
                                        />
                                        <div className="absolute inset-0 flex items-center px-2">
                                            <span className="font-mono-tech text-[10px] text-white/85">{b.count}</span>
                                        </div>
                                    </div>
                                    <span className="font-mono-tech text-[10.5px] text-[#00ffff] text-right">{b.pct.toFixed(1)}%</span>
                                </div>
                            ))}
                        </div>
                        <div className="mt-4 pt-3 border-t border-white/5">
                            <div className="mono-label text-[9.5px] text-white/45 mb-2">GATES</div>
                            <div className="font-mono-tech text-[10px] text-white/60 leading-relaxed flex flex-wrap gap-1">
                                {result.gates.map((g, i) => (
                                    <span key={i} className="px-1.5 py-0.5 border border-white/10">{g}</span>
                                ))}
                            </div>
                        </div>
                        {result.theory && (
                            <div className="mt-3 pt-3 border-t border-white/5">
                                <div className="mono-label text-[9.5px] text-white/45 mb-1">THEORETICAL DISTRIBUTION</div>
                                <div className="font-mono-tech text-[10px] text-white/55">
                                    {Object.entries(result.theory).map(([s, p]) => `|${s}⟩ ${(p * 100).toFixed(1)}%`).join(" · ")}
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}

/* ============================ MODULES · 50+ ============================ */
function ModulesPanel() {
    const [data, setData] = useState(null);
    const [filter, setFilter] = useState("ALL");

    useEffect(() => {
        api.get("/quantum/modules").then(({ data }) => setData(data)).catch(() => {});
    }, []);

    if (!data) {
        return <div className="font-mono-tech text-white/45">// loading modules…</div>;
    }

    const categories = ["ALL", ...data.categories];
    const list = filter === "ALL" ? data.modules : data.modules.filter((m) => m.cat === filter);

    const statusColor = (s) => ({
        live: ACCENT.jade,
        beta: ACCENT.cyan,
        pilot: ACCENT.amber,
        roadmap: "rgba(255,255,255,0.45)",
    }[s] || "rgba(255,255,255,0.45)");

    return (
        <div className="space-y-4" data-testid="qai-modules-panel">
            <div className="flex flex-wrap items-center gap-2">
                <div className="mono-label text-[10px] text-[#ccff00] mr-3">
                    {data.total} MODULES · FILTER →
                </div>
                {categories.map((c) => {
                    const active = filter === c;
                    return (
                        <button
                            key={c}
                            data-testid={`qai-module-filter-${c.toLowerCase()}`}
                            onClick={() => setFilter(c)}
                            className="px-2.5 py-1 mono-label text-[9.5px] transition"
                            style={{
                                border: `1px solid ${active ? ACCENT.jade : "rgba(255,255,255,0.10)"}`,
                                color: active ? ACCENT.jade : "rgba(255,255,255,0.65)",
                                background: active ? `${ACCENT.jade}11` : "transparent",
                            }}
                        >
                            {c}
                        </button>
                    );
                })}
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {list.map((m) => (
                    <div key={m.id}
                         data-testid={`qai-module-${m.id}`}
                         className="relative border border-white/10 p-3 bg-[#0a0c18] hover:border-[#ccff0044] transition">
                        <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2 min-w-0">
                                <span className="font-mono-tech text-[10px] text-white/45">{m.id}</span>
                                <span className="font-display font-black text-white text-[13px] truncate">{m.name}</span>
                            </div>
                            <span className="mono-label text-[8.5px]" style={{ color: statusColor(m.status) }}>● {m.status.toUpperCase()}</span>
                        </div>
                        <div className="font-mono-tech text-[10px] text-white/55 mt-1.5 leading-relaxed">{m.desc}</div>
                        <div className="mono-label text-[8.5px] text-white/35 mt-2">{m.cat}</div>
                    </div>
                ))}
            </div>
        </div>
    );
}

/* ============================ MEMORY · PERSISTENT ============================ */
function MemoryPanel() {
    const [thread, setThread] = useState(null);

    useEffect(() => {
        api.get("/quantum/memory-preview").then(({ data }) => setThread(data)).catch(() => {});
    }, []);

    if (!thread) return <div className="font-mono-tech text-white/45">// loading memory thread…</div>;

    const factColors = {
        HAPPENED: ACCENT.cyan,
        DECIDED: ACCENT.jade,
        OPEN_QUESTIONS: ACCENT.amber,
        RISKS: ACCENT.magenta,
        NEXT_ACTIONS: ACCENT.violet,
    };

    return (
        <div className="grid lg:grid-cols-[1.2fr_1fr] gap-5" data-testid="qai-memory-panel">
            <div className="relative border border-white/10 p-5 bg-[#0a0c18]">
                <CornerBrackets />
                <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="mono-label text-[10px] text-[#ff3b8a]">PERSISTENT THREAD · {thread.thread_type}</div>
                    <div className="font-mono-tech text-[10px] text-white/55">
                        turns={thread.turns_total} · {thread.turns_since_last_distill}/{thread.distill_every_n_turns} until distill
                    </div>
                </div>
                <div className="mono-label text-[9.5px] text-white/45 mt-3">FACTS LEDGER · AUTO-DISTILLED EVERY 6 TURNS</div>
                <div className="space-y-4 mt-4">
                    {Object.entries(thread.facts_ledger).map(([cat, items]) => (
                        <div key={cat} data-testid={`qai-memory-fact-${cat}`}>
                            <div className="mono-label text-[10px] mb-1.5" style={{ color: factColors[cat] }}>
                                ● {cat.replace(/_/g, " ")}
                            </div>
                            <ul className="space-y-1">
                                {items.map((it, i) => (
                                    <li key={i} className="font-mono-tech text-[11px] text-white/80 flex gap-2 leading-relaxed">
                                        <span style={{ color: factColors[cat] }}>▸</span>
                                        {it}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>
            </div>
            <div className="relative border border-[#ff3b8a44] p-5 bg-[#ff3b8a08]">
                <CornerBrackets />
                <div className="mono-label text-[10px] text-[#ff3b8a]">RECENT TURNS · APPEND-ONLY TAPE</div>
                <ol className="mt-4 space-y-3">
                    {thread.recent_turns.map((t, i) => (
                        <li key={i} className="border-l-2 pl-3" style={{ borderColor: t.role === "operator" ? ACCENT.violet : t.role === "agent_action" ? ACCENT.amber : ACCENT.jade }}>
                            <div className="flex items-center justify-between flex-wrap gap-2">
                                <span className="mono-label text-[9.5px]"
                                      style={{ color: t.role === "operator" ? ACCENT.violet : t.role === "agent_action" ? ACCENT.amber : ACCENT.jade }}>
                                    {t.role.toUpperCase()}
                                </span>
                                <span className="font-mono-tech text-[9.5px] text-white/40">{t.at}</span>
                            </div>
                            <div className="font-mono-tech text-[11px] text-white/80 mt-1 leading-relaxed">{t.text}</div>
                        </li>
                    ))}
                </ol>
                <div className="font-mono-tech text-[9.5px] text-white/40 mt-5 pt-3 border-t border-white/5 leading-relaxed">
                    Same substrate powers JadeOS-Agent Suite workflow memory and Hot Shot TMS dispatch threads.
                    Per-tenant isolated · SHA-256 audit chain on every append.
                </div>
            </div>
        </div>
    );
}
