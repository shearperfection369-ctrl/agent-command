/**
 * OperationsPanel — admin OPERATIONS · LIGHTHOUSE PROGRAM tab.
 *
 * The 5-client lighthouse plan as operating tooling:
 *   • Team roster + monthly burn
 *   • Infra costs
 *   • SLA tiers (P1/P2/P3) + live ticket queue
 *   • 5-phase onboarding playbook
 *   • Roadmap prioritization matrix
 *   • Year-1 financial model
 *   • 12-month milestones
 */
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "./Brackets";
import { JadeWorking } from "./JadeAvatar";

const PRIORITY_COLOR = { P1: "#ff3b8a", P2: "#ffce4f", P3: "#7c5cff" };

function Stat({ k, v, c }) {
    return (
        <div className="border px-4 py-3" style={{ borderColor: `${c}33`, background: `${c}08` }}>
            <div className="mono-label text-[10px]" style={{ color: c }}>{k}</div>
            <div className="font-display font-black text-2xl mt-1" style={{ color: c }}>{v}</div>
        </div>
    );
}

function TeamCard({ t }) {
    return (
        <div className="deck-card relative p-4" data-testid={`team-${t.id}`}>
            <CornerBrackets />
            <div className="flex items-baseline justify-between flex-wrap gap-2">
                <div>
                    <div className="font-display font-bold text-white text-base">{t.role}</div>
                    <div className="font-mono-tech text-[10px] text-white/55 mt-0.5">{t.name_or_status}</div>
                </div>
                <span className="mono-label text-[10px] text-[#ccff00]">{t.fte} FTE · {t.weekly_hours}h/wk</span>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-3">
                <div className="border border-white/10 p-2">
                    <div className="mono-label text-[9px] text-white/40">CONTRACTOR</div>
                    <div className="font-display font-bold text-sm" style={{ color: "#7c5cff" }}>${(t.monthly_cost / 1000).toFixed(1)}k/mo</div>
                </div>
                <div className="border border-white/10 p-2">
                    <div className="mono-label text-[9px] text-white/40">FTE</div>
                    <div className="font-display font-bold text-sm" style={{ color: "#00ffff" }}>${((t.monthly_cost_fte || t.monthly_cost) / 1000).toFixed(1)}k/mo</div>
                </div>
            </div>
            <ul className="space-y-1 mt-3">
                {t.responsibilities.map((r, i) => (
                    <li key={i} className="font-mono-tech text-[10px] text-white/65 flex gap-1.5 leading-snug"><span className="text-[#ccff00]">▸</span>{r}</li>
                ))}
            </ul>
            {t.criticality && (
                <div className="mt-3 pt-2 border-t border-white/5 font-mono-tech text-[10px] text-[#ffce4f] leading-snug">⚠ {t.criticality}</div>
            )}
            <div className="mt-2 mono-label text-[9px] text-white/45">STATUS · {t.status?.toUpperCase().replace(/_/g, " ")}</div>
        </div>
    );
}

function SlaCard({ t }) {
    return (
        <div className="deck-card relative p-5" style={{ borderColor: `${t.color}55` }} data-testid={`sla-${t.priority}`}>
            <CornerBrackets />
            <div className="flex items-baseline justify-between mb-2">
                <div className="font-display font-black text-2xl" style={{ color: t.color }}>{t.label}</div>
            </div>
            <p className="font-mono-tech text-[11px] text-white/85 leading-relaxed">{t.definition}</p>
            <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-white/5">
                <div><div className="mono-label text-[9px] text-white/40">RESPONSE</div><div className="font-display font-bold text-base mt-0.5" style={{ color: t.color }}>{t.response_target_hours}h</div></div>
                <div><div className="mono-label text-[9px] text-white/40">FIX TARGET</div><div className="font-display font-bold text-base mt-0.5" style={{ color: t.color }}>{typeof t.fix_target_hours === "number" ? `${t.fix_target_hours}h` : t.fix_target_hours}</div></div>
            </div>
            <div className="mt-3">
                <div className="mono-label text-[9px] text-white/40 mb-1">EXAMPLES</div>
                <ul className="space-y-0.5">
                    {t.examples.map((e, i) => <li key={i} className="font-mono-tech text-[10px] text-white/65">· {e}</li>)}
                </ul>
            </div>
            <div className="mt-3 pt-2 border-t border-white/5 font-mono-tech text-[10px] text-[#ffce4f] leading-snug">{t.penalty_if_missed}</div>
        </div>
    );
}

function OnboardingPhase({ phase, idx }) {
    return (
        <div className="deck-card relative p-5" style={{ borderColor: `${phase.color}55` }} data-testid={`onboarding-${idx}`}>
            <CornerBrackets />
            <div className="flex items-baseline gap-3 mb-2">
                <span className="font-display font-black text-2xl" style={{ color: phase.color }}>{String(phase.phase).padStart(2, "0")}</span>
                <div className="font-display font-bold text-white text-base">{phase.label}</div>
            </div>
            <div className="mono-label text-[9px] text-white/55">{phase.owner} · {phase.duration_days} DAYS</div>
            <ul className="space-y-1.5 mt-3">
                {phase.tasks.map((t, i) => (
                    <li key={i} className="font-mono-tech text-[11px] text-white/85 leading-snug flex gap-2">
                        <span style={{ color: phase.color }}>▸</span>{t}
                    </li>
                ))}
            </ul>
            <div className="mt-3 pt-2 border-t border-white/5 font-mono-tech text-[10px] text-[#ccff00] leading-snug">EXIT · {phase.exit_criteria}</div>
        </div>
    );
}

function TicketRow({ t, onUpdate, onDelete }) {
    return (
        <div className="grid grid-cols-[60px_1fr_140px_100px_100px] gap-3 items-center px-4 py-2 border-b border-white/5" data-testid={`ticket-${t.id}`}>
            <span className="mono-label text-[10px]" style={{ color: PRIORITY_COLOR[t.priority] }}>● {t.priority}</span>
            <div>
                <div className="font-display font-bold text-white text-sm">{t.title}</div>
                <div className="font-mono-tech text-[10px] text-white/55">{t.company} · {new Date(t.created_at).toLocaleString()}</div>
            </div>
            <span className="font-mono-tech text-[10px]" style={{ color: t.status === "open" ? "#ff3b8a" : t.status === "in_progress" ? "#ffce4f" : "#ccff00" }}>{t.status?.toUpperCase()}</span>
            <select
                value={t.status}
                onChange={(e) => onUpdate(t.id, { status: e.target.value })}
                className="input-tech text-[10px] py-1"
                data-testid={`ticket-status-${t.id}`}
            >
                <option value="open">OPEN</option>
                <option value="in_progress">IN PROGRESS</option>
                <option value="resolved">RESOLVED</option>
            </select>
            <button onClick={() => onDelete(t.id)} className="mono-label text-[10px] text-white/40 hover:text-[#ff3b8a]">✕</button>
        </div>
    );
}

function TicketsSection({ tickets, reload }) {
    const [showForm, setShowForm] = useState(false);
    const [company, setCompany] = useState("");
    const [priority, setPriority] = useState("P2");
    const [title, setTitle] = useState("");

    const submit = async (e) => {
        e.preventDefault();
        if (!company.trim() || !title.trim()) return;
        try {
            await api.post("/admin/pilot-tickets", { company, priority, title });
            setCompany(""); setTitle(""); setPriority("P2");
            setShowForm(false);
            toast.success("Ticket opened");
            reload();
        } catch { toast.error("Failed to open ticket"); }
    };

    const updateT = async (id, patch) => {
        try {
            await api.patch(`/admin/pilot-tickets/${id}`, null, { params: patch });
            reload();
        } catch { toast.error("Update failed"); }
    };

    const deleteT = async (id) => {
        if (!confirm("Delete ticket?")) return;
        try {
            await api.delete(`/admin/pilot-tickets/${id}`);
            reload();
        } catch { toast.error("Delete failed"); }
    };

    return (
        <div className="deck-card relative" data-testid="tickets-section">
            <CornerBrackets />
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
                <div>
                    <div className="mono-label text-[#ff3b8a]">PILOT TICKETS · LIVE QUEUE</div>
                    <div className="font-mono-tech text-[10px] text-white/55 mt-1">
                        OPEN · P1 <span className="text-[#ff3b8a]">{tickets.open?.P1 || 0}</span> · P2 <span className="text-[#ffce4f]">{tickets.open?.P2 || 0}</span> · P3 <span className="text-[#7c5cff]">{tickets.open?.P3 || 0}</span>
                    </div>
                </div>
                <button
                    data-testid="open-ticket-btn"
                    onClick={() => setShowForm((v) => !v)}
                    className="btn-jade text-xs px-3"
                >{showForm ? "✕ CANCEL" : "+ OPEN TICKET"}</button>
            </div>
            {showForm && (
                <form onSubmit={submit} className="grid sm:grid-cols-4 gap-3 items-end p-4 border-b border-white/10 bg-[#06081a]">
                    <input data-testid="ticket-company" placeholder="Company" value={company} onChange={(e) => setCompany(e.target.value)} className="input-tech text-xs" required />
                    <select data-testid="ticket-priority" value={priority} onChange={(e) => setPriority(e.target.value)} className="input-tech text-xs">
                        <option value="P1">P1 · BLOCKER</option>
                        <option value="P2">P2 · DEGRADED</option>
                        <option value="P3">P3 · ENHANCEMENT</option>
                    </select>
                    <input data-testid="ticket-title" placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} className="input-tech text-xs" required />
                    <button data-testid="ticket-submit" className="btn-jade text-xs">+ OPEN</button>
                </form>
            )}
            {tickets.all?.length === 0 ? (
                <div className="px-6 py-12 text-center font-mono-tech text-xs text-white/40">// no open tickets · clean board //</div>
            ) : (
                <div>
                    {tickets.all.map((t) => <TicketRow key={t.id} t={t} onUpdate={updateT} onDelete={deleteT} />)}
                </div>
            )}
        </div>
    );
}

export default function OperationsPanel() {
    const [data, setData] = useState(null);
    const [tickets, setTickets] = useState({ all: [], open: { P1: 0, P2: 0, P3: 0 } });
    const [loading, setLoading] = useState(true);

    const load = async () => {
        try {
            const [o, t] = await Promise.all([
                api.get("/admin/operations"),
                api.get("/admin/pilot-tickets"),
            ]);
            setData(o.data);
            setTickets(t.data);
        } catch { toast.error("Failed to load operations"); }
        finally { setLoading(false); }
    };

    useEffect(() => { load(); }, []);

    if (loading) return <div className="deck-card p-12 flex justify-center"><JadeWorking verb="loading operations" size={72} /></div>;
    if (!data) return null;

    const fin = data.year_1_financial_model;

    return (
        <div className="space-y-6" data-testid="operations-panel">
            <div className="deck-card p-6 relative" data-testid="ops-hero">
                <CornerBrackets />
                <SectionLabel idx={0} color="#7c5cff">OPERATIONS · LIGHTHOUSE</SectionLabel>
                <h2 className="font-display font-black text-white text-4xl tracking-tighter mt-2">
                    Ship the plan. <span className="accent-lime">Without burning out.</span>
                </h2>
                <p className="text-white/65 text-sm mt-3 max-w-2xl leading-relaxed">{data.subtitle}</p>

                <div className="grid sm:grid-cols-4 gap-4 mt-6">
                    <Stat k="TEAM BURN · MO" v={`$${(data.team_burn.monthly_contractor_floor / 1000).toFixed(1)}k`} c="#ccff00" />
                    <Stat k="INFRA · MO" v={`$${(data.infrastructure_burn.monthly_low / 1000).toFixed(1)}-${(data.infrastructure_burn.monthly_high / 1000).toFixed(1)}k`} c="#00ffff" />
                    <Stat k="YR1 COST RANGE" v={`$${(fin.summary.total_cost_low / 1000).toFixed(0)}-${(fin.summary.total_cost_high / 1000).toFixed(0)}k`} c="#ff3b8a" />
                    <Stat k="YR1 REVENUE" v={`$${(fin.summary.total_revenue_low / 1000).toFixed(0)}-${(fin.summary.total_revenue_high / 1000).toFixed(0)}k`} c="#7c5cff" />
                </div>
            </div>

            {/* TICKETS · LIVE */}
            <TicketsSection tickets={tickets} reload={load} />

            {/* TEAM */}
            <div data-testid="team-section">
                <div className="mono-label text-[#ccff00] mb-3">TEAM · 5-CLIENT LIGHTHOUSE PHASE</div>
                <div className="grid sm:grid-cols-2 gap-4">
                    {data.team.map((t) => <TeamCard key={t.id} t={t} />)}
                </div>
            </div>

            {/* INFRA COSTS */}
            <div className="deck-card relative" data-testid="infra-section">
                <CornerBrackets />
                <div className="px-6 py-4 border-b border-white/10 mono-label text-[#00ffff]">INFRASTRUCTURE COST MATRIX · MONTHLY</div>
                <div>
                    {data.infrastructure.map((c) => (
                        <div key={c.id} className="grid grid-cols-[1fr_140px_1fr] gap-3 items-center px-6 py-3 border-b border-white/5">
                            <div>
                                <div className="font-display font-bold text-white text-sm">{c.category}</div>
                                <div className="font-mono-tech text-[10px] text-white/55 mt-1 leading-snug">{c.notes}</div>
                            </div>
                            <div className="text-right">
                                <div className="font-display font-black text-base text-[#ccff00]">${c.monthly_low}-${c.monthly_high}</div>
                                <div className="mono-label text-[9px] text-white/40 mt-0.5">{c.per_client_scale ? "PER · SCALES" : "FIXED"}</div>
                            </div>
                            <div></div>
                        </div>
                    ))}
                </div>
            </div>

            {/* SLA TIERS */}
            <div data-testid="sla-section">
                <div className="mono-label text-[#ff3b8a] mb-3">SLA TIERS · CUSTOMER COMMITMENTS</div>
                <div className="grid sm:grid-cols-3 gap-4">
                    {data.sla_tiers.map((t) => <SlaCard key={t.priority} t={t} />)}
                </div>
            </div>

            {/* ONBOARDING */}
            <div data-testid="onboarding-section">
                <div className="mono-label text-[#7c5cff] mb-3">ONBOARDING · 2-3 WEEK PLAYBOOK PER CLIENT</div>
                <div className="grid sm:grid-cols-2 gap-4">
                    {data.onboarding_playbook.map((p, i) => <OnboardingPhase key={p.phase} phase={p} idx={i} />)}
                </div>
            </div>

            {/* ROADMAP MATRIX */}
            <div className="deck-card relative p-6" data-testid="roadmap-matrix">
                <CornerBrackets />
                <div className="mono-label text-[#ccff00] mb-3">ROADMAP · CLIENT REQUEST DECISION MATRIX</div>
                <div className="grid sm:grid-cols-2 gap-3">
                    {Object.entries(data.roadmap_prioritization).map(([k, v]) => {
                        if (typeof v === "string") return null;
                        return (
                            <div key={k} className="border p-3" style={{ borderColor: `${v.color}44`, background: `${v.color}11` }} data-testid={`roadmap-${k}`}>
                                <div className="mono-label text-[10px]" style={{ color: v.color }}>{k.replace(/_/g, " ").toUpperCase()}</div>
                                <div className="font-display font-bold text-white text-sm mt-1">{v.rule}</div>
                                <ul className="space-y-0.5 mt-2">
                                    {v.examples?.map((e, i) => <li key={i} className="font-mono-tech text-[10px] text-white/65">· {e}</li>)}
                                </ul>
                            </div>
                        );
                    })}
                </div>
                <div className="mt-3 pt-3 border-t border-white/5 font-mono-tech text-[11px] text-[#ffce4f] leading-snug">
                    ⏱ {data.roadmap_prioritization.engineer_time_allocation}
                </div>
            </div>

            {/* FINANCIAL MODEL */}
            <div className="deck-card relative" data-testid="financial-model">
                <CornerBrackets />
                <div className="px-6 py-4 border-b border-white/10">
                    <div className="mono-label text-[#ff3b8a]">YEAR 1 FINANCIAL MODEL · 5 CLIENTS</div>
                    <div className="font-mono-tech text-[10px] text-white/55 mt-1">{fin.summary.verdict}</div>
                </div>
                <div className="grid sm:grid-cols-2 divide-x divide-white/5">
                    <div className="p-5">
                        <div className="mono-label text-[#ff3b8a] mb-2">COSTS · ANNUAL</div>
                        {fin.annual_costs.map((c, i) => (
                            <div key={i} className="grid grid-cols-[1fr_120px] gap-2 items-center py-1.5 border-b border-white/5">
                                <span className="font-mono-tech text-[11px] text-white/85">{c.item}</span>
                                <span className="font-display font-bold text-sm text-[#ff3b8a] text-right">${(c.low / 1000).toFixed(0)}-${(c.high / 1000).toFixed(0)}k</span>
                            </div>
                        ))}
                        <div className="mt-2 pt-2 border-t border-white/10 grid grid-cols-[1fr_120px] gap-2 items-baseline">
                            <span className="font-display font-bold text-white">TOTAL</span>
                            <span className="font-display font-black text-xl text-[#ff3b8a] text-right">${(fin.summary.total_cost_low / 1000).toFixed(0)}-${(fin.summary.total_cost_high / 1000).toFixed(0)}k</span>
                        </div>
                    </div>
                    <div className="p-5">
                        <div className="mono-label text-[#ccff00] mb-2">REVENUE · ANNUAL</div>
                        {fin.annual_revenue.map((r, i) => (
                            <div key={i} className="grid grid-cols-[1fr_120px] gap-2 items-center py-1.5 border-b border-white/5">
                                <span className="font-mono-tech text-[11px] text-white/85">{r.item}</span>
                                <span className="font-display font-bold text-sm text-[#ccff00] text-right">${(r.low / 1000).toFixed(0)}-${(r.high / 1000).toFixed(0)}k</span>
                            </div>
                        ))}
                        <div className="mt-2 pt-2 border-t border-white/10 grid grid-cols-[1fr_120px] gap-2 items-baseline">
                            <span className="font-display font-bold text-white">TOTAL</span>
                            <span className="font-display font-black text-xl text-[#ccff00] text-right">${(fin.summary.total_revenue_low / 1000).toFixed(0)}-${(fin.summary.total_revenue_high / 1000).toFixed(0)}k</span>
                        </div>
                        <div className="mt-3 pt-2 border-t border-white/10">
                            <div className="mono-label text-[10px] text-[#7c5cff]">GROSS MARGIN</div>
                            <div className="font-display font-black text-2xl text-[#7c5cff] mt-1">{fin.summary.gross_margin_low_pct}-{fin.summary.gross_margin_high_pct}%</div>
                        </div>
                    </div>
                </div>
                <div className="px-6 py-4 border-t border-white/5 font-mono-tech text-[11px] text-[#ccff00] leading-relaxed">
                    🔥 {fin.summary.compounding_unlock}
                </div>
            </div>

            {/* MILESTONES */}
            <div data-testid="milestones-section">
                <div className="mono-label text-[#00ffff] mb-3">12-MONTH MILESTONE TIMELINE</div>
                <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
                    {data.milestones.map((m, i) => (
                        <div key={i} className="deck-card relative p-4" style={{ borderTop: `2px solid ${m.color}` }} data-testid={`milestone-${i}`}>
                            <CornerBrackets />
                            <div className="font-display font-black text-2xl" style={{ color: m.color }}>{m.month}</div>
                            <div className="mono-label text-[10px] mt-1" style={{ color: m.color }}>{m.label}</div>
                            <ul className="space-y-1 mt-3">
                                {m.items.map((it, j) => (
                                    <li key={j} className="font-mono-tech text-[10px] text-white/80 leading-snug flex gap-1"><span style={{ color: m.color }}>·</span>{it}</li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>
            </div>

            {/* PRINCIPLES */}
            <div className="deck-card p-6 relative" data-testid="operating-principles">
                <CornerBrackets />
                <div className="mono-label text-[#7c5cff] mb-3">OPERATING PRINCIPLES · TAPE TO MONITOR</div>
                <ol className="space-y-2">
                    {data.operating_principles.map((p, i) => (
                        <li key={i} className="font-mono-tech text-xs text-white/85 leading-relaxed flex gap-3">
                            <span className="text-[#ccff00] font-bold">{String(i + 1).padStart(2, "0")}</span>{p}
                        </li>
                    ))}
                </ol>
            </div>
        </div>
    );
}
