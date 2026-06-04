import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Link } from "react-router-dom";
import { CornerBrackets, SectionLabel } from "../components/Brackets";
import { api, API_BASE } from "../lib/api";
import { Play, Pause, ArrowsClockwise, ArrowRight, SkipForward, ArrowClockwise } from "@/lib/icons";

/**
 * Demo Reel — plays through 5 hand-curated company problems end-to-end.
 * Each scene streams the LLM response so the user sees JADE actually working.
 */
const SCENES = [
  {
    id: 1, industry: "freight_brokerage", color: "#ccff00",
    company: "NORTHSTAR LOGISTICS",
    role: "Dispatcher",
    title: "BOL parse + carrier outreach in 8 seconds.",
    problem: "Dispatcher pastes a load posting at 7:42am. Today: 22-minute manual data entry + email draft. With JADE: paste → structured load → carrier-ready email.",
    steps: [
      {
        kind: "extract",
        label: "EXTRACT BOL",
        input: `LOAD ID: 88421-MN
Pickup: 02/15 08:00-12:00, Eagan, MN 55121
Delivery: 02/16 14:00-18:00, Joliet, IL 60432
Equipment: 53' Reefer, 38,000 lbs, Temp 34F
Commodity: General Mills frozen breakfast
Miles: 482
Rate: $1,950 ALL-IN
MC 654321 · Dana B. · (612) 555-0117`,
      },
      {
        kind: "outreach",
        label: "DRAFT CARRIER OUTREACH",
        recipient: "Bay & Bay Transportation",
        summary: "53' reefer, Eagan MN→Joliet IL, pickup 02/15, $1,950 ALL-IN, drop & hook, MC 654321",
      },
    ],
  },
  {
    id: 2, industry: "healthcare", color: "#7c5cff",
    company: "TWIN CITIES HEALTH",
    role: "Front-Desk Admin",
    title: "Patient intake form → EMR-ready JSON.",
    problem: "Front desk keys 450 forms/day at 9 minutes each. JADE parses intake + redacts PHI in logs in seconds.",
    steps: [
      {
        kind: "extract",
        label: "PARSE INTAKE FORM",
        input: `Patient Intake Form
Name: J. Sample
DOB: 1971-04-22
Insurer: BlueCross MN — Member ID 8842XXXX
Visit: 02/12, Dr. Patel, Allina Clinic
Reason: chest pain follow-up
Prior auth: PA-2024-0911, status APPROVED
CPT planned: 93306, 93000`,
      },
      {
        kind: "support",
        label: "TRIAGE A PATIENT INQUIRY",
        ticket: "Patient called 3 times today angry — denied MRI, says scheduler told her it would be covered. Spoke to Cigna Friday.",
      },
    ],
  },
  {
    id: 3, industry: "saas", color: "#00ffff",
    company: "BJORNSON SAAS",
    role: "Support Lead",
    title: "Tier-1 ticket → triaged + draft response.",
    problem: "Support gets 100+ tickets/day. 60% are FAQ-able. JADE classifies, prioritizes, drafts a first response, flags escalation.",
    steps: [
      {
        kind: "support",
        label: "TRIAGE TICKET",
        ticket: "Customer says they're being charged for 250 seats but only have 180 active users. CSV attached showing last 30 days. Asking for refund AND threatening to switch to Zendesk.",
      },
      {
        kind: "outreach",
        label: "DRAFT EXPANSION FOLLOWUP",
        recipient: "K. Chen, VP Eng at Acme Inc.",
        summary: "Acme Inc., 250-seat enterprise renewal in 30 days. Usage up 40% YoY. Propose 12-month renewal with 8% increase + premium SLA.",
      },
    ],
  },
  {
    id: 4, industry: "manufacturing", color: "#ff3b8a",
    company: "PENTAIR · PROCUREMENT",
    role: "Buyer",
    title: "PO extraction + vendor follow-up in one breath.",
    problem: "Procurement has 200+ POs/week across 40 vendors. JADE pulls fields and drafts the late-vendor escalation.",
    steps: [
      {
        kind: "extract",
        label: "PARSE PURCHASE ORDER",
        input: `Purchase Order #PO-44218
Vendor: Acme Steel Supply
Items:
  - 250x Bar Stock 1018 CRS 1/2" — $4.20/ea
  - 100x Plate 304 SS 1/4" 4x8 — $185.00/ea
Total: $19,550.00
Required by: 03/04
Buyer: J. Sundberg, Pentair MN
Terms: Net 30`,
      },
      {
        kind: "outreach",
        label: "DRAFT LATE-VENDOR ESCALATION",
        recipient: "Acme Steel Supply",
        summary: "PO #PO-44218 is 5 business days past due. Need updated ship date. Production line down by Friday if not received.",
      },
    ],
  },
  {
    id: 5, industry: "real_estate", color: "#ccff00",
    company: "CUSHMAN & WAKEFIELD MSP",
    role: "Property Manager",
    title: "After-hours maintenance triage.",
    problem: "Property mgmt fields ~30 after-hours tickets/week. JADE triages, sets priority, drafts the tenant response, escalates if it's a P0.",
    steps: [
      {
        kind: "support",
        label: "TRIAGE MAINTENANCE TICKET",
        ticket: "Tenant in Unit 412 — water leaking from ceiling, coming through the light fixture. Reported 11:42pm Friday. Has small kids in unit.",
      },
      {
        kind: "outreach",
        label: "DRAFT TENANT RESPONSE",
        recipient: "Riverline Coffee LLC (Unit 412)",
        summary: "Acknowledge after-hours water leak in Unit 412. Confirm emergency plumber dispatched. Provide 30-min ETA window. Reassure on safety.",
      },
    ],
  },
];

const PHASES = ["IDLE", "RUNNING", "DONE"];

export default function DemoReel() {
  const [sceneIdx, setSceneIdx] = useState(0);
  const [stepIdx, setStepIdx] = useState(0);
  const [phase, setPhase] = useState("IDLE");
  const [outputs, setOutputs] = useState({}); // {sceneIdx-stepIdx: text}
  const [autoplay, setAutoplay] = useState(true);
  const cancelRef = useRef(false);

  const scene = SCENES[sceneIdx];
  const safeStepIdx = Math.min(stepIdx, scene.steps.length - 1);
  const step = scene.steps[safeStepIdx];
  const outputKey = `${sceneIdx}-${safeStepIdx}`;
  const output = outputs[outputKey] || "";

  useEffect(() => {
    cancelRef.current = false;
    // Always normalize stepIdx when scene changes
    if (stepIdx >= scene.steps.length) {
      setStepIdx(0);
      return;
    }
    if (!autoplay) return;
    runStep();
    return () => { cancelRef.current = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sceneIdx, stepIdx]);

  const setOut = (txt) => setOutputs((m) => ({ ...m, [outputKey]: txt }));

  const runStep = async () => {
    if (!step) return;
    setPhase("RUNNING");
    setOut("");
    try {
      if (step.kind === "extract") {
        const { data } = await api.post("/agent/extract", { text: step.input, industry: scene.industry, provider: "anthropic" });
        if (cancelRef.current) return;
        setOut(JSON.stringify(data.extracted, null, 2));
      } else if (step.kind === "outreach") {
        const { data } = await api.post("/agent/draft-outreach", {
          recipient: step.recipient, summary: step.summary, industry: scene.industry, provider: "anthropic", tone: "direct",
        });
        if (cancelRef.current) return;
        setOut(data.email);
      } else if (step.kind === "support") {
        const { data } = await api.post("/agent/support-triage", { ticket: step.ticket, industry: scene.industry, provider: "anthropic" });
        if (cancelRef.current) return;
        setOut(JSON.stringify(data.result, null, 2));
      }
      if (cancelRef.current) return;
      setPhase("DONE");
      if (autoplay) {
        // Snapshot the current scene/step at fire-time of the timer so we don't advance
        // a NEW scene that the user may have clicked into during the delay.
        const sceneAtSchedule = sceneIdx;
        const stepAtSchedule = safeStepIdx;
        setTimeout(() => {
          if (cancelRef.current) return;
          if (sceneAtSchedule !== sceneIdx || stepAtSchedule !== safeStepIdx) return; // stale timer
          if (stepAtSchedule + 1 < scene.steps.length) {
            setStepIdx(stepAtSchedule + 1);
          } else if (sceneAtSchedule + 1 < SCENES.length) {
            setSceneIdx(sceneAtSchedule + 1);
            setStepIdx(0);
          } else {
            setAutoplay(false);
          }
        }, 2500);
      }
    } catch (e) {
      toast.error("Demo step failed");
      setPhase("IDLE");
    }
  };

  const skipScene = () => {
    cancelRef.current = true;
    if (sceneIdx + 1 < SCENES.length) {
      setSceneIdx((x) => x + 1);
      setStepIdx(0);
      setPhase("IDLE");
    }
  };

  const replay = () => {
    cancelRef.current = true;
    setSceneIdx(0);
    setStepIdx(0);
    setOutputs({});
    setPhase("IDLE");
    setAutoplay(true);
  };

  return (
    <div className="bg-console min-h-screen">
      {/* HEADER */}
      <section className="px-6 lg:px-10 py-10 border-b border-white/5 grid-bg-tight">
        <div className="max-w-[1400px] mx-auto">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <SectionLabel idx={0} color="#00ffff">DEMO REEL · LIVE</SectionLabel>
              <h1 className="font-display font-black text-white text-4xl sm:text-6xl tracking-tighter">
                JADE on the <span className="accent-cyan">job.</span>
              </h1>
              <p className="mt-3 text-white/65 max-w-2xl text-sm">
                Five real company problems. JADE handles each one live, in front of you. No prompt engineering. No mocks.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button data-testid="reel-embed-btn" onClick={() => {
                const code = `<iframe src="${window.location.origin}/embed/reel?industry=${scene.industry}&scene=${sceneIdx}" width="100%" height="520" style="border:0;border-radius:0"></iframe>`;
                navigator.clipboard.writeText(code);
                toast.success("Embed snippet copied — paste into any site");
              }} className="btn-ghost text-xs inline-flex items-center gap-2">
                ⧉ COPY EMBED
              </button>
              <button data-testid="reel-autoplay-btn" onClick={() => setAutoplay((x) => !x)} className="btn-ghost text-xs inline-flex items-center gap-2">
                {autoplay ? <><Pause size={14} weight="bold" /> PAUSE</> : <><Play size={14} weight="bold" /> AUTOPLAY</>}
              </button>
              <button data-testid="reel-skip-btn" onClick={skipScene} className="btn-ghost text-xs inline-flex items-center gap-2">
                <SkipForward size={14} weight="bold" /> SKIP SCENE
              </button>
              <button data-testid="reel-replay-btn" onClick={replay} className="btn-jade text-xs inline-flex items-center gap-2">
                <ArrowClockwise size={14} weight="bold" /> REPLAY ALL
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* SCENE STAGE */}
      <section className="px-6 lg:px-10 py-10">
        <div className="max-w-[1400px] mx-auto grid lg:grid-cols-12 gap-6">
          {/* LEFT — scene index */}
          <aside className="lg:col-span-3 space-y-2" data-testid="reel-sidebar">
            <div className="mono-label text-white/45 mb-3">SCENE LIST · {sceneIdx + 1} / {SCENES.length}</div>
            {SCENES.map((s, i) => (
              <button
                key={s.id}
                data-testid={`reel-scene-${i}`}
                onClick={() => { cancelRef.current = true; setSceneIdx(i); setStepIdx(0); setPhase("IDLE"); }}
                className="block w-full text-left p-4 border transition"
                style={{
                  borderColor: i === sceneIdx ? s.color : "rgba(255,255,255,0.08)",
                  background: i === sceneIdx ? "#0a0c18" : "#02030a",
                }}
              >
                <div className="mono-label" style={{ color: s.color }}>0{i + 1} · {s.industry.replace("_", " ").toUpperCase()}</div>
                <div className="font-display font-bold text-white text-sm mt-2 leading-tight">{s.company}</div>
                <div className="font-mono-tech text-[10px] text-white/50 mt-1">{s.role}</div>
              </button>
            ))}
          </aside>

          {/* CENTER — stage */}
          <main className="lg:col-span-9 deck-card relative" data-testid="reel-stage">
            <CornerBrackets />
            {/* Scene meta */}
            <div className="p-7 border-b border-white/5">
              <div className="flex flex-wrap items-center gap-3 mb-4">
                <span className="chip" style={{ borderColor: scene.color, color: scene.color, background: `${scene.color}11` }}>
                  SCENE {sceneIdx + 1}
                </span>
                <span className="chip chip-cyan">{scene.industry.replace("_", " ").toUpperCase()}</span>
                <span className="chip chip-violet">{scene.company}</span>
              </div>
              <h2 className="font-display font-bold text-white text-2xl sm:text-3xl tracking-tight leading-tight">{scene.title}</h2>
              <p className="text-sm text-white/65 mt-3 max-w-3xl leading-relaxed">{scene.problem}</p>
            </div>

            {/* Step tracker */}
            <div className="px-7 py-4 border-b border-white/5 flex items-center gap-3">
              {scene.steps.map((st, i) => (
                <div key={i} className={`flex-1 p-3 border ${i === safeStepIdx ? "" : "opacity-50"}`}
                  style={{ borderColor: i === safeStepIdx ? scene.color : "rgba(255,255,255,0.08)" }}>
                  <div className="mono-label" style={{ color: i === safeStepIdx ? scene.color : "rgba(255,255,255,0.4)" }}>
                    STEP {String(i + 1).padStart(2, "0")} · {st.label}
                  </div>
                </div>
              ))}
              <div className="px-3 py-3 border" style={{
                borderColor: phase === "RUNNING" ? scene.color : "rgba(255,255,255,0.08)",
              }}>
                <span className="mono-label" style={{ color: phase === "RUNNING" ? scene.color : "rgba(255,255,255,0.4)" }}>
                  {phase === "RUNNING" && <span className="dot mr-2" />}{phase}
                </span>
              </div>
            </div>

            {/* Two panels */}
            <div className="grid lg:grid-cols-2 divide-x divide-white/5">
              <div className="p-7">
                <div className="mono-label text-[#7c5cff] mb-3">INPUT · {step.label}</div>
                <pre className="font-mono-tech text-[11px] text-white/75 whitespace-pre-wrap leading-relaxed bg-[#02030a] p-4 border border-white/5 max-h-[420px] overflow-y-auto">
                  {step.kind === "extract" && step.input}
                  {step.kind === "outreach" && `RECIPIENT: ${step.recipient}\n\nCONTEXT:\n${step.summary}`}
                  {step.kind === "support" && step.ticket}
                </pre>
                <div className="mt-4 flex gap-3">
                  {!autoplay && phase !== "RUNNING" && (
                    <button data-testid="reel-run-step-btn" onClick={runStep} className="btn-jade text-xs inline-flex items-center gap-2">
                      RUN STEP <ArrowRight size={12} weight="bold" />
                    </button>
                  )}
                </div>
              </div>
              <div className="p-7">
                <div className="mono-label text-[#ccff00] mb-3">OUTPUT · JADE</div>
                {phase === "RUNNING" && !output && (
                  <div className="font-mono-tech text-xs text-[#ccff00] animate-pulse">// JADE is working… <span className="dot ml-2" /></div>
                )}
                {output && (
                  <pre data-testid="reel-output" className="font-mono-tech text-[11px] text-white/85 whitespace-pre-wrap leading-relaxed bg-[#02030a] p-4 border border-[#ccff00]/30 max-h-[420px] overflow-y-auto">{output}</pre>
                )}
                {!output && phase === "IDLE" && <div className="font-mono-tech text-xs text-white/40">// awaiting…</div>}
              </div>
            </div>

            {/* Footer CTA */}
            <div className="p-7 border-t border-white/5 flex flex-wrap items-center justify-between gap-4">
              <div className="mono-label text-white/35">SCENE {sceneIdx + 1} / {SCENES.length} · STEP {safeStepIdx + 1} / {scene.steps.length}</div>
              <div className="flex gap-2">
                <Link to="/demo" className="btn-ghost text-xs">OPEN FULL CONSOLE</Link>
                <Link to="/#book" className="btn-jade text-xs inline-flex items-center gap-2">BOOK A DEMO <ArrowRight size={12} weight="bold" /></Link>
              </div>
            </div>
          </main>
        </div>
      </section>
    </div>
  );
}
