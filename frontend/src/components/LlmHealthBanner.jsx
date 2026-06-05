/**
 * LlmHealthBanner — global red banner shown when the Universal LLM Key is
 * degraded (budget exceeded / insufficient balance / auth failed).
 *
 * Polls /api/llm-health (public, zero-cost) every 60s. Hides itself when
 * status is "ok" or "healthy". Dismissable for the current session.
 */
import { useEffect, useState } from "react";
import { api } from "../lib/api";

const STORAGE_KEY = "jadeos.health.dismissed_at";

export default function LlmHealthBanner() {
    const [health, setHealth] = useState(null);
    const [dismissed, setDismissed] = useState(() => {
        try { return sessionStorage.getItem(STORAGE_KEY); } catch { return null; }
    });

    useEffect(() => {
        let alive = true;
        const tick = async () => {
            try {
                const { data } = await api.get("/llm-health");
                if (alive) setHealth(data);
            } catch (e) { /* ignore */ }
        };
        tick();
        const id = setInterval(tick, 60000);
        return () => { alive = false; clearInterval(id); };
    }, []);

    if (!health) return null;
    if (health.status === "ok" || health.code === "healthy") return null;
    if (dismissed) return null;

    const isBudget = health.code === "budget_exceeded" || health.code === "insufficient_balance";
    const bg = isBudget ? "#ff3b8a" : "#ffce4f";
    const ink = "#02030a";

    const onDismiss = () => {
        try { sessionStorage.setItem(STORAGE_KEY, String(Date.now())); } catch (e) { /* ignore */ }
        setDismissed(String(Date.now()));
    };

    return (
        <div
            data-testid="llm-health-banner"
            data-print-hide
            className="w-full px-4 py-2 flex items-center justify-between gap-4 flex-wrap"
            style={{ background: bg, color: ink, borderBottom: `2px solid ${ink}33` }}
        >
            <div className="flex items-center gap-3 flex-wrap">
                <span className="font-display font-black text-xs uppercase tracking-widest">⚠ LLM</span>
                <span className="font-mono-tech text-xs leading-snug">
                    {health.message}
                    {typeof health.current_cost === "number" && typeof health.max_budget === "number" && (
                        <span className="ml-2 opacity-70">
                            (${health.current_cost.toFixed(2)} / ${health.max_budget.toFixed(2)})
                        </span>
                    )}
                </span>
            </div>
            <div className="flex items-center gap-2">
                <a
                    data-testid="llm-health-action"
                    href="/admin"
                    className="font-mono-tech text-[10px] uppercase tracking-widest px-3 py-1 border"
                    style={{ borderColor: ink, color: ink, background: "#ffffff44" }}
                >
                    OPEN HEALTH TAB →
                </a>
                <button
                    data-testid="llm-health-dismiss"
                    onClick={onDismiss}
                    aria-label="Dismiss"
                    className="font-mono-tech text-xs px-2 py-1"
                    style={{ color: ink }}
                >✕</button>
            </div>
        </div>
    );
}
