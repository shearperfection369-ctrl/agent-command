/**
 * PartnerPackagePanel — admin PARTNER PACKAGE tab.
 *
 * Renders four sections per vertical:
 *   1. Capabilities · what JADE actually does
 *   2. ROI scenarios · cost / hours / savings per tier
 *   3. Client requirements · hardware / software / integrations / data / compliance
 *   4. Social proof · benchmarks we can publish
 *
 * Plus a platform-level CAPACITY ASSESSMENT for "can we serve 5 Lighthouse
 * pilots on launch day" — the answer + what to wire up before scaling.
 *
 * Endpoints:
 *   GET /api/admin/partner-package    · capability + ROI matrix
 *   GET /api/admin/requirements       · client + platform requirements
 */
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "./Brackets";
import { JadeWorking } from "./JadeAvatar";
import { SaveActions } from "./SaveActions";

const TIER_COLOR = { operator: "#ccff00", fleet: "#00ffff", enterprise: "#ff3b8a" };
const PRIORITY_COLOR = { P0: "#ff3b8a", P1: "#ffce4f", P2: "#7c5cff", P3: "#00ffff" };
const VERDICT_COLOR = { YES: "#ccff00", "YES · with two operator caveats": "#ccff00", NO: "#ff3b8a" };

function Stat({ k, v, c }) {
    return (
        <div className="border px-4 py-3" style={{ borderColor: `${c}33`, background: `${c}08` }}>
            <div className="mono-label text-[10px]" style={{ color: c }}>{k}</div>
            <div className="font-display font-black text-2xl mt-1" style={{ color: c }}>{v}</div>
        </div>
    );
}

function CapabilityCard({ cap }) {
    return (
        <div className="border border-white/10 p-4 bg-[#06081a] space-y-2" data-testid={`capability-${cap.id}`}>
            <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="font-display font-bold text-white text-base">{cap.name}</div>
                <span className="mono-label text-[10px] text-[#ccff00]">{cap.time_saved_hrs_week} HRS/WK</span>
            </div>
            <p className="font-mono-tech text-[12px] text-white/80 leading-relaxed">{cap.what_it_does}</p>
            <div className="grid sm:grid-cols-2 gap-3 pt-2 border-t border-white/5">
                <div>
                    <div className="mono-label text-[9px] text-white/40">KPI</div>
                    <div className="font-mono-tech text-[11px] text-[#00ffff] mt-1">{cap.primary_kpi}</div>
                </div>
                <div>
                    <div className="mono-label text-[9px] text-white/40">HOW IT WORKS</div>
                    <div className="font-mono-tech text-[11px] text-white/65 mt-1 leading-snug">{cap.how_it_works}</div>
                </div>
            </div>
            {cap.integrations?.length > 0 && (
                <div className="flex flex-wrap gap-1 pt-2 border-t border-white/5">
                    {cap.integrations.map((i, k) => (
                        <span key={k} className="font-mono-tech text-[9px] text-[#7c5cff] border border-[#7c5cff]/30 px-2 py-0.5">{i}</span>
                    ))}
                </div>
            )}
        </div>
    );
}

function RoiCard({ s }) {
    const c = TIER_COLOR[s.tier] || "#fff";
    return (
        <div className="border p-4 bg-[#02030a]" style={{ borderColor: `${c}55` }} data-testid={`roi-${s.tier}`}>
            <div className="mono-label text-[10px] mb-2" style={{ color: c }}>{s.tier?.toUpperCase()} · ${s.monthly_cost.toLocaleString()}/MO</div>
            <div className="grid grid-cols-3 gap-2">
                <div><div className="mono-label text-[8px] text-white/40">HRS · RECLAIMED</div><div className="font-display font-bold text-lg mt-0.5" style={{ color: c }}>{s.hours_reclaimed_monthly}</div></div>
                <div><div className="mono-label text-[8px] text-white/40">$ · SAVED</div><div className="font-display font-bold text-lg mt-0.5" style={{ color: c }}>${(s.dollar_savings_monthly / 1000).toFixed(0)}k</div></div>
                <div><div className="mono-label text-[8px] text-white/40">ROI · MULT</div><div className="font-display font-bold text-lg mt-0.5" style={{ color: c }}>{s.roi_multiple}x</div></div>
            </div>
            <div className="mono-label text-[9px] text-white/45 mt-2">PAYBACK · {s.payback_weeks} weeks</div>
        </div>
    );
}

function RequirementsList({ title, items, color, testid }) {
    if (!items || items.length === 0) return null;
    return (
        <div data-testid={testid}>
            <div className="mono-label text-[10px] mb-2" style={{ color }}>{title}</div>
            <ul className="space-y-1">
                {items.map((i, k) => (
                    <li key={k} className="font-mono-tech text-[11px] text-white/80 leading-snug flex gap-2">
                        <span style={{ color }}>·</span><span>{i}</span>
                    </li>
                ))}
            </ul>
        </div>
    );
}

function IndustryFullCard({ industryId, capabilities, requirements }) {
    if (!capabilities || !requirements) return null;
    return (
        <div className="deck-card relative p-6" data-testid={`industry-card-${industryId}`}>
            <CornerBrackets />
            <div className="flex items-baseline justify-between flex-wrap gap-3 mb-4">
                <div className="font-display font-black text-white text-2xl tracking-tight">{capabilities.label}</div>
                <span className="mono-label text-[10px] text-[#7c5cff]">{capabilities.capabilities.length} CAPABILITIES</span>
            </div>
            <p className="font-mono-tech text-[12px] text-[#ff3b8a] mb-5">PAIN · {capabilities.primary_pain}</p>

            {/* CAPABILITIES */}
            <div className="mono-label text-[#ccff00] mb-3">WHAT JADE DOES · {capabilities.capabilities.length}</div>
            <div className="grid lg:grid-cols-2 gap-3 mb-6">
                {capabilities.capabilities.map((c) => <CapabilityCard key={c.id} cap={c} />)}
            </div>

            {/* ROI */}
            <div className="mono-label text-[#00ffff] mb-3">ROI · BY TIER</div>
            <div className="grid sm:grid-cols-3 gap-3 mb-6">
                {capabilities.roi_scenarios.map((s) => <RoiCard key={s.tier} s={s} />)}
            </div>

            {/* SOCIAL PROOF */}
            {capabilities.social_proof?.length > 0 && (
                <div className="mb-6">
                    <div className="mono-label text-[#7c5cff] mb-2">PUBLISHABLE PROOF · USE IN PITCHES</div>
                    <ul className="space-y-1">
                        {capabilities.social_proof.map((p, i) => (
                            <li key={i} className="font-mono-tech text-[11px] text-white/85 leading-relaxed flex gap-2">
                                <span className="text-[#ccff00]">✓</span><span>{p}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* REQUIREMENTS */}
            <div className="mono-label text-[#ffce4f] mb-3">CLIENT REQUIREMENTS · WHAT THE PILOT NEEDS</div>
            <div className="grid sm:grid-cols-2 gap-5">
                <RequirementsList title="HARDWARE · MINIMUM" color="#ccff00" items={requirements.hardware_min} testid={`req-hardware-${industryId}`} />
                <RequirementsList title="SOFTWARE · REQUIRED" color="#00ffff" items={requirements.software_required} testid={`req-software-${industryId}`} />
                <RequirementsList title="DATA · FOR PILOT KICKOFF" color="#7c5cff" items={requirements.data_required_for_pilot} testid={`req-data-${industryId}`} />
                <RequirementsList title="INTEGRATIONS · REQUIRED" color="#ff3b8a" items={requirements.integrations_required} testid={`req-int-${industryId}`} />
                {requirements.integrations_optional?.length > 0 && (
                    <RequirementsList title="INTEGRATIONS · OPTIONAL" color="#ffce4f" items={requirements.integrations_optional} testid={`req-int-opt-${industryId}`} />
                )}
                {requirements.compliance_required?.length > 0 && (
                    <RequirementsList title="COMPLIANCE · REQUIRED" color="#ff3b8a" items={requirements.compliance_required} testid={`req-compliance-${industryId}`} />
                )}
            </div>

            <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between flex-wrap gap-3">
                <span className="mono-label text-[10px] text-white/55">TRAINING · {requirements.training_required_hours} HRS</span>
                {requirements.blocked_until && (
                    <span className="mono-label text-[10px] text-[#ff3b8a]">⚠ BLOCKED · {requirements.blocked_until}</span>
                )}
                {capabilities.guardrail && (
                    <span className="font-mono-tech text-[10px] text-[#ffce4f]">⚠ {capabilities.guardrail}</span>
                )}
            </div>
        </div>
    );
}

function CapacitySection({ cap }) {
    if (!cap) return null;
    const v = cap.ready_now_for_5_lighthouse_users;
    const vColor = v.verdict?.startsWith("YES") ? "#ccff00" : "#ff3b8a";
    return (
        <div className="space-y-5" data-testid="capacity-section">
            <div className="deck-card p-6 relative" data-testid="capacity-verdict">
                <CornerBrackets />
                <div className="mono-label text-[#7c5cff] mb-2">CAPACITY ASSESSMENT · CAN WE LAUNCH 5 LIGHTHOUSE PILOTS?</div>
                <div className="font-display font-black text-4xl tracking-tighter" style={{ color: vColor }}>
                    {v.verdict}
                </div>

                <div className="grid sm:grid-cols-2 gap-4 mt-5">
                    <div>
                        <div className="mono-label text-[#ccff00] text-[10px] mb-2">EVIDENCE</div>
                        <ul className="space-y-1.5">
                            {v.evidence.map((e, i) => (
                                <li key={i} className="font-mono-tech text-[11px] text-white/85 leading-snug flex gap-2">
                                    <span className="text-[#ccff00]">✓</span><span>{e}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                    <div>
                        <div className="mono-label text-[#ff3b8a] text-[10px] mb-2">CAVEATS · MUST RESOLVE</div>
                        <ul className="space-y-1.5">
                            {v.caveats.map((c, i) => (
                                <li key={i} className="font-mono-tech text-[11px] text-white/85 leading-snug flex gap-2">
                                    <span className="text-[#ff3b8a]">⚠</span><span>{c}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>

            {/* Current config */}
            <div className="deck-card p-6 relative">
                <CornerBrackets />
                <div className="mono-label text-[#00ffff] mb-3">CURRENT CONFIGURATION</div>
                <div className="grid sm:grid-cols-2 gap-y-2 gap-x-6">
                    {Object.entries(cap.current_config).map(([k, val]) => (
                        <div key={k} className="border-b border-white/5 py-2">
                            <div className="mono-label text-[9px] text-white/40 uppercase">{k.replace(/_/g, " ")}</div>
                            <div className="font-mono-tech text-[11px] text-white/85 leading-snug mt-1">{val}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Integrations to add */}
            <div className="deck-card p-6 relative" data-testid="integrations-to-add">
                <CornerBrackets />
                <div className="mono-label text-[#ccff00] mb-3">INTEGRATIONS · ADD FOR ROBUSTNESS</div>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {cap.integrations_to_add_for_robustness.map((it, i) => (
                        <div key={i} className="border border-white/10 p-3 bg-[#06081a]" data-testid={`integration-${it.name.toLowerCase().replace(/\s+/g, "-")}`}>
                            <div className="flex items-start justify-between gap-2">
                                <div className="font-display font-bold text-white text-sm">{it.name}</div>
                                <span className="mono-label text-[9px]" style={{ color: PRIORITY_COLOR[it.priority] }}>{it.priority}</span>
                            </div>
                            <div className="mono-label text-[9px] text-white/40 mt-1">{it.category}</div>
                            <div className="font-mono-tech text-[10px] text-[#ffce4f] mt-2 leading-snug">{it.status}</div>
                            <div className="font-mono-tech text-[10px] text-white/75 mt-2 leading-snug">{it.what_it_unlocks}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Scale milestones */}
            <div className="deck-card p-6 relative">
                <CornerBrackets />
                <div className="mono-label text-[#7c5cff] mb-3">SCALE MILESTONES</div>
                <div className="grid sm:grid-cols-2 gap-4">
                    {cap.scale_milestones.map((m, i) => (
                        <div key={i} className="border border-white/10 p-4 bg-[#02030a]">
                            <div className="font-display font-black text-white text-xl">{m.tier}</div>
                            <ul className="space-y-1 mt-3">
                                {m.what_to_add.map((x, j) => (
                                    <li key={j} className="font-mono-tech text-[11px] text-white/75 leading-snug flex gap-2"><span className="text-[#7c5cff]">▸</span>{x}</li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>
            </div>

            {/* Launch checklist */}
            <div className="deck-card p-6 relative" data-testid="launch-checklist">
                <CornerBrackets />
                <div className="mono-label text-[#ff3b8a] mb-3">LAUNCH DAY CHECKLIST</div>
                <ul className="space-y-2">
                    {cap.launch_day_checklist.map((item, i) => (
                        <li key={i} className="grid grid-cols-[24px_1fr_100px_120px] gap-3 items-center border-b border-white/5 py-2">
                            <span className="mono-label" style={{ color: item.blocks_launch ? "#ff3b8a" : "#ffce4f" }}>{item.blocks_launch ? "●" : "○"}</span>
                            <span className="font-mono-tech text-[12px] text-white/85">{item.item}</span>
                            <span className="mono-label text-[9px] text-white/55 uppercase">{item.owner}</span>
                            <span className="mono-label text-[9px]" style={{ color: item.blocks_launch ? "#ff3b8a" : "#ccff00" }}>{item.blocks_launch ? "BLOCKS LAUNCH" : "POST-LAUNCH OK"}</span>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}

export default function PartnerPackagePanel() {
    const [pkg, setPkg] = useState(null);
    const [req, setReq] = useState(null);
    const [loading, setLoading] = useState(true);
    const [view, setView] = useState("verticals");  // verticals | capacity
    const [selectedIndustry, setSelectedIndustry] = useState("freight_brokerage");

    const load = async () => {
        setLoading(true);
        try {
            const [p, r] = await Promise.all([
                api.get("/admin/partner-package"),
                api.get("/admin/requirements"),
            ]);
            setPkg(p.data);
            setReq(r.data);
        } catch { toast.error("Failed to load partner package"); }
        finally { setLoading(false); }
    };

    useEffect(() => { load(); }, []);

    if (loading) {
        return <div className="deck-card p-12 flex justify-center"><JadeWorking verb="loading partner package" size={72} /></div>;
    }
    if (!pkg || !req) return null;

    const industryIds = Object.keys(pkg.industries);

    return (
        <div className="space-y-6" data-testid="partner-package-panel">
            {/* HERO */}
            <div className="deck-card p-6 relative" data-testid="pp-hero">
                <CornerBrackets />
                <SectionLabel idx={0} color="#ccff00">PARTNER · PACKAGE</SectionLabel>
                <h2 className="font-display font-black text-white text-4xl tracking-tighter mt-2">
                    Eleven verticals. <span className="accent-lime">{pkg.total_capabilities}</span> capabilities. <span className="accent-cyan">One product.</span>
                </h2>
                <p className="text-white/65 text-sm mt-3 max-w-2xl leading-relaxed">
                    Everything JADE OS does — by industry, with ROI math, with the integrations your customer needs to bring, with the platform-capacity assessment for launch day.
                </p>
                <div className="flex flex-wrap gap-2 mt-5">
                    <button
                        data-testid="pp-view-verticals"
                        onClick={() => setView("verticals")}
                        className="mono-label px-3 py-1.5 border text-[10px]"
                        style={{ borderColor: view === "verticals" ? "#ccff00" : "rgba(255,255,255,0.10)", color: view === "verticals" ? "#ccff00" : "rgba(255,255,255,0.55)" }}
                    >▸ BY VERTICAL</button>
                    <button
                        data-testid="pp-view-capacity"
                        onClick={() => setView("capacity")}
                        className="mono-label px-3 py-1.5 border text-[10px]"
                        style={{ borderColor: view === "capacity" ? "#7c5cff" : "rgba(255,255,255,0.10)", color: view === "capacity" ? "#7c5cff" : "rgba(255,255,255,0.55)" }}
                    >⚙ CAPACITY · INFRASTRUCTURE</button>
                    <div className="ml-auto"><SaveActions data={{ pkg, req }} kind="json" filename="jadeos-partner-package" /></div>
                </div>
            </div>

            {view === "verticals" && (
                <>
                    {/* INDUSTRY PICKER */}
                    <div className="flex flex-wrap gap-2" data-testid="industry-picker">
                        {industryIds.map((id) => {
                            const active = selectedIndustry === id;
                            return (
                                <button
                                    key={id}
                                    data-testid={`pp-industry-${id}`}
                                    onClick={() => setSelectedIndustry(id)}
                                    className="mono-label px-3 py-2 border text-[10px]"
                                    style={{
                                        borderColor: active ? "#ccff00" : "rgba(255,255,255,0.12)",
                                        color: active ? "#ccff00" : "rgba(255,255,255,0.65)",
                                        background: active ? "#ccff0011" : "transparent",
                                    }}
                                >{pkg.industries[id].label}</button>
                            );
                        })}
                    </div>

                    <IndustryFullCard
                        industryId={selectedIndustry}
                        capabilities={pkg.industries[selectedIndustry]}
                        requirements={req.client_requirements[selectedIndustry]}
                    />
                </>
            )}

            {view === "capacity" && <CapacitySection cap={req.platform_capacity} />}
        </div>
    );
}
