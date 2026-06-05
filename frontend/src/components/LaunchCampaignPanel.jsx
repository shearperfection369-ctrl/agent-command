/**
 * LaunchCampaignPanel — admin BIG BANG · LAUNCH tab.
 *
 * Renders the 28-day organic-growth campaign:
 *   • Weekly phase headers (TEASE → REVEAL → PROOF → CONVERT)
 *   • Per-platform post templates with one-click COPY POST
 *   • Re-encoded video assets ready to drop into TikTok/IG/X/LinkedIn/YT
 *   • Growth principles cheat-sheet
 *
 * Endpoints: GET /api/admin/launch/campaign · GET /api/admin/launch/assets
 */
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api, API_BASE } from "../lib/api";
import { CornerBrackets, SectionLabel } from "./Brackets";
import { JadeWorking } from "./JadeAvatar";

const PHASE_COLOR = {
    TEASE: "#7c5cff",
    REVEAL: "#ccff00",
    PROOF: "#00ffff",
    CONVERT: "#ff3b8a",
};

const PLATFORM_COLOR = {
    linkedin: "#00ffff",
    x: "#ffffff",
    instagram_reel: "#ff3b8a",
    instagram_feed: "#ff3b8a",
    tiktok: "#ccff00",
    youtube_short: "#ff3b8a",
    youtube: "#ff3b8a",
    facebook: "#7c5cff",
    reddit: "#ffce4f",
    hackernews: "#ffce4f",
    threads: "#ccff00",
};

function PlatformBadge({ id, label }) {
    const c = PLATFORM_COLOR[id] || "#ccff00";
    return (
        <span
            data-testid={`platform-badge-${id}`}
            className="mono-label px-2 py-1 border"
            style={{ color: c, borderColor: `${c}55`, background: `${c}11` }}
        >{label}</span>
    );
}

function PostCard({ post }) {
    const [copied, setCopied] = useState(false);
    const fullText = (
        post.body +
        (post.hashtags?.length ? "\n\n" + post.hashtags.join(" ") : "")
    );

    const copy = async () => {
        await navigator.clipboard.writeText(fullText);
        setCopied(true); setTimeout(() => setCopied(false), 1600);
        toast.success(`Copied ${post.platform_label} post`);
    };

    return (
        <div
            data-testid={`post-card-${post.platform}-day-${post.day}`}
            className="border p-4 space-y-3"
            style={{ borderColor: `${PLATFORM_COLOR[post.platform] || "#ccff00"}44`, background: "#06081a" }}
        >
            <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-2 flex-wrap">
                    <span
                        className="mono-label px-2 py-1 border"
                        style={{ color: PHASE_COLOR[post.phase], borderColor: `${PHASE_COLOR[post.phase]}55` }}
                    >DAY {post.day}</span>
                    <PlatformBadge id={post.platform} label={post.platform_label} />
                    <span className="font-mono-tech text-[10px] text-white/45">{post.best_window}</span>
                </div>
                <button
                    data-testid={`copy-post-${post.platform}-${post.day}`}
                    onClick={copy}
                    className="mono-label text-[#ccff00] hover:text-white border border-[#ccff00]/40 hover:border-[#ccff00] px-3 py-1"
                >
                    {copied ? "✓ COPIED" : "↗ COPY POST"}
                </button>
            </div>

            <div className="font-display font-bold text-white text-lg leading-tight">{post.headline}</div>

            <pre
                data-testid={`post-body-${post.platform}-${post.day}`}
                className="font-mono-tech text-[12px] text-white/85 whitespace-pre-wrap leading-relaxed bg-[#02030a] p-3 border border-white/5"
            >{post.body}</pre>

            {post.hashtags?.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                    {post.hashtags.map((h) => (
                        <span key={h} className="font-mono-tech text-[10px] text-[#00ffff]">{h}</span>
                    ))}
                </div>
            )}

            <div className="grid sm:grid-cols-3 gap-3 pt-2 border-t border-white/5">
                <Meta k="FORMAT" v={post.format_spec} />
                <Meta k="TONE" v={post.tone} />
                <Meta k="ASSET" v={post.asset_recommended} mono />
            </div>

            {post.cta && (
                <div className="mono-label text-[#ccff00] text-[10px]">CTA · {post.cta}</div>
            )}
        </div>
    );
}

function Meta({ k, v, mono }) {
    return (
        <div>
            <div className="mono-label text-[9px] text-white/40">{k}</div>
            <div className={mono ? "font-mono-tech text-[10px] text-white/75 mt-1 break-all" : "font-mono-tech text-[10px] text-white/75 mt-1"}>{v}</div>
        </div>
    );
}

function AssetCard({ asset }) {
    const fullUrl = `${(typeof process !== "undefined" && process.env?.REACT_APP_BACKEND_URL) || ""}${asset.url}`;
    const isVideo = asset.name.endsWith(".mp4");
    const isImage = asset.name.endsWith(".jpg") || asset.name.endsWith(".png");
    const isAudio = asset.name.endsWith(".mp3");

    const copy = async () => {
        await navigator.clipboard.writeText(fullUrl);
        toast.success("Public asset URL copied");
    };

    return (
        <div className="deck-card relative" data-testid={`asset-${asset.name}`}>
            <CornerBrackets />
            <div className="p-4 border-b border-white/10 flex items-center justify-between flex-wrap gap-2">
                <span className="mono-label text-[#ccff00]">{asset.name}</span>
                <span className="font-mono-tech text-[10px] text-white/45">{asset.size_mb} MB</span>
            </div>
            <div className="p-4 bg-black flex justify-center items-center min-h-[200px]">
                {isVideo && <video src={fullUrl} controls preload="metadata" className="max-h-[260px] max-w-full" />}
                {isImage && <img src={fullUrl} alt={asset.name} className="max-h-[260px] max-w-full" />}
                {isAudio && <audio src={fullUrl} controls className="w-full" />}
            </div>
            <div className="p-3 flex flex-wrap gap-2 border-t border-white/5">
                <a
                    data-testid={`asset-download-${asset.name}`}
                    href={fullUrl}
                    download={asset.name}
                    className="btn-jade text-xs px-3 py-1.5 inline-flex items-center gap-2"
                >↓ DOWNLOAD</a>
                <button
                    data-testid={`asset-copy-url-${asset.name}`}
                    onClick={copy}
                    className="btn-ghost text-xs px-3 py-1.5"
                >↗ COPY URL</button>
            </div>
        </div>
    );
}

export default function LaunchCampaignPanel() {
    const [campaign, setCampaign] = useState(null);
    const [assets, setAssets] = useState(null);
    const [loading, setLoading] = useState(true);
    const [filterPlatform, setFilterPlatform] = useState("ALL");
    const [filterPhase, setFilterPhase] = useState("ALL");
    const [startDate, setStartDate] = useState("");

    const load = async () => {
        setLoading(true);
        try {
            const params = startDate ? { start_date: startDate } : {};
            const [c, a] = await Promise.all([
                api.get("/admin/launch/campaign", { params }),
                api.get("/admin/launch/assets"),
            ]);
            setCampaign(c.data);
            setAssets(a.data);
        } catch (e) {
            toast.error("Failed to load campaign");
        } finally { setLoading(false); }
    };

    useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

    if (loading) {
        return <div className="deck-card p-12 flex justify-center"><JadeWorking verb="building launch campaign" size={72} /></div>;
    }
    if (!campaign) return null;

    const allPlatforms = ["ALL", ...new Set(campaign.all_posts.map((p) => p.platform))];
    const allPhases = ["ALL", "TEASE", "REVEAL", "PROOF", "CONVERT"];

    const filtered = campaign.all_posts.filter((p) => {
        if (filterPlatform !== "ALL" && p.platform !== filterPlatform) return false;
        if (filterPhase !== "ALL" && p.phase !== filterPhase) return false;
        return true;
    });

    return (
        <div className="space-y-6" data-testid="launch-campaign-panel">
            {/* HERO */}
            <div className="deck-card p-6 relative" data-testid="launch-hero">
                <CornerBrackets />
                <SectionLabel idx={0} color="#ff3b8a">BIG BANG · LAUNCH CAMPAIGN</SectionLabel>
                <h2 className="font-display font-black text-white text-4xl tracking-tighter mt-2">
                    Make a <span className="accent-pink">scene.</span>
                </h2>
                <p className="text-white/65 text-sm mt-3 max-w-2xl leading-relaxed">
                    A 28-day, all-platforms organic-growth playbook tuned for curiosity → reveal → proof → conversion.
                    Every post is pre-written in JADE voice. Every video pre-encoded for the platform. Hit COPY, paste, schedule.
                </p>
                <div className="grid sm:grid-cols-4 gap-4 mt-6">
                    <Stat k="POSTS" v={campaign.total_posts} c="#ccff00" />
                    <Stat k="WEEKS" v={campaign.weeks.length} c="#00ffff" />
                    <Stat k="PLATFORMS" v={Object.keys(campaign.platforms).length} c="#7c5cff" />
                    <Stat k="ASSETS" v={assets?.assets?.length || 0} c="#ff3b8a" />
                </div>

                {/* Schedule control */}
                <div className="mt-6 flex items-end gap-3 flex-wrap">
                    <div>
                        <div className="mono-label text-white/45 mb-2 text-[10px]">CAMPAIGN START DATE</div>
                        <input
                            data-testid="campaign-start-date"
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="input-tech text-xs"
                        />
                    </div>
                    <button data-testid="campaign-reload-btn" onClick={load} className="btn-ghost text-xs">↻ RE-SCHEDULE</button>
                </div>
            </div>

            {/* WEEK STRIP */}
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="launch-weeks">
                {campaign.weeks.map((w) => (
                    <div
                        key={w.week}
                        className="deck-card p-5 relative"
                        style={{ borderTop: `2px solid ${PHASE_COLOR[w.phase.split(" ")[0]] || "#ccff00"}` }}
                    >
                        <CornerBrackets />
                        <div className="mono-label text-white/45 text-[10px]">WEEK {w.week}</div>
                        <div className="font-display font-black text-2xl mt-1" style={{ color: PHASE_COLOR[w.phase.split(" ")[0]] }}>{w.phase}</div>
                        <div className="font-mono-tech text-[11px] text-white/75 mt-3 leading-relaxed">{w.theme}</div>
                        <div className="mt-3 pt-3 border-t border-white/5">
                            <div className="mono-label text-[#ccff00] text-[9px]">GOAL</div>
                            <div className="font-mono-tech text-[10px] text-white/65 mt-1 leading-snug">{w.goal}</div>
                        </div>
                        <div className="mt-2">
                            <div className="mono-label text-[#00ffff] text-[9px]">KPI</div>
                            <div className="font-mono-tech text-[10px] text-white/65 mt-1 leading-snug">{w.kpi}</div>
                        </div>
                    </div>
                ))}
            </div>

            {/* GROWTH PRINCIPLES */}
            <div className="deck-card p-6 relative" data-testid="growth-principles">
                <CornerBrackets />
                <div className="mono-label text-[#7c5cff] mb-3">GROWTH PRINCIPLES · READ BEFORE YOU POST</div>
                <ol className="space-y-2 list-none">
                    {campaign.growth_principles.map((g, i) => (
                        <li key={i} className="font-mono-tech text-xs text-white/85 leading-relaxed flex gap-3">
                            <span className="text-[#ccff00] font-bold">{String(i + 1).padStart(2, "0")}</span>
                            <span>{g}</span>
                        </li>
                    ))}
                </ol>
            </div>

            {/* ASSETS */}
            {assets?.available && (
                <div data-testid="launch-assets-section">
                    <div className="mono-label text-[#ccff00] mb-3">VIDEO ASSETS · DROP-IN READY FOR EVERY PLATFORM</div>
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {assets.assets.map((a) => <AssetCard key={a.name} asset={a} />)}
                    </div>
                </div>
            )}

            {/* POSTS · filtered */}
            <div className="deck-card p-6 relative" data-testid="launch-posts">
                <CornerBrackets />
                <div className="flex items-center justify-between flex-wrap gap-3 mb-5">
                    <div className="mono-label text-[#ff3b8a]">POSTS · COPY · PASTE · SCHEDULE · {filtered.length}/{campaign.all_posts.length}</div>
                    <div className="flex flex-wrap gap-2">
                        <select
                            data-testid="filter-phase"
                            value={filterPhase}
                            onChange={(e) => setFilterPhase(e.target.value)}
                            className="input-tech text-xs py-1.5 w-[140px]"
                        >
                            {allPhases.map((p) => <option key={p} value={p}>{p === "ALL" ? "PHASE · ALL" : `PHASE · ${p}`}</option>)}
                        </select>
                        <select
                            data-testid="filter-platform"
                            value={filterPlatform}
                            onChange={(e) => setFilterPlatform(e.target.value)}
                            className="input-tech text-xs py-1.5 w-[180px]"
                        >
                            {allPlatforms.map((p) => <option key={p} value={p}>{p === "ALL" ? "PLATFORM · ALL" : p.replace(/_/g, " ").toUpperCase()}</option>)}
                        </select>
                    </div>
                </div>
                <div className="grid lg:grid-cols-2 gap-4">
                    {filtered.map((p, i) => <PostCard key={`${p.platform}-${p.day}-${i}`} post={p} />)}
                </div>
            </div>
        </div>
    );
}

function Stat({ k, v, c }) {
    return (
        <div className="border px-4 py-3" style={{ borderColor: `${c}33`, background: `${c}08` }}>
            <div className="mono-label text-[10px]" style={{ color: c }}>{k}</div>
            <div className="font-display font-black text-3xl mt-1" style={{ color: c }}>{v}</div>
        </div>
    );
}
