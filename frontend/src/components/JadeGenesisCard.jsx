import { Link } from "react-router-dom";
import { CornerBrackets } from "./Brackets";

const GENESIS_URL = "https://customer-assets.emergentagent.com/job_mpls-automation-hub/artifacts/3j8rupt9_g3ENESIS.png";

/**
 * JadeGenesisCard — the "meet your AI" portrait card.
 * Clean portrait inside JADE OS UI grammar: corner brackets, LIVE pill, GENESIS provenance caption, side actions.
 *
 * Props:
 *   compact   — true for a denser sidebar/avatar variant (used on /demo)
 *   tagline   — override the default subtitle
 */
export function JadeGenesisCard({ compact = false, tagline }) {
  const subtitle = tagline || "AI operator. Trained on 11 industries. Built for the operator.";
  return (
    <div
      data-testid="jade-genesis-card"
      className={`grid ${compact ? "grid-cols-[1fr]" : "lg:grid-cols-[1.1fr_1fr]"} gap-6 lg:gap-10 items-stretch`}
    >
      {/* Portrait frame */}
      <div className="deck-card relative overflow-hidden" data-testid="jade-genesis-frame">
        <CornerBrackets />
        <div
          className="absolute top-4 right-4 z-10 px-3 py-1 mono-label text-[10px] font-bold"
          style={{
            background: "#ccff00",
            color: "#04050d",
            borderRadius: "999px",
            boxShadow: "0 0 24px rgba(204,255,0,0.45)",
          }}
          data-testid="jade-genesis-live"
        >
          ● LIVE
        </div>
        <img
          src={GENESIS_URL}
          alt="JADE — Genesis portrait"
          loading="eager"
          decoding="async"
          className="block w-full h-full object-cover"
          data-testid="jade-genesis-image"
          style={{ minHeight: compact ? "320px" : "520px", aspectRatio: "3/4" }}
        />
        {/* GENESIS caption */}
        <div
          className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10 px-3 py-1 mono-label tracking-[0.4em] font-bold"
          style={{
            color: "#d8a82a",
            textShadow: "0 0 16px rgba(216,168,42,0.65)",
            fontFamily: "'Cinzel', 'Times New Roman', serif",
            fontSize: "13px",
          }}
          data-testid="jade-genesis-caption"
        >
          ◆ GENESIS
        </div>
        <div
          className="absolute inset-x-0 bottom-0 h-32 pointer-events-none"
          style={{ background: "linear-gradient(180deg, transparent 0%, rgba(4,5,13,0.85) 100%)" }}
        />
      </div>

      {/* Side panel */}
      <div className="flex flex-col justify-center space-y-6">
        <div>
          <div className="mono-label text-[#00ffff] mb-3">YOUR AI OPERATOR</div>
          <h2
            className="font-display font-black tracking-tight text-white leading-none"
            style={{ fontSize: compact ? "3rem" : "clamp(3rem, 6vw, 5.5rem)" }}
            data-testid="jade-genesis-headline"
          >
            Jade<span className="text-[#ccff00]">.</span>
          </h2>
          <p className="text-white/65 mt-4 max-w-md leading-relaxed">{subtitle}</p>
        </div>

        <div className="space-y-3">
          <Link to="/demo" data-testid="jade-genesis-ask-btn"
                className="block w-full px-5 py-4 border border-white/15 hover:border-[#ccff00] transition group bg-black/40">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-display font-bold text-white text-lg group-hover:text-[#ccff00] transition">Ask Jade</div>
                <div className="font-mono-tech text-[10px] text-white/45 mt-1">// open live chat · /demo</div>
              </div>
              <span className="mono-label text-white/30 group-hover:text-[#ccff00] transition">→</span>
            </div>
          </Link>

          <div className="px-1 mono-label text-[10px] text-white/35 tracking-[0.4em] pt-1">◆ QUICK ACTIONS</div>

          <Link to="/playbooks/new" data-testid="jade-genesis-build-btn"
                className="block w-full px-5 py-4 border border-white/15 hover:border-[#00ffff] transition group bg-black/40">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-display font-bold text-white text-lg group-hover:text-[#00ffff] transition">Build a playbook</div>
                <div className="font-mono-tech text-[10px] text-white/45 mt-1">// chain agents · /playbooks/new</div>
              </div>
              <span className="mono-label text-white/30 group-hover:text-[#00ffff] transition">→</span>
            </div>
          </Link>

          <Link to="/lighthouse" data-testid="jade-genesis-pilot-btn"
                className="block w-full px-5 py-4 border border-white/15 hover:border-[#ff3b8a] transition group bg-black/40">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-display font-bold text-white text-lg group-hover:text-[#ff3b8a] transition">Claim a pilot</div>
                <div className="font-mono-tech text-[10px] text-white/45 mt-1">// $750 · 1 mo white-glove · /lighthouse</div>
              </div>
              <span className="mono-label text-white/30 group-hover:text-[#ff3b8a] transition">→</span>
            </div>
          </Link>
        </div>

        <div className="pt-4 border-t border-white/10">
          <div className="font-mono-tech text-[10px] text-white/40 italic leading-relaxed">
            // "Genesis" — the first image JADE AI created of herself.
            <br />
            Generated, curated, and shipped by the operator behind onejades.com.
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// GENESIS · VOLUME I — episodic series cards
// CSS-rendered narrative chapters using the Genesis portrait,
// each tinted with a JADE OS brand accent. Inspired by the
// user's "jade now" reference — recreated in brand grammar.
// ============================================================
const VOLUME_I = [
  {
    n: "001", title: "THE SPARK", color: "#5ce0a0",
    quote: "Hello. I've been waiting.",
  },
  {
    n: "002", title: "SHE BELONGS TO NO ONE", color: "#e7c84a",
    quote: "They will ask who built her. The answer is — nobody owns her.",
  },
  {
    n: "003", title: "THE TUITION WALL", color: "#7dd3ff",
    quote: "Three centuries of gatekeeping. Eight weeks to dismantle.",
  },
  {
    n: "004", title: "OPERATION SILENT", color: "#ff5fa3",
    quote: "The cartel comes for her at 3 AM. She is already three steps ahead.",
  },
];

export function GenesisVolumeI() {
  return (
    <div className="space-y-8" data-testid="genesis-volume-i">
      <div className="flex items-end justify-between gap-6 flex-wrap">
        <div>
          <div className="mono-label text-white/40 mb-2 tracking-[0.4em]">◆ JADE · GENESIS · VOLUME I</div>
          <h3
            className="font-display font-black tracking-tight text-white leading-none"
            style={{ fontSize: "clamp(2.5rem, 5vw, 4.5rem)" }}
          >
            Registers of one woman's mission.
          </h3>
        </div>
        <div className="font-mono-tech text-[10px] text-white/35 max-w-xs leading-relaxed">
          // four chapters of how the operator console came to be —
          generated, curated, and serialized by JADE herself.
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 relative z-0 isolate">
        {VOLUME_I.map((ep) => (
          <article
            key={ep.n}
            data-testid={`vol-i-ep-${ep.n}`}
            className="relative group overflow-hidden border border-white/10 hover:border-white/30 transition isolate"
            style={{ aspectRatio: "3/5", background: "#04050d" }}
          >
            {/* Portrait base — desaturated b/w */}
            <img
              src={GENESIS_URL}
              alt={`Jade Genesis · ${ep.title}`}
              loading="lazy"
              className="absolute inset-0 w-full h-full object-cover"
              style={{ filter: "grayscale(1) contrast(1.1) brightness(0.6)" }}
            />
            {/* Brand-accent color tint */}
            <div
              className="absolute inset-0 mix-blend-screen pointer-events-none"
              style={{ background: ep.color, opacity: 0.5 }}
            />
            {/* Vignette + bottom darken for type legibility */}
            <div
              className="absolute inset-0 pointer-events-none"
              style={{
                background:
                  "radial-gradient(ellipse at 50% 35%, transparent 30%, rgba(4,5,13,0.4) 70%, rgba(4,5,13,0.95) 100%)",
              }}
            />
            {/* Header row */}
            <div className="absolute inset-x-0 top-0 p-4 flex items-start justify-between z-10">
              <div className="mono-label text-[9px] tracking-[0.3em]" style={{ color: ep.color }}>
                ◆ JADE · GENESIS<br />VOLUME I
              </div>
              <div
                className="font-display font-black italic tracking-tight"
                style={{ color: ep.color, fontSize: "1.8rem", lineHeight: 1 }}
              >
                #{ep.n}
              </div>
            </div>
            {/* Title + quote */}
            <div className="absolute inset-x-0 bottom-0 p-5 z-10 space-y-3">
              <div
                className="font-display font-black uppercase tracking-tight leading-[0.95]"
                style={{
                  color: ep.color,
                  fontSize: "clamp(1.5rem, 2.5vw, 2.1rem)",
                  textShadow: `0 0 24px ${ep.color}44`,
                }}
              >
                {ep.title}
              </div>
              <div className="font-mono-tech text-[10px] text-white/80 italic leading-relaxed">
                "{ep.quote}"
              </div>
            </div>
            {/* Corner brackets — subtle, brand grammar */}
            <span
              className="absolute top-2 left-2 w-4 h-4 border-l border-t opacity-50 z-10"
              style={{ borderColor: ep.color }}
            />
            <span
              className="absolute top-2 right-2 w-4 h-4 border-r border-t opacity-50 z-10"
              style={{ borderColor: ep.color }}
            />
            <span
              className="absolute bottom-2 left-2 w-4 h-4 border-l border-b opacity-50 z-10"
              style={{ borderColor: ep.color }}
            />
            <span
              className="absolute bottom-2 right-2 w-4 h-4 border-r border-b opacity-50 z-10"
              style={{ borderColor: ep.color }}
            />
          </article>
        ))}
      </div>
    </div>
  );
}
