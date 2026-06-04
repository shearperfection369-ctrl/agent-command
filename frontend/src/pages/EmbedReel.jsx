import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../lib/api";

/**
 * Stripped-down embeddable demo reel. Renders a single scene at a time,
 * meant to be loaded via <iframe src="/embed/reel?industry=freight_brokerage&scene=0">.
 * No nav/footer chrome.
 */
const SCENES = [
  { industry: "freight_brokerage", company: "NORTHSTAR LOGISTICS", title: "BOL parse → carrier outreach in 8 seconds.", color: "#ccff00",
    input: "LOAD 88421 Eagan MN → Joliet IL 53 reefer 38000lbs pickup 02/15 $1,950 ALL-IN MC 654321" },
  { industry: "healthcare", company: "TWIN CITIES HEALTH", title: "Patient intake → EMR-ready JSON.", color: "#7c5cff",
    input: "Patient J. Sample DOB 1971-04-22 BlueCross 8842XXXX Allina Clinic Dr. Patel chest pain follow-up CPT 93306" },
  { industry: "saas", company: "BJORNSON SAAS", title: "Tier-1 ticket → triaged + draft response.", color: "#00ffff",
    input: "Customer charged for 250 seats but only 180 active users. CSV attached. Asking for refund." },
  { industry: "manufacturing", company: "PENTAIR · PROCUREMENT", title: "PO extraction → vendor follow-up.", color: "#ff3b8a",
    input: "PO #PO-44218 Vendor Acme Steel 250x Bar Stock 1018 CRS 1/2 $4.20/ea Total $19,550 due 03/04" },
  { industry: "real_estate", company: "CUSHMAN & WAKEFIELD MSP", title: "After-hours maintenance triage.", color: "#ccff00",
    input: "Tenant Unit 412 — water leaking from ceiling, coming through light fixture. 11:42pm Friday." },
];

export default function EmbedReel() {
  const [sp] = useSearchParams();
  const startScene = parseInt(sp.get("scene") || "0", 10);
  const filter = sp.get("industry");

  const filtered = filter ? SCENES.filter((s) => s.industry === filter) : SCENES;
  const list = filtered.length ? filtered : SCENES;

  const [i, setI] = useState(Math.max(0, Math.min(list.length - 1, startScene)));
  const [phase, setPhase] = useState("IDLE");
  const [output, setOutput] = useState("");
  const scene = list[i];

  const run = async () => {
    setPhase("RUNNING"); setOutput("");
    try {
      const { data } = await api.post("/agent/extract", { text: scene.input, industry: scene.industry, provider: "anthropic" });
      setOutput(JSON.stringify(data.extracted, null, 2));
      setPhase("DONE");
      setTimeout(() => {
        if (i + 1 < list.length) { setI(i + 1); setPhase("IDLE"); setOutput(""); }
      }, 6000);
    } catch (e) { setPhase("IDLE"); }
  };

  useEffect(() => { run(); /* autoplay */ /* eslint-disable-next-line */ }, [i]);

  return (
    <div className="min-h-screen bg-[#02030a] text-white p-4">
      <div className="border border-white/10 bg-[#06081a] p-5 max-w-full">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="font-mono-tech text-[10px] tracking-[0.3em] text-[#ccff00]">JADE OS · LIVE</span>
            <span className="dot" />
          </div>
          <span className="font-mono-tech text-[10px] tracking-[0.3em] text-white/40">SCENE {i + 1}/{list.length} · {scene.industry.replace("_", " ").toUpperCase()}</span>
        </div>
        <h2 className="font-display font-bold text-white text-xl leading-tight" style={{ color: scene.color }}>{scene.company}</h2>
        <p className="text-sm text-white/80 mt-1">{scene.title}</p>
        <div className="mt-4 grid sm:grid-cols-2 gap-3">
          <div>
            <div className="font-mono-tech text-[9px] tracking-[0.3em] text-[#7c5cff] mb-2">INPUT</div>
            <pre className="font-mono-tech text-[10px] text-white/70 whitespace-pre-wrap bg-[#02030a] p-2 border border-white/5 max-h-[180px] overflow-y-auto">{scene.input}</pre>
          </div>
          <div>
            <div className="font-mono-tech text-[9px] tracking-[0.3em] text-[#ccff00] mb-2">OUTPUT · {phase}</div>
            {!output && phase === "RUNNING" && <div className="font-mono-tech text-[10px] text-[#ccff00] animate-pulse">// JADE working… <span className="dot ml-1" /></div>}
            {output && <pre className="font-mono-tech text-[10px] text-white/85 whitespace-pre-wrap bg-[#02030a] p-2 border border-[#ccff00]/30 max-h-[180px] overflow-y-auto">{output}</pre>}
          </div>
        </div>
        <div className="mt-3 text-center">
          <a href="https://jadeos.ai" target="_blank" rel="noreferrer" className="font-mono-tech text-[9px] tracking-[0.3em] text-[#00ffff] hover:text-[#ccff00]">▶ POWERED BY JADE OS · TRY IT</a>
        </div>
      </div>
    </div>
  );
}
