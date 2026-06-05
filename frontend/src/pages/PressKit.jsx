import { useState } from "react";
import { Link } from "react-router-dom";
import { CornerBrackets } from "../components/Brackets";
import { toast } from "sonner";

const ASSETS = {
  workspace: "https://customer-assets.emergentagent.com/job_mpls-automation-hub/artifacts/cghzdrkp_jade%20ultra%20image.png",
  quanta: "https://customer-assets.emergentagent.com/job_mpls-automation-hub/artifacts/7atwkaoe_quanta-1779558560741.png",
  banner: "https://customer-assets.emergentagent.com/job_mpls-automation-hub/artifacts/fahm9un7_banner-970x260.png",
  voice: "https://customer-assets.emergentagent.com/job_mpls-automation-hub/artifacts/jlqa2gtk_09-jade-survival-codex.mp3",
};

const COLORS = [
  { name: "Jade Lime", hex: "#ccff00", role: "Primary action · brand accent · highlights" },
  { name: "Quantum Cyan", hex: "#00ffff", role: "Secondary signal · live state · data" },
  { name: "Vault Violet", hex: "#7c5cff", role: "Tertiary · governance · system events" },
  { name: "Console Black", hex: "#04050d", role: "Background · neutral · negative space" },
  { name: "Crimson Pulse", hex: "#ff3b8a", role: "Critical · escalations · attention" },
];

const FACTS = [
  { k: "Founded", v: "2025 · Minneapolis-St. Paul" },
  { k: "Founder", v: "Oliver Cummins" },
  { k: "Category", v: "AI agent platform for ops teams" },
  { k: "Stack", v: "Claude Sonnet 4.5 · GPT-5.2 · MongoDB · FastAPI · React" },
  { k: "Industries", v: "11 (Freight, Healthcare, SaaS, Manufacturing, Legal, E-comm, Insurance, Real Estate, Logistics, Professional Services, General)" },
  { k: "Pricing", v: "$750 Lighthouse pilots · $1.5k-$4.5k/mo subscriptions" },
];

const ONE_LINERS = [
  "JADE OS is the AI-agent platform for Minneapolis ops teams drowning in inbox, docs, tickets, and lead work.",
  "Six industry-trained agents — chat, extract, qualify, triage, draft outreach, run multi-step playbooks — operator-grade, your data stays in your tenant.",
  "Built by an operator for operators. The system fires while you sleep.",
];

export default function PressKit() {
  const copy = (text, label) => {
    navigator.clipboard.writeText(text).then(
      () => toast.success(`${label} copied`),
      () => toast.error("Clipboard blocked")
    );
  };

  return (
    <div className="bg-[#04050d] text-white min-h-screen">
      {/* Hero */}
      <section className="border-b border-white/10 relative overflow-hidden">
        <div className="absolute inset-0 grid-bg pointer-events-none" />
        <div className="absolute inset-0 scanlines pointer-events-none" />
        <div className="max-w-7xl mx-auto px-6 py-20 relative">
          <div className="mono-label text-[#ccff00] mb-4">01 · PRESS · MARKETING PACK</div>
          <h1 className="font-display font-black tracking-tighter text-white leading-none"
              style={{ fontSize: "clamp(3rem, 8vw, 7rem)" }}
              data-testid="press-headline">
            Press kit<span className="text-[#ccff00]">.</span>
          </h1>
          <p className="text-white/65 max-w-2xl mt-6 leading-relaxed text-lg">
            Everything press, partners, and prospects need to talk about JADE OS — Genesis portrait,
            the Quanta hardware, brand palette, voice, key facts, founder bio, and one-liners.
            Click anything to copy. Right-click any asset to save.
          </p>
        </div>
      </section>

      {/* Brand assets grid */}
      <section className="max-w-7xl mx-auto px-6 py-20 border-t border-white/10" data-testid="press-assets">
        <div className="mono-label text-[#7c5cff] mb-3">02 · BRAND ASSETS · DOWNLOAD</div>
        <h2 className="font-display font-black tracking-tight text-white mb-10"
            style={{ fontSize: "clamp(2rem, 4vw, 3.5rem)" }}>
          Logos, hardware, banners.
        </h2>
        <div className="grid sm:grid-cols-2 gap-6">
          <AssetTile testid="asset-workspace" name="JADE OS Workstation" desc="Hero product shot · laptop + monitor running the console · staged photography" url={ASSETS.workspace} />
          <AssetTile testid="asset-quanta" name="Quanta Keychain" desc="Hardware companion · lime-LED edges · holographic projection" url={ASSETS.quanta} />
          <AssetTile testid="asset-banner" name="Web Banner · 970×260" desc="Leaderboard ad unit · cross-platform · ready for socials + display" url={ASSETS.banner} />
        </div>
      </section>

      {/* Brand palette */}
      <section className="max-w-7xl mx-auto px-6 py-20 border-t border-white/10" data-testid="press-palette">
        <div className="mono-label text-[#ff3b8a] mb-3">03 · BRAND PALETTE</div>
        <h2 className="font-display font-black tracking-tight text-white mb-10"
            style={{ fontSize: "clamp(2rem, 4vw, 3.5rem)" }}>
          Five colors, one console.
        </h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {COLORS.map((c) => (
            <button
              key={c.hex}
              onClick={() => copy(c.hex, c.name + " hex")}
              className="text-left group"
              data-testid={`palette-${c.hex.replace('#', '')}`}
            >
              <div
                className="w-full aspect-square border border-white/10 group-hover:border-white/40 transition"
                style={{ background: c.hex }}
              />
              <div className="mt-3">
                <div className="font-display font-bold text-white">{c.name}</div>
                <div className="font-mono-tech text-[11px] text-white/55 mt-1">{c.hex}</div>
                <div className="text-[11px] text-white/45 mt-1 leading-relaxed">{c.role}</div>
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* Voice */}
      <section className="max-w-7xl mx-auto px-6 py-20 border-t border-white/10" data-testid="press-voice">
        <div className="mono-label text-[#ccff00] mb-3">04 · OFFICIAL VOICE</div>
        <h2 className="font-display font-black tracking-tight text-white mb-10"
            style={{ fontSize: "clamp(2rem, 4vw, 3.5rem)" }}>
          This is what Jade sounds like.
        </h2>
        <div className="deck-card p-8 relative max-w-3xl">
          <CornerBrackets />
          <audio controls preload="metadata" className="w-full" data-testid="press-voice-audio">
            <source src={ASSETS.voice} type="audio/mpeg" />
          </audio>
          <p className="text-white/65 text-sm mt-4 italic leading-relaxed">
            "Hello, I'm Jade. Welcome to the JADE OS audio library…" — 4:36 narration sample.
            High-quality TTS, female, North-American, confident operator-grade tone.
          </p>
        </div>
      </section>

      {/* Demo reel */}
      <section className="max-w-7xl mx-auto px-6 py-20 border-t border-white/10" data-testid="press-reel">
        <div className="mono-label text-[#00ffff] mb-3">05 · PROMOTIONAL REEL</div>
        <h2 className="font-display font-black tracking-tight text-white mb-10"
            style={{ fontSize: "clamp(2rem, 4vw, 3.5rem)" }}>
          12 seconds. The pitch.
        </h2>
        <div className="deck-card relative overflow-hidden max-w-4xl">
          <CornerBrackets />
          <video
            controls
            playsInline
            preload="metadata"
            className="w-full block bg-black"
            data-testid="press-reel-video"
            src={`${process.env.REACT_APP_BACKEND_URL || ""}/api/promo/video`}
          />
        </div>
        <div className="mt-4 flex gap-3 flex-wrap">
          <a
            href={`${process.env.REACT_APP_BACKEND_URL || ""}/api/promo/video`}
            download="jadeos_promo.mp4"
            className="btn-jade inline-flex items-center gap-2"
            data-testid="press-reel-download"
          >
            DOWNLOAD MP4
          </a>
          <Link to="/reel" className="btn-ghost inline-flex items-center gap-2">
            VIEW EMBEDDED VERSION
          </Link>
        </div>
      </section>

      {/* Facts */}
      <section className="max-w-7xl mx-auto px-6 py-20 border-t border-white/10" data-testid="press-facts">
        <div className="mono-label text-[#7c5cff] mb-3">06 · KEY FACTS</div>
        <h2 className="font-display font-black tracking-tight text-white mb-10"
            style={{ fontSize: "clamp(2rem, 4vw, 3.5rem)" }}>
          Numbers, names, dates.
        </h2>
        <div className="grid sm:grid-cols-2 gap-4">
          {FACTS.map((f) => (
            <div key={f.k} className="deck-card p-5 relative" data-testid={`fact-${f.k.toLowerCase().replace(/\s+/g, '-')}`}>
              <CornerBrackets />
              <div className="mono-label text-[10px] text-white/45 mb-2">{f.k}</div>
              <div className="text-white font-display font-bold leading-snug">{f.v}</div>
            </div>
          ))}
        </div>
      </section>

      {/* One-liners */}
      <section className="max-w-7xl mx-auto px-6 py-20 border-t border-white/10" data-testid="press-oneliners">
        <div className="mono-label text-[#ff3b8a] mb-3">07 · APPROVED ONE-LINERS</div>
        <h2 className="font-display font-black tracking-tight text-white mb-10"
            style={{ fontSize: "clamp(2rem, 4vw, 3.5rem)" }}>
          Drop these straight into your story.
        </h2>
        <div className="space-y-3">
          {ONE_LINERS.map((line, i) => (
            <button
              key={i}
              onClick={() => copy(line, "One-liner")}
              className="deck-card p-6 relative w-full text-left group hover:bg-white/[0.02] transition"
              data-testid={`oneliner-${i}`}
            >
              <CornerBrackets />
              <div className="flex items-start gap-4">
                <span className="mono-label text-[#ccff00] text-[11px] mt-1">0{i + 1}</span>
                <p className="text-white text-lg leading-relaxed flex-1">"{line}"</p>
                <span className="mono-label text-white/30 group-hover:text-[#ccff00] transition text-[10px]">COPY</span>
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* Contact */}
      <section className="max-w-7xl mx-auto px-6 py-20 border-t border-white/10" data-testid="press-contact">
        <div className="mono-label text-[#00ffff] mb-3">08 · CONTACT</div>
        <h2 className="font-display font-black tracking-tight text-white mb-10"
            style={{ fontSize: "clamp(2rem, 4vw, 3.5rem)" }}>
          Coverage requests welcome.
        </h2>
        <div className="deck-card p-8 relative max-w-2xl">
          <CornerBrackets />
          <div className="space-y-4">
            <div>
              <div className="mono-label text-[10px] text-white/45">FOUNDER</div>
              <div className="text-white font-display font-bold text-2xl mt-1">Oliver Cummins</div>
            </div>
            <div>
              <div className="mono-label text-[10px] text-white/45">EMAIL</div>
              <a href="mailto:cummins_oliver@yahoo.com" className="text-[#ccff00] font-mono-tech mt-1 inline-block">cummins_oliver@yahoo.com</a>
            </div>
            <div>
              <div className="mono-label text-[10px] text-white/45">WEB</div>
              <a href="https://onejades.com" className="text-[#ccff00] font-mono-tech mt-1 inline-block">onejades.com</a>
            </div>
            <div>
              <div className="mono-label text-[10px] text-white/45">REGION</div>
              <div className="text-white/85 font-mono-tech mt-1">Minneapolis-St. Paul, MN</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function AssetTile({ name, desc, url, testid }) {
  return (
    <div className="deck-card relative overflow-hidden group" data-testid={testid}>
      <CornerBrackets />
      <div className="aspect-[4/3] bg-black/40 flex items-center justify-center overflow-hidden">
        <img
          src={url}
          alt={name}
          loading="lazy"
          className="max-w-full max-h-full object-contain group-hover:scale-105 transition-transform duration-500"
        />
      </div>
      <div className="p-5 border-t border-white/10">
        <div className="font-display font-bold text-white">{name}</div>
        <div className="font-mono-tech text-[11px] text-white/55 mt-1 leading-relaxed">{desc}</div>
        <a
          href={url}
          download
          target="_blank"
          rel="noreferrer"
          className="mt-3 inline-flex items-center gap-2 mono-label text-[10px] text-[#ccff00] hover:underline"
          data-testid={`${testid}-download`}
        >
          DOWNLOAD →
        </a>
      </div>
    </div>
  );
}
