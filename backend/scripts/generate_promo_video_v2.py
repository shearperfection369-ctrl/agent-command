"""Generate JADE OS promo reel v2 — keychain-animated, 12s sora-2-pro, real ops use cases.

Outputs: /app/static/jadeos_promo_v2.mp4 + .json sidecar
"""
import os
import sys
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

OUT_DIR = Path("/app/static")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / "jadeos_promo_v2.mp4"
META_PATH = OUT_DIR / "jadeos_promo_v2.json"

# Detailed cinematic prompt. Sora 2 responds well to scene/beat structure.
PROMPT = (
    "Cinematic 4K commercial reel for JADE OS — the AI operator console for Minneapolis ops "
    "teams. 12 seconds, anamorphic widescreen, console-black background with a faint cyan tech-grid "
    "floor receding to vanishing point. Color palette strictly: electric lime-green #ccff00, "
    "quantum-cyan #00ffff, vault-violet #7c5cff, on jet black. Subtle scanline overlay throughout. "
    "Premium investor-tier production value. "

    "BEAT 1 (0-2s): A matte-black titanium carabiner-style keyfob device — a JADE QUANTA — sits "
    "centered on a dark surface. The device has glowing lime-green LED rim accents tracing its outer "
    "edge, two transparent windows on the body revealing intricate green circuit boards beneath, a "
    "fingerprint-scanner panel on top, and a black nylon lanyard with steel ring. It rests in soft "
    "rim-lighting like a flagship product shot. The lime LED edges pulse once like a heartbeat. "

    "BEAT 2 (2-4s): The fingerprint scanner blooms cyan. From above the device, a translucent "
    "holographic UI projects upward — a rectangular tablet-sized panel hovering mid-air with the "
    "wordmark 'JADE OS' rendered in crisp lime-green geometric sans-serif. The projection has subtle "
    "light-cone rays. Inside the panel, a tiny animated line chart rises. "

    "BEAT 3 (4-6s): The hologram splits into four orbiting glass UI cards around the device, each "
    "labeled in monospaced caps: 'EMAIL · AUTO-SORTED · 184 TODAY' (showing a chaotic inbox column "
    "on the left morphing into clean labelled folders on the right with animated arrows), "
    "'TICKETS · TRIAGED · 38s AVG' (a queue of red-dots flowing into category buckets), "
    "'LEADS · SCORED · 1.2k MTD' (a score gauge spinning to 87), "
    "'DOCS · EXTRACTED · 2.4k MTD' (a BOL document with fields lighting up as JSON keys appear). "

    "BEAT 4 (6-9s): Quick montage of industry sigils orbiting the Quanta in violet light-trails — "
    "freight semi-truck, stethoscope, factory gear, contract document, judge's gavel, dollar sign — "
    "each pulsing as data flows into the central device. Crisp UI overlay reads 'OPERATOR · MISSION "
    "CONTROL · 11 INDUSTRIES TUNED'. "

    "BEAT 5 (9-12s): The camera dollies forward through the holographic stack. All UI dissolves into "
    "a clean wordmark reveal — 'JADE OS' centered in massive bold geometric sans-serif lime-green on "
    "black, with subtle scanlines. Below in small caps: 'AI AGENTS FOR THE OPERATOR · ONEJADES.COM'. "
    "A final lime accent bracket frames the wordmark like the corner brackets used throughout the "
    "JADE OS UI system. Hold the logo for the final beat. "

    "STYLE: Anamorphic lens flares, deliberate motion, depth-of-field, particle motes drifting "
    "across the frame, faint film grain, broadcast-quality colour grade. NO PEOPLE. NO GARBLED TEXT. "
    "All on-screen typography in clean monospaced or geometric sans-serif. Confident, precise, "
    "premium — like an Apple keynote crossed with a Bloomberg terminal. Avoid any cliché AI "
    "imagery (no glowing brains, no blue spirals, no robot heads)."
)


def main():
    started = datetime.now(timezone.utc)
    try:
        from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration
    except Exception as e:
        print(f"FATAL: emergentintegrations not importable: {e}", flush=True)
        sys.exit(1)

    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        print("FATAL: EMERGENT_LLM_KEY missing", flush=True)
        sys.exit(1)

    print(f"[{started.isoformat()}] sora-2-pro · 1280x720 · 12s …", flush=True)
    vg = OpenAIVideoGeneration(api_key=key)
    try:
        video_bytes = vg.text_to_video(
            prompt=PROMPT,
            model="sora-2-pro",
            size="1280x720",
            duration=12,
            max_wait_time=900,
        )
    except Exception as e:
        print(f"FATAL during text_to_video: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        sys.exit(2)

    if not video_bytes:
        print("FATAL: no bytes returned", flush=True)
        sys.exit(3)

    vg.save_video(video_bytes, str(OUT_PATH))
    finished = datetime.now(timezone.utc)
    elapsed = (finished - started).total_seconds()
    size_mb = OUT_PATH.stat().st_size / 1_000_000
    META_PATH.write_text(json.dumps({
        "prompt": PROMPT,
        "model": "sora-2-pro",
        "size": "1280x720",
        "duration_s": 12,
        "started": started.isoformat(),
        "finished": finished.isoformat(),
        "elapsed_s": round(elapsed, 1),
        "file_mb": round(size_mb, 2),
        "version": 2,
    }, indent=2))
    print(f"OK · {OUT_PATH} ({size_mb:.2f} MB) in {elapsed:.1f}s", flush=True)


if __name__ == "__main__":
    main()
