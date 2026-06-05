import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { ArrowRight, Plus, TrashSimple, ArrowLeft } from "@/lib/icons";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "../components/Brackets";

const STEP_KINDS = [
  { id: "extract", label: "DATA EXTRACTION", c: "#00ffff" },
  { id: "qualify", label: "LEAD QUALIFICATION", c: "#ff3b8a" },
  { id: "draft_outreach", label: "DRAFT OUTREACH", c: "#7c5cff" },
  { id: "support_triage", label: "SUPPORT TRIAGE", c: "#ccff00" },
  { id: "chat", label: "CHAT REASONING", c: "#ccff00" },
];

const INDUSTRIES = [
  "freight_brokerage","logistics","manufacturing","healthcare","saas",
  "ecommerce","insurance","legal","real_estate","professional_services","general",
];

export default function PlaybookBuilder() {
  const nav = useNavigate();
  const [name, setName] = useState("");
  const [industry, setIndustry] = useState("general");
  const [description, setDescription] = useState("");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [steps, setSteps] = useState([{ kind: "extract", label: "Step 1 · Extract structured data" }]);

  const [testInput, setTestInput] = useState("");
  const [running, setRunning] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saving, setSaving] = useState(false);

  const addStep = () => setSteps([...steps, { kind: "draft_outreach", label: `Step ${steps.length + 1}` }]);
  const updateStep = (i, patch) => setSteps(steps.map((s, idx) => (idx === i ? { ...s, ...patch } : s)));
  const removeStep = (i) => setSteps(steps.filter((_, idx) => idx !== i));

  const runTest = async () => {
    if (!testInput.trim()) return toast.error("Need input text to test.");
    if (steps.length === 0) return toast.error("Add at least one step.");
    setRunning(true); setTestResult(null);
    try {
      // Save as a temporary playbook to test
      const tmpSlug = `tmp_${Date.now()}`;
      await api.post("/playbooks/customer", {
        name: `[TEST] ${name || tmpSlug}`,
        industry,
        description,
        steps,
        owner_email: ownerEmail || "anon@onejades.com",
      });
      // The endpoint generated a unique slug — fetch it
      const list = await api.get("/playbooks/by-owner", { params: { email: ownerEmail || "anon@onejades.com" } });
      const slug = list.data[0]?.slug;
      if (!slug) throw new Error("Failed to save temp playbook");
      const { data } = await api.post("/playbooks/run", { slug, input: testInput, industry, provider: "anthropic" });
      setTestResult(data);
      toast.success(`Test run · ${data.elapsed_ms}ms · ${data.steps.length} steps`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Test failed.");
    } finally { setRunning(false); }
  };

  const save = async () => {
    if (!name || !ownerEmail) return toast.error("Name + owner email required.");
    if (steps.length === 0) return toast.error("Add at least one step.");
    setSaving(true);
    try {
      const { data } = await api.post("/playbooks/customer", {
        name, industry, description, steps, owner_email: ownerEmail,
      });
      toast.success(`Saved playbook · ${data.slug}`);
      nav("/portal");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Save failed.");
    } finally { setSaving(false); }
  };

  return (
    <div className="bg-console min-h-screen">
      <section className="px-6 lg:px-10 py-12 border-b border-white/5 grid-bg-tight">
        <div className="max-w-[1400px] mx-auto">
          <button onClick={() => nav(-1)} className="mono-label text-[#00ffff] inline-flex items-center gap-2 mb-6 hover:text-[#ccff00]">
            <ArrowLeft size={12} weight="bold" /> BACK
          </button>
          <SectionLabel idx={0} color="#ccff00">PLAYBOOK BUILDER · PUBLIC</SectionLabel>
          <h1 className="font-display font-black text-white text-4xl sm:text-6xl tracking-tighter">
            Build your own <span className="accent-cyan">playbook.</span>
          </h1>
          <p className="mt-4 text-white/65 max-w-2xl text-sm">
            Chain JADE agents into a multi-step workflow. Each step's output feeds the next. Test on real data, then save it to your portal.
          </p>
        </div>
      </section>

      <section className="px-6 lg:px-10 py-12">
        <div className="max-w-[1400px] mx-auto grid lg:grid-cols-2 gap-8">
          {/* LEFT — Builder */}
          <div className="space-y-6">
            <div className="deck-card p-6 relative" data-testid="builder-meta">
              <CornerBrackets />
              <div className="mono-label text-[#00ffff] mb-4">01 · METADATA</div>
              <div className="space-y-3">
                <label className="block">
                  <span className="mono-label text-white/45 block mb-2">PLAYBOOK NAME</span>
                  <input data-testid="builder-name" className="input-tech" placeholder="My Lead Triage Playbook" value={name} onChange={(e) => setName(e.target.value)} />
                </label>
                <div className="grid sm:grid-cols-2 gap-3">
                  <label className="block">
                    <span className="mono-label text-white/45 block mb-2">INDUSTRY</span>
                    <select data-testid="builder-industry" className="input-tech" value={industry} onChange={(e) => setIndustry(e.target.value)}>
                      {INDUSTRIES.map((i) => <option key={i}>{i}</option>)}
                    </select>
                  </label>
                  <label className="block">
                    <span className="mono-label text-white/45 block mb-2">OWNER EMAIL</span>
                    <input data-testid="builder-owner" type="email" className="input-tech" placeholder="you@company.com" value={ownerEmail} onChange={(e) => setOwnerEmail(e.target.value)} />
                  </label>
                </div>
                <label className="block">
                  <span className="mono-label text-white/45 block mb-2">DESCRIPTION</span>
                  <textarea data-testid="builder-description" className="input-tech" rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
                </label>
              </div>
            </div>

            <div className="deck-card p-6 relative" data-testid="builder-steps">
              <CornerBrackets />
              <div className="flex items-center justify-between mb-4">
                <div className="mono-label text-[#ccff00]">02 · STEPS · OUTPUT FLOWS DOWN</div>
                <button data-testid="builder-add-step" onClick={addStep} className="btn-jade text-xs inline-flex items-center gap-1"><Plus size={12} weight="bold" /> ADD STEP</button>
              </div>
              <div className="space-y-3">
                {steps.map((s, i) => {
                  const k = STEP_KINDS.find((x) => x.id === s.kind);
                  return (
                    <div key={i} data-testid={`builder-step-${i}`} className="border border-white/10 p-4" style={{ borderColor: k?.c }}>
                      <div className="flex items-center justify-between mb-3">
                        <div className="mono-label" style={{ color: k?.c }}>STEP {i + 1}</div>
                        <button data-testid={`builder-step-remove-${i}`} onClick={() => removeStep(i)} className="text-[#ff3b8a] hover:text-white"><TrashSimple size={14} weight="bold" /></button>
                      </div>
                      <div className="grid sm:grid-cols-2 gap-3">
                        <select data-testid={`builder-step-kind-${i}`} className="input-tech" value={s.kind} onChange={(e) => updateStep(i, { kind: e.target.value })}>
                          {STEP_KINDS.map((x) => <option key={x.id} value={x.id}>{x.label}</option>)}
                        </select>
                        <input data-testid={`builder-step-label-${i}`} className="input-tech" placeholder="Step label" value={s.label || ""} onChange={(e) => updateStep(i, { label: e.target.value })} />
                      </div>
                    </div>
                  );
                })}
                {steps.length === 0 && <div className="font-mono-tech text-xs text-white/40">// no steps · add one to begin</div>}
              </div>
            </div>

            <div className="flex gap-3">
              <button data-testid="builder-save-btn" onClick={save} disabled={saving} className="btn-jade inline-flex items-center gap-2">
                {saving ? "SAVING…" : <>SAVE TO PORTAL <ArrowRight size={14} weight="bold" /></>}
              </button>
            </div>
          </div>

          {/* RIGHT — Test runner */}
          <div className="space-y-6">
            <div className="deck-card p-6 relative" data-testid="builder-test">
              <CornerBrackets />
              <div className="mono-label text-[#7c5cff] mb-4">03 · TEST IT · LIVE ON YOUR DATA</div>
              <label className="block">
                <span className="mono-label text-white/45 block mb-2">INPUT · TEXT THAT WILL FEED STEP 1</span>
                <textarea data-testid="builder-test-input" className="input-tech font-mono-tech text-xs" rows={10} placeholder="Paste a sample doc, ticket, lead, or transcript here…" value={testInput} onChange={(e) => setTestInput(e.target.value)} />
              </label>
              <button data-testid="builder-test-btn" onClick={runTest} disabled={running} className="btn-ghost mt-4 inline-flex items-center gap-2">
                {running ? "RUNNING…" : <>RUN TEST · LIVE <ArrowRight size={12} weight="bold" /></>}
              </button>
            </div>

            {testResult && (
              <div className="deck-card p-6 relative" data-testid="builder-test-output">
                <CornerBrackets />
                <div className="flex items-center justify-between mb-4">
                  <div className="mono-label text-[#ccff00]">TEST RESULT</div>
                  <span className="mono-label text-white/40">{testResult.elapsed_ms}ms · {testResult.steps?.length} steps</span>
                </div>
                <div className="space-y-3">
                  {testResult.steps?.map((st, i) => (
                    <div key={i} className="border border-white/10 p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="mono-label text-[#00ffff]">STEP {i + 1} · {st.kind?.toUpperCase()}</span>
                        <span className="mono-label" style={{ color: st.status === "ok" ? "#ccff00" : "#ff3b8a" }}>{st.status?.toUpperCase()}</span>
                      </div>
                      <pre className="font-mono-tech text-[10px] text-white/70 whitespace-pre-wrap leading-snug bg-[#02030a] p-3 border border-white/5 max-h-[200px] overflow-y-auto">{typeof st.output === "string" ? st.output : JSON.stringify(st.output, null, 2)}</pre>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
