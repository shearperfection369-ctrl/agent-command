/**
 * /client/login — magic-link entry for the client portal.
 *
 * Scaffold-grade: the backend mints a magic link and either emails it (if
 * Resend is wired) or returns it in the response so the operator can click
 * through manually during dev / preview.
 *
 * Hitting /client/verify?token=... finalizes the session.
 */
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { CornerBrackets, SectionLabel } from "../components/Brackets";
import { clientRequestMagic, clientVerify, isClientAuthed } from "../lib/clientAuth";

export default function ClientLogin() {
    const nav = useNavigate();
    const loc = useLocation();
    const [email, setEmail] = useState("");
    const [company, setCompany] = useState("");
    const [sent, setSent] = useState(null);
    const [busy, setBusy] = useState(false);

    // /client/verify?token=... handler
    useEffect(() => {
        if (isClientAuthed() && loc.pathname === "/client/login") {
            nav("/client/dashboard", { replace: true });
            return;
        }
        if (loc.pathname === "/client/verify") {
            const params = new URLSearchParams(loc.search);
            const token = params.get("token");
            if (!token) {
                toast.error("Missing token in link.");
                return;
            }
            (async () => {
                try {
                    await clientVerify(token);
                    toast.success("Signed in.");
                    nav("/client/dashboard", { replace: true });
                } catch (e) {
                    toast.error(e?.response?.data?.detail || "Magic link expired or already used.");
                }
            })();
        }
    }, [loc.pathname, loc.search]);

    const submit = async (e) => {
        e.preventDefault();
        if (!email) return;
        setBusy(true);
        try {
            const res = await clientRequestMagic(email, company);
            setSent(res);
            if (res.email_sent) toast.success("Sign-in link sent. Check your email.");
            else toast.info("Email delivery not yet wired · use the magic link below.");
        } catch (e) {
            toast.error("Could not send magic link.");
        } finally { setBusy(false); }
    };

    return (
        <div className="bg-console min-h-screen">
            <section className="px-6 lg:px-10 py-20 grid-bg-tight border-b border-white/5">
                <div className="max-w-[640px] mx-auto deck-card relative p-8" data-testid="client-login-card">
                    <CornerBrackets />
                    <SectionLabel idx={0} color="#7c5cff">CLIENT · PORTAL</SectionLabel>
                    <h1 className="font-display font-black text-white text-4xl tracking-tighter mt-3">
                        Operator <span className="accent-cyan">sign-in.</span>
                    </h1>
                    <p className="text-white/65 text-sm mt-3 leading-relaxed">
                        Magic-link sign-in for design partners. Drop your email — we send a one-time link, no passwords.
                    </p>

                    <form onSubmit={submit} className="mt-8 space-y-3" data-testid="client-login-form">
                        <div>
                            <label className="mono-label text-[10px] text-white/55">EMAIL</label>
                            <input
                                data-testid="client-email"
                                required
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="input-tech w-full mt-1"
                                placeholder="you@broker.com"
                            />
                        </div>
                        <div>
                            <label className="mono-label text-[10px] text-white/55">COMPANY · OPTIONAL</label>
                            <input
                                data-testid="client-company"
                                type="text"
                                value={company}
                                onChange={(e) => setCompany(e.target.value)}
                                className="input-tech w-full mt-1"
                                placeholder="Acme Freight"
                            />
                        </div>
                        <button
                            data-testid="client-magic-btn"
                            disabled={busy}
                            className="btn-jade w-full text-sm disabled:opacity-50"
                        >{busy ? "SENDING…" : "SEND MAGIC LINK →"}</button>
                    </form>

                    {sent && (
                        <div className="mt-6 border border-[#ccff00]/30 bg-[#ccff00]/05 p-4" data-testid="client-magic-result">
                            <div className="mono-label text-[10px] text-[#ccff00]">LINK MINTED · EXPIRES {new Date(sent.expires).toLocaleTimeString()}</div>
                            {sent.email_sent ? (
                                <div className="font-mono-tech text-[11px] text-white/85 mt-2">
                                    Check your inbox. The link signs you straight into the portal.
                                </div>
                            ) : (
                                <>
                                    <div className="font-mono-tech text-[11px] text-[#ffce4f] mt-2 leading-relaxed">
                                        Resend isn't wired yet — preview-mode link below. Click to finish sign-in.
                                    </div>
                                    {sent.magic_url && (
                                        <a
                                            data-testid="client-magic-link"
                                            href={sent.magic_url}
                                            className="font-mono-tech text-[11px] text-[#00ffff] underline break-all block mt-2"
                                        >{sent.magic_url}</a>
                                    )}
                                </>
                            )}
                        </div>
                    )}

                    <div className="mt-6 pt-4 border-t border-white/5 font-mono-tech text-[10px] text-white/40 leading-relaxed">
                        Operator-grade. Per-tenant. SOC 2 path on the roadmap.
                    </div>
                </div>
            </section>
        </div>
    );
}
