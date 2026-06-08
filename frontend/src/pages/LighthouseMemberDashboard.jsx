/**
 * LighthouseMemberDashboard · /lighthouse/member/:auditId
 *
 * Read-only Lighthouse cohort dashboard. No admin features.
 *
 * audit_id IS the access token (16-hex). User receives it on intake and
 * bookmarks the link. Same model as Notion / Calendly share URLs.
 *
 * Surfaces:
 *   - Audit summary (score, tier, top agent, savings band)
 *   - 7-stage pilot timeline (complete / current / pending)
 *   - Deliverables (download PDF, view results, playbook, press kit)
 *   - Founder contacts + Slack invite path
 *   - 6 founding-customer perks
 */
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { CornerBrackets } from "../components/Brackets";
import { toast } from "sonner";

const ACCENT = { jade: "#ccff00", cyan: "#00ffff", violet: "#7c5cff", magenta: "#ff3b8a", amber: "#ffce4f" };
const TIER_COLOR = { PIONEER: ACCENT.jade, BUILDER: ACCENT.cyan, CURIOUS: ACCENT.violet, LEARNING: ACCENT.amber };

export default function LighthouseMemberDashboard() {
    const { auditId } = useParams();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [err, setErr] = useState(null);

    useEffect(() => {
        let cancelled = false;
        (async () => {
            setLoading(true);
            try {
                const { data: d } = await api.get(`/audit/lighthouse/${auditId}/dashboard`);
                if (!cancelled) setData(d);
            } catch (e) {
                if (!cancelled) {
                    setErr(e?.response?.status === 404 ? "Audit not found." :
                           e?.response?.status === 403 ? "This link is not a Lighthouse audit." :
                           "Could not load dashboard.");
                }
            } finally { if (!cancelled) setLoading(false); }
        })();
        return () => { cancelled = true; };
    }, [auditId]);

    const copyLink = () => {
        const url = window.location.href;
        navigator.clipboard?.writeText(url);
        toast.success("Member link copied.");
    };

    if (loading) {
        return <div className="min-h-[60vh] grid place-items-center font-mono-tech text-white/55">// loading member dashboard…</div>;
    }
    if (err || !data) {
        return (
            <div className="min-h-[60vh] grid place-items-center px-6">
                <div className="text-center max-w-md">
                    <div className="mono-label text-[10px] text-[#ff3b8a]">DASHBOARD UNAVAILABLE</div>
                    <h1 className="font-display font-bold text-white text-2xl mt-2">{err || "Not found."}</h1>
                    <p className="font-mono-tech text-[12px] text-white/55 mt-3">
                        Need help? Email{" "}
                        <a href="mailto:founder@jadeos.ai" className="text-[#00ffff]">founder@jadeos.ai</a>
                    </p>
                    <Link to="/lighthouse/audit" className="btn-ghost mt-6 inline-block">
                        START A NEW LIGHTHOUSE AUDIT →
                    </Link>
                </div>
            </div>
        );
    }

    const sum = data.summary;
    const tierColor = sum.tier_color || TIER_COLOR[sum.tier] || ACCENT.jade;
    const hasAnalysis = !!sum.tier;

    return (
        <div className="min-h-[80vh] py-10 px-6" data-testid="lighthouse-member-dashboard">
            <div className="max-w-6xl mx-auto space-y-6">
                {/* HEADER */}
                <div className="relative border p-6 sm:p-8 bg-gradient-to-br from-[#0a0c18] to-[#15102a]"
                     style={{ borderColor: `${tierColor}55` }}>
                    <CornerBrackets />
                    <div className="grid lg:grid-cols-[1.4fr_1fr] gap-6 items-start">
                        <div>
                            <div className="mono-label text-[10px]" style={{ color: tierColor }}>
                                LIGHTHOUSE MEMBER · {data.industry.replace("_", " ").toUpperCase()} · MEMBER SINCE {new Date(data.created_at).toLocaleDateString(undefined, { month: "short", year: "numeric" })}
                            </div>
                            <h1 className="font-display font-black text-white text-3xl sm:text-5xl mt-2 tracking-tight">
                                {data.company_name}
                            </h1>
                            <p className="font-mono-tech text-[12px] text-white/70 mt-3 max-w-2xl">
                                Welcome back, {data.operator_name || "operator"}. This is your private Lighthouse
                                member view — bookmark the URL above. No login required, but only people you share
                                this link with can see it.
                            </p>
                            <div className="flex flex-wrap gap-2 mt-5">
                                <button data-testid="lh-copy-link" onClick={copyLink} className="btn-ghost text-xs">
                                    ⎘ COPY MEMBER LINK
                                </button>
                                {hasAnalysis && (
                                    <a data-testid="lh-pdf-download"
                                       href={`${process.env.REACT_APP_BACKEND_URL}${data.deliverables.audit_pdf_url}`}
                                       target="_blank" rel="noreferrer"
                                       className="btn-jade text-xs"
                                       style={{ background: tierColor, color: "#02030a" }}>
                                        ↓ DOWNLOAD 14-PAGE PDF
                                    </a>
                                )}
                                <Link to={data.deliverables.audit_results_url} data-testid="lh-view-results"
                                      className="btn-ghost text-xs">
                                    VIEW FULL RESULTS →
                                </Link>
                            </div>
                        </div>

                        {hasAnalysis ? (
                            <div className="text-center sm:text-right">
                                <div className="mono-label text-[10px] text-white/45 mb-1">READINESS SCORE</div>
                                <div className="font-display font-black leading-none"
                                     style={{ color: tierColor, fontSize: "clamp(4rem, 11vw, 7rem)" }}
                                     data-testid="lh-overall-score">
                                    {Math.round(sum.overall_score)}
                                </div>
                                <div className="mono-label text-[14px] mt-1" style={{ color: tierColor }}>
                                    TIER · {sum.tier}
                                </div>
                                <div className="font-mono-tech text-[10.5px] text-white/55 mt-2 max-w-xs ml-auto">
                                    {sum.tier_blurb}
                                </div>
                            </div>
                        ) : (
                            <div className="border border-[#ffce4f44] p-4 bg-[#1a1d2e]">
                                <div className="mono-label text-[10px] text-[#ffce4f]">AUDIT IN PROGRESS</div>
                                <p className="font-mono-tech text-[11.5px] text-white/85 mt-2">
                                    Finish your audit to unlock your score, tier, and personalized 90-day pilot terms.
                                </p>
                                <Link to={data.deliverables.audit_wizard_url} className="btn-jade text-xs mt-3 inline-block">
                                    RESUME AUDIT →
                                </Link>
                            </div>
                        )}
                    </div>
                </div>

                {/* PILOT TIMELINE */}
                <div className="relative border border-white/10 p-6 bg-[#0a0c18]">
                    <CornerBrackets />
                    <div className="flex items-center justify-between mb-5">
                        <div className="mono-label text-[10px] text-[#7c5cff]">PILOT TIMELINE</div>
                        <div className="mono-label text-[9px] text-white/45">
                            {data.timeline.filter((t) => t.complete).length} OF {data.timeline.length} STAGES COMPLETE
                        </div>
                    </div>
                    <div className="grid grid-cols-[max-content_1fr] gap-x-5">
                        {data.timeline.map((stage, idx) => (
                            <Stage key={stage.id} stage={stage} isLast={idx === data.timeline.length - 1} />
                        ))}
                    </div>
                </div>

                {/* SUMMARY CARDS */}
                {hasAnalysis && (
                    <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        <SummaryCard label="ANCHOR AGENT"
                                     value={sum.top_agent?.name || "—"}
                                     sub={sum.top_agent?.id ? `Module ${sum.top_agent.id}` : ""}
                                     c={ACCENT.jade} />
                        <SummaryCard label="YEAR-1 SAVINGS · CENTRAL"
                                     value={`$${(sum.annual_savings_central_usd || 0).toLocaleString()}`}
                                     sub={`Range $${(sum.annual_savings_low_usd || 0).toLocaleString()} – $${(sum.annual_savings_high_usd || 0).toLocaleString()}`}
                                     c={ACCENT.cyan} />
                        <SummaryCard label="PAYBACK"
                                     value={`~${sum.payback_months_estimate || "—"} months`}
                                     sub="at central estimate"
                                     c={ACCENT.violet} />
                        <SummaryCard label="LIGHTHOUSE RATE"
                                     value="$17,500"
                                     sub="vs $35,000 list · locked"
                                     c={ACCENT.amber} />
                    </div>
                )}

                {/* CONTACTS + DELIVERABLES */}
                <div className="grid lg:grid-cols-2 gap-6">
                    <div className="relative border border-white/10 p-6 bg-[#0a0c18]" data-testid="lh-contacts">
                        <CornerBrackets />
                        <div className="mono-label text-[10px] text-[#ccff00] mb-4">FOUNDER · DIRECT LINE</div>
                        <div className="space-y-3">
                            <ContactRow label="FOUNDER"  value={data.contacts.founder_name}     c={ACCENT.jade} />
                            <ContactRow label="EMAIL"    value={data.contacts.founder_email}    c={ACCENT.cyan}    href={`mailto:${data.contacts.founder_email}`} />
                            <ContactRow label="LINKEDIN" value={data.contacts.founder_linkedin} c={ACCENT.violet}  href={`https://${data.contacts.founder_linkedin}`} />
                            <ContactRow label="SLACK"
                                        value="Email for invite"
                                        c={ACCENT.amber}
                                        href={`mailto:${data.contacts.slack_invite}?subject=Lighthouse · Slack invite · ${encodeURIComponent(data.company_name)}`} />
                        </div>
                    </div>

                    <div className="relative border border-white/10 p-6 bg-[#0a0c18]" data-testid="lh-deliverables">
                        <CornerBrackets />
                        <div className="mono-label text-[10px] text-[#00ffff] mb-4">YOUR DELIVERABLES</div>
                        <div className="space-y-3">
                            {hasAnalysis && (
                                <DeliverableRow href={`${process.env.REACT_APP_BACKEND_URL}${data.deliverables.audit_pdf_url}`}
                                                label="14-Page Audit PDF" sub="Tailored to your responses · ready to share with your board" external />
                            )}
                            <DeliverableRow href={data.deliverables.audit_results_url}
                                            label="Live Results Dashboard" sub="Radar chart · breakdown · click any dimension for analyst drill-down" />
                            <DeliverableRow href={data.deliverables.playbook_url}
                                            label="Operator Playbook" sub="How we run the 30-question audit · talk track + objection handling" />
                            <DeliverableRow href={data.deliverables.press_kit_url}
                                            label="Press Kit" sub="Logos · brand assets · audio sample · approved copy" />
                        </div>
                    </div>
                </div>

                {/* PERKS */}
                <div className="relative border border-white/10 p-6 bg-[#0a0c18]">
                    <CornerBrackets />
                    <div className="mono-label text-[10px] text-[#ccff00] mb-4">FOUNDING-CUSTOMER PERKS</div>
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {data.perks.map((p) => (
                            <div key={p.label} className="border border-white/5 p-4 bg-[#06070d]">
                                <div className="mono-label text-[9.5px] text-[#ccff00] mb-1.5">{p.label.toUpperCase()}</div>
                                <p className="font-mono-tech text-[11.5px] text-white/80 leading-relaxed">{p.detail}</p>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="flex justify-between items-center pt-4 border-t border-white/5">
                    <Link to="/lighthouse" className="mono-label text-[10px] text-white/55 hover:text-[#ccff00]">
                        ◀ LIGHTHOUSE PROGRAM
                    </Link>
                    <a href="mailto:founder@jadeos.ai" className="mono-label text-[10px] text-[#7c5cff] hover:underline">
                        EMAIL FOUNDER ▸
                    </a>
                </div>
            </div>
        </div>
    );
}

function Stage({ stage, isLast }) {
    const dotColor = stage.complete ? "#ccff00" : stage.current ? "#00ffff" : "#1a1d2e";
    const lineColor = stage.complete ? "#ccff0055" : "#1a1d2e";
    return (
        <>
            <div className="flex flex-col items-center" style={{ minHeight: isLast ? "auto" : 64 }}>
                <div className="w-4 h-4 rounded-full"
                     style={{
                         background: dotColor,
                         boxShadow: stage.current ? "0 0 12px #00ffff" : "none",
                     }} />
                {!isLast && (
                    <div className="w-[2px] flex-1 mt-1" style={{ background: lineColor }} />
                )}
            </div>
            <div className="pb-5">
                <div className="flex items-center gap-2 flex-wrap">
                    <div className="font-display font-bold text-white text-sm">{stage.label}</div>
                    {stage.complete && <span className="mono-label text-[9px] text-[#ccff00]">✓ COMPLETE</span>}
                    {stage.current && <span className="mono-label text-[9px] text-[#00ffff]">▶ CURRENT</span>}
                </div>
                <p className="font-mono-tech text-[11px] text-white/55 mt-1 leading-relaxed">{stage.blurb}</p>
            </div>
        </>
    );
}

function SummaryCard({ label, value, sub, c }) {
    return (
        <div className="relative border border-white/10 p-5 bg-[#0a0c18]">
            <CornerBrackets />
            <div className="mono-label text-[9.5px]" style={{ color: c }}>{label}</div>
            <div className="font-display font-bold text-white text-xl mt-2 truncate">{value}</div>
            <div className="font-mono-tech text-[10px] text-white/50 mt-1">{sub}</div>
        </div>
    );
}

function ContactRow({ label, value, c, href }) {
    const cls = "font-mono-tech text-[12px] text-white/90 truncate";
    return (
        <div className="grid grid-cols-[90px_1fr] gap-3 items-center">
            <span className="mono-label text-[9.5px]" style={{ color: c }}>{label}</span>
            {href ? (
                <a href={href} target="_blank" rel="noreferrer"
                   className={`${cls} hover:underline`} style={{ color: c }}>{value}</a>
            ) : (
                <span className={cls}>{value}</span>
            )}
        </div>
    );
}

function DeliverableRow({ href, label, sub, external }) {
    const Comp = external ? "a" : Link;
    const props = external ? { href, target: "_blank", rel: "noreferrer" } : { to: href };
    return (
        <Comp {...props} className="block border border-white/5 px-4 py-3 bg-[#06070d] hover:border-[#ccff0055] transition-colors">
            <div className="font-display font-bold text-white text-sm">{label}</div>
            <div className="font-mono-tech text-[10.5px] text-white/55 mt-1">{sub}</div>
        </Comp>
    );
}
