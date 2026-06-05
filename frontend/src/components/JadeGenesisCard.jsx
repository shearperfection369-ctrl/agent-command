import { Link } from "react-router-dom";
import { CornerBrackets } from "./Brackets";

const GENESIS_URL = "https://customer-assets.emergentagent.com/job_mpls-automation-hub/artifacts/3j8rupt9_g3ENESIS.png";

/**
 * JadeGenesisCard — the "meet your AI" portrait card.
 * Uses Genesis (the first self-portrait Jade AI generated of herself) inside JADE OS UI grammar:
 * corner brackets, LIVE pill, GENESIS provenance caption, and side actions.
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
        {/* LIVE pill */}
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
          alt="JADE — Genesis self-portrait, the first image JADE AI created of herself"
          loading="eager"
          decoding="async"
          className="block w-full h-full object-cover"
          data-testid="jade-genesis-image"
          style={{ minHeight: compact ? "320px" : "480px", aspectRatio: "3/4" }}
        />
        {/* GENESIS provenance caption */}
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
        {/* Console-black bottom gradient for caption legibility */}
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
          <Link
            to="/demo"
            data-testid="jade-genesis-ask-btn"
            className="block w-full px-5 py-4 border border-white/15 hover:border-[#ccff00] transition group bg-black/40"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="font-display font-bold text-white text-lg group-hover:text-[#ccff00] transition">Ask Jade</div>
                <div className="font-mono-tech text-[10px] text-white/45 mt-1">// open live chat · /demo</div>
              </div>
              <span className="mono-label text-white/30 group-hover:text-[#ccff00] transition">→</span>
            </div>
          </Link>

          <div className="px-1 mono-label text-[10px] text-white/35 tracking-[0.4em] pt-1">◆ QUICK ACTIONS</div>

          <Link
            to="/playbooks/new"
            data-testid="jade-genesis-build-btn"
            className="block w-full px-5 py-4 border border-white/15 hover:border-[#00ffff] transition group bg-black/40"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="font-display font-bold text-white text-lg group-hover:text-[#00ffff] transition">Build a playbook</div>
                <div className="font-mono-tech text-[10px] text-white/45 mt-1">// chain agents · /playbooks/new</div>
              </div>
              <span className="mono-label text-white/30 group-hover:text-[#00ffff] transition">→</span>
            </div>
          </Link>

          <Link
            to="/lighthouse"
            data-testid="jade-genesis-pilot-btn"
            className="block w-full px-5 py-4 border border-white/15 hover:border-[#ff3b8a] transition group bg-black/40"
          >
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
