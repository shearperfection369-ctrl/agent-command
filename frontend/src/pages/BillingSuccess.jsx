import { useEffect, useState, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../lib/api";
import { CornerBrackets, SectionLabel } from "../components/Brackets";
import { CheckCircle, XCircle } from "@phosphor-icons/react";

export default function BillingSuccess() {
  const [sp] = useSearchParams();
  const sessionId = sp.get("session_id");
  const [status, setStatus] = useState({ phase: "pending", payment_status: null, info: null });
  const attempts = useRef(0);
  const nav = useNavigate();

  useEffect(() => {
    if (!sessionId) {
      setStatus({ phase: "error", info: "Missing session_id" });
      return;
    }
    let cancelled = false;
    const poll = async () => {
      if (cancelled) return;
      if (attempts.current >= 8) {
        setStatus({ phase: "timeout", info: "Status check timed out — refresh in a minute." });
        return;
      }
      attempts.current += 1;
      try {
        const { data } = await api.get(`/billing/status/${sessionId}`);
        if (data.payment_status === "paid") {
          setStatus({ phase: "paid", payment_status: "paid", info: data });
          toast.success("Subscription active. Welcome aboard, operator.");
          return;
        }
        if (data.status === "expired" || data.payment_status === "expired") {
          setStatus({ phase: "expired", info: data });
          return;
        }
        setStatus({ phase: "pending", info: data });
        setTimeout(poll, 2000);
      } catch (e) {
        setStatus({ phase: "error", info: e?.response?.data?.detail || "lookup failed" });
      }
    };
    poll();
    return () => { cancelled = true; };
  }, [sessionId]);

  const isPaid = status.phase === "paid";
  const isErr = status.phase === "error" || status.phase === "expired" || status.phase === "timeout";

  return (
    <div className="bg-console min-h-screen grid place-items-center px-6">
      <div className="deck-card p-10 max-w-lg w-full relative" data-testid="billing-success">
        <CornerBrackets />
        <div className="mono-label text-[#00ffff] mb-4">BILLING · STATUS</div>
        {status.phase === "pending" && (
          <>
            <div className="font-display font-black text-white text-4xl tracking-tighter">Locked in.<br /><span className="accent-cyan">Verifying tape…</span></div>
            <p className="mt-5 text-white/65 text-sm">Polling Stripe for confirmation. This usually takes 3–6 seconds.</p>
            <div className="mt-6 font-mono-tech text-xs text-[#ccff00] animate-pulse">// attempt {attempts.current} / 8</div>
          </>
        )}
        {isPaid && (
          <>
            <CheckCircle size={48} className="text-[#ccff00]" weight="duotone" />
            <h1 className="mt-4 font-display font-black text-white text-4xl">Subscription active.</h1>
            <p className="mt-3 text-white/70">Your tier: <span className="text-[#ccff00] font-bold">{(status.info?.tier || "FLEET").toUpperCase()}</span>. We'll reach out within 24 hours to schedule onboarding.</p>
            <div className="mt-6 grid sm:grid-cols-2 gap-3">
              <button data-testid="success-portal-btn" onClick={() => nav("/portal")} className="btn-jade">OPEN PORTAL</button>
              <button data-testid="success-home-btn" onClick={() => nav("/")} className="btn-ghost">BACK HOME</button>
            </div>
          </>
        )}
        {isErr && (
          <>
            <XCircle size={48} className="text-[#ff3b8a]" weight="duotone" />
            <h1 className="mt-4 font-display font-black text-white text-4xl">Something's off.</h1>
            <p className="mt-3 text-white/70">{status.info?.toString?.() || JSON.stringify(status.info)}</p>
            <button data-testid="error-back-btn" onClick={() => nav("/billing")} className="btn-jade mt-6">TRY AGAIN</button>
          </>
        )}
      </div>
    </div>
  );
}
