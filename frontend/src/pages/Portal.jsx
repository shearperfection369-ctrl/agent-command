import { useState } from "react";
import { toast } from "sonner";
import { CornerBrackets, SectionLabel } from "../components/Brackets";
import { api } from "../lib/api";
import { ArrowRight, MagnifyingGlass } from "@phosphor-icons/react";

export default function Portal() {
  const [email, setEmail] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const lookup = async (e) => {
    e?.preventDefault();
    if (!email) return;
    setLoading(true);
    try {
      const { data } = await api.get("/portal/preview", { params: { email } });
      setData(data);
      if (!data.org) toast.error("No subscription found for that email.");
    } catch (err) {
      toast.error("Lookup failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-console min-h-screen">
      <section className="px-6 lg:px-10 py-16 grid-bg-tight border-b border-white/5">
        <div className="max-w-[1100px] mx-auto">
          <SectionLabel idx={0} color="#7c5cff">CUSTOMER · PORTAL PREVIEW</SectionLabel>
          <h1 className="font-display font-black text-white text-4xl sm:text-6xl tracking-tighter">
            Your <span className="accent-cyan">deck.</span>
          </h1>
          <p className="mt-4 text-white/65 max-w-xl text-sm">
            Read-only preview of your subscription, agent runs, and token usage. Production portal (multi-user, role-based) ships in your Fleet onboarding.
          </p>

          <form onSubmit={lookup} className="mt-8 flex gap-2 max-w-md">
            <input data-testid="portal-email" required type="email" placeholder="you@company.com"
              value={email} onChange={(e) => setEmail(e.target.value)} className="input-tech" />
            <button data-testid="portal-lookup-btn" className="btn-jade inline-flex items-center gap-2">
              <MagnifyingGlass size={14} weight="bold" /> LOOK UP
            </button>
          </form>
        </div>
      </section>

      <section className="px-6 lg:px-10 py-16">
        <div className="max-w-[1100px] mx-auto">
          {loading && <div className="font-mono-tech text-[#ccff00]">// pulling tape…</div>}
          {data && data.org && (
            <div className="space-y-8">
              <div className="grid sm:grid-cols-4 gap-4">
                <Stat k="COMPANY" v={data.org.company} c="#ccff00" />
                <Stat k="TIER" v={(data.org.tier || "TRIAL").toUpperCase()} c="#00ffff" />
                <Stat k="STATUS" v={data.org.subscription_status?.toUpperCase()} c="#7c5cff" />
                <Stat k="MONTHLY BUDGET" v={`${(data.org.monthly_token_budget / 1000).toLocaleString()}k TOK`} c="#ff3b8a" />
              </div>

              <div className="deck-card relative" data-testid="portal-runs">
                <CornerBrackets />
                <div className="p-6 border-b border-white/10 mono-label text-[#ccff00]">RECENT AGENT RUNS · TAPE</div>
                <div className="divide-y divide-white/5">
                  {data.runs.length === 0 && <div className="p-6 font-mono-tech text-xs text-white/40">// no runs yet</div>}
                  {data.runs.map((r) => (
                    <div key={r.id} className="p-4 grid grid-cols-[120px_100px_1fr_140px] gap-4 items-center">
                      <span className="mono-label" style={{ color: r.agent_type === "chat" ? "#ccff00" : "#00ffff" }}>{r.agent_type}</span>
                      <span className="font-mono-tech text-[10px] text-white/40">{r.provider}</span>
                      <span className="font-mono-tech text-xs text-white/65 truncate">{r.input_preview}</span>
                      <span className="font-mono-tech text-[10px] text-white/35 text-right">{new Date(r.created_at).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function Stat({ k, v, c }) {
  return (
    <div className="deck-card p-5 relative">
      <CornerBrackets />
      <div className="mono-label text-white/40">{k}</div>
      <div className="font-display font-bold text-white text-xl mt-2" style={{ color: c }}>{v}</div>
    </div>
  );
}
