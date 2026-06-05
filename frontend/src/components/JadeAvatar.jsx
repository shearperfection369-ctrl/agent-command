/**
 * JadeAvatar — the glowing holographic Jade-lime AI presence.
 *
 * Renders a breathing orb with rotating rings, scanlines, particle motes,
 * and a center "J" monogram. Pure CSS/SVG, no external animation lib.
 *
 * Props:
 *   size   — px (default 88)
 *   busy   — when true, ring spins faster and glow intensifies
 *   label  — optional verb to display beside the orb (e.g. "extracting")
 */
import React from "react";

export function JadeAvatar({ size = 88, busy = false, className = "" }) {
  const s = size;
  // Theme-reactive via CSS variable; falls back to lime
  const stroke = "var(--jade-lime, #ccff00)";
  const glow = "var(--jade-lime, #ccff00)";
  return (
    <div
      className={`jade-avatar ${busy ? "is-busy" : ""} ${className}`}
      style={{ "--av-size": `${s}px`, "--av-stroke": stroke, "--av-glow": glow }}
      data-testid="jade-avatar"
      aria-hidden="true"
    >
      <svg viewBox="0 0 100 100" width={s} height={s} className="jade-avatar-svg">
        {/* Outer rotating dashed ring */}
        <circle
          cx="50" cy="50" r="46"
          fill="none"
          stroke={stroke}
          strokeWidth="0.8"
          strokeDasharray="3 4"
          className="jade-avatar-ring jade-avatar-ring-1"
        />
        {/* Inner counter-rotating tick ring */}
        <circle
          cx="50" cy="50" r="38"
          fill="none"
          stroke={stroke}
          strokeWidth="0.6"
          strokeDasharray="1 6"
          opacity="0.55"
          className="jade-avatar-ring jade-avatar-ring-2"
        />
        {/* Soft orb body */}
        <defs>
          <radialGradient id="jade-avatar-orb" cx="50%" cy="38%" r="60%">
            <stop offset="0%" stopColor={stroke} stopOpacity="0.95" />
            <stop offset="55%" stopColor={stroke} stopOpacity="0.30" />
            <stop offset="100%" stopColor={stroke} stopOpacity="0" />
          </radialGradient>
          <linearGradient id="jade-avatar-scan" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={stroke} stopOpacity="0" />
            <stop offset="50%" stopColor={stroke} stopOpacity="0.55" />
            <stop offset="100%" stopColor={stroke} stopOpacity="0" />
          </linearGradient>
        </defs>
        <circle cx="50" cy="50" r="30" fill="url(#jade-avatar-orb)" className="jade-avatar-orb" />
        {/* Hologram scanline sweep */}
        <rect
          x="20" y="0" width="60" height="3"
          fill="url(#jade-avatar-scan)"
          className="jade-avatar-scan"
        />
        {/* J monogram */}
        <text
          x="50" y="62"
          textAnchor="middle"
          fontFamily="'Space Grotesk', sans-serif"
          fontWeight="900"
          fontSize="34"
          fill={stroke}
          style={{ filter: `drop-shadow(0 0 6px ${glow})` }}
        >J</text>
        {/* Corner brackets */}
        <g stroke={stroke} strokeWidth="1.2" fill="none" opacity="0.7">
          <polyline points="6,18 6,6 18,6" />
          <polyline points="94,18 94,6 82,6" />
          <polyline points="6,82 6,94 18,94" />
          <polyline points="94,82 94,94 82,94" />
        </g>
        {/* Pulse motes */}
        <circle cx="14" cy="50" r="1.4" fill={stroke} className="jade-avatar-mote jade-avatar-mote-1" />
        <circle cx="86" cy="50" r="1.4" fill={stroke} className="jade-avatar-mote jade-avatar-mote-2" />
        <circle cx="50" cy="14" r="1.4" fill={stroke} className="jade-avatar-mote jade-avatar-mote-3" />
      </svg>
    </div>
  );
}

/**
 * JadeWorking — orb + breathing status text + ellipsis. Drop-in replacement
 * for any "running…" / "loading…" inline spinner across the app.
 */
export function JadeWorking({ verb = "thinking", size = 64, className = "" }) {
  return (
    <div className={`jade-working ${className}`} data-testid="jade-working">
      <JadeAvatar size={size} busy />
      <div className="jade-working-copy">
        <div className="jade-working-label">JADE is <span className="jade-working-verb">{verb}</span><span className="jade-working-dots" aria-hidden>…</span></div>
        <div className="jade-working-sub">// holographic compute · live</div>
      </div>
    </div>
  );
}
