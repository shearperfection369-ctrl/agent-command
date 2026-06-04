import { useState } from "react";
import { toast } from "sonner";
import { jsPDF } from "jspdf";
import { CornerBrackets, SectionLabel } from "../components/Brackets";
import { Copy, DownloadSimple, EnvelopeSimple, PhoneCall, LinkedinLogo } from "@phosphor-icons/react";

const ASSETS = {
  email_intro: {
    label: "EMAIL · UNIVERSAL COLD INTRO",
    color: "#ccff00",
    body: `Subject: 4 hours back per team member, per day

{{first_name}} — saw {{company_name}} on the {{industry_list_or_event}}. Quick ask, not a pitch.

I'm building JADE OS — AI agents that handle Tier-1 support, document extraction, lead qualification, and outbound for ops teams in {{industry}}. Two design partners are seeing 4 hours/day reclaimed per team member.

20 minutes next week to walk you through a live demo on one of your real workflows? I'll come to the office.

— {{founder_first}}, JADE OS
(612) 555-0117 · jadeos.ai`,
  },
  email_followup: {
    label: "EMAIL · FOLLOW-UP (ANY VERTICAL)",
    color: "#00ffff",
    body: `Subject: Bumping this — JADE OS demo for {{company_name}}

{{first_name}} — circling back. Pulled a public sample of your team's {{document_type_or_workflow}} and ran a quick mock: JADE would have handled 14 of them this morning before your team got coffee.

5 minutes on Friday at 2pm? I'll send a Loom showing the run if a meeting is tight.

— {{founder_first}}`,
  },
  linkedin: {
    label: "LINKEDIN · DM TO OPS DIRECTOR",
    color: "#7c5cff",
    body: `{{first_name}}, fellow MSP {{industry_short}} operator here. Built AI agents that auto-triage Tier-1 tickets, extract data from {{document_type}}, and qualify inbound leads — pre-tuned for {{industry}}. Two MSP companies piloting it now. Worth a 20-min look on Friday? — {{founder_first}}, JADE OS`,
  },
  call_script: {
    label: "CALL SCRIPT · 30s OPENER",
    color: "#ff3b8a",
    body: `{{first_name}}, this is {{founder_first}} from JADE OS in Minneapolis — not a vendor pitch, 30 seconds and I'll let you go.

I'm shipping AI agents that handle Tier-1 support tickets, parse {{vertical_document}} into structured data, and draft outbound emails — pre-tuned for {{industry}}. Two design partners are seeing 4 hours back per team member per day.

Two questions: (1) is {{primary_pain}} a real pain right now? (2) if so, can I send you a 90-second Loom showing the agent run on a real {{workflow}}?

(Stay quiet. Let them answer.)`,
  },
  one_pager: {
    label: "ONE-PAGER · UNIVERSAL LEAVE-BEHIND",
    color: "#ccff00",
    body: `JADE OS · ONE-PAGER · UNIVERSAL AI AGENTS FOR MSP

PROBLEM
Ops teams across freight, healthcare, SaaS, manufacturing, e-commerce, insurance, legal, real estate, and pro services are bleeding 2–4 hours/day per team member to manual ticket triage, data entry from PDFs/forms, lead qualification, and outbound drafting.

SOLUTION
Six AI agents — Tier-1 Support · Sales Qualification · Document Extraction · Ops Automation · Outreach · On-Call Ops Co-Pilot — pre-tuned for 10+ industries out of the box. Built on Claude Sonnet 4.5 + GPT-5.2. Human-in-the-loop approvals. Audit logs on every action.

PROOF (DESIGN PARTNERS · 90-DAY PILOT · CROSS-VERTICAL)
· Northstar Logistics (freight) — 4.2 hrs/day saved per dispatcher
· Twin Cities Health (healthcare) — 96% intake form extraction · zero rekey errors
· Bjornson SaaS (B2B SaaS) — 47% Tier-1 ticket deflection · CSAT up 18 pts

PRICING
Dispatch · $1,500/mo · 1 agent · any vertical
Fleet · $4,500/mo · 3 agents · any verticals (most popular)
Vault · Custom · unlimited + on-prem

NEXT STEP
20-minute live demo on one of YOUR real workflows. We come to the office. NDA available. Pilot at half-price for the first 5 MSP partners.

jadeos.ai · ops@jadeos.ai · (612) 555-0117`,
  },
};

const TARGET_LIST = [
  { name: "Northstar Logistics", industry: "FREIGHT", contact: "Dana Bjornson — VP Ops", channel: "Warm intro · TIA", status: "MEETING SET" },
  { name: "Allina Health · Admin Ops", industry: "HEALTHCARE", contact: "Karen Holst — Director", channel: "MN HIMSS event", status: "NURTURING" },
  { name: "Pentair · Procurement", industry: "MANUFACTURING", contact: "J. Sundberg — Sourcing Lead", channel: "LinkedIn", status: "QUEUED" },
  { name: "Bay & Bay Transportation", industry: "FREIGHT", contact: "Mark Anderson — Dir. Brokerage", channel: "LinkedIn", status: "NURTURING" },
  { name: "Code42 · Support Ops", industry: "SAAS", contact: "S. Cho — Head of Support", channel: "MSP SaaS meetup", status: "QUEUED" },
  { name: "Securian Financial", industry: "INSURANCE", contact: "via referral", channel: "Warm intro pending", status: "RESEARCH" },
  { name: "Faegre Drinker · Ops", industry: "LEGAL", contact: "M. Calhoun — COO", channel: "Cold email", status: "QUEUED" },
  { name: "Faribault Mill · DTC", industry: "E-COMMERCE", contact: "L. Bruininks — Ops Mgr", channel: "Trade show", status: "RESEARCH" },
  { name: "Cushman & Wakefield · MSP", industry: "REAL ESTATE", contact: "B. Whitman — Portfolio Lead", channel: "Referral", status: "QUEUED" },
  { name: "Best Buy · Returns Ops", industry: "RETAIL", contact: "H. Schaaf — VP CX", channel: "Cold email + LinkedIn", status: "RESEARCH" },
];

export default function LaunchKit() {
  const [copied, setCopied] = useState("");

  const copy = (key, text) => {
    navigator.clipboard.writeText(text);
    setCopied(key); setTimeout(() => setCopied(""), 1500);
    toast.success("Copied to deck.");
  };

  const downloadKit = () => {
    const doc = new jsPDF({ unit: "pt", format: "letter" });
    const margin = 54;
    const w = 612 - margin * 2;
    let y = margin;

    doc.setFillColor(2, 3, 10); doc.rect(0,0,612,792,"F");
    doc.setTextColor(204,255,0); doc.setFontSize(36); doc.setFont("helvetica","bold");
    doc.text("JADE OS · LAUNCH KIT", margin, 110);
    doc.setFontSize(10); doc.setTextColor(0,255,255);
    doc.text("OUTREACH · TARGETS · SCRIPTS · MINNEAPOLIS", margin, 132);

    y = 180;
    Object.values(ASSETS).forEach((a) => {
      if (y > 700) { doc.addPage(); doc.setFillColor(2,3,10); doc.rect(0,0,612,792,"F"); y = margin; }
      doc.setTextColor(204,255,0); doc.setFontSize(9); doc.text(a.label, margin, y); y += 16;
      doc.setTextColor(255,255,255); doc.setFontSize(10);
      const lines = doc.splitTextToSize(a.body, w);
      lines.forEach((ln) => {
        if (y > 740) { doc.addPage(); doc.setFillColor(2,3,10); doc.rect(0,0,612,792,"F"); y = margin; }
        doc.text(ln, margin, y); y += 13;
      });
      y += 18;
    });

    doc.addPage(); doc.setFillColor(2,3,10); doc.rect(0,0,612,792,"F"); y = margin;
    doc.setTextColor(204,255,0); doc.setFontSize(14); doc.text("PHASE-1 TARGET LIST · MSP · CROSS-VERTICAL", margin, y); y += 26;
    doc.setTextColor(255,255,255); doc.setFontSize(10);
    TARGET_LIST.forEach((t) => {
      const block = `▸ ${t.name} [${t.industry}]\n  ${t.contact}\n  Channel: ${t.channel} · Status: ${t.status}`;
      const lines = doc.splitTextToSize(block, w);
      lines.forEach((ln) => { doc.text(ln, margin, y); y += 13; });
      y += 6;
    });

    doc.save("JADE-OS-launch-kit.pdf");
    toast.success("Kit downloaded.");
  };

  return (
    <div className="bg-console min-h-screen">
      <section className="relative px-6 lg:px-10 py-16 lg:py-24 grid-bg-tight border-b border-white/5">
        <div className="max-w-[1400px] mx-auto">
          <SectionLabel idx={0} color="#00ffff">LAUNCH KIT · GO-TO-MARKET DECK</SectionLabel>
          <div className="grid lg:grid-cols-3 gap-10 items-end">
            <div className="lg:col-span-2">
              <h1 className="font-display font-black text-white text-5xl sm:text-7xl tracking-tighter glow-cyan">
                The launch<br />
                <span className="accent-cyan">tape.</span>
              </h1>
              <p className="mt-6 text-white/65 max-w-2xl leading-relaxed">
                Copy-ready outreach, a Minneapolis target list, scripts, and a leave-behind one-pager. Print the kit. Run the plays. Drop in your name and ship.
              </p>
            </div>
            <button data-testid="launch-download-btn" onClick={downloadKit} className="btn-jade inline-flex items-center justify-center gap-2">
              <DownloadSimple size={16} weight="bold" /> DOWNLOAD KIT
            </button>
          </div>
        </div>
      </section>

      <section className="px-6 lg:px-10 py-16">
        <div className="max-w-[1400px] mx-auto space-y-10">
          {/* Outreach assets */}
          <div>
            <SectionLabel idx={1} color="#ccff00">OUTREACH ASSETS</SectionLabel>
            <div className="grid lg:grid-cols-2 gap-5">
              {Object.entries(ASSETS).map(([k, a]) => (
                <div key={k} data-testid={`asset-${k}`} className="deck-card p-7 relative">
                  <CornerBrackets />
                  <div className="flex items-center justify-between mb-4">
                    <span className="mono-label" style={{ color: a.color }}>{a.label}</span>
                    <button data-testid={`copy-${k}`} onClick={() => copy(k, a.body)} className="mono-label text-white/60 hover:text-[#00ffff] inline-flex items-center gap-1">
                      <Copy size={12} weight="bold" /> {copied === k ? "COPIED" : "COPY"}
                    </button>
                  </div>
                  <pre className="text-sm text-white/80 whitespace-pre-wrap font-sans leading-relaxed">{a.body}</pre>
                </div>
              ))}
            </div>
          </div>

          {/* Target accounts */}
          <div>
            <SectionLabel idx={2} color="#7c5cff">PHASE-1 TARGET LIST · MSP · CROSS-VERTICAL</SectionLabel>
            <div className="deck-card relative" data-testid="target-list-table">
              <CornerBrackets />
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/10">
                    {["COMPANY","INDUSTRY","CONTACT","CHANNEL","STATUS"].map((h) => (
                      <th key={h} className="text-left mono-label text-white/40 p-4">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {TARGET_LIST.map((t, i) => (
                    <tr key={i} data-testid={`target-row-${i}`} className="border-b border-white/5 hover:bg-white/[0.02]">
                      <td className="p-4 font-display text-white font-bold">{t.name}</td>
                      <td className="p-4 mono-label text-[#ccff00]">{t.industry}</td>
                      <td className="p-4 text-white/70 font-mono-tech text-xs">{t.contact}</td>
                      <td className="p-4 text-white/70 font-mono-tech text-xs">{t.channel}</td>
                      <td className="p-4">
                        <span className="mono-label" style={{
                          color: t.status === "MEETING SET" ? "#ccff00" : t.status === "NURTURING" ? "#00ffff" : t.status === "RESEARCH" ? "#7c5cff" : "#ff3b8a"
                        }}>{t.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Channels card */}
          <div>
            <SectionLabel idx={3} color="#ff3b8a">CHANNELS · ORDER OF OPERATIONS</SectionLabel>
            <div className="grid md:grid-cols-3 gap-5">
              <ChannelCard icon={EnvelopeSimple} c="#ccff00" t="EMAIL · WEEK 1-2" b="50 cold emails to MC-authority brokers in MN/WI/IA. Personalize line 1 only. CTA: 20-min demo." />
              <ChannelCard icon={LinkedinLogo} c="#00ffff" t="LINKEDIN · WEEK 2-3" b="Connect with Ops Directors at the top-50 MSP brokers. Soft-touch DM. Comment on freight market posts." />
              <ChannelCard icon={PhoneCall} c="#7c5cff" t="IN-PERSON · WEEK 3-4" b="TIA chapter meetings, MN Trucking Association events, drop-in visits to brokers within 30 minutes of MSP." />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function ChannelCard({ icon: Icon, c, t, b }) {
  return (
    <div className="deck-card p-7 relative">
      <CornerBrackets />
      <Icon size={28} weight="bold" style={{ color: c }} />
      <div className="mono-label mt-4" style={{ color: c }}>{t}</div>
      <p className="text-sm text-white/70 mt-3 leading-relaxed">{b}</p>
    </div>
  );
}
