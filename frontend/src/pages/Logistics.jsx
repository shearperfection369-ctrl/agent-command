/**
 * Logistics — vertical landing page tuned to freight / 3PL / brokerage pain.
 *
 * Drives Lighthouse pilot applications + design-partner DMs.
 * Network-relevant for the operator's MSP-area logistics cluster.
 */
import { useNavigate } from "react-router-dom";
import { CornerBrackets, SectionLabel } from "../components/Brackets";

const PAINS = [
    { k: "Driver shortage tax", v: "Your ops team is on the phone all day chasing capacity. JADE drafts the carrier outreach in under a second per load. Tier-1 carriers get the loads they fit; your humans only see the misses." },
    { k: "BOL chaos", v: "97.4% field accuracy on 14-field BOL extraction. PDFs, scanned faxes, broker emails — all parsed into structured JSON in 800ms. No more 4pm Friday re-keying marathons." },
    { k: "Invoice exceptions", v: "JADE reads carrier invoices, cross-checks rate confirmations, and flags the discrepancies. Your AP team only sees the real exceptions — not 200 of them, the 12 that matter." },
    { k: "Shipper comms", v: "Inbound 'where's my load?' emails get drafted-and-staged responses with the live status pulled from your TMS. Your team approves. JADE sends." },
    { k: "Lane scoring + carrier matching", v: "Every load gets a Tier-1 / Tier-2 / Tier-3 fit score with the rationale. No more guesswork. No more 'I think Schneider does this lane.'" },
];

const PROOF = [
    { n: "184", l: "emails auto-triaged per day on a benchmark MSP freight workload" },
    { n: "97.4%", l: "BOL field-extraction accuracy on a 14-field schema" },
    { n: "800ms", l: "average BOL extract time per page" },
    { n: "84%", l: "support tickets drafted by JADE were sent without an edit" },
    { n: "38s", l: "average triage time per inbound support ticket" },
];

export default function Logistics() {
    const nav = useNavigate();
    return (
        <div className="bg-console min-h-screen" data-testid="logistics-page">
            {/* HERO */}
            <section className="px-6 sm:px-10 lg:px-16 pt-24 pb-12 max-w-6xl mx-auto">
                <SectionLabel idx={0} color="#ccff00">VERTICAL · 01 · LOGISTICS</SectionLabel>
                <h1 className="font-display font-black text-white text-5xl sm:text-6xl lg:text-7xl tracking-tighter mt-3 leading-[0.95]">
                    Driver shortage <span className="accent-pink">tax</span>.
                    <br />
                    BOL <span className="accent-cyan">chaos</span>.
                    <br />
                    Invoice <span className="accent-violet">exceptions</span>.
                </h1>
                <p className="text-white/65 text-lg mt-6 max-w-2xl leading-relaxed">
                    Your dispatchers, your brokers, your AP team — drowning in tasks that don't move freight. JADE OS runs them, faster, cleaner, all night. So your humans focus on the lanes that win.
                </p>
                <div className="flex flex-wrap gap-3 mt-8">
                    <button
                        data-testid="logistics-pilot-cta"
                        onClick={() => nav("/lighthouse?vertical=freight")}
                        className="btn-jade text-sm px-6 py-3"
                    >▶ APPLY FOR LIGHTHOUSE PILOT</button>
                    <button
                        data-testid="logistics-demo-cta"
                        onClick={() => nav("/demo")}
                        className="btn-ghost text-sm px-6 py-3"
                    >→ RUN A LIVE BOL EXTRACT</button>
                </div>
            </section>

            {/* PROMO VIDEO */}
            <section className="px-6 sm:px-10 lg:px-16 py-12 max-w-6xl mx-auto">
                <div className="deck-card p-0 relative overflow-hidden" data-testid="logistics-reel">
                    <CornerBrackets />
                    <video
                        controls
                        autoPlay
                        muted
                        loop
                        playsInline
                        src={`${process.env.REACT_APP_BACKEND_URL}/api/promo/video?v=3`}
                        className="w-full h-auto block bg-black"
                    />
                </div>
            </section>

            {/* PAINS */}
            <section className="px-6 sm:px-10 lg:px-16 py-16 max-w-6xl mx-auto" data-testid="logistics-pains">
                <SectionLabel idx={2} color="#ff3b8a">PAIN · FIVE</SectionLabel>
                <h2 className="font-display font-black text-white text-4xl tracking-tighter mt-2">Five fires we put out.</h2>
                <div className="grid sm:grid-cols-2 lg:grid-cols-2 gap-4 mt-8">
                    {PAINS.map((p, i) => (
                        <div key={i} className="deck-card p-5 relative" data-testid={`pain-${i}`}>
                            <CornerBrackets />
                            <div className="mono-label text-[#ff3b8a]">PAIN · 0{i + 1}</div>
                            <div className="font-display font-bold text-white text-xl mt-2">{p.k}</div>
                            <p className="font-mono-tech text-xs text-white/75 mt-3 leading-relaxed">{p.v}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* PROOF */}
            <section className="px-6 sm:px-10 lg:px-16 py-16 max-w-6xl mx-auto bg-[#06081a] border-y border-white/10" data-testid="logistics-proof">
                <SectionLabel idx={3} color="#00ffff">PROOF · BENCHMARKS</SectionLabel>
                <h2 className="font-display font-black text-white text-4xl tracking-tighter mt-2">Receipts.</h2>
                <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4 mt-8">
                    {PROOF.map((p, i) => (
                        <div key={i} className="border border-white/10 p-4">
                            <div className="font-display font-black text-[#ccff00] text-3xl">{p.n}</div>
                            <div className="font-mono-tech text-[11px] text-white/65 mt-2 leading-snug">{p.l}</div>
                        </div>
                    ))}
                </div>
            </section>

            {/* WHO WE'RE BUILT FOR */}
            <section className="px-6 sm:px-10 lg:px-16 py-16 max-w-6xl mx-auto">
                <SectionLabel idx={4} color="#7c5cff">BUILT · FOR</SectionLabel>
                <h2 className="font-display font-black text-white text-4xl tracking-tighter mt-2">Who this is for.</h2>
                <div className="grid sm:grid-cols-3 gap-4 mt-8">
                    <div className="deck-card p-5 relative" data-testid="built-for-broker">
                        <CornerBrackets />
                        <div className="mono-label text-[#ccff00]">FREIGHT BROKERS</div>
                        <p className="font-mono-tech text-xs text-white/75 mt-3 leading-relaxed">
                            Asset-light brokerages running 100-10,000 loads/month. Your ops team is the bottleneck. JADE clears the queue.
                        </p>
                    </div>
                    <div className="deck-card p-5 relative" data-testid="built-for-3pl">
                        <CornerBrackets />
                        <div className="mono-label text-[#00ffff]">3PLS & WAREHOUSING</div>
                        <p className="font-mono-tech text-xs text-white/75 mt-3 leading-relaxed">
                            Multi-shipper operations with intake / receiving / shipping document chaos. JADE indexes the chaos into clean structured data.
                        </p>
                    </div>
                    <div className="deck-card p-5 relative" data-testid="built-for-carrier">
                        <CornerBrackets />
                        <div className="mono-label text-[#ff3b8a]">REGIONAL CARRIERS</div>
                        <p className="font-mono-tech text-xs text-white/75 mt-3 leading-relaxed">
                            500-5,000 truck fleets. The phone-tree is the workflow. JADE drafts the dispatcher's outbound the moment a load drops.
                        </p>
                    </div>
                </div>
            </section>

            {/* CTA */}
            <section className="px-6 sm:px-10 lg:px-16 py-20 max-w-6xl mx-auto text-center" data-testid="logistics-cta">
                <SectionLabel idx={5} color="#ccff00">NEXT MOVE</SectionLabel>
                <h2 className="font-display font-black text-white text-5xl tracking-tighter mt-2">
                    Five <span className="accent-lime">design-partner</span> slots.
                </h2>
                <p className="text-white/65 text-lg mt-4 max-w-2xl mx-auto">
                    Six-month JADE OS pilot. White-glove onboarding. Co-authored case study. First-come, first-locked.
                </p>
                <div className="flex flex-wrap gap-3 justify-center mt-8">
                    <button
                        data-testid="logistics-bottom-apply"
                        onClick={() => nav("/lighthouse?vertical=freight")}
                        className="btn-jade text-sm px-6 py-3"
                    >▶ APPLY · LIGHTHOUSE PILOT</button>
                    <button
                        data-testid="logistics-bottom-demo"
                        onClick={() => nav("/demo")}
                        className="btn-ghost text-sm px-6 py-3"
                    >→ TRY THE DEMO</button>
                </div>
            </section>
        </div>
    );
}
