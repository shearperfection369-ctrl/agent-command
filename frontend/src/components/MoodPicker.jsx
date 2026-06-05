/**
 * MoodPicker — floating bottom-left widget that swaps JADE OS color/mood.
 * Persists to localStorage and applies via [data-theme] attribute on <html>.
 */
import { useEffect, useState } from "react";

const THEMES = [
  { id: "console",   label: "CONSOLE",   color: "#ccff00", desc: "Default · dark operator deck" },
  { id: "atlantean", label: "ATLANTEAN", color: "#6cf2ff", desc: "Bioluminescent · lab depths" },
  { id: "warm",      label: "WARM",      color: "#ffce4f", desc: "Amber · candlelit · easy on eyes" },
  { id: "contrast",  label: "HI-CONTRAST", color: "#ffffff", desc: "Maximum legibility" },
];

const STORAGE_KEY = "jadeos.theme";

export function MoodPicker() {
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem(STORAGE_KEY) || "console"; }
    catch { return "console"; }
  });

  useEffect(() => {
    const html = document.documentElement;
    if (theme === "console") {
      html.removeAttribute("data-theme");
    } else {
      html.setAttribute("data-theme", theme);
    }
    try { localStorage.setItem(STORAGE_KEY, theme); } catch (e) { /* ignore */ }
  }, [theme]);

  return (
    <div className="mood-picker" data-testid="mood-picker">
      <span className="mood-picker-label">MOOD</span>
      {THEMES.map((t) => (
        <button
          key={t.id}
          title={`${t.label} — ${t.desc}`}
          data-testid={`mood-${t.id}`}
          className={theme === t.id ? "is-active" : ""}
          onClick={() => setTheme(t.id)}
          style={{ background: t.color, color: t.color }}
          aria-label={`Switch to ${t.label} theme`}
        />
      ))}
    </div>
  );
}
