/**
 * PipelinePanel — admin tab. Lighthouse-pipeline kanban.
 *
 * One card per company. Six stages: COLD → AUDIT_STARTED → AUDIT_ANALYZED →
 * PILOT_DISCUSSED → PILOT_SIGNED → PASSED. Cards drag between stages OR click
 * the dropdown to move. Each card surfaces: industry, AI Readiness Score,
 * tier, last outreach campaign, estimated annual savings, quick links to
 * the underlying audit + outreach rows.
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { CornerBrackets } from "./Brackets";
import { toast } from "sonner";

const TIER_COLOR = {
    PIONEER: "#ccff00", BUILDER: "#00ffff", CURIOUS: "#7c5cff", LEARNING: "#ffce4f",
};

export default function PipelinePanel() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [draggingId, setDraggingId] = useState(null);
    const [reloadKey, setReloadKey] = useState(0);
    const [adding, setAdding] = useState(false);
    const [newCard, setNewCard] = useState({ company_name: "", industry: "", stage: "cold", notes: "" });

    useEffect(() => {
        let cancelled = false;
        (async () => {
            setLoading(true);
            try {
                const { data: d } = await api.get("/admin/pipeline");
                if (!cancelled) setData(d);
            } catch {
                if (!cancelled) toast.error("Could not load pipeline.");
            } finally { if (!cancelled) setLoading(false); }
        })();
        return () => { cancelled = true; };
    }, [reloadKey]);

    if (loading || !data) {
        return <div className="font-mono-tech text-white/45 p-6">// loading pipeline…</div>;
    }

    const stageOrder = Object.entries(data.stages).sort((a, b) => a[1].order - b[1].order).map(([k]) => k);

    return (
        <div className="space-y-6" data-testid="pipeline-panel">
            {/* Header */}
            <div className="flex items-center justify-between flex-wrap gap-3">
                <div>
                    <div className="mono-label text-[10px] text-[#ccff00]">CONSOLE · LIGHTHOUSE PIPELINE</div>
                    <h2 className="font-display font-black text-white text-2xl mt-1 tracking-tight">
                        One funnel. Three sources.
                    </h2>
                    <p className="font-mono-tech text-[11px] text-white/55 mt-1.5">
                        Cards auto-created when you start an audit or log outreach. Drag between stages or use the dropdown.
                    </p>
                </div>
                <button data-testid="pipeline-add-card-btn"
                        onClick={() => setAdding(true)}
                        className="btn-jade text-xs"
                        style={{ background: "#ccff00", color: "#02030a" }}>
                    + ADD COMPANY
                </button>
            </div>

            {/* KPI strip */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2" data-testid="pipeline-kpis">
                {stageOrder.map((s) => (
                    <Kpi key={s} label={data.stages[s].label} value={data.kpis[s] || 0} c={data.stages[s].color} />
                ))}
                <Kpi label="SIGNED $ / YR" value={`$${(data.kpis.annual_savings_signed_usd / 1000).toFixed(0)}k`} c="#ccff00" />
            </div>

            {/* Quick-add card form */}
            {adding && (
                <div className="relative border border-[#ccff0044] p-4 bg-[#ccff0008]" data-testid="pipeline-add-form">
                    <CornerBrackets />
                    <div className="mono-label text-[10px] text-[#ccff00] mb-3">ADD COMPANY MANUALLY</div>
                    <div className="grid sm:grid-cols-4 gap-3">
                        <input data-testid="pipeline-new-company"
                               className="input-tech text-[12px]"
                               placeholder="Company name"
                               value={newCard.company_name}
                               onChange={(e) => setNewCard({ ...newCard, company_name: e.target.value })} />
                        <input data-testid="pipeline-new-industry"
                               className="input-tech text-[12px]"
                               placeholder="Industry (optional)"
                               value={newCard.industry}
                               onChange={(e) => setNewCard({ ...newCard, industry: e.target.value })} />
                        <select data-testid="pipeline-new-stage"
                                className="input-tech text-[12px]"
                                value={newCard.stage}
                                onChange={(e) => setNewCard({ ...newCard, stage: e.target.value })}>
                            {stageOrder.map((s) => (
                                <option key={s} value={s}>{data.stages[s].label}</option>
                            ))}
                        </select>
                        <div className="flex gap-2">
                            <button data-testid="pipeline-create-btn"
                                    onClick={async () => {
                                        if (!newCard.company_name.trim()) { toast.error("Company name required."); return; }
                                        try {
                                            await api.post("/admin/pipeline", {
                                                company_name: newCard.company_name,
                                                industry: newCard.industry || undefined,
                                                stage: newCard.stage,
                                                notes: newCard.notes || undefined,
                                            });
                                            toast.success("Card added.");
                                            setNewCard({ company_name: "", industry: "", stage: "cold", notes: "" });
                                            setAdding(false);
                                            setReloadKey((k) => k + 1);
                                        } catch { toast.error("Create failed."); }
                                    }}
                                    className="btn-jade text-xs"
                                    style={{ background: "#ccff00", color: "#02030a" }}>
                                CREATE
                            </button>
                            <button onClick={() => setAdding(false)} className="btn-jade text-xs"
                                    style={{ background: "transparent", color: "white", border: "1px solid rgba(255,255,255,0.15)" }}>
                                CANCEL
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* KANBAN */}
            <div className="overflow-x-auto pb-4" data-testid="pipeline-kanban">
                <div className="flex gap-3 min-w-fit">
                    {stageOrder.map((stage) => {
                        const stageData = data.stages[stage];
                        const cards = data.by_stage[stage] || [];
                        return (
                            <div key={stage}
                                 data-testid={`pipeline-col-${stage}`}
                                 onDragOver={(e) => e.preventDefault()}
                                 onDrop={async (e) => {
                                     e.preventDefault();
                                     const id = draggingId;
                                     setDraggingId(null);
                                     if (!id) return;
                                     try {
                                         await api.patch(`/admin/pipeline/${id}`, { stage });
                                         setReloadKey((k) => k + 1);
                                     } catch { toast.error("Move failed."); }
                                 }}
                                 className="w-[300px] flex-shrink-0">
                                <div className="relative border p-3 bg-[#0a0c18] sticky top-0 z-10"
                                     style={{ borderColor: `${stageData.color}55` }}>
                                    <CornerBrackets />
                                    <div className="flex items-center justify-between">
                                        <span className="mono-label text-[10px]" style={{ color: stageData.color }}>
                                            ● {stageData.label}
                                        </span>
                                        <span className="font-display font-black" style={{ color: stageData.color, fontSize: "1rem" }}>
                                            {cards.length}
                                        </span>
                                    </div>
                                </div>
                                <div className="space-y-2 mt-2 min-h-[120px]">
                                    {cards.length === 0 && (
                                        <div className="border border-dashed border-white/10 p-4 text-center
                                                        font-mono-tech text-[10px] text-white/30">
                                            drop here
                                        </div>
                                    )}
                                    {cards.map((c) => (
                                        <Card key={c.id} card={c} stages={data.stages}
                                              onDragStart={() => setDraggingId(c.id)}
                                              onPatch={(stage) => {
                                                  api.patch(`/admin/pipeline/${c.id}`, { stage })
                                                     .then(() => setReloadKey((k) => k + 1))
                                                     .catch(() => toast.error("Move failed."));
                                              }}
                                              onDelete={() => {
                                                  if (!window.confirm(`Remove ${c.company_name} from pipeline?`)) return;
                                                  api.delete(`/admin/pipeline/${c.id}`)
                                                     .then(() => setReloadKey((k) => k + 1))
                                                     .catch(() => toast.error("Delete failed."));
                                              }} />
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>

            <div className="font-mono-tech text-[10px] text-white/40 pt-4 border-t border-white/5">
                Cards reflect ONE company across the JadeOS lifecycle. Stage promotes automatically when an audit
                is started or analyzed. Past `audit_analyzed`, you drive the funnel.
            </div>
        </div>
    );
}

function Card({ card, stages, onDragStart, onPatch, onDelete }) {
    const stageOrder = Object.entries(stages).sort((a, b) => a[1].order - b[1].order).map(([k]) => k);
    const tierC = TIER_COLOR[card.tier];

    return (
        <div draggable
             onDragStart={onDragStart}
             data-testid={`pipeline-card-${card.id}`}
             className="relative border border-white/10 p-3 bg-[#0a0c18] hover:border-white/30 transition cursor-move">
            <CornerBrackets />
            <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                    <div className="font-display font-black text-white text-[13px] truncate">{card.company_name}</div>
                    <div className="font-mono-tech text-[9.5px] text-white/45 mt-0.5">
                        {card.industry?.replace("_", " ").toUpperCase() || "—"}
                    </div>
                </div>
                {card.tier && (
                    <span className="mono-label text-[8.5px] font-bold whitespace-nowrap"
                          style={{ color: tierC }}>
                        {card.tier}
                    </span>
                )}
            </div>

            {/* Score + savings row */}
            {(card.score != null || card.savings_central != null) && (
                <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/5">
                    {card.score != null && (
                        <div>
                            <div className="mono-label text-[8px] text-white/40">SCORE</div>
                            <div className="font-display font-bold text-[18px]" style={{ color: tierC || "white" }}>
                                {Math.round(card.score)}
                            </div>
                        </div>
                    )}
                    {card.savings_central != null && (
                        <div className="text-right">
                            <div className="mono-label text-[8px] text-white/40">EST $ / YR</div>
                            <div className="font-display font-bold text-[#ccff00] text-[14px]">
                                ${(card.savings_central / 1000).toFixed(0)}k
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Outreach line */}
            {card.last_outreach_campaign && (
                <div className="font-mono-tech text-[9px] text-white/50 mt-2 truncate">
                    <span style={{ color: "#ff3b8a" }}>↗ </span>
                    {card.last_outreach_campaign} · {card.last_outreach_sent_at?.slice(0, 10)}
                </div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-between mt-3 pt-2 border-t border-white/5 gap-2">
                <select className="bg-transparent border border-white/10 text-[9px] mono-label text-white/75 px-1.5 py-1 outline-none"
                        value={card.stage}
                        data-testid={`pipeline-card-${card.id}-stage-select`}
                        onChange={(e) => onPatch(e.target.value)}>
                    {stageOrder.map((s) => (
                        <option key={s} value={s}>{stages[s].label}</option>
                    ))}
                </select>
                <div className="flex gap-2">
                    {card.audit_id && (
                        <Link to={`/audit/${card.audit_id}`}
                              data-testid={`pipeline-card-${card.id}-audit-link`}
                              className="mono-label text-[9px] text-[#00ffff] hover:underline">↗ AUDIT</Link>
                    )}
                    <button onClick={onDelete}
                            data-testid={`pipeline-card-${card.id}-delete`}
                            className="mono-label text-[9px] text-[#ff3b8a] hover:underline">DEL</button>
                </div>
            </div>
        </div>
    );
}

function Kpi({ label, value, c }) {
    return (
        <div className="relative border p-3 bg-[#0a0c18]" style={{ borderColor: `${c}44` }}>
            <CornerBrackets />
            <div className="mono-label text-[9px] text-white/55 truncate">{label}</div>
            <div className="font-display font-black mt-1" style={{ color: c, fontSize: "1.3rem" }}>{value}</div>
        </div>
    );
}
