/**
 * HealthPanel — admin HEALTH · DIAGNOSTICS tab.
 *
 * Real-time readout of every external dep (LLM key budget, Mongo, Twilio,
 * Stripe, Resend), Mongo health, recent LLM errors, security posture,
 * disk usage, and one-click self-repair actions.
 *
 * Endpoints used:
 *   GET    /api/admin/system-health
 *   GET    /api/admin/llm-errors
 *   POST   /api/admin/llm-probe
 *   DELETE /api/admin/llm-errors
 *   POST   /api/admin/repair/retry-followups
 *   POST   /api/admin/repair/clear-stale-runs
 */
import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { CornerBrackets } from "./Brackets";
import { JadeWorking } from "./JadeAvatar";

const OVERALL_COLORS = {
    healthy: "#ccff00",
    warn: "#ffce4f",
    degraded: "#ff3b8a",
};

function StatusPill({ status }) {
    const color = OVERALL_COLORS[status] || "#7c5cff";
    return (
        <span
            data-testid={`health-overall-${status}`}
            className="mono-label inline-flex items-center gap-2 px-3 py-1.5 border"
            style={{ color, borderColor: `${color}66`, background: `${color}11` }}
        >
            <span className="inline-block w-2 h-2 rounded-full" style={{ background: color, boxShadow: `0 0 10px ${color}` }} />
            SYSTEM · {status?.toUpperCase() || "UNKNOWN"}
        </span>
    );
}

function ServiceRow({ id, svc }) {
    const ok = svc.configured;
    const color = ok ? "#ccff00" : (svc.required ? "#ff3b8a" : "#ffce4f");
    return (
        <div
            data-testid={`health-service-${id}`}
            className="grid grid-cols-[140px_120px_1fr] gap-4 items-center px-4 py-3 border-b border-white/5"
        >
            <span className="mono-label" style={{ color }}>{svc.label}</span>
            <span className="mono-label text-[10px]" style={{ color }}>
                {ok ? "● CONFIGURED" : (svc.required ? "● MISSING · REQUIRED" : "○ MISSING · OPTIONAL")}
            </span>
            <span className="font-mono-tech text-[11px] text-white/55 leading-relaxed">{svc.purpose || "—"}</span>
        </div>
    );
}

function BudgetMeter({ current, max }) {
    if (typeof current !== "number" || typeof max !== "number" || max <= 0) return null;
    const pct = Math.min(100, (current / max) * 100);
    const color = pct >= 100 ? "#ff3b8a" : pct >= 80 ? "#ffce4f" : "#ccff00";
    return (
        <div data-testid="health-budget-meter" className="mt-3">
            <div className="flex items-baseline justify-between mb-1">
                <span className="mono-label text-white/55">UNIVERSAL KEY · COST / CAP</span>
                <span className="font-mono-tech text-xs" style={{ color }}>
                    ${current.toFixed(2)} / ${max.toFixed(2)} ({pct.toFixed(1)}%)
                </span>
            </div>
            <div className="h-2 bg-white/10 overflow-hidden">
                <div
                    className="h-full transition-all duration-700"
                    style={{ width: `${pct}%`, background: color, boxShadow: `0 0 10px ${color}` }}
                />
            </div>
            {pct >= 100 && (
                <div className="mt-2 font-mono-tech text-[11px] text-[#ff3b8a]" data-testid="health-budget-exceeded">
                    → Top up at Profile → Universal Key → Add Balance
                </div>
            )}
        </div>
    );
}

function Section({ title, color, children, testid }) {
    return (
        <div className="deck-card relative" data-testid={testid}>
            <CornerBrackets />
            <div className="px-6 py-4 border-b border-white/10 mono-label" style={{ color }}>{title}</div>
            <div>{children}</div>
        </div>
    );
}

export default function HealthPanel() {
    const [data, setData] = useState(null);
    const [errors, setErrors] = useState(null);
    const [loading, setLoading] = useState(true);
    const [probing, setProbing] = useState(false);
    const [probeResult, setProbeResult] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const [h, e] = await Promise.all([
                api.get("/admin/system-health"),
                api.get("/admin/llm-errors", { params: { limit: 50 } }),
            ]);
            setData(h.data);
            setErrors(e.data);
        } catch (err) {
            toast.error("Failed to load system health");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);
    useEffect(() => {
        const id = setInterval(load, 30000);  // auto-refresh every 30s
        return () => clearInterval(id);
    }, [load]);

    const probe = async () => {
        setProbing(true); setProbeResult(null);
        try {
            const { data } = await api.post("/admin/llm-probe");
            setProbeResult(data);
            if (data.status === "healthy") toast.success(`LLM healthy · ${data.latency_ms}ms`);
            else toast.error(data.message || "LLM degraded");
            load();
        } catch (err) {
            toast.error("Probe failed");
        } finally { setProbing(false); }
    };

    const clearErrors = async () => {
        if (!confirm("Clear all logged LLM errors?")) return;
        try {
            const { data } = await api.delete("/admin/llm-errors");
            toast.success(`Cleared ${data.deleted} errors`);
            load();
        } catch { toast.error("Clear failed"); }
    };

    const retryFollowups = async () => {
        try {
            const { data } = await api.post("/admin/repair/retry-followups");
            toast.success(`Re-queued ${data.queued_for_send} followups`);
            load();
        } catch { toast.error("Repair failed"); }
    };

    const clearStaleRuns = async () => {
        if (!confirm("Delete agent runs older than 30 days?")) return;
        try {
            const { data } = await api.post("/admin/repair/clear-stale-runs", null, { params: { days: 30 } });
            toast.success(`Purged ${data.deleted} stale runs`);
            load();
        } catch { toast.error("Repair failed"); }
    };

    if (loading && !data) {
        return (
            <div className="deck-card p-12 flex justify-center"><JadeWorking verb="checking system health" size={72} /></div>
        );
    }
    if (!data) return null;

    const last = data?.llm?.last_error;

    return (
        <div className="space-y-6" data-testid="health-panel">
            {/* TOP STRIP — overall status + actions */}
            <div className="deck-card p-6 relative" data-testid="health-overall-card">
                <CornerBrackets />
                <div className="flex items-start justify-between flex-wrap gap-4">
                    <div>
                        <div className="mono-label text-white/55 mb-2">JADE OS · OPERATIONAL READOUT</div>
                        <div className="flex items-center gap-3 flex-wrap">
                            <StatusPill status={data.overall} />
                            <span className="font-mono-tech text-[11px] text-white/45">
                                checked {new Date(data.checked_at).toLocaleTimeString()}
                            </span>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                        <button
                            data-testid="health-refresh-btn"
                            onClick={load}
                            className="btn-ghost text-xs px-4"
                        >↻ REFRESH</button>
                        <button
                            data-testid="health-probe-btn"
                            onClick={probe}
                            disabled={probing}
                            className="btn-jade text-xs px-4 inline-flex items-center gap-2"
                        >
                            {probing ? "PROBING…" : "▶ PROBE LLM NOW"}
                        </button>
                    </div>
                </div>

                {data.needs_action?.length > 0 && (
                    <div className="mt-5" data-testid="health-needs">
                        <div className="mono-label text-[#ff3b8a] mb-2">ACTION REQUIRED · {data.needs_action.length}</div>
                        <ul className="space-y-1.5">
                            {data.needs_action.map((n, i) => (
                                <li key={i} className="font-mono-tech text-xs text-white/85 leading-relaxed flex gap-2">
                                    <span className="text-[#ff3b8a]">▸</span>{n}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {probeResult && (
                    <div
                        data-testid="health-probe-result"
                        className="mt-5 p-4 border"
                        style={{
                            borderColor: probeResult.status === "healthy" ? "#ccff00" : "#ff3b8a",
                            background: probeResult.status === "healthy" ? "#ccff0011" : "#ff3b8a11",
                        }}
                    >
                        <div className="mono-label mb-1" style={{ color: probeResult.status === "healthy" ? "#ccff00" : "#ff3b8a" }}>
                            LIVE PROBE · {probeResult.status?.toUpperCase()}
                        </div>
                        <div className="font-mono-tech text-xs text-white/85">
                            {probeResult.status === "healthy"
                                ? <>round-trip {probeResult.latency_ms}ms · model {probeResult.model} · reply "{probeResult.reply}"</>
                                : <>{probeResult.message || probeResult.code}</>}
                        </div>
                    </div>
                )}
            </div>

            {/* LLM PANEL — budget meter + last error */}
            <Section title={`LLM · UNIVERSAL KEY · ${data.llm.status?.toUpperCase()}`} color="#7c5cff" testid="health-llm-section">
                <div className="p-6 space-y-3">
                    <div className="grid sm:grid-cols-3 gap-4">
                        <div className="border border-white/10 px-4 py-3">
                            <div className="mono-label text-[10px] text-white/40">ERRORS · 24H</div>
                            <div className="font-display font-black text-3xl" style={{ color: data.llm.errors_24h > 0 ? "#ff3b8a" : "#ccff00" }}>{data.llm.errors_24h}</div>
                        </div>
                        <div className="border border-white/10 px-4 py-3">
                            <div className="mono-label text-[10px] text-white/40">CONFIGURED</div>
                            <div className="font-display font-black text-2xl mt-1" style={{ color: data.services.llm.configured ? "#ccff00" : "#ff3b8a" }}>
                                {data.services.llm.configured ? "YES" : "NO · CRITICAL"}
                            </div>
                        </div>
                        <div className="border border-white/10 px-4 py-3">
                            <div className="mono-label text-[10px] text-white/40">LAST ERROR CODE</div>
                            <div className="font-mono-tech text-[#ff3b8a] mt-2 text-sm">{last?.code || "—"}</div>
                        </div>
                    </div>
                    {last && (last.current_cost != null) && (
                        <BudgetMeter current={last.current_cost} max={last.max_budget} />
                    )}
                    {last && (
                        <div className="mt-3 p-3 bg-[#02030a] border border-[#ff3b8a]/30">
                            <div className="mono-label text-[#ff3b8a] text-[10px] mb-1">MOST RECENT LLM ERROR · {new Date(last.created_at).toLocaleString()}</div>
                            <div className="font-mono-tech text-xs text-white/85">{last.message}</div>
                            {last.raw && <div className="font-mono-tech text-[10px] text-white/45 mt-2 break-all">{last.raw}</div>}
                        </div>
                    )}
                </div>
            </Section>

            {/* SERVICES MATRIX */}
            <Section title="SERVICES · CONFIGURATION MATRIX" color="#00ffff" testid="health-services-section">
                <div>
                    {Object.entries(data.services).map(([id, svc]) => <ServiceRow key={id} id={id} svc={svc} />)}
                </div>
            </Section>

            {/* SECURITY POSTURE */}
            <Section title="SECURITY POSTURE" color="#ff3b8a" testid="health-security-section">
                <div className="grid sm:grid-cols-2 gap-0 divide-y sm:divide-y-0 divide-white/5">
                    {Object.entries(data.security).map(([k, v]) => (
                        <div key={k} className="px-4 py-3 flex items-center justify-between sm:border-b sm:border-white/5">
                            <span className="font-mono-tech text-xs text-white/75">{k.replace(/_/g, " ")}</span>
                            <span className="mono-label" style={{ color: v === true ? "#ccff00" : v === false ? "#ff3b8a" : "#ffce4f" }}>
                                {v === true ? "● ENFORCED" : v === false ? "○ OFF" : "◐ PARTIAL"}
                            </span>
                        </div>
                    ))}
                </div>
            </Section>

            {/* SYSTEM */}
            <div className="grid lg:grid-cols-2 gap-6">
                <Section title="MONGO · DATABASE" color="#ccff00" testid="health-mongo-section">
                    <div className="p-6">
                        <div className="flex items-center gap-3">
                            <span className="mono-label" style={{ color: data.mongo.ok ? "#ccff00" : "#ff3b8a" }}>
                                {data.mongo.ok ? "● ONLINE · PINGABLE" : "● OFFLINE"}
                            </span>
                        </div>
                        <div className="grid grid-cols-3 gap-3 mt-4">
                            <div className="border border-white/10 p-3"><div className="mono-label text-[10px] text-white/40">LEADS</div><div className="font-display font-bold text-xl text-white">{data.counts.leads}</div></div>
                            <div className="border border-white/10 p-3"><div className="mono-label text-[10px] text-white/40">RUNS</div><div className="font-display font-bold text-xl text-white">{data.counts.runs}</div></div>
                            <div className="border border-white/10 p-3"><div className="mono-label text-[10px] text-white/40">LIGHTHOUSE</div><div className="font-display font-bold text-xl text-white">{data.counts.lighthouse}</div></div>
                        </div>
                    </div>
                </Section>

                <Section title="DISK · STORAGE" color="#7c5cff" testid="health-disk-section">
                    <div className="p-6">
                        {data.disk ? (
                            <>
                                <div className="flex items-baseline justify-between mb-2">
                                    <span className="mono-label text-white/55">USED / TOTAL</span>
                                    <span className="font-mono-tech text-sm text-white">{data.disk.used_gb} GB / {data.disk.total_gb} GB</span>
                                </div>
                                <div className="h-2 bg-white/10 overflow-hidden">
                                    <div className="h-full transition-all duration-700"
                                         style={{ width: `${data.disk.pct_used}%`, background: data.disk.pct_used > 80 ? "#ff3b8a" : "#7c5cff" }} />
                                </div>
                                <div className="font-mono-tech text-[11px] text-white/55 mt-2">{data.disk.free_gb} GB free</div>
                            </>
                        ) : <div className="font-mono-tech text-xs text-white/40">// disk metrics unavailable</div>}
                    </div>
                </Section>
            </div>

            {/* AUTO-FOLLOWUP QUEUE */}
            <Section title="AUTO-FOLLOWUP QUEUE" color="#ffce4f" testid="health-followups-section">
                <div className="p-6 grid sm:grid-cols-3 gap-4">
                    <div className="border border-white/10 p-3"><div className="mono-label text-[10px] text-white/40">QUEUED</div><div className="font-display font-bold text-2xl text-[#ffce4f]">{data.auto_followups.queued}</div></div>
                    <div className="border border-white/10 p-3"><div className="mono-label text-[10px] text-white/40">FAILED</div><div className="font-display font-bold text-2xl text-[#ff3b8a]">{data.auto_followups.failed}</div></div>
                    <button data-testid="health-retry-followups-btn" onClick={retryFollowups} className="btn-ghost text-xs">↻ RETRY QUEUED + FAILED</button>
                </div>
            </Section>

            {/* RECENT LLM ERRORS STREAM */}
            <Section title={`LLM ERROR STREAM · LAST ${errors?.errors?.length || 0}`} color="#ff3b8a" testid="health-errors-section">
                <div>
                    <div className="px-6 py-3 border-b border-white/5 flex items-center justify-between flex-wrap gap-2">
                        <div className="flex flex-wrap gap-3">
                            {errors && Object.entries(errors.by_code || {}).map(([code, n]) => (
                                <span key={code} className="mono-label text-[10px] text-white/65" data-testid={`error-bucket-${code}`}>
                                    {code} · <span className="text-[#ff3b8a]">{n}</span>
                                </span>
                            ))}
                            {(!errors?.errors || errors.errors.length === 0) && (
                                <span className="font-mono-tech text-xs text-[#ccff00]">// no errors recorded</span>
                            )}
                        </div>
                        {errors?.errors?.length > 0 && (
                            <button data-testid="health-clear-errors-btn" onClick={clearErrors} className="mono-label text-[10px] text-white/55 hover:text-[#ff3b8a]">✕ CLEAR ALL</button>
                        )}
                    </div>
                    <div className="divide-y divide-white/5 max-h-[400px] overflow-y-auto">
                        {errors?.errors?.map((e, i) => (
                            <div key={i} className="px-6 py-3 grid grid-cols-[120px_160px_1fr] gap-3 items-center">
                                <span className="font-mono-tech text-[10px] text-white/45">{new Date(e.created_at).toLocaleTimeString()}</span>
                                <span className="mono-label text-[#ff3b8a]">{e.code}</span>
                                <span className="font-mono-tech text-[11px] text-white/75 truncate" title={e.message}>{e.message}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </Section>

            {/* REPAIR */}
            <Section title="SELF-REPAIR · OPS" color="#00ffff" testid="health-repair-section">
                <div className="p-6 flex flex-wrap gap-3">
                    <button data-testid="repair-clear-stale-btn" onClick={clearStaleRuns} className="btn-ghost text-xs">↻ PURGE STALE RUNS · 30D+</button>
                    <button data-testid="repair-retry-followups-btn" onClick={retryFollowups} className="btn-ghost text-xs">↻ RETRY FOLLOWUPS</button>
                    <button data-testid="repair-clear-errors-btn" onClick={clearErrors} className="btn-ghost text-xs">✕ CLEAR LLM ERROR LOG</button>
                </div>
            </Section>
        </div>
    );
}
