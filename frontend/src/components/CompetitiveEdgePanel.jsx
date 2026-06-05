/**
 * CompetitiveEdgePanel — admin COMPETITIVE EDGE tab.
 *
 * Three views:
 *   1. MOATS — the six structural advantages (HubSpot says X / JADE does Y)
 *   2. WORKFLOWS — five highest-ROI freight workflows with savings + endpoint
 *   3. SCENARIO — live "HubSpot killer" load-match demo with copy-pasteable output
 *   4. PITCH KIT — elevator / cold email / InMail / objection handlers
 */
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "./Brackets";
import { JadeWorking } from "./JadeAvatar";
import { SaveActions } from "./SaveActions";

function MoatCard({ m }) {
    return (
        <div
            data-testid={`moat-${m.id}`}
            className="deck-card relative p-5"
            style={{ borderColor: `${m.color}44` }}
        >
            <CornerBrackets />
            <div className="flex items-baseline gap-3">
                <span className="font-display font-black text-3xl" style={{ color: m.color }}>0{m.rank}</span>
                <div className="font-display font-bold text-white text-lg leading-tight">{m.title}</div>
            </div>
            <div className="grid sm:grid-cols-2 gap-4 mt-4">
                <div className="border border-[#ff3b8a]/30 bg-[#ff3b8a]/05 p-3">
                    <div className="mono-label text-[#ff3b8a] text-[10px] mb-1">HUBSPOT / SERVICETITAN / BIG FOUR</div>
                    <p className="font-mono-tech text-[11px] text-white/85 leading-relaxed">{m.competitor_does}</p>
                </div>
                <div className="border p-3" style={{ borderColor: `${m.color}55`, background: `${m.color}11` }}>
                    <div className="mono-label text-[10px] mb-1" style={{ color: m.color }}>JADE OS</div>
                    <p className="font-mono-tech text-[11px] text-white/95 leading-relaxed">{m.jade_does}</p>
                </div>
            </div>
            {m.concrete_example && (
                <div className="mt-4">
                    <div className="mono-label text-[#7c5cff] text-[10px] mb-1">CONCRETE EXAMPLE</div>
                    <p className="font-mono-tech text-[11px] text-white/80 leading-relaxed">{m.concrete_example}</p>
                </div>
            )}
            {m.why_competitor_cant && (
                <div className="mt-3 pt-3 border-t border-white/5">
                    <div className="mono-label text-[#ffce4f] text-[10px] mb-1">WHY THEY CAN'T COPY THIS</div>
                    <p className="font-mono-tech text-[11px] text-[#ffce4f]/90 leading-relaxed">{m.why_competitor_cant}</p>
                </div>
            )}
        </div>
    );
}

function WorkflowCard({ w }) {
    return (
        <div className="deck-card relative p-5" data-testid={`workflow-${w.id}`}>
            <CornerBrackets />
            <div className="flex items-baseline gap-3">
                <span className="font-display font-black text-3xl text-[#ccff00]">0{w.rank}</span>
                <div className="font-display font-bold text-white text-lg leading-tight">{w.name}</div>
            </div>
            <p className="font-mono-tech text-[12px] text-white/85 mt-3 leading-relaxed">{w.what_it_does}</p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4 pt-3 border-t border-white/5">
                <Stat k="MANUAL" v={w.manual_time} c="#ff3b8a" small />
                <Stat k="JADE" v={w.jade_time} c="#ccff00" small />
                <Stat k="HRS/WK" v={w.hours_saved_week} c="#00ffff" small />
                <Stat k="LIFT" v={w.revenue_lift_pct} c="#7c5cff" small />
            </div>
            <div className="mt-2 font-mono-tech text-[10px] text-white/45">▸ {w.endpoint}</div>
        </div>
    );
}

function Stat({ k, v, c, small }) {
    return (
        <div className="border px-2 py-2" style={{ borderColor: `${c}33`, background: `${c}08` }}>
            <div className="mono-label text-[9px]" style={{ color: c }}>{k}</div>
            <div className={`font-display font-black mt-0.5 ${small ? "text-sm" : "text-2xl"}`} style={{ color: c }}>{v}</div>
        </div>
    );
}

function ComparisonTable({ rows }) {
    return (
        <div className="deck-card relative overflow-x-auto" data-testid="comparison-table">
            <CornerBrackets />
            <table className="w-full min-w-[800px]">
                <thead>
                    <tr className="border-b border-white/10">
                        <th className="text-left mono-label text-white/55 text-[10px] px-4 py-3">DIMENSION</th>
                        <th className="text-left mono-label text-[#ff3b8a] text-[10px] px-4 py-3">HUBSPOT</th>
                        <th className="text-left mono-label text-[#ff3b8a] text-[10px] px-4 py-3">SERVICETITAN</th>
                        <th className="text-left mono-label text-[#ff3b8a] text-[10px] px-4 py-3">BIG FOUR</th>
                        <th className="text-left mono-label text-[#ccff00] text-[10px] px-4 py-3">JADE OS</th>
                    </tr>
                </thead>
                <tbody>
                    {rows.map((r, i) => (
                        <tr key={i} className="border-b border-white/5">
                            <td className="font-display font-bold text-white text-xs px-4 py-3">{r.dimension}</td>
                            <td className="font-mono-tech text-[11px] text-white/65 px-4 py-3">{r.hubspot}</td>
                            <td className="font-mono-tech text-[11px] text-white/65 px-4 py-3">{r.servicetitan}</td>
                            <td className="font-mono-tech text-[11px] text-white/65 px-4 py-3">{r.big_four}</td>
                            <td className="font-mono-tech text-[11px] text-[#ccff00] px-4 py-3">{r.jade_os}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function PitchKit({ pitch }) {
    const [copied, setCopied] = useState(null);
    const copy = (key, text) => {
        navigator.clipboard.writeText(text);
        setCopied(key); setTimeout(() => setCopied(null), 1500);
        toast.success("Pitch copied");
    };

    return (
        <div className="space-y-4" data-testid="pitch-kit">
            {[
                { k: "elevator_30s", label: "ELEVATOR · 30s", text: pitch.elevator_30s, c: "#ccff00" },
                { k: "cold_email_120w", label: "COLD EMAIL · 120 WORDS", text: pitch.cold_email_120w, c: "#00ffff" },
                { k: "linkedin_inmail_4lines", label: "LINKEDIN INMAIL · 4 LINES", text: pitch.linkedin_inmail_4lines, c: "#7c5cff" },
            ].map((p) => (
                <div key={p.k} className="deck-card relative p-5" data-testid={`pitch-${p.k}`}>
                    <CornerBrackets />
                    <div className="flex items-center justify-between mb-3">
                        <div className="mono-label" style={{ color: p.c }}>{p.label}</div>
                        <button
                            data-testid={`copy-${p.k}`}
                            onClick={() => copy(p.k, p.text)}
                            className="mono-label text-[#ccff00] hover:text-white border border-[#ccff00]/40 px-3 py-1 text-[10px]"
                        >{copied === p.k ? "✓ COPIED" : "↗ COPY"}</button>
                    </div>
                    <pre className="font-mono-tech text-[12px] text-white/85 whitespace-pre-wrap leading-relaxed">{p.text}</pre>
                </div>
            ))}

            <div className="deck-card relative p-5" data-testid="objections">
                <CornerBrackets />
                <div className="mono-label text-[#ff3b8a] mb-3">OBJECTION HANDLERS</div>
                <div className="space-y-4">
                    {pitch.objection_handlers.map((o, i) => (
                        <div key={i} className="border-l-2 border-[#ff3b8a]/40 pl-3" data-testid={`objection-${i}`}>
                            <div className="font-mono-tech text-[11px] text-[#ff3b8a] mb-1">▸ "{o.objection}"</div>
                            <div className="font-mono-tech text-[11px] text-white/85 leading-relaxed">{o.response}</div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

function ScenarioRunner() {
    const [busy, setBusy] = useState(false);
    const [result, setResult] = useState(null);
    const [load, setLoad] = useState({
        origin: "Chicago, IL",
        destination: "Memphis, TN",
        commodity: "Machinery",
        weight_lbs: 18000,
        equipment: "Reefer",
        pickup_date: "in 3 days",
        special_requirements: "Shipper budget $1,200",
    });

    const run = async () => {
        setBusy(true); setResult(null);
        try {
            const { data } = await api.post("/agent/freight/load-match", load);
            setResult(data);
            toast.success("Scenario complete");
        } catch (e) {
            if (!e?.isLlmBudget) toast.error("Scenario run failed");
        } finally { setBusy(false); }
    };

    const m = result?.match || {};

    return (
        <div className="space-y-4" data-testid="scenario-runner">
            <div className="deck-card relative p-5">
                <CornerBrackets />
                <div className="mono-label text-[#ccff00] mb-3">HUBSPOT-KILLER SCENARIO · LOAD INQUIRY</div>
                <p className="font-mono-tech text-[11px] text-white/65 mb-4 leading-relaxed">
                    Generic AI says: "Draft a response asking for more details." JADE runs the entire operator analysis — equipment-fit check, HOS feasibility, rate-vs-market realism, top-4 carrier matches, drafted shipper response, follow-up timer. In 45 seconds.
                </p>
                <div className="grid sm:grid-cols-2 gap-3">
                    {Object.entries(load).map(([k, v]) => (
                        <div key={k}>
                            <label className="mono-label text-[9px] text-white/55 block mb-1">{k.toUpperCase().replace(/_/g, " ")}</label>
                            <input
                                data-testid={`scenario-input-${k}`}
                                value={v}
                                onChange={(e) => setLoad({ ...load, [k]: k === "weight_lbs" ? Number(e.target.value) : e.target.value })}
                                className="input-tech w-full text-xs"
                            />
                        </div>
                    ))}
                </div>
                <button
                    data-testid="scenario-run-btn"
                    disabled={busy}
                    onClick={run}
                    className="btn-jade w-full mt-4"
                >
                    {busy ? "RUNNING…" : "▶ RUN THE FULL ANALYSIS"}
                </button>
            </div>

            {busy && <div className="deck-card p-8 flex justify-center"><JadeWorking verb="running operator analysis" size={64} /></div>}

            {result && !m.parse_error && (
                <div className="space-y-4" data-testid="scenario-result">
                    {/* Equipment + HOS + Rate */}
                    <div className="grid sm:grid-cols-3 gap-3">
                        <Pill testid="scenario-equipment-mismatch" label="EQUIPMENT MISMATCH" value={m.equipment_mismatch_flag ? "YES · FLAGGED" : "NO"} color={m.equipment_mismatch_flag ? "#ff3b8a" : "#ccff00"} />
                        <Pill testid="scenario-hos-feasible" label="HOS FEASIBLE" value={m.hos_feasibility?.feasible ? "YES" : "NO · TIGHT"} color={m.hos_feasibility?.feasible ? "#ccff00" : "#ffce4f"} />
                        <Pill testid="scenario-rate-verdict" label="RATE VS MARKET" value={m.rate_analysis?.verdict?.replace(/_/g, " ").toUpperCase() || "—"} color={m.rate_analysis?.verdict === "below_market" ? "#ff3b8a" : "#ccff00"} />
                    </div>

                    {/* Exceptions */}
                    {m.exceptions?.length > 0 && (
                        <div className="deck-card relative p-4" data-testid="scenario-exceptions">
                            <CornerBrackets />
                            <div className="mono-label text-[#ff3b8a] mb-2">EXCEPTIONS · {m.exceptions.length}</div>
                            <ul className="space-y-2">
                                {m.exceptions.map((e, i) => (
                                    <li key={i} className="font-mono-tech text-[11px] text-white/85 leading-snug flex gap-2">
                                        <span className="mono-label text-[9px] px-1.5 py-0.5 border whitespace-nowrap" style={{ color: e.severity === "blocker" ? "#ff3b8a" : e.severity === "high" ? "#ffce4f" : "#7c5cff", borderColor: "currentColor" }}>{e.severity?.toUpperCase()}</span>
                                        <div>
                                            <div className="text-white font-bold">{e.type}</div>
                                            <div className="text-white/75">{e.explanation}</div>
                                            <div className="text-[#ccff00] text-[10px] mt-1">→ {e.recommended_action}</div>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Top matches */}
                    {m.top_matches?.length > 0 && (
                        <div data-testid="scenario-matches">
                            <div className="mono-label text-[#ccff00] mb-3">TOP {m.top_matches.length} CARRIER MATCHES</div>
                            <div className="grid sm:grid-cols-2 gap-3">
                                {m.top_matches.map((c, i) => (
                                    <div key={i} className="deck-card relative p-3" data-testid={`match-${i}`}>
                                        <CornerBrackets />
                                        <div className="flex items-start justify-between mb-1">
                                            <div className="font-display font-bold text-white text-sm">{c.carrier_profile}</div>
                                            <span className="mono-label text-[10px] text-[#ccff00]">FIT {c.fit_score_0_100}</span>
                                        </div>
                                        <div className="font-mono-tech text-[10px] text-[#7c5cff]">{c.mc_number} · {c.typical_rate_band}</div>
                                        <div className="font-mono-tech text-[11px] text-white/75 mt-2 leading-snug">{c.fit_rationale}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Drafted response */}
                    {m.drafted_response && (
                        <div className="deck-card relative p-4" data-testid="scenario-draft">
                            <CornerBrackets />
                            <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                                <div className="mono-label text-[#00ffff]">DRAFTED RESPONSE · BROKER REVIEW</div>
                                <SaveActions data={`SUBJECT: ${m.drafted_response.subject}\n\n${m.drafted_response.body}`} kind="txt" filename="jadeos-load-response" />
                            </div>
                            <div className="font-display font-bold text-white text-sm mb-2">SUBJECT: {m.drafted_response.subject}</div>
                            <pre className="font-mono-tech text-[12px] text-white/85 whitespace-pre-wrap leading-relaxed">{m.drafted_response.body}</pre>
                            {m.followup_reminder_minutes && (
                                <div className="mt-3 pt-3 border-t border-white/5 mono-label text-[10px] text-[#ffce4f]">
                                    ⏱ FOLLOW-UP REMINDER · {m.followup_reminder_minutes} MINUTES
                                </div>
                            )}
                        </div>
                    )}

                    {/* Broker review notes */}
                    {m.broker_review_notes?.length > 0 && (
                        <div className="deck-card relative p-4" data-testid="scenario-review">
                            <CornerBrackets />
                            <div className="mono-label text-[#7c5cff] mb-2">BROKER REVIEW · VERIFY BEFORE SEND</div>
                            <ul className="space-y-1">
                                {m.broker_review_notes.map((n, i) => (
                                    <li key={i} className="font-mono-tech text-[11px] text-white/85 flex gap-2"><span className="text-[#7c5cff]">▸</span>{n}</li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            )}

            {result && m.parse_error && (
                <pre className="deck-card p-4 font-mono-tech text-[11px] text-white/65 whitespace-pre-wrap">{m.raw}</pre>
            )}
        </div>
    );
}

function Pill({ label, value, color, testid }) {
    return (
        <div className="border px-3 py-2" style={{ borderColor: `${color}55`, background: `${color}11` }} data-testid={testid}>
            <div className="mono-label text-[9px] text-white/55">{label}</div>
            <div className="font-display font-black mt-1" style={{ color }}>{value}</div>
        </div>
    );
}

export default function CompetitiveEdgePanel() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [view, setView] = useState("moats");

    useEffect(() => {
        (async () => {
            try {
                const { data } = await api.get("/admin/competitive-moat");
                setData(data);
            } catch { toast.error("Failed to load moat"); }
            finally { setLoading(false); }
        })();
    }, []);

    if (loading) {
        return <div className="deck-card p-12 flex justify-center"><JadeWorking verb="loading competitive edge" size={72} /></div>;
    }
    if (!data) return null;

    const TABS = [
        { id: "moats", label: "MOATS · 6", c: "#ccff00" },
        { id: "workflows", label: "WORKFLOWS · 5", c: "#00ffff" },
        { id: "comparison", label: "COMPARISON", c: "#7c5cff" },
        { id: "pitch", label: "PITCH KIT", c: "#ff3b8a" },
        { id: "scenario", label: "▶ RUN THE SCENARIO", c: "#ffce4f" },
    ];

    return (
        <div className="space-y-6" data-testid="competitive-edge-panel">
            <div className="deck-card p-6 relative" data-testid="ce-hero">
                <CornerBrackets />
                <SectionLabel idx={0} color="#ff3b8a">COMPETITIVE · EDGE</SectionLabel>
                <h2 className="font-display font-black text-white text-4xl tracking-tighter mt-2">
                    Six moats. <span className="accent-lime">Five workflows.</span> <span className="accent-cyan">One pitch.</span>
                </h2>
                <p className="text-white/65 text-sm mt-3 max-w-2xl leading-relaxed">{data.subtitle}</p>
                <div className="flex flex-wrap gap-2 mt-5">
                    {TABS.map((t) => {
                        const active = view === t.id;
                        return (
                            <button
                                key={t.id}
                                data-testid={`ce-view-${t.id}`}
                                onClick={() => setView(t.id)}
                                className="mono-label px-3 py-1.5 border text-[10px]"
                                style={{
                                    borderColor: active ? t.c : "rgba(255,255,255,0.10)",
                                    color: active ? t.c : "rgba(255,255,255,0.55)",
                                    background: active ? `${t.c}11` : "transparent",
                                }}
                            >{t.label}</button>
                        );
                    })}
                </div>
            </div>

            {view === "moats" && (
                <>
                    <div className="grid lg:grid-cols-2 gap-4" data-testid="moats-grid">
                        {data.moats.map((m) => <MoatCard key={m.id} m={m} />)}
                    </div>
                    <div className="deck-card p-5 relative" data-testid="weaponization">
                        <CornerBrackets />
                        <div className="mono-label text-[#7c5cff] mb-3">WEAPONIZATION PRINCIPLES</div>
                        <ol className="space-y-2 list-none">
                            {data.weaponization_principles.map((p, i) => (
                                <li key={i} className="font-mono-tech text-xs text-white/85 leading-relaxed flex gap-3">
                                    <span className="text-[#ccff00] font-bold">{String(i + 1).padStart(2, "0")}</span>{p}
                                </li>
                            ))}
                        </ol>
                    </div>
                </>
            )}

            {view === "workflows" && (
                <div className="grid lg:grid-cols-2 gap-4" data-testid="workflows-grid">
                    {data.highest_roi_workflows.map((w) => <WorkflowCard key={w.id} w={w} />)}
                </div>
            )}

            {view === "comparison" && <ComparisonTable rows={data.comparison_table} />}

            {view === "pitch" && <PitchKit pitch={data.pitch_language} />}

            {view === "scenario" && <ScenarioRunner />}
        </div>
    );
}
