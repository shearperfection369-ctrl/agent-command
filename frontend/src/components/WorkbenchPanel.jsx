/* eslint-disable no-empty */
/**
 * WorkbenchPanel — Operations Workbench tab.
 *
 * 6 LABS · 8 PHASES · DECISIONS · RISKS · MATERIALS · TOOLS
 *
 * Each Lab has an OPEN LAB button that triggers the real backend workflow:
 *   • OP-01 · Market Analysis → LLM + PDF download (real reportlab output)
 *   • OP-02 · Financial Modeling → 3-archetype ROI w/ NPV + sensitivity
 *   • OP-06 · Business Research → real FMCSA-anchored MN freight seed
 *   • OP-03/04/05 · Scaffolded — return the deliverable plan, full gen later
 */
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "./Brackets";
import { JadeWorking } from "./JadeAvatar";

const SEV_COLORS = { LOW: "#ccff00", MEDIUM: "#ffce4f", HIGH: "#ff7e3b", CRITICAL: "#ff3b8a" };
const STATUS_COLORS = { open: "#ffce4f", mitigated: "#ccff00", accepted: "#7c5cff", transferred: "#00ffff", closed: "rgba(255,255,255,0.4)" };

function Stat({ k, v, c, sub }) {
    return (
        <div className="border px-4 py-3" style={{ borderColor: `${c}33`, background: `${c}08` }}>
            <div className="mono-label text-[10px]" style={{ color: c }}>{k}</div>
            <div className="font-display font-black text-2xl mt-1" style={{ color: c }}>{v}</div>
            {sub && <div className="font-mono-tech text-[10px] text-white/40 mt-1">{sub}</div>}
        </div>
    );
}

function OperationsGrid({ ops, onOpen }) {
    return (
        <div className="grid lg:grid-cols-2 gap-4" data-testid="ops-grid">
            {ops.map((o) => (
                <div key={o.id} className="deck-card relative p-5" style={{ borderColor: `${o.color}55` }} data-testid={`op-card-${o.id}`}>
                    <CornerBrackets />
                    <div className="flex items-baseline justify-between gap-3">
                        <span className="mono-label text-[11px]" style={{ color: o.color }}>{o.id} · {o.code}</span>
                        <span className="mono-label text-[10px]" style={{ color: o.depth === "full" ? "#ccff00" : "#ffce4f" }}>
                            {o.depth === "full" ? "● FULL LAB" : "○ SCAFFOLD"}
                        </span>
                    </div>
                    <h3 className="font-display font-black text-white text-lg mt-2 leading-snug">{o.title}</h3>
                    <p className="font-mono-tech text-[11px] text-white/65 mt-2 leading-relaxed">{o.deliverable}</p>
                    <button data-testid={`op-open-${o.id}`} onClick={() => onOpen(o)}
                        className="btn-jade text-xs mt-4 w-full inline-flex items-center justify-center gap-2"
                        style={{ background: o.color, color: "#0a0c18" }}>
                        → OPEN LAB
                    </button>
                </div>
            ))}
        </div>
    );
}

function LabOP01({ onBack }) {
    const [data, setData] = useState(null);
    const [busy, setBusy] = useState(false);
    const [runs, setRuns] = useState([]);
    const loadRuns = async () => {
        try { const { data } = await api.get("/workbench/labs/OP-01/runs"); setRuns(data.runs || []); } catch {}
    };
    useEffect(() => { loadRuns(); }, []);
    const run = async () => {
        setBusy(true);
        try {
            const { data } = await api.post("/workbench/labs/op-01/run", null, { timeout: 120000 });
            setData(data);
            toast.success(`Market analysis · ${data.section_count} sections · PDF ready`);
            loadRuns();
        } catch (e) { toast.error(e?.response?.data?.detail || "Run failed."); }
        finally { setBusy(false); }
    };
    const download = async (runId) => {
        try {
            const tok = localStorage.getItem("jade_token");
            const url = `${process.env.REACT_APP_BACKEND_URL}/api/workbench/labs/op-01/download/${runId}`;
            const r = await fetch(url, { headers: { Authorization: `Bearer ${tok}` } });
            if (!r.ok) throw new Error("download failed");
            const blob = await r.blob();
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = `jadeos_market_analysis_${runId.slice(0, 8)}.pdf`;
            a.click();
        } catch { toast.error("Download failed."); }
    };
    return (
        <div className="space-y-4" data-testid="lab-op-01">
            <div className="flex items-center justify-between">
                <h2 className="font-display font-black text-white text-2xl">OP-01 · MARKET_ANALYSIS</h2>
                <button data-testid="lab-back-btn" onClick={onBack} className="btn-ghost text-xs">← BACK</button>
            </div>
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="mono-label text-[#ccff00]">DEEP-DIVE · MINNESOTA FREIGHT INDUSTRY</div>
                <p className="font-mono-tech text-[11px] text-white/65 mt-2 leading-relaxed">
                    LLM-generated 3–5 page analysis with cited public sources (ATA · ATRI · BLS · MN DOT · McKinsey). Outputs a downloadable PDF.
                </p>
                <button data-testid="lab-op01-run-btn" onClick={run} disabled={busy} className="btn-jade text-xs mt-4 disabled:opacity-50">
                    {busy ? "GENERATING (60-90s)…" : "▶ RUN ANALYSIS · GENERATE PDF"}
                </button>
            </div>
            {data && (
                <div className="deck-card p-5 relative" data-testid="lab-op01-result">
                    <CornerBrackets />
                    <div className="flex justify-between items-baseline flex-wrap gap-2">
                        <div className="mono-label text-[#ccff00]">✓ COMPLETED · {data.section_count} SECTIONS</div>
                        <button onClick={() => download(data.id)} className="btn-jade text-xs px-4">↓ DOWNLOAD PDF</button>
                    </div>
                    <div className="mt-4 space-y-3 max-h-[420px] overflow-y-auto">
                        {data.sections.map((s, i) => (
                            <div key={i} className="border border-white/10 p-3">
                                <div className="font-display font-bold text-[#ccff00] text-sm">{s.title}</div>
                                <div className="font-mono-tech text-[10.5px] text-white/85 mt-1 leading-relaxed whitespace-pre-line">{s.body}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
            {runs.length > 0 && (
                <div className="deck-card relative" data-testid="lab-op01-history">
                    <CornerBrackets />
                    <div className="px-5 py-3 border-b border-white/10 mono-label text-[#7c5cff]">RUN HISTORY · {runs.length}</div>
                    <div className="divide-y divide-white/5 max-h-[260px] overflow-y-auto">
                        {runs.map((r) => (
                            <div key={r.id} className="px-5 py-2 flex justify-between items-center gap-3 text-[11px] font-mono-tech text-white/85">
                                <span>{new Date(r.completed_at).toLocaleString()}</span>
                                <span className="text-[#ccff00]">{r.section_count} sections</span>
                                <button onClick={() => download(r.id)} className="text-[#00ffff] hover:underline">↓ PDF</button>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

function LabOP02({ onBack }) {
    const [archetype, setArchetype] = useState("mid_market");
    const [fleet, setFleet] = useState(0);
    const [data, setData] = useState(null);
    const [busy, setBusy] = useState(false);
    const run = async () => {
        setBusy(true);
        try {
            const { data } = await api.post("/workbench/labs/op-02/run", { archetype, fleet_size: fleet || 0 });
            setData(data);
        } catch (e) { toast.error(e?.response?.data?.detail || "Model failed."); }
        finally { setBusy(false); }
    };
    useEffect(() => { run(); }, [archetype]);
    return (
        <div className="space-y-4" data-testid="lab-op-02">
            <div className="flex items-center justify-between">
                <h2 className="font-display font-black text-white text-2xl">OP-02 · FINANCIAL_MODELING</h2>
                <button data-testid="lab-back-btn" onClick={onBack} className="btn-ghost text-xs">← BACK</button>
            </div>
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="grid lg:grid-cols-[1fr_180px_140px] gap-3 items-end">
                    <div>
                        <label className="mono-label text-[10px] text-white/55">ARCHETYPE</label>
                        <select data-testid="op02-archetype" value={archetype} onChange={(e) => setArchetype(e.target.value)} className="input-tech text-xs w-full mt-1">
                            <option value="small_regional">SMALL REGIONAL · 25-75 TRUCKS</option>
                            <option value="mid_market">MID-MARKET · 100-250 TRUCKS</option>
                            <option value="specialized_hazmat">SPECIALIZED / HAZMAT · 50-150</option>
                        </select>
                    </div>
                    <div>
                        <label className="mono-label text-[10px] text-white/55">FLEET OVERRIDE · OPTIONAL</label>
                        <input data-testid="op02-fleet" type="number" value={fleet} onChange={(e) => setFleet(parseInt(e.target.value || 0))} className="input-tech text-xs w-full mt-1" />
                    </div>
                    <button data-testid="op02-run-btn" onClick={run} disabled={busy} className="btn-jade text-xs disabled:opacity-50">{busy ? "MODELING…" : "▶ RECOMPUTE"}</button>
                </div>
            </div>
            {data && (
                <>
                    <div className="grid sm:grid-cols-3 gap-3" data-testid="op02-result">
                        <Stat k="ANNUAL SAVINGS" v={`$${data.model.annual_total_savings_usd.toLocaleString()}`} c="#ccff00" />
                        <Stat k="3-YR NPV @ 10%" v={`$${data.model.three_year.npv_at_10pct_discount_usd.toLocaleString()}`} c="#00ffff" sub="net of license + setup" />
                        <Stat k="PAYBACK" v={data.model.three_year.payback_months ? `${data.model.three_year.payback_months}mo` : "—"} c="#7c5cff" />
                    </div>
                    <div className="deck-card p-5 relative">
                        <CornerBrackets />
                        <div className="mono-label text-[#ccff00] mb-3">BREAKDOWN · 6 COST-SAVINGS CATEGORIES</div>
                        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
                            {Object.entries(data.model.by_category_usd).map(([k, v]) => (
                                <div key={k} className="border border-white/10 p-3">
                                    <div className="mono-label text-[10px] text-white/55">{k.replace(/_usd$/, "").replace(/_/g, " ").toUpperCase()}</div>
                                    <div className="font-display font-bold text-[#ccff00] text-lg mt-1">${v.toLocaleString()}</div>
                                </div>
                            ))}
                        </div>
                        <div className="mt-4 pt-3 border-t border-white/5">
                            <div className="mono-label text-[10px] text-[#ffce4f]">SENSITIVITY ± 10%</div>
                            <div className="grid sm:grid-cols-3 gap-2 mt-2">
                                <div className="border border-white/10 p-2"><div className="mono-label text-[9px] text-white/55">CONSERVATIVE</div><div className="font-mono-tech text-sm text-white/85">${data.model.sensitivity.conservative_neg10pct_annual_usd.toLocaleString()}</div></div>
                                <div className="border border-white/10 p-2"><div className="mono-label text-[9px] text-[#ccff00]">BASE</div><div className="font-mono-tech text-sm text-[#ccff00]">${data.model.sensitivity.base_annual_usd.toLocaleString()}</div></div>
                                <div className="border border-white/10 p-2"><div className="mono-label text-[9px] text-white/55">OPTIMISTIC</div><div className="font-mono-tech text-sm text-white/85">${data.model.sensitivity.optimistic_plus10pct_annual_usd.toLocaleString()}</div></div>
                            </div>
                        </div>
                        <div className="mt-4 pt-3 border-t border-white/5 font-mono-tech text-[10px] text-white/55 leading-snug">
                            <div className="mono-label text-[10px] text-[#7c5cff] mb-1">SOURCES · {data.model.sources.length}</div>
                            <ul className="space-y-0.5">{data.model.sources.map((s, i) => <li key={i}>· {s}</li>)}</ul>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

function LabOP06({ onBack }) {
    const [data, setData] = useState(null);
    const [busy, setBusy] = useState(false);
    const run = async () => {
        setBusy(true);
        try {
            const { data } = await api.post("/workbench/labs/op-06/run");
            setData(data);
            toast.success(`Seeded · ${data.inserted} new + ${data.updated} refreshed (${data.count} total)`);
        } catch (e) { toast.error(e?.response?.data?.detail || "Seed failed."); }
        finally { setBusy(false); }
    };
    useEffect(() => { run(); }, []);
    return (
        <div className="space-y-4" data-testid="lab-op-06">
            <div className="flex items-center justify-between">
                <h2 className="font-display font-black text-white text-2xl">OP-06 · BUSINESS_RESEARCH</h2>
                <button data-testid="lab-back-btn" onClick={onBack} className="btn-ghost text-xs">← BACK</button>
            </div>
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="flex items-center justify-between flex-wrap gap-3">
                    <div>
                        <div className="mono-label text-[#00ffff]">TARGET COMPANY LIST · MN FREIGHT · FMCSA-ANCHORED</div>
                        <p className="font-mono-tech text-[11px] text-white/65 mt-1">Every entry has a verifiable DOT# / MC# at safer.fmcsa.dot.gov.</p>
                    </div>
                    <button data-testid="op06-rerun-btn" onClick={run} disabled={busy} className="btn-jade text-xs disabled:opacity-50">{busy ? "SEEDING…" : "↻ REFRESH"}</button>
                </div>
            </div>
            {data && (
                <div className="deck-card relative" data-testid="op06-result">
                    <CornerBrackets />
                    <div className="px-5 py-3 border-b border-white/10 flex justify-between flex-wrap">
                        <div className="mono-label text-[#ccff00]">{data.count} COMPANIES · ALL VERIFIABLE</div>
                        <span className="font-mono-tech text-[10px] text-white/55">{data.inserted} added · {data.updated} refreshed</span>
                    </div>
                    <div className="divide-y divide-white/5 max-h-[480px] overflow-y-auto">
                        {data.companies.map((c) => (
                            <div key={c.id} className="px-5 py-3 grid grid-cols-[1fr_140px_140px_120px] gap-3 items-center">
                                <div>
                                    <div className="font-display font-bold text-white text-sm">{c.company}</div>
                                    <div className="font-mono-tech text-[10px] text-white/55">{c.city}{c.state ? `, ${c.state}` : ""} · {c.industry}</div>
                                    {c.website && <a href={c.website} target="_blank" rel="noreferrer" className="font-mono-tech text-[10px] text-[#00ffff] hover:underline">{c.website}</a>}
                                </div>
                                <span className="mono-label text-[10px] text-[#00ffff]">DOT {c.dot_number || "—"}</span>
                                <span className="mono-label text-[10px] text-[#ccff00]">{c.mc_number || "—"}</span>
                                <span className="font-mono-tech text-[10px] text-white/55">{c.company_size || "—"}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

function LabOP03({ onBack }) {
    const [data, setData] = useState(null);
    const [busy, setBusy] = useState(false);
    const run = async () => {
        setBusy(true);
        try {
            const { data } = await api.post("/workbench/labs/op-03/run");
            setData(data);
        } catch (e) { toast.error(e?.response?.data?.detail || "Run failed."); }
        finally { setBusy(false); }
    };
    useEffect(() => { run(); }, []);
    return (
        <div className="space-y-4" data-testid="lab-op-03">
            <div className="flex items-center justify-between">
                <h2 className="font-display font-black text-white text-2xl">OP-03 · AI_SYSTEMS_ARCHITECTURE</h2>
                <button data-testid="lab-back-btn" onClick={onBack} className="btn-ghost text-xs">← BACK</button>
            </div>
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="mono-label text-[#7c5cff]">SIX AGENT MODULES · DATA PIPELINE · SWIMLANES · API SURFACE</div>
                <p className="font-mono-tech text-[11px] text-white/65 mt-1">Operator-grade reference architecture — every module includes inputs, decision logic, autonomy level, KPI band.</p>
                <button onClick={run} disabled={busy} className="btn-jade text-xs mt-3 disabled:opacity-50">{busy ? "..." : "↻ RECOMPUTE"}</button>
            </div>
            {data && (
                <>
                    <div className="deck-card p-5 relative" data-testid="op03-modules">
                        <CornerBrackets />
                        <div className="mono-label text-[#ccff00] mb-3">MODULES · {data.architecture.modules.length}</div>
                        <div className="grid lg:grid-cols-2 gap-3">
                            {data.architecture.modules.map((m) => (
                                <div key={m.id} className="border border-white/10 p-3 space-y-1.5">
                                    <div className="flex justify-between items-baseline gap-2">
                                        <span className="font-display font-black text-white text-sm">{m.id} · {m.name}</span>
                                        <span className="mono-label text-[10px] text-[#ccff00]">{m.autonomy}</span>
                                    </div>
                                    <div className="font-mono-tech text-[10px] text-white/55">IN · {m.inputs.join(" · ")}</div>
                                    <div className="font-mono-tech text-[10px] text-white/55">OUT · {m.outputs.join(" · ")}</div>
                                    <div className="font-mono-tech text-[10.5px] text-[#7c5cff]">LOGIC · {m.decision_logic}</div>
                                    <div className="font-mono-tech text-[10.5px] text-[#ccff00]">KPI · {m.kpi}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="grid lg:grid-cols-2 gap-3">
                        <div className="deck-card p-5 relative">
                            <CornerBrackets />
                            <div className="mono-label text-[#00ffff] mb-2">DATA PIPELINE</div>
                            {data.architecture.data_pipeline.map((s, i) => (
                                <div key={i} className="border-l-2 border-[#00ffff44] pl-3 py-1.5">
                                    <div className="font-display font-bold text-white text-sm">{s.stage}</div>
                                    <div className="font-mono-tech text-[10px] text-white/65">{s.items.join(" · ")}</div>
                                </div>
                            ))}
                        </div>
                        <div className="deck-card p-5 relative">
                            <CornerBrackets />
                            <div className="mono-label text-[#ff3b8a] mb-2">SWIMLANES</div>
                            {data.architecture.swimlanes.map((s, i) => (
                                <div key={i} className="border-l-2 border-[#ff3b8a44] pl-3 py-1.5">
                                    <div className="font-display font-bold text-white text-sm">{s.lane}</div>
                                    <div className="font-mono-tech text-[10px] text-white/65">{s.events.join(" → ")}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="deck-card p-5 relative" data-testid="op03-api">
                        <CornerBrackets />
                        <div className="mono-label text-[#ffce4f] mb-2">API SURFACE</div>
                        <div className="divide-y divide-white/5">
                            {data.architecture.api_surface.map((a, i) => (
                                <div key={i} className="py-1.5 grid grid-cols-[60px_1fr_100px] gap-2 text-[10.5px] font-mono-tech">
                                    <span className="text-[#ccff00]">{a.method}</span>
                                    <span className="text-white">{a.path}</span>
                                    <span className="text-white/55">{a.purpose}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

function LabOP04({ onBack }) {
    const [data, setData] = useState(null);
    const [busy, setBusy] = useState(false);
    const run = async () => {
        setBusy(true);
        try {
            const { data } = await api.post("/workbench/labs/op-04/run");
            setData(data);
            toast.success(`Deck · ${data.slide_count} slides · ${data.factsheet_count} fact sheets · PDF ready`);
        } catch (e) { toast.error(e?.response?.data?.detail || "Run failed."); }
        finally { setBusy(false); }
    };
    useEffect(() => { run(); }, []);
    const download = async () => {
        try {
            const tok = localStorage.getItem("jade_token");
            const r = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/workbench/labs/op-04/download/${data.id}`,
                { headers: { Authorization: `Bearer ${tok}` } });
            if (!r.ok) throw new Error();
            const blob = await r.blob();
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = `jadeos_pitch_deck_${data.id.slice(0, 8)}.pdf`;
            a.click();
        } catch { toast.error("Download failed."); }
    };
    return (
        <div className="space-y-4" data-testid="lab-op-04">
            <div className="flex items-center justify-between">
                <h2 className="font-display font-black text-white text-2xl">OP-04 · SALES_COLLATERAL</h2>
                <button data-testid="lab-back-btn" onClick={onBack} className="btn-ghost text-xs">← BACK</button>
            </div>
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="mono-label text-[#ff3b8a]">PITCH DECK · FACT SHEETS · READINESS · COMPETITIVE BRIEF</div>
                <div className="flex gap-2 mt-3 flex-wrap">
                    <button onClick={run} disabled={busy} className="btn-jade text-xs disabled:opacity-50">{busy ? "BUILDING…" : "↻ REBUILD"}</button>
                    {data && <button onClick={download} className="btn-jade text-xs" style={{ background: "#ff3b8a" }}>↓ DOWNLOAD 12-SLIDE DECK · PDF</button>}
                </div>
            </div>
            {data && (
                <>
                    <div className="deck-card p-5 relative" data-testid="op04-slides">
                        <CornerBrackets />
                        <div className="mono-label text-[#ccff00] mb-3">DECK · {data.slide_count} SLIDES</div>
                        <div className="grid lg:grid-cols-2 gap-3 max-h-[400px] overflow-y-auto">
                            {data.deck.slides.map((s) => (
                                <div key={s.n} className="border border-white/10 p-3">
                                    <div className="flex justify-between items-baseline">
                                        <span className="mono-label text-[10px] text-[#7c5cff]">SLIDE {s.n} · {s.kind.toUpperCase()}</span>
                                    </div>
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
                    <div className="deck-card p-5 relative" data-testid="op04-factsheets">
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
                    <div className="grid lg:grid-cols-2 gap-3">
                        <div className="deck-card p-5 relative" data-testid="op04-readiness">
                            <CornerBrackets />
                            <div className="mono-label text-[#ffce4f] mb-2">READINESS ASSESSMENT</div>
                            {data.deck.readiness_assessment.map((g, i) => (
                                <div key={i} className="border-l-2 border-[#ffce4f55] pl-3 py-1">
                                    <div className="font-display font-bold text-white text-sm">{g.area}</div>
                                    {g.questions.map((q, j) => (
                                        <div key={j} className="font-mono-tech text-[10.5px] text-white/65">• {q}</div>
                                    ))}
                                </div>
                            ))}
                        </div>
                        <div className="deck-card p-5 relative" data-testid="op04-competitive">
                            <CornerBrackets />
                            <div className="mono-label text-[#7c5cff] mb-2">COMPETITIVE BRIEF</div>
                            {Object.entries(data.deck.competitive_brief).map(([k, v]) => (
                                <div key={k} className="border-l-2 border-[#7c5cff55] pl-3 py-1">
                                    <div className="mono-label text-[10px] text-[#7c5cff]">{k.replace(/_/g, " ").toUpperCase()}</div>
                                    <div className="font-mono-tech text-[10.5px] text-white/85 mt-0.5">{v}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

function LabOP05({ onBack }) {
    const [data, setData] = useState(null);
    const [busy, setBusy] = useState(false);
    const run = async () => {
        setBusy(true);
        try {
            const { data } = await api.post("/workbench/labs/op-05/run");
            setData(data);
            toast.success(`Brief · ${data.section_count} sections · PDF ready`);
        } catch (e) { toast.error(e?.response?.data?.detail || "Run failed."); }
        finally { setBusy(false); }
    };
    useEffect(() => { run(); }, []);
    const download = async () => {
        try {
            const tok = localStorage.getItem("jade_token");
            const r = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/workbench/labs/op-05/download/${data.id}`,
                { headers: { Authorization: `Bearer ${tok}` } });
            if (!r.ok) throw new Error();
            const blob = await r.blob();
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = `jadeos_technical_brief_${data.id.slice(0, 8)}.pdf`;
            a.click();
        } catch { toast.error("Download failed."); }
    };
    return (
        <div className="space-y-4" data-testid="lab-op-05">
            <div className="flex items-center justify-between">
                <h2 className="font-display font-black text-white text-2xl">OP-05 · DOCUMENTS</h2>
                <button data-testid="lab-back-btn" onClick={onBack} className="btn-ghost text-xs">← BACK</button>
            </div>
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="mono-label text-[#ffce4f]">20–30 PAGE TECHNICAL BRIEF · ALL SECTIONS BENCHMARK-TRACEABLE</div>
                <div className="flex gap-2 mt-3 flex-wrap">
                    <button onClick={run} disabled={busy} className="btn-jade text-xs disabled:opacity-50">{busy ? "BUILDING…" : "↻ REBUILD"}</button>
                    {data && <button onClick={download} className="btn-jade text-xs" style={{ background: "#ffce4f", color: "#0a0c18" }}>↓ DOWNLOAD BRIEF · PDF</button>}
                </div>
            </div>
            {data && (
                <div className="deck-card p-5 relative" data-testid="op05-sections">
                    <CornerBrackets />
                    <div className="mono-label text-[#ccff00] mb-3">SECTIONS · {data.section_count}</div>
                    <div className="space-y-3 max-h-[520px] overflow-y-auto">
                        {data.sections.map((s, i) => (
                            <div key={i} className="border border-white/10 p-3">
                                <div className="font-display font-bold text-[#ffce4f] text-sm">{s.title}</div>
                                <div className="font-mono-tech text-[10.5px] text-white/85 mt-1 leading-relaxed whitespace-pre-line">{s.body}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

function LabScaffold({ op, onBack }) {
    const [data, setData] = useState(null);
    const [busy, setBusy] = useState(false);
    const run = async () => {
        setBusy(true);
        try {
            const { data } = await api.post(`/workbench/labs/${op.id.toLowerCase()}/run`);
            setData(data);
        } catch (e) { toast.error(e?.response?.data?.detail || "Run failed."); }
        finally { setBusy(false); }
    };
    useEffect(() => { run(); }, []);
    return (
        <div className="space-y-4" data-testid={`lab-${op.id}`}>
            <div className="flex items-center justify-between">
                <h2 className="font-display font-black text-white text-2xl">{op.id} · {op.code}</h2>
                <button onClick={onBack} className="btn-ghost text-xs">← BACK</button>
            </div>
            <div className="deck-card p-5 relative" style={{ borderColor: `${op.color}55` }}>
                <CornerBrackets />
                <div className="mono-label text-[#ffce4f]">○ SCAFFOLDED LAB</div>
                <h3 className="font-display font-black text-white text-xl mt-2">{op.title}</h3>
                <p className="font-mono-tech text-[12px] text-white/85 mt-3 leading-relaxed">{op.deliverable}</p>
                {data && (
                    <div className="mt-4 pt-3 border-t border-white/5 font-mono-tech text-[11px] text-[#ffce4f] leading-relaxed">
                        ▸ {data.note}
                    </div>
                )}
                <button onClick={run} disabled={busy} className="btn-jade text-xs mt-4 disabled:opacity-50">{busy ? "..." : "↻ RE-LOG SCAFFOLD"}</button>
            </div>
        </div>
    );
}

function DecisionsTracker({ decisions, onFlip }) {
    return (
        <div className="deck-card relative" data-testid="decisions-tracker">
            <CornerBrackets />
            <div className="px-5 py-3 border-b border-white/10 mono-label text-[#ff3b8a]">DECISIONS · {decisions.length}</div>
            <div className="divide-y divide-white/5">
                {decisions.map((d) => (
                    <div key={d.id} className="px-5 py-4" data-testid={`decision-${d.id}`}>
                        <div className="flex items-baseline justify-between gap-3 flex-wrap">
                            <span className="font-display font-bold text-white text-sm">{d.id} · {d.title}</span>
                            <span className="mono-label text-[10px]" style={{ color: d.status === "decided" ? "#ccff00" : d.status === "deferred" ? "#ffce4f" : "#ff3b8a" }}>{d.status.toUpperCase()}</span>
                        </div>
                        <p className="font-mono-tech text-[11px] text-white/65 mt-1 leading-relaxed">{d.context}</p>
                        <p className="font-mono-tech text-[11px] text-[#ccff00] mt-1 leading-relaxed">▸ {d.recommendation}</p>
                        <div className="flex flex-wrap gap-2 mt-3">
                            {d.options.map((opt) => (
                                <button key={opt} data-testid={`decision-${d.id}-opt-${opt}`} onClick={() => onFlip(d.id, opt)}
                                    className="mono-label text-[10px] px-3 py-1.5"
                                    style={{
                                        border: `1px solid ${d.choice === opt ? "#ccff00" : "rgba(255,255,255,0.10)"}`,
                                        color: d.choice === opt ? "#ccff00" : "rgba(255,255,255,0.55)",
                                        background: d.choice === opt ? "#ccff0011" : "transparent",
                                    }}>{opt.toUpperCase().replace(/_/g, " ")}</button>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

function RisksRegister({ risks, onUpdate }) {
    return (
        <div className="deck-card relative" data-testid="risks-register">
            <CornerBrackets />
            <div className="px-5 py-3 border-b border-white/10 mono-label text-[#ffce4f]">RISKS · {risks.length}</div>
            <div className="divide-y divide-white/5">
                {risks.map((r) => (
                    <div key={r.id} className="px-5 py-3" data-testid={`risk-${r.id}`}>
                        <div className="flex items-baseline justify-between gap-3 flex-wrap">
                            <div className="flex items-baseline gap-2">
                                <span className="mono-label text-[10px]" style={{ color: SEV_COLORS[r.severity] }}>● {r.severity}</span>
                                <span className="font-mono-tech text-[11px] text-white/85">{r.id}</span>
                            </div>
                            <span className="mono-label text-[10px]" style={{ color: STATUS_COLORS[r.status] }}>{r.status.toUpperCase()}</span>
                        </div>
                        <p className="font-mono-tech text-[11px] text-white/85 mt-1 leading-relaxed">{r.text}</p>
                        <div className="flex gap-2 mt-2">
                            {r.status === "open" && <button data-testid={`risk-${r.id}-mitigate`} onClick={() => onUpdate(r.id, { status: "mitigated" })} className="mono-label text-[10px] text-[#ccff00] hover:underline">→ MITIGATED</button>}
                            {r.status === "open" && <button data-testid={`risk-${r.id}-accept`} onClick={() => onUpdate(r.id, { status: "accepted" })} className="mono-label text-[10px] text-[#7c5cff] hover:underline">→ ACCEPTED</button>}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

function PhasesView({ phases, onStepUpdate }) {
    const STATUS_META = {
        todo: { sym: "○", c: "rgba(255,255,255,0.45)", lbl: "TODO" },
        in_progress: { sym: "▸", c: "#00ffff", lbl: "ACTIVE" },
        done: { sym: "✓", c: "#ccff00", lbl: "DONE" },
        blocked: { sym: "✗", c: "#ff3b8a", lbl: "BLOCKED" },
    };
    const NEXT_STATUS = { todo: "in_progress", in_progress: "done", done: "todo", blocked: "in_progress" };
    const totalSteps = phases.reduce((a, p) => a + (p.steps || []).length, 0);
    const totalHours = phases.reduce((a, p) => a + (p.steps || []).reduce((b, s) => b + (s.hours || 0), 0), 0);
    const totalDone = phases.reduce((a, p) => a + (p.steps || []).filter((s) => s.status === "done").length, 0);
    return (
        <div className="space-y-4" data-testid="phases-view">
            <div className="grid sm:grid-cols-4 gap-3">
                <Stat k="PHASES" v={phases.length} c="#7c5cff" />
                <Stat k="SUBSTEPS" v={totalSteps} c="#00ffff" sub={`${totalDone} done`} />
                <Stat k="HOURS · BUDGET" v={`${totalHours}h`} c="#ccff00" sub={`~${(totalHours / 8).toFixed(1)} days`} />
                <Stat k="COMPLETE" v={`${totalSteps ? Math.round((totalDone / totalSteps) * 100) : 0}%`} c="#ff3b8a" />
            </div>
            {phases.map((p) => {
                const pSteps = p.steps || [];
                const pDone = pSteps.filter((s) => s.status === "done").length;
                const pHours = pSteps.reduce((b, s) => b + (s.hours || 0), 0);
                const pct = pSteps.length ? Math.round((pDone / pSteps.length) * 100) : 0;
                return (
                    <div key={p.n} className="deck-card relative" data-testid={`phase-${p.n}`}>
                        <CornerBrackets />
                        <div className="px-5 py-4 border-b border-white/10">
                            <div className="flex items-baseline justify-between flex-wrap gap-2">
                                <div>
                                    <div className="mono-label text-[10px] text-[#7c5cff]">PHASE {p.n}</div>
                                    <h3 className="font-display font-black text-white text-lg leading-tight mt-0.5">{p.title}</h3>
                                </div>
                                <div className="flex flex-wrap items-baseline gap-3 text-[10px] font-mono-tech">
                                    <span className="text-white/55">DURATION · {p.duration}</span>
                                    {p.owner && <span className="text-white/55">OWNER · {p.owner}</span>}
                                    <span className="text-white/55">{pSteps.length} STEPS · {pHours}h</span>
                                    {p.op_link && (
                                        <a href={`#lab-${p.op_link}`} className="mono-label text-[10px] text-[#ccff00] hover:underline">{p.op_link_label || `→ ${p.op_link}`}</a>
                                    )}
                                </div>
                            </div>
                            {p.outcome && (
                                <p className="font-mono-tech text-[11px] text-white/70 mt-2 leading-relaxed border-l-2 border-[#ccff0055] pl-3">
                                    <span className="mono-label text-[9px] text-[#ccff00] mr-2">OUTCOME</span>{p.outcome}
                                </p>
                            )}
                            <div className="mt-3 flex items-center gap-2">
                                <div className="flex-1 h-1.5 bg-white/5 overflow-hidden">
                                    <div className="h-full" style={{ width: `${pct}%`, background: pct >= 100 ? "#ccff00" : pct > 0 ? "#00ffff" : "rgba(255,255,255,0.2)" }} />
                                </div>
                                <span className="mono-label text-[10px] text-white/55">{pct}% · {pDone}/{pSteps.length}</span>
                            </div>
                        </div>
                        <div className="divide-y divide-white/5">
                            {pSteps.map((s, i) => {
                                if (typeof s === "string") return (
                                    <div key={i} className="px-5 py-2 font-mono-tech text-[11px] text-white/65">○ {s}</div>
                                );
                                const meta = STATUS_META[s.status || "todo"];
                                return (
                                    <div key={i} className="px-5 py-3" data-testid={`phase-${p.n}-step-${s.id || i}`}>
                                        <div className="flex items-start gap-3">
                                            <span className="font-mono-tech text-base mt-0.5" style={{ color: meta.c }}>{meta.sym}</span>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-baseline justify-between gap-2 flex-wrap">
                                                    <span className="font-display font-bold text-white text-[12.5px] leading-snug">{s.id ? `${s.id} · ` : ""}{s.text}</span>
                                                    <div className="flex flex-wrap gap-2 items-baseline text-[10px] font-mono-tech">
                                                        {s.hours != null && <span className="mono-label" style={{ color: "#ccff00" }}>{s.hours}h</span>}
                                                        {s.owner && <span className="text-[#7c5cff]">{s.owner.toUpperCase()}</span>}
                                                        {s.op_link && <a href={`#lab-${s.op_link}`} className="text-[#00ffff] hover:underline">→ {s.op_link}</a>}
                                                        <span className="mono-label" style={{ color: meta.c }}>{meta.lbl}</span>
                                                        {onStepUpdate && (
                                                            <button data-testid={`phase-${p.n}-step-${s.id || i}-advance`}
                                                                onClick={() => onStepUpdate(p.n, i, NEXT_STATUS[s.status || "todo"])}
                                                                className="mono-label text-[9px] text-[#ccff00] hover:underline">→ ADVANCE</button>
                                                        )}
                                                    </div>
                                                </div>
                                                {s.deliverable && (
                                                    <div className="font-mono-tech text-[10.5px] text-white/65 mt-1">
                                                        <span className="mono-label text-[9px] text-[#ccff00] mr-1">DELIVERABLE</span>{s.deliverable}
                                                    </div>
                                                )}
                                                {s.exit_criteria && (
                                                    <div className="font-mono-tech text-[10.5px] text-white/65 mt-1">
                                                        <span className="mono-label text-[9px] text-[#00ffff] mr-1">EXIT</span>{s.exit_criteria}
                                                    </div>
                                                )}
                                                {(s.tools || []).length > 0 && (
                                                    <div className="flex flex-wrap gap-1 mt-1.5">
                                                        {s.tools.map((t, j) => (
                                                            <span key={j} className="px-2 py-0.5 mono-label text-[9px] text-white/55 border border-white/10">{t}</span>
                                                        ))}
                                                    </div>
                                                )}
                                                {(s.depends_on || []).length > 0 && (
                                                    <div className="font-mono-tech text-[9.5px] text-white/45 mt-1">
                                                        ⊢ depends · {s.depends_on.join(" · ")}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

function MaterialsTools({ materials, tools }) {
    const COST_COLOR = (c) => c === 0 ? "#ccff00" : c <= 100 ? "#00ffff" : c <= 500 ? "#ffce4f" : "#ff3b8a";
    const totalCost = materials.reduce((a, m) => a + (m.cost_usd || 0), 0);
    const freeCount = materials.filter((m) => m.cost_usd === 0).length;
    const KIND_LABEL = {
        public: "PUBLIC · FREE",
        subscription_or_trial: "SUBSCRIPTION / TRIAL",
        paid_reports: "PAID REPORTS",
        api: "API",
    };
    const CATEGORY_COLOR = {
        business_research: "#00ffff",
        market_analysis: "#7c5cff",
        financial_modeling: "#ccff00",
        ai_systems_architecture: "#ff3b8a",
        sales_collateral: "#ffce4f",
        documents: "#00ffff",
    };
    return (
        <div className="space-y-4" data-testid="materials-tools-dashboard">
            <div className="grid sm:grid-cols-4 gap-3">
                <Stat k="MATERIALS" v={materials.length} c="#00ffff" />
                <Stat k="FREE" v={`${freeCount}/${materials.length}`} c="#ccff00" sub="public sources" />
                <Stat k="STACK COST" v={`$${totalCost}`} c="#ffce4f" sub="one-time + subscription" />
                <Stat k="TOOLS" v={tools.length} c="#7c5cff" sub="operator stack" />
            </div>

            <div className="deck-card relative" data-testid="materials-panel">
                <CornerBrackets />
                <div className="px-5 py-3 border-b border-white/10 flex justify-between items-baseline gap-3 flex-wrap">
                    <div>
                        <div className="mono-label text-[#00ffff]">MATERIALS · {materials.length} SOURCES</div>
                        <p className="font-mono-tech text-[10.5px] text-white/55 mt-1">Curated reference stack · click any source to open</p>
                    </div>
                    <div className="font-mono-tech text-[10px] text-white/45">SORTED · category × cost ↑</div>
                </div>
                <div className="grid sm:grid-cols-2 gap-px bg-white/5">
                    {materials
                        .slice()
                        .sort((a, b) => (a.category || "").localeCompare(b.category) || (a.cost_usd || 0) - (b.cost_usd || 0))
                        .map((m, i) => {
                            const cc = CATEGORY_COLOR[m.category] || "#ccff00";
                            return (
                                <a key={i} href={m.url || "#"} target="_blank" rel="noreferrer"
                                    className="bg-[#0a0c18] px-5 py-4 relative block hover:bg-[#10131e] transition group"
                                    data-testid={`material-${i}`}
                                    style={{ borderLeft: `3px solid ${cc}` }}>
                                    <div className="flex items-baseline justify-between gap-2">
                                        <span className="mono-label text-[10px]" style={{ color: cc }}>{(m.category || "").replace(/_/g, " ").toUpperCase()}</span>
                                        <span className="mono-label text-[10px]" style={{ color: COST_COLOR(m.cost_usd || 0) }}>
                                            {m.cost_usd === 0 ? "● FREE" : `$${m.cost_usd}`}
                                        </span>
                                    </div>
                                    <div className="font-display font-black text-white text-sm mt-1.5 leading-snug group-hover:text-[#ccff00] transition">
                                        {m.name}
                                    </div>
                                    <div className="flex items-baseline justify-between mt-2 flex-wrap gap-2">
                                        <span className="font-mono-tech text-[10px] text-white/45">{KIND_LABEL[m.kind] || (m.kind || "").toUpperCase()}</span>
                                        {m.url && <span className="font-mono-tech text-[10px] text-white/45 truncate max-w-[260px]">↗ {m.url.replace(/^https?:\/\//, "").replace(/\/$/, "")}</span>}
                                    </div>
                                </a>
                            );
                        })}
                </div>
            </div>

            <div className="deck-card relative" data-testid="tools-panel">
                <CornerBrackets />
                <div className="px-5 py-3 border-b border-white/10 flex justify-between items-baseline gap-3 flex-wrap">
                    <div>
                        <div className="mono-label text-[#ccff00]">TOOLS · {tools.length} OPERATOR STACK</div>
                        <p className="font-mono-tech text-[10.5px] text-white/55 mt-1">Software + canvas used to produce each deliverable</p>
                    </div>
                </div>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-px bg-white/5">
                    {tools.map((t, i) => {
                        const cc = CATEGORY_COLOR[t.category] || "#ccff00";
                        return (
                            <div key={i} className="bg-[#0a0c18] px-5 py-4 relative" data-testid={`tool-${i}`}
                                style={{ borderTop: `2px solid ${cc}55` }}>
                                <div className="mono-label text-[10px]" style={{ color: cc }}>{(t.category || "").replace(/_/g, " ").toUpperCase()}</div>
                                <div className="font-display font-bold text-white text-sm mt-1.5 leading-snug">{t.name}</div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}

export default function WorkbenchPanel() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [view, setView] = useState("ops");
    const [openOp, setOpenOp] = useState(null);

    const load = async () => {
        try { const { data } = await api.get("/workbench/overview"); setData(data); }
        catch { toast.error("Workbench load failed."); }
        finally { setLoading(false); }
    };
    useEffect(() => { setLoading(true); load(); }, []);

    const flipDecision = async (id, choice) => {
        try {
            await api.patch(`/workbench/decisions/${id}`, { choice, status: "decided" });
            toast.success(`${id} → ${choice}`);
            load();
        } catch { toast.error("Flip failed."); }
    };

    const updateRisk = async (id, body) => {
        try { await api.patch(`/workbench/risks/${id}`, body); toast.success("Updated"); load(); }
        catch { toast.error("Update failed."); }
    };

    const updateStep = async (n, step_index, status) => {
        try { await api.patch(`/workbench/phases/${n}/steps`, { step_index, status }); load(); }
        catch { toast.error("Step update failed."); }
    };

    if (loading) return <div className="deck-card p-12 flex justify-center"><JadeWorking verb="loading workbench" size={72} /></div>;
    if (!data) return null;

    if (openOp) {
        if (openOp.id === "OP-01") return <LabOP01 onBack={() => { setOpenOp(null); load(); }} />;
        if (openOp.id === "OP-02") return <LabOP02 onBack={() => { setOpenOp(null); load(); }} />;
        if (openOp.id === "OP-03") return <LabOP03 onBack={() => { setOpenOp(null); load(); }} />;
        if (openOp.id === "OP-04") return <LabOP04 onBack={() => { setOpenOp(null); load(); }} />;
        if (openOp.id === "OP-05") return <LabOP05 onBack={() => { setOpenOp(null); load(); }} />;
        if (openOp.id === "OP-06") return <LabOP06 onBack={() => { setOpenOp(null); load(); }} />;
        return <LabScaffold op={openOp} onBack={() => { setOpenOp(null); load(); }} />;
    }

    const VIEWS = [
        { id: "ops", label: `LABS · ${data.summary.ops_total}`, c: "#ccff00" },
        { id: "phases", label: `PHASES · ${data.phases.length}`, c: "#7c5cff" },
        { id: "decisions", label: `DECISIONS · ${data.summary.decisions_pending}/${data.summary.decisions_pending + data.summary.decisions_decided}`, c: "#ff3b8a" },
        { id: "risks", label: `RISKS · ${data.summary.risks_open}`, c: "#ffce4f" },
        { id: "materials", label: "MATERIALS + TOOLS", c: "#00ffff" },
    ];

    return (
        <div className="space-y-6" data-testid="workbench-panel">
            <div className="deck-card p-6 relative">
                <CornerBrackets />
                <SectionLabel idx={0} color="#ccff00">OPERATIONS · WORKBENCH</SectionLabel>
                <h2 className="font-display font-black text-white text-4xl tracking-tighter mt-2">
                    Six Labs. Eight Phases. <span className="accent-cyan">Zero mock data.</span>
                </h2>
                <p className="text-white/65 text-sm mt-3 max-w-2xl leading-relaxed">
                    The full Sales Engineering Operations Workbench — Market Analysis, ROI modeling, AI architecture, sales collateral, technical docs, business research. Each Lab is personally testable; OP-01/02/06 ship live, OP-03/04/05 land as scaffolds.
                </p>
                <div className="grid sm:grid-cols-5 gap-3 mt-5">
                    <Stat k="LABS · FULL" v={`${data.summary.ops_full}/${data.summary.ops_total}`} c="#ccff00" sub="functional today" />
                    <Stat k="PHASES" v={data.phases.length} c="#7c5cff" sub="sequenced" />
                    <Stat k="DECISIONS" v={`${data.summary.decisions_decided}/${data.summary.decisions_decided + data.summary.decisions_pending}`} c="#ff3b8a" sub="decided" />
                    <Stat k="RISKS · OPEN" v={data.summary.risks_open} c="#ffce4f" />
                    <Stat k="DATA POLICY" v="VERIFIED" c="#00ffff" sub="source attribution required" />
                </div>
            </div>

            <div className="flex flex-wrap gap-2">
                {VIEWS.map((v) => {
                    const active = view === v.id;
                    return (
                        <button key={v.id} data-testid={`workbench-view-${v.id}`} onClick={() => setView(v.id)}
                            className="px-4 py-2 mono-label text-[11px] transition"
                            style={{ border: `1px solid ${active ? v.c : "rgba(255,255,255,0.10)"}`,
                                color: active ? v.c : "rgba(255,255,255,0.55)",
                                background: active ? `${v.c}11` : "transparent" }}>{v.label}</button>
                    );
                })}
            </div>

            {view === "ops" && <OperationsGrid ops={data.operations} onOpen={setOpenOp} />}
            {view === "phases" && <PhasesView phases={data.phases} onStepUpdate={updateStep} />}
            {view === "decisions" && <DecisionsTracker decisions={data.decisions} onFlip={flipDecision} />}
            {view === "risks" && <RisksRegister risks={data.risks} onUpdate={updateRisk} />}
            {view === "materials" && <MaterialsTools materials={data.materials} tools={data.tools} />}
        </div>
    );
}
