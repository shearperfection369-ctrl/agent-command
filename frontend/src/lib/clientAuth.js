/**
 * Client portal auth helpers — JWT stored under `jade_client_token`.
 * Production-ready surface (request-magic-link / verify / me) wired to
 * /api/client/auth/* on the backend.
 */
import { api } from "./api";

const KEY = "jade_client_token";

export function getClientToken() {
    return typeof window !== "undefined" ? window.localStorage.getItem(KEY) : null;
}

export function setClientToken(tok) {
    if (typeof window === "undefined") return;
    if (tok) window.localStorage.setItem(KEY, tok);
    else window.localStorage.removeItem(KEY);
}

export function isClientAuthed() {
    return !!getClientToken();
}

export async function clientRequestMagic(email, company) {
    const { data } = await api.post("/client/auth/request-magic-link", { email, company });
    return data;
}

export async function clientVerify(token) {
    const { data } = await api.post("/client/auth/verify", { token });
    setClientToken(data.token);
    return data;
}

export async function clientMe() {
    const tok = getClientToken();
    if (!tok) throw new Error("not authenticated");
    const { data } = await api.get("/client/me", { headers: { Authorization: `Bearer ${tok}` } });
    return data;
}

export function clientLogout() {
    setClientToken(null);
}
