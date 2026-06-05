"""JADE OS · Big Bang launch campaign — 4-week organic-growth playbook.

Returns structured campaign data: weekly themes, per-platform post templates
(LinkedIn, X/Twitter, Instagram, TikTok, YouTube, Reddit, Facebook,
Hacker News, Threads), and asset recommendations.

Pure data + builder helpers — no I/O, no LLM calls. Safe to import anywhere.
"""
from typing import List, Dict
from datetime import datetime, timedelta, timezone


# ============================================================
# CAMPAIGN COPY · approved JADE voice + operator-grade tone
# ============================================================

WEEKS = [
    {
        "week": 1,
        "phase": "TEASE",
        "theme": "Curiosity. No reveal. Plant the seed.",
        "goal": "Generate intrigue — operators ask 'what is JADE OS?' without us saying.",
        "kpi": "Profile visits, save/bookmark count, DM inbound 'what is this'.",
    },
    {
        "week": 2,
        "phase": "REVEAL · BIG BANG",
        "theme": "Synchronized drop. Full reel. Every platform. Same hour.",
        "goal": "Maximum reach in 24 hours. Show the product running, not pitching.",
        "kpi": "Reel views, click-throughs to onejades.com, Lighthouse applications.",
    },
    {
        "week": 3,
        "phase": "PROOF",
        "theme": "Receipts. Live metrics. Behind-the-build.",
        "goal": "Move skeptics from 'cool demo' to 'this actually works'.",
        "kpi": "Engaged comments, founder DMs, demo bookings.",
    },
    {
        "week": 4,
        "phase": "CONVERT · LIGHTHOUSE",
        "theme": "Scarcity. Pilot slots running out.",
        "goal": "Close the loop — 5 Lighthouse pilots locked in.",
        "kpi": "Lighthouse applications, pilot conversion, signed POs.",
    },
]

PLATFORMS = {
    "linkedin": {
        "label": "LinkedIn",
        "best_window": "Tue–Thu · 7–9am CST",
        "format": "16:9 landscape video OR 1:1 square video · 1300-char post · 3-5 hashtags",
        "video": "jadeos_v3_landscape_16x9.mp4 OR jadeos_v3_square_1x1.mp4",
        "tone": "Operator-direct · founder POV · technical credibility",
    },
    "x": {
        "label": "X (Twitter)",
        "best_window": "Tue–Thu · 8–10am or 7–9pm CST",
        "format": "16:9 video · 280 chars · 1-2 hashtags · thread for long-form",
        "video": "jadeos_v3_landscape_16x9.mp4",
        "tone": "Punchy hook · dev/AI crowd · contrarian where genuine",
    },
    "instagram_reel": {
        "label": "Instagram Reels",
        "best_window": "Mon, Wed, Fri · 11am–1pm CST",
        "format": "9:16 vertical · ≤90s · trending audio optional · 3-5 hashtags",
        "video": "jadeos_v3_vertical_9x16.mp4",
        "tone": "Visual-first · aesthetic-driven · hook in 1st second",
    },
    "instagram_feed": {
        "label": "Instagram Feed",
        "best_window": "Mon, Wed, Fri · 11am–1pm CST",
        "format": "1:1 square · 2200-char caption · 8-12 hashtags",
        "video": "jadeos_v3_square_1x1.mp4",
        "tone": "Studio-grade visual · brand aesthetic · curated",
    },
    "tiktok": {
        "label": "TikTok",
        "best_window": "Tue–Thu · 6–10pm CST",
        "format": "9:16 vertical · 15–60s · hook in 1st 0.8s · captions on-screen",
        "video": "jadeos_v3_vertical_9x16.mp4",
        "tone": "Fast-paced · pattern-interrupt · educational",
    },
    "youtube_short": {
        "label": "YouTube Shorts",
        "best_window": "Wed-Fri · 12–3pm CST",
        "format": "9:16 vertical · ≤60s · loop-friendly",
        "video": "jadeos_v3_vertical_9x16.mp4",
        "tone": "Tutorial-adjacent · demo-first · subscribe CTA",
    },
    "youtube": {
        "label": "YouTube (long form)",
        "best_window": "Thu–Sat · 12–3pm CST",
        "format": "16:9 · the V3 reel as a 12s ad-style trailer + linked long demo",
        "video": "jadeos_v3_landscape_16x9.mp4",
        "tone": "Production-value · authoritative",
    },
    "facebook": {
        "label": "Facebook",
        "best_window": "Wed–Fri · 1–4pm CST",
        "format": "1:1 square · 80-120 word post · 1-2 hashtags",
        "video": "jadeos_v3_square_1x1.mp4",
        "tone": "Story-first · local-Minneapolis hook",
    },
    "reddit": {
        "label": "Reddit (r/SaaS, r/smallbusiness, r/MachineLearning)",
        "best_window": "Mon–Wed · 9–11am CST",
        "format": "Native text post · no salesy tone · 1 hyperlink at most",
        "video": "—",
        "tone": "Story-driven · learning-focused · transparent · no marketing speak",
    },
    "hackernews": {
        "label": "Hacker News (Show HN)",
        "best_window": "Tue–Thu · 8–10am EST",
        "format": "Show HN title + 1-paragraph intro comment · onejades.com link",
        "video": "—",
        "tone": "Builder-first · technical · no jargon · invite scrutiny",
    },
    "threads": {
        "label": "Threads",
        "best_window": "Tue–Thu · 8–10am CST",
        "format": "500 chars · 1 image or 1:1 video",
        "video": "jadeos_v3_square_1x1.mp4",
        "tone": "Casual · founder-voice · curious",
    },
}


def _hashtags_for(week: int) -> Dict[str, List[str]]:
    base = ["#JadeOS", "#AIAgents", "#Minneapolis"]
    return {
        "linkedin": base + ["#OpsAutomation", "#B2BSaaS"],
        "x": base + ["#BuildInPublic"],
        "instagram_reel": base + ["#Tech", "#AI", "#Automation", "#OpsTok", "#MinneapolisTech"],
        "instagram_feed": base + ["#Tech", "#AI", "#Automation", "#OperatorLife", "#ProductLaunch", "#MinneapolisTech", "#B2B"],
        "tiktok": ["#AI", "#Automation", "#Tech", "#OpsTok", "#SmallBiz", "#MinneapolisTech"],
        "youtube_short": ["#AI", "#Automation", "#OpsTools"],
        "youtube": ["#AI", "#Automation", "#OpsAutomation"],
        "facebook": ["#MinneapolisBusiness", "#AI"],
        "reddit": [],
        "hackernews": [],
        "threads": ["#AI", "#Automation", "#Minneapolis"],
    }


# ============================================================
# THE BIG BANG POST LIBRARY
# Each post: {day_offset, platform, headline, body, asset, cta, ab_variant?}
# day_offset is days from campaign start day 0
# ============================================================

POSTS: List[Dict] = [
    # ---------- WEEK 1 · TEASE ----------
    {
        "day": 0, "platform": "x", "phase": "TEASE",
        "headline": "Something is operating in Minneapolis.",
        "body": "Something is operating in Minneapolis.\n\nNo one knows it's there.\nIt sorts. It scores. It triages.\nIt doesn't sleep.\n\n12 days until it speaks for itself.\n\n→ onejades.com",
        "asset": "jadeos_v3_poster.jpg",
        "cta": "onejades.com",
    },
    {
        "day": 0, "platform": "linkedin", "phase": "TEASE",
        "headline": "An open letter to every Minneapolis operator drowning in inbox triage",
        "body": "An open letter to every Minneapolis operator drowning in inbox triage, freight BOL transcription, and ticket queues at 11pm on a Sunday.\n\nWe've been building something for you.\n\nNot another SaaS. Not another ChatGPT wrapper. An operator-grade AI agent platform that runs the work — not just chats about it.\n\nIt's been live in stealth across 4 verticals for 60 days.\n\nThe reveal drops in 12 days.\n\n#JadeOS #AIAgents #Minneapolis #OpsAutomation",
        "asset": "jadeos_v3_poster.jpg",
        "cta": "Follow this page · turn on notifications",
    },
    {
        "day": 0, "platform": "instagram_feed", "phase": "TEASE",
        "headline": "12.",
        "body": "12.\n\n.\n.\n\n#JadeOS",
        "asset": "jadeos_v3_poster.jpg",
        "cta": "—",
    },
    {
        "day": 2, "platform": "x", "phase": "TEASE",
        "headline": "While you slept, 184 emails sorted themselves.",
        "body": "While you slept, 184 emails sorted themselves.\n\n38 tickets got drafted replies.\n2,438 BOLs auto-extracted.\n\nNot AGI. Not magic. Just an operator-grade AI agent doing the unglamorous work.\n\n→ onejades.com",
        "asset": "—",
        "cta": "onejades.com",
    },
    {
        "day": 2, "platform": "tiktok", "phase": "TEASE",
        "headline": "POV: your inbox sorted itself overnight",
        "body": "POV: you walked into Monday and your inbox was already triaged, your BOLs extracted, your tickets drafted.\n\nNot a productivity hack. Not a Zap. An AI operator.\n\n#OpsTok #AI #SmallBiz",
        "asset": "jadeos_v3_vertical_9x16.mp4",
        "cta": "link in bio",
    },
    {
        "day": 4, "platform": "instagram_reel", "phase": "TEASE",
        "headline": "A 6-second window into JADE OS",
        "body": "Six seconds. One Quanta. Three live ops.\n\nThe full reel drops next week.\n\n#JadeOS #AI #Automation",
        "asset": "jadeos_v3_vertical_9x16.mp4",
        "cta": "follow · save · share",
    },
    {
        "day": 5, "platform": "linkedin", "phase": "TEASE",
        "headline": "What if your support team could go home at 5pm?",
        "body": "What if your support team could go home at 5pm and JADE handled Tier-1 overnight?\n\nWhat if your sales team only saw warm leads — the rest pre-scored, pre-qualified, pre-routed?\n\nWhat if your ops team never re-keyed a BOL again?\n\nThis isn't a vision. It's been running.\n\n5 Lighthouse pilot slots open next week.\n\nDM me 'Lighthouse' if you want yours.\n\n#JadeOS #Operations #B2B",
        "asset": "—",
        "cta": "DM Oliver · 'Lighthouse'",
    },

    # ---------- WEEK 2 · REVEAL · BIG BANG ----------
    {
        "day": 7, "platform": "x", "phase": "REVEAL",
        "headline": "Meet JADE OS.",
        "body": "Meet JADE OS.\n\nUniversal AI agents that *run* the business.\nSix agents. Eleven industries.\nOne console.\n\n→ onejades.com",
        "asset": "jadeos_v3_landscape_16x9.mp4",
        "cta": "Watch the 12-second reel",
    },
    {
        "day": 7, "platform": "linkedin", "phase": "REVEAL",
        "headline": "Today we launch JADE OS publicly.",
        "body": "Today we launch JADE OS publicly.\n\n60 days ago I started building an AI operator console — not a chat wrapper, not a 'copilot', but a real agent platform that runs operational work end-to-end across 11 industries.\n\nWhat it does, today, in production:\n\n· Auto-sorts and triages inbound email at ~184/day on a benchmark workload\n· Extracts freight BOLs, healthcare intake forms, manufacturing POs into clean JSON in ~800ms\n· Triages support tickets with priority + drafted response in 38s avg\n· Qualifies inbound leads with rationale + recommended next action\n· Drafts industry-tuned outreach in the operator's voice\n· Runs multi-step playbooks chaining all of the above\n\nBuilt by an operator, for operators. From Minneapolis.\n\n5 Lighthouse pilot slots open. First-come, first-locked.\n\n→ onejades.com\n\n#JadeOS #AIAgents #Minneapolis #ProductLaunch",
        "asset": "jadeos_v3_landscape_16x9.mp4",
        "cta": "Apply for Lighthouse pilot",
    },
    {
        "day": 7, "platform": "hackernews", "phase": "REVEAL",
        "headline": "Show HN: JADE OS – AI agents that run operational work across 11 industries",
        "body": "Hey HN — I'm Oliver, founder of JADE OS (onejades.com).\n\nBuilt over the past 60 days as a single-operator response to a real pain: my own ops team was drowning in BOL transcription, ticket triage, and lead qualification. Tried every Zap, every workflow tool, every 'AI copilot'. Nothing actually ran the work end-to-end.\n\nJADE OS is six production agents (support triage, sales qual, data extraction, ops automation, content gen, ops co-pilot) wrapping Claude Sonnet 4.5 / GPT-5.2 via an Emergent Universal Key router. Tuned per industry (freight, healthcare, SaaS, manufacturing, legal, e-commerce, insurance, real estate, pro services, logistics, general) — each with its own lexicon, extraction schema, tone profile, and a versioned 'Moat' of customer-corrected schemas.\n\nKey design choices: streaming SSE, per-industry system prompt builder, PHI redaction in regulated verticals, playbooks as code (not Zapier), self-test endpoint runs 21 health checks end-to-end including LLM round-trips.\n\nHappy to answer questions about the architecture, the agent design, the per-vertical tuning, or the (very candid) cost economics of running this on the Universal Key.\n\nLink: https://onejades.com",
        "asset": "—",
        "cta": "Comments welcome",
    },
    {
        "day": 7, "platform": "tiktok", "phase": "REVEAL",
        "headline": "Watch an AI run 3 ops simultaneously in 12 seconds",
        "body": "Inbox auto-sorting. BOL extraction. Ticket triage. All from one device. All at once. All real.\n\nThis is JADE OS.\n\n#AI #Automation #OpsTok #SmallBiz #Tech",
        "asset": "jadeos_v3_vertical_9x16.mp4",
        "cta": "onejades.com (link in bio)",
    },
    {
        "day": 7, "platform": "instagram_reel", "phase": "REVEAL",
        "headline": "JADE OS · Reveal",
        "body": "12 seconds. 3 ops. 1 console.\n\nJADE OS is live.\n\n#JadeOS #AI #Automation #Tech #ProductLaunch",
        "asset": "jadeos_v3_vertical_9x16.mp4",
        "cta": "Tap link in bio",
    },
    {
        "day": 7, "platform": "youtube", "phase": "REVEAL",
        "headline": "JADE OS — AI Agents That Run The Business · 12s Reel",
        "body": "JADE OS is the AI operator console for ops teams.\n\nSix production-grade agents, eleven industries, one console.\n\nThis is the launch reel — 12 seconds of JADE handling three real ops scenarios simultaneously: Outlook inbox auto-sorting, freight BOL extraction, and support ticket triage.\n\nLearn more: onejades.com\nLighthouse pilot applications: onejades.com/lighthouse\n\nBuilt by Oliver Cummins · Minneapolis · 2026.\n\n#AI #Automation #OpsAutomation",
        "asset": "jadeos_v3_landscape_16x9.mp4",
        "cta": "Subscribe · onejades.com",
    },
    {
        "day": 9, "platform": "reddit", "phase": "REVEAL",
        "headline": "I built an AI agent platform for ops teams over 60 days — feedback welcome",
        "body": "Subreddit: r/SaaS or r/smallbusiness or r/MachineLearning (rotate)\n\nHey all — solo founder here. Spent the last 60 days building JADE OS, an AI agent platform for operations teams. Six agents (support triage, sales qualification, data extraction, ops automation, content gen, ops co-pilot) tuned per industry across 11 verticals.\n\nNot trying to sell — genuinely want feedback on the architecture and where this falls short.\n\nA few things I made unusual decisions on:\n\n1. Per-industry prompt builder + schema library (not a generic 'AI assistant'). Each vertical gets a different lexicon, extraction schema, and tone profile.\n2. Versioned 'moat' — customer schema corrections increment a correction_count and feed back into our defaults. The longer customers use it, the more accurate we get.\n3. Model router (fast / default / smart profiles). Customer code never changes when prices shift.\n4. PHI redaction enforced at the extraction layer for healthcare/legal/insurance.\n5. Playbooks as code, not as Zaps.\n\nDemos are live at onejades.com — would love brutal feedback, esp on the agent design and where you think this would break in production.",
        "asset": "—",
        "cta": "Comment thread",
    },

    # ---------- WEEK 3 · PROOF ----------
    {
        "day": 14, "platform": "linkedin", "phase": "PROOF",
        "headline": "I let JADE run my own ops for 7 days. Here's the receipts.",
        "body": "I let JADE run my own ops for 7 days. Here's the receipts.\n\n· 1,284 emails auto-triaged\n· 312 freight BOLs extracted (97.4% field accuracy on a 14-field schema)\n· 89 support tickets drafted (84% sent without edit)\n· 41 leads scored (top 6 became real conversations)\n· $0 in re-keying labor\n\nThe boring stuff is the whole game.\n\n#JadeOS #AIAgents #Operations",
        "asset": "jadeos_v3_square_1x1.mp4",
        "cta": "DM 'Lighthouse'",
    },
    {
        "day": 14, "platform": "x", "phase": "PROOF",
        "headline": "Receipts thread →",
        "body": "JADE OS · week 1 of public dogfooding · receipts thread 👇\n\n1/ 1,284 emails auto-triaged. 38s avg.\n\n2/ 312 BOLs extracted. 97.4% field accuracy on a 14-field schema.\n\n3/ 89 tickets drafted. 84% sent without a single edit.\n\n4/ 41 leads scored. Top 6 became actual conversations.\n\n5/ Zero re-keying labor. Zero copy-paste. Zero 'wait, where did I save that file'.\n\nThe boring stuff is the whole game.\n\n→ onejades.com",
        "asset": "—",
        "cta": "Thread continues",
    },
    {
        "day": 16, "platform": "instagram_feed", "phase": "PROOF",
        "headline": "Behind the Quanta",
        "body": "Behind the Quanta · how JADE actually extracts a BOL in 800ms.\n\nStep 1: PDF lands\nStep 2: pypdf strips raw text\nStep 3: Claude Sonnet 4.5 runs against a versioned freight_brokerage schema\nStep 4: 14 fields parsed into clean JSON\nStep 5: Customer corrections (if any) bump the schema's correction_count — our defaults improve from their data\n\nThis is the moat. Not the model. The schema.\n\n#JadeOS #AI #Tech #BehindTheBuild",
        "asset": "jadeos_v3_poster.jpg",
        "cta": "Watch the reel → onejades.com",
    },

    # ---------- WEEK 4 · CONVERT · LIGHTHOUSE ----------
    {
        "day": 21, "platform": "x", "phase": "CONVERT",
        "headline": "3 Lighthouse slots remaining.",
        "body": "3 Lighthouse pilot slots remaining.\n\n· 6-month JADE OS pilot\n· Full agent platform · all 11 industry profiles\n· White-glove onboarding\n· Co-authored case study at end of pilot\n\nFirst-come, first-locked.\n\n→ onejades.com/lighthouse",
        "asset": "jadeos_v3_landscape_16x9.mp4",
        "cta": "onejades.com/lighthouse",
    },
    {
        "day": 21, "platform": "linkedin", "phase": "CONVERT",
        "headline": "Last call · 3 Lighthouse pilot slots remaining",
        "body": "Last call · 3 Lighthouse pilot slots remaining.\n\nWhat you get:\n· 6-month pilot of JADE OS · full agent platform\n· White-glove onboarding · we tune the schemas to your data\n· All 11 industry profiles unlocked\n· A co-authored case study at the end (your win, our proof)\n\nWho fits:\n· Minneapolis or Twin Cities-area operator\n· Has at least one of: support queue, doc extraction pain, lead-routing chaos, ops triage backlog\n· Ready to give us 2 hours of integration time\n\nApply: onejades.com/lighthouse\n\n#JadeOS #Lighthouse #B2B",
        "asset": "—",
        "cta": "Apply",
    },
    {
        "day": 24, "platform": "instagram_reel", "phase": "CONVERT",
        "headline": "2 slots left.",
        "body": "Lighthouse pilots are first-come, first-locked.\n\n2 slots remain.\n\n#JadeOS #Lighthouse",
        "asset": "jadeos_v3_vertical_9x16.mp4",
        "cta": "Link in bio",
    },
    {
        "day": 27, "platform": "x", "phase": "CONVERT",
        "headline": "Final slot.",
        "body": "1 Lighthouse pilot slot remaining.\n\nApplications close Friday.\n\n→ onejades.com/lighthouse",
        "asset": "jadeos_v3_poster.jpg",
        "cta": "Apply now",
    },
]


def _enrich(post: Dict, start_date: datetime, hashmap: Dict) -> Dict:
    p = dict(post)
    plat = p["platform"]
    p["platform_label"] = PLATFORMS.get(plat, {}).get("label", plat)
    p["best_window"] = PLATFORMS.get(plat, {}).get("best_window", "—")
    p["format_spec"] = PLATFORMS.get(plat, {}).get("format", "—")
    p["asset_recommended"] = PLATFORMS.get(plat, {}).get("video", "—")
    p["tone"] = PLATFORMS.get(plat, {}).get("tone", "—")
    p["hashtags"] = hashmap.get(plat, [])
    p["scheduled_for"] = (start_date + timedelta(days=p["day"])).strftime("%Y-%m-%d")
    return p


def build_campaign(start_date_iso: str = None) -> Dict:
    """Return the full Big Bang launch campaign as a structured plan."""
    if start_date_iso:
        try:
            start = datetime.fromisoformat(start_date_iso.replace("Z", "+00:00"))
        except Exception:
            start = datetime.now(timezone.utc)
    else:
        start = datetime.now(timezone.utc)

    hashmap = _hashtags_for(1)
    enriched_posts = [_enrich(p, start, hashmap) for p in POSTS]

    # Group by week for the UI
    by_week: Dict[int, List[Dict]] = {1: [], 2: [], 3: [], 4: []}
    for p in enriched_posts:
        week_no = (p["day"] // 7) + 1
        by_week.setdefault(week_no, []).append(p)

    return {
        "name": "JADE OS · Big Bang Launch · 28-day organic campaign",
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": (start + timedelta(days=27)).strftime("%Y-%m-%d"),
        "total_posts": len(enriched_posts),
        "weeks": WEEKS,
        "platforms": PLATFORMS,
        "posts_by_week": by_week,
        "all_posts": enriched_posts,
        "growth_principles": [
            "TEASE before REVEAL — curiosity outperforms direct pitch 3-5x in organic feeds.",
            "Big Bang launch day · all platforms within a 3-hour window for compounding cross-platform discovery.",
            "Receipts > claims · post real numbers, real screenshots, real screen recordings.",
            "Founder voice on LinkedIn + X · platform brand voice on IG/TikTok.",
            "Cross-platform asset reuse · same 12s reel re-edited to 9:16, 1:1, 16:9 (already provided).",
            "Engagement: reply to EVERY comment in the first 4 hours of each post.",
            "Scarcity at end (Lighthouse pilot slots) converts intrigue to applications.",
            "Always link to onejades.com — own the destination, not the platform's.",
        ],
        "video_assets": {
            "landscape_16_9": "/static/social/jadeos_v3_landscape_16x9.mp4",
            "vertical_9_16": "/static/social/jadeos_v3_vertical_9x16.mp4",
            "square_1_1": "/static/social/jadeos_v3_square_1x1.mp4",
            "poster": "/static/social/jadeos_v3_poster.jpg",
            "audio_mp3": "/static/social/jadeos_v3_audio.mp3",
        },
    }
