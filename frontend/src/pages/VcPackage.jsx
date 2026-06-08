/**
 * VcPackage · /vc-package
 *
 * One shareable URL. Investors land here and have everything in one place —
 * promo reel, pitch deck PDFs, live demos, press kit, founder bio, contact.
 *
 * This is a DISTRIBUTION surface, not a pitch surface. Every section ends
 * in a one-click download or external link so the recipient can act
 * immediately. Designed to be dropped in an email or DM.
 */
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CornerBrackets } from "../components/Brackets";
import { ArrowRight, DownloadSimple, ArrowUpRight, Copy, Check } from "@/lib/icons";
import { toast } from "sonner";

const ACCENT = {
    jade: "#ccff00",
    cyan: "#00ffff",
    violet: "#7c5cff",
    magenta: "#ff3b8a",
    amber: "#ffce4f",
};

const API = process.env.REACT_APP_BACKEND_URL;

const STATS = [
    { k: "TICKETS RESOLVED",  v: "6,330",  c: ACCENT.jade,   sub: "tier-1 deflection · 38s avg" },
    { k: "DOCS PARSED",       v: "21,604", c: ACCENT.cyan,   sub: "BOL · invoice · PO" },
    { k: "INDUSTRIES TUNED",  v: "11",     c: ACCENT.violet, sub: "freight · health · saas · …" },
    { k: "AGENTS · SHIPPED",  v: "6 of 6", c: ACCENT.amber,  sub: "production-grade · audited" },
];

const PDFS = [
    {
        id: "deck",
        label: "12-Slide Pitch Deck",
        sub: "Landscape · ~10KB · regenerates fresh on download",
        href: `${API}/api/agent/workbench/deck.pdf`,
        c: ACCENT.jade,
    },
    {
        id: "tech",
        label: "Technical Brief",
        sub: "10-section operator-grade portrait deck · architecture + ROI cases",
        href: `${API}/api/agent/workbench/document.pdf`,
        c: ACCENT.cyan,
    },
    {
        id: "audit",
        label: "Sample 12-Page AI Readiness Audit",
        sub: "What every prospect receives · same engine that runs the consulting layer",
        href: "/audit/broker-free",
        c: ACCENT.violet,
        internal: true,
    },
    {
        id: "playbook",
        label: "Audit Playbook + SOW Templates",
        sub: "4 operator PDFs · checklist, talk track, request letter, pilot agreement",
        href: "/audit/playbook",
        c: ACCENT.amber,
        internal: true,
    },
];

const REEL_VERSIONS = [
    { id: 3, label: "V3 · Split Ops",          c: ACCENT.jade },
    { id: 2, label: "V2 · Trinity Reveal",     c: ACCENT.cyan },
    { id: 1, label: "V1 · Original",           c: ACCENT.violet },
];

const LIVE_LINKS = [
    {
        href: "/invite",
        label: "Full Pitch Page",
        sub: "Trinity hero · live agent status · founder bio",
        c: ACCENT.jade,
    },
    {
        href: "/demo",
        label: "Live Console",
        sub: "Quantum AI · Hot Shot TMS · Trucker AI · Risk Guard · 10 tabs",
        c: ACCENT.cyan,
    },
    {
        href: "/press",
        label: "Press Kit",
        sub: "Logos · 5-color palette · voice sample · approved copy",
        c: ACCENT.violet,
    },
    {
        href: "/lighthouse",
        label: "Lighthouse Program",
        sub: "Founding-customer cohort · 5 seats · 50% off year one for life",
        c: ACCENT.magenta,
    },
    {
        href: "/cases",
        label: "Case Studies",
        sub: "Field reports from existing deployments",
        c: ACCENT.amber,
    },
    {
        href: "/plan",
        label: "Business Plan",
        sub: "Year-1 financial model · team roster · GTM",
        c: ACCENT.jade,
    },
];

const TRINITY = [
    {
        id: "quantum",
        name: "JadeOS Quantum AI",
        tag: "FLAGSHIP",
        c: ACCENT.jade,
        body: "50+ modules · voice-first 'Hey Jade' · 128-qubit Qiskit Aer + Claude Haiku 4.5. Operator-grade memory, claims filing, dispatch optimizer, support triage.",
    },
    {
        id: "agent",
        name: "JadeOS-Agent Suite",
        tag: "VERTICAL",
        c: ACCENT.cyan,
        body: "Six freight-vertical agents · sits on top of any TMS. Carrier vetting, quote negotiation, track-and-trace, doc extract, retention, predictive maintenance.",
    },
    {
        id: "tms",
        name: "Hot Shot TMS",
        tag: "INFRASTRUCTURE",
        c: ACCENT.violet,
        body: "Operator-built system of record for the underserved hot-shot freight segment. Built by a 13-year operator. Currently in production at design partners.",
    },
];

export default function VcPackage() {
    const [reelVersion, setReelVersion] = useState(3);
    const [meta, setMeta] = useState(null);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        // Fetch promo meta so we can show duration / size
        fetch(`${API}/api/promo/meta`).then((r) => r.json()).then(setMeta).catch(() => {});
    }, []);

    const copyShareLink = () => {
        const url = `${window.location.origin}/vc-package`;
        navigator.clipboard?.writeText(url);
        setCopied(true);
        toast.success("Investor link copied · drop it in any DM.");
        setTimeout(() => setCopied(false), 2200);
    };

    const reelSrc = `${API}/api/promo/video?v=${reelVersion}`;

    return (
        <div className="min-h-screen bg-console" data-testid="vc-package-page">
            {/* HERO */}
            <section className="relative overflow-hidden border-b border-white/5">
                <div className="absolute inset-0 grid-bg pointer-events-none" />
                <div className="absolute inset-0 scanlines pointer-events-none opacity-40" />
                <div className="relative max-w-[1400px] mx-auto px-6 lg:px-10 pt-16 lg:pt-24 pb-12">
                    <div className="bracket-frame p-6 lg:p-10 max-w-4xl">
                        <div className="flex items-center gap-3 mb-6 flex-wrap">
                            <span className="dot" />
                            <span className="mono-label text-[#ccff00]">
                                JADEOS · INVESTOR PACKAGE · MINNEAPOLIS · FEB 2026
                            </span>
                        </div>
                        <h1 className="font-display font-black text-white text-5xl sm:text-7xl lg:text-8xl leading-[0.88] tracking-tighter">
                            Three products.<br />
                            <span style={{ color: ACCENT.jade }}>One investable stack.</span>
                        </h1>
                        <p className="mt-6 text-lg sm:text-xl text-white/85 max-w-2xl font-display tracking-tight leading-snug">
                            Everything in one place. Pitch deck, promo reel, live console, press kit,
                            business plan — all downloadable below.
                        </p>
                        <p className="mt-4 text-sm text-white/55 max-w-2xl leading-relaxed">
                            Built solo by a 13-year operator. JadeOS Quantum AI · JadeOS-Agent Suite · Hot Shot TMS.
                            Production-grade. Audited. Honest about what is shipped and what is not.
                        </p>

                        <div className="mt-10 flex flex-wrap gap-3">
                            <button
                                data-testid="vc-share-link-btn"
                                onClick={copyShareLink}
                                className="btn-jade inline-flex items-center gap-2">
                                {copied ? <><Check size={16} weight="bold" /> COPIED</> :
                                          <><Copy size={16} weight="bold" /> COPY INVESTOR LINK</>}
                            </button>
                            <a href="mailto:founder@jadeos.ai?subject=JadeOS · investor sync"
                               data-testid="vc-book-cta"
                               className="btn-ghost inline-flex items-center gap-2">
                                BOOK 20-MIN REVIEW <ArrowRight size={16} weight="bold" />
                            </a>
                        </div>

                        <div className="mt-12 grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
                            {STATS.map((s) => (
                                <div key={s.k} className="border px-4 py-3"
                                     style={{ borderColor: `${s.c}33`, background: `${s.c}08` }}>
                                    <div className="mono-label text-[10px]" style={{ color: s.c }}>{s.k}</div>
                                    <div className="font-display font-black text-2xl mt-1" style={{ color: s.c }}>{s.v}</div>
                                    <div className="font-mono-tech text-[10px] text-white/40 mt-1">{s.sub}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* WATCH · 16s PROMO */}
            <section className="border-b border-white/5 bg-console-2">
                <div className="max-w-[1400px] mx-auto px-6 lg:px-10 py-16 lg:py-20">
                    <div className="flex items-end justify-between flex-wrap gap-4 mb-8">
                        <div>
                            <div className="mono-label text-[#00ffff]">01 · WATCH</div>
                            <h2 className="font-display font-black text-white text-4xl sm:text-5xl mt-2 tracking-tight">
                                16 seconds.
                            </h2>
                        </div>
                        <div className="flex gap-2 flex-wrap">
                            {REEL_VERSIONS.map((r) => (
                                <button
                                    key={r.id}
                                    data-testid={`vc-reel-v${r.id}`}
                                    onClick={() => setReelVersion(r.id)}
                                    className="px-3 py-1.5 mono-label text-[10px] transition"
                                    style={{
                                        border: `1px solid ${reelVersion === r.id ? r.c : "rgba(255,255,255,0.12)"}`,
                                        color: reelVersion === r.id ? r.c : "rgba(255,255,255,0.65)",
                                        background: reelVersion === r.id ? `${r.c}11` : "transparent",
                                    }}>
                                    {r.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="relative border border-white/10 bg-black aspect-video overflow-hidden max-w-4xl mx-auto">
                        <CornerBrackets />
                        {/* key forces re-render when version changes */}
                        <video key={reelVersion}
                               data-testid="vc-promo-reel"
                               controls
                               playsInline
                               className="w-full h-full object-cover">
                            <source src={reelSrc} type="video/mp4" />
                        </video>
                    </div>
                    <div className="flex flex-wrap items-center justify-between gap-3 mt-5 max-w-4xl mx-auto">
                        <div className="font-mono-tech text-[11px] text-white/55">
                            {meta?.resolution && <>{meta.resolution} · </>}
                            {meta?.fps && <>{meta.fps}fps · </>}
                            1080p · clean wordmark · ffmpeg-rendered text (no Sora text artifacts)
                        </div>
                        <a href={reelSrc}
                           data-testid="vc-reel-download"
                           download
                           className="btn-jade text-xs inline-flex items-center gap-2">
                            <DownloadSimple size={14} weight="bold" /> DOWNLOAD MP4
                        </a>
                    </div>
                </div>
            </section>

            {/* READ · THE DECK */}
            <section className="border-b border-white/5">
                <div className="max-w-[1400px] mx-auto px-6 lg:px-10 py-16 lg:py-20">
                    <div className="mono-label text-[#ccff00]">02 · READ</div>
                    <h2 className="font-display font-black text-white text-4xl sm:text-5xl mt-2 tracking-tight">
                        The full deck.
                    </h2>
                    <p className="font-mono-tech text-[12px] text-white/55 mt-3 max-w-2xl">
                        Auto-regenerated from the live data layer every time you click. No stale numbers,
                        no PowerPoint version drift.
                    </p>

                    <div className="mt-10 grid sm:grid-cols-2 gap-4">
                        {PDFS.map((p) => (
                            <PdfCard key={p.id} {...p} />
                        ))}
                    </div>
                </div>
            </section>

            {/* SEE IT LIVE */}
            <section className="border-b border-white/5 bg-console-2">
                <div className="max-w-[1400px] mx-auto px-6 lg:px-10 py-16 lg:py-20">
                    <div className="mono-label text-[#7c5cff]">03 · SEE IT LIVE</div>
                    <h2 className="font-display font-black text-white text-4xl sm:text-5xl mt-2 tracking-tight">
                        Click anything. It works.
                    </h2>
                    <p className="font-mono-tech text-[12px] text-white/55 mt-3 max-w-2xl">
                        Six surfaces. All public. All real product, not screenshots.
                    </p>

                    <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {LIVE_LINKS.map((l) => (
                            <LiveCard key={l.href} {...l} />
                        ))}
                    </div>
                </div>
            </section>

            {/* TRINITY */}
            <section className="border-b border-white/5">
                <div className="max-w-[1400px] mx-auto px-6 lg:px-10 py-16 lg:py-20">
                    <div className="mono-label text-[#00ffff]">04 · THE TRINITY</div>
                    <h2 className="font-display font-black text-white text-4xl sm:text-5xl mt-2 tracking-tight">
                        What you&apos;re investing in.
                    </h2>
                    <div className="mt-10 grid lg:grid-cols-3 gap-4">
                        {TRINITY.map((t) => (
                            <div key={t.id}
                                 className="relative border p-6 bg-[#0a0c18]"
                                 style={{ borderColor: `${t.c}33` }}>
                                <CornerBrackets />
                                <div className="mono-label text-[9.5px]" style={{ color: t.c }}>{t.tag}</div>
                                <h3 className="font-display font-bold text-white text-2xl mt-2 tracking-tight">
                                    {t.name}
                                </h3>
                                <p className="font-mono-tech text-[12px] text-white/80 mt-3 leading-relaxed">
                                    {t.body}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* FOUNDER + CTA */}
            <section className="bg-console-2">
                <div className="max-w-[1400px] mx-auto px-6 lg:px-10 py-16 lg:py-20">
                    <div className="grid lg:grid-cols-[1.4fr_1fr] gap-10 items-start">
                        <div>
                            <div className="mono-label text-[#ccff00]">05 · THE FOUNDER</div>
                            <h2 className="font-display font-black text-white text-4xl sm:text-5xl mt-2 tracking-tight">
                                Oliver Cummins.
                            </h2>
                            <p className="font-mono-tech text-[13px] text-white/85 mt-4 max-w-2xl leading-relaxed">
                                13 years operating in freight + logistics. Built JadeOS solo — engineering, design,
                                product, GTM, support. Looking for a co-conspirator on the cap table, not a passenger.
                            </p>
                            <div className="mt-6 flex flex-wrap gap-3">
                                <a href="mailto:founder@jadeos.ai"
                                   data-testid="vc-founder-email"
                                   className="btn-jade text-sm inline-flex items-center gap-2">
                                    EMAIL FOUNDER · founder@jadeos.ai
                                </a>
                                <a href="https://linkedin.com/in/oliver-cummins-a27304a3/"
                                   target="_blank" rel="noreferrer"
                                   data-testid="vc-founder-linkedin"
                                   className="btn-ghost text-sm inline-flex items-center gap-2">
                                    LINKEDIN <ArrowUpRight size={14} weight="bold" />
                                </a>
                            </div>
                        </div>

                        <div className="relative border border-[#ccff0044] bg-[#0a0c18] p-6">
                            <CornerBrackets />
                            <div className="mono-label text-[10px] text-[#ccff00]">SHARE THIS PACKAGE</div>
                            <p className="font-mono-tech text-[12px] text-white/70 mt-3 leading-relaxed">
                                One link. Everything an investor needs. Drop in any DM, email, or thread.
                            </p>
                            <button
                                data-testid="vc-share-link-btn-footer"
                                onClick={copyShareLink}
                                className="btn-jade w-full mt-5 inline-flex items-center justify-center gap-2">
                                {copied ? <><Check size={16} weight="bold" /> COPIED · GO PASTE IT</> :
                                          <><Copy size={16} weight="bold" /> COPY INVESTOR LINK</>}
                            </button>
                            <div className="font-mono-tech text-[10px] text-white/35 mt-4 break-all">
                                {window.location.origin}/vc-package
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* FOOTER NAV */}
            <section className="border-t border-white/5 py-6 px-6">
                <div className="max-w-[1400px] mx-auto flex flex-wrap justify-between items-center gap-3">
                    <Link to="/" className="mono-label text-[10px] text-white/55 hover:text-[#ccff00]">
                        ◀ HOME
                    </Link>
                    <div className="flex gap-4 flex-wrap">
                        <Link to="/invite"     className="mono-label text-[10px] text-white/55 hover:text-[#ccff00]">PITCH</Link>
                        <Link to="/demo"       className="mono-label text-[10px] text-white/55 hover:text-[#00ffff]">DEMO</Link>
                        <Link to="/press"      className="mono-label text-[10px] text-white/55 hover:text-[#7c5cff]">PRESS</Link>
                        <Link to="/lighthouse" className="mono-label text-[10px] text-white/55 hover:text-[#ff3b8a]">LIGHTHOUSE</Link>
                    </div>
                </div>
            </section>
        </div>
    );
}

function PdfCard({ label, sub, href, c, internal }) {
    const Comp = internal ? Link : "a";
    const props = internal
        ? { to: href }
        : { href, target: "_blank", rel: "noreferrer", download: true };
    return (
        <Comp {...props}
              data-testid={`vc-pdf-${label.toLowerCase().replace(/\W+/g, "-").slice(0, 28)}`}
              className="block relative border p-5 bg-[#0a0c18] hover:bg-[#13152a] transition-colors group"
              style={{ borderColor: `${c}33` }}>
            <CornerBrackets />
            <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                    <div className="mono-label text-[9.5px]" style={{ color: c }}>
                        {internal ? "VIEW" : "DOWNLOAD PDF"}
                    </div>
                    <h3 className="font-display font-bold text-white text-lg mt-1.5 tracking-tight">
                        {label}
                    </h3>
                    <p className="font-mono-tech text-[11px] text-white/55 mt-2 leading-relaxed">
                        {sub}
                    </p>
                </div>
                <div className="text-2xl group-hover:translate-x-1 transition-transform" style={{ color: c }}>
                    {internal ? "▸" : "↓"}
                </div>
            </div>
        </Comp>
    );
}

function LiveCard({ href, label, sub, c }) {
    return (
        <Link to={href}
              data-testid={`vc-live-${label.toLowerCase().replace(/\W+/g, "-").slice(0, 28)}`}
              className="block relative border p-5 bg-[#0a0c18] hover:bg-[#13152a] transition-colors group"
              style={{ borderColor: `${c}33` }}>
            <CornerBrackets />
            <div className="mono-label text-[9.5px]" style={{ color: c }}>OPEN</div>
            <h3 className="font-display font-bold text-white text-lg mt-1.5 tracking-tight">
                {label}
            </h3>
            <p className="font-mono-tech text-[11px] text-white/55 mt-2 leading-relaxed">
                {sub}
            </p>
            <div className="mt-3 mono-label text-[10px] flex items-center gap-1 group-hover:translate-x-1 transition-transform"
                 style={{ color: c }}>
                LAUNCH ▸
            </div>
        </Link>
    );
}
