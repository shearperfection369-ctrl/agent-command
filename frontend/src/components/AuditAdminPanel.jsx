/**
 * AuditAdminPanel — admin tab that lists every AI Readiness Audit ever run,
 * filterable by industry and status, with click-through to the results page.
 */
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { CornerBrackets } from "./Brackets";
import { toast } from "sonner";

const TIER_COLOR = {
    PIONEER: "#ccff00", BUILDER: "#00ffff", CURIOUS: "#7c5cff", LEARNING: "#ffce4f",
};
const STATUS_COLOR = {
    draft: "#777", complete: "#00ffff", analyzed: "#ccff00",
};

export default function AuditAdminPanel() {
    const [audits, setAudits] = useState([]);
    const [loading, setLoading] = useState(true);
    const [industry, setIndustry] = useState("");
    const [status, setStatus] = useState("");
    const [reloadKey, setReloadKey] = useState(0);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            setLoading(true);
            try {
                const params = {};
                if (industry) params.industry = industry;
                if (status) params.status = status;
                const { data } = await api.get("/admin/audits", { params });
                if (!cancelled) setAudits(data.audits || []);
            } catch {
                if (!cancelled) toast.error("Could not load audits.");
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => { cancelled = true; };
    }, [industry, status, reloadKey]);

    const load = () => setReloadKey((k) => k + 1);

    const remove = async (id) => {
        if (!window.confirm("Delete this audit permanently?")) return;
        try {
            await api.delete(`/admin/audits/${id}`);
            toast.success("Deleted.");
            load();
        } catch { toast.error("Delete failed."); }
    };

    const industries = useMemo(() => {
        const s = new Set(audits.map((a) => a.industry));
        return ["", ...Array.from(s)];
    }, [audits]);

    // KPI tiles (computed from analyzed audits only)
    const analyzed = audits.filter((a) => a.status === "analyzed" && a.analysis);
    const avgScore = analyzed.length
        ? Math.round(analyzed.reduce((sum, a) => sum + (a.analysis?.scores?.overall_score || 0), 0) / analyzed.length)
        : 0;
    const totalPipelineValue = analyzed.reduce(
        (sum, a) => sum + (a.analysis?.savings?.annual_savings_central_usd || 0), 0
    );
    const tierBreakdown = analyzed.reduce((acc, a) => {
        const t = a.analysis?.scores?.tier;
        if (t) acc[t] = (acc[t] || 0) + 1;
        return acc;
    }, {});

    return (
        <div className="space-y-6" data-testid="audit-admin-panel">
            <div className="flex items-center justify-between flex-wrap gap-3">
                <div>
                    <div className="mono-label text-[10px] text-[#ccff00]">CONSOLE · AI READINESS AUDIT</div>
                    <h2 className="font-display font-black text-white text-2xl mt-1 tracking-tight">
                        Consulting audit log.
                    </h2>
                </div>
                <Link to="/audit" data-testid="audit-new-from-admin"
                      className="btn-jade text-xs"
                      style={{ background: "#ccff00", color: "#02030a" }}>
                    ▶ NEW AUDIT
                </Link>
            </div>

            {/* KPIs */}
            <div className="grid sm:grid-cols-4 gap-3" data-testid="audit-kpis">
                <Kpi label="TOTAL AUDITS" value={audits.length} c="#ccff00" />
                <Kpi label="ANALYZED" value={analyzed.length} c="#00ffff" />
                <Kpi label="AVG SCORE" value={avgScore || "—"} c="#7c5cff" />
                <Kpi label="ANNUAL PIPELINE" value={`$${(totalPipelineValue / 1000).toFixed(0)}k`} c="#ffce4f" />
            </div>

            {/* Tier breakdown */}
            {analyzed.length > 0 && (
                <div className="relative border border-white/10 p-4 bg-[#0a0c18]" data-testid="audit-tier-breakdown">
                    <CornerBrackets />
                    <div className="mono-label text-[10px] text-white/55 mb-3">TIER BREAKDOWN</div>
                    <div className="flex gap-2 h-6 overflow-hidden">
                        {Object.entries(tierBreakdown).map(([tier, count]) => (
                            <div key={tier} className="relative flex items-center justify-center text-[10px] font-bold px-2"
                                 style={{
                                     flex: count,
                                     background: TIER_COLOR[tier],
                                     color: "#02030a",
                                 }}>
                                {tier} · {count}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Filters */}
            <div className="flex flex-wrap items-center gap-3" data-testid="audit-filters">
                <div className="mono-label text-[10px] text-white/55">FILTER ·</div>
                <select className="input-tech max-w-[200px]" value={industry}
                        onChange={(e) => setIndustry(e.target.value)}
                        data-testid="audit-filter-industry">
                    <option value="">ALL INDUSTRIES</option>
                    {industries.filter(Boolean).map((i) => (
                        <option key={i} value={i}>{i.replace("_", " ").toUpperCase()}</option>
                    ))}
                </select>
                <select className="input-tech max-w-[160px]" value={status}
                        onChange={(e) => setStatus(e.target.value)}
                        data-testid="audit-filter-status">
                    <option value="">ALL STATUSES</option>
                    <option value="draft">DRAFT</option>
                    <option value="complete">COMPLETE</option>
                    <option value="analyzed">ANALYZED</option>
                </select>
                <button onClick={load} className="btn-ghost text-xs">↻ REFRESH</button>
            </div>

            {/* Table */}
            <div className="relative border border-white/10 bg-[#0a0c18] overflow-x-auto"
                 data-testid="audit-table">
                <table className="w-full text-left">
                    <thead>
                        <tr className="border-b border-white/10">
                            <Th>COMPANY</Th>
                            <Th>INDUSTRY</Th>
                            <Th>STATUS</Th>
                            <Th>SCORE</Th>
                            <Th>TIER</Th>
                            <Th>SAVINGS</Th>
                            <Th>CREATED</Th>
                            <Th>ACTIONS</Th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan="8" className="px-4 py-6 font-mono-tech text-white/45">// loading…</td></tr>
                        ) : audits.length === 0 ? (
                            <tr><td colSpan="8" className="px-4 py-6 font-mono-tech text-white/45">
                                No audits yet. <Link to="/audit" className="text-[#ccff00] underline">Run the first one →</Link>
                            </td></tr>
                        ) : audits.map((a) => {
                            const score = a.analysis?.scores?.overall_score;
                            const tier = a.analysis?.scores?.tier;
                            const sav = a.analysis?.savings?.annual_savings_central_usd;
                            return (
                                <tr key={a.id} className="border-b border-white/5 hover:bg-white/5 transition"
                                    data-testid={`audit-row-${a.id}`}>
                                    <Td>
                                        <Link to={`/audit/${a.id}`} className="text-white hover:text-[#ccff00] font-bold">
                                            {a.company_name}
                                        </Link>
                                        {a.operator_name && (
                                            <div className="font-mono-tech text-[10px] text-white/45">{a.operator_name}</div>
                                        )}
                                    </Td>
                                    <Td><span className="font-mono-tech text-[11px] text-white/75">
                                        {a.industry.replace("_", " ")}
                                    </span></Td>
                                    <Td><span className="mono-label text-[9.5px] font-bold"
                                              style={{ color: STATUS_COLOR[a.status] || "#777" }}>
                                        ● {a.status.toUpperCase()}
                                    </span></Td>
                                    <Td><span className="font-display font-bold text-white">
                                        {score != null ? Math.round(score) : "—"}
                                    </span></Td>
                                    <Td>{tier ? (
                                        <span className="mono-label text-[9.5px] font-bold"
                                              style={{ color: TIER_COLOR[tier] }}>
                                            {tier}
                                        </span>
                                    ) : <span className="text-white/30">—</span>}</Td>
                                    <Td><span className="font-mono-tech text-[11px] text-white/75">
                                        {sav != null ? `$${(sav / 1000).toFixed(0)}k` : "—"}
                                    </span></Td>
                                    <Td><span className="font-mono-tech text-[10px] text-white/55">
                                        {a.created_at?.slice(0, 10)}
                                    </span></Td>
                                    <Td>
                                        <div className="flex gap-2">
                                            <Link to={`/audit/${a.id}`}
                                                  data-testid={`audit-open-${a.id}`}
                                                  className="mono-label text-[9.5px] text-[#00ffff] hover:underline">OPEN</Link>
                                            {a.status === "analyzed" && (
                                                <a href={`${process.env.REACT_APP_BACKEND_URL}/api/audit/${a.id}/report.pdf`}
                                                   target="_blank" rel="noreferrer"
                                                   data-testid={`audit-pdf-${a.id}`}
                                                   className="mono-label text-[9.5px] text-[#ccff00] hover:underline">PDF</a>
                                            )}
                                            <button onClick={() => remove(a.id)}
                                                    data-testid={`audit-delete-${a.id}`}
                                                    className="mono-label text-[9.5px] text-[#ff3b8a] hover:underline">DEL</button>
                                        </div>
                                    </Td>
                                </tr>
                            );
                        })}
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

const Th = ({ children }) => (
    <th className="px-4 py-3 mono-label text-[9.5px] text-white/55 font-normal">{children}</th>
);
const Td = ({ children }) => (
    <td className="px-4 py-3 align-top">{children}</td>
);
