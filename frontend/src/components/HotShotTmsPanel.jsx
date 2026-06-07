/**
 * HotShotTmsPanel — Embedded preview of the Hot Shot TMS UI inside /demo.
 * Lets VCs click through 4 representative TMS screens during a discovery call
 * without leaving the JADE OS console.
 *
 * All data here is illustrative SAMPLE data — clearly labeled as a preview of
 * the production-ready Hot Shot TMS build.
 */
import { useState } from "react";
import { CornerBrackets } from "./Brackets";

const VIEWS = [
    { id: "dispatch", label: "DISPATCH BOARD", c: "#ccff00" },
    { id: "map", label: "LIVE MAP", c: "#00ffff" },
    { id: "fleet", label: "FLEET + DRIVERS", c: "#7c5cff" },
    { id: "billing", label: "BOL + INVOICING", c: "#ff3b8a" },
];

const STATUS_COLOR = {
    "PLANNED": "#ffce4f",
    "DISPATCHED": "#00ffff",
    "PICKED-UP": "#7c5cff",
    "IN-TRANSIT": "#00ffff",
    "DELIVERED": "#ccff00",
    "EXCEPTION": "#ff3b8a",
};

const SAMPLE_LOADS = [
    { id: "L-2841", customer: "Carlson Wholesale", origin: "Mpls, MN", dest: "Madison, WI", driver: "A. Iverson", truck: "T-447", mode: "TL", revenue: 1825, status: "IN-TRANSIT", eta: "Today 16:40" },
    { id: "L-2842", customer: "Northern Tool Co", origin: "Burnsville, MN", dest: "Duluth, MN", driver: "B. Petersen", truck: "T-318", mode: "TL", revenue: 950, status: "DISPATCHED", eta: "Today 19:10" },
    { id: "L-2843", customer: "Cargill Edina HQ", origin: "Edina, MN", dest: "Fargo, ND", driver: "—", truck: "—", mode: "LTL", revenue: 1240, status: "PLANNED", eta: "Tomorrow 09:00" },
    { id: "L-2844", customer: "Bay & Bay Logistics", origin: "Roseville, MN", dest: "St. Cloud, MN", driver: "D. Olsen", truck: "T-512", mode: "TL", revenue: 685, status: "DELIVERED", eta: "Done · 12:14" },
    { id: "L-2845", customer: "ATS Specialized", origin: "St. Paul, MN", dest: "Sioux Falls, SD", driver: "E. Larson", truck: "T-209", mode: "TL", revenue: 2180, status: "PICKED-UP", eta: "Today 22:30" },
    { id: "L-2846", customer: "3M Maplewood", origin: "Maplewood, MN", dest: "Eau Claire, WI", driver: "F. Nguyen", truck: "T-661", mode: "TL", revenue: 1395, status: "EXCEPTION", eta: "DEF fault · paused" },
    { id: "L-2847", customer: "Lakeville Motor Exp", origin: "Lakeville, MN", dest: "Hudson, WI", driver: "—", truck: "—", mode: "LTL", revenue: 480, status: "PLANNED", eta: "Tomorrow 11:00" },
];

const SAMPLE_TRUCKS = [
    { id: "T-318", driver: "B. Petersen", status: "ON-DUTY", lat: 44.78, lon: -93.28, hosRemaining: 6.5, lastReport: "12s ago" },
    { id: "T-447", driver: "A. Iverson", status: "DRIVING", lat: 44.94, lon: -93.09, hosRemaining: 4.2, lastReport: "8s ago" },
    { id: "T-512", driver: "D. Olsen", status: "OFF-DUTY", lat: 45.20, lon: -93.20, hosRemaining: 10.5, lastReport: "1m ago" },
    { id: "T-209", driver: "E. Larson", status: "DRIVING", lat: 44.79, lon: -94.66, hosRemaining: 3.0, lastReport: "5s ago" },
    { id: "T-661", driver: "F. Nguyen", status: "EXCEPTION", lat: 44.95, lon: -92.99, hosRemaining: 5.8, lastReport: "31s ago" },
];

function PreviewBanner() {
    return (
        <div className="relative border border-[#ccff0044] p-3 bg-[#ccff0008]" data-testid="tms-preview-banner">
            <div className="flex items-baseline justify-between gap-3 flex-wrap">
                <div className="flex items-baseline gap-3 flex-wrap">
                    <span className="mono-label text-[10px] text-[#ccff00]">● PREVIEW</span>
                    <span className="font-mono-tech text-[11px] text-white/70">
                        Sample data shown · the full Hot Shot TMS build is deployment-ready · zero customers yet by design (raising to launch)
                    </span>
                </div>
                <a href="mailto:founder@jadeos.ai?subject=Hot%20Shot%20TMS%20full%20demo%20request"
                   className="mono-label text-[10px] text-[#ccff00] hover:underline">→ REQUEST FULL TMS DEMO</a>
            </div>
        </div>
    );
}

function DispatchBoard() {
    const totalRev = SAMPLE_LOADS.reduce((a, l) => a + l.revenue, 0);
    const byStatus = SAMPLE_LOADS.reduce((a, l) => { a[l.status] = (a[l.status] || 0) + 1; return a; }, {});
    return (
        <div className="space-y-3" data-testid="tms-dispatch">
            <div className="grid sm:grid-cols-4 gap-2">
                <div className="border border-white/10 px-3 py-2 bg-[#0a0c18]">
                    <div className="mono-label text-[10px] text-[#ccff00]">OPEN LOADS</div>
                    <div className="font-display font-black text-[#ccff00] text-2xl mt-1">{SAMPLE_LOADS.length}</div>
                </div>
                <div className="border border-white/10 px-3 py-2 bg-[#0a0c18]">
                    <div className="mono-label text-[10px] text-[#00ffff]">DAY REVENUE</div>
                    <div className="font-display font-black text-[#00ffff] text-2xl mt-1">${totalRev.toLocaleString()}</div>
                </div>
                <div className="border border-white/10 px-3 py-2 bg-[#0a0c18]">
                    <div className="mono-label text-[10px] text-[#ff3b8a]">EXCEPTIONS</div>
                    <div className="font-display font-black text-[#ff3b8a] text-2xl mt-1">{byStatus["EXCEPTION"] || 0}</div>
                </div>
                <div className="border border-white/10 px-3 py-2 bg-[#0a0c18]">
                    <div className="mono-label text-[10px] text-[#7c5cff]">PLANNED</div>
                    <div className="font-display font-black text-[#7c5cff] text-2xl mt-1">{byStatus["PLANNED"] || 0}</div>
                </div>
            </div>
            <div className="relative deck-card overflow-hidden" data-testid="tms-load-table">
                <CornerBrackets />
                <div className="overflow-x-auto">
                    <table className="w-full text-[11px] font-mono-tech min-w-[860px]">
                        <thead>
                            <tr className="text-left border-b border-white/10 bg-[#0a0c18]">
                                {["LOAD", "CUSTOMER", "ORIGIN → DEST", "MODE", "DRIVER / TRUCK", "REV", "STATUS", "ETA"].map((h) => (
                                    <th key={h} className="px-3 py-2 mono-label text-[10px] text-white/55">{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {SAMPLE_LOADS.map((l) => (
                                <tr key={l.id} className="border-b border-white/5 hover:bg-white/[0.02]">
                                    <td className="px-3 py-2.5 font-display font-bold text-white">{l.id}</td>
                                    <td className="px-3 py-2.5 text-white/85">{l.customer}</td>
                                    <td className="px-3 py-2.5 text-white/65">{l.origin} <span className="text-[#ccff00]">→</span> {l.dest}</td>
                                    <td className="px-3 py-2.5 text-[#7c5cff]">{l.mode}</td>
                                    <td className="px-3 py-2.5 text-white/75">{l.driver} <span className="text-white/35">/</span> {l.truck}</td>
                                    <td className="px-3 py-2.5 text-[#ccff00]">${l.revenue.toLocaleString()}</td>
                                    <td className="px-3 py-2.5">
                                        <span className="mono-label text-[10px]" style={{ color: STATUS_COLOR[l.status] }}>● {l.status}</span>
                                    </td>
                                    <td className="px-3 py-2.5 text-white/65">{l.eta}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

function LiveMap() {
    // Bounding box covering greater Minneapolis-St. Paul + Mankato + Eau Claire
    const minLat = 44.5, maxLat = 45.5, minLon = -94.8, maxLon = -92.5;
    const W = 100, H = 60;
    const project = (lat, lon) => ({
        x: ((lon - minLon) / (maxLon - minLon)) * W,
        y: H - ((lat - minLat) / (maxLat - minLat)) * H,
    });
    return (
        <div className="space-y-3" data-testid="tms-map">
            <div className="relative deck-card p-4 bg-[#06080f]">
                <CornerBrackets />
                <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
                    <div className="mono-label text-[#00ffff]">LIVE FLEET · MINNEAPOLIS / ST. PAUL REGION</div>
                    <span className="font-mono-tech text-[10px] text-white/55">{SAMPLE_TRUCKS.length} TRUCKS · TELEMATICS POLL 10s</span>
                </div>
                <div className="relative border border-white/10 aspect-[5/3] overflow-hidden"
                     style={{ background: "radial-gradient(circle at 50% 50%, #0a1422 0%, #06080f 80%)" }}>
                    {/* fake "road" grid */}
                    <svg viewBox={`0 0 ${W} ${H}`} className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
                        {/* lat gridlines */}
                        {[0.25, 0.5, 0.75].map((p, i) => (
                            <line key={`h${i}`} x1="0" y1={H * p} x2={W} y2={H * p} stroke="#1a2030" strokeWidth="0.15" />
                        ))}
                        {[0.25, 0.5, 0.75].map((p, i) => (
                            <line key={`v${i}`} x1={W * p} y1="0" x2={W * p} y2={H} stroke="#1a2030" strokeWidth="0.15" />
                        ))}
                        {/* "river" diagonal */}
                        <path d={`M ${W * 0.1} ${H * 0.95} Q ${W * 0.45} ${H * 0.55} ${W * 0.7} ${H * 0.15}`}
                              fill="none" stroke="#0f3a4a" strokeWidth="0.8" opacity="0.6" />
                    </svg>
                    {/* Trucks */}
                    {SAMPLE_TRUCKS.map((t, i) => {
                        const p = project(t.lat, t.lon);
                        const color = t.status === "EXCEPTION" ? "#ff3b8a"
                            : t.status === "DRIVING" ? "#00ffff"
                            : t.status === "ON-DUTY" ? "#ccff00"
                            : "#7c5cff";
                        return (
                            <div key={i} className="absolute" style={{ left: `${p.x}%`, top: `${p.y / H * 100}%`, transform: "translate(-50%, -50%)" }}>
                                <div className="relative">
                                    <span className="block w-3 h-3 rounded-full" style={{ background: color, boxShadow: `0 0 12px ${color}` }} />
                                    <span className="absolute top-3.5 left-1/2 -translate-x-1/2 mono-label text-[9px] whitespace-nowrap px-1.5 py-0.5 bg-[#0a0c18] border border-white/10" style={{ color }}>
                                        {t.id}
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                    <div className="absolute top-3 left-3 mono-label text-[10px] text-white/45">LAT {minLat}–{maxLat} · LON {minLon}–{maxLon}</div>
                </div>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-2" data-testid="tms-fleet-strip">
                {SAMPLE_TRUCKS.map((t) => {
                    const c = t.status === "EXCEPTION" ? "#ff3b8a"
                        : t.status === "DRIVING" ? "#00ffff"
                        : t.status === "ON-DUTY" ? "#ccff00"
                        : "#7c5cff";
                    return (
                        <div key={t.id} className="border border-white/10 p-3 bg-[#0a0c18]">
                            <div className="flex items-baseline justify-between">
                                <span className="font-display font-black text-white text-base">{t.id}</span>
                                <span className="mono-label text-[9px]" style={{ color: c }}>● {t.status}</span>
                            </div>
                            <div className="font-mono-tech text-[10px] text-white/65 mt-1">{t.driver}</div>
                            <div className="font-mono-tech text-[10px] text-[#ccff00] mt-1">HOS {t.hosRemaining}h</div>
                            <div className="font-mono-tech text-[9px] text-white/35 mt-1">{t.lastReport}</div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

function FleetDrivers() {
    const drivers = [
        { id: "DR-101", name: "A. Iverson", tenure: "47mo", milesYTD: 88420, retention: "LOW", endorsements: ["TWIC", "H"], hosState: "DRIVING · 4.2h left" },
        { id: "DR-102", name: "B. Petersen", tenure: "11mo", milesYTD: 21800, retention: "MEDIUM", endorsements: ["H"], hosState: "ON-DUTY · 6.5h left" },
        { id: "DR-103", name: "D. Olsen", tenure: "62mo", milesYTD: 92110, retention: "LOW", endorsements: ["TWIC", "H", "T"], hosState: "OFF-DUTY · resets at 02:00" },
        { id: "DR-104", name: "E. Larson", tenure: "5mo", milesYTD: 11420, retention: "HIGH", endorsements: ["—"], hosState: "DRIVING · 3.0h left" },
        { id: "DR-105", name: "F. Nguyen", tenure: "28mo", milesYTD: 64880, retention: "MEDIUM", endorsements: ["H"], hosState: "EXCEPTION · DEF fault paused" },
    ];
    const RBADGE = { LOW: "#ccff00", MEDIUM: "#ffce4f", HIGH: "#ff3b8a" };
    return (
        <div className="space-y-3" data-testid="tms-fleet-drivers">
            <div className="relative deck-card overflow-hidden">
                <CornerBrackets />
                <div className="px-4 py-3 border-b border-white/10 mono-label text-[#7c5cff]">DRIVER ROSTER · {drivers.length} ACTIVE</div>
                <div className="overflow-x-auto">
                    <table className="w-full text-[11px] font-mono-tech min-w-[800px]">
                        <thead>
                            <tr className="text-left border-b border-white/5 bg-[#0a0c18]">
                                {["ID", "DRIVER", "TENURE", "YTD MILES", "ENDORSEMENTS", "HOS STATE", "RETENTION (M5)"].map((h) => (
                                    <th key={h} className="px-3 py-2 mono-label text-[10px] text-white/55">{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {drivers.map((d) => (
                                <tr key={d.id} className="border-b border-white/5 hover:bg-white/[0.02]">
                                    <td className="px-3 py-2.5 font-display font-bold text-white">{d.id}</td>
                                    <td className="px-3 py-2.5 text-white/85">{d.name}</td>
                                    <td className="px-3 py-2.5 text-[#00ffff]">{d.tenure}</td>
                                    <td className="px-3 py-2.5 text-[#ccff00]">{d.milesYTD.toLocaleString()}</td>
                                    <td className="px-3 py-2.5 text-white/65">{d.endorsements.join(" · ")}</td>
                                    <td className="px-3 py-2.5 text-white/65">{d.hosState}</td>
                                    <td className="px-3 py-2.5">
                                        <span className="mono-label text-[10px]" style={{ color: RBADGE[d.retention] }}>● {d.retention}</span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
            <div className="border border-[#7c5cff44] bg-[#7c5cff08] p-4">
                <div className="mono-label text-[10px] text-[#7c5cff] mb-2">JADE OS M5 INTEGRATION</div>
                <div className="font-mono-tech text-[11px] text-white/75 leading-relaxed">
                    Every driver row carries a live JADE OS retention band sourced from <span className="text-[#ccff00]">/api/agent/retention/risk</span>.
                    Click a driver in the production build to see the weighted factors (home-time deficit, pay stagnation, tenure cliff)
                    and recommended actions.
                </div>
            </div>
        </div>
    );
}

function BillingBol() {
    const invoices = [
        { id: "INV-44183", load: "L-2841", customer: "Carlson Wholesale", amount: 1825, status: "PAID", due: "Net 30 · paid 12 days early" },
        { id: "INV-44184", load: "L-2844", customer: "Bay & Bay Logistics", amount: 685, status: "INVOICED", due: "Net 30 · 18 days remaining" },
        { id: "INV-44185", load: "L-2842", customer: "Northern Tool Co", amount: 950, status: "READY-TO-INVOICE", due: "POD received · invoice queued" },
    ];
    const SBADGE = { PAID: "#ccff00", INVOICED: "#00ffff", "READY-TO-INVOICE": "#ffce4f", OVERDUE: "#ff3b8a" };
    return (
        <div className="space-y-3" data-testid="tms-billing">
            <div className="grid sm:grid-cols-4 gap-2">
                <div className="border border-white/10 px-3 py-2 bg-[#0a0c18]">
                    <div className="mono-label text-[10px] text-[#ccff00]">DAY-RECEIVED</div>
                    <div className="font-display font-black text-[#ccff00] text-xl mt-1">$1,825</div>
                </div>
                <div className="border border-white/10 px-3 py-2 bg-[#0a0c18]">
                    <div className="mono-label text-[10px] text-[#00ffff]">DAY-INVOICED</div>
                    <div className="font-display font-black text-[#00ffff] text-xl mt-1">$685</div>
                </div>
                <div className="border border-white/10 px-3 py-2 bg-[#0a0c18]">
                    <div className="mono-label text-[10px] text-[#ffce4f]">READY · WAITING</div>
                    <div className="font-display font-black text-[#ffce4f] text-xl mt-1">$950</div>
                </div>
                <div className="border border-white/10 px-3 py-2 bg-[#0a0c18]">
                    <div className="mono-label text-[10px] text-[#ff3b8a]">EXCEPTIONS</div>
                    <div className="font-display font-black text-[#ff3b8a] text-xl mt-1">$1,395</div>
                </div>
            </div>
            <div className="relative deck-card overflow-hidden">
                <CornerBrackets />
                <div className="px-4 py-3 border-b border-white/10 mono-label text-[#ff3b8a]">INVOICES · LAST 24h</div>
                <div className="overflow-x-auto">
                    <table className="w-full text-[11px] font-mono-tech min-w-[760px]">
                        <thead>
                            <tr className="text-left border-b border-white/5 bg-[#0a0c18]">
                                {["INVOICE", "LOAD", "CUSTOMER", "AMOUNT", "STATUS", "DUE"].map((h) => (
                                    <th key={h} className="px-3 py-2 mono-label text-[10px] text-white/55">{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {invoices.map((iv) => (
                                <tr key={iv.id} className="border-b border-white/5 hover:bg-white/[0.02]">
                                    <td className="px-3 py-2.5 font-display font-bold text-white">{iv.id}</td>
                                    <td className="px-3 py-2.5 text-[#7c5cff]">{iv.load}</td>
                                    <td className="px-3 py-2.5 text-white/85">{iv.customer}</td>
                                    <td className="px-3 py-2.5 text-[#ccff00]">${iv.amount.toLocaleString()}</td>
                                    <td className="px-3 py-2.5">
                                        <span className="mono-label text-[10px]" style={{ color: SBADGE[iv.status] }}>● {iv.status}</span>
                                    </td>
                                    <td className="px-3 py-2.5 text-white/65">{iv.due}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
            <div className="border border-[#ff3b8a44] bg-[#ff3b8a08] p-4">
                <div className="mono-label text-[10px] text-[#ff3b8a] mb-2">JADE OS RISK GUARD INTEGRATION</div>
                <div className="font-mono-tech text-[11px] text-white/75 leading-relaxed">
                    Every quote that becomes an invoice is first validated against <span className="text-[#ccff00]">/api/quotes/validate</span> — the rate-floor guard
                    HARD-BLOCKS below-floor sells. The SHA-256 audit chain captures the decision regardless of outcome.
                </div>
            </div>
        </div>
    );
}

export default function HotShotTmsPanel() {
    const [view, setView] = useState("dispatch");
    return (
        <div className="space-y-4" data-testid="tms-panel">
            <div className="relative deck-card p-5 bg-gradient-to-br from-[#0a0c18] to-[#0f1426]">
                <CornerBrackets />
                <div className="flex justify-between items-baseline flex-wrap gap-3">
                    <div>
                        <div className="mono-label text-[11px] text-[#ccff00]">HOT SHOT TMS · PREVIEW</div>
                        <h2 className="font-display font-black text-white text-2xl mt-1">Operator-built TMS · deployment-ready</h2>
                        <p className="font-mono-tech text-[11.5px] text-white/65 mt-1.5 leading-relaxed max-w-2xl">
                            The system of record paired with JADE OS. Click through the dispatch board, live map, fleet roster, and BOL/invoicing
                            views to see the surface VCs would be funding. Sample data shown.
                        </p>
                    </div>
                </div>
            </div>
            <PreviewBanner />
            <div className="flex flex-wrap gap-2" data-testid="tms-view-switcher">
                {VIEWS.map((v) => {
                    const active = view === v.id;
                    return (
                        <button key={v.id} data-testid={`tms-view-${v.id}`} onClick={() => setView(v.id)}
                            className="px-3 py-2 mono-label text-[11px] transition"
                            style={{ border: `1px solid ${active ? v.c : "rgba(255,255,255,0.10)"}`,
                                color: active ? v.c : "rgba(255,255,255,0.55)",
                                background: active ? `${v.c}11` : "transparent" }}>
                            {v.label}
                        </button>
                    );
                })}
            </div>
            {view === "dispatch" && <DispatchBoard />}
            {view === "map" && <LiveMap />}
            {view === "fleet" && <FleetDrivers />}
            {view === "billing" && <BillingBol />}
        </div>
    );
}
