/**
 * ConsoleWorkbenchPanel — Public console agents that expose Workbench
 * capabilities to AgentDemo viewers (no admin login required).
 *
 * Modes:
 *  • ROI MODELER · OP-02 (pure math, 3 archetypes, NPV + sensitivity)
 *  • ARCHITECTURE · OP-03 (6 modules + pipeline + swimlanes + API surface)
 *  • COLLATERAL · OP-04 (12-slide deck + 4 fact sheets + competitive brief + PDF)
 *  • TECHNICAL BRIEF · OP-05 (10-section operator-grade document + PDF)
 *  • STRATEGY · decisions + risks + 8-phase rollout (read-only)
 */
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api, API_BASE } from "../lib/api";
import { CornerBrackets } from "./Brackets";

const MODES = [
    { id: "roi", label: "ROI MODELER · OP-02", c: "#ccff00" },
    { id: "arch", label: "ARCHITECTURE · OP-03", c: "#7c5cff" },
    { id: "collateral", label: "COLLATERAL · OP-04", c: "#ff3b8a" },
    { id: "doc", label: "TECHNICAL BRIEF · OP-05", c: "#ffce4f" },
    { id: "strategy", label: "DECISIONS · RISKS · PHASES", c: "#00ffff" },
];

function Stat({ k, v, c, sub }) {
    return (
        <div className="border px-4 py-3" style={{ borderColor: `${c}33`, background: `${c}08` }}>
            <div className="mono-label text-[10px]" style={{ color: c }}>{k}</div>
            <div className="font-display font-black text-xl mt-1" style={{ color: c }}>{v}</div>
            {sub && <div className="font-mono-tech text-[10px] text-white/40 mt-1">{sub}</div>}
        </div>
    );
}

function RoiPanel() {
    const [archetype, setArchetype] = useState("mid_market");
    const [fleet, setFleet] = useState(0);
    const [data, setData] = useState(null);
    const [busy, setBusy] = useState(false);
    const run = async () => {
        setBusy(true);
        try {
            const { data } = await api.post("/agent/workbench/roi", { archetype, fleet_size: fleet || 0 });
            setData(data);
        } catch (e) { toast.error("ROI model failed."); }
        finally { setBusy(false); }
    };
    useEffect(() => { run(); }, [archetype]);
    return (
        <div className="space-y-4" data-testid="console-roi">
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="mono-label text-[#ccff00]">ROI MODELER · OP-02 · INDUSTRY-BENCHMARK MATH (NO LLM)</div>
                <div className="grid lg:grid-cols-[1fr_180px_140px] gap-3 items-end mt-3">
                    <div>
                        <label className="mono-label text-[10px] text-white/55">ARCHETYPE</label>
                        <select data-testid="console-roi-archetype" value={archetype} onChange={(e) => setArchetype(e.target.value)} className="input-tech text-xs w-full mt-1">
                            <option value="small_regional">SMALL REGIONAL · 25-75 TRUCKS</option>
                            <option value="mid_market">MID-MARKET · 100-250 TRUCKS</option>
                            <option value="specialized_hazmat">SPECIALIZED / HAZMAT · 50-150</option>
                        </select>
                    </div>
                    <div>
                        <label className="mono-label text-[10px] text-white/55">FLEET OVERRIDE</label>
                        <input data-testid="console-roi-fleet" type="number" value={fleet} onChange={(e) => setFleet(parseInt(e.target.value || 0))} className="input-tech text-xs w-full mt-1" />
                    </div>
                    <button data-testid="console-roi-run" onClick={run} disabled={busy} className="btn-jade text-xs disabled:opacity-50">{busy ? "MODELING…" : "▶ RECOMPUTE"}</button>
                </div>
            </div>
            {data && (
                <>
                    <div className="grid sm:grid-cols-3 gap-3">
                        <Stat k="ANNUAL SAVINGS" v={`$${data.model.annual_total_savings_usd.toLocaleString()}`} c="#ccff00" />
                        <Stat k="3-YR NPV @ 10%" v={`$${data.model.three_year.npv_at_10pct_discount_usd.toLocaleString()}`} c="#00ffff" />
                        <Stat k="PAYBACK" v={data.model.three_year.payback_months ? `${data.model.three_year.payback_months}mo` : "—"} c="#7c5cff" />
                    </div>
                    <div className="deck-card p-5 relative">
                        <CornerBrackets />
                        <div className="mono-label text-[#ccff00] mb-3">6-CATEGORY BREAKDOWN</div>
                        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
                            {Object.entries(data.model.by_category_usd).map(([k, v]) => (
                                <div key={k} className="border border-white/10 p-3">
                                    <div className="mono-label text-[10px] text-white/55">{k.replace(/_usd$/, "").replace(/_/g, " ").toUpperCase()}</div>
                                    <div className="font-display font-bold text-[#ccff00] text-lg mt-1">${v.toLocaleString()}</div>
                                </div>
                            ))}
                        </div>
                        <div className="mt-4 pt-3 border-t border-white/5 font-mono-tech text-[10px] text-white/55">
                            <div className="mono-label text-[10px] text-[#7c5cff] mb-1">SOURCES · {data.model.sources.length}</div>
                            <ul className="space-y-0.5">{data.model.sources.map((s, i) => <li key={i}>· {s}</li>)}</ul>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

function ArchPanel() {
    const [data, setData] = useState(null);
    useEffect(() => {
        api.get("/agent/workbench/architecture").then(({ data }) => setData(data)).catch(() => toast.error("Load failed."));
    }, []);
    if (!data) return <div className="deck-card p-12 text-center font-mono-tech text-white/45">// loading architecture…</div>;
    return (
        <div className="space-y-4" data-testid="console-arch">
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="mono-label text-[#7c5cff]">AI ARCHITECTURE · OP-03 · 6 AGENT MODULES · 6-STAGE DATA PIPELINE</div>
                <p className="font-mono-tech text-[11px] text-white/65 mt-2">Operator-grade reference. Every module documents inputs, decision logic, autonomy level, and KPI band.</p>
            </div>
            <div className="grid lg:grid-cols-2 gap-3">
                {data.modules.map((m) => (
                    <div key={m.id} className="deck-card p-4 relative" data-testid={`console-arch-${m.id}`}>
                        <CornerBrackets />
                        <div className="flex justify-between items-baseline">
                            <span className="font-display font-black text-white text-sm">{m.id} · {m.name}</span>
                            <span className="mono-label text-[10px] text-[#ccff00]">{m.autonomy}</span>
                        </div>
                        <div className="font-mono-tech text-[10px] text-white/55 mt-2">IN · {m.inputs.join(" · ")}</div>
                        <div className="font-mono-tech text-[10px] text-white/55 mt-1">OUT · {m.outputs.join(" · ")}</div>
                        <div className="font-mono-tech text-[10.5px] text-[#7c5cff] mt-1">LOGIC · {m.decision_logic}</div>
                        <div className="font-mono-tech text-[10.5px] text-[#ccff00] mt-1">KPI · {m.kpi}</div>
                    </div>
                ))}
            </div>
            <div className="grid lg:grid-cols-2 gap-3">
                <div className="deck-card p-4 relative">
                    <CornerBrackets />
                    <div className="mono-label text-[#00ffff] mb-2">DATA PIPELINE</div>
                    {data.data_pipeline.map((s, i) => (
                        <div key={i} className="border-l-2 border-[#00ffff44] pl-3 py-1">
                            <div className="font-display font-bold text-white text-sm">{s.stage}</div>
                            <div className="font-mono-tech text-[10px] text-white/65">{s.items.join(" · ")}</div>
                        </div>
                    ))}
                </div>
                <div className="deck-card p-4 relative">
                    <CornerBrackets />
                    <div className="mono-label text-[#ffce4f] mb-2">API SURFACE</div>
                    <div className="divide-y divide-white/5">
                        {data.api_surface.map((a, i) => (
                            <div key={i} className="py-1.5 grid grid-cols-[60px_1fr] gap-2 text-[10.5px] font-mono-tech">
                                <span className="text-[#ccff00]">{a.method}</span>
                                <div>
                                    <div className="text-white">{a.path}</div>
                                    <div className="text-white/55">{a.purpose}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

function CollateralPanel() {
    const [data, setData] = useState(null);
    useEffect(() => {
        api.get("/agent/workbench/collateral").then(({ data }) => setData(data)).catch(() => toast.error("Load failed."));
    }, []);
    if (!data) return <div className="deck-card p-12 text-center font-mono-tech text-white/45">// loading collateral…</div>;
    return (
        <div className="space-y-4" data-testid="console-collateral">
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="flex flex-wrap justify-between items-baseline gap-3">
                    <div>
                        <div className="mono-label text-[#ff3b8a]">COLLATERAL · OP-04 · 12-SLIDE DECK · {data.factsheet_count} FACT SHEETS</div>
                        <p className="font-mono-tech text-[11px] text-white/65 mt-1">Persona-tuned pitch deck, 1-page fact sheets, readiness assessment, and head-to-head competitive brief.</p>
                    </div>
                    <a data-testid="console-deck-download" href={`${API_BASE}/agent/workbench/deck.pdf`} target="_blank" rel="noreferrer"
                        className="btn-jade text-xs" style={{ background: "#ff3b8a" }}>↓ DOWNLOAD DECK · PDF</a>
                </div>
            </div>
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="mono-label text-[#ccff00] mb-3">DECK · {data.slide_count} SLIDES</div>
                <div className="grid lg:grid-cols-2 gap-3 max-h-[420px] overflow-y-auto">
                    {data.deck.slides.map((s) => (
                        <div key={s.n} className="border border-white/10 p-3">
                            <span className="mono-label text-[10px] text-[#7c5cff]">SLIDE {s.n} · {s.kind.toUpperCase()}</span>
                            <div className="font-display font-bold text-white text-sm mt-1">{s.title}</div>
                            {s.subtitle && <div className="font-mono-tech text-[10.5px] text-[#ccff00] mt-1">{s.subtitle}</div>}
                            {s.bullets && (
                                <ul className="mt-2 space-y-0.5">
                                    {s.bullets.map((b, i) => <li key={i} className="font-mono-tech text-[10px] text-white/75">• {b}</li>)}
                                </ul>
                            )}
                        </div>
                    ))}
                </div>
            </div>
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="mono-label text-[#00ffff] mb-3">FACT SHEETS · {data.factsheet_count}</div>
                <div className="grid sm:grid-cols-2 gap-3">
                    {data.deck.fact_sheets.map((f, i) => (
                        <div key={i} className="border border-white/10 p-3">
                            <div className="font-display font-black text-[#00ffff] text-sm">{f.persona}</div>
                            <div className="font-mono-tech text-[11px] text-[#ccff00] mt-1">{f.headline}</div>
                            <div className="font-mono-tech text-[10px] text-white/55 mt-2">PAINS · {f.pains.join(" · ")}</div>
                            <div className="font-mono-tech text-[10px] text-white/55 mt-1">LEAD · {f.lead_agent}</div>
                            <div className="font-mono-tech text-[10.5px] text-[#ccff00] mt-1">ROI · {f.expected_roi}</div>
                        </div>
                    ))}
                </div>
            </div>
            <div className="deck-card p-5 relative" data-testid="console-competitive">
                <CornerBrackets />
                <div className="mono-label text-[#7c5cff] mb-2">COMPETITIVE BRIEF</div>
                {Object.entries(data.deck.competitive_brief).map(([k, v]) => (
                    <div key={k} className="border-l-2 border-[#7c5cff55] pl-3 py-1.5">
                        <div className="mono-label text-[10px] text-[#7c5cff]">{k.replace(/_/g, " ").toUpperCase()}</div>
                        <div className="font-mono-tech text-[10.5px] text-white/85 mt-0.5">{v}</div>
                    </div>
                ))}
            </div>
        </div>
    );
}

function DocPanel() {
    const [data, setData] = useState(null);
    useEffect(() => {
        api.get("/agent/workbench/document").then(({ data }) => setData(data)).catch(() => toast.error("Load failed."));
    }, []);
    if (!data) return <div className="deck-card p-12 text-center font-mono-tech text-white/45">// loading brief…</div>;
    return (
        <div className="space-y-4" data-testid="console-doc">
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="flex flex-wrap justify-between items-baseline gap-3">
                    <div>
                        <div className="mono-label text-[#ffce4f]">TECHNICAL BRIEF · OP-05 · {data.section_count} SECTIONS</div>
                        <p className="font-mono-tech text-[11px] text-white/65 mt-1">Operator-grade Benefits &amp; Features. Every claim is benchmark-traceable.</p>
                    </div>
                    <a data-testid="console-doc-download" href={`${API_BASE}/agent/workbench/document.pdf`} target="_blank" rel="noreferrer"
                        className="btn-jade text-xs" style={{ background: "#ffce4f", color: "#0a0c18" }}>↓ DOWNLOAD BRIEF · PDF</a>
                </div>
            </div>
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                    {data.sections.map((s, i) => (
                        <div key={i} className="border border-white/10 p-3">
                            <div className="font-display font-bold text-[#ffce4f] text-sm">{s.title}</div>
                            <div className="font-mono-tech text-[10.5px] text-white/85 mt-1 leading-relaxed whitespace-pre-line">{s.body}</div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

function StrategyPanel() {
    const [data, setData] = useState({ decisions: [], risks: [], phases: [] });
    useEffect(() => {
        Promise.all([
            api.get("/agent/workbench/decisions"),
            api.get("/agent/workbench/risks"),
            api.get("/agent/workbench/phases"),
        ]).then(([d, r, p]) => setData({ decisions: d.data.decisions, risks: r.data.risks, phases: p.data.phases }))
            .catch(() => toast.error("Load failed."));
    }, []);
    return (
        <div className="space-y-4" data-testid="console-strategy">
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="flex flex-wrap items-baseline justify-between gap-3">
                    <div>
                        <div className="mono-label text-[#00ffff]">STRATEGY · 5 DECISIONS · 7 RISKS · 8 PHASES</div>
                        <p className="font-mono-tech text-[11px] text-white/65 mt-1">The same decisions, risks, and phases the operator tracks in the admin Workbench — visible here as proof of the operating layer.</p>
                    </div>
                    <a data-testid="console-plan-download" href={`${API_BASE}/agent/workbench/plan.pdf`} target="_blank" rel="noreferrer"
                        className="btn-jade text-xs" style={{ background: "#7c5cff", color: "#fff" }}>↓ DOWNLOAD EXECUTION PLAN · PDF</a>
                </div>
            </div>
            <div className="grid lg:grid-cols-2 gap-3">
                <div className="deck-card relative" data-testid="console-decisions">
                    <CornerBrackets />
                    <div className="px-5 py-3 border-b border-white/10 mono-label text-[#ff3b8a]">DECISIONS · {data.decisions.length}</div>
                    <div className="divide-y divide-white/5 max-h-[420px] overflow-y-auto">
                        {data.decisions.map((d) => (
                            <div key={d.id} className="px-5 py-3">
                                <div className="flex justify-between items-baseline gap-2">
                                    <span className="font-display font-bold text-white text-sm">{d.id} · {d.title}</span>
                                    <span className="mono-label text-[9px] text-[#ccff00]">{(d.status || "pending").toUpperCase()}</span>
                                </div>
                                <p className="font-mono-tech text-[10.5px] text-white/65 mt-1">{d.context}</p>
                                <p className="font-mono-tech text-[10.5px] text-[#ccff00] mt-1">▸ {d.recommendation}</p>
                            </div>
                        ))}
                    </div>
                </div>
                <div className="deck-card relative" data-testid="console-risks">
                    <CornerBrackets />
                    <div className="px-5 py-3 border-b border-white/10 mono-label text-[#ffce4f]">RISKS · {data.risks.length}</div>
                    <div className="divide-y divide-white/5 max-h-[420px] overflow-y-auto">
                        {data.risks.map((r) => (
                            <div key={r.id} className="px-5 py-3">
                                <div className="flex justify-between items-baseline">
                                    <span className="mono-label text-[10px] text-[#ffce4f]">● {r.severity} · {r.id}</span>
                                    <span className="mono-label text-[10px] text-white/45">{(r.status || "open").toUpperCase()}</span>
                                </div>
                                <p className="font-mono-tech text-[10.5px] text-white/85 mt-1">{r.text}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
            <div className="deck-card p-5 relative" data-testid="console-phases">
                <CornerBrackets />
                <div className="mono-label text-[#7c5cff] mb-3">8-PHASE ROLLOUT</div>
                <div className="grid lg:grid-cols-2 gap-3">
                    {data.phases.map((p) => (
                        <div key={p.n} className="border border-white/10 p-3">
                            <div className="flex justify-between items-baseline">
                                <span className="font-display font-bold text-white text-sm">PHASE {p.n} · {p.title}</span>
                                <span className="mono-label text-[10px] text-[#7c5cff]">{p.duration}</span>
                            </div>
                            <ul className="mt-1 space-y-0.5">
                                {(p.steps || []).map((s, i) => {
                                    const t = typeof s === "string" ? s : s.text;
                                    return <li key={i} className="font-mono-tech text-[10px] text-white/65">• {t}</li>;
                                })}
                            </ul>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default function ConsoleWorkbenchPanel() {
    const [mode, setMode] = useState("roi");
    return (
        <div className="space-y-4" data-testid="console-workbench-panel">
            <div className="flex flex-wrap gap-2">
                {MODES.map((m) => {
                    const active = mode === m.id;
                    return (
                        <button key={m.id} data-testid={`console-mode-${m.id}`} onClick={() => setMode(m.id)}
                            className="px-3 py-2 mono-label text-[11px] transition"
                            style={{ border: `1px solid ${active ? m.c : "rgba(255,255,255,0.10)"}`,
                                color: active ? m.c : "rgba(255,255,255,0.55)",
                                background: active ? `${m.c}11` : "transparent" }}>{m.label}</button>
                    );
                })}
            </div>
            {mode === "roi" && <RoiPanel />}
            {mode === "arch" && <ArchPanel />}
            {mode === "collateral" && <CollateralPanel />}
            {mode === "doc" && <DocPanel />}
            {mode === "strategy" && <StrategyPanel />}
        </div>
    );
}
