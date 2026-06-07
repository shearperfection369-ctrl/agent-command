/**
 * InvestorInvite — Full VC package landing page.
 * Positions JadeOS-Agent Suite (six AI agents) + Hot Shot TMS (operator-built TMS) as one
 * investable stack. Replaces the previous slide-based pitch.
 *
 * Sections:
 *  • Hero · The Joint Offering
 *  • Founder Credential · 13-year operator
 *  • The Two Products · TMS + JadeOS-Agent Suite side-by-side
 *  • Six Agents · ship-status honest (live from /api/agent/modules/status)
 *  • Traction · production users + Tennant rethemed deployment
 *  • ROI · pre-baked Mid-Market 175-truck case
 *  • The Ask · $1.5M seed + 30-min discovery CTA
 *  • Investor Access · pitch PDF + full execution plan PDF + technical brief PDF
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CornerBrackets } from "../components/Brackets";
import { api, API_BASE } from "../lib/api";

const ACCENT = {
    jade: "#ccff00",
    cyan: "#00ffff",
    violet: "#7c5cff",
    magenta: "#ff3b8a",
    amber: "#ffce4f",
};

function Stat({ k, v, c, sub }) {
    return (
        <div className="border px-4 py-3" style={{ borderColor: `${c}33`, background: `${c}08` }}>
            <div className="mono-label text-[10px]" style={{ color: c }}>{k}</div>
            <div className="font-display font-black text-2xl mt-1" style={{ color: c }}>{v}</div>
            {sub && <div className="font-mono-tech text-[10px] text-white/40 mt-1">{sub}</div>}
        </div>
    );
}

function Section({ eyebrow, eyebrowColor, title, children, id }) {
    return (
        <section id={id} className="py-14 sm:py-20 border-t border-white/5">
            <div className="max-w-6xl mx-auto px-6">
                <div className="mono-label text-[11px] mb-3" style={{ color: eyebrowColor }}>{eyebrow}</div>
                <h2 className="font-display font-black text-white text-3xl sm:text-4xl lg:text-5xl leading-[1.05]">{title}</h2>
                <div className="mt-8">{children}</div>
            </div>
        </section>
    );
}

function ModuleCard({ m }) {
    const BADGE = {
        shipping_full: { label: "● LIVE · PRODUCTION", c: ACCENT.jade },
        shipping_partial: { label: "◐ LIVE · PARTIAL", c: ACCENT.cyan },
        shipping_pilot_phase: { label: "◐ PILOT-PHASE MVP", c: ACCENT.amber },
        not_built: { label: "○ ROADMAP", c: "rgba(255,255,255,0.45)" },
    };
    const b = BADGE[m.ship_status] || BADGE.not_built;
    return (
        <div className="relative border border-white/10 bg-[#0a0c18] p-5" data-testid={`investor-module-${m.id}`}
             style={{ borderLeft: `3px solid ${b.c}` }}>
            <CornerBrackets />
            <div className="flex items-baseline justify-between gap-2 flex-wrap">
                <span className="font-display font-black text-white text-base">{m.id} · {m.name}</span>
                <span className="mono-label text-[10px]" style={{ color: b.c }}>{b.label}</span>
            </div>
            {m.live_endpoint && (
                <div className="font-mono-tech text-[10.5px] text-[#00ffff] mt-2">{m.live_endpoint}</div>
            )}
            <div className="font-mono-tech text-[11px] text-white/70 mt-2 leading-relaxed">{m.kpi}</div>
        </div>
    );
}

export default function InvestorInvite() {
    const [modules, setModules] = useState([]);
    const [deck, setDeck] = useState(null);
    const [roi, setRoi] = useState(null);

    useEffect(() => {
        api.get("/agent/workbench/architecture").then(({ data }) => setModules(data.modules || [])).catch(() => {});
        api.get("/agent/workbench/collateral").then(({ data }) => setDeck(data)).catch(() => {});
        api.post("/agent/workbench/roi", { archetype: "mid_market" }).then(({ data }) => setRoi(data.model)).catch(() => {});
    }, []);

    const askEmail = "founder@jadeos.ai";

    return (
        <div className="min-h-screen bg-[#06070d] text-white" data-testid="investor-invite-page">
            {/* ===================== HERO ===================== */}
            <section className="relative overflow-hidden border-b border-white/10">
                <div className="absolute inset-0 pointer-events-none opacity-[0.12]"
                     style={{ backgroundImage:
                         "radial-gradient(circle at 15% 10%, #ccff00 0, transparent 35%), " +
                         "radial-gradient(circle at 85% 85%, #00ffff 0, transparent 40%)" }} />
                <div className="relative max-w-6xl mx-auto px-6 py-16 sm:py-24 lg:py-28">
                    <div className="mono-label text-[11px] text-[#ccff00]" data-testid="invite-eyebrow">
                        INVESTOR INVITE · PRE-SEED · 2026 · MINNEAPOLIS, MN
                    </div>
                    <h1 className="font-display font-black text-white mt-4 leading-[0.95] tracking-tight text-5xl sm:text-6xl lg:text-7xl">
                        One founder.<br />Three products.<br />
                        <span style={{ color: ACCENT.jade }}>One investable thesis.</span>
                    </h1>
                    <p className="font-mono-tech text-base sm:text-lg text-white/75 mt-8 max-w-3xl leading-relaxed">
                        <span className="text-[#7c5cff]">JadeOS Quantum AI</span> is the flagship AI command center &mdash; 50+ modules,
                        voice-first, persistent memory, 128-qubit Qiskit Aer + Claude Haiku 4.5.{" "}
                        <span className="text-[#00ffff]">JadeOS-Agent Suite</span> is the freight-vertical agent productization
                        for logistics. <span className="text-[#ccff00]">Hot Shot TMS</span> is the operator-built
                        system of record for the underserved hot-shot segment.{" "}
                        <span className="text-[#ccff00]">All three built solo by Oliver Cummins. All three ready
                        to deploy. Raising in tandem.</span>
                    </p>
                    <div className="flex flex-wrap gap-3 mt-10">
                        <a href={`mailto:${askEmail}?subject=JADE%20OS%20%2B%20Hot%20Shot%20TMS%20Investor%20Discovery`}
                           data-testid="invite-discovery-btn"
                           className="btn-jade text-sm inline-flex items-center gap-2"
                           style={{ background: ACCENT.jade, color: "#0a0c18" }}>
                            → 30-MIN DISCOVERY
                        </a>
                        <a href={`${API_BASE}/agent/workbench/deck.pdf`} target="_blank" rel="noreferrer"
                           data-testid="invite-deck-btn"
                           className="btn-jade text-sm inline-flex items-center gap-2"
                           style={{ background: ACCENT.violet, color: "white" }}>
                            ↓ INVESTOR PITCH · 12-SLIDE PDF
                        </a>
                        <Link to="/demo" data-testid="invite-live-demo-btn"
                              className="btn-jade text-sm inline-flex items-center gap-2"
                              style={{ background: "transparent", color: "white", border: "1px solid rgba(255,255,255,0.2)" }}>
                            ▶ LIVE PRODUCT DEMO
                        </Link>
                        <Link to="/demo?tab=tms" data-testid="invite-tms-preview-btn"
                              className="btn-jade text-sm inline-flex items-center gap-2"
                              style={{ background: "transparent", color: ACCENT.cyan, border: `1px solid ${ACCENT.cyan}55` }}>
                            ▶ HOT SHOT TMS · PREVIEW
                        </Link>
                    </div>
                    <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-12">
                        <Stat k="HEADQUARTERS" v="MPLS · MN" c={ACCENT.jade} sub="Minnesota beachhead" />
                        <Stat k="FOUNDER" v="OLIVER CUMMINS" c={ACCENT.cyan} sub="Sole · 13-yr operator + builder" />
                        <Stat k="PRODUCTS · BUILD STATUS" v="3 / READY" c={ACCENT.violet} sub="JadeOS Quantum AI · JadeOS-Agent Suite · Hot Shot TMS" />
                        <Stat k="SEED ASK" v="$2.0M" c={ACCENT.magenta} sub="SAFE · $12M post-money cap" />
                    </div>
                </div>
            </section>

            {/* ===================== FOUNDER CREDENTIAL ===================== */}
            <Section id="founder" eyebrow="01 · FOUNDER" eyebrowColor={ACCENT.cyan}
                     title={<>Not built by software founders<br /><span style={{ color: ACCENT.cyan }}>who read a book about logistics.</span></>}>
                <div className="grid lg:grid-cols-[2fr_1fr] gap-6">
                    <div className="relative border border-white/10 p-7 bg-gradient-to-br from-[#0a0c18] to-[#0f1426]">
                        <CornerBrackets />
                        <p className="font-mono-tech text-base text-white/85 leading-relaxed">
                            JadeOS-Agent Suite + Hot Shot TMS were both built by a <span className="text-[#ccff00] font-bold">13-year transportation
                            operator</span>. The TMS was the system the operator wished he had for a decade.
                            The AI agents automate the exact decisions the operator was making 60 times a day &mdash;
                            dispatch, pricing, compliance, retention.
                        </p>
                        <p className="font-mono-tech text-[15px] text-white/65 mt-5 leading-relaxed">
                            We don&apos;t ship to logistics. We ship from logistics.
                        </p>
                        <div className="mt-6 grid sm:grid-cols-3 gap-3">
                            <div className="border-l-2 border-[#ccff00] pl-3">
                                <div className="mono-label text-[10px] text-[#ccff00]">DISPATCH</div>
                                <div className="font-mono-tech text-[11px] text-white/65 mt-0.5">10+ years inside the chair</div>
                            </div>
                            <div className="border-l-2 border-[#00ffff] pl-3">
                                <div className="mono-label text-[10px] text-[#00ffff]">PRICING + RFP</div>
                                <div className="font-mono-tech text-[11px] text-white/65 mt-0.5">Rate-floor guard is muscle memory</div>
                            </div>
                            <div className="border-l-2 border-[#7c5cff] pl-3">
                                <div className="mono-label text-[10px] text-[#7c5cff]">COMPLIANCE</div>
                                <div className="font-mono-tech text-[11px] text-white/65 mt-0.5">FMCSA §395/396 from first principles</div>
                            </div>
                        </div>
                    </div>
                    <div className="relative border border-[#ccff0044] p-6 bg-[#ccff0008]">
                        <CornerBrackets />
                        <div className="mono-label text-[#ccff00]">OPERATOR&apos;S BIAS</div>
                        <ul className="mt-3 space-y-3">
                            {[
                                "Every decision in the platform has been made manually by the founder",
                                "Every number is benchmark-cited · ATA · ATRI · BLS · EIA · FMCSA",
                                "Every workflow has been used in a real dispatch shift",
                                "Every UI element answers the operator's question, not the engineer's"
                            ].map((t, i) => (
                                <li key={i} className="font-mono-tech text-[11.5px] text-white/85 flex gap-2 leading-relaxed">
                                    <span className="text-[#ccff00]">▸</span>{t}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </Section>

            {/* ===================== FOUNDER BIO ===================== */}
            <Section id="bio" eyebrow="01.5 · FOUNDER BIO" eyebrowColor={ACCENT.cyan}
                     title={<>13 years inside the chair.<br /><span style={{ color: ACCENT.cyan }}>One operator. Two products.</span></>}>
                <div className="grid lg:grid-cols-[260px_1fr] gap-6 items-start" data-testid="founder-bio-block">
                    {/* Portrait */}
                    <div className="relative border border-[#00ffff44] bg-[#0a0c18] overflow-hidden" data-testid="founder-portrait">
                        <CornerBrackets />
                        <div className="relative aspect-[3/4] overflow-hidden">
                            <img src="/assets/founder.png" alt="Founder · 13-year transportation operator"
                                 className="w-full h-full object-cover object-center" />
                            <div className="absolute inset-0 pointer-events-none"
                                 style={{ background: "linear-gradient(180deg, transparent 55%, rgba(6,8,15,0.92) 100%)" }} />
                            <div className="absolute bottom-0 left-0 right-0 p-4">
                                <div className="mono-label text-[10px] text-[#00ffff]">FOUNDER · CEO</div>
                                <div className="font-display font-black text-white text-xl mt-1 leading-tight">Oliver Cummins</div>
                                <div className="font-mono-tech text-[10.5px] text-[#ccff00] mt-1">Sole founder · 13-yr transportation operator · Minneapolis · MN</div>
                            </div>
                        </div>
                        <div className="px-4 py-3 border-t border-white/10 flex flex-wrap gap-3 bg-[#0a0c18]">
                            <a href="https://www.linkedin.com/" target="_blank" rel="noreferrer"
                               data-testid="founder-linkedin"
                               className="mono-label text-[10px] text-[#00ffff] hover:underline">↗ LINKEDIN</a>
                            <a href="mailto:founder@jadeos.ai" data-testid="founder-email"
                               className="mono-label text-[10px] text-[#ccff00] hover:underline">✉ EMAIL</a>
                        </div>
                    </div>

                    {/* Bio + chapter ribbon */}
                    <div className="space-y-5">
                        <div className="relative border border-white/10 p-6 bg-gradient-to-br from-[#0a0c18] to-[#0a1820]">
                            <CornerBrackets />
                            <p className="font-mono-tech text-base text-white/85 leading-relaxed">
                                Thirteen years inside transportation operations — dispatch desk, pricing seat, compliance lead, driver-manager.
                                Started in a hot-shot operation that grew through three TMS migrations, none of which fit the segment. That gap
                                is the reason <span className="text-[#ccff00]">Hot Shot TMS</span> exists.
                            </p>
                            <p className="font-mono-tech text-[13.5px] text-white/70 mt-4 leading-relaxed">
                                Every recurring decision in that thirteen years &mdash; dispatch matching, rate-floor enforcement, HOS feasibility,
                                retention conversations, maintenance triage &mdash; is now an agent inside <span className="text-[#00ffff]">JadeOS-Agent Suite</span>.
                                The agents aren&apos;t guesses. They&apos;re a documented operator playbook converted into code.
                            </p>
                            <blockquote className="mt-5 border-l-2 border-[#ccff00] pl-4">
                                <p className="font-display font-bold text-white text-lg leading-snug">
                                    &ldquo;Hot Shot TMS is the system I built because none of the incumbents
                                    served the segment I actually worked in. JadeOS-Agent Suite is the AI layer for every
                                    decision I made 60 times a day.&rdquo;
                                </p>
                                <footer className="font-mono-tech text-[11px] text-[#ccff00] mt-2">— Founder · 13-yr transportation operator</footer>
                            </blockquote>
                        </div>

                        {/* Career chapter ribbon */}
                        <div className="grid sm:grid-cols-4 gap-2" data-testid="founder-chapters">
                            {[
                                { yrs: "YR 1-3", role: "Dispatcher", note: "Hot-shot fleet · 14 trucks · ran the desk solo nights & weekends", c: ACCENT.jade },
                                { yrs: "YR 4-7", role: "Pricing + RFP Lead", note: "Lane-rate analysis · rate-floor discipline · contract vs spot mix", c: ACCENT.cyan },
                                { yrs: "YR 8-10", role: "Compliance & Safety", note: "FMCSA §395/396 in production · CSA-score work · audit-pack hand-runs", c: ACCENT.violet },
                                { yrs: "YR 11-13", role: "Operations + Builder", note: "Spec'd the TMS the segment needed · then built it with JadeOS-Agent Suite on top", c: ACCENT.amber },
                            ].map((ch, i) => (
                                <div key={i} className="border p-3" style={{ borderColor: `${ch.c}44`, background: `${ch.c}08` }}>
                                    <div className="mono-label text-[9.5px]" style={{ color: ch.c }}>{ch.yrs}</div>
                                    <div className="font-display font-black text-white text-sm mt-1">{ch.role}</div>
                                    <div className="font-mono-tech text-[10px] text-white/65 mt-1 leading-relaxed">{ch.note}</div>
                                </div>
                            ))}
                        </div>

                        {/* Why-now / why-me */}
                        <div className="grid sm:grid-cols-2 gap-3" data-testid="founder-why">
                            <div className="border border-[#ccff0044] p-4 bg-[#ccff0008]">
                                <div className="mono-label text-[10px] text-[#ccff00] mb-2">WHY ME</div>
                                <ul className="space-y-1.5">
                                    {[
                                        "Operated through 3 TMS migrations · saw what no vendor served",
                                        "Made the same 60 decisions/shift agents now automate",
                                        "Carrier network warm in MN · 14 FMCSA-verified hot-list seeded",
                                    ].map((t, i) => (
                                        <li key={i} className="font-mono-tech text-[11px] text-white/85 flex gap-2 leading-relaxed">
                                            <span className="text-[#ccff00]">▸</span>{t}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                            <div className="border border-[#00ffff44] p-4 bg-[#00ffff08]">
                                <div className="mono-label text-[10px] text-[#00ffff] mb-2">WHY NOW</div>
                                <ul className="space-y-1.5">
                                    {[
                                        "Hot-shot segment fully digitized but underserved by TMS incumbents",
                                        "AI agents on top of TMS is the consensus VC thesis · we add a TMS layer they can't",
                                        "Both products build-complete · 18 months to land · 6-month pilots ready",
                                    ].map((t, i) => (
                                        <li key={i} className="font-mono-tech text-[11px] text-white/85 flex gap-2 leading-relaxed">
                                            <span className="text-[#00ffff]">▸</span>{t}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </Section>

            {/* ===================== THREE PRODUCTS ===================== */}
            <Section id="products" eyebrow="02 · THE STACK" eyebrowColor={ACCENT.jade}
                     title={<>Three products.<br /><span style={{ color: ACCENT.jade }}>One investable thesis.</span></>}>
                <p className="font-mono-tech text-[13px] text-white/65 max-w-3xl leading-relaxed -mt-3 mb-6">
                    JadeOS Quantum AI is the flagship. JadeOS-Agent Suite is the freight-vertical productization. Hot Shot TMS is the
                    operator-built system of record. Same builder. Same persistent-memory substrate. One cap table.
                </p>
                <div className="grid lg:grid-cols-3 gap-5">
                    {/* JadeOS Quantum AI flagship */}
                    <div className="relative border border-[#7c5cff33] p-6 bg-gradient-to-br from-[#0a0c18] to-[#15102a]" data-testid="product-jade">
                        <CornerBrackets />
                        <div className="mono-label text-[11px] text-[#7c5cff]">PRODUCT 01 · FLAGSHIP</div>
                        <h3 className="font-display font-black text-white text-3xl mt-2">JadeOS Quantum AI</h3>
                        <p className="font-mono-tech text-[13px] text-white/65 mt-3 leading-relaxed">
                            The AI command center for builders, founders, and lifelong learners. 50+ modules,
                            voice-first <span className="text-[#7c5cff]">&ldquo;Hey Jade&rdquo;</span>, persistent memory across modules.
                            <span className="text-[#7c5cff]"> 128-qubit Qiskit Aer + Claude Haiku 4.5.</span>
                        </p>
                        <div className="grid grid-cols-3 gap-2 mt-5">
                            {[["50+", "MODULES"], ["128", "QUBITS"], ["3", "BETA"]].map(([v, k], i) => (
                                <div key={i} className="border border-white/10 p-3">
                                    <div className="font-display font-black text-[#7c5cff] text-xl">{v}</div>
                                    <div className="mono-label text-[9px] text-white/55 mt-1">{k}</div>
                                </div>
                            ))}
                        </div>
                        <ul className="mt-5 space-y-1.5">
                            {[
                                "Unifies 8-14 fragmented SaaS subs · $187/mo avg power-user spend",
                                "Voice-first · biometric Face ID sign-in · 7-day session",
                                "Pricing · Free / Pro $19/mo / Enterprise $99-499/user/mo",
                                "5-yr arc · $31.7M ARR by Y5 · break-even Q4 Y3",
                            ].map((t, i) => (
                                <li key={i} className="font-mono-tech text-[11px] text-white/75 flex gap-2">
                                    <span className="text-[#7c5cff]">●</span>{t}
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* JadeOS-Agent Suite */}
                    <div className="relative border border-[#00ffff33] p-6 bg-gradient-to-br from-[#0a0c18] to-[#0a1820]" data-testid="product-jadeos">
                        <CornerBrackets />
                        <div className="mono-label text-[11px] text-[#00ffff]">PRODUCT 02 · FREIGHT-VERTICAL AGENTS</div>
                        <h3 className="font-display font-black text-white text-3xl mt-2">JadeOS-Agent Suite</h3>
                        <p className="font-mono-tech text-[13px] text-white/65 mt-3 leading-relaxed">
                            Six AI agents that sit on top of any TMS &mdash; Hot Shot or Descartes/McLeod/TMW.
                            Rate-floor guard, audit chain, workflow memory, active claims all production-class.
                            The vertical productization of JadeOS Quantum AI for logistics.
                        </p>
                        <div className="grid grid-cols-3 gap-2 mt-5">
                            {[["6", "AGENTS"], ["1", "LIVE PROD"], ["2", "LIVE PARTIAL"]].map(([v, k], i) => (
                                <div key={i} className="border border-white/10 p-3">
                                    <div className="font-display font-black text-[#00ffff] text-xl">{v}</div>
                                    <div className="mono-label text-[9px] text-white/55 mt-1">{k}</div>
                                </div>
                            ))}
                        </div>
                        <ul className="mt-5 space-y-1.5">
                            {[
                                "Sells on top of Hot Shot OR any incumbent TMS · two GTM tracks",
                                "Rate-floor guard + SHA-256 immutable audit chain",
                                "Workflow memory · 30+ day prospect threads with auto-distillation",
                                "Public ROI Modeler · industry-benchmark math",
                            ].map((t, i) => (
                                <li key={i} className="font-mono-tech text-[11px] text-white/75 flex gap-2">
                                    <span className="text-[#00ffff]">●</span>{t}
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Hot Shot TMS */}
                    <div className="relative border border-[#ccff0033] p-6 bg-gradient-to-br from-[#0a0c18] to-[#13180a]" data-testid="product-tms">
                        <CornerBrackets />
                        <div className="mono-label text-[11px] text-[#ccff00]">PRODUCT 03 · SYSTEM OF RECORD</div>
                        <h3 className="font-display font-black text-white text-3xl mt-2">Hot Shot TMS</h3>
                        <p className="font-mono-tech text-[13px] text-white/65 mt-3 leading-relaxed">
                            Operator-built transportation management for the hot-shot &middot; small-to-mid carrier
                            segment that <span className="text-[#ccff00]">incumbent TMS vendors don&apos;t serve well</span>.
                            Build complete &middot; deployment-ready &middot; zero customers yet by design.
                        </p>
                        <div className="grid grid-cols-3 gap-2 mt-5">
                            {[["BUILD", "COMPLETE"], ["6", "MODES"], ["READY", "TO DEPLOY"]].map(([v, k], i) => (
                                <div key={i} className="border border-white/10 p-3">
                                    <div className="font-display font-black text-[#ccff00] text-xl">{v}</div>
                                    <div className="mono-label text-[9px] text-white/55 mt-1">{k}</div>
                                </div>
                            ))}
                        </div>
                        <ul className="mt-5 space-y-1.5">
                            {[
                                "Targets the underserved hot-shot / small-to-mid carrier segment",
                                "Brand re-themer · type a company name → app re-skins instantly",
                                "Live map · dispatch board · BOL · invoicing · accessorials",
                                "Pairs with JadeOS-Agent Suite agents for the full stack story",
                            ].map((t, i) => (
                                <li key={i} className="font-mono-tech text-[11px] text-white/75 flex gap-2">
                                    <span className="text-[#ccff00]">●</span>{t}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </Section>

            {/* ===================== SIX AGENTS ===================== */}
            <Section id="agents" eyebrow="03 · PRODUCT · JadeOS-Agent Suite" eyebrowColor={ACCENT.violet}
                     title={<>Six agents.<br /><span style={{ color: ACCENT.violet }}>Ship-status honest.</span></>}>
                <p className="font-mono-tech text-[13px] text-white/65 max-w-3xl leading-relaxed -mt-3 mb-6">
                    We label exactly what ships in production, what&apos;s live-partial, and what&apos;s a deterministic-MVP
                    activated at pilot start. No daylight between the brief and the platform.
                </p>
                <div className="grid lg:grid-cols-2 gap-3">
                    {modules.map((m) => <ModuleCard key={m.id} m={m} />)}
                </div>
            </Section>

            {/* ===================== ROI ===================== */}
            <Section id="roi" eyebrow="04 · ECONOMICS" eyebrowColor={ACCENT.jade}
                     title={<>Mid-market · 175 trucks ·<br /><span style={{ color: ACCENT.jade }}>$2M+ annual savings.</span></>}>
                {roi ? (
                    <div className="space-y-5">
                        <div className="grid sm:grid-cols-3 gap-3">
                            <Stat k="ANNUAL SAVINGS" v={`$${(roi.annual_total_savings_usd / 1e6).toFixed(2)}M`} c={ACCENT.jade} />
                            <Stat k="3-YR NPV @ 10%" v={`$${(roi.three_year.npv_at_10pct_discount_usd / 1e6).toFixed(2)}M`} c={ACCENT.cyan} />
                            <Stat k="PAYBACK" v={`${roi.three_year.payback_months}mo`} c={ACCENT.violet} />
                        </div>
                        <div className="border border-white/10 p-5">
                            <div className="mono-label text-[10px] text-[#ccff00] mb-3">6 SAVINGS CATEGORIES · ALL BENCHMARK-CITED</div>
                            <div className="grid sm:grid-cols-3 gap-2">
                                {Object.entries(roi.by_category_usd || {}).map(([k, v]) => (
                                    <div key={k} className="border border-white/5 p-3">
                                        <div className="mono-label text-[10px] text-white/55">{k.replace(/_usd$/, "").replace(/_/g, " ").toUpperCase()}</div>
                                        <div className="font-display font-bold text-[#ccff00] text-lg mt-1">${(v / 1000).toFixed(0)}k</div>
                                    </div>
                                ))}
                            </div>
                            <div className="font-mono-tech text-[10px] text-white/45 mt-3 pt-3 border-t border-white/5">
                                Sources · {(roi.sources || []).join(" · ")}
                            </div>
                        </div>
                        <Link to="/demo" className="btn-jade text-sm inline-flex items-center gap-2"
                              style={{ background: "transparent", border: `1px solid ${ACCENT.jade}55`, color: ACCENT.jade }}>
                            ▶ RECOMPUTE LIVE · /demo → OPS WORKBENCH
                        </Link>
                    </div>
                ) : <div className="font-mono-tech text-white/45">// loading ROI model…</div>}
            </Section>

            {/* ===================== TRACTION ===================== */}
            <Section id="traction" eyebrow="05 · BUILD STATUS" eyebrowColor={ACCENT.cyan}
                     title={<>Build complete.<br /><span style={{ color: ACCENT.cyan }}>Ready to deploy. Not a deck. A working stack.</span></>}>
                <p className="font-mono-tech text-[13px] text-white/65 max-w-3xl leading-relaxed -mt-3 mb-6">
                    Everything below exists and runs today. Zero paying customers by design &mdash; we&apos;re
                    raising to launch into the market, not to finish the product.
                </p>
                <div className="grid lg:grid-cols-3 gap-4">
                    {[
                        { c: ACCENT.jade, h: "Hot Shot TMS · Build Complete", b: "Fully developed transportation management for the hot-shot / small-to-mid carrier segment. Deployment-ready · zero customers yet by design." },
                        { c: ACCENT.cyan, h: "JadeOS-Agent Suite Production Console", b: "/demo · 7 agent tabs · 6 OP labs · 8-phase 43-substep execution tracker. Live today." },
                        { c: ACCENT.violet, h: "Brand Re-themer", b: "Type a company name → Claude Sonnet 4.5 writes a brand profile → app re-skins instantly. Live." },
                        { c: ACCENT.magenta, h: "Risk Guard · Audit Chain", b: "Rate-floor guard with HARD/SOFT block. SHA-256 immutable event log. /api/audit/verify." },
                        { c: ACCENT.amber, h: "Workflow Memory + Claims", b: "30+ day prospect threads with auto-distillation. Active claims filing with mixed autonomy." },
                        { c: ACCENT.jade, h: "Real Prospects · FMCSA-anchored", b: "14 verified Minnesota mid-market carriers seeded as the hot list. Zero synthetic leads." },
                    ].map((t, i) => (
                        <div key={i} className="relative border p-5" style={{ borderColor: `${t.c}33`, background: `${t.c}06` }}>
                            <CornerBrackets />
                            <div className="mono-label text-[10px] mb-2" style={{ color: t.c }}>● BUILT · READY</div>
                            <div className="font-display font-black text-white text-base">{t.h}</div>
                            <p className="font-mono-tech text-[11px] text-white/70 mt-2 leading-relaxed">{t.b}</p>
                        </div>
                    ))}
                </div>
            </Section>

            {/* ===================== THE ASK ===================== */}
            <Section id="ask" eyebrow="06 · THE ASK" eyebrowColor={ACCENT.amber}
                     title={<>$2.0M seed.<br /><span style={{ color: ACCENT.amber }}>SAFE · $12M post-money cap · 18-month runway · 3 products in market.</span></>}>
                <p className="font-mono-tech text-[13px] text-white/65 max-w-3xl leading-relaxed -mt-3 mb-6">
                    JadeOS Quantum AI flagship into the prosumer/builder market. JadeOS-Agent Suite agents into existing-TMS freight shops.
                    Hot Shot TMS into the underserved hot-shot segment. Three GTM tracks. One sole founder operating
                    lean. One cap table.
                </p>
                <div className="grid lg:grid-cols-3 gap-3">
                    {[
                        { h: "USE OF FUNDS", c: ACCENT.jade, items: [
                            "Engineering 45% · Eng #2 (full-stack AI) + tooling · Jade Pro · mobile · SOC 2 prep",
                            "Growth 25% · PMM hire · ads + content · 50k MAU target",
                            "Ops & Compliance 12% · Legal · SOC 2 · insurance · accounting",
                            "Cloud + LLM infra 10% · 18-month runway of compute",
                            "Founder salary 8% · 18 months · sole founder by design",
                        ] },
                        { h: "LAND IN 18 MONTHS", c: ACCENT.cyan, items: [
                            "JadeOS Quantum AI · 50k MAU · 1,000+ paying users · $50k+ MRR Series A trigger",
                            "JadeOS-Agent Suite · 2 paid agent conversions in existing-TMS shops",
                            "Hot Shot TMS · 3 paid launches in underserved hot-shot segment",
                            "Brand-themed enterprise re-deploy (any product)",
                        ] },
                        { h: "SHIP IN 18 MONTHS", c: ACCENT.violet, items: [
                            "Jade Pro · mobile app · marketplace beta",
                            "JadeOS-Agent Suite · M2 fuel-MILP · M3 audit-pack PDF · multi-tenant JWT",
                            "Hot Shot TMS · multi-tenant rollout · brand-themer at scale",
                            "SOC 2 readiness narrative across all three",
                        ] },
                    ].map((g, i) => (
                        <div key={i} className="relative border p-5" style={{ borderColor: `${g.c}55`, background: `${g.c}08` }}>
                            <CornerBrackets />
                            <div className="mono-label text-[12px] mb-3" style={{ color: g.c }}>● {g.h}</div>
                            <ul className="space-y-2">
                                {g.items.map((t, j) => (
                                    <li key={j} className="font-mono-tech text-[11.5px] text-white/85 flex gap-2 leading-relaxed">
                                        <span style={{ color: g.c }}>▸</span>{t}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>
            </Section>

            {/* ===================== INVESTOR PACKAGE ===================== */}
            <Section id="package" eyebrow="07 · INVESTOR PACKAGE" eyebrowColor={ACCENT.magenta}
                     title={<>Take the package home.<br /><span style={{ color: ACCENT.magenta }}>Three PDFs · one ROI tool · one live demo.</span></>}>
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    {[
                        { label: "INVESTOR PITCH", sub: "12-slide widescreen PDF", c: ACCENT.violet,
                          href: `${API_BASE}/agent/workbench/deck.pdf`, ext: true, tid: "pkg-deck" },
                        { label: "TECHNICAL BRIEF", sub: "10-section operator-grade", c: ACCENT.amber,
                          href: `${API_BASE}/agent/workbench/document.pdf`, ext: true, tid: "pkg-brief" },
                        { label: "EXECUTION PLAN", sub: "8 phases · 43 substeps · ~116h", c: ACCENT.jade,
                          href: `${API_BASE}/agent/workbench/plan.pdf`, ext: true, tid: "pkg-plan" },
                        { label: "LIVE PRODUCT", sub: "/demo · 7 agent tabs", c: ACCENT.cyan,
                          href: "/demo", ext: false, tid: "pkg-demo" },
                    ].map((p, i) => {
                        const Cmp = p.ext ? "a" : Link;
                        const props = p.ext
                            ? { href: p.href, target: "_blank", rel: "noreferrer" }
                            : { to: p.href };
                        return (
                            <Cmp key={i} {...props} data-testid={p.tid}
                                 className="relative border p-5 hover:bg-white/[0.03] transition block"
                                 style={{ borderColor: `${p.c}55` }}>
                                <CornerBrackets />
                                <div className="mono-label text-[10px]" style={{ color: p.c }}>↓ {p.label}</div>
                                <div className="font-mono-tech text-[11px] text-white/65 mt-2 leading-snug">{p.sub}</div>
                                <div className="mono-label text-[10px] mt-4" style={{ color: p.c }}>OPEN →</div>
                            </Cmp>
                        );
                    })}
                </div>
                <div className="mt-10 border border-[#ccff0055] p-6 bg-[#ccff0008]">
                    <div className="mono-label text-[#ccff00]">NEXT STEP</div>
                    <h3 className="font-display font-black text-white text-2xl mt-2">30-minute discovery this week.</h3>
                    <p className="font-mono-tech text-[12.5px] text-white/75 mt-3 leading-relaxed">
                        We&apos;ll walk you through the live product, the FMCSA-verified prospect list,
                        the rate-floor guard in action, and the 90-day pilot structure with success
                        metrics declared in writing.
                    </p>
                    <a href={`mailto:${askEmail}?subject=JADE%20OS%20%2B%20Hot%20Shot%20TMS%20Investor%20Discovery&body=I'd%20like%2030%20minutes%20to%20review%20the%20joint%20stack.`}
                       data-testid="invite-final-cta"
                       className="btn-jade text-sm mt-5 inline-flex items-center gap-2"
                       style={{ background: ACCENT.jade, color: "#0a0c18" }}>
                        → BOOK 30-MIN DISCOVERY
                    </a>
                </div>
            </Section>

            <div className="py-10 text-center font-mono-tech text-[10px] text-white/35">
                JadeOS · Hot Shot TMS · Minneapolis · 2026 · investor-grade build
            </div>
        </div>
    );
}
