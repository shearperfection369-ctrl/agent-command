import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "../components/Brackets";
import { Quotes, ArrowRight, ArrowLeft, Check } from "@/lib/icons";

export function CaseStudiesIndex() {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/case-studies").then((r) => setCases(r.data)).catch(() => toast.error("Failed")).finally(() => setLoading(false));
  }, []);

  return (
    <div className="bg-console min-h-screen">
      <section className="px-6 lg:px-10 py-16 lg:py-24 grid-bg-tight border-b border-white/5">
        <div className="max-w-[1400px] mx-auto">
          <SectionLabel idx={0} color="#ccff00">FIELD REPORTS · CASE STUDIES</SectionLabel>
          <h1 className="font-display font-black text-white text-5xl sm:text-7xl tracking-tighter glow-lime">
            Tape from<br />
            <span className="accent-cyan">the field.</span>
          </h1>
          <p className="mt-6 text-white/65 max-w-2xl leading-relaxed">
            Real customers. Real numbers. Real workflows. No vanity metrics, no AI hype.
          </p>
        </div>
      </section>

      <section className="px-6 lg:px-10 py-16">
        <div className="max-w-[1400px] mx-auto grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loading && <div className="font-mono-tech text-[#ccff00]">// loading…</div>}
          {cases.map((c, i) => (
            <Link to={`/cases/${c.slug}`} key={c.id} data-testid={`case-card-${c.slug}`}
              className="deck-card p-7 relative block hover:bg-white/[0.02]">
              <CornerBrackets />
              <div className="mono-label text-[#00ffff]">{c.industry.replace("_", " ").toUpperCase()}</div>
              <h2 className="font-display font-bold text-white text-2xl tracking-tight mt-4 leading-tight">{c.headline}</h2>
              <div className="mt-5 mono-label text-white/40">CUSTOMER</div>
              <div className="font-mono-tech text-sm text-white/80 mt-1">{c.company}</div>
              <div className="mt-6 pt-5 border-t border-white/5">
                <span className="mono-label text-[#ccff00] inline-flex items-center gap-1">READ FIELD REPORT <ArrowRight size={12} weight="bold" /></span>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

export function CaseStudyDetail() {
  const { slug } = useParams();
  const [c, setC] = useState(null);

  useEffect(() => {
    api.get(`/case-studies/${slug}`).then((r) => setC(r.data)).catch(() => toast.error("Not found"));
  }, [slug]);

  if (!c) return <div className="bg-console min-h-screen grid place-items-center font-mono-tech text-[#ccff00]">// loading…</div>;

  return (
    <div className="bg-console min-h-screen">
      <section className="px-6 lg:px-10 py-16 lg:py-20 grid-bg-tight border-b border-white/5">
        <div className="max-w-[1100px] mx-auto">
          <Link to="/cases" className="mono-label text-[#00ffff] inline-flex items-center gap-2 mb-8 hover:text-[#ccff00]">
            <ArrowLeft size={12} weight="bold" /> ALL FIELD REPORTS
          </Link>
          <div className="mono-label text-[#ccff00] mb-3">{c.industry.replace("_", " ").toUpperCase()} · {c.company}</div>
          <h1 className="font-display font-black text-white text-4xl sm:text-6xl tracking-tighter glow-lime">{c.headline}</h1>
        </div>
      </section>

      <section className="px-6 lg:px-10 py-16">
        <div className="max-w-[1100px] mx-auto grid lg:grid-cols-3 gap-10">
          <div className="lg:col-span-2 space-y-10">
            <Block label="01 · THE PROBLEM" color="#ff3b8a" body={c.problem} />
            <Block label="02 · THE SOLUTION" color="#00ffff" body={c.solution} />
            <div>
              <div className="mono-label text-[#ccff00] mb-4">03 · RESULTS</div>
              <ul className="space-y-3">
                {c.results.map((r, i) => (
                  <li key={i} className="deck-card p-5 flex items-start gap-3 relative">
                    <Check size={18} className="text-[#ccff00] mt-1" weight="bold" />
                    <span className="text-white/85">{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <aside className="lg:col-span-1">
            {c.quote && (
              <div className="deck-card p-7 relative sticky top-24">
                <CornerBrackets />
                <Quotes size={26} className="text-[#00ffff]" weight="bold" />
                <p className="mt-4 font-display text-white text-xl leading-snug italic">"{c.quote}"</p>
                {c.quote_attribution && <div className="mt-4 mono-label text-[#ccff00]">— {c.quote_attribution}</div>}
              </div>
            )}
          </aside>
        </div>
      </section>
    </div>
  );
}

function Block({ label, color, body }) {
  return (
    <div>
      <div className="mono-label mb-4" style={{ color }}>{label}</div>
      <p className="text-white/80 text-lg leading-relaxed">{body}</p>
    </div>
  );
}
