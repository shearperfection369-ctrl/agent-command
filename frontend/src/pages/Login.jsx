import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { ArrowRight, Lock } from "@/lib/icons";
import { api } from "../lib/api";
import { setToken } from "../lib/auth";
import { CornerBrackets } from "../components/Brackets";

export default function Login() {
  const nav = useNavigate();
  const [params] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/auth/login", { email, password });
      setToken(data.access_token);
      toast.success("Locked in.");
      const next = params.get("next");
      // Only honor in-app paths to avoid open-redirect
      if (next && next.startsWith("/")) {
        nav(next);
      } else {
        nav("/admin");
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Bad credentials.");
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-[80vh] bg-console grid place-items-center px-6 relative">
      <div className="absolute inset-0 grid-bg pointer-events-none" />
      <form onSubmit={submit} className="deck-card p-10 max-w-md w-full relative" data-testid="login-form">
        <CornerBrackets />
        <div className="flex items-center gap-2 mb-2">
          <Lock size={14} className="text-[#ccff00]" weight="bold" />
          <span className="mono-label text-[#ccff00]">ADMIN · VAULT ACCESS</span>
        </div>
        <h1 className="font-display font-black text-white text-3xl tracking-tight">Punch in.</h1>
        <p className="text-white/55 text-sm mt-2">Operator-only. JADE leads + agent run history live behind this door.</p>

        <div className="mt-7 space-y-4">
          <label className="block">
            <span className="mono-label text-white/45 block mb-2">EMAIL</span>
            <input data-testid="login-email" required type="email" className="input-tech" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="admin@jadeos.ai" />
          </label>
          <label className="block">
            <span className="mono-label text-white/45 block mb-2">PASSWORD</span>
            <input data-testid="login-password" required type="password" className="input-tech" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
          </label>
        </div>
        <button data-testid="login-submit-btn" disabled={loading} className="btn-jade mt-7 w-full inline-flex items-center justify-center gap-2">
          {loading ? "AUTHENTICATING…" : <>OPEN THE VAULT <ArrowRight size={16} weight="bold" /></>}
        </button>
      </form>
    </div>
  );
}
