/**
 * TruckerAIPanel — operator-grade driver tools.
 * EVERY DATA SOURCE IS FREE PUBLIC. No mock data anywhere.
 *
 * Sub-views:
 *   • HOS · 49 CFR §395 compliance calculator
 *   • PARKING · truck stops + rest areas + weigh stations (OpenStreetMap)
 *   • ROUTE · point-to-point routing (OSRM)
 *   • WEATHER · NOAA forecast
 *   • 511 · all 50 state DOT travel info directory
 */
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "./Brackets";
import { JadeWorking } from "./JadeAvatar";

const KIND_COLOR = {
    truck_stop: "#ccff00", fuel: "#00ffff", rest_area: "#7c5cff",
    services: "#ffce4f", weighbridge: "#ff3b8a",
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

function HOSView() {
    const [form, setForm] = useState({
        driving_hours_so_far: 8, on_duty_hours_so_far: 10,
        consecutive_driving_since_break: 4, hours_in_last_8_days: 55,
        carrier_operates_7_day: true, pending_drive_hours: 3,
    });
    const [result, setResult] = useState(null);
    const [busy, setBusy] = useState(false);
    const run = async () => {
        setBusy(true);
        try {
            const { data } = await api.post("/trucker/hos-check", form);
            setResult(data);
        } catch { toast.error("HOS check failed."); }
        finally { setBusy(false); }
    };
    useEffect(() => { run(); }, []);
    return (
        <div className="space-y-4" data-testid="hos-view">
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="mono-label text-[#ccff00] mb-3">49 CFR §395 · HOS COMPLIANCE CALCULATOR</div>
                <div className="grid lg:grid-cols-3 gap-3">
                    {[
                        ["driving_hours_so_far", "DRIVING HOURS THIS DUTY"],
                        ["on_duty_hours_so_far", "ON-DUTY HOURS THIS DUTY"],
                        ["consecutive_driving_since_break", "DRIVING SINCE LAST BREAK"],
                        ["hours_in_last_8_days", "HOURS LAST 8 DAYS"],
                        ["pending_drive_hours", "PLANNED DRIVE NEXT"],
                    ].map(([k, label]) => (
                        <div key={k}>
                            <label className="mono-label text-[10px] text-white/55">{label}</label>
                            <input data-testid={`hos-${k}`} type="number" step="0.25" value={form[k]} onChange={(e) => setForm({ ...form, [k]: parseFloat(e.target.value || 0) })} className="input-tech text-xs w-full mt-1" />
                        </div>
                    ))}
                    <div className="flex items-end">
                        <label className="flex items-center gap-2 mono-label text-[10px] text-white/85 cursor-pointer">
                            <input type="checkbox" checked={form.carrier_operates_7_day} onChange={(e) => setForm({ ...form, carrier_operates_7_day: e.target.checked })} />
                            7-DAY CARRIER (70/8 RULE)
                        </label>
                    </div>
                </div>
                <button data-testid="hos-run-btn" onClick={run} disabled={busy} className="btn-jade text-xs mt-4 disabled:opacity-50">{busy ? "CHECKING…" : "▶ RUN COMPLIANCE CHECK"}</button>
            </div>
            {result && (
                <div className="deck-card p-5 relative" data-testid="hos-result" style={{ borderColor: result.ok ? "#ccff0055" : "#ff3b8a55" }}>
                    <CornerBrackets />
                    <div className="flex items-baseline justify-between gap-3 flex-wrap">
                        <div className="mono-label text-[11px]" style={{ color: result.ok ? "#ccff00" : "#ff3b8a" }}>
                            {result.ok ? "✓ COMPLIANT · CLEARED TO DRIVE" : "✗ VIOLATIONS · CANNOT DRIVE"}
                        </div>
                        <span className="font-mono-tech text-[10px] text-white/55">window · {result.rules_applied?.weekly_window}</span>
                    </div>
                    <div className="grid sm:grid-cols-4 gap-3 mt-4">
                        <Stat k="DRIVE LEFT" v={`${result.remaining.driving_h}h`} c="#ccff00" sub="of 11h limit" />
                        <Stat k="DUTY LEFT" v={`${result.remaining.on_duty_h}h`} c="#00ffff" sub="of 14h window" />
                        <Stat k="UNTIL BREAK" v={`${result.remaining.until_30min_break_h}h`} c="#ffce4f" sub="30-min required" />
                        <Stat k="WEEKLY LEFT" v={`${result.remaining.weekly_h}h`} c="#7c5cff" sub={`of ${result.rules_applied?.weekly_window}`} />
                    </div>
                    {result.issues.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-white/5">
                            <div className="mono-label text-[10px] text-[#ff3b8a]">VIOLATIONS ({result.issues.length})</div>
                            <ul className="space-y-1.5 mt-2">{result.issues.map((i, n) => <li key={n} className="font-mono-tech text-[11px] text-white/85 flex gap-2"><span className="text-[#ff3b8a]">✗</span>{i}</li>)}</ul>
                        </div>
                    )}
                    {result.warnings.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-white/5">
                            <div className="mono-label text-[10px] text-[#ffce4f]">WARNINGS</div>
                            <ul className="space-y-1.5 mt-2">{result.warnings.map((w, n) => <li key={n} className="font-mono-tech text-[11px] text-white/85 flex gap-2"><span className="text-[#ffce4f]">⚠</span>{w}</li>)}</ul>
                        </div>
                    )}
                    <div className="mt-3 pt-3 border-t border-white/5 font-mono-tech text-[10px] text-white/40">
                        ▸ source · <a href={result.rules_applied?.source?.split(" — ")[1]} target="_blank" rel="noreferrer" className="text-[#00ffff] hover:underline">{result.rules_applied?.source}</a>
                    </div>
                </div>
            )}
        </div>
    );
}

function ParkingView() {
    const [query, setQuery] = useState("Eagan, MN");
    const [radius, setRadius] = useState(25);
    const [data, setData] = useState(null);
    const [busy, setBusy] = useState(false);
    const search = async () => {
        if (!query.trim()) return;
        setBusy(true);
        try {
            const { data } = await api.post("/trucker/truck-stops", { query, radius_miles: radius });
            setData(data);
            toast.success(`${data.count} stops within ${radius}mi`);
        } catch (e) { toast.error(e?.response?.data?.detail || "Search failed."); }
        finally { setBusy(false); }
    };
    return (
        <div className="space-y-4" data-testid="parking-view">
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="mono-label text-[#7c5cff] mb-3">PARKING + AMENITIES · OPENSTREETMAP</div>
                <div className="grid lg:grid-cols-[1fr_140px_160px] gap-2 items-end">
                    <div>
                        <label className="mono-label text-[10px] text-white/55">LOCATION OR ADDRESS</label>
                        <input data-testid="parking-query" value={query} onChange={(e) => setQuery(e.target.value)} className="input-tech text-xs w-full mt-1" placeholder="city, address, or coords" />
                    </div>
                    <div>
                        <label className="mono-label text-[10px] text-white/55">RADIUS · MI</label>
                        <input data-testid="parking-radius" type="number" value={radius} onChange={(e) => setRadius(parseFloat(e.target.value || 25))} className="input-tech text-xs w-full mt-1" />
                    </div>
                    <button data-testid="parking-search-btn" onClick={search} disabled={busy} className="btn-jade text-xs disabled:opacity-50">{busy ? "SEARCHING…" : "▶ SEARCH OSM"}</button>
                </div>
            </div>
            {data && (
                <div className="deck-card relative" data-testid="parking-result">
                    <CornerBrackets />
                    <div className="px-5 py-3 border-b border-white/10 flex justify-between flex-wrap gap-2">
                        <div className="mono-label text-[#ccff00]">{data.count} STOPS · &lt;{data.radius_miles}MI</div>
                        <span className="font-mono-tech text-[10px] text-white/40">▸ source · openstreetmap.org · live overpass query</span>
                    </div>
                    {data.stops.length === 0 ? (
                        <div className="px-5 py-8 text-center font-mono-tech text-xs text-white/40">// no matches — try wider radius or different location</div>
                    ) : (
                        <div className="divide-y divide-white/5 max-h-[480px] overflow-y-auto">
                            {data.stops.map((s) => (
                                <div key={s.id} className="px-5 py-3 grid grid-cols-[110px_1fr_100px_70px] gap-3 items-start" data-testid={`stop-${s.id}`}>
                                    <span className="mono-label text-[10px]" style={{ color: KIND_COLOR[s.kind] || "#ccff00" }}>● {s.kind.toUpperCase()}</span>
                                    <div>
                                        <div className="font-display font-bold text-white text-sm">{s.name}</div>
                                        <div className="font-mono-tech text-[10px] text-white/55 mt-0.5">{s.address || "—"}</div>
                                        <div className="flex gap-2 mt-1 flex-wrap">
                                            {s.hgv_friendly && <span className="mono-label text-[9px] text-[#ccff00]">HGV ✓</span>}
                                            {s.diesel && <span className="mono-label text-[9px] text-[#00ffff]">DIESEL</span>}
                                            {s.showers && <span className="mono-label text-[9px] text-[#7c5cff]">SHOWERS</span>}
                                            {s.parking_capacity && <span className="mono-label text-[9px] text-[#ffce4f]">CAP {s.parking_capacity}</span>}
                                        </div>
                                    </div>
                                    <span className="font-display font-bold text-base text-[#ccff00] text-right">{s.distance_miles}mi</span>
                                    <a href={s.source_url} target="_blank" rel="noreferrer" className="font-mono-tech text-[10px] text-[#00ffff] hover:underline text-right">OSM →</a>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

function RouteView() {
    const [origin, setOrigin] = useState("Eagan, MN");
    const [dest, setDest] = useState("Dallas, TX");
    const [data, setData] = useState(null);
    const [busy, setBusy] = useState(false);
    const compute = async () => {
        setBusy(true);
        try {
            const { data } = await api.post("/trucker/route", { origin, destination: dest });
            setData(data);
        } catch (e) { toast.error(e?.response?.data?.detail || "Routing failed."); }
        finally { setBusy(false); }
    };
    return (
        <div className="space-y-4" data-testid="route-view">
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="mono-label text-[#00ffff] mb-3">ROUTE · OSRM PUBLIC</div>
                <div className="grid lg:grid-cols-[1fr_1fr_140px] gap-2 items-end">
                    <div><label className="mono-label text-[10px] text-white/55">ORIGIN</label>
                        <input data-testid="route-origin" value={origin} onChange={(e) => setOrigin(e.target.value)} className="input-tech text-xs w-full mt-1" /></div>
                    <div><label className="mono-label text-[10px] text-white/55">DESTINATION</label>
                        <input data-testid="route-dest" value={dest} onChange={(e) => setDest(e.target.value)} className="input-tech text-xs w-full mt-1" /></div>
                    <button data-testid="route-go-btn" onClick={compute} disabled={busy} className="btn-jade text-xs disabled:opacity-50">{busy ? "ROUTING…" : "▶ COMPUTE"}</button>
                </div>
            </div>
            {data && (
                <div className="deck-card p-5 relative" data-testid="route-result">
                    <CornerBrackets />
                    <div className="grid sm:grid-cols-3 gap-3">
                        <Stat k="DISTANCE" v={`${data.distance_miles}mi`} c="#ccff00" />
                        <Stat k="DURATION · AUTO" v={`${Math.floor(data.duration_minutes / 60)}h ${Math.round(data.duration_minutes % 60)}m`} c="#00ffff" />
                        <Stat k="STEPS" v={data.steps_count} c="#7c5cff" />
                    </div>
                    <div className="mt-4 pt-3 border-t border-white/5">
                        <div className="mono-label text-[10px] text-[#ffce4f]">⚠ WARNINGS</div>
                        <ul className="space-y-1.5 mt-2">{data.warnings.map((w, n) => <li key={n} className="font-mono-tech text-[11px] text-white/85 flex gap-2"><span className="text-[#ffce4f]">⚠</span>{w}</li>)}</ul>
                    </div>
                    <div className="mt-3 pt-3 border-t border-white/5 font-mono-tech text-[10px] text-white/40">
                        ▸ source · <a href={data.source_url} target="_blank" rel="noreferrer" className="text-[#00ffff] hover:underline">{data.source_url}</a> · profile <span className="text-[#ccff00]">{data.profile}</span>
                    </div>
                </div>
            )}
        </div>
    );
}

function WeatherView() {
    const [query, setQuery] = useState("Eagan, MN");
    const [data, setData] = useState(null);
    const [busy, setBusy] = useState(false);
    const fetch = async () => {
        setBusy(true);
        try {
            const { data } = await api.post("/trucker/weather", { query });
            setData(data);
        } catch (e) { toast.error(e?.response?.data?.detail || "Weather fetch failed."); }
        finally { setBusy(false); }
    };
    return (
        <div className="space-y-4" data-testid="weather-view">
            <div className="deck-card p-5 relative">
                <CornerBrackets />
                <div className="mono-label text-[#ffce4f] mb-3">WEATHER · NOAA · POINT FORECAST</div>
                <div className="flex gap-2 items-end">
                    <div className="flex-1"><label className="mono-label text-[10px] text-white/55">LOCATION</label>
                        <input data-testid="weather-query" value={query} onChange={(e) => setQuery(e.target.value)} className="input-tech text-xs w-full mt-1" /></div>
                    <button data-testid="weather-fetch-btn" onClick={fetch} disabled={busy} className="btn-jade text-xs disabled:opacity-50">{busy ? "FETCHING…" : "▶ FETCH"}</button>
                </div>
            </div>
            {data && (
                <div className="grid lg:grid-cols-2 gap-3" data-testid="weather-result">
                    {data.periods.map((p, i) => (
                        <div key={i} className="deck-card p-4 relative">
                            <CornerBrackets />
                            <div className="flex items-baseline justify-between">
                                <div className="mono-label text-[#ffce4f]">{p.name}</div>
                                <div className="font-display font-black text-2xl text-white">{p.temperature}°{p.temperature_unit}</div>
                            </div>
                            <div className="font-mono-tech text-[11px] text-white/85 mt-1">{p.short_forecast}</div>
                            <div className="font-mono-tech text-[10px] text-white/55 mt-1">wind · {p.wind_speed} {p.wind_direction}</div>
                            <div className="font-mono-tech text-[10px] text-white/65 mt-2 leading-snug">{p.detailed_forecast}</div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function State511View() {
    const [data, setData] = useState([]);
    useEffect(() => { (async () => {
        try { const { data } = await api.get("/trucker/state-511"); setData(data.states); }
        catch { toast.error("Directory load failed."); }
    })(); }, []);
    return (
        <div className="deck-card relative" data-testid="state-511-view">
            <CornerBrackets />
            <div className="px-5 py-3 border-b border-white/10">
                <div className="mono-label text-[#ccff00]">STATE DOT 511 DIRECTORY · ALL 50</div>
                <div className="font-mono-tech text-[10px] text-white/55 mt-1">Live road conditions · closures · construction · weight + truck restrictions per state. Click any to open.</div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2 p-4">
                {data.map((s) => (
                    <a key={s.state} href={s.url} target="_blank" rel="noreferrer" data-testid={`511-${s.state}`}
                        className="border border-white/10 hover:border-[#ccff00] px-3 py-2 transition group">
                        <div className="font-display font-black text-[#ccff00] text-xl group-hover:text-[#00ffff]">{s.state}</div>
                        <div className="font-mono-tech text-[10px] text-white/55 mt-0.5 leading-snug">{s.name}</div>
                    </a>
                ))}
            </div>
        </div>
    );
}

export default function TruckerAIPanel() {
    const [view, setView] = useState("hos");
    const VIEWS = [
        { id: "hos", label: "HOS · §395", c: "#ccff00" },
        { id: "parking", label: "PARKING", c: "#7c5cff" },
        { id: "route", label: "ROUTE", c: "#00ffff" },
        { id: "weather", label: "WEATHER", c: "#ffce4f" },
        { id: "511", label: "511 · ALL 50", c: "#ff3b8a" },
    ];
    return (
        <div className="space-y-6" data-testid="trucker-panel">
            <div className="deck-card p-6 relative">
                <CornerBrackets />
                <SectionLabel idx={0} color="#ccff00">TRUCKER · DRIVER OPS</SectionLabel>
                <h2 className="font-display font-black text-white text-4xl tracking-tighter mt-2">
                    Verifiable. <span className="accent-cyan">Free public data only.</span>
                </h2>
                <p className="text-white/65 text-sm mt-3 max-w-2xl leading-relaxed">
                    HOS compliance (49 CFR §395) · OSM truck stops · OSRM routing · NOAA weather · 50-state DOT 511.
                    Every answer is sourced — no fabrication, no mock data, no paid keys required.
                </p>
                <div className="grid sm:grid-cols-5 gap-3 mt-5">
                    <Stat k="HOS RULES" v="§395" c="#ccff00" sub="49 CFR codified" />
                    <Stat k="MAP DATA" v="OSM" c="#7c5cff" sub="openstreetmap.org" />
                    <Stat k="ROUTING" v="OSRM" c="#00ffff" sub="project-osrm.org" />
                    <Stat k="WEATHER" v="NOAA" c="#ffce4f" sub="api.weather.gov" />
                    <Stat k="511 STATES" v="50" c="#ff3b8a" sub="curated directory" />
                </div>
            </div>
            <div className="flex flex-wrap gap-2">
                {VIEWS.map((v) => {
                    const active = view === v.id;
                    return (
                        <button key={v.id} data-testid={`trucker-view-${v.id}`} onClick={() => setView(v.id)}
                            className="px-4 py-2 mono-label text-[11px] transition"
                            style={{
                                border: `1px solid ${active ? v.c : "rgba(255,255,255,0.10)"}`,
                                color: active ? v.c : "rgba(255,255,255,0.55)",
                                background: active ? `${v.c}11` : "transparent",
                            }}>{v.label}</button>
                    );
                })}
            </div>
            {view === "hos" && <HOSView />}
            {view === "parking" && <ParkingView />}
            {view === "route" && <RouteView />}
            {view === "weather" && <WeatherView />}
            {view === "511" && <State511View />}
        </div>
    );
}
