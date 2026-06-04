import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { ArrowRight, ChatCircle, FileText, EnvelopeSimple, Target, Stop, Robot, User, ArrowsClockwise, Lifebuoy } from "@phosphor-icons/react";
import { api, API_BASE } from "../lib/api";
import { CornerBrackets, SectionLabel } from "../components/Brackets";
import { INDUSTRIES, sampleFor } from "../lib/industries";

const TABS = [
  { id: "chat", label: "OPS CO-PILOT", icon: ChatCircle, color: "#ccff00" },
  { id: "extract", label: "DATA EXTRACT", icon: FileText, color: "#00ffff" },
  { id: "outreach", label: "OUTREACH DRAFT", icon: EnvelopeSimple, color: "#7c5cff" },
  { id: "qualify", label: "LEAD QUAL", icon: Target, color: "#ff3b8a" },
  { id: "support", label: "SUPPORT TRIAGE", icon: Lifebuoy, color: "#ccff00" },
];

export default function AgentDemo() {
  const [tab, setTab] = useState("chat");
  const [provider, setProvider] = useState("anthropic");
  const [industry, setIndustry] = useState("freight_brokerage");

  return (
    <div className="bg-console min-h-screen">
      {/* Header */}
      <section className="border-b border-white/5 px-6 lg:px-10 py-10 grid-bg-tight relative">
        <div className="max-w-[1400px] mx-auto">
          <SectionLabel idx={0} color="#00ffff">CONSOLE · LIVE</SectionLabel>
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6">
            <div>
              <h1 className="font-display font-black text-white text-4xl sm:text-6xl tracking-tighter">
                The <span className="accent-cyan">deck</span> is hot.
              </h1>
              <p className="mt-4 text-white/65 max-w-2xl text-sm">
                Pick an industry. Pick an agent. JADE loads the right lexicon, schema, and tone profile — then shows the work. Streaming from Claude Sonnet 4.5 or GPT-5.2.
              </p>
            </div>
            <ProviderSwitch provider={provider} setProvider={setProvider} />
          </div>

          {/* INDUSTRY SELECTOR */}
          <div className="mt-8">
            <div className="mono-label text-white/45 mb-3">INDUSTRY · TUNE THE AGENT</div>
            <div className="flex flex-wrap gap-2" data-testid="industry-selector">
              {INDUSTRIES.map((ind) => {
                const active = industry === ind.id;
                return (
                  <button
                    key={ind.id}
                    data-testid={`industry-${ind.id}`}
                    onClick={() => setIndustry(ind.id)}
                    className="inline-flex items-center px-3 py-2 mono-label transition"
                    style={{
                      border: `1px solid ${active ? ind.color : "rgba(255,255,255,0.10)"}`,
                      color: active ? ind.color : "rgba(255,255,255,0.55)",
                      background: active ? `${ind.color}11` : "transparent",
                    }}
                  >
                    {ind.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* AGENT TAB SELECTOR */}
          <div className="mt-6 flex flex-wrap gap-2">
            {TABS.map((t) => {
              const Icon = t.icon;
              const active = tab === t.id;
              return (
                <button
                  key={t.id}
                  data-testid={`tab-${t.id}`}
                  onClick={() => setTab(t.id)}
                  className="inline-flex items-center gap-2 px-4 py-3 mono-label transition"
                  style={{
                    border: `1px solid ${active ? t.color : "rgba(255,255,255,0.12)"}`,
                    color: active ? t.color : "rgba(255,255,255,0.65)",
                    background: active ? `${t.color}11` : "transparent",
                  }}
                >
                  <Icon size={14} weight="bold" /> {t.label}
                </button>
              );
            })}
          </div>
        </div>
      </section>

      <section className="px-6 lg:px-10 py-12">
        <div className="max-w-[1400px] mx-auto">
          {tab === "chat" && <ChatPanel key={`chat-${industry}-${provider}`} provider={provider} industry={industry} />}
          {tab === "extract" && <ExtractPanel key={`ext-${industry}`} provider={provider} industry={industry} />}
          {tab === "outreach" && <OutreachPanel key={`out-${industry}`} provider={provider} industry={industry} />}
          {tab === "qualify" && <QualifyPanel key={`qua-${industry}`} provider={provider} industry={industry} />}
          {tab === "support" && <SupportPanel key={`sup-${industry}`} provider={provider} industry={industry} />}
        </div>
      </section>
    </div>
  );
}

function ProviderSwitch({ provider, setProvider }) {
  return (
    <div className="flex items-center gap-2 p-1 border border-white/10" data-testid="provider-switch">
      {[
        { id: "anthropic", label: "CLAUDE 4.5", c: "#ccff00" },
        { id: "openai", label: "GPT-5.2", c: "#00ffff" },
      ].map((p) => (
        <button
          key={p.id}
          data-testid={`provider-${p.id}`}
          onClick={() => setProvider(p.id)}
          className="px-4 py-2 mono-label transition"
          style={{
            background: provider === p.id ? p.c : "transparent",
            color: provider === p.id ? "#02030a" : "rgba(255,255,255,0.6)",
            fontWeight: 700,
          }}
        >
          {p.label}
        </button>
      ))}
    </div>
  );
}

/* ===================== CHAT ===================== */
function ChatPanel({ provider, industry }) {
  const sample = sampleFor(industry);
  const [msgs, setMsgs] = useState([
    { role: "jade", text: `Locked in. Compiling for ${industry.replace("_", " ")}. Ask me anything — I'll watch the tape.` }
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [sessionId] = useState(() => `demo-${Math.random().toString(36).slice(2, 10)}`);
  const scrollRef = useRef(null);
  const abortRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [msgs]);

  const send = async (override) => {
    const userText = (override ?? input).trim();
    if (!userText || streaming) return;
    if (!override) setInput("");
    setMsgs((m) => [...m, { role: "user", text: userText }, { role: "jade", text: "" }]);
    setStreaming(true);

    const ctrl = new AbortController();
    abortRef.current = ctrl;
    try {
      const res = await fetch(`${API_BASE}/agent/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: userText, provider, industry }),
        signal: ctrl.signal,
      });
      if (!res.body) throw new Error("No stream");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n\n");
        buf = lines.pop() || "";
        for (const ln of lines) {
          const ms = ln.replace(/^data:\s*/, "").trim();
          if (!ms) continue;
          try {
            const j = JSON.parse(ms);
            if (j.delta) {
              setMsgs((arr) => {
                const copy = [...arr];
                copy[copy.length - 1] = { role: "jade", text: copy[copy.length - 1].text + j.delta };
                return copy;
              });
            }
            if (j.error) toast.error(j.error);
          } catch {}
        }
      }
    } catch (e) {
      if (e.name !== "AbortError") toast.error("Stream failed");
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div className="grid lg:grid-cols-12 gap-6">
      <aside className="lg:col-span-3 deck-card p-6 relative" data-testid="chat-rail">
        <CornerBrackets />
        <div className="mono-label text-[#ccff00] mb-4">SESSION</div>
        <div className="font-mono-tech text-xs text-white/60 break-all mb-6">{sessionId}</div>
        <div className="mono-label text-white/40 mb-3">SAMPLE PROMPTS · {industry.replace("_", " ").toUpperCase()}</div>
        <ul className="space-y-2 text-sm">
          {sample.chat_prompts.map((p, i) => (
            <li key={i}>
              <button data-testid={`chat-prompt-${i}`} onClick={() => send(p)} disabled={streaming}
                className="text-left w-full text-white/70 hover:text-[#00ffff] transition py-2 border-b border-white/5 font-mono-tech text-xs disabled:opacity-50">
                ▶ {p}
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <main className="lg:col-span-6 deck-card relative flex flex-col h-[640px]" data-testid="chat-panel">
        <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-2"><span className="dot" /><span className="mono-label text-[#ccff00]">JADE · {provider === "anthropic" ? "CLAUDE-SONNET-4.5" : "GPT-5.2"}</span></div>
          <span className="mono-label text-white/35">{industry.replace("_", " ").toUpperCase()}</span>
        </div>
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-5">
          {msgs.map((m, i) => (
            <div key={i} data-testid={`chat-msg-${i}`} className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : ""}`}>
              <div className="h-8 w-8 border grid place-items-center shrink-0"
                style={{ borderColor: m.role === "user" ? "#7c5cff" : "#ccff00" }}>
                {m.role === "user" ? <User size={14} color="#7c5cff" weight="bold" /> : <Robot size={14} color="#ccff00" weight="bold" />}
              </div>
              <div className={`max-w-[80%] p-4 ${m.role === "user" ? "bg-[#7c5cff]/10 border border-[#7c5cff]/40" : "bg-[#06081a] border border-white/5"}`}>
                <div className="mono-label mb-2" style={{ color: m.role === "user" ? "#7c5cff" : "#ccff00" }}>{m.role === "user" ? "OPERATOR" : "JADE"}</div>
                <pre className="text-sm text-white/85 leading-relaxed whitespace-pre-wrap font-sans">{m.text}{m.role === "jade" && streaming && i === msgs.length - 1 && <span className="inline-block w-2 h-4 bg-[#ccff00] ml-1 align-middle animate-pulse" />}</pre>
              </div>
            </div>
          ))}
        </div>
        <div className="border-t border-white/5 p-4">
          <div className="flex gap-2">
            <input
              data-testid="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), send())}
              className="input-tech flex-1"
              placeholder="Say the word, operator…"
              disabled={streaming}
            />
            <button data-testid="chat-send-btn" onClick={() => send()} disabled={streaming || !input.trim()} className="btn-jade">
              {streaming ? <Stop size={16} weight="bold" /> : <ArrowRight size={16} weight="bold" />}
            </button>
          </div>
        </div>
      </main>

      <aside className="lg:col-span-3 deck-card p-6 relative" data-testid="chat-trust">
        <CornerBrackets />
        <div className="mono-label text-[#00ffff] mb-4">TRUST · LIVE</div>
        <Metric label="INDUSTRY" v={industry.replace("_", " ").toUpperCase()} c="#ccff00" />
        <Metric label="MODEL" v={provider === "anthropic" ? "CLAUDE 4.5" : "GPT-5.2"} c="#00ffff" />
        <Metric label="STREAMING" v={streaming ? "ACTIVE" : "IDLE"} c="#7c5cff" />
        <Metric label="TURNS" v={Math.max(0, msgs.length - 1)} c="#ff3b8a" />
        <Metric label="DATA · RETAIN" v="ZERO" c="#ccff00" />
        <div className="mt-8 mono-label text-white/40 mb-3">ACTIONS</div>
        <ul className="space-y-2 text-xs text-white/60 font-mono-tech">
          <li className="flex items-center gap-2"><span className="text-[#ccff00]">✓</span> Vertical lexicon loaded</li>
          <li className="flex items-center gap-2"><span className="text-[#ccff00]">✓</span> Human-in-the-loop ready</li>
          <li className="flex items-center gap-2"><span className="text-[#ccff00]">✓</span> Audit log per turn</li>
        </ul>
      </aside>
    </div>
  );
}

function Metric({ label, v, c }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-white/5">
      <span className="mono-label text-white/40">{label}</span>
      <span className="font-mono-tech text-sm" style={{ color: c }}>{v}</span>
    </div>
  );
}

/* ===================== EXTRACT ===================== */
function ExtractPanel({ provider, industry }) {
  const sample = sampleFor(industry);
  const [text, setText] = useState(sample.extract);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadBusy, setUploadBusy] = useState(false);

  const run = async () => {
    setLoading(true); setResult(null);
    try {
      const { data } = await api.post("/agent/extract", { text, provider, industry });
      setResult(data.extracted);
      toast.success("Extraction complete.");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Extraction failed.");
    } finally { setLoading(false); }
  };

  const onPdf = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadBusy(true); setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("industry", industry);
      fd.append("provider", provider);
      const { data } = await api.post("/agent/extract-pdf", fd, { headers: { "Content-Type": "multipart/form-data" } });
      setResult(data.extracted);
      toast.success(`Parsed ${file.name}`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "PDF parse failed.");
    } finally { setUploadBusy(false); e.target.value = ""; }
  };

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      <div className="deck-card p-6 relative" data-testid="extract-input-panel">
        <CornerBrackets />
        <div className="flex items-center justify-between mb-4">
          <div className="mono-label text-[#00ffff]">INPUT · DOC / FORM / TICKET · {industry.replace("_", " ").toUpperCase()}</div>
          <label className="mono-label text-[#ccff00] hover:text-white cursor-pointer">
            {uploadBusy ? "PARSING PDF…" : "↑ UPLOAD PDF"}
            <input data-testid="extract-pdf-input" type="file" accept="application/pdf" className="hidden" onChange={onPdf} disabled={uploadBusy} />
          </label>
        </div>
        <textarea data-testid="extract-input" value={text} onChange={(e) => setText(e.target.value)} rows={18} className="input-tech font-mono-tech text-xs" spellCheck={false} />
        <div className="mt-4 flex gap-3">
          <button data-testid="extract-run-btn" onClick={run} disabled={loading} className="btn-jade inline-flex items-center gap-2">
            {loading ? <><ArrowsClockwise size={14} weight="bold" className="animate-spin" /> PARSING…</> : <>RUN EXTRACTION <ArrowRight size={14} weight="bold" /></>}
          </button>
          <button data-testid="extract-reset-btn" onClick={() => setText(sample.extract)} className="btn-ghost text-xs">RESET</button>
        </div>
      </div>
      <div className="deck-card p-6 relative" data-testid="extract-output-panel">
        <CornerBrackets />
        <div className="mono-label text-[#ccff00] mb-4">OUTPUT · STRUCTURED JSON</div>
        {!result && !loading && <div className="font-mono-tech text-xs text-white/40">// awaiting input…</div>}
        {loading && <div className="font-mono-tech text-xs text-[#00ffff] animate-pulse">// parsing tape…</div>}
        {result && (
          <div>
            <ExtractTopFields result={result} />
            <pre data-testid="extract-output-json" className="font-mono-tech text-[11px] text-white/70 leading-relaxed bg-[#02030a] p-4 border border-white/5 max-h-[280px] overflow-y-auto">{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

function ExtractTopFields({ result }) {
  if (!result || typeof result !== "object") return null;
  const entries = Object.entries(result)
    .filter(([k, v]) => v != null && k !== "raw" && k !== "parse_error" && typeof v !== "object")
    .slice(0, 6);
  if (entries.length === 0) return null;
  const colors = ["#ccff00","#00ffff","#7c5cff","#ff3b8a","#ccff00","#00ffff"];
  return (
    <div className="grid grid-cols-2 gap-3 mb-5">
      {entries.map(([k, v], i) => (
        <div key={k} className="border border-white/5 p-3 bg-[#02030a]">
          <div className="mono-label text-white/40">{k.replace(/_/g, " ").toUpperCase()}</div>
          <div className="font-mono-tech text-sm mt-1 break-words" style={{ color: colors[i] }}>{String(v)}</div>
        </div>
      ))}
    </div>
  );
}

/* ===================== OUTREACH ===================== */
function OutreachPanel({ provider, industry }) {
  const sample = sampleFor(industry);
  const [recipient, setRecipient] = useState(sample.outreach_recipient);
  const [summary, setSummary] = useState(sample.outreach_summary);
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const run = async () => {
    setLoading(true); setEmail("");
    try {
      const { data } = await api.post("/agent/draft-outreach", { recipient, summary, provider, industry, tone: "direct" });
      setEmail(data.email);
    } catch (e) {
      toast.error("Draft failed.");
    } finally { setLoading(false); }
  };

  const copy = async () => {
    await navigator.clipboard.writeText(email);
    setCopied(true); setTimeout(() => setCopied(false), 1500);
    toast.success("Tape copied.");
  };

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      <div className="deck-card p-6 relative" data-testid="outreach-input-panel">
        <CornerBrackets />
        <div className="mono-label text-[#7c5cff] mb-4">INPUT · RECIPIENT + CONTEXT · {industry.replace("_", " ").toUpperCase()}</div>
        <div className="space-y-4">
          <div>
            <div className="mono-label text-white/45 mb-2">RECIPIENT</div>
            <input data-testid="outreach-recipient" className="input-tech" value={recipient} onChange={(e) => setRecipient(e.target.value)} />
          </div>
          <div>
            <div className="mono-label text-white/45 mb-2">CONTEXT</div>
            <textarea data-testid="outreach-summary" className="input-tech" rows={8} value={summary} onChange={(e) => setSummary(e.target.value)} />
          </div>
          <button data-testid="outreach-run-btn" onClick={run} disabled={loading} className="btn-jade inline-flex items-center gap-2">
            {loading ? "DRAFTING…" : <>DRAFT THE EMAIL <ArrowRight size={14} weight="bold" /></>}
          </button>
        </div>
      </div>
      <div className="deck-card p-6 relative" data-testid="outreach-output-panel">
        <CornerBrackets />
        <div className="flex items-center justify-between mb-4">
          <span className="mono-label text-[#ccff00]">OUTPUT · DRAFT EMAIL</span>
          {email && <button data-testid="outreach-copy-btn" onClick={copy} className="mono-label text-[#00ffff] hover:text-[#ccff00]">{copied ? "✓ COPIED" : "COPY"}</button>}
        </div>
        {!email && !loading && <div className="font-mono-tech text-xs text-white/40">// awaiting input…</div>}
        {loading && <div className="font-mono-tech text-xs text-[#7c5cff] animate-pulse">// composing tape…</div>}
        {email && <pre data-testid="outreach-output" className="text-sm text-white/85 whitespace-pre-wrap leading-relaxed font-sans">{email}</pre>}
      </div>
    </div>
  );
}

/* ===================== QUALIFY ===================== */
function QualifyPanel({ provider, industry }) {
  const [form, setForm] = useState({
    company: "Acme Industries",
    role: "Director of Operations",
    use_case: "Tier-1 support deflection + document extraction",
    monthly_volume: "~2,000 docs / 800 tickets",
    budget: "$3-5k/mo",
    timeline: "Pilot in 30 days",
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true); setResult(null);
    try {
      const { data } = await api.post("/agent/qualify-lead", { ...form, provider, industry });
      setResult(data.result);
    } catch (e) {
      toast.error("Scoring failed.");
    } finally { setLoading(false); }
  };

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      <div className="deck-card p-6 relative" data-testid="qualify-input-panel">
        <CornerBrackets />
        <div className="mono-label text-[#ff3b8a] mb-4">INPUT · LEAD · {industry.replace("_", " ").toUpperCase()}</div>
        <div className="space-y-3">
          {Object.entries({ company: "COMPANY", role: "ROLE", use_case: "USE CASE", monthly_volume: "VOLUME", budget: "BUDGET", timeline: "TIMELINE" }).map(([k, label]) => (
            <div key={k}>
              <div className="mono-label text-white/45 mb-1">{label}</div>
              <input data-testid={`qualify-${k}`} className="input-tech" value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} />
            </div>
          ))}
        </div>
        <button data-testid="qualify-run-btn" onClick={run} disabled={loading} className="btn-jade mt-5 inline-flex items-center gap-2">
          {loading ? "SCORING…" : <>SCORE THE LEAD <ArrowRight size={14} weight="bold" /></>}
        </button>
      </div>
      <div className="deck-card p-6 relative" data-testid="qualify-output-panel">
        <CornerBrackets />
        <div className="mono-label text-[#ccff00] mb-4">OUTPUT · QUALIFICATION</div>
        {!result && !loading && <div className="font-mono-tech text-xs text-white/40">// awaiting input…</div>}
        {loading && <div className="font-mono-tech text-xs text-[#ff3b8a] animate-pulse">// scoring…</div>}
        {result && !result.parse_error && (
          <div>
            <div className="flex items-end gap-6 mb-6">
              <div>
                <div className="mono-label text-white/45">SCORE</div>
                <div className="font-display font-black text-[#ccff00] text-7xl leading-none glow-lime">{result.score}</div>
              </div>
              <div className="pb-2">
                <div className="mono-label text-white/45">TIER</div>
                <div className="font-display font-bold text-2xl uppercase" style={{ color: result.tier === "hot" ? "#ff3b8a" : result.tier === "warm" ? "#ccff00" : "#7c5cff" }}>{result.tier}</div>
              </div>
              {result.recommended_agent && (
                <div className="pb-2">
                  <div className="mono-label text-white/45">RECOMMEND</div>
                  <div className="font-mono-tech text-sm text-[#00ffff] uppercase">{result.recommended_agent}</div>
                </div>
              )}
            </div>
            <Section title="RATIONALE" body={result.rationale} color="#00ffff" />
            <Section title="NEXT ACTION" body={result.next_action} color="#ccff00" />
            <div className="grid sm:grid-cols-2 gap-4 mt-5">
              <FlagList title="GREEN FLAGS" items={result.green_flags || []} color="#ccff00" />
              <FlagList title="RED FLAGS" items={result.red_flags || []} color="#ff3b8a" />
            </div>
          </div>
        )}
        {result?.parse_error && <pre className="font-mono-tech text-xs text-white/65 whitespace-pre-wrap">{result.raw}</pre>}
      </div>
    </div>
  );
}

/* ===================== SUPPORT TRIAGE ===================== */
function SupportPanel({ provider, industry }) {
  const sample = sampleFor(industry);
  const [ticket, setTicket] = useState(sample.ticket);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true); setResult(null);
    try {
      const { data } = await api.post("/agent/support-triage", { ticket, provider, industry });
      setResult(data.result);
    } catch (e) {
      toast.error("Triage failed.");
    } finally { setLoading(false); }
  };

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      <div className="deck-card p-6 relative" data-testid="support-input-panel">
        <CornerBrackets />
        <div className="mono-label text-[#ccff00] mb-4">INPUT · INCOMING TICKET · {industry.replace("_", " ").toUpperCase()}</div>
        <textarea data-testid="support-input" value={ticket} onChange={(e) => setTicket(e.target.value)} rows={14} className="input-tech text-sm" />
        <button data-testid="support-run-btn" onClick={run} disabled={loading} className="btn-jade mt-4 inline-flex items-center gap-2">
          {loading ? "TRIAGING…" : <>TRIAGE THE TICKET <ArrowRight size={14} weight="bold" /></>}
        </button>
      </div>
      <div className="deck-card p-6 relative" data-testid="support-output-panel">
        <CornerBrackets />
        <div className="mono-label text-[#00ffff] mb-4">OUTPUT · TRIAGE RESULT</div>
        {!result && !loading && <div className="font-mono-tech text-xs text-white/40">// awaiting input…</div>}
        {loading && <div className="font-mono-tech text-xs text-[#ccff00] animate-pulse">// reading the tape…</div>}
        {result && !result.parse_error && (
          <div>
            <div className="grid grid-cols-2 gap-3 mb-5">
              <Stat k="PRIORITY" v={result.priority?.toUpperCase() || "—"} c="#ff3b8a" />
              <Stat k="SENTIMENT" v={result.sentiment?.toUpperCase() || "—"} c="#7c5cff" />
              <Stat k="CATEGORY" v={result.category || "—"} c="#00ffff" />
              <Stat k="ESCALATE" v={result.escalate ? `YES → ${result.escalate_to || "MGR"}` : "NO"} c="#ccff00" />
            </div>
            <Section title="SUMMARY" body={result.summary} color="#00ffff" />
            <Section title="SUGGESTED RESPONSE" body={result.suggested_response} color="#ccff00" />
            {result.tags?.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {result.tags.map((t) => <span key={t} className="chip chip-violet">{t}</span>)}
              </div>
            )}
          </div>
        )}
        {result?.parse_error && <pre className="font-mono-tech text-xs text-white/65 whitespace-pre-wrap">{result.raw}</pre>}
      </div>
    </div>
  );
}

function Stat({ k, v, c }) {
  return (
    <div className="border border-white/5 p-3 bg-[#02030a]">
      <div className="mono-label text-white/40">{k}</div>
      <div className="font-mono-tech text-sm mt-1 break-words" style={{ color: c }}>{v}</div>
    </div>
  );
}

function Section({ title, body, color }) {
  if (!body) return null;
  return (
    <div className="mt-5">
      <div className="mono-label mb-2" style={{ color }}>{title}</div>
      <p className="text-sm text-white/80 leading-relaxed whitespace-pre-wrap">{body}</p>
    </div>
  );
}

function FlagList({ title, items, color }) {
  return (
    <div>
      <div className="mono-label mb-2" style={{ color }}>{title}</div>
      <ul className="space-y-1.5">
        {items.length === 0 && <li className="font-mono-tech text-xs text-white/40">// none</li>}
        {items.map((it, i) => (
          <li key={i} className="text-xs text-white/70 font-mono-tech flex gap-2"><span style={{ color }}>▸</span>{it}</li>
        ))}
      </ul>
    </div>
  );
}
