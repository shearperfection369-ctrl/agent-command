/**
 * SaveActions — small toolbar for AI output panels.
 * Lets older / less-technical users SAVE (download .txt or .json)
 * or PRINT (browser print dialog, uses print CSS already in index.css).
 *
 * Drop into any output panel:
 *   <SaveActions data={result} filename="jadeos-extract" kind="json" />
 *   <SaveActions data={email}  filename="jadeos-outreach" kind="txt" />
 */
import React from "react";
import { toast } from "sonner";

function stringify(data, kind) {
    if (data == null) return "";
    if (kind === "txt") return typeof data === "string" ? data : JSON.stringify(data, null, 2);
    return typeof data === "string" ? data : JSON.stringify(data, null, 2);
}

function timestamp() {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}`;
}

export function SaveActions({ data, filename = "jadeos-advice", kind = "txt", className = "" }) {
    if (data == null || data === "") return null;

    const onSave = () => {
        const body = stringify(data, kind);
        const ext = kind === "json" ? "json" : "txt";
        const mime = kind === "json" ? "application/json" : "text/plain";
        const blob = new Blob([body], { type: `${mime};charset=utf-8` });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${filename}-${timestamp()}.${ext}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        toast.success("Saved to your downloads.");
    };

    const onPrint = () => {
        window.print();
    };

    return (
        <div
            data-testid="save-actions"
            data-print-hide
            className={`save-actions inline-flex items-center gap-2 ${className}`}
        >
            <button
                type="button"
                data-testid="save-advice-btn"
                onClick={onSave}
                className="mono-label text-[#ccff00] hover:text-white border border-[#ccff00]/40 hover:border-[#ccff00] px-3 py-1.5 transition-colors"
                title="Download this advice as a file"
            >
                ↓ SAVE
            </button>
            <button
                type="button"
                data-testid="print-advice-btn"
                onClick={onPrint}
                className="mono-label text-[#00ffff] hover:text-white border border-[#00ffff]/40 hover:border-[#00ffff] px-3 py-1.5 transition-colors"
                title="Print this advice (uses your browser print dialog)"
            >
                ⎙ PRINT
            </button>
        </div>
    );
}

export default SaveActions;
