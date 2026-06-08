"""Programmatically verify the consulting audit PDF respects page margins.

This test:
  1. Builds a synthetic audit doc with INTENTIONALLY long/realistic strings
     in every dense field (executive summary, narrative, scope, rationale,
     mitigation, callout, etc.).
  2. Calls generate_audit_pdf() directly (no LLM, no DB).
  3. Uses pdfplumber to inspect the position of every drawn character
     and confirms nothing extends past the right or bottom margin.
  4. Also renders each page to a PNG so the operator can eyeball them.

Run:  python /app/backend/tests/test_audit_pdf_layout.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure /app/backend is on sys.path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("EMERGENT_LLM_KEY", "dummy")  # generate_audit_pdf does not use it

import pdfplumber  # type: ignore
import pypdfium2 as pdfium  # type: ignore

from consulting_audit import generate_audit_pdf  # noqa: E402


# Landscape letter: 792 × 612 pt.  Margins per consulting_audit.py:
PAGE_W = 792.0
PAGE_H = 612.0
MARGIN_L = 48.0
MARGIN_R = 48.0
MARGIN_B = 18.0   # footer text baseline=24; descender ~22.3 so allow 18
TOLERANCE = 1.0   # 1pt slack for rounding


LONG_STRING = (
    "This is a deliberately long string intended to stress the PDF text "
    "wrapping pipeline so that every dense paragraph in the audit deck has "
    "to break across multiple lines without ever crossing the right margin "
    "of the landscape-letter page. Logistics, freight brokerage, manufacturing, "
    "healthcare, SaaS — operators across verticals deserve consistent layout."
)


def synthetic_audit() -> dict:
    return {
        "id": "test_audit_layout_001",
        "company_name": "Lighthouse Logistics & Distribution International Holdings",
        "industry": "freight_brokerage",
        "operator_name": "Test Operator",
        "operator_email": "ops@lighthouse.test",
        "fleet_or_team_size": 24,
        "responses": {
            # Industry KPI ids for freight_brokerage (see INDUSTRY_KPIS)
            "FB-1": 4, "FB-2": 3, "FB-3": 5, "FB-4": 2, "FB-5": 4, "FB-6": 3,
        },
        "analysis": {
            "scores": {
                "overall_score": 72.0,
                "tier": "BUILDER",
                "tier_color": "#00ffff",
                "tier_blurb": (
                    "Solid foundation — you've built process discipline and have "
                    "real data to operate against. Now is the moment to layer "
                    "agents on top of the workflows you already trust, instead "
                    "of retraining the team on yet another dashboard."
                ),
                "dimension_scores": {
                    "DATA": 78, "PROCESS": 65, "TOOLS": 70,
                    "CHANGE": 60, "ROI": 80, "TECH": 75,
                },
            },
            "recommended_agents": [
                {"id": "JADE-001", "name": "Carrier Vetting Agent",
                 "rationale": LONG_STRING},
                {"id": "JADE-002", "name": "Quote Negotiation Agent",
                 "rationale": LONG_STRING},
                {"id": "JADE-003", "name": "Track-and-Trace Agent",
                 "rationale": "Cuts manual check-call labor by 80% with reliable "
                              "ELD + EDI ingestion and proactive exception flags."},
            ],
            "savings": {
                "annual_savings_central_usd": 285_000,
                "annual_savings_low_usd": 210_000,
                "annual_savings_high_usd": 360_000,
                "payback_months_estimate": 7,
                "size_used": 24,
            },
            "narrative": {
                "executive_summary": LONG_STRING + " " + LONG_STRING,
                "strengths": [
                    LONG_STRING,
                    "Operator-grade audit substrate ready on day one with full "
                    "chain-of-custody logging across every agent action.",
                    "Strong vertical fit · purpose-built agents for freight brokerage "
                    "that ingest your existing TMS, CRM and document store.",
                ],
                "gaps": [
                    LONG_STRING,
                    "Manual carrier vetting consuming 12+ team hours per week.",
                    "Limited structured data flow for downstream agent ingestion.",
                ],
                "pilot_proposal": {
                    "duration_days": 90,
                    "scope": LONG_STRING,
                    "success_metrics": [
                        "≥20% reduction in time-per-decision across the brokerage desk, "
                        "measured against a 30-day baseline captured in week one.",
                        "≥95% audit chain coverage of agent actions, exported daily "
                        "to the operator's review queue.",
                        "User satisfaction score ≥4.2/5 from the front-line dispatcher panel.",
                        "Documented ROI in the pilot exit memo, signed by the executive sponsor.",
                    ],
                    "team_required": "Executive sponsor + 1 ops lead + 1 IT/data contact + "
                                     "1 front-line dispatcher who actually runs the daily playbook.",
                    "investment_usd": 35000,
                },
                "risks": [
                    {"risk": LONG_STRING, "severity": "high",
                     "mitigation": LONG_STRING},
                    {"risk": "Change-management drag on rollout from front-line dispatchers.",
                     "severity": "med",
                     "mitigation": "Identify a front-line champion before pilot starts; "
                                   "give them direct slack channel to the operator."},
                ],
                "next_30_days": [
                    LONG_STRING,
                    "Identify executive sponsor + ops lead + IT contact.",
                    "Schedule a 60-minute data walk-through.",
                    "Cut a sandbox workspace in JadeOS for the pilot tenant.",
                ],
                "callout": "Build complete. Ready to deploy. Score: 72/100 · BUILDER. "
                           "Lead with the Carrier Vetting Agent on a 90-day pilot.",
            },
        },
    }


def check_pdf(pdf_bytes: bytes, out_dir: Path) -> list[str]:
    """Return list of violation strings. Empty list = pass."""
    violations: list[str] = []
    pdf_path = out_dir / "audit_layout_test.pdf"
    pdf_path.write_bytes(pdf_bytes)

    with pdfplumber.open(pdf_path) as pdf:
        assert len(pdf.pages) == 12, f"expected 12 pages, got {len(pdf.pages)}"
        for idx, page in enumerate(pdf.pages, start=1):
            chars = page.chars
            for ch in chars:
                x1 = ch["x1"]
                y0 = ch["y0"]
                if x1 > PAGE_W - MARGIN_R + TOLERANCE:
                    violations.append(
                        f"PAGE {idx:02d}: char {ch['text']!r} at x1={x1:.1f} "
                        f"exceeds right margin (limit {PAGE_W - MARGIN_R:.1f})"
                    )
                if y0 < MARGIN_B - TOLERANCE:
                    violations.append(
                        f"PAGE {idx:02d}: char {ch['text']!r} at y0={y0:.1f} "
                        f"below bottom margin (limit {MARGIN_B:.1f})"
                    )

    # Render PNGs for eyeball review
    doc = pdfium.PdfDocument(str(pdf_path))
    for i, page in enumerate(doc, start=1):
        bitmap = page.render(scale=1.5)
        pil = bitmap.to_pil()
        pil.save(out_dir / f"audit_page_{i:02d}.png")
    doc.close()
    return violations


def main() -> int:
    audit = synthetic_audit()
    pdf_bytes = generate_audit_pdf(audit)

    out_dir = Path("/tmp/audit_pdf_test")
    out_dir.mkdir(parents=True, exist_ok=True)

    violations = check_pdf(pdf_bytes, out_dir)
    print(f"PDF written: {out_dir / 'audit_layout_test.pdf'}  ({len(pdf_bytes):,} bytes)")
    print(f"Rendered PNGs: {out_dir}")
    if violations:
        print(f"\nFAIL · {len(violations)} margin violations:\n")
        # Cap output
        for v in violations[:30]:
            print("  " + v)
        if len(violations) > 30:
            print(f"  ... and {len(violations) - 30} more")
        return 1
    print("\nPASS · no text crosses margins on any page.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
