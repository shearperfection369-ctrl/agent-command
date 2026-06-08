/**
 * OutreachPanel — admin tab. Five pre-baked campaigns + a tracker.
 *
 * Workflow:
 *   1. Pick a campaign template (left column)
 *   2. Fill in template variables
 *   3. "RENDER" shows the personalized subject + body
 *   4. "COPY TO CLIPBOARD" + manual send via your email client
 *   5. "LOG SEND" creates a tracker row → bottom table
 *   6. Mark replied / meeting_booked / passed as the convo progresses
 */
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { CornerBrackets } from "./Brackets";
import { toast } from "sonner";

const STATUS_COLOR = {
    sent: "#00ffff", opened: "#ccff00", replied: "#ccff00",
    meeting_booked: "#7c5cff", passed: "#ff3b8a",
};

export default function OutreachPanel() {
    const [campaigns, setCampaigns] = useState([]);
    const [selected, setSelected] = useState(null);
    // Vars keyed by campaign_id so switching campaigns preserves prior fills
    const [allVars, setAllVars] = useState({});
    const vars = selected ? (allVars[selected.id] || {}) : {};
    const [rendered, setRendered] = useState(null);
    const [recipient, setRecipient] = useState({ recipient_name: "", recipient_company: "", recipient_email: "", recipient_linkedin: "" });
    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState({});
    const [loading, setLoading] = useState(true);
    const [logReloadKey, setLogReloadKey] = useState(0);

    // Load campaigns once
    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                const { data } = await api.get("/outreach/campaigns");
                if (cancelled) return;
                setCampaigns(data.campaigns || []);
                if (data.campaigns?.length) {
                    setSelected(data.campaigns[0]);
                    setRendered(null);
                }
            } catch { toast.error("Could not load campaigns."); }
        })();
        return () => { cancelled = true; };
    }, []);

    // Load log on changes
    useEffect(() => {
        let cancelled = false;
        (async () => {
            setLoading(true);
            try {
                const { data } = await api.get("/admin/outreach/log");
                if (cancelled) return;
                setLogs(data.log || []);
                setStats(data.stats || {});
            } catch { /* admin endpoint might not be auth'd yet */ }
            finally { if (!cancelled) setLoading(false); }
        })();
        return () => { cancelled = true; };
    }, [logReloadKey]);

    const sentCount = logs.filter((l) => l.status === "sent").length;
    const repliedCount = logs.filter((l) => l.status === "replied").length;
    const meetingCount = logs.filter((l) => l.status === "meeting_booked").length;
    const passedCount = logs.filter((l) => l.status === "passed").length;

    return (
        <div className="space-y-6" data-testid="outreach-panel">
            {/* Header */}
            <div className="flex items-center justify-between flex-wrap gap-3">
                <div>
                    <div className="mono-label text-[10px] text-[#ff3b8a]">CONSOLE · OUTREACH CAMPAIGNS</div>
                    <h2 className="font-display font-black text-white text-2xl mt-1 tracking-tight">
                        Get JadeOS in their inbox.
                    </h2>
                </div>
                <div className="flex gap-3">
                    <a href="/audit/playbook" className="mono-label text-[10px] text-[#ccff00] hover:underline">↗ PLAYBOOK ASSETS</a>
                    <a href="/audit/broker-free" target="_blank" rel="noreferrer"
                       className="mono-label text-[10px] text-[#00ffff] hover:underline">↗ PUBLIC LANDING</a>
                </div>
            </div>

            {/* KPI strip */}
            <div className="grid grid-cols-4 gap-3" data-testid="outreach-kpis">
                <Kpi label="SENT" value={sentCount} c="#00ffff" />
                <Kpi label="REPLIED" value={repliedCount} c="#ccff00" />
                <Kpi label="MEETINGS" value={meetingCount} c="#7c5cff" />
                <Kpi label="PASSED" value={passedCount} c="#ff3b8a" />
            </div>

            {/* MAIN · 3 cols (templates · render · log send) */}
            <div className="grid xl:grid-cols-[280px_1fr_320px] gap-4">
                {/* Templates */}
                <div className="relative border border-white/10 p-4 bg-[#0a0c18]">
                    <CornerBrackets />
                    <div className="mono-label text-[10px] text-white/55 mb-3">CAMPAIGNS · 5</div>
                    <div className="space-y-2">
                        {campaigns.map((c) => {
                            const active = selected?.id === c.id;
                            return (
                                <button key={c.id}
                                        data-testid={`outreach-campaign-${c.id}`}
                                        onClick={() => { setSelected(c); setRendered(null); }}
                                        className="block w-full text-left p-2.5 transition"
                                        style={{
                                            border: `1px solid ${active ? c.color : "rgba(255,255,255,0.10)"}`,
                                            background: active ? `${c.color}11` : "transparent",
                                        }}>
                                    <div className="mono-label text-[9.5px]" style={{ color: c.color }}>
                                        {c.channel.toUpperCase()}
                                    </div>
                                    <div className="font-display font-black text-white text-[12px] mt-0.5 leading-tight">
                                        {c.label}
                                    </div>
                                    <div className="font-mono-tech text-[9.5px] text-white/50 mt-1 leading-relaxed">
                                        {c.audience}
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Render + Variables */}
                <div className="relative border border-white/10 p-5 bg-[#0a0c18]">
                    <CornerBrackets />
                    {!selected ? (
                        <div className="font-mono-tech text-white/45">// pick a campaign on the left</div>
                    ) : (
                        <>
                            <div className="flex items-center justify-between flex-wrap gap-2">
                                <div className="mono-label text-[10px]" style={{ color: selected.color }}>
                                    {selected.label}
                                </div>
                                <div className="font-mono-tech text-[10px] text-white/55">
                                    channel · {selected.channel} · vars · {selected.variables.length}
                                </div>
                            </div>
                            {/* Variables */}
                            <div className="grid sm:grid-cols-2 gap-3 mt-4">
                                {selected.variables.map((k) => (
                                    <div key={k}>
                                        <div className="mono-label text-[9.5px] text-white/55 mb-1.5">{k.toUpperCase()}</div>
                                        <input data-testid={`outreach-var-${k}`}
                                               className="input-tech"
                                               value={vars[k] || ""}
                                               onChange={(e) => {
                                                   const newVal = e.target.value;
                                                   const cid = selected.id;
                                                   setAllVars((prev) => ({
                                                       ...prev,
                                                       [cid]: { ...(prev[cid] || {}), [k]: newVal },
                                                   }));
                                               }}
                                               placeholder={`{{${k}}}`} />
                                    </div>
                                ))}
                            </div>
                            <div className="flex gap-2 mt-4">
                                <button data-testid="outreach-render-btn"
                                        onClick={async () => {
                                            if (!selected) return;
                                            try {
                                                const variables = { ...vars };
                                                const { data } = await api.post("/outreach/render", { campaign_id: selected.id, variables });
                                                setRendered(data);
                                            } catch { toast.error("Render failed."); }
                                        }}
                                        className="btn-jade text-xs"
                                        style={{ background: selected.color, color: "#02030a" }}>
                                    ▶ RENDER
                                </button>
                                {rendered && (
                                    <button data-testid="outreach-copy-btn"
                                            onClick={() => {
                                                const text = `Subject: ${rendered.subject}\n\n${rendered.body}`;
                                                navigator.clipboard.writeText(text).then(
                                                    () => toast.success("Copied to clipboard."),
                                                    () => toast.error("Copy failed.")
                                                );
                                            }}
                                            className="btn-jade text-xs"
                                            style={{ background: "transparent", color: "white", border: "1px solid rgba(255,255,255,0.20)" }}>
                                        📋 COPY EMAIL
                                    </button>
                                )}
                            </div>

                            {/* Rendered output */}
                            {rendered && (
                                <div className="mt-5 pt-5 border-t border-white/10" data-testid="outreach-rendered">
                                    <div className="mono-label text-[9.5px] text-white/55 mb-1">SUBJECT</div>
                                    <div className="font-display font-bold text-white text-[14px] mb-4">{rendered.subject}</div>
                                    <div className="mono-label text-[9.5px] text-white/55 mb-1">BODY</div>
                                    <pre className="font-mono-tech text-[11.5px] text-white/85 whitespace-pre-wrap leading-relaxed">{rendered.body}</pre>
                                    {rendered.attach_pdfs && rendered.attach_pdfs.length > 0 && (
                                        <div className="mt-4 pt-3 border-t border-white/5">
                                            <div className="mono-label text-[9.5px] text-[#ccff00] mb-2">ATTACH THESE PDFS</div>
                                            <div className="flex gap-2 flex-wrap">
                                                {rendered.attach_pdfs.map((p) => (
                                                    <a key={p}
                                                       href={`${process.env.REACT_APP_BACKEND_URL}/api/audit/${p}`}
                                                       target="_blank" rel="noreferrer"
                                                       className="mono-label text-[9.5px] text-[#ccff00] hover:underline">
                                                        ↓ {p}
                                                    </a>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </>
                    )}
                </div>

                {/* Log a send */}
                <div className="relative border border-[#ff3b8a44] p-5 bg-[#ff3b8a08]">
                    <CornerBrackets />
                    <div className="mono-label text-[10px] text-[#ff3b8a] mb-4">LOG A SEND</div>
                    <div className="space-y-3">
                        {[
                            { k: "recipient_name", label: "NAME · REQUIRED" },
                            { k: "recipient_company", label: "COMPANY" },
                            { k: "recipient_email", label: "EMAIL" },
                            { k: "recipient_linkedin", label: "LINKEDIN URL" },
                        ].map((f) => (
                            <div key={f.k}>
                                <div className="mono-label text-[9.5px] text-white/55 mb-1.5">{f.label}</div>
                                <input data-testid={`outreach-recipient-${f.k}`}
                                       className="input-tech text-[12px]"
                                       value={recipient[f.k]}
                                       onChange={(e) => setRecipient({ ...recipient, [f.k]: e.target.value })} />
                            </div>
                        ))}
                        <button data-testid="outreach-log-btn"
                                onClick={async () => {
                                    if (!selected || !recipient.recipient_name.trim()) {
                                        toast.error("Recipient name required."); return;
                                    }
                                    try {
                                        await api.post("/outreach/log", { campaign_id: selected.id, ...recipient });
                                        toast.success("Logged.");
                                        setRecipient({ recipient_name: "", recipient_company: "", recipient_email: "", recipient_linkedin: "" });
                                        setLogReloadKey((k) => k + 1);
                                    } catch { toast.error("Log failed."); }
                                }}
                                disabled={!selected || !recipient.recipient_name}
                                className="btn-jade text-xs w-full disabled:opacity-50"
                                style={{ background: "#ff3b8a", color: "#02030a" }}>
                            ▶ LOG SEND
                        </button>
                    </div>
                </div>
            </div>

            {/* TRACKER · log table */}
            <div className="relative border border-white/10 bg-[#0a0c18] overflow-x-auto"
                 data-testid="outreach-tracker">
                <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
                    <div className="mono-label text-[10px] text-white/55">OUTREACH TRACKER · ALL SENDS</div>
                    <div className="font-mono-tech text-[10px] text-white/55">{logs.length} rows</div>
                </div>
                <table className="w-full text-left">
                    <thead>
                        <tr className="border-b border-white/10">
                            {["RECIPIENT", "COMPANY", "CAMPAIGN", "STATUS", "SENT", "ACTIONS"].map((h) => (
                                <th key={h} className="px-4 py-2 mono-label text-[9.5px] text-white/45 font-normal">{h}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="6" className="px-4 py-4 font-mono-tech text-white/45">// loading…</td></tr>
                        ) : logs.length === 0 ? (
                            <tr><td colSpan="6" className="px-4 py-4 font-mono-tech text-white/45">
                                No sends logged yet. Render a campaign, log it, watch the funnel grow.
                            </td></tr>
                        ) : logs.map((l) => (
                            <tr key={l.id} className="border-b border-white/5 hover:bg-white/5">
                                <td className="px-4 py-2.5 text-white font-bold">{l.recipient_name}</td>
                                <td className="px-4 py-2.5 font-mono-tech text-[11px] text-white/75">{l.recipient_company || "—"}</td>
                                <td className="px-4 py-2.5 font-mono-tech text-[10px] text-white/55">{l.campaign_id}</td>
                                <td className="px-4 py-2.5">
                                    <span className="mono-label text-[9.5px] font-bold"
                                          style={{ color: STATUS_COLOR[l.status] || "#999" }}>
                                        ● {l.status.toUpperCase()}
                                    </span>
                                </td>
                                <td className="px-4 py-2.5 font-mono-tech text-[10px] text-white/55">
                                    {l.sent_at?.slice(0, 16).replace("T", " ")}
                                </td>
                                <td className="px-4 py-2.5">
                                    <div className="flex gap-2 flex-wrap">
                                        {["replied", "meeting_booked", "passed"].map((s) => (
                                            <button key={s}
                                                    data-testid={`outreach-set-${l.id}-${s}`}
                                                    onClick={async () => {
                                                        try {
                                                            await api.patch(`/admin/outreach/log/${l.id}`, { status: s });
                                                            setLogReloadKey((k) => k + 1);
                                                        } catch { toast.error("Update failed."); }
                                                    }}
                                                    disabled={l.status === s}
                                                    className="mono-label text-[9px] disabled:opacity-40 hover:underline"
                                                    style={{ color: STATUS_COLOR[s] }}>
                                                ⇨ {s.replace("_", " ").toUpperCase()}
                                            </button>
                                        ))}
                                        <button onClick={async () => {
                                                    if (!window.confirm("Delete this log row?")) return;
                                                    try {
                                                        await api.delete(`/admin/outreach/log/${l.id}`);
                                                        setLogReloadKey((k) => k + 1);
                                                    } catch { toast.error("Delete failed."); }
                                                }}
                                                data-testid={`outreach-del-${l.id}`}
                                                className="mono-label text-[9px] text-[#ff3b8a] hover:underline">DEL</button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function Kpi({ label, value, c }) {
    return (
        <div className="relative border p-4 bg-[#0a0c18]" style={{ borderColor: `${c}44` }}>
            <CornerBrackets />
            <div className="mono-label text-[9.5px] text-white/55">{label}</div>
            <div className="font-display font-black mt-1" style={{ color: c, fontSize: "1.8rem" }}>{value}</div>
        </div>
    );
}
