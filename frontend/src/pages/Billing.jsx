import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "../components/Brackets";
import { Check, ArrowRight } from "@phosphor-icons/react";

const TIERS = [
  { id: "dispatch", name: "DISPATCH", price: "$1,500", per: "/MO", c: "#ccff00",
    feats: ["1 agent · any vertical", "Up to 500 runs / mo", "Slack + email delivery", "Email support · 1 business day"] },
  { id: "fleet", name: "FLEET", price: "$4,500", per: "/MO", c: "#00ffff", featured: true,
    feats: ["3 agents · any verticals", "Up to 5,000 runs / mo", "Native CRM / TMS / EMR webhooks", "Dedicated Slack · same-day"] },
  { id: "vault", name: "VAULT", price: "Custom", per: "ANNUAL", c: "#7c5cff",
    feats: ["Unlimited agents + custom builds", "On-prem / VPC deployment", "SOC2 + BAA for healthcare", "Quarterly ops review · named engineer"] },
];

export default function Billing() {
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [loadingTier, setLoadingTier] = useState(null);

  const checkout = async (tier) => {
    if (tier === "vault") {
      window.location.href = "/#book";
      return;
    }
    if (!email || !company) {
      toast.error("Enter work email + company before checkout, operator.");
      return;
    }
    setLoadingTier(tier);
    try {
      const { data } = await api.post("/billing/checkout", {
        tier,
        email,
        company,
        origin_url: window.location.origin,
      });
      window.location.href = data.url;
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Checkout failed.");
      setLoadingTier(null);
    }
  };

  return (
    <div className="bg-console min-h-screen">
      <section className="px-6 lg:px-10 py-16 lg:py-24 grid-bg-tight border-b border-white/5">
        <div className="max-w-[1400px] mx-auto">
          <SectionLabel idx={0} color="#ccff00">VAULT TIERS · CHECKOUT</SectionLabel>
          <h1 className="font-display font-black text-white text-5xl sm:text-7xl tracking-tighter glow-lime">
            Pick a tier.<br />
            <span className="accent-cyan">Ship in 30 days.</span>
          </h1>
          <p className="mt-6 text-white/65 max-w-2xl leading-relaxed">
            Stripe handles checkout. We handle the agent. Test mode active — use 4242 4242 4242 4242 with any future date + any CVC.
          </p>
        </div>
      </section>

      <section className="px-6 lg:px-10 py-12">
        <div className="max-w-[1400px] mx-auto deck-card p-6 lg:p-8 relative">
          <CornerBrackets />
          <div className="mono-label text-[#00ffff] mb-4">YOUR DETAILS · USED FOR THE SUBSCRIPTION</div>
          <div className="grid sm:grid-cols-2 gap-4">
            <input data-testid="billing-email" type="email" placeholder="WORK EMAIL"
              value={email} onChange={(e) => setEmail(e.target.value)} className="input-tech" />
            <input data-testid="billing-company" placeholder="COMPANY NAME"
              value={company} onChange={(e) => setCompany(e.target.value)} className="input-tech" />
          </div>
        </div>
      </section>

      <section className="px-6 lg:px-10 pb-24">
        <div className="max-w-[1400px] mx-auto grid md:grid-cols-3 gap-5">
          {TIERS.map((t) => (
            <div key={t.id} data-testid={`tier-${t.id}`}
              className={`relative p-8 ${t.featured ? "bg-[#0a0c18]" : "bg-[#06081a]"}`}
              style={{ border: `1px solid ${t.featured ? t.c : "rgba(255,255,255,0.08)"}` }}>
              {t.featured && <div className="absolute -top-3 left-6 px-2 py-1 bg-[#00ffff] text-[#02030a] mono-label font-bold">MOST FLEETS</div>}
              <div className="mono-label" style={{ color: t.c }}>{t.name}</div>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="font-display font-black text-white text-5xl">{t.price}</span>
                <span className="mono-label text-white/40">{t.per}</span>
              </div>
              <ul className="mt-8 space-y-3 text-sm text-white/70">
                {t.feats.map((f) => (
                  <li key={f} className="flex gap-3"><Check size={16} className="mt-0.5" style={{ color: t.c }} weight="bold" />{f}</li>
                ))}
              </ul>
              <button data-testid={`tier-cta-${t.id}`} onClick={() => checkout(t.id)} disabled={loadingTier === t.id}
                className={t.featured ? "btn-jade mt-8 w-full inline-flex items-center justify-center gap-2"
                                       : "btn-ghost mt-8 w-full inline-flex items-center justify-center gap-2"}>
                {loadingTier === t.id ? "OPENING STRIPE…" : <>{t.id === "vault" ? "TALK TO US" : "CHECKOUT"} <ArrowRight size={14} weight="bold" /></>}
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
