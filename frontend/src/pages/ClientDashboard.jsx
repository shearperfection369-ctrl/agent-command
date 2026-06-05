/**
 * /client/dashboard — read-only client portal home.
 *
 * Scaffold-grade: shows authenticated email, last seen, recent agent runs,
 * and a placeholder for per-tenant RAG / billing controls. Production rollout
 * will swap the stubs for real per-tenant data, RBAC, and live agent telemetry.
 */
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { CornerBrackets, SectionLabel } from "../components/Brackets";
import { clientMe, clientLogout, isClientAuthed } from "../lib/clientAuth";

export default function ClientDashboard() {
    const nav = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!isClientAuthed()) { nav("/client/login", { replace: true }); return; }
        (async () => {
            try {
                const me = await clientMe();
                setData(me);
            } catch (e) {
                toast.error("Session expired.");
                nav("/client/login", { replace: true });
            } finally { setLoading(false); }
        })();
    }, []);

    const logout = () => { clientLogout(); nav("/client/login", { replace: true }); };

    if (loading) return <div className="min-h-screen bg-console grid place-items-center font-mono-tech text-[#ccff00]">// loading portal…</div>;
    if (!data) return null;

    return (
        <div className="bg-console min-h-screen" data-testid="client-dashboard">
            <section className="px-6 lg:px-10 py-12 grid-bg-tight border-b border-white/5">
                <div className="max-w-[1100px] mx-auto">
                    <div className="flex items-baseline justify-between flex-wrap gap-3">
                        <div>
                            <SectionLabel idx={0} color="#7c5cff">CLIENT · PORTAL</SectionLabel>
                            <h1 className="font-display font-black text-white text-4xl tracking-tighter mt-2">
                                Hi <span className="accent-cyan">{data.user.email}</span>.
                            </h1>
                            <p className="text-white/65 text-sm mt-2">{data.user.company || "Welcome — operator-grade dashboard."}</p>
                        </div>
                        <button
                            data-testid="client-logout-btn"
                            onClick={logout}
                            className="btn-ghost text-xs"
                        >SIGN OUT</button>
                    </div>
                </div>
            </section>

            <section className="px-6 lg:px-10 py-12">
                <div className="max-w-[1100px] mx-auto space-y-6">
                    <div className="grid sm:grid-cols-3 gap-4">
                        <Stat k="ACCOUNT EMAIL" v={data.user.email} c="#ccff00" />
                        <Stat k="COMPANY" v={data.user.company || "—"} c="#00ffff" />
                        <Stat k="LAST SEEN" v={data.user.last_seen_at ? new Date(data.user.last_seen_at).toLocaleString() : "—"} c="#7c5cff" />
                    </div>

                    <div className="deck-card relative" data-testid="client-runs">
                        <CornerBrackets />
                        <div className="px-6 py-4 border-b border-white/10 mono-label text-[#ccff00]">RECENT AGENT RUNS · TAPE</div>
                        <div className="divide-y divide-white/5">
                            {data.runs.length === 0 ? (
                                <div className="p-8 font-mono-tech text-xs text-white/40 text-center">// no runs scoped to your account yet</div>
                            ) : data.runs.map((r) => (
                                <div key={r.id} className="p-4 grid grid-cols-[120px_100px_1fr_140px] gap-4 items-center">
                                    <span className="mono-label" style={{ color: r.agent_type === "chat" ? "#ccff00" : "#00ffff" }}>{r.agent_type}</span>
                                    <span className="font-mono-tech text-[10px] text-white/40">{r.provider}</span>
                                    <span className="font-mono-tech text-xs text-white/65 truncate">{r.input_preview}</span>
                                    <span className="font-mono-tech text-[10px] text-white/35 text-right">{new Date(r.created_at).toLocaleString()}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="deck-card p-6 relative" data-testid="client-roadmap">
                        <CornerBrackets />
                        <div className="mono-label text-[#7c5cff]">ROADMAP · WHAT'S COMING TO YOUR PORTAL</div>
                        <ul className="space-y-2 mt-3">
                            {[
                                "Per-tenant RAG · ingest your carrier directory + BOL library and query inside the portal",
                                "Live agent runs · stream agent activity in real-time for your account only",
                                "Stripe self-serve · upgrade tier / manage seats without emailing us",
                                "SOC 2 audit log · download every action JADE took on your data",
                                "RBAC · invite teammates with view-only / operator / admin roles",
                            ].map((item, i) => (
                                <li key={i} className="font-mono-tech text-[11px] text-white/85 leading-snug flex gap-2">
                                    <span className="text-[#ccff00]">▸</span>{item}
                                </li>
                            ))}
                        </ul>
                        <div className="mt-4 pt-3 border-t border-white/5 font-mono-tech text-[10px] text-white/40 leading-relaxed">
                            Lighthouse design partners get early access. Talk to your CS lead.
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}

function Stat({ k, v, c }) {
    return (
        <div className="deck-card p-5 relative">
            <CornerBrackets />
            <div className="mono-label text-white/40">{k}</div>
            <div className="font-display font-bold text-white text-base mt-2 truncate" style={{ color: c }}>{v}</div>
        </div>
    );
}
