/**
 * RiskGuardPanel — admin RISK GUARD tab.
 *
 * The "don't let the agent quote $800 on a $1200 load" UI.
 * Five sub-views:
 *   • Validate · live test bench (operator simulates a quote, sees the engine's verdict)
 *   • Floors    · CRUD per-lane manual floors
 *   • Reviews   · pending breach queue (approve/reject/override)
 *   • Alerts    · unread fires (banner counterpart lives in <App />)
 *   • Audit     · tamper-evident event chain + verify button
 */
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "./Brackets";
import { JadeWorking } from "./JadeAvatar";

const SEV_COLORS = {
    CLEAR: "#ccff00", LOW: "#ccff00", MEDIUM: "#ffce4f",
    HIGH: "#ff7e3b", CRITICAL: "#ff3b8a",
};
const DEC_COLORS = { AUTO_OK: "#ccff00", QUEUE_REVIEW: "#ffce4f", HARD_BLOCK: "#ff3b8a" };

function Stat({ k, v, c, sub }) {
    return (
        <div className="border px-4 py-3" style={{ borderColor: `${c}33`, background: `${c}08` }}>
            <div className="mono-label text-[10px]" style={{ color: c }}>{k}</div>
            <div className="font-display font-black text-2xl mt-1" style={{ color: c }}>{v}</div>
            {sub && <div className="font-mono-tech text-[10px] text-white/40 mt-1">{sub}</div>}
        </div>
    );
}

function ValidateBench() {
    const [form, setForm] = useState({
        proposed_rate_usd: 800, carrier_pay_usd: 900, fuel_surcharge_usd: 100,
        origin: "MSP", destination: "DFW", equipment: "R53", customer: "Acme Foods",
        load_id: "LD-DEMO-001", agent_rationale: "",
    });
    const [result, setResult] = useState(null);
    const [busy, setBusy] = useState(false);

    const f = (k, v) => setForm((s) => ({ ...s, [k]: v }));

    const run = async () => {
        setBusy(true);
        try {
            const body = { ...form };
            body.proposed_rate_usd = parseFloat(body.proposed_rate_usd);
            body.carrier_pay_usd = body.carrier_pay_usd === "" ? null : parseFloat(body.carrier_pay_usd);
            body.fuel_surcharge_usd = parseFloat(body.fuel_surcharge_usd || 0);
            const { data } = await api.post("/quotes/validate", body);
            setResult(data);
            const sev = data.severity;
            if (data.decision === "HARD_BLOCK") toast.error(`${sev} · HARD BLOCK · agent cannot send this quote`);
            else if (data.decision === "QUEUE_REVIEW") toast.warning(`${sev} · queued for human review`);
            else toast.success(`${sev} · AUTO OK`);
        } catch (e) {
            toast.error(e?.response?.data?.detail || "Validation failed.");
        } finally { setBusy(false); }
    };

    return (
        <div className="deck-card relative" data-testid="risk-validate-bench">
            <CornerBrackets />
            <div className="px-6 py-4 border-b border-white/10">
                <div className="mono-label text-[#ccff00]">VALIDATE · LIVE BENCH</div>
                <div className="font-mono-tech text-[10px] text-white/55 mt-1">
                    Simulate what the agent will see. Every call hits the same engine the agent does.
                </div>
            </div>
            <div className="grid lg:grid-cols-4 gap-3 p-5">
                {[
                    ["proposed_rate_usd", "PROPOSED $", "number"],
                    ["carrier_pay_usd", "CARRIER PAY $", "number"],
                    ["fuel_surcharge_usd", "FUEL $", "number"],
                    ["equipment", "EQUIPMENT", "text"],
                    ["origin", "ORIGIN", "text"],
                    ["destination", "DESTINATION", "text"],
                    ["customer", "CUSTOMER", "text"],
                    ["load_id", "LOAD ID", "text"],
                ].map(([k, label, type]) => (
                    <div key={k}>
                        <label className="mono-label text-[10px] text-white/55">{label}</label>
                        <input data-testid={`validate-${k}`} type={type} value={form[k]} onChange={(e) => f(k, e.target.value)} className="input-tech text-xs w-full mt-1" />
                    </div>
                ))}
                <div className="lg:col-span-4">
                    <label className="mono-label text-[10px] text-white/55">AGENT RATIONALE · OPTIONAL</label>
                    <input data-testid="validate-rationale" value={form.agent_rationale} onChange={(e) => f("agent_rationale", e.target.value)} className="input-tech text-xs w-full mt-1" />
                </div>
                <div className="lg:col-span-4">
                    <button data-testid="validate-run-btn" onClick={run} disabled={busy} className="btn-jade text-xs disabled:opacity-50 w-full">
                        {busy ? "VALIDATING…" : "▶ RUN VALIDATION"}
                    </button>
                </div>
            </div>
            {result && (
                <div className="border-t border-white/10 p-5 bg-[#06081a]" data-testid="validate-result">
                    <div className="grid sm:grid-cols-4 gap-3">
                        <Stat k="SEVERITY" v={result.severity} c={SEV_COLORS[result.severity] || "#ccff00"} />
                        <Stat k="DECISION" v={result.decision.replace(/_/g, " ")} c={DEC_COLORS[result.decision] || "#ccff00"} />
                        <Stat k="BREACH $" v={`$${(result.breach_amount_usd || 0).toLocaleString()}`} c="#ff3b8a" sub={`${result.breach_pct || 0}%`} />
                        <Stat k="FLOOR USED" v={`$${(result.floor_rate_usd || 0).toLocaleString()}`} c="#7c5cff" sub={(result.floor_source || "none").toUpperCase()} />
                    </div>
                    <div className="mt-3 font-mono-tech text-[11px] text-white/85 leading-relaxed">
                        <span className="text-[#00ffff]">▸ rationale</span> · {result.floor_rationale || "—"}
                    </div>
                    {(result.floor_candidates || []).length > 0 && (
                        <div className="mt-3 pt-3 border-t border-white/5">
                            <div className="mono-label text-[10px] text-white/55">FLOOR CANDIDATES · ALL SOURCES</div>
                            <div className="grid sm:grid-cols-3 gap-2 mt-2">
                                {result.floor_candidates.map((c, i) => (
                                    <div key={i} className="border border-white/10 p-2">
                                        <div className="mono-label text-[9px] text-[#00ffff]">{c.source.toUpperCase()}</div>
                                        <div className="font-display font-bold text-sm text-white">${(c.floor_rate_usd || 0).toLocaleString()}</div>
                                        <div className="font-mono-tech text-[10px] text-white/55 leading-snug">{c.rationale}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

function FloorsTable({ floors, onChange }) {
    const [form, setForm] = useState({ origin: "", destination: "", equipment: "V53", floor_rate_usd: "", cost_basis_usd: "", rationale: "" });
    const [busy, setBusy] = useState(false);
    const create = async (e) => {
        e.preventDefault();
        if (!form.floor_rate_usd) return;
        setBusy(true);
        try {
            await api.post("/rate-floors", {
                ...form, floor_rate_usd: parseFloat(form.floor_rate_usd),
                cost_basis_usd: form.cost_basis_usd ? parseFloat(form.cost_basis_usd) : null,
            });
            toast.success("Floor added.");
            setForm({ origin: "", destination: "", equipment: "V53", floor_rate_usd: "", cost_basis_usd: "", rationale: "" });
            onChange();
        } catch (e) { toast.error(e?.response?.data?.detail || "Create failed."); }
        finally { setBusy(false); }
    };
    const del = async (id) => {
        if (!confirm("Delete floor?")) return;
        try { await api.delete(`/rate-floors/${id}`); toast.success("Deleted."); onChange(); }
        catch { toast.error("Delete failed."); }
    };
    return (
        <div className="deck-card relative" data-testid="floors-table">
            <CornerBrackets />
            <div className="px-6 py-4 border-b border-white/10 mono-label text-[#7c5cff]">RATE FLOORS · PER LANE</div>
            <form onSubmit={create} className="grid lg:grid-cols-7 gap-2 items-end p-4 border-b border-white/10 bg-[#06081a]" data-testid="floors-new-form">
                <input data-testid="floor-origin" placeholder="ORIGIN" value={form.origin} onChange={(e) => setForm({ ...form, origin: e.target.value })} className="input-tech text-xs" required />
                <input data-testid="floor-destination" placeholder="DEST" value={form.destination} onChange={(e) => setForm({ ...form, destination: e.target.value })} className="input-tech text-xs" required />
                <input data-testid="floor-equipment" placeholder="EQUIP" value={form.equipment} onChange={(e) => setForm({ ...form, equipment: e.target.value })} className="input-tech text-xs" />
                <input data-testid="floor-rate" type="number" step="0.01" placeholder="FLOOR $" value={form.floor_rate_usd} onChange={(e) => setForm({ ...form, floor_rate_usd: e.target.value })} className="input-tech text-xs" required />
                <input data-testid="floor-cost" type="number" step="0.01" placeholder="COST BASIS $" value={form.cost_basis_usd} onChange={(e) => setForm({ ...form, cost_basis_usd: e.target.value })} className="input-tech text-xs" />
                <input data-testid="floor-rationale" placeholder="rationale (optional)" value={form.rationale} onChange={(e) => setForm({ ...form, rationale: e.target.value })} className="input-tech text-xs lg:col-span-1" />
                <button data-testid="floor-create-btn" disabled={busy} className="btn-jade text-xs disabled:opacity-50">+ ADD</button>
            </form>
            {floors.length === 0 ? (
                <div className="px-6 py-8 text-center font-mono-tech text-xs text-white/40">// no floors yet · the agent has no protection on any lane until you add at least one //</div>
            ) : (
                <div className="divide-y divide-white/5">
                    {floors.map((f) => (
                        <div key={f.id} className="px-6 py-3 grid grid-cols-[180px_100px_120px_120px_1fr_60px] gap-3 items-center" data-testid={`floor-row-${f.id}`}>
                            <span className="font-mono-tech text-[11px] text-white/85">{f.lane_key}</span>
                            <span className="mono-label text-[10px] text-[#00ffff]">{f.equipment}</span>
                            <span className="font-display font-bold text-[#ccff00]">${(f.floor_rate_usd || 0).toLocaleString()}</span>
                            <span className="font-mono-tech text-[10.5px] text-[#ff3b8a]">{f.cost_basis_usd ? `cost $${f.cost_basis_usd.toLocaleString()}` : "—"}</span>
                            <span className="font-mono-tech text-[10px] text-white/55 truncate">{f.rationale || "—"}</span>
                            <button onClick={() => del(f.id)} className="mono-label text-[10px] text-white/40 hover:text-[#ff3b8a] text-right">✕</button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function ReviewsQueue({ reviews, onChange }) {
    const decide = async (id, action, notes) => {
        try {
            await api.post(`/quote-reviews/${id}/${action}`, null, { params: notes ? { notes } : {} });
            toast.success(action.toUpperCase());
            onChange();
        } catch (e) {
            toast.error(e?.response?.data?.detail || `${action} failed`);
        }
    };
    return (
        <div className="deck-card relative" data-testid="reviews-queue">
            <CornerBrackets />
            <div className="px-6 py-4 border-b border-white/10 mono-label text-[#ff3b8a]">REVIEW QUEUE · BREACHES</div>
            {reviews.length === 0 ? (
                <div className="px-6 py-8 text-center font-mono-tech text-xs text-white/40">// queue clean · no breaches awaiting review //</div>
            ) : (
                <div className="divide-y divide-white/5">
                    {reviews.map((r) => {
                        const isBlock = r.decision === "HARD_BLOCK";
                        return (
                            <div key={r.id} className="px-6 py-4 grid lg:grid-cols-[110px_1fr_130px_130px_220px] gap-3 items-center" data-testid={`review-row-${r.id}`}>
                                <span className="mono-label text-[11px]" style={{ color: SEV_COLORS[r.severity] }}>● {r.severity}</span>
                                <div>
                                    <div className="font-display font-bold text-white text-sm">{r.customer || "—"} · {r.lane_key}</div>
                                    <div className="font-mono-tech text-[10px] text-white/55 mt-0.5">
                                        proposed <span className="text-[#ccff00]">${(r.proposed_rate_usd || 0).toLocaleString()}</span> · floor <span className="text-[#7c5cff]">${(r.floor_rate_usd || 0).toLocaleString()}</span> · src {r.floor_source}
                                    </div>
                                    {r.agent_rationale && <div className="font-mono-tech text-[10px] text-[#00ffff] mt-0.5 truncate">agent · {r.agent_rationale}</div>}
                                </div>
                                <div>
                                    <span className="mono-label text-[10px]" style={{ color: DEC_COLORS[r.decision] }}>{r.decision.replace(/_/g, " ")}</span>
                                    <div className="font-mono-tech text-[10px] text-white/40 mt-0.5">{r.status}</div>
                                </div>
                                <span className="font-display font-bold text-[#ff3b8a]">
                                    ${(r.breach_amount_usd || 0).toLocaleString()}<span className="text-[10px] text-white/40 ml-1">{r.breach_pct}%</span>
                                </span>
                                <div className="flex flex-wrap gap-1 justify-end">
                                    {isBlock && r.status === "pending" && (
                                        <button data-testid={`review-override-${r.id}`} onClick={() => {
                                            const reason = prompt("OVERRIDE REQUIRES WRITTEN REASON · what changed to make this rate acceptable?");
                                            if (reason && reason.trim()) decide(r.id, "override", reason.trim());
                                        }} className="btn-jade text-[10px] px-2" style={{ background: "#ff3b8a", color: "#0a0c18" }}>OVERRIDE BLOCK</button>
                                    )}
                                    {!isBlock && r.status === "pending" && (
                                        <button data-testid={`review-approve-${r.id}`} onClick={() => decide(r.id, "approve", prompt("Notes (optional)") || "")} className="btn-jade text-[10px] px-2">APPROVE</button>
                                    )}
                                    {r.status === "pending" && (
                                        <button data-testid={`review-reject-${r.id}`} onClick={() => decide(r.id, "reject", prompt("Why rejected?") || "")} className="btn-ghost text-[10px] px-2">REJECT</button>
                                    )}
                                    {r.status !== "pending" && (
                                        <span className="font-mono-tech text-[10px] text-white/40">by {r.reviewer || "—"}</span>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

function AuditTimeline({ events, onVerify, verifyResult }) {
    return (
        <div className="deck-card relative" data-testid="audit-timeline">
            <CornerBrackets />
            <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between flex-wrap gap-2">
                <div>
                    <div className="mono-label text-[#00ffff]">AUDIT · IMMUTABLE CHAIN</div>
                    <div className="font-mono-tech text-[10px] text-white/55 mt-1">SHA-256 hash chain · every event linked to the prior · tamper-evident</div>
                </div>
                <button data-testid="audit-verify-btn" onClick={onVerify} className="btn-jade text-xs">VERIFY CHAIN</button>
            </div>
            {verifyResult && (
                <div className="px-6 py-3 border-b border-white/10 font-mono-tech text-[11px]"
                     style={{ color: verifyResult.ok ? "#ccff00" : "#ff3b8a", background: verifyResult.ok ? "#ccff0008" : "#ff3b8a08" }}>
                    {verifyResult.ok ? `✓ chain intact · ${verifyResult.checked} events verified` : `✗ chain broken at event ${verifyResult.first_break}`}
                </div>
            )}
            <div className="divide-y divide-white/5 max-h-[420px] overflow-y-auto">
                {events.length === 0 ? (
                    <div className="px-6 py-8 text-center font-mono-tech text-xs text-white/40">// no events yet //</div>
                ) : events.map((e) => (
                    <div key={e.id} className="px-6 py-3 grid grid-cols-[60px_120px_160px_1fr_180px] gap-3 items-start" data-testid={`audit-row-${e.id}`}>
                        <span className="font-mono-tech text-[10px] text-white/40">#{e.seq}</span>
                        <span className="mono-label text-[10px] text-[#7c5cff]">{e.actor}</span>
                        <span className="mono-label text-[10px] text-[#00ffff]">{e.action}</span>
                        <span className="font-mono-tech text-[10.5px] text-white/85 truncate">
                            {e.target_type}/{(e.target_id || "").slice(0, 8)} · {Object.entries(e.metadata || {}).slice(0, 3).map(([k, v]) => `${k}=${typeof v === "object" ? JSON.stringify(v).slice(0, 24) : v}`).join(" · ")}
                        </span>
                        <span className="font-mono-tech text-[10px] text-white/35 text-right">{new Date(e.created_at).toLocaleString()}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default function RiskGuardPanel() {
    const [floors, setFloors] = useState([]);
    const [reviews, setReviews] = useState({ reviews: [], pending: 0, hard_blocks: 0 });
    const [audit, setAudit] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [verifyResult, setVerifyResult] = useState(null);
    const [loading, setLoading] = useState(true);
    const [view, setView] = useState("validate");

    const load = async () => {
        try {
            const [f, r, a, al] = await Promise.all([
                api.get("/rate-floors"),
                api.get("/quote-reviews"),
                api.get("/audit/events", { params: { limit: 100 } }),
                api.get("/alerts/unread", { params: { limit: 50 } }),
            ]);
            setFloors(f.data.floors || []);
            setReviews(r.data);
            setAudit(a.data.events || []);
            setAlerts(al.data.alerts || []);
        } catch { toast.error("Risk Guard load failed."); }
        finally { setLoading(false); }
    };

    useEffect(() => { setLoading(true); load(); }, []);

    const verify = async () => {
        try {
            const { data } = await api.get("/audit/verify", { params: { limit: 1000 } });
            setVerifyResult(data);
            if (data.ok) toast.success(`Chain intact · ${data.checked} events`);
            else toast.error("Chain broken — investigate immediately");
        } catch { toast.error("Verify failed."); }
    };

    const ackAll = async () => {
        try { await api.post("/alerts/ack-all"); toast.success("All alerts cleared"); load(); }
        catch { toast.error("Ack failed."); }
    };

    if (loading) return <div className="deck-card p-12 flex justify-center"><JadeWorking verb="loading risk guard" size={72} /></div>;

    const VIEWS = [
        { id: "validate", label: "VALIDATE · BENCH", c: "#ccff00" },
        { id: "reviews", label: `REVIEWS · ${reviews.pending}`, c: "#ff3b8a" },
        { id: "floors", label: `FLOORS · ${floors.length}`, c: "#7c5cff" },
        { id: "alerts", label: `ALERTS · ${alerts.length}`, c: "#ffce4f" },
        { id: "audit", label: "AUDIT · CHAIN", c: "#00ffff" },
    ];

    return (
        <div className="space-y-6" data-testid="risk-guard-panel">
            <div className="deck-card p-6 relative">
                <CornerBrackets />
                <SectionLabel idx={0} color="#ff3b8a">RISK GUARD · PRE-QUOTE</SectionLabel>
                <h2 className="font-display font-black text-white text-4xl tracking-tighter mt-2">
                    Catch the $400 loss <span className="accent-pink">before</span> it ships.
                </h2>
                <p className="text-white/65 text-sm mt-3 max-w-2xl leading-relaxed">
                    Every agent quote runs through a layered floor engine (manual + formula + historical). CRITICAL breaches HARD-BLOCK.
                    MEDIUM/HIGH route to your review queue. Every decision lands in the tamper-evident audit chain — the same chain you can hand to underwriters or counsel.
                </p>
                <div className="grid sm:grid-cols-5 gap-3 mt-5">
                    <Stat k="FLOORS" v={floors.length} c="#7c5cff" sub="lanes covered" />
                    <Stat k="PENDING" v={reviews.pending} c="#ffce4f" sub="awaiting human" />
                    <Stat k="HARD BLOCKS" v={reviews.hard_blocks} c="#ff3b8a" sub="not sendable" />
                    <Stat k="UNREAD ALERTS" v={alerts.length} c="#ff3b8a" />
                    <Stat k="AUDIT EVENTS" v={audit.length} c="#00ffff" sub="last 100" />
                </div>
            </div>

            <div className="flex flex-wrap gap-2">
                {VIEWS.map((v) => {
                    const active = view === v.id;
                    return (
                        <button key={v.id} data-testid={`risk-view-${v.id}`} onClick={() => setView(v.id)}
                            className="px-4 py-2 mono-label text-[11px] transition"
                            style={{
                                border: `1px solid ${active ? v.c : "rgba(255,255,255,0.10)"}`,
                                color: active ? v.c : "rgba(255,255,255,0.55)",
                                background: active ? `${v.c}11` : "transparent",
                            }}>{v.label}</button>
                    );
                })}
            </div>

            {view === "validate" && <ValidateBench />}
            {view === "floors" && <FloorsTable floors={floors} onChange={load} />}
            {view === "reviews" && <ReviewsQueue reviews={reviews.reviews} onChange={load} />}
            {view === "alerts" && (
                <div className="deck-card relative" data-testid="alerts-list">
                    <CornerBrackets />
                    <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                        <div className="mono-label text-[#ff3b8a]">UNREAD ALERTS</div>
                        {alerts.length > 0 && <button data-testid="alerts-ack-all" onClick={ackAll} className="btn-ghost text-[10px]">ACK ALL</button>}
                    </div>
                    {alerts.length === 0 ? (
                        <div className="px-6 py-8 text-center font-mono-tech text-xs text-white/40">// queue clean · no live alerts //</div>
                    ) : (
                        <div className="divide-y divide-white/5">
                            {alerts.map((a) => (
                                <div key={a.id} className="px-6 py-3 grid grid-cols-[80px_1fr_180px] gap-3 items-start">
                                    <span className="mono-label text-[10px]" style={{ color: a.severity === "page" ? "#ff3b8a" : a.severity === "high" ? "#ff7e3b" : "#ffce4f" }}>{a.severity.toUpperCase()}</span>
                                    <div>
                                        <div className="font-display font-bold text-white text-sm">{a.title}</div>
                                        <div className="font-mono-tech text-[10.5px] text-white/85 mt-0.5 whitespace-pre-line">{a.body}</div>
                                    </div>
                                    <span className="font-mono-tech text-[10px] text-white/35 text-right">{new Date(a.created_at).toLocaleString()}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
            {view === "audit" && <AuditTimeline events={audit} onVerify={verify} verifyResult={verifyResult} />}
        </div>
    );
}
