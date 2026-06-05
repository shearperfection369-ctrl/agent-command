/**
 * CompliancePanel — admin ROUTE TO COMPLIANCE tab.
 *
 * Renders:
 *   • Industry routing matrix (GO NOW · GO WITH ToS · BLOCKED)
 *   • Universal compliance checklist (Privacy Policy / ToS / DPA / SOC 2 / E&O)
 *   • 8-month roadmap with unlocks per milestone
 *   • Per-industry gates with cost estimates so the operator can self-diagnose
 *     "what do I need to spend to unlock vertical X?"
 *
 * Endpoint: GET /api/admin/compliance
 */
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "./Brackets";
import { JadeWorking } from "./JadeAvatar";

const STATUS_COLOR = {
    go_now: "#ccff00",
    go_with_tos: "#ffce4f",
    blocked: "#ff3b8a",
};
const STATUS_LABEL = {
    go_now: "● GO · NO GATE",
    go_with_tos: "◐ GO · WITH ToS",
    blocked: "○ BLOCKED · GATE",
};

function StatusPill({ status }) {
    const c = STATUS_COLOR[status] || "#7c5cff";
    return (
        <span
            data-testid={`compliance-status-${status}`}
            className="mono-label px-2 py-1 border inline-flex items-center"
            style={{ color: c, borderColor: `${c}66`, background: `${c}11` }}
        >{STATUS_LABEL[status] || status}</span>
    );
}

function IndustryCard({ ind }) {
    const c = STATUS_COLOR[ind.status];
    return (
        <div
            data-testid={`compliance-industry-${ind.id}`}
            className="deck-card relative p-5"
            style={{ borderColor: `${c}55` }}
        >
            <CornerBrackets />
            <div className="flex items-start justify-between gap-3 flex-wrap mb-3">
                <div>
                    <div className="font-display font-black text-white text-xl tracking-tight">{ind.label}</div>
                    <div className="font-mono-tech text-[11px] mt-1" style={{ color: c }}>{ind.headline}</div>
                </div>
                <StatusPill status={ind.status} />
            </div>

            <p className="font-mono-tech text-[12px] text-white/75 leading-relaxed">{ind.summary}</p>

            {ind.estimated_market_size_msp && ind.estimated_market_size_msp !== "—" && (
                <div className="mt-3 mono-label text-[10px] text-white/55">
                    MSP MARKET · <span className="text-[#00ffff]">{ind.estimated_market_size_msp}</span>
                </div>
            )}

            {ind.gates?.length > 0 && (
                <div className="mt-4">
                    <div className="mono-label text-[10px] text-[#ff3b8a] mb-2">GATES · {ind.gates.length}</div>
                    <ul className="space-y-1.5">
                        {ind.gates.map((g, i) => (
                            <li key={i} className="font-mono-tech text-[11px] text-white/80 flex justify-between gap-3">
                                <span><span className="text-[#ff3b8a] mr-1">▸</span>{g.label}</span>
                                <span className="text-white/45 text-[10px] whitespace-nowrap">{g.cost_est}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {ind.tos_must_have?.length > 0 && (
                <div className="mt-4 pt-3 border-t border-white/5">
                    <div className="mono-label text-[10px] text-[#7c5cff] mb-2">ToS · MUST INCLUDE</div>
                    <ul className="space-y-1">
                        {ind.tos_must_have.map((t, i) => (
                            <li key={i} className="font-mono-tech text-[11px] text-white/70 leading-snug">
                                <span className="text-[#7c5cff] mr-1">·</span>{t}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {ind.unlock_path && (
                <div className="mt-3 pt-3 border-t border-white/5 font-mono-tech text-[11px] text-[#ffce4f] leading-snug">
                    <span className="mono-label text-[10px] block mb-1">UNLOCK PATH</span>
                    {ind.unlock_path}
                </div>
            )}
            {ind.expansion_path && (
                <div className="mt-3 pt-3 border-t border-white/5 font-mono-tech text-[11px] text-[#00ffff] leading-snug">
                    <span className="mono-label text-[10px] block mb-1">EXPANSION PATH</span>
                    {ind.expansion_path}
                </div>
            )}
        </div>
    );
}

function UniversalRow({ req }) {
    const color = req.status === "milestone" ? "#7c5cff" : "#ccff00";
    return (
        <div
            data-testid={`compliance-req-${req.id}`}
            className="grid grid-cols-[1fr_120px_140px] gap-3 items-center px-4 py-3 border-b border-white/5"
        >
            <div>
                <div className="font-display font-bold text-white text-sm">{req.label}</div>
                <div className="font-mono-tech text-[11px] text-white/55 mt-1 leading-snug">{req.purpose}</div>
            </div>
            <div className="text-right">
                <div className="mono-label text-[10px]" style={{ color }}>{req.priority}</div>
                <div className="font-mono-tech text-[10px] text-white/55 mt-1">{req.cost_est}</div>
            </div>
            <div className="text-right">
                <div className="mono-label text-[10px] text-white/40">EFFORT</div>
                <div className="font-mono-tech text-sm mt-1" style={{ color }}>{req.effort_weeks ? `${req.effort_weeks}w` : "—"}</div>
            </div>
        </div>
    );
}

function RoadmapCard({ phase }) {
    return (
        <div
            data-testid={`compliance-roadmap-${phase.month}`}
            className="deck-card relative p-5"
            style={{ borderTop: `2px solid ${phase.color}` }}
        >
            <CornerBrackets />
            <div className="font-display font-black text-2xl" style={{ color: phase.color }}>{phase.month}</div>
            <div className="mono-label text-white/55 text-[10px] mt-1">{phase.label}</div>

            <div className="mt-4">
                <div className="mono-label text-[10px] text-[#00ffff] mb-2">ACTIONS</div>
                <ul className="space-y-1.5">
                    {phase.actions.map((a, i) => (
                        <li key={i} className="font-mono-tech text-[11px] text-white/80 flex gap-2 leading-snug">
                            <span style={{ color: phase.color }}>▸</span><span>{a}</span>
                        </li>
                    ))}
                </ul>
            </div>

            <div className="mt-4 pt-3 border-t border-white/5">
                <div className="mono-label text-[10px] text-[#ccff00] mb-2">UNLOCKS</div>
                <ul className="space-y-1">
                    {phase.unlocks.map((u, i) => (
                        <li key={i} className="font-mono-tech text-[11px] text-[#ccff00]/90 flex gap-2 leading-snug">
                            <span>✓</span><span>{u}</span>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}

export default function CompliancePanel() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState("ALL");

    const load = async () => {
        setLoading(true);
        try {
            const { data } = await api.get("/admin/compliance");
            setData(data);
        } catch (e) {
            toast.error("Failed to load compliance routing");
        } finally { setLoading(false); }
    };

    useEffect(() => { load(); }, []);

    if (loading) {
        return <div className="deck-card p-12 flex justify-center"><JadeWorking verb="building compliance routing" size={72} /></div>;
    }
    if (!data) return null;

    const filterMap = { go_now: "go_now", go_with_tos: "go_with_tos", blocked: "blocked" };
    const filtered = filter === "ALL" ? data.industries : data.industries.filter((i) => i.status === filterMap[filter]);

    return (
        <div className="space-y-6" data-testid="compliance-panel">
            {/* HERO */}
            <div className="deck-card p-6 relative" data-testid="compliance-hero">
                <CornerBrackets />
                <SectionLabel idx={0} color="#7c5cff">ROUTE · TO · FULL COMPLIANCE</SectionLabel>
                <h2 className="font-display font-black text-white text-4xl tracking-tighter mt-2">
                    Sell what you <span className="accent-cyan">can.</span> <span className="text-white/35">Build the rest in parallel.</span>
                </h2>
                <p className="text-white/65 text-sm mt-3 max-w-3xl leading-relaxed">{data.subtitle}</p>

                <div className="grid sm:grid-cols-4 gap-4 mt-6">
                    <Stat k="INDUSTRIES" v={data.summary.total_industries} c="#fff" />
                    <Stat k="GO · NOW" v={data.summary.go_now} c="#ccff00" />
                    <Stat k="GO · ToS" v={data.summary.go_with_tos} c="#ffce4f" />
                    <Stat k="BLOCKED" v={data.summary.blocked} c="#ff3b8a" />
                </div>
            </div>

            {/* HEADLINE PRINCIPLES */}
            <div className="deck-card p-6 relative" data-testid="compliance-principles">
                <CornerBrackets />
                <div className="mono-label text-[#7c5cff] mb-3">HEADLINE PRINCIPLES · READ FIRST</div>
                <ol className="space-y-2 list-none">
                    {data.headline_principles.map((p, i) => (
                        <li key={i} className="font-mono-tech text-xs text-white/85 leading-relaxed flex gap-3">
                            <span className="text-[#ccff00] font-bold">{String(i + 1).padStart(2, "0")}</span>
                            <span>{p}</span>
                        </li>
                    ))}
                </ol>
            </div>

            {/* GO-NOW QUICK STRIP */}
            <div data-testid="compliance-go-now-strip">
                <div className="mono-label text-[#ccff00] mb-3">
                    READY · TO · SELL · TODAY · {data.industries_by_status.go_now.length} VERTICALS · NO GATE
                </div>
                <div className="flex flex-wrap gap-2">
                    {data.industries_by_status.go_now.map((i) => (
                        <span
                            key={i.id}
                            data-testid={`go-now-pill-${i.id}`}
                            className="mono-label px-3 py-2 border"
                            style={{ color: "#ccff00", borderColor: "#ccff0055", background: "#ccff0011" }}
                        >{i.label}</span>
                    ))}
                </div>
                {data.industries_by_status.go_with_tos.length > 0 && (
                    <>
                        <div className="mono-label text-[#ffce4f] mb-3 mt-5">
                            READY · WITH ToS GUARDRAILS · {data.industries_by_status.go_with_tos.length} VERTICALS
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {data.industries_by_status.go_with_tos.map((i) => (
                                <span
                                    key={i.id}
                                    data-testid={`go-tos-pill-${i.id}`}
                                    className="mono-label px-3 py-2 border"
                                    style={{ color: "#ffce4f", borderColor: "#ffce4f55", background: "#ffce4f11" }}
                                >{i.label}</span>
                            ))}
                        </div>
                    </>
                )}
                {data.industries_by_status.blocked.length > 0 && (
                    <>
                        <div className="mono-label text-[#ff3b8a] mb-3 mt-5">
                            BLOCKED · UNTIL COMPLIANCE · {data.industries_by_status.blocked.length} VERTICALS
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {data.industries_by_status.blocked.map((i) => (
                                <span
                                    key={i.id}
                                    data-testid={`blocked-pill-${i.id}`}
                                    className="mono-label px-3 py-2 border"
                                    style={{ color: "#ff3b8a", borderColor: "#ff3b8a55", background: "#ff3b8a11" }}
                                >{i.label}</span>
                            ))}
                        </div>
                    </>
                )}
            </div>

            {/* INDUSTRY GRID with filter */}
            <div className="deck-card p-6 relative" data-testid="compliance-industries">
                <CornerBrackets />
                <div className="flex items-center justify-between flex-wrap gap-3 mb-5">
                    <div className="mono-label text-[#00ffff]">INDUSTRY ROUTING · {filtered.length}/{data.industries.length}</div>
                    <div className="flex gap-2 flex-wrap">
                        {["ALL", "go_now", "go_with_tos", "blocked"].map((s) => (
                            <button
                                key={s}
                                data-testid={`compliance-filter-${s}`}
                                onClick={() => setFilter(s)}
                                className="mono-label px-3 py-1.5 border text-[10px]"
                                style={{
                                    borderColor: filter === s ? (STATUS_COLOR[s] || "#ccff00") : "rgba(255,255,255,0.10)",
                                    color: filter === s ? (STATUS_COLOR[s] || "#ccff00") : "rgba(255,255,255,0.55)",
                                    background: filter === s ? `${STATUS_COLOR[s] || "#ccff00"}11` : "transparent",
                                }}
                            >
                                {s === "ALL" ? "ALL" : STATUS_LABEL[s]}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="grid lg:grid-cols-2 gap-4">
                    {filtered.map((i) => <IndustryCard key={i.id} ind={i} />)}
                </div>
            </div>

            {/* UNIVERSAL REQUIREMENTS */}
            <div className="deck-card relative" data-testid="compliance-universal">
                <CornerBrackets />
                <div className="px-6 py-4 border-b border-white/10 mono-label text-[#ccff00]">
                    UNIVERSAL REQUIREMENTS · MUST-HAVE BEFORE ANY ENTERPRISE DEAL
                </div>
                <div>
                    {data.universal_requirements.map((r) => <UniversalRow key={r.id} req={r} />)}
                </div>
            </div>

            {/* ROADMAP */}
            <div data-testid="compliance-roadmap">
                <div className="mono-label text-[#7c5cff] mb-3">8-MONTH COMPLIANCE ROADMAP</div>
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {data.roadmap.map((p) => <RoadmapCard key={p.month} phase={p} />)}
                </div>
            </div>
        </div>
    );
}

function Stat({ k, v, c }) {
    return (
        <div className="border px-4 py-3" style={{ borderColor: `${c}33`, background: `${c}08` }}>
            <div className="mono-label text-[10px]" style={{ color: c }}>{k}</div>
            <div className="font-display font-black text-3xl mt-1" style={{ color: c }}>{v}</div>
        </div>
    );
}
