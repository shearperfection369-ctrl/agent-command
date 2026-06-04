import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="border-t border-white/5 bg-[#02030a] mt-24">
      <div className="max-w-[1400px] mx-auto px-6 lg:px-10 py-12 grid md:grid-cols-4 gap-10">
        <div className="md:col-span-2">
          <div className="flex items-center gap-3 mb-4">
            <div className="h-8 w-8 border border-[#ccff00] grid place-items-center">
              <span className="font-display text-[#ccff00] font-black">J</span>
            </div>
            <span className="font-display font-bold text-white text-lg">JADE OS</span>
          </div>
          <p className="text-sm text-white/60 max-w-md leading-relaxed">
            Operator-grade AI agents for Minneapolis freight, ops, and revenue teams.
            <span className="accent-cyan"> Built for power users.</span>
          </p>
          <div className="mt-5 mono-label text-white/40">HQ · MPLS / SAINT PAUL · 55401</div>
        </div>
        <div>
          <div className="mono-label text-[#ccff00] mb-3">SYSTEM</div>
          <ul className="space-y-2 text-sm text-white/70">
            <li><Link className="hover:text-[#00ffff]" to="/">Home</Link></li>
            <li><Link className="hover:text-[#00ffff]" to="/reel">Demo Reel</Link></li>
            <li><Link className="hover:text-[#00ffff]" to="/demo">Console</Link></li>
            <li><Link className="hover:text-[#00ffff]" to="/deck">Pitch Deck</Link></li>
            <li><Link className="hover:text-[#00ffff]" to="/cases">Case Studies</Link></li>
            <li><Link className="hover:text-[#00ffff]" to="/plan">Business Plan</Link></li>
            <li><Link className="hover:text-[#00ffff]" to="/launch">Launch Kit</Link></li>
            <li><Link className="hover:text-[#00ffff]" to="/billing">Pricing</Link></li>
            <li><Link className="hover:text-[#00ffff]" to="/portal">Customer Portal</Link></li>
          </ul>
        </div>
        <div>
          <div className="mono-label text-[#ccff00] mb-3">CONTACT</div>
          <ul className="space-y-2 text-sm text-white/70 font-mono-tech">
            <li>OPS@JADEOS.AI</li>
            <li>+1 (612) 555 · 0117</li>
            <li>NORTH LOOP · MPLS</li>
          </ul>
        </div>
      </div>
      <div className="border-t border-white/5 py-5 text-center mono-label text-white/30">
        © 2026 JADE OS · ALL OPERATIONS LOCKED IN
      </div>
    </footer>
  );
}
