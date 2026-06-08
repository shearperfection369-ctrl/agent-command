/**
 * AuditPlaybook · /audit/playbook
 *
 * Operator-facing hub for the four PDF assets the founder uses on every audit.
 * Public — anyone with the URL can download. No auth gate (it's not sensitive).
 */
import { API_BASE } from "../lib/api";
import { CornerBrackets } from "../components/Brackets";

const ACCENT = {
    jade: "#ccff00", cyan: "#00ffff", violet: "#7c5cff", magenta: "#ff3b8a", amber: "#ffce4f",
};

const PDFS = [
    {
        id: "data-checklist",
        c: ACCENT.jade,
        eyebrow: "ASSET 01",
        label: "Data Checklist · 1-Pager",
        body: "The 8-item data packet the prospect needs to send before the audit. Drop it as an attachment on the cold email.",
        url: "/audit/data-checklist.pdf",
        cta: "DOWNLOAD CHECKLIST",
    },
    {
        id: "playbook",
        c: ACCENT.cyan,
        eyebrow: "ASSET 02",
        label: "Audit Playbook · 6-Page",
        body: "How to run the 30-question audit live. Prep checklist · talk track per dimension · scoring rubric · objection handling · post-audit handoff.",
        url: "/audit/playbook.pdf",
        cta: "DOWNLOAD PLAYBOOK",
    },
    {
        id: "letter",
        c: ACCENT.violet,
        eyebrow: "ASSET 03",
        label: "Data Request Letter · Drop-in Template",
        body: "Pre-signed letter you email a prospect 48 hours pre-audit. Bracketed fields you personalize.",
        url: "/audit/data-request-letter.pdf",
        cta: "DOWNLOAD LETTER",
    },
    {
        id: "agreement",
        c: ACCENT.magenta,
        eyebrow: "ASSET 04",
        label: "Pilot Engagement Agreement · 1-Page SOW",
        body: "Free 90-day pilot scope of work. Success metrics declared upfront. Light, signable, send same day as audit.",
        url: "/audit/engagement-agreement.pdf",
        cta: "DOWNLOAD AGREEMENT",
    },
];

export default function AuditPlaybook() {
    return (
        <div className="min-h-[80vh] py-12 px-6" data-testid="audit-playbook-page">
            <div className="max-w-5xl mx-auto">
                <div className="mono-label text-[10px] text-[#ccff00]">JADEOS · AUDIT PLAYBOOK · OPERATOR ASSETS</div>
                <h1 className="font-display font-black text-white text-4xl sm:text-5xl mt-2 tracking-tight">
                    Everything you need<br />
                    <span style={{ color: ACCENT.cyan }}>to run an audit in the room.</span>
                </h1>
                <p className="font-mono-tech text-[13px] text-white/65 mt-5 max-w-2xl leading-relaxed">
                    Four auto-generated PDFs. Print them. Email them. Bring them into the engagement.
                    Updated every time the audit engine changes — these are always in sync with the
                    live <code className="text-[#ccff00]">/api/audit/*</code> endpoints.
                </p>

                <div className="grid sm:grid-cols-2 gap-4 mt-10">
                    {PDFS.map((p) => (
                        <a key={p.id}
                           href={`${API_BASE}${p.url}`}
                           target="_blank" rel="noreferrer"
                           data-testid={`playbook-${p.id}`}
                           className="relative border p-5 bg-[#0a0c18] hover:bg-[#0e1126] transition group"
                           style={{ borderColor: `${p.c}44` }}>
                            <CornerBrackets />
                            <div className="mono-label text-[10px]" style={{ color: p.c }}>{p.eyebrow}</div>
                            <div className="font-display font-black text-white text-lg mt-2 leading-tight">{p.label}</div>
                            <div className="font-mono-tech text-[11.5px] text-white/65 mt-2 leading-relaxed">{p.body}</div>
                            <div className="mono-label text-[10px] mt-4 inline-flex items-center gap-1.5 group-hover:underline"
                                 style={{ color: p.c }}>
                                ↓ {p.cta}
                            </div>
                        </a>
                    ))}
                </div>

                <div className="mt-12 relative border border-[#7c5cff44] p-6 bg-[#7c5cff08]">
                    <CornerBrackets />
                    <div className="mono-label text-[10px] text-[#7c5cff] mb-2">HOW TO USE THESE IN ORDER</div>
                    <ol className="space-y-2.5">
                        {[
                            "Send the Data Checklist as the attachment on your first cold email (broker outreach).",
                            "When they reply YES, send the Data Request Letter 48 hours before the call.",
                            "Print the Audit Playbook. Bring it into the room. Run the 30 questions live.",
                            "Walk out with the Engagement Agreement signed if the audit comes back BUILDER+.",
                        ].map((s, i) => (
                            <li key={i} className="grid grid-cols-[32px_1fr] gap-2 items-start">
                                <span className="font-display font-black text-[#7c5cff] text-lg leading-none">{i + 1}</span>
                                <span className="font-mono-tech text-[12px] text-white/85 leading-relaxed">{s}</span>
                            </li>
                        ))}
                    </ol>
                </div>

                <div className="mt-8 flex gap-3 flex-wrap">
                    <a href="/audit" className="mono-label text-[10px] text-[#ccff00] hover:underline">▶ START A NEW AUDIT</a>
                    <a href="/audit/broker-free" className="mono-label text-[10px] text-[#00ffff] hover:underline">▶ PUBLIC BROKER FREE-AUDIT LANDING</a>
                    <a href="/admin?tab=audits" className="mono-label text-[10px] text-[#7c5cff] hover:underline">▶ ADMIN · AUDIT LOG</a>
                    <a href="/admin?tab=outreach" className="mono-label text-[10px] text-[#ff3b8a] hover:underline">▶ ADMIN · OUTREACH CAMPAIGNS</a>
                </div>
            </div>
        </div>
    );
}
