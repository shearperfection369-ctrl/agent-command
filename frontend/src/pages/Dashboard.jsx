import { useEffect, useState, Fragment } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import { isAuthed } from "../lib/auth";
import { CornerBrackets, SectionLabel } from "../components/Brackets";
import { ArrowsClockwise, Users, ChartBar, Robot, Clock, Webhooks, Database, Building, TrashSimple, Plus, Lightning, EnvelopeSimple } from "@/lib/icons";
import { INDUSTRIES, SAMPLES } from "../lib/industries";

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
    { id: "playground", label: "PLAYGROUND", c: "#7c5cff", n: "" },
    { id: "runs", label: "AGENT RUNS", c: "#00ffff", n: runs.length },
    { id: "orgs", label: "ORGS", c: "#7c5cff", n: orgs.length },
    { id: "hooks", label: "WEBHOOKS", c: "#ff3b8a", n: hooks.length },
    { id: "kb", label: "KNOWLEDGE BASE", c: "#ccff00", n: kb.length },
    { id: "promo", label: "PROMO REEL", c: "#ff3b8a", n: "" },
    { id: "selftest", label: "SELF-TEST", c: "#00ffff", n: "" },
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
          {tab === "leads" && (
            <div className="space-y-6">
              <ProspectsPanel />
              <LeadsTable leads={leads} updateLead={updateLead} />
            </div>
          )}
          {tab === "runs" && <RunsTable runs={runs} />}
          {tab === "playground" && <PlaygroundPanel />}
          {tab === "orgs" && <OrgsTable orgs={orgs} />}
          {tab === "hooks" && <WebhooksPanel hooks={hooks} reload={load} />}
          {tab === "kb" && <KbPanel kb={kb} reload={load} />}
          {tab === "promo" && <PromoReelPanel />}
          {tab === "selftest" && <SelfTestPanel />}
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


// ============================================================
// SELF-TEST PANEL — runs the /api/admin/self-test battery and
// renders per-check status, latency, and details for every major feature.
// ============================================================
function SelfTestPanel() {
  const [running, setRunning] = useState(false);
  const [deep, setDeep] = useState(false);
  const [report, setReport] = useState(null);
  const [openRow, setOpenRow] = useState(null);

  const run = async () => {
    setRunning(true);
    setReport(null);
    setOpenRow(null);
    const startedAt = Date.now();
    try {
      const { data } = await api.get(`/admin/self-test`, { params: { deep }, timeout: 120000 });
      setReport(data);
      const { pass, fail, skip } = data.summary;
      if (fail === 0) toast.success(`Self-test: ${pass} pass · ${skip} skip · 0 fail`);
      else toast.error(`Self-test: ${fail} FAIL · ${pass} pass · ${skip} skip`);
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Self-test failed to run";
      toast.error(msg);
      setReport({
        results: [],
        summary: { pass: 0, fail: 1, skip: 0, total: 1, total_ms: Date.now() - startedAt, deep, ran_at: new Date().toISOString() },
        error: msg,
      });
    } finally {
      setRunning(false);
    }
  };

  const statusColor = (s) => ({ pass: "#ccff00", fail: "#ff3b8a", skip: "#7c5cff", warn: "#00ffff" }[s] || "#fff");
  const statusGlyph = (s) => ({ pass: "✓", fail: "✗", skip: "⊘", warn: "!" }[s] || "?");

  const groups = report?.results
    ? report.results.reduce((acc, r) => {
        (acc[r.category] = acc[r.category] || []).push(r);
        return acc;
      }, {})
    : {};

  return (
    <div className="space-y-6" data-testid="selftest-panel">
      {/* Controls */}
      <div className="deck-card p-6 relative" data-testid="selftest-controls">
        <CornerBrackets />
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <div className="mono-label text-[#00ffff] mb-2">SYSTEM SELF-TEST · END-TO-END HEALTH CHECK</div>
            <p className="text-sm text-white/65 max-w-2xl leading-relaxed">
              Runs a battery of checks across every major feature — auth, leads, lighthouse, the MOAT
              (schemas/prompts/playbooks), knowledge base, webhooks, billing, Twilio, LLM connectivity,
              PDF extraction, and Mongo health. Each check reports status, latency, and details.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <label className="inline-flex items-center gap-2 cursor-pointer select-none" data-testid="selftest-deep-toggle">
              <input
                type="checkbox"
                checked={deep}
                onChange={(e) => setDeep(e.target.checked)}
                className="accent-[#ccff00] w-4 h-4"
                data-testid="selftest-deep-checkbox"
              />
              <span className="mono-label text-white/70">
                DEEP <span className="text-white/40">(invokes LLM · costs tokens)</span>
              </span>
            </label>
            <button
              data-testid="selftest-run-btn"
              onClick={run}
              disabled={running}
              className="btn-jade inline-flex items-center gap-2 px-5"
            >
              <Lightning size={14} weight="bold" />
              {running ? "RUNNING…" : "RUN TESTS"}
            </button>
          </div>
        </div>

        {/* Summary strip */}
        {report?.summary && (
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mt-6" data-testid="selftest-summary">
            <SummaryStat k="TOTAL" v={report.summary.total} c="#fff" />
            <SummaryStat k="PASS" v={report.summary.pass} c="#ccff00" />
            <SummaryStat k="FAIL" v={report.summary.fail} c="#ff3b8a" />
            <SummaryStat k="SKIP" v={report.summary.skip} c="#7c5cff" />
            <SummaryStat k="ELAPSED" v={`${(report.summary.total_ms / 1000).toFixed(2)}s`} c="#00ffff" />
          </div>
        )}
      </div>

      {/* Empty state */}
      {!report && !running && (
        <div className="deck-card p-12 relative text-center" data-testid="selftest-empty">
          <CornerBrackets />
          <Lightning size={36} weight="bold" className="mx-auto text-[#00ffff] mb-4" />
          <div className="font-display font-black text-white text-2xl tracking-tight">No report yet.</div>
          <div className="font-mono-tech text-xs text-white/50 mt-2">
            // hit RUN TESTS — full sweep typically completes in &lt; 100ms (skip-LLM) or ~4s (deep)
          </div>
        </div>
      )}

      {/* Running state */}
      {running && (
        <div className="deck-card p-12 relative text-center" data-testid="selftest-running">
          <CornerBrackets />
          <div className="font-mono-tech text-sm text-[#ccff00] animate-pulse">
            // JADE OS · running diagnostics{deep ? " · LLM round-trips engaged" : ""}…
          </div>
        </div>
      )}

      {/* Results grouped by category */}
      {report?.results && report.results.length > 0 && (
        <div className="space-y-4">
          {Object.entries(groups).map(([cat, rows]) => {
            const fails = rows.filter((r) => r.status === "fail").length;
            const passes = rows.filter((r) => r.status === "pass").length;
            const skips = rows.filter((r) => r.status === "skip").length;
            return (
              <div key={cat} className="deck-card relative" data-testid={`selftest-group-${cat}`}>
                <CornerBrackets />
                <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between flex-wrap gap-2">
                  <div className="mono-label text-[#00ffff]">{cat}</div>
                  <div className="font-mono-tech text-[11px] text-white/55 flex gap-3">
                    <span className="text-[#ccff00]">PASS {passes}</span>
                    {fails > 0 && <span className="text-[#ff3b8a]">FAIL {fails}</span>}
                    {skips > 0 && <span className="text-[#7c5cff]">SKIP {skips}</span>}
                  </div>
                </div>
                <table className="w-full text-sm">
                  <tbody>
                    {rows.map((r, idx) => {
                      const key = `${cat}-${idx}`;
                      const open = openRow === key;
                      const hasDetails = r.details || r.message !== "OK";
                      return (
                        <Fragment key={key}>
                          <tr
                            data-testid={`selftest-row-${cat}-${idx}`}
                            className={`border-b border-white/5 hover:bg-white/[0.02] ${hasDetails ? "cursor-pointer" : ""}`}
                            onClick={() => hasDetails && setOpenRow(open ? null : key)}
                          >
                            <td className="p-4 w-[60px] text-center">
                              <span
                                className="font-mono-tech font-bold text-lg"
                                style={{ color: statusColor(r.status) }}
                                data-testid={`selftest-status-${cat}-${idx}`}
                              >
                                {statusGlyph(r.status)}
                              </span>
                            </td>
                            <td className="p-4">
                              <div className="text-white font-display font-bold">{r.name}</div>
                              {r.status !== "pass" && (
                                <div
                                  className="font-mono-tech text-[11px] mt-1"
                                  style={{ color: statusColor(r.status) }}
                                >
                                  {r.message}
                                </div>
                              )}
                            </td>
                            <td className="p-4 w-[120px] font-mono-tech text-xs text-white/55 text-right">
                              {r.latency_ms.toFixed(1)}ms
                            </td>
                            <td className="p-4 w-[100px] text-right">
                              <span className="mono-label" style={{ color: statusColor(r.status) }}>
                                {r.status.toUpperCase()}
                              </span>
                            </td>
                          </tr>
                          {open && hasDetails && (
                            <tr className="border-b border-white/5 bg-[#06081a]">
                              <td colSpan={4} className="p-5">
                                <div className="mono-label text-white/40 mb-2">RAW</div>
                                <pre className="font-mono-tech text-[11px] text-white/75 whitespace-pre-wrap break-all leading-relaxed">
{JSON.stringify({ message: r.message, details: r.details }, null, 2)}
                                </pre>
                              </td>
                            </tr>
                          )}
                        </Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function SummaryStat({ k, v, c }) {
  return (
    <div
      className="border border-white/10 px-4 py-3"
      style={{ borderColor: `${c}33`, background: `${c}08` }}
    >
      <div className="mono-label text-[10px]" style={{ color: c }}>{k}</div>
      <div className="font-display font-black text-2xl tracking-tighter mt-1" style={{ color: c }}>{v}</div>
    </div>
  );
}

// Used by LighthousePanel (was missing — caused ReferenceError)
function Stat({ k, v, c }) {
  return (
    <div className="border border-white/10 px-4 py-3" style={{ borderColor: `${c}33`, background: `${c}08` }}>
      <div className="mono-label text-[10px]" style={{ color: c }}>{k}</div>
      <div className="font-display font-black text-3xl tracking-tighter mt-1" style={{ color: c }}>{v}</div>
    </div>
  );
}



// ============================================================
// PROMO REEL PANEL — preview/share/download the Sora 2-generated
// promotional video for socials.
// ============================================================
function PromoReelPanel() {
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(true);
  const apiBase = process.env.REACT_APP_BACKEND_URL || "";
  const videoUrl = `${apiBase}/api/promo/video`;

  useEffect(() => {
    let alive = true;
    api.get("/promo/meta")
      .then((r) => { if (alive) setMeta(r.data); })
      .catch(() => { if (alive) setMeta({ available: false }); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, []);

  const copy = (text, label) => {
    navigator.clipboard.writeText(text).then(
      () => toast.success(`${label} copied to clipboard`),
      () => toast.error("Clipboard blocked")
    );
  };

  const captionDraft = `Stop drowning in ops work.

JADE OS is the AI-agent platform for Minneapolis operators — 6 industry-trained agents that triage support, qualify leads, extract docs, and run multi-step playbooks while you sleep.

· Freight · Healthcare · SaaS · Manufacturing · Legal · E-commerce · Real-Estate · Insurance ·

Built by an operator, for operators.

→ onejades.com

#AI #Automation #Minneapolis #SaaS #Operations #Logistics #Healthcare`;

  if (loading) {
    return (
      <div className="deck-card p-12 text-center font-mono-tech text-xs text-[#ccff00]" data-testid="promo-loading">
        // loading promo reel…
      </div>
    );
  }

  if (!meta?.available) {
    return (
      <div className="deck-card p-10 relative" data-testid="promo-empty">
        <CornerBrackets />
        <div className="mono-label text-[#ff3b8a] mb-3">PROMO REEL · NOT GENERATED</div>
        <p className="text-white/65 text-sm leading-relaxed max-w-2xl">
          The promotional video hasn't been generated yet. Run{" "}
          <code className="font-mono-tech text-[#ccff00]">python backend/scripts/generate_promo_video.py</code>{" "}
          from the repo root to produce <code className="font-mono-tech text-[#00ffff]">jadeos_promo.mp4</code> (Sora 2 · 12s · 1280×720). Takes ~3 minutes.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="promo-panel">
      <div className="grid lg:grid-cols-[1.4fr_1fr] gap-6">
        {/* Video preview */}
        <div className="deck-card relative overflow-hidden" data-testid="promo-player">
          <CornerBrackets />
          <div className="p-5 border-b border-white/10 flex items-center justify-between">
            <div className="mono-label text-[#ff3b8a]">PROMOTIONAL REEL · JADE OS · {meta.duration_s}s · {meta.size}</div>
            <span className="font-mono-tech text-[10px] text-white/45">{meta.file_mb} MB</span>
          </div>
          <video
            data-testid="promo-video-el"
            controls
            playsInline
            preload="metadata"
            className="w-full block bg-black"
            src={videoUrl}
          >
            Sorry, your browser doesn't support embedded video.
          </video>
        </div>

        {/* Share / actions */}
        <div className="space-y-4">
          <div className="deck-card p-6 relative" data-testid="promo-share">
            <CornerBrackets />
            <div className="mono-label text-[#00ffff] mb-4">SHARE · ONE-CLICK ACTIONS</div>
            <div className="space-y-3">
              <a
                data-testid="promo-download-btn"
                href={videoUrl}
                download="jadeos_promo.mp4"
                className="btn-jade w-full inline-flex items-center justify-center gap-2"
              >
                <Database size={14} weight="bold" /> DOWNLOAD MP4
              </a>
              <button
                data-testid="promo-copy-url-btn"
                onClick={() => copy(videoUrl, "Public video URL")}
                className="btn-ghost w-full inline-flex items-center justify-center gap-2"
              >
                <Webhooks size={14} weight="bold" /> COPY PUBLIC URL
              </button>
              <button
                data-testid="promo-copy-caption-btn"
                onClick={() => copy(captionDraft, "Caption")}
                className="btn-ghost w-full inline-flex items-center justify-center gap-2"
              >
                <ChartBar size={14} weight="bold" /> COPY SOCIAL CAPTION
              </button>
            </div>
            <div className="mt-5 pt-5 border-t border-white/10">
              <div className="mono-label text-[10px] text-white/40 mb-2">PUBLIC URL</div>
              <div
                className="font-mono-tech text-[10px] text-white/65 break-all leading-relaxed bg-black/40 p-3 border border-white/5"
                data-testid="promo-url"
              >
                {videoUrl}
              </div>
            </div>
          </div>

          <div className="deck-card p-6 relative">
            <CornerBrackets />
            <div className="mono-label text-[#7c5cff] mb-3">PLATFORM SUGGESTIONS</div>
            <ul className="space-y-2 text-xs text-white/70 font-mono-tech leading-relaxed">
              <li><span className="text-[#ccff00]">▸</span> X / Twitter — works native, autoplay on feed</li>
              <li><span className="text-[#ccff00]">▸</span> LinkedIn — upload directly, this 16:9 displays full</li>
              <li><span className="text-[#ccff00]">▸</span> YouTube Shorts — re-crop to 9:16 in CapCut first</li>
              <li><span className="text-[#ccff00]">▸</span> Instagram / TikTok — same 9:16 crop, add caption overlay</li>
              <li><span className="text-[#ccff00]">▸</span> Email signature — link the public URL</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Prompt reference */}
      <div className="deck-card p-6 relative" data-testid="promo-prompt">
        <CornerBrackets />
        <div className="flex items-center justify-between mb-4">
          <div className="mono-label text-white/50">SORA 2 PROMPT · {meta.model}</div>
          <div className="flex items-center gap-3 font-mono-tech text-[10px] text-white/45">
            <span>RENDERED IN {meta.elapsed_s}s</span>
            <span className="text-white/25">·</span>
            <span>{new Date(meta.finished).toLocaleString()}</span>
          </div>
        </div>
        <p className="font-mono-tech text-[11px] text-white/65 leading-relaxed whitespace-pre-wrap">
          {meta.prompt}
        </p>
      </div>
    </div>
  );
}



// ============================================================
// PROSPECTS PANEL — sits above the LeadsTable. AI-generates
// Minneapolis-area B2B prospects per industry, drafts tailored
// solicitation email packages, hands off to default mail client.
// ============================================================
function ProspectsPanel() {
  const [industry, setIndustry] = useState("freight_brokerage");
  const [count, setCount] = useState(8);
  const [generating, setGenerating] = useState(false);
  const [prospects, setProspects] = useState([]);
  const [filterIndustry, setFilterIndustry] = useState("");
  const [draftFor, setDraftFor] = useState(null); // {prospect, pkg, loading}

  const load = async (ind) => {
    try {
      const params = ind ? { industry: ind } : {};
      const { data } = await api.get("/prospects", { params });
      setProspects(data);
    } catch {
      toast.error("Failed to load prospects.");
    }
  };

  useEffect(() => { load(filterIndustry); }, [filterIndustry]);

  const generate = async () => {
    setGenerating(true);
    try {
      const { data } = await api.post("/prospects/generate", { industry, count }, { timeout: 90000 });
      toast.success(`Generated ${data.count} ${industry.replace(/_/g, " ")} prospects`);
      setFilterIndustry(industry);
      await load(industry);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Generation failed.");
    } finally {
      setGenerating(false);
    }
  };

  const del = async (id) => {
    if (!confirm("Delete this prospect?")) return;
    try { await api.delete(`/prospects/${id}`); load(filterIndustry); }
    catch { toast.error("Delete failed."); }
  };

  const markContacted = async (id) => {
    try { await api.patch(`/prospects/${id}/contacted`); load(filterIndustry); toast.success("Marked contacted."); }
    catch { toast.error("Failed."); }
  };

  const draftEmail = async (p) => {
    setDraftFor({ prospect: p, pkg: null, loading: true });
    try {
      const { data } = await api.post(`/prospects/${p.id}/email-draft`, {}, { timeout: 60000 });
      setDraftFor({ prospect: p, pkg: data, loading: false });
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Email draft failed.");
      setDraftFor(null);
    }
  };

  const scoreColor = (s) =>
    s >= 85 ? "#ccff00" : s >= 70 ? "#00ffff" : s >= 55 ? "#7c5cff" : "#ff3b8a";

  return (
    <div className="space-y-4" data-testid="prospects-panel">
      {/* Generate strip */}
      <div className="deck-card p-6 relative" data-testid="prospects-generate">
        <CornerBrackets />
        <div className="flex flex-col lg:flex-row lg:items-center gap-4 lg:justify-between">
          <div>
            <div className="mono-label text-[#ccff00] mb-1 flex items-center gap-2">
              <Lightning size={12} weight="bold" /> PROSPECTS · MSP-AREA LEAD MINING
            </div>
            <p className="text-xs text-white/55 max-w-xl leading-relaxed">
              JADE synthesizes realistic Minneapolis-St. Paul B2B prospects per industry —
              role, company, plausible email, pain-point + a tailored hook + a fit score. Then drafts
              the cold-outreach package on demand.
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <select
              data-testid="prospects-industry-select"
              className="input-tech text-xs py-2"
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
            >
              {INDUSTRIES.map((i) => <option key={i.id} value={i.id}>{i.label}</option>)}
            </select>
            <input
              data-testid="prospects-count-input"
              type="number"
              min={1}
              max={12}
              value={count}
              onChange={(e) => setCount(Math.max(1, Math.min(12, parseInt(e.target.value || "1", 10))))}
              className="input-tech text-xs py-2 w-[80px]"
            />
            <button
              data-testid="prospects-generate-btn"
              onClick={generate}
              disabled={generating}
              className="btn-jade inline-flex items-center gap-2 px-5"
            >
              <Lightning size={14} weight="bold" />
              {generating ? "MINING…" : "GENERATE"}
            </button>
          </div>
        </div>
      </div>

      {/* Filter + list */}
      <div className="deck-card relative" data-testid="prospects-table">
        <CornerBrackets />
        <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between flex-wrap gap-3">
          <div className="mono-label text-[#00ffff]">PROSPECT POOL · {prospects.length}</div>
          <div className="flex items-center gap-2">
            <span className="mono-label text-white/40 text-[10px]">FILTER</span>
            <select
              data-testid="prospects-filter-select"
              className="input-tech text-xs py-1.5"
              value={filterIndustry}
              onChange={(e) => setFilterIndustry(e.target.value)}
            >
              <option value="">ALL INDUSTRIES</option>
              {INDUSTRIES.map((i) => <option key={i.id} value={i.id}>{i.label}</option>)}
            </select>
          </div>
        </div>

        {prospects.length === 0 ? (
          <div className="p-10 text-center font-mono-tech text-xs text-white/40" data-testid="prospects-empty">
            // pool empty — pick an industry above and hit GENERATE
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/5">
                  {["SCORE", "COMPANY · OPERATOR", "INDUSTRY", "PAIN + HOOK", "ACTIONS"].map((h) => (
                    <th key={h} className="p-4 text-left mono-label text-white/40">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {prospects.map((p) => (
                  <tr
                    key={p.id}
                    data-testid={`prospect-row-${p.id}`}
                    className={`border-b border-white/5 hover:bg-white/[0.02] ${p.contacted ? "opacity-55" : ""}`}
                  >
                    <td className="p-4 w-[80px]">
                      <div
                        className="font-display font-black text-3xl tracking-tighter"
                        style={{ color: scoreColor(p.jade_fit_score) }}
                      >
                        {p.jade_fit_score}
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="text-white font-display font-bold">{p.company}</div>
                      <div className="font-mono-tech text-[11px] text-white/65 mt-1">{p.name} · {p.title}</div>
                      <div className="font-mono-tech text-[10px] text-white/45 mt-0.5">
                        {p.email} · {p.city} · {p.company_size}
                      </div>
                    </td>
                    <td className="p-4 w-[160px] mono-label text-[#00ffff] text-[10px]">
                      {p.industry.replace(/_/g, " ").toUpperCase()}
                    </td>
                    <td className="p-4 max-w-[440px]">
                      <div className="text-xs text-white/80 leading-relaxed">{p.pain_point}</div>
                      <div className="font-mono-tech text-[10px] text-[#ccff00] mt-2 italic leading-relaxed">
                        “{p.hook}”
                      </div>
                    </td>
                    <td className="p-4 w-[180px]">
                      <div className="flex flex-col gap-1.5">
                        <button
                          data-testid={`prospect-email-${p.id}`}
                          onClick={() => draftEmail(p)}
                          className="btn-jade text-xs py-1.5 inline-flex items-center justify-center gap-1.5"
                        >
                          <EnvelopeSimple size={11} weight="bold" /> DRAFT EMAIL
                        </button>
                        <div className="flex gap-1.5">
                          {!p.contacted && (
                            <button
                              data-testid={`prospect-contacted-${p.id}`}
                              onClick={() => markContacted(p.id)}
                              className="btn-ghost text-[10px] px-2 py-1 flex-1"
                              title="Mark as contacted"
                            >
                              ✓ SENT
                            </button>
                          )}
                          {p.contacted && (
                            <span className="mono-label text-[10px] text-[#ccff00] flex-1 inline-flex items-center justify-center border border-[#ccff0033] py-1">
                              CONTACTED
                            </span>
                          )}
                          <button
                            data-testid={`prospect-del-${p.id}`}
                            onClick={() => del(p.id)}
                            className="btn-ghost text-xs px-2 py-1 text-[#ff3b8a]"
                            title="Delete prospect"
                          >
                            <TrashSimple size={11} weight="bold" />
                          </button>
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {draftFor && <EmailDraftModal data={draftFor} onClose={() => setDraftFor(null)} onSent={() => { markContacted(draftFor.prospect.id); setDraftFor(null); }} />}
    </div>
  );
}

function EmailDraftModal({ data, onClose, onSent }) {
  const { prospect, pkg, loading } = data;
  const [resendStatus, setResendStatus] = useState(null);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    api.get("/resend/status").then((r) => setResendStatus(r.data)).catch(() => setResendStatus({ configured: false }));
  }, []);

  const copy = (text, label) => {
    navigator.clipboard.writeText(text).then(
      () => toast.success(`${label} copied`),
      () => toast.error("Clipboard blocked")
    );
  };
  const mailto = pkg
    ? `mailto:${encodeURIComponent(prospect.email)}?subject=${encodeURIComponent(pkg.subject || "")}&body=${encodeURIComponent(pkg.body || "")}`
    : "#";

  const sendViaResend = async () => {
    if (!pkg) return;
    if (!resendStatus?.configured) {
      toast.error("Resend not configured — add RESEND_API_KEY in /app/backend/.env");
      return;
    }
    setSending(true);
    try {
      await api.post(`/prospects/${prospect.id}/send-via-resend`, {
        prospect_id: prospect.id,
        subject: pkg.subject,
        body: pkg.body,
      }, { timeout: 30000 });
      toast.success(`Sent → ${prospect.email}`);
      setTimeout(onSent, 300);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Send failed.");
    } finally {
      setSending(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm grid place-items-center px-4 py-10 overflow-y-auto"
      onClick={onClose}
      data-testid="email-draft-modal"
    >
      <div
        className="deck-card relative max-w-3xl w-full"
        onClick={(e) => e.stopPropagation()}
      >
        <CornerBrackets />
        <div className="p-6 border-b border-white/10 flex items-center justify-between gap-4">
          <div>
            <div className="mono-label text-[#ccff00] mb-1">SOLICITATION PACKAGE</div>
            <div className="text-white font-display font-bold text-lg">
              {prospect.name} · {prospect.company}
            </div>
            <div className="font-mono-tech text-[11px] text-white/55 mt-1">
              → {prospect.email}
            </div>
          </div>
          <button onClick={onClose} className="btn-ghost text-xs px-3" data-testid="email-draft-close">✕ CLOSE</button>
        </div>

        {loading && (
          <div className="p-12 text-center font-mono-tech text-xs text-[#ccff00] animate-pulse" data-testid="email-draft-loading">
            // JADE drafting tailored outreach package…
          </div>
        )}

        {pkg && (
          <div className="p-6 space-y-5">
            <div>
              <div className="mono-label text-white/40 text-[10px] mb-2">SUBJECT</div>
              <div
                className="font-display font-bold text-white text-lg border border-white/10 px-4 py-3 bg-black/40"
                data-testid="email-draft-subject"
              >
                {pkg.subject}
              </div>
            </div>

            <div>
              <div className="mono-label text-white/40 text-[10px] mb-2">BODY</div>
              <div
                className="font-mono-tech text-xs text-white/85 leading-relaxed border border-white/10 p-4 bg-black/40 whitespace-pre-wrap"
                data-testid="email-draft-body"
              >
                {pkg.body}
              </div>
            </div>

            {pkg.talking_points?.length > 0 && (
              <div>
                <div className="mono-label text-[#00ffff] text-[10px] mb-2">TALKING POINTS</div>
                <ul className="space-y-1.5">
                  {pkg.talking_points.map((tp, i) => (
                    <li key={i} className="font-mono-tech text-xs text-white/75 flex gap-2 leading-relaxed">
                      <span className="text-[#ccff00]">▸</span>{tp}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {pkg.ps && (
              <div>
                <div className="mono-label text-[#7c5cff] text-[10px] mb-2">PS · ADD AS NEEDED</div>
                <div className="font-mono-tech text-xs text-white/70 leading-relaxed italic">{pkg.ps}</div>
              </div>
            )}

            <div className="pt-4 border-t border-white/10 flex flex-wrap gap-2 items-center">
              <button
                data-testid="email-draft-send-resend"
                onClick={sendViaResend}
                disabled={sending || !resendStatus?.configured}
                className="btn-jade inline-flex items-center gap-2"
                title={resendStatus?.configured ? `Send from ${resendStatus.sender}` : "Resend not configured"}
              >
                <Lightning size={14} weight="bold" />
                {sending ? "SENDING…" : "SEND VIA JADE"}
              </button>
              <a
                data-testid="email-draft-mailto"
                href={mailto}
                onClick={() => setTimeout(onSent, 500)}
                className="btn-ghost inline-flex items-center gap-2"
              >
                <EnvelopeSimple size={14} weight="bold" /> OPEN IN MAIL CLIENT
              </a>
              <button
                data-testid="email-draft-copy-subject"
                onClick={() => copy(pkg.subject, "Subject")}
                className="btn-ghost text-xs"
              >
                COPY SUBJECT
              </button>
              <button
                data-testid="email-draft-copy-body"
                onClick={() => copy(pkg.body, "Body")}
                className="btn-ghost text-xs"
              >
                COPY BODY
              </button>
              <button
                data-testid="email-draft-copy-all"
                onClick={() => copy(`Subject: ${pkg.subject}\n\n${pkg.body}`, "Full email")}
                className="btn-ghost text-xs"
              >
                COPY ALL
              </button>
              {resendStatus && !resendStatus.configured && (
                <span
                  className="font-mono-tech text-[10px] text-[#ff3b8a] ml-auto"
                  data-testid="resend-not-configured"
                >
                  // resend not configured — using mailto fallback
                </span>
              )}
              {resendStatus?.configured && (
                <span
                  className="font-mono-tech text-[10px] text-white/45 ml-auto"
                  data-testid="resend-configured"
                >
                  from: {resendStatus.sender}
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}



// ============================================================
// INDUSTRY PLAYGROUND — interactive per-industry sandbox.
// Live-runs each agent against pre-loaded industry samples (editable),
// shows the real LLM response inline. Lets Oliver test JADE end-to-end
// for any vertical as if he were the operator.
// ============================================================
function PlaygroundPanel() {
  const [industry, setIndustry] = useState("freight_brokerage");
  const cur = INDUSTRY_BY_ID_LOOKUP(industry);

  return (
    <div className="space-y-6" data-testid="playground-panel">
      {/* Industry picker strip */}
      <div className="deck-card p-6 relative" data-testid="playground-controls">
        <CornerBrackets />
        <div className="flex flex-col lg:flex-row lg:items-center gap-4 lg:justify-between">
          <div>
            <div className="mono-label text-[#7c5cff] mb-1">INDUSTRY PLAYGROUND · LIVE AGENTS</div>
            <p className="text-xs text-white/55 max-w-2xl leading-relaxed">
              Pick a vertical → JADE pre-loads realistic sample inputs across all 4 agents.
              Hit RUN on any card to fire the real LLM endpoint. Edit the inputs to test your own scenarios.
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {INDUSTRIES.map((i) => {
              const active = i.id === industry;
              return (
                <button
                  key={i.id}
                  data-testid={`playground-industry-${i.id}`}
                  onClick={() => setIndustry(i.id)}
                  className="px-3 py-2 mono-label text-[10px] transition"
                  style={{
                    border: `1px solid ${active ? i.color : "rgba(255,255,255,0.12)"}`,
                    color: active ? i.color : "rgba(255,255,255,0.55)",
                    background: active ? `${i.color}14` : "transparent",
                  }}
                >
                  {i.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 2x2 agent grid */}
      <div className="grid lg:grid-cols-2 gap-6">
        <ExtractCard industry={industry} color={cur.color} />
        <QualifyLeadCard industry={industry} color="#ccff00" />
        <SupportTriageCard industry={industry} color="#00ffff" />
        <DraftOutreachCard industry={industry} color="#ff3b8a" />
      </div>
    </div>
  );
}

const INDUSTRY_BY_ID_LOOKUP = (id) => INDUSTRIES.find((i) => i.id === id) || INDUSTRIES[0];
const sampleFor = (industry) => SAMPLES[industry] || SAMPLES.general || {};

function AgentCardShell({ title, color, busy, children, footer, testid }) {
  return (
    <div className="deck-card relative" data-testid={testid}>
      <CornerBrackets />
      <div className="p-5 border-b border-white/10 flex items-center justify-between">
        <div className="mono-label" style={{ color }}>{title}</div>
        {busy && (
          <span className="font-mono-tech text-[10px] text-[#ccff00] animate-pulse">// running…</span>
        )}
      </div>
      <div className="p-5 space-y-4">
        {children}
      </div>
      {footer && <div className="px-5 pb-5">{footer}</div>}
    </div>
  );
}

function ResultBlock({ title, color, content, monoJson }) {
  if (!content) return null;
  return (
    <div className="mt-3">
      <div className="mono-label text-[10px] mb-2" style={{ color }}>{title}</div>
      <pre
        className="font-mono-tech text-[11px] text-white/80 leading-relaxed whitespace-pre-wrap break-words border border-white/10 p-3 bg-black/40 max-h-[320px] overflow-auto"
      >
        {monoJson ? JSON.stringify(content, null, 2) : content}
      </pre>
    </div>
  );
}

// ---------- EXTRACT ----------
function ExtractCard({ industry, color }) {
  const sample = sampleFor(industry).extract || "Paste any text or document here…";
  const [text, setText] = useState(sample);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  useEffect(() => { setText(sampleFor(industry).extract || ""); setResult(null); }, [industry]);

  const run = async () => {
    setBusy(true); setResult(null);
    try {
      const { data } = await api.post("/agent/extract", { text, industry }, { timeout: 60000 });
      setResult(data.extracted);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Extract failed.");
    } finally { setBusy(false); }
  };

  return (
    <AgentCardShell title="EXTRACT · STRUCTURED JSON FROM DOCS" color={color} busy={busy} testid="playground-extract">
      <textarea
        data-testid="playground-extract-input"
        className="input-tech font-mono-tech text-xs leading-relaxed"
        rows={8}
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <button
        data-testid="playground-extract-run"
        onClick={run}
        disabled={busy || !text.trim()}
        className="btn-jade inline-flex items-center gap-2"
      >
        <Lightning size={14} weight="bold" /> RUN EXTRACT
      </button>
      <ResultBlock title="EXTRACTED JSON" color={color} content={result} monoJson />
    </AgentCardShell>
  );
}

// ---------- QUALIFY LEAD ----------
function QualifyLeadCard({ industry, color }) {
  const seed = () => ({
    company: "Acme " + (sampleFor(industry).outreach_recipient || "Logistics"),
    role: "Director of Operations",
    use_case: sampleFor(industry).outreach_summary || "looking to automate ops",
    monthly_volume: "1,200 tickets/mo",
    budget: "$1,500-$4,500/mo",
    timeline: "30 days",
  });
  const [form, setForm] = useState(seed());
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  useEffect(() => { setForm(seed()); setResult(null); /* eslint-disable-next-line */ }, [industry]);

  const run = async () => {
    setBusy(true); setResult(null);
    try {
      const { data } = await api.post("/agent/qualify-lead", { industry, ...form }, { timeout: 60000 });
      setResult(data.result);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Qualify failed.");
    } finally { setBusy(false); }
  };

  const tierColor = (t) => t === "hot" ? "#ff3b8a" : t === "warm" ? "#ccff00" : t === "cold" ? "#7c5cff" : "#fff";
  const fld = (k, label, span = 1) => (
    <label className={`block ${span === 2 ? "col-span-2" : ""}`}>
      <span className="mono-label text-[10px] text-white/40 block mb-1">{label}</span>
      <input
        data-testid={`playground-qualify-${k}`}
        className="input-tech text-xs py-1.5"
        value={form[k]}
        onChange={(e) => setForm({ ...form, [k]: e.target.value })}
      />
    </label>
  );

  return (
    <AgentCardShell title="QUALIFY LEAD · 0-100 FIT SCORE" color={color} busy={busy} testid="playground-qualify">
      <div className="grid grid-cols-2 gap-3">
        {fld("company", "COMPANY")}
        {fld("role", "ROLE")}
        {fld("use_case", "USE CASE", 2)}
        {fld("monthly_volume", "VOLUME")}
        {fld("budget", "BUDGET")}
        {fld("timeline", "TIMELINE", 2)}
      </div>
      <button
        data-testid="playground-qualify-run"
        onClick={run}
        disabled={busy}
        className="btn-jade inline-flex items-center gap-2"
      >
        <Lightning size={14} weight="bold" /> SCORE LEAD
      </button>
      {result && (
        <div className="border border-white/10 p-4 bg-black/40">
          <div className="flex items-center gap-4 mb-2">
            <span className="font-display font-black text-4xl tracking-tighter" style={{ color: tierColor(result.tier) }}>
              {result.score ?? "—"}
            </span>
            <span className="mono-label" style={{ color: tierColor(result.tier) }}>{(result.tier || "—").toUpperCase()}</span>
            {result.recommended_agent && (
              <span className="mono-label text-white/55 text-[10px] ml-auto">→ {result.recommended_agent}</span>
            )}
          </div>
          <p className="text-xs text-white/80 leading-relaxed">{result.rationale}</p>
          <div className="grid grid-cols-2 gap-3 mt-3">
            <div>
              <div className="mono-label text-[10px] text-[#ccff00] mb-1">GREEN</div>
              <ul className="space-y-1">{(result.green_flags || []).map((f, i) => <li key={i} className="font-mono-tech text-[11px] text-white/70">▸ {f}</li>)}</ul>
            </div>
            <div>
              <div className="mono-label text-[10px] text-[#ff3b8a] mb-1">RED</div>
              <ul className="space-y-1">{(result.red_flags || []).map((f, i) => <li key={i} className="font-mono-tech text-[11px] text-white/70">▸ {f}</li>)}</ul>
            </div>
          </div>
          {result.next_action && (
            <div className="mt-3 pt-3 border-t border-white/10">
              <div className="mono-label text-[10px] text-[#00ffff] mb-1">NEXT ACTION</div>
              <p className="text-xs text-white/80">{result.next_action}</p>
            </div>
          )}
        </div>
      )}
    </AgentCardShell>
  );
}

// ---------- SUPPORT TRIAGE ----------
function SupportTriageCard({ industry, color }) {
  const sample = sampleFor(industry).ticket || "A customer wrote in with a problem…";
  const [ticket, setTicket] = useState(sample);
  const [context, setContext] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  useEffect(() => { setTicket(sampleFor(industry).ticket || ""); setResult(null); }, [industry]);

  const run = async () => {
    setBusy(true); setResult(null);
    try {
      const { data } = await api.post("/agent/support-triage", { industry, ticket, company_context: context }, { timeout: 60000 });
      setResult(data.result);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Triage failed.");
    } finally { setBusy(false); }
  };

  const priColor = (p) => ({ p0: "#ff3b8a", p1: "#ff3b8a", p2: "#ccff00", p3: "#7c5cff" }[p] || "#fff");

  return (
    <AgentCardShell title="SUPPORT TRIAGE · TIER-1 ROUTING" color={color} busy={busy} testid="playground-triage">
      <textarea
        data-testid="playground-triage-input"
        className="input-tech font-mono-tech text-xs leading-relaxed"
        rows={6}
        placeholder="Paste the inbound ticket…"
        value={ticket}
        onChange={(e) => setTicket(e.target.value)}
      />
      <input
        data-testid="playground-triage-context"
        className="input-tech text-xs"
        placeholder="Optional company context (e.g. 'SaaS, 250 seats, enterprise tier')"
        value={context}
        onChange={(e) => setContext(e.target.value)}
      />
      <button
        data-testid="playground-triage-run"
        onClick={run}
        disabled={busy || !ticket.trim()}
        className="btn-jade inline-flex items-center gap-2"
      >
        <Lightning size={14} weight="bold" /> TRIAGE
      </button>
      {result && (
        <div className="border border-white/10 p-4 bg-black/40 space-y-2">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="mono-label text-[11px]" style={{ color: priColor(result.priority) }}>{(result.priority || "—").toUpperCase()}</span>
            <span className="mono-label text-[11px] text-[#00ffff]">{(result.category || "—").toUpperCase()}</span>
            <span className="mono-label text-[11px] text-white/60">SENTIMENT: {(result.sentiment || "—").toUpperCase()}</span>
            {result.escalate && (
              <span className="mono-label text-[11px] text-[#ff3b8a] ml-auto">ESCALATE → {result.escalate_to || "ops"}</span>
            )}
          </div>
          <p className="text-xs text-white/85 italic">{result.summary}</p>
          <div>
            <div className="mono-label text-[10px] text-[#ccff00] mb-1">SUGGESTED RESPONSE</div>
            <p className="font-mono-tech text-xs text-white/75 leading-relaxed whitespace-pre-wrap">{result.suggested_response}</p>
          </div>
          {result.tags?.length > 0 && (
            <div className="pt-2 border-t border-white/10 flex flex-wrap gap-1.5">
              {result.tags.map((t, i) => (
                <span key={i} className="mono-label text-[9px] px-2 py-0.5 border border-white/10 text-white/60">{t}</span>
              ))}
            </div>
          )}
        </div>
      )}
    </AgentCardShell>
  );
}

// ---------- DRAFT OUTREACH ----------
function DraftOutreachCard({ industry, color }) {
  const seedRecip = () => sampleFor(industry).outreach_recipient || "—";
  const seedSummary = () => sampleFor(industry).outreach_summary || "";
  const [recipient, setRecipient] = useState(seedRecip());
  const [summary, setSummary] = useState(seedSummary());
  const [tone, setTone] = useState("operator_direct");
  const [busy, setBusy] = useState(false);
  const [email, setEmail] = useState("");
  useEffect(() => { setRecipient(seedRecip()); setSummary(seedSummary()); setEmail(""); /* eslint-disable-next-line */ }, [industry]);

  const run = async () => {
    setBusy(true); setEmail("");
    try {
      const { data } = await api.post("/agent/draft-outreach", { industry, recipient, summary, tone }, { timeout: 60000 });
      setEmail(data.email);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Draft failed.");
    } finally { setBusy(false); }
  };

  return (
    <AgentCardShell title="DRAFT OUTREACH · COLD/WARM EMAILS" color={color} busy={busy} testid="playground-outreach">
      <input
        data-testid="playground-outreach-recipient"
        className="input-tech text-xs"
        placeholder="Recipient (name or company)"
        value={recipient}
        onChange={(e) => setRecipient(e.target.value)}
      />
      <textarea
        data-testid="playground-outreach-summary"
        className="input-tech font-mono-tech text-xs leading-relaxed"
        rows={5}
        placeholder="Context (what you want to communicate)"
        value={summary}
        onChange={(e) => setSummary(e.target.value)}
      />
      <select
        data-testid="playground-outreach-tone"
        className="input-tech text-xs py-2"
        value={tone}
        onChange={(e) => setTone(e.target.value)}
      >
        <option value="operator_direct">OPERATOR-DIRECT</option>
        <option value="courteous_direct">COURTEOUS-DIRECT</option>
        <option value="warm">WARM</option>
        <option value="urgent">URGENT</option>
      </select>
      <button
        data-testid="playground-outreach-run"
        onClick={run}
        disabled={busy || !summary.trim()}
        className="btn-jade inline-flex items-center gap-2"
      >
        <Lightning size={14} weight="bold" /> DRAFT EMAIL
      </button>
      <ResultBlock title="DRAFTED EMAIL" color={color} content={email} />
    </AgentCardShell>
  );
}

