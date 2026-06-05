"""Generate the JADE OS promotional reel via Sora 2.

Output: /app/static/jadeos_promo.mp4 (served by FastAPI at /api/static/jadeos_promo.mp4
once the static mount is wired). Also saves a sidecar JSON with the prompt used.
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
OUT_PATH = OUT_DIR / "jadeos_promo.mp4"
META_PATH = OUT_DIR / "jadeos_promo.json"

PROMPT = (
    "Cinematic 4K promotional reel for JADE OS — an AI operator console for Minneapolis "
    "freight, healthcare, manufacturing, SaaS, e-commerce, insurance, legal, and real-estate "
    "operators. Pitch-black studio set with a faint cyan grid floor receding to vanishing point. "
    "A holographic terminal interface materializes mid-air, glowing in electric lime-green and "
    "quantum-cyan wireframe — data streams flow across translucent panels: BOLs auto-extracted, "
    "lead scores ticking up, support tickets routing themselves. Industry sigils orbit a central "
    "JADE bracketed monogram (a sharp lime-green letter J inside corner brackets): a freight "
    "semi-truck, a stethoscope, a precision factory gear, a contract document, a dollar sign, a "
    "judge's gavel — each connecting into the core via thin violet light-trails that pulse on "
    "every transaction. Crisp UI cards animate in: 'OPERATOR · MISSION CONTROL', 'LIGHTHOUSE "
    "PROGRAM', '6 AGENTS · 11 INDUSTRIES'. Anamorphic flares, depth-of-field, particle motes drift "
    "through the frame. The camera dollies forward through the holographic stack and resolves on a "
    "clean wordmark reveal — 'JADE OS' in bold geometric sans-serif, lime-green on console black, "
    "with a subtle scanline. A small caption beneath reads 'MPLS · AI AGENTS'. Mood: confident, "
    "precise, premium, investor-grade tech reel. High contrast, futuristic, no humans, no garbled "
    "text. Aspect 16:9, broadcast-quality colour, deliberate motion."
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
        print("FATAL: EMERGENT_LLM_KEY missing in env", flush=True)
        sys.exit(1)

    print(f"[{started.isoformat()}] kicking off sora-2 (1280x720, 12s)…", flush=True)
    vg = OpenAIVideoGeneration(api_key=key)
    try:
        video_bytes = vg.text_to_video(
            prompt=PROMPT,
            model="sora-2",
            size="1280x720",
            duration=12,
            max_wait_time=900,
        )
    except Exception as e:
        print(f"FATAL during text_to_video: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        sys.exit(2)

    if not video_bytes:
        print("FATAL: generation returned no bytes", flush=True)
        sys.exit(3)

    vg.save_video(video_bytes, str(OUT_PATH))
    finished = datetime.now(timezone.utc)
    elapsed = (finished - started).total_seconds()
    size_mb = OUT_PATH.stat().st_size / 1_000_000
    META_PATH.write_text(json.dumps({
        "prompt": PROMPT,
        "model": "sora-2",
        "size": "1280x720",
        "duration_s": 12,
        "started": started.isoformat(),
        "finished": finished.isoformat(),
        "elapsed_s": round(elapsed, 1),
        "file_mb": round(size_mb, 2),
    }, indent=2))
    print(f"OK · saved {OUT_PATH} ({size_mb:.2f} MB) in {elapsed:.1f}s", flush=True)


if __name__ == "__main__":
    main()
