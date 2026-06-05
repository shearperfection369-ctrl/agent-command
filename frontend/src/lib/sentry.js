/**
 * Sentry scaffold — initialized once at app boot from /src/App.js.
 *
 * Activation:
 *   1. Drop a DSN in /app/frontend/.env as REACT_APP_SENTRY_DSN=https://...@sentry.io/...
 *   2. `yarn add @sentry/react`
 *   3. Restart frontend. Errors auto-flow to Sentry.
 *
 * No DSN → initSentry() returns false and the rest of the app is unaffected.
 */

let _initialized = false;

export function isSentryConfigured() {
    return !!(process.env.REACT_APP_SENTRY_DSN || "").trim();
}

export async function initSentry() {
    if (_initialized) return true;
    const dsn = (process.env.REACT_APP_SENTRY_DSN || "").trim();
    if (!dsn) {
        // eslint-disable-next-line no-console
        console.info("[sentry] scaffold present · DSN not set · skipping init");
        return false;
    }
    try {
        // Dynamic import keeps the bundle clean when not wired.
        const Sentry = await import("@sentry/react");
        Sentry.init({
            dsn,
            environment: process.env.REACT_APP_SENTRY_ENV || "preview",
            release: process.env.REACT_APP_SENTRY_RELEASE || "jadeos@dev",
            tracesSampleRate: parseFloat(process.env.REACT_APP_SENTRY_TRACES || "0.1"),
            sendDefaultPii: false,
        });
        _initialized = true;
        // eslint-disable-next-line no-console
        console.info("[sentry] initialized");
        return true;
    } catch (e) {
        // eslint-disable-next-line no-console
        console.warn("[sentry] init failed — run `yarn add @sentry/react`", e);
        return false;
    }
}

export function captureException(err) {
    if (!_initialized) {
        // eslint-disable-next-line no-console
        console.warn("[sentry] (local) exception", err);
        return;
    }
    try {
        // eslint-disable-next-line no-undef
        import("@sentry/react").then((S) => S.captureException(err));
    } catch (e) {
        // eslint-disable-next-line no-console
        console.warn("[sentry] capture failed", e);
    }
}
