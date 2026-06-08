import { Link, NavLink, useNavigate } from "react-router-dom";
import { isAuthed, clearToken } from "../lib/auth";

const links = [
  { to: "/", label: "Home" },
  { to: "/reel", label: "Demo Reel" },
  { to: "/demo", label: "Console" },
  { to: "/lighthouse", label: "Lighthouse" },
  { to: "/vc-package", label: "VC Package" },
  { to: "/deck", label: "Pitch Deck" },
  { to: "/cases", label: "Cases" },
  { to: "/billing", label: "Pricing" },
];

export default function Nav() {
  const nav = useNavigate();
  const authed = isAuthed();

  return (
    <header className="sticky top-0 z-50 backdrop-blur bg-[#02030a]/85 border-b border-white/5">
      <div className="max-w-[1400px] mx-auto px-6 lg:px-10 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group" data-testid="nav-logo">
          <div className="relative">
            <div className="h-9 w-9 border border-[#ccff00] grid place-items-center">
              <span className="font-display text-[#ccff00] font-black text-lg leading-none">J</span>
            </div>
            <span className="absolute -bottom-1 -right-1 h-2 w-2 bg-[#00ffff]" />
          </div>
          <div className="flex flex-col leading-tight">
            <span className="font-display font-bold tracking-tight text-white text-lg">JadeOS</span>
            <span className="mono-label text-[#ccff00]">MPLS · AI AGENTS</span>
          </div>
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              data-testid={`nav-${l.label.toLowerCase().replace(/\s/g, "-")}`}
              className={({ isActive }) =>
                `font-mono-tech text-xs tracking-[0.25em] uppercase transition-colors ${
                  isActive ? "text-[#ccff00]" : "text-white/70 hover:text-[#00ffff]"
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
          {authed ? (
            <NavLink to="/admin" data-testid="nav-admin" className="font-mono-tech text-xs tracking-[0.25em] uppercase text-[#7c5cff] hover:text-[#00ffff]">
              Admin
            </NavLink>
          ) : null}
        </nav>

        <div className="flex items-center gap-3">
          {authed ? (
            <button
              data-testid="nav-logout-btn"
              onClick={() => { clearToken(); nav("/"); }}
              className="btn-ghost text-xs"
            >
              LOG OUT
            </button>
          ) : (
            <Link to="/login" data-testid="nav-login-btn" className="btn-ghost text-xs hidden sm:inline-block">
              ADMIN LOGIN
            </Link>
          )}
          <Link to="/demo" data-testid="nav-cta-demo" className="btn-jade text-xs">
            LAUNCH DEMO →
          </Link>
        </div>
      </div>
    </header>
  );
}
