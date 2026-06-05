/**
 * IntegrationsScaffoldPanel — admin tab showing every wire-in stub + activation hint.
 *
 * Each row reflects the GET /admin/integrations-scaffold contract:
 *   • Sentry      · drop SENTRY_DSN (backend) + REACT_APP_SENTRY_DSN (frontend)
 *   • RAG         · per-tenant vector store · drop VECTOR_STORE_PROVIDER + provider key
 *   • Client Auth · magic-link · drop RESEND_API_KEY to send email
 *   • Resend      · transactional email · drop RESEND_API_KEY to flush queued sends
 */
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "./Brackets";
import { JadeWorking } from "./JadeAvatar";

function StatusBadge({ on, label }) {
    return (
        <span
            className="mono-label text-[10px] px-2 py-1 border"
            style={{
                color: on ? "#0a0c18" : "#ffce4f",
                borderColor: on ? "#ccff00" : "#ffce4f55",
                background: on ? "#ccff00" : "transparent",
            }}
        >{on ? "WIRED · LIVE" : label || "AWAITING KEY"}</span>
    );
}

function ScaffoldRow({ name, color, configured, fields, hint, extras, testid }) {
    return (
        <div className="deck-card relative p-5" style={{ borderColor: `${color}55` }} data-testid={testid}>
            <CornerBrackets />
            <div className="flex items-baseline justify-between gap-3 flex-wrap">
                <div className="font-display font-black text-white text-xl" style={{ color }}>{name}</div>
                <StatusBadge on={configured} />
            </div>
            {fields && fields.length > 0 && (
                <div className="grid sm:grid-cols-2 gap-2 mt-3">
                    {fields.map((f, i) => (
                        <div key={i} className="border border-white/10 px-3 py-2 flex items-baseline justify-between gap-2">
                            <span className="mono-label text-[10px] text-white/55">{f.k}</span>
                            <span className="font-mono-tech text-[11px]" style={{ color: f.c || "#ccff00" }}>{f.v}</span>
                        </div>
                    ))}
                </div>
            )}
            {extras && (
                <div className="mt-3 pt-3 border-t border-white/5 font-mono-tech text-[11px] text-white/75 leading-relaxed">{extras}</div>
            )}
            {hint && (
                <div className="mt-3 pt-3 border-t border-white/5 font-mono-tech text-[10px] text-[#ffce4f] leading-snug">
                    <span className="text-[#ffce4f]">▸ ACTIVATE</span> · {hint}
                </div>
            )}
        </div>
    );
}

export default function IntegrationsScaffoldPanel() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    // RAG quick-test state
    const [tenant, setTenant] = useState("acme-freight");
    const [ingestTitle, setIngestTitle] = useState("");
    const [ingestContent, setIngestContent] = useState("");
    const [query, setQuery] = useState("");
    const [queryResult, setQueryResult] = useState(null);
    const [busy, setBusy] = useState(false);

    const load = async () => {
        try {
            const { data } = await api.get("/admin/integrations-scaffold");
            setData(data);
        } catch { toast.error("Failed to load integrations scaffold"); }
        finally { setLoading(false); }
    };

    useEffect(() => { load(); }, []);

    const ingest = async () => {
        if (!tenant.trim() || !ingestTitle.trim() || !ingestContent.trim()) {
            toast.error("Tenant, title and content all required.");
            return;
        }
        setBusy(true);
        try {
            await api.post("/rag/ingest", { tenant_id: tenant, title: ingestTitle, content: ingestContent });
            setIngestTitle(""); setIngestContent("");
            toast.success("Doc ingested to per-tenant store.");
            load();
        } catch { toast.error("Ingest failed."); }
        finally { setBusy(false); }
    };

    const runQuery = async () => {
        if (!tenant.trim() || !query.trim()) return;
        setBusy(true);
        try {
            const { data } = await api.post("/rag/query", { tenant_id: tenant, question: query, k: 5 });
            setQueryResult(data);
        } catch { toast.error("Query failed."); }
        finally { setBusy(false); }
    };

    if (loading) return <div className="deck-card p-12 flex justify-center"><JadeWorking verb="probing scaffolds" size={72} /></div>;
    if (!data) return null;

    const totalWired = ["sentry", "rag", "client_auth", "resend"].filter((k) => {
        if (k === "rag") return data.rag.embeddings_configured;
        if (k === "client_auth") return data.client_auth.email_delivery_configured;
        return data[k].configured;
    }).length;

    return (
        <div className="space-y-6" data-testid="integrations-panel">
            <div className="deck-card p-6 relative">
                <CornerBrackets />
                <SectionLabel idx={0} color="#00ffff">INTEGRATIONS · SCAFFOLDS</SectionLabel>
                <h2 className="font-display font-black text-white text-4xl tracking-tighter mt-2">
                    Pre-wired. <span className="accent-cyan">Drop the key, ship.</span>
                </h2>
                <p className="text-white/65 text-sm mt-3 max-w-2xl leading-relaxed">
                    {data.scaffold_principle}
                </p>
                <div className="grid sm:grid-cols-4 gap-3 mt-5">
                    <div className="border border-[#ccff00]/30 px-4 py-3">
                        <div className="mono-label text-[10px] text-[#ccff00]">WIRED · LIVE</div>
                        <div className="font-display font-black text-3xl text-[#ccff00] mt-1">{totalWired} / 4</div>
                    </div>
                    <div className="border border-white/10 px-4 py-3 col-span-3">
                        <div className="mono-label text-[10px] text-white/55">CONTRACT</div>
                        <div className="font-mono-tech text-[11px] text-white/85 mt-1 leading-relaxed">
                            Every scaffold below ships behind the same API contract production will use. The keys live in <code className="text-[#00ffff]">backend/.env</code> and <code className="text-[#00ffff]">frontend/.env</code>. No refactor required at activation.
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid lg:grid-cols-2 gap-4">
                <ScaffoldRow
                    name="SENTRY · ERROR MONITORING"
                    color="#ff3b8a"
                    configured={data.sentry.configured && data.sentry.initialized}
                    fields={[
                        { k: "DSN PRESENT", v: data.sentry.configured ? "YES" : "NO", c: data.sentry.configured ? "#ccff00" : "#ffce4f" },
                        { k: "INITIALIZED", v: data.sentry.initialized ? "YES" : "NO", c: data.sentry.initialized ? "#ccff00" : "#ffce4f" },
                        { k: "ENVIRONMENT", v: data.sentry.env, c: "#00ffff" },
                        { k: "RELEASE", v: data.sentry.release, c: "#00ffff" },
                    ]}
                    hint={data.sentry.activate_hint}
                    testid="scaffold-sentry"
                />
                <ScaffoldRow
                    name="RAG · PER-TENANT VECTORS"
                    color="#7c5cff"
                    configured={data.rag.embeddings_configured}
                    fields={[
                        { k: "PROVIDER", v: data.rag.provider.toUpperCase(), c: "#00ffff" },
                        { k: "REAL EMBEDDINGS", v: data.rag.real_embeddings ? "YES" : "NO (TOKEN OVERLAP)", c: data.rag.real_embeddings ? "#ccff00" : "#ffce4f" },
                        { k: "TENANTS", v: String(data.rag.tenants || 0), c: "#ccff00" },
                        { k: "DOCS TOTAL", v: String(data.rag.docs_total || 0), c: "#ccff00" },
                    ]}
                    hint={data.rag.activate_hint}
                    testid="scaffold-rag"
                />
                <ScaffoldRow
                    name="CLIENT AUTH · MAGIC LINK"
                    color="#ccff00"
                    configured={data.client_auth.email_delivery_configured}
                    fields={[
                        { k: "MAGIC TTL", v: `${data.client_auth.magic_link_ttl_min} MIN`, c: "#00ffff" },
                        { k: "SESSION TTL", v: `${data.client_auth.session_ttl_hours} HR`, c: "#00ffff" },
                        { k: "EMAIL DELIVERY", v: data.client_auth.email_delivery_configured ? "RESEND WIRED" : "DEV LINK MODE", c: data.client_auth.email_delivery_configured ? "#ccff00" : "#ffce4f" },
                        { k: "ROUTE", v: "/client/login", c: "#7c5cff" },
                    ]}
                    extras="Magic link mints a JWT scoped with `aud=client` so it never collides with admin tokens. Hit /client/login as a customer; mints a one-time link valid for 15 minutes."
                    hint={data.client_auth.activate_hint}
                    testid="scaffold-client-auth"
                />
                <ScaffoldRow
                    name="RESEND · EMAIL DELIVERY"
                    color="#00ffff"
                    configured={data.resend.configured}
                    fields={[
                        { k: "API KEY", v: data.resend.configured ? "SET" : "MISSING", c: data.resend.configured ? "#ccff00" : "#ffce4f" },
                        { k: "SENDER", v: data.resend.sender, c: "#00ffff" },
                        { k: "QUEUED", v: String(data.resend.queued || 0), c: "#ffce4f" },
                        { k: "FAILED", v: String(data.resend.failed || 0), c: "#ff3b8a" },
                    ]}
                    extras="Auto-followup emails for lighthouse applicants + magic-link sign-ins queue here. Drop the key, they flush on next retry call."
                    hint={data.resend.activate_hint}
                    testid="scaffold-resend"
                />
            </div>

            {/* RAG live test bench */}
            <div className="deck-card relative" data-testid="rag-testbench">
                <CornerBrackets />
                <div className="px-6 py-4 border-b border-white/10">
                    <div className="mono-label text-[#7c5cff]">RAG · LIVE TEST BENCH</div>
                    <div className="font-mono-tech text-[10px] text-white/55 mt-1">
                        Ingest a doc into <code className="text-[#00ffff]">tenant_id</code>, then query. Tenants are isolated — queries against another tenant return zero hits.
                    </div>
                </div>
                <div className="grid lg:grid-cols-2 gap-4 p-6">
                    <div>
                        <div className="mono-label text-[10px] text-[#ccff00] mb-2">INGEST</div>
                        <input data-testid="rag-tenant" value={tenant} onChange={(e) => setTenant(e.target.value)} placeholder="tenant_id" className="input-tech w-full text-xs" />
                        <input data-testid="rag-title" value={ingestTitle} onChange={(e) => setIngestTitle(e.target.value)} placeholder="doc title" className="input-tech w-full text-xs mt-2" />
                        <textarea data-testid="rag-content" rows={4} value={ingestContent} onChange={(e) => setIngestContent(e.target.value)} placeholder="doc content (carrier directory · BOL fields · process docs · etc.)" className="input-tech w-full text-xs mt-2 font-mono-tech" />
                        <button data-testid="rag-ingest-btn" disabled={busy} onClick={ingest} className="btn-jade text-xs mt-2 w-full disabled:opacity-50">+ INGEST DOC</button>
                    </div>
                    <div>
                        <div className="mono-label text-[10px] text-[#00ffff] mb-2">QUERY</div>
                        <input data-testid="rag-query" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="ask a question…" className="input-tech w-full text-xs" />
                        <button data-testid="rag-query-btn" disabled={busy} onClick={runQuery} className="btn-jade text-xs mt-2 w-full disabled:opacity-50">QUERY · {tenant}</button>
                        {queryResult && (
                            <div className="mt-3 border border-white/10 p-3" data-testid="rag-result">
                                <div className="mono-label text-[10px] text-white/55">{queryResult.hits.length} HITS · {queryResult.provider}</div>
                                {queryResult.hits.length === 0 ? (
                                    <div className="font-mono-tech text-[11px] text-white/40 mt-2">// no docs match · tenant is isolated</div>
                                ) : queryResult.hits.map((h) => (
                                    <div key={h.id} className="mt-2 pb-2 border-b border-white/5 last:border-0">
                                        <div className="flex justify-between text-[10px]">
                                            <span className="font-display font-bold text-white">{h.title}</span>
                                            <span className="text-[#ccff00]">score · {h.score}</span>
                                        </div>
                                        <div className="font-mono-tech text-[10px] text-white/65 mt-1 leading-snug">{h.snippet}</div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <div className="font-mono-tech text-[10px] text-white/40 leading-relaxed">
                ▸ Edit <code className="text-[#00ffff]">backend/.env</code> + <code className="text-[#00ffff]">frontend/.env</code> to activate any scaffold. Restart backend after backend env changes.
            </div>
        </div>
    );
}
