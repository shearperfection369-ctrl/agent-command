import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import { isAuthed } from "../lib/auth";
import { CornerBrackets, SectionLabel } from "../components/Brackets";
import { ArrowsClockwise, Users, ChartBar, Robot, Clock } from "@phosphor-icons/react";

export default function Dashboard() {
  const nav = useNavigate();
  const [stats, setStats] = useState(null);
  const [leads, setLeads] = useState([]);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthed()) { nav("/login"); return; }
    load();
  }, []);

  const load = async () => {
    setLoading(true);
    try {
      const [s, l, r] = await Promise.all([
        api.get("/admin/stats"),
        api.get("/leads"),
        api.get("/admin/agent-runs"),
      ]);
      setStats(s.data); setLeads(l.data); setRuns(r.data);
    } catch (e) {
      if (e?.response?.status === 401) nav("/login");
      else toast.error("Failed to load.");
    } finally { setLoading(false); }
  };

  const updateLead = async (id, status) => {
    try {
      await api.patch(`/leads/${id}`, null, { params: { status_value: status } });
      toast.success(`Lead → ${status}`);
      load();
    } catch (e) { toast.error("Update failed."); }
  };

  if (loading) {
    return <div className="min-h-screen bg-console grid place-items-center font-mono-tech text-[#ccff00]">// loading console…</div>;
  }

  return (
    <div className="bg-console min-h-screen">
      <section className="px-6 lg:px-10 py-12 border-b border-white/5 grid-bg-tight">
        <div className="max-w-[1400px] mx-auto">
          <div className="flex items-center justify-between">
            <div>
              <SectionLabel idx={0} color="#ccff00">CONSOLE · ADMIN VAULT</SectionLabel>
              <h1 className="font-display font-black text-white text-5xl tracking-tighter">
                Mission <span className="accent-cyan">control.</span>
              </h1>
            </div>
            <button data-testid="dashboard-refresh-btn" onClick={load} className="btn-ghost inline-flex items-center gap-2"><ArrowsClockwise size={14} weight="bold" /> REFRESH</button>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
            <StatCard icon={Users} c="#ccff00" k="LEADS TOTAL" v={stats?.leads_total ?? 0} />
            <StatCard icon={ChartBar} c="#00ffff" k="NEW LEADS" v={stats?.leads_new ?? 0} />
            <StatCard icon={Robot} c="#7c5cff" k="AGENT RUNS" v={stats?.runs_total ?? 0} />
            <StatCard icon={Clock} c="#ff3b8a" k="MODELS · LIVE" v="CLAUDE · GPT" />
          </div>
        </div>
      </section>

      <section className="px-6 lg:px-10 py-12">
        <div className="max-w-[1400px] mx-auto grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 deck-card relative" data-testid="leads-table">
            <CornerBrackets />
            <div className="p-6 border-b border-white/10 flex items-center justify-between">
              <div className="mono-label text-[#ccff00]">LEADS · QUEUE</div>
              <span className="mono-label text-white/40">SORTED · NEWEST</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/5">
                    {["NAME","COMPANY","VERTICAL","USE CASE","STATUS","ACTIONS"].map((h) => (
                      <th key={h} className="p-4 text-left mono-label text-white/40">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {leads.length === 0 && <tr><td colSpan={6} className="p-8 text-center font-mono-tech text-xs text-white/40">// no leads yet</td></tr>}
                  {leads.map((l) => (
                    <tr key={l.id} data-testid={`lead-row-${l.id}`} className="border-b border-white/5 hover:bg-white/[0.02]">
                      <td className="p-4">
                        <div className="text-white font-display font-bold">{l.name}</div>
                        <div className="font-mono-tech text-[11px] text-white/45">{l.email}</div>
                      </td>
                      <td className="p-4 text-white/75 font-mono-tech text-xs">{l.company}</td>
                      <td className="p-4 mono-label text-[#00ffff]">{l.vertical?.toUpperCase()}</td>
                      <td className="p-4 text-white/65 text-xs max-w-[240px] truncate" title={l.use_case}>{l.use_case || "—"}</td>
                      <td className="p-4">
                        <span className="mono-label" style={{
                          color: l.status === "new" ? "#ccff00" :
                                 l.status === "contacted" ? "#00ffff" :
                                 l.status === "won" ? "#7c5cff" : "#ff3b8a"
                        }}>{l.status?.toUpperCase()}</span>
                      </td>
                      <td className="p-4">
                        <select
                          data-testid={`lead-status-${l.id}`}
                          value={l.status}
                          onChange={(e) => updateLead(l.id, e.target.value)}
                          className="input-tech text-xs py-1.5 w-[130px]"
                        >
                          {["new","contacted","qualified","won","lost"].map((s) => <option key={s}>{s}</option>)}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="deck-card relative" data-testid="runs-panel">
            <CornerBrackets />
            <div className="p-6 border-b border-white/10 mono-label text-[#7c5cff]">AGENT RUNS · TAPE</div>
            <div className="max-h-[600px] overflow-y-auto">
              {runs.length === 0 && <div className="p-6 font-mono-tech text-xs text-white/40">// no runs yet</div>}
              {runs.map((r) => (
                <div key={r.id} data-testid={`run-${r.id}`} className="p-4 border-b border-white/5 hover:bg-white/[0.02]">
                  <div className="flex items-center justify-between">
                    <span className="mono-label" style={{
                      color: r.agent_type === "chat" ? "#ccff00" :
                             r.agent_type === "extract_bol" ? "#00ffff" :
                             r.agent_type === "draft_outreach" ? "#7c5cff" : "#ff3b8a"
                    }}>{r.agent_type}</span>
                    <span className="font-mono-tech text-[10px] text-white/40">{new Date(r.created_at).toLocaleTimeString()}</span>
                  </div>
                  <div className="font-mono-tech text-[11px] text-white/55 mt-2 line-clamp-2">{r.input_preview}</div>
                  <div className="font-mono-tech text-[10px] text-white/35 mt-2">{r.provider} · {r.model}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function StatCard({ icon: Icon, c, k, v }) {
  return (
    <div className="deck-card p-6 relative">
      <CornerBrackets />
      <div className="flex items-center justify-between mb-4">
        <Icon size={20} style={{ color: c }} weight="bold" />
        <span className="mono-label" style={{ color: c }}>{k}</span>
      </div>
      <div className="font-display font-black text-white text-4xl tracking-tighter">{v}</div>
    </div>
  );
}
