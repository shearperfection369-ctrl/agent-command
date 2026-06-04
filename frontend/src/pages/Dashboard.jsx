import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import { isAuthed } from "../lib/auth";
import { CornerBrackets, SectionLabel } from "../components/Brackets";
import { ArrowsClockwise, Users, ChartBar, Robot, Clock, Webhooks, Database, Building, TrashSimple, Plus } from "@/lib/icons";

export default function Dashboard() {
  const nav = useNavigate();
  const [stats, setStats] = useState(null);
  const [leads, setLeads] = useState([]);
  const [runs, setRuns] = useState([]);
  const [orgs, setOrgs] = useState([]);
  const [usage, setUsage] = useState(null);
  const [hooks, setHooks] = useState([]);
  const [kb, setKb] = useState([]);
  const [lighthouse, setLighthouse] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("leads");

  useEffect(() => {
    if (!isAuthed()) { nav("/login"); return; }
    load();
  }, []);

  const load = async () => {
    setLoading(true);
    try {
      const [s, l, r, o, u, h, k, lh] = await Promise.all([
        api.get("/admin/stats"),
        api.get("/leads"),
        api.get("/admin/agent-runs"),
        api.get("/orgs"),
        api.get("/orgs/usage"),
        api.get("/webhooks"),
        api.get("/kb/docs"),
        api.get("/lighthouse/applications"),
      ]);
      setStats(s.data); setLeads(l.data); setRuns(r.data); setOrgs(o.data);
      setUsage(u.data); setHooks(h.data); setKb(k.data); setLighthouse(lh.data);
    } catch (e) {
      if (e?.response?.status === 401) nav("/login");
      else toast.error("Failed to load.");
    } finally { setLoading(false); }
  };

  const updateLead = async (id, status) => {
    try { await api.patch(`/leads/${id}`, null, { params: { status_value: status } }); toast.success(`→ ${status}`); load(); }
    catch { toast.error("Update failed."); }
  };

  if (loading) return <div className="min-h-screen bg-console grid place-items-center font-mono-tech text-[#ccff00]">// loading console…</div>;

  const TABS = [
    { id: "lighthouse", label: "LIGHTHOUSE", c: "#ff3b8a", n: lighthouse.length },
    { id: "leads", label: "LEADS", c: "#ccff00", n: leads.length },
    { id: "runs", label: "AGENT RUNS", c: "#00ffff", n: runs.length },
    { id: "orgs", label: "ORGS", c: "#7c5cff", n: orgs.length },
    { id: "hooks", label: "WEBHOOKS", c: "#ff3b8a", n: hooks.length },
    { id: "kb", label: "KNOWLEDGE BASE", c: "#ccff00", n: kb.length },
  ];

  return (
    <div className="bg-console min-h-screen">
      <section className="px-6 lg:px-10 py-12 border-b border-white/5 grid-bg-tight">
        <div className="max-w-[1400px] mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <SectionLabel idx={0} color="#ccff00">CONSOLE · ADMIN VAULT</SectionLabel>
              <h1 className="font-display font-black text-white text-5xl tracking-tighter">Mission <span className="accent-cyan">control.</span></h1>
            </div>
            <button data-testid="dashboard-refresh-btn" onClick={load} className="btn-ghost inline-flex items-center gap-2"><ArrowsClockwise size={14} weight="bold" /> REFRESH</button>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4 mt-8">
            <StatCard icon={Users} c="#ccff00" k="LEADS" v={stats?.leads_total ?? 0} />
            <StatCard icon={ChartBar} c="#00ffff" k="NEW" v={stats?.leads_new ?? 0} />
            <StatCard icon={Robot} c="#7c5cff" k="RUNS" v={stats?.runs_total ?? 0} />
            <StatCard icon={Building} c="#ff3b8a" k="ORGS · PAID" v={orgs.filter(o => o.subscription_status === "active").length} />
            <StatCard icon={Database} c="#ccff00" k="TOKENS ~" v={usage ? `${Math.round(usage.estimated_tokens / 1000)}k` : "—"} />
          </div>

          <div className="mt-8 flex flex-wrap gap-2">
            {TABS.map((t) => {
              const active = tab === t.id;
              return (
                <button key={t.id} data-testid={`admin-tab-${t.id}`} onClick={() => setTab(t.id)}
                  className="px-4 py-3 mono-label transition inline-flex items-center gap-2"
                  style={{
                    border: `1px solid ${active ? t.c : "rgba(255,255,255,0.10)"}`,
                    color: active ? t.c : "rgba(255,255,255,0.55)",
                    background: active ? `${t.c}11` : "transparent",
                  }}>
                  {t.label} <span className="font-mono-tech text-[10px] opacity-60">{t.n}</span>
                </button>
              );
            })}
          </div>
        </div>
      </section>

      <section className="px-6 lg:px-10 py-10">
        <div className="max-w-[1400px] mx-auto">
          {tab === "lighthouse" && <LighthousePanel apps={lighthouse} reload={load} />}
          {tab === "leads" && <LeadsTable leads={leads} updateLead={updateLead} />}
          {tab === "runs" && <RunsTable runs={runs} />}
          {tab === "orgs" && <OrgsTable orgs={orgs} />}
          {tab === "hooks" && <WebhooksPanel hooks={hooks} reload={load} />}
          {tab === "kb" && <KbPanel kb={kb} reload={load} />}
        </div>
      </section>
    </div>
  );
}

function StatCard({ icon: Icon, c, k, v }) {
  return (
    <div className="deck-card p-5 relative">
      <CornerBrackets />
      <div className="flex items-center justify-between mb-3">
        <Icon size={18} style={{ color: c }} weight="bold" />
        <span className="mono-label" style={{ color: c }}>{k}</span>
      </div>
      <div className="font-display font-black text-white text-3xl tracking-tighter">{v}</div>
    </div>
  );
}

function LeadsTable({ leads, updateLead }) {
  return (
    <div className="deck-card relative" data-testid="leads-table">
      <CornerBrackets />
      <div className="p-6 border-b border-white/10 flex items-center justify-between">
        <div className="mono-label text-[#ccff00]">LEADS · QUEUE</div>
        <span className="mono-label text-white/40">{leads.length} TOTAL</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-white/5">{["NAME","COMPANY","VERTICAL","USE CASE","STATUS","ACTIONS"].map((h) => <th key={h} className="p-4 text-left mono-label text-white/40">{h}</th>)}</tr></thead>
          <tbody>
            {leads.length === 0 && <tr><td colSpan={6} className="p-8 text-center font-mono-tech text-xs text-white/40">// no leads yet</td></tr>}
            {leads.map((l) => (
              <tr key={l.id} data-testid={`lead-row-${l.id}`} className="border-b border-white/5 hover:bg-white/[0.02]">
                <td className="p-4"><div className="text-white font-display font-bold">{l.name}</div><div className="font-mono-tech text-[11px] text-white/45">{l.email}</div></td>
                <td className="p-4 text-white/75 font-mono-tech text-xs">{l.company}</td>
                <td className="p-4 mono-label text-[#00ffff]">{l.vertical?.toUpperCase()}</td>
                <td className="p-4 text-white/65 text-xs max-w-[240px] truncate" title={l.use_case}>{l.use_case || "—"}</td>
                <td className="p-4"><span className="mono-label" style={{ color: l.status === "new" ? "#ccff00" : l.status === "contacted" ? "#00ffff" : l.status === "won" ? "#7c5cff" : "#ff3b8a" }}>{l.status?.toUpperCase()}</span></td>
                <td className="p-4">
                  <select data-testid={`lead-status-${l.id}`} value={l.status} onChange={(e) => updateLead(l.id, e.target.value)} className="input-tech text-xs py-1.5 w-[130px]">
                    {["new","contacted","qualified","won","lost"].map((s) => <option key={s}>{s}</option>)}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function RunsTable({ runs }) {
  return (
    <div className="deck-card relative" data-testid="runs-table">
      <CornerBrackets />
      <div className="p-6 border-b border-white/10 mono-label text-[#00ffff]">AGENT RUNS · TAPE</div>
      <div className="max-h-[640px] overflow-y-auto divide-y divide-white/5">
        {runs.length === 0 && <div className="p-6 font-mono-tech text-xs text-white/40">// no runs yet</div>}
        {runs.map((r) => (
          <div key={r.id} className="p-4 grid grid-cols-[140px_100px_1fr_160px] gap-4 items-center hover:bg-white/[0.02]">
            <span className="mono-label" style={{ color: { chat: "#ccff00", extract: "#00ffff", draft_outreach: "#7c5cff", qualify_lead: "#ff3b8a", support_triage: "#ccff00" }[r.agent_type] || "#fff" }}>{r.agent_type}</span>
            <span className="font-mono-tech text-[10px] text-white/40">{r.provider}</span>
            <span className="font-mono-tech text-xs text-white/65 truncate">{r.input_preview}</span>
            <span className="font-mono-tech text-[10px] text-white/35 text-right">{new Date(r.created_at).toLocaleString()}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function OrgsTable({ orgs }) {
  return (
    <div className="deck-card relative" data-testid="orgs-table">
      <CornerBrackets />
      <div className="p-6 border-b border-white/10 mono-label text-[#7c5cff]">ORGS · MULTI-TENANT REGISTRY</div>
      <table className="w-full text-sm">
        <thead><tr className="border-b border-white/5">{["COMPANY","EMAIL","TIER","STATUS","TOKEN BUDGET","CREATED"].map((h) => <th key={h} className="p-4 text-left mono-label text-white/40">{h}</th>)}</tr></thead>
        <tbody>
          {orgs.length === 0 && <tr><td colSpan={6} className="p-8 text-center font-mono-tech text-xs text-white/40">// no paid orgs yet · run a checkout in Stripe to populate</td></tr>}
          {orgs.map((o) => (
            <tr key={o.id} className="border-b border-white/5 hover:bg-white/[0.02]">
              <td className="p-4 text-white font-display font-bold">{o.company}</td>
              <td className="p-4 font-mono-tech text-xs text-white/65">{o.email}</td>
              <td className="p-4 mono-label text-[#ccff00]">{(o.tier || "TRIAL").toUpperCase()}</td>
              <td className="p-4 mono-label" style={{ color: o.subscription_status === "active" ? "#ccff00" : "#7c5cff" }}>{o.subscription_status?.toUpperCase()}</td>
              <td className="p-4 font-mono-tech text-xs text-white/65">{(o.monthly_token_budget / 1000).toLocaleString()}k</td>
              <td className="p-4 font-mono-tech text-[10px] text-white/40">{new Date(o.created_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function WebhooksPanel({ hooks, reload }) {
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [kind, setKind] = useState("slack");
  const [busy, setBusy] = useState(false);

  const add = async () => {
    if (!name || !url) return toast.error("Name + URL required.");
    setBusy(true);
    try { await api.post("/webhooks", { name, url, kind }); setName(""); setUrl(""); reload(); toast.success("Webhook registered."); }
    catch { toast.error("Failed."); } finally { setBusy(false); }
  };

  const test = async (id) => {
    try {
      const { data } = await api.post(`/webhooks/${id}/dispatch`, {
        title: "JADE OS test ping",
        body: "If you can read this, your webhook is live. — JADE",
      });
      data.delivered ? toast.success("Test delivered.") : toast.error(`Failed: ${data.error}`);
    } catch (e) { toast.error("Dispatch failed."); }
  };

  const del = async (id) => { await api.delete(`/webhooks/${id}`); reload(); };

  return (
    <div className="space-y-6">
      <div className="deck-card p-6 relative" data-testid="webhook-form">
        <CornerBrackets />
        <div className="mono-label text-[#ff3b8a] mb-4">REGISTER WEBHOOK</div>
        <div className="grid sm:grid-cols-4 gap-3">
          <input data-testid="webhook-name" className="input-tech" placeholder="NAME (e.g. ops-slack)" value={name} onChange={(e) => setName(e.target.value)} />
          <input data-testid="webhook-url" className="input-tech sm:col-span-2" placeholder="https://hooks.slack.com/services/…" value={url} onChange={(e) => setUrl(e.target.value)} />
          <select data-testid="webhook-kind" className="input-tech" value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="slack">SLACK</option>
            <option value="crm">CRM</option>
            <option value="generic">GENERIC</option>
          </select>
        </div>
        <button data-testid="webhook-add-btn" onClick={add} disabled={busy} className="btn-jade mt-4 inline-flex items-center gap-2"><Plus size={14} weight="bold" /> ADD</button>
      </div>

      <div className="deck-card relative" data-testid="webhooks-list">
        <CornerBrackets />
        <div className="p-6 border-b border-white/10 mono-label text-[#ff3b8a]">REGISTERED WEBHOOKS</div>
        <table className="w-full text-sm">
          <thead><tr className="border-b border-white/5">{["NAME","KIND","URL","ACTIONS"].map((h) => <th key={h} className="p-4 text-left mono-label text-white/40">{h}</th>)}</tr></thead>
          <tbody>
            {hooks.length === 0 && <tr><td colSpan={4} className="p-8 text-center font-mono-tech text-xs text-white/40">// no webhooks yet</td></tr>}
            {hooks.map((h) => (
              <tr key={h.id} className="border-b border-white/5 hover:bg-white/[0.02]">
                <td className="p-4 text-white font-display font-bold">{h.name}</td>
                <td className="p-4 mono-label text-[#7c5cff]">{h.kind.toUpperCase()}</td>
                <td className="p-4 font-mono-tech text-xs text-white/60 truncate max-w-[420px]">{h.url}</td>
                <td className="p-4 flex gap-2">
                  <button data-testid={`webhook-test-${h.id}`} onClick={() => test(h.id)} className="btn-ghost text-xs px-3">TEST</button>
                  <button data-testid={`webhook-del-${h.id}`} onClick={() => del(h.id)} className="btn-ghost text-xs px-3 text-[#ff3b8a]"><TrashSimple size={12} weight="bold" /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function KbPanel({ kb, reload }) {
  const [industry, setIndustry] = useState("general");
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [busy, setBusy] = useState(false);

  const add = async () => {
    if (!title || !content) return toast.error("Title + content required.");
    setBusy(true);
    try { await api.post("/kb/docs", { industry, title, content }); setTitle(""); setContent(""); reload(); toast.success("Doc added to KB."); }
    catch { toast.error("Failed."); } finally { setBusy(false); }
  };

  const del = async (id) => { await api.delete(`/kb/docs/${id}`); reload(); };

  return (
    <div className="space-y-6">
      <div className="deck-card p-6 relative" data-testid="kb-form">
        <CornerBrackets />
        <div className="mono-label text-[#ccff00] mb-4">ADD KB DOC · POWERS THE SUPPORT AGENT</div>
        <div className="grid sm:grid-cols-3 gap-3 mb-3">
          <select data-testid="kb-industry" className="input-tech" value={industry} onChange={(e) => setIndustry(e.target.value)}>
            {["general","freight_brokerage","logistics","healthcare","saas","ecommerce","manufacturing","insurance","legal","real_estate","professional_services"].map((i) => <option key={i}>{i}</option>)}
          </select>
          <input data-testid="kb-title" className="input-tech sm:col-span-2" placeholder="TITLE (e.g. 'Reset password procedure')" value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <textarea data-testid="kb-content" className="input-tech" rows={6} placeholder="Doc content — markdown or plain text…" value={content} onChange={(e) => setContent(e.target.value)} />
        <button data-testid="kb-add-btn" onClick={add} disabled={busy} className="btn-jade mt-4 inline-flex items-center gap-2"><Plus size={14} weight="bold" /> ADD DOC</button>
      </div>

      <div className="deck-card relative" data-testid="kb-list">
        <CornerBrackets />
        <div className="p-6 border-b border-white/10 mono-label text-[#ccff00]">KB DOCS</div>
        <div className="divide-y divide-white/5">
          {kb.length === 0 && <div className="p-6 font-mono-tech text-xs text-white/40">// empty knowledge base</div>}
          {kb.map((d) => (
            <div key={d.id} className="p-5 grid grid-cols-[120px_1fr_60px] gap-4 items-start">
              <span className="mono-label text-[#00ffff]">{d.industry.toUpperCase()}</span>
              <div>
                <div className="text-white font-display font-bold">{d.title}</div>
                <div className="font-mono-tech text-[11px] text-white/55 mt-2 line-clamp-2">{d.content}</div>
              </div>
              <button data-testid={`kb-del-${d.id}`} onClick={() => del(d.id)} className="btn-ghost text-xs px-3 text-[#ff3b8a]"><TrashSimple size={12} weight="bold" /></button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}


const LIGHTHOUSE_STATUSES = ["new", "screening", "interview_scheduled", "selected", "pilot_live", "case_published", "passed"];

function LighthousePanel({ apps, reload }) {
  const [expanded, setExpanded] = useState(null);

  const updateStatus = async (id, status_value) => {
    try { await api.patch(`/lighthouse/applications/${id}`, null, { params: { status_value } }); toast.success(`→ ${status_value}`); reload(); }
    catch { toast.error("Update failed."); }
  };

  const tierColor = (t) => t === "hot" ? "#ff3b8a" : t === "warm" ? "#ccff00" : t === "cold" ? "#7c5cff" : "#666";

  // Sort hottest first
  const sorted = [...apps].sort((a, b) => (b.score ?? -1) - (a.score ?? -1));

  return (
    <div className="space-y-4">
      <div className="deck-card p-5 relative" data-testid="lighthouse-stats">
        <CornerBrackets />
        <div className="grid sm:grid-cols-4 gap-4">
          <Stat k="TOTAL APPLICATIONS" v={apps.length} c="#ccff00" />
          <Stat k="HOT" v={apps.filter((a) => a.tier === "hot").length} c="#ff3b8a" />
          <Stat k="WARM" v={apps.filter((a) => a.tier === "warm").length} c="#ccff00" />
          <Stat k="SELECTED · LIVE" v={apps.filter((a) => ["selected","pilot_live","case_published"].includes(a.status)).length} c="#7c5cff" />
        </div>
      </div>

      <div className="deck-card relative" data-testid="lighthouse-table">
        <CornerBrackets />
        <div className="p-6 border-b border-white/10 flex items-center justify-between">
          <div className="mono-label text-[#ff3b8a]">LIGHTHOUSE APPLICATIONS · SORTED BY JADE SCORE</div>
          <span className="mono-label text-white/40">{apps.length} TOTAL</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-white/5">{["SCORE","TIER","COMPANY · OPERATOR","INDUSTRY","PAIN","STATUS","ACTIONS"].map((h) => <th key={h} className="p-4 text-left mono-label text-white/40">{h}</th>)}</tr></thead>
            <tbody>
              {sorted.length === 0 && <tr><td colSpan={7} className="p-8 text-center font-mono-tech text-xs text-white/40">// no applications yet — share /lighthouse</td></tr>}
              {sorted.map((a) => (
                <>
                <tr key={a.id} data-testid={`lh-row-${a.id}`} className="border-b border-white/5 hover:bg-white/[0.02] cursor-pointer" onClick={() => setExpanded(expanded === a.id ? null : a.id)}>
                  <td className="p-4 font-display font-black text-3xl" style={{ color: tierColor(a.tier) }}>{a.score ?? "—"}</td>
                  <td className="p-4 mono-label uppercase" style={{ color: tierColor(a.tier) }}>{a.tier || "—"}</td>
                  <td className="p-4">
                    <div className="text-white font-display font-bold">{a.company}</div>
                    <div className="font-mono-tech text-[11px] text-white/55 mt-1">{a.name} · {a.title}</div>
                    <div className="font-mono-tech text-[11px] text-white/45">{a.email}</div>
                  </td>
                  <td className="p-4 mono-label text-[#00ffff]">{a.industry.toUpperCase()}</td>
                  <td className="p-4 text-white/65 text-xs max-w-[200px] truncate" title={a.primary_pain}>{a.primary_pain?.replace(/_/g," ")}</td>
                  <td className="p-4"><span className="mono-label" style={{ color: a.status === "selected" || a.status === "pilot_live" ? "#ccff00" : a.status === "passed" ? "#7c5cff" : "#fff" }}>{a.status?.toUpperCase()}</span></td>
                  <td className="p-4">
                    <select data-testid={`lh-status-${a.id}`} value={a.status} onClick={(e) => e.stopPropagation()} onChange={(e) => updateStatus(a.id, e.target.value)} className="input-tech text-xs py-1.5 w-[160px]">
                      {LIGHTHOUSE_STATUSES.map((s) => <option key={s} value={s}>{s.replace(/_/g," ").toUpperCase()}</option>)}
                    </select>
                  </td>
                </tr>
                {expanded === a.id && (
                  <tr className="border-b border-white/5 bg-[#06081a]">
                    <td colSpan={7} className="p-6">
                      <div className="grid lg:grid-cols-3 gap-6">
                        <div>
                          <div className="mono-label text-[#00ffff] mb-2">RATIONALE · JADE'S READ</div>
                          <p className="text-sm text-white/80 leading-relaxed">{a.rationale || "—"}</p>
                          <div className="mono-label text-[#ccff00] mt-5 mb-2">NEXT ACTION</div>
                          <p className="text-sm text-white/80 leading-relaxed">{a.next_action || "—"}</p>
                        </div>
                        <div>
                          <div className="mono-label text-[#ccff00] mb-2">GREEN FLAGS</div>
                          <ul className="space-y-1.5">{(a.green_flags || []).map((f, i) => <li key={i} className="font-mono-tech text-xs text-white/70 flex gap-2"><span className="text-[#ccff00]">▸</span>{f}</li>)}</ul>
                          <div className="mono-label text-[#ff3b8a] mt-5 mb-2">RED FLAGS</div>
                          <ul className="space-y-1.5">{(a.red_flags || []).map((f, i) => <li key={i} className="font-mono-tech text-xs text-white/70 flex gap-2"><span className="text-[#ff3b8a]">▸</span>{f}</li>)}</ul>
                        </div>
                        <div>
                          <div className="mono-label text-white/45 mb-2">PAIN DETAIL</div>
                          <p className="text-xs text-white/75 leading-relaxed">{a.pain_detail}</p>
                          <div className="mono-label text-white/45 mt-4 mb-2">TARGET OUTCOME</div>
                          <p className="text-xs text-white/75 leading-relaxed accent-cyan">{a.target_outcome}</p>
                          <div className="mt-5 grid grid-cols-3 gap-2 text-[10px] font-mono-tech text-white/60">
                            <div><span className="text-white/40">SIZE:</span> {a.company_size}</div>
                            <div><span className="text-white/40">TIMELINE:</span> {a.timeline}</div>
                            <div><span className="text-white/40">BUDGET:</span> {a.budget_band}</div>
                            <div><span className="text-white/40">AUTH:</span> {a.decision_authority}</div>
                            <div><span className="text-white/40">CASE OK:</span> {a.case_study_consent ? "✓" : "✗"}</div>
                            <div><span className="text-white/40">LOGO OK:</span> {a.logo_consent ? "✓" : "✗"}</div>
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
