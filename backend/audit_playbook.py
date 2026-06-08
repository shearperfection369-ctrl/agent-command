"""JadeOS · Audit playbook + data-request + engagement PDFs (auto-generated via reportlab).

These are operator-facing assets you bring into a client engagement:

  • GET /api/audit/data-checklist.pdf        — 1-pager: exactly what data to ask the prospect for
  • GET /api/audit/playbook.pdf              — full operator playbook (prep, talk track, scoring)
  • GET /api/audit/data-request-letter.pdf   — drop-in client email/letter template
  • GET /api/audit/engagement-agreement.pdf  — light scope-of-work (free pilot terms)

Same visual language as the pitch deck (dark theme, lime/cyan/violet accents).
"""
from __future__ import annotations

import io
from datetime import datetime, timezone

from fastapi import APIRouter, Response
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import landscape, letter, portrait
from reportlab.pdfgen import canvas

playbook_router = APIRouter(prefix="/audit", tags=["audit-playbook"])

BG = HexColor("#06070d")
JADE = HexColor("#ccff00")
CYAN = HexColor("#00ffff")
VIOLET = HexColor("#7c5cff")
MAGENTA = HexColor("#ff3b8a")
AMBER = HexColor("#ffce4f")
WHITE_DIM = HexColor("#cccccc")


def _wrap(text: str, width: int = 95):
    words, line, lines = text.split(" "), [], []
    for w in words:
        if sum(len(s) + 1 for s in line) + len(w) > width:
            lines.append(" ".join(line)); line = [w]
        else:
            line.append(w)
    if line:
        lines.append(" ".join(line))
    return lines


def _new_page(c, page_n, total, accent, title_text):
    c.setFillColor(BG)
    c.rect(0, 0, c._pagesize[0], c._pagesize[1], fill=1, stroke=0)
    c.setFillColor(accent)
    c.rect(0, c._pagesize[1] - 24, c._pagesize[0], 4, fill=1, stroke=0)
    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(48, c._pagesize[1] - 70, title_text)
    c.setFillColor(HexColor("#777777"))
    c.setFont("Helvetica", 8)
    c.drawString(48, 24, "JadeOS · AI Readiness Audit · onejades.com · founder@jadeos.ai")
    c.drawRightString(c._pagesize[0] - 48, 24, f"{page_n:02d} / {total:02d}")


def _draw_body(c, lines, y_start, color=WHITE_DIM, size=11, x=48, leading=14):
    c.setFillColor(color)
    c.setFont("Helvetica", size)
    y = y_start
    for ln in lines:
        c.drawString(x, y, ln)
        y -= leading
    return y


def _bullets(c, items, y_start, color=WHITE_DIM, size=11, x=60, leading=16):
    c.setFont("Helvetica", size)
    y = y_start
    for it in items:
        c.setFillColor(JADE)
        c.drawString(x, y, "▸")
        c.setFillColor(white)
        for i, ln in enumerate(_wrap(it, width=90)):
            c.drawString(x + 18, y - i * 13, ln)
        y -= leading + 13 * (len(_wrap(it, width=90)) - 1)
    return y


# ============================================================
# 1 · DATA CHECKLIST · 1-pager for the broker
# ============================================================

def _data_checklist_pdf() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=portrait(letter))
    PW, PH = portrait(letter)

    # Cover header
    c.setFillColor(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
    c.setFillColor(JADE); c.rect(0, PH - 20, PW, 4, fill=1, stroke=0)
    c.setFillColor(JADE); c.setFont("Helvetica-Bold", 26); c.drawString(48, PH - 70, "Free 90-Day AI Readiness Audit")
    c.setFillColor(CYAN); c.setFont("Helvetica", 12); c.drawString(48, PH - 92, "For Freight Brokers · Data Checklist")
    c.setFillColor(WHITE_DIM); c.setFont("Helvetica", 10); c.drawString(48, PH - 110, "JadeOS · Minneapolis · founder@jadeos.ai · onejades.com")

    # Why
    c.setFillColor(VIOLET); c.setFont("Helvetica-Bold", 14); c.drawString(48, PH - 150, "WHY THIS AUDIT")
    body = (
        "30 questions · 6 dimensions of AI readiness · industry-specific KPIs. "
        "You walk away with a 12-page PowerPoint-style report scored 0-100, "
        "recommended JadeOS agents, a 90-day pilot proposal with success metrics, "
        "and an estimated annual savings number. Cost: $0. No obligation."
    )
    _draw_body(c, _wrap(body, width=85), PH - 175, size=11)

    # What we need
    c.setFillColor(JADE); c.setFont("Helvetica-Bold", 14); c.drawString(48, PH - 260, "WHAT WE NEED FROM YOU")
    items = [
        "LOAD HISTORY · last 90 days as CSV — pickup/delivery, lane, miles, rate, carrier, cost, customer",
        "CARRIER ROSTER · current active carrier list with MC numbers + lanes covered",
        "QUOTE LOGS · last 90 days — won/lost flag + booked rate vs ask rate",
        "CUSTOMER LIST · top 25 by revenue · contact + monthly load count",
        "OPS HEADCOUNT · roles, FTE count, hourly or salaried, full or part-time",
        "CURRENT TOOLS / TMS · what software runs the desk today (TMS · CRM · accounting · phone)",
        "MONTHLY P&L SUMMARY · last 3 months · gross margin · driver/carrier pay · ops cost",
        "WORKFLOW PAIN · 3 sentences from you: where is the team drowning?",
    ]
    y = PH - 285
    y = _bullets(c, items, y, size=11, leading=18)

    # How we handle it
    c.setFillColor(CYAN); c.setFont("Helvetica-Bold", 14); c.drawString(48, y - 10, "DATA HANDLING · NO BS")
    body2 = (
        "Files are encrypted at rest, never shared with third parties. We sign an NDA before any "
        "data is exchanged if you'd like one. Audit complete in 5-7 business days from receipt."
    )
    _draw_body(c, _wrap(body2, width=85), y - 35, size=10)

    # CTA
    c.setFillColor(JADE); c.setFont("Helvetica-Bold", 16); c.drawString(48, 140, "Send your packet to · founder@jadeos.ai")
    c.setFillColor(WHITE_DIM); c.setFont("Helvetica", 11)
    c.drawString(48, 120, "Subject: 'Free Audit · {your_company_name}'")
    c.drawString(48, 100, "Or schedule a 30-minute walk-through · text +1 (763) 443-6659")

    # Footer
    c.setFillColor(VIOLET); c.setFont("Helvetica-Bold", 10)
    c.drawString(48, 60, "JadeOS · operator-grade AI for freight · built by a 13-year operator.")
    c.setFillColor(HexColor("#666"))
    c.drawString(48, 44, f"Generated · {datetime.now(timezone.utc).strftime('%B %d, %Y')}")
    c.showPage(); c.save()
    return buf.getvalue()


# ============================================================
# 2 · AUDIT PLAYBOOK · operator-facing how-to
# ============================================================

def _playbook_pdf() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(letter))
    PW, PH = landscape(letter)
    total = 6

    # ----- Page 1 · Cover -----
    c.setFillColor(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
    c.setFillColor(JADE); c.setFont("Helvetica-Bold", 52); c.drawString(48, PH - 180, "Audit Playbook")
    c.setFillColor(white); c.setFont("Helvetica-Bold", 22); c.drawString(48, PH - 220, "How to run a JadeOS AI Readiness Audit.")
    c.setFillColor(CYAN); c.setFont("Helvetica", 14); c.drawString(48, PH - 250, "Operator-facing · prep, talk track, scoring, objection handling, handoff.")
    c.setFillColor(WHITE_DIM); c.setFont("Helvetica", 10); c.drawString(48, 50, "JadeOS · onejades.com · 01 of 06")
    c.showPage()

    # ----- Page 2 · Prep -----
    _new_page(c, 2, total, CYAN, "01 · PREP · 24 HOURS BEFORE")
    prep_items = [
        "Confirm the audit window · pick a 60-minute slot · book a quiet room or call line.",
        "Send the Data Request Letter (next PDF) 48 hours ahead · ask for the 8-item packet.",
        "Pull a current JadeOS demo URL · have /demo?tab=quantum and /demo?tab=tms tabs ready.",
        "Read the prospect's website + LinkedIn · know their 3 biggest customers + 2 biggest pains.",
        "Open the audit at /audit · pre-fill company name, industry, fleet/team size.",
        "Bring the printed 12-page sample report from a similar-tier company (anonymized).",
    ]
    _bullets(c, prep_items, PH - 130, size=12)
    c.showPage()

    # ----- Page 3 · Talk Track by Dimension -----
    _new_page(c, 3, total, JADE, "02 · TALK TRACK · ONE BLOCK PER DIMENSION")
    talk = [
        ("DATA", "Open with 'Walk me through how your operations data flows today.' Listen for words like 'spreadsheet', 'email thread', 'whiteboard' — score lower. Listen for 'API', 'real-time', 'dashboard' — score higher."),
        ("PROCESS", "Ask 'How many repetitive decisions does the team make per day that follow the same script?' Count out loud. >100/day = score 5."),
        ("TOOLS", "Ask what runs the desk today. Modern + cloud + API = 4-5. Spreadsheets + paper + on-prem = 1-2."),
        ("CHANGE", "Read body language. Skeptical leadership = 1-2. Active champion in the room = 5."),
        ("ROI", "Ask annual labor spend on the targeted workflow. >$1M/yr = 4-5. <$250k = 1-2."),
        ("TECH", "Ask 'Do you have in-house IT?' and 'Are you SOC 2 / HIPAA?' Adjust accordingly."),
    ]
    y = PH - 130
    for k, v in talk:
        c.setFillColor(JADE); c.setFont("Helvetica-Bold", 12); c.drawString(48, y, k)
        c.setFillColor(white); c.setFont("Helvetica", 10.5)
        for i, ln in enumerate(_wrap(v, width=130)):
            c.drawString(110, y - i * 13, ln)
        y -= 13 * len(_wrap(v, width=130)) + 8
    c.showPage()

    # ----- Page 4 · Scoring Rubric -----
    _new_page(c, 4, total, VIOLET, "03 · SCORING RUBRIC · 1-5 LIKERT")
    rubric = [
        ("1 · VERY LOW",  "Multiple critical gaps. Manual. Resistant culture. Score 0-25%."),
        ("2 · LOW",       "Mostly manual with islands of automation. Score 25-40%."),
        ("3 · MEDIUM",    "Mixed maturity. Some structure, some chaos. Score 40-60%."),
        ("4 · HIGH",      "Most processes structured + measured. Score 60-80%."),
        ("5 · VERY HIGH", "Best-in-class. Real-time, instrumented, automated. Score 80-100%."),
    ]
    y = PH - 130
    for k, v in rubric:
        c.setFillColor(VIOLET); c.setFont("Helvetica-Bold", 12); c.drawString(48, y, k)
        c.setFillColor(white); c.setFont("Helvetica", 11)
        c.drawString(220, y, v)
        y -= 30
    c.setFillColor(WHITE_DIM); c.setFont("Helvetica", 10)
    c.drawString(48, y - 20, "Tip · the LLM synthesis layer expects a SPREAD of scores. If every answer is a 4, the tier ")
    c.drawString(48, y - 35, "comes out flat-line PIONEER and the gaps section feels weak. Don't game the rubric.")
    c.showPage()

    # ----- Page 5 · Objection Handling -----
    _new_page(c, 5, total, MAGENTA, "04 · OBJECTION HANDLING")
    obj = [
        ("'We tried AI last year. Didn't work.'",
         "Response: 'What you tried was a chatbot wrapper. JadeOS is operator-grade — purpose-built per "
         "vertical, with audit chain, persistent memory, and a 90-day pilot scoped before you sign.'"),
        ("'We can't share that data.'",
         "Response: 'You don't have to share it to start the audit. Score yourself on the 30 questions "
         "and we'll do a desk audit. Data exchange happens after we mutually decide to pilot.'"),
        ("'How is this different from Salesforce / RPA / ChatGPT?'",
         "Response: 'Three things — voice-first capture, persistent multi-modal memory across modules, "
         "and operator-grade audit chain. None of the above ship those three together.'"),
        ("'We need to talk to references.'",
         "Response: 'Here's our Lighthouse pilot tier. First 5 customers get founder-led implementation. "
         "References after pilot kickoff — you'd be one of them.'"),
        ("'What does this cost?'",
         "Response: 'Pilot is $35k flat, 90 days, success metrics declared upfront. Production license "
         "is per-seat after pilot. Audit itself is free.'"),
    ]
    y = PH - 130
    for q, a in obj:
        c.setFillColor(MAGENTA); c.setFont("Helvetica-Bold", 11); c.drawString(48, y, q[:120])
        c.setFillColor(white); c.setFont("Helvetica", 10)
        for i, ln in enumerate(_wrap(a, width=120)):
            c.drawString(48, y - 14 - i * 12, ln)
        y -= 14 + 12 * len(_wrap(a, width=120)) + 12
    c.showPage()

    # ----- Page 6 · Handoff -----
    _new_page(c, 6, total, AMBER, "05 · POST-AUDIT HANDOFF")
    handoff = [
        "Run /api/audit/{id}/analyze the moment they leave the room — synthesis takes 15 seconds.",
        "Download the 12-page PDF · email within 60 minutes of the meeting · subject 'Your JadeOS audit · {company}'.",
        "Schedule the follow-up call before they leave the room. 5 business days out.",
        "If tier = PIONEER or BUILDER · attach the 90-day pilot agreement (engagement-agreement.pdf).",
        "If tier = CURIOUS or LEARNING · attach the consulting proposal · lead with data + process hygiene.",
        "Log the meeting in admin · /admin → AI READINESS AUDIT tab · note score + tier + next step.",
    ]
    _bullets(c, handoff, PH - 130, size=12)
    c.setFillColor(JADE); c.setFont("Helvetica-Bold", 16); c.drawString(48, 100, "Ready to deploy. ▸ onejades.com")
    c.showPage(); c.save()
    return buf.getvalue()


# ============================================================
# 3 · DATA REQUEST LETTER · drop-in client letter
# ============================================================

def _data_request_letter_pdf() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=portrait(letter))
    PW, PH = portrait(letter)

    c.setFillColor(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
    c.setFillColor(JADE); c.rect(0, PH - 20, PW, 4, fill=1, stroke=0)

    c.setFillColor(white); c.setFont("Helvetica-Bold", 22); c.drawString(48, PH - 70, "JadeOS · Data Request Letter")
    c.setFillColor(CYAN); c.setFont("Helvetica", 11); c.drawString(48, PH - 92, "Drop-in template · personalize the bracketed fields · send to prospect 48 hours pre-audit.")

    body = (
        "Subject: Your Free AI Readiness Audit · [PROSPECT COMPANY]\n\n"
        "[FIRST NAME],\n\n"
        "Thanks for agreeing to the audit. Below is the packet I'll need to deliver the strongest report.\n\n"
        "WHAT TO SEND BACK (any format you have — CSV, PDF export, screenshots, whatever's easy):\n\n"
        "  1. LOAD HISTORY · last 90 days · pickup, delivery, lane, miles, rate, carrier, cost, customer.\n"
        "  2. CARRIER ROSTER · current active carriers with MC numbers + lanes covered.\n"
        "  3. QUOTE LOGS · last 90 days · won/lost flag · booked vs ask rate.\n"
        "  4. CUSTOMER LIST · top 25 by revenue · contact + monthly load count.\n"
        "  5. OPS HEADCOUNT · roles, FTE count, hourly or salaried.\n"
        "  6. CURRENT TOOLS · TMS, CRM, accounting, phone system.\n"
        "  7. MONTHLY P&L SUMMARY · last 3 months · gross margin, carrier pay, ops cost.\n"
        "  8. 3-SENTENCE PAIN STATEMENT · where is the team drowning right now?\n\n"
        "DATA HANDLING\n"
        "Files encrypted at rest. Not shared with third parties. NDA on request — happy to sign.\n\n"
        "WHAT YOU GET\n"
        "12-page audit report. AI Readiness Score (0-100). Recommended agents. 90-day pilot proposal "
        "with success metrics declared upfront. Annual savings estimate. Delivered within 5-7 business "
        "days of receipt.\n\n"
        "Cost: $0. No obligation.\n\n"
        "Reply to this email with the packet, or text me at +1 (763) 443-6659 to walk through it.\n\n"
        "Oliver Cummins · Founder · JadeOS\n"
        "founder@jadeos.ai · onejades.com\n"
        "linkedin.com/in/oliver-cummins-a27304a3/"
    )
    c.setFillColor(white); c.setFont("Helvetica", 10.5)
    y = PH - 130
    for line in body.split("\n"):
        if y < 80:
            c.showPage()
            c.setFillColor(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
            c.setFillColor(white); c.setFont("Helvetica", 10.5)
            y = PH - 70
        c.drawString(48, y, line[:100])
        y -= 13
    c.showPage(); c.save()
    return buf.getvalue()


# ============================================================
# 4 · ENGAGEMENT AGREEMENT · light SOW for free pilot
# ============================================================

def _engagement_agreement_pdf() -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=portrait(letter))
    PW, PH = portrait(letter)

    c.setFillColor(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
    c.setFillColor(VIOLET); c.rect(0, PH - 20, PW, 4, fill=1, stroke=0)
    c.setFillColor(VIOLET); c.setFont("Helvetica-Bold", 22); c.drawString(48, PH - 70, "JadeOS · Pilot Engagement Agreement")
    c.setFillColor(CYAN); c.setFont("Helvetica", 11); c.drawString(48, PH - 92, "1-page scope of work · free 90-day pilot · success metrics declared upfront.")

    sections = [
        ("PARTIES", "JadeOS (provider · Oliver Cummins · Minneapolis MN) AND [CLIENT COMPANY] (client)."),
        ("SCOPE", "Provider will deploy [SELECTED AGENT(S)] from the JadeOS-Agent Suite on client's "
                  "highest-density workflow, identified during the AI Readiness Audit, for a 90-day "
                  "pilot period beginning [START DATE]."),
        ("INVESTMENT", "$0 for the free audit-driven pilot tier (Lighthouse program · first 5 clients). "
                       "Standard pilot pricing is $35,000 flat for 90 days · waived for this engagement."),
        ("SUCCESS METRICS", "Declared in writing before kickoff. Typical pilot exit criteria:\n"
                            "  • >=20% reduction in time-per-decision on targeted workflow\n"
                            "  • >=95% audit chain coverage of agent actions\n"
                            "  • User satisfaction score >=4.2/5 from front-line team\n"
                            "  • Documented ROI in pilot exit memo"),
        ("CLIENT RESPONSIBILITIES", "Identify executive sponsor + 1 ops lead + 1 IT contact. Provide "
                                     "read access to operational data needed for agent training. Commit "
                                     "≥4 hours/week for the first 14 days for setup + tuning."),
        ("PROVIDER RESPONSIBILITIES", "Deploy + tune agents in JadeOS sandbox. Weekly 30-minute pilot "
                                       "review call. Full audit chain. Free production migration if "
                                       "success metrics are met."),
        ("DATA + IP", "Client retains all rights to client data. Provider retains all rights to "
                      "JadeOS platform IP. Aggregate/anonymized usage telemetry permitted."),
        ("CONFIDENTIALITY", "Mutual NDA covering all data + product details exchanged during pilot. "
                            "90-day survival post-engagement."),
        ("TERM + TERMINATION", "Effective on signature. Term: 90 days. Either party may terminate "
                                "with 7 days written notice. No penalty."),
        ("CONTINUATION", "If success metrics met at day 90, client may sign a production license at "
                         "$[NEGOTIATED]/seat/month with the audit chain + agents already in place."),
    ]
    c.setFillColor(white); c.setFont("Helvetica", 10)
    y = PH - 130
    for title_t, body_t in sections:
        if y < 100:
            c.showPage()
            c.setFillColor(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
            y = PH - 70
        c.setFillColor(JADE); c.setFont("Helvetica-Bold", 11); c.drawString(48, y, title_t)
        c.setFillColor(white); c.setFont("Helvetica", 10)
        for ln in body_t.split("\n"):
            for sub in _wrap(ln, width=92):
                y -= 13
                c.drawString(48, y, sub)
        y -= 10

    # Signature block
    if y < 130:
        c.showPage()
        c.setFillColor(BG); c.rect(0, 0, PW, PH, fill=1, stroke=0)
        y = PH - 80
    c.setFillColor(CYAN); c.setFont("Helvetica-Bold", 12); c.drawString(48, y - 30, "SIGNATURES")
    c.setFillColor(WHITE_DIM); c.setFont("Helvetica", 10)
    c.drawString(48,  y - 60, "Oliver Cummins · JadeOS                    ___________________________   Date: __________")
    c.drawString(48,  y - 90, "[CLIENT NAME] · [TITLE] · [COMPANY]         ___________________________   Date: __________")
    c.showPage(); c.save()
    return buf.getvalue()


# ============================================================
# ROUTES
# ============================================================

def _resp(pdf: bytes, filename: str) -> Response:
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@playbook_router.get("/data-checklist.pdf")
async def get_data_checklist():
    return _resp(_data_checklist_pdf(), "JadeOS_Free_Audit_Data_Checklist.pdf")


@playbook_router.get("/playbook.pdf")
async def get_playbook():
    return _resp(_playbook_pdf(), "JadeOS_Audit_Playbook.pdf")


@playbook_router.get("/data-request-letter.pdf")
async def get_data_request_letter():
    return _resp(_data_request_letter_pdf(), "JadeOS_Data_Request_Letter.pdf")


@playbook_router.get("/engagement-agreement.pdf")
async def get_engagement_agreement():
    return _resp(_engagement_agreement_pdf(), "JadeOS_Pilot_Engagement_Agreement.pdf")
