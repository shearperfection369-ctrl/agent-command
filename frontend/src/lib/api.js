import axios from "axios";
import { toast } from "sonner";

const BASE = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = `${BASE}/api`;

export const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((cfg) => {
  const t = localStorage.getItem("jade_token");
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

// Centralized LLM-failure detection: a 402 with a structured detail.code
// means the Universal LLM Key is out of budget / has an auth issue.
// Surface a single, unambiguous toast so callers don't show "stream failed".
let _lastBudgetToast = 0;
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err?.response?.data?.detail;
    const code = detail?.code;
    const status = err?.response?.status;
    if (status === 402 && (code === "budget_exceeded" || code === "insufficient_balance")) {
      const now = Date.now();
      if (now - _lastBudgetToast > 8000) {  // throttle
        _lastBudgetToast = now;
        toast.error(detail.message || "Universal LLM Key budget exceeded. Top up to continue.", {
          duration: 8000,
          action: { label: "OPEN HEALTH", onClick: () => { window.location.href = "/admin"; } },
        });
      }
      // Stamp the error so callers can short-circuit fallback messages
      err.isLlmBudget = true;
    } else if (status === 429 && code === "rate_limited") {
      toast.warning(detail.message);
    } else if (status === 401 && code === "auth_failed") {
      toast.error(detail.message);
    }
    return Promise.reject(err);
  }
);
