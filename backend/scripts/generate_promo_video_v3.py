"""Generate JADE OS promo reel v3 — split-screen REAL OPS scenes + narration mux.

Visual: Quanta keychain projects three live ops UIs simultaneously —
  Outlook inbox auto-sorting (left), Freight BOL extracting (right), Support ticket triage (bottom)

Audio: first 12s of /app/backend/audio/jade_voice.mp3 (the user-supplied JADE TTS voice).

Output: /app/static/jadeos_promo_v3.mp4 (with audio) + .json sidecar
"""
import os
import sys
import json
import shutil
import subprocess
import traceback
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

OUT_DIR = Path("/app/static")
OUT_DIR.mkdir(parents=True, exist_ok=True)
SILENT_PATH = OUT_DIR / "jadeos_promo_v3_silent.mp4"
OUT_PATH = OUT_DIR / "jadeos_promo_v3.mp4"
META_PATH = OUT_DIR / "jadeos_promo_v3.json"
AUDIO_PATH = ROOT / "audio" / "jade_voice_12s.mp3"

PROMPT = (
    "Cinematic 4K commercial reel for JADE OS, the AI operator console for Minneapolis ops teams. "
    "12 seconds, anamorphic widescreen, console-black background with a faint cyan tech-grid floor "
    "receding to vanishing point. Strict color palette: electric lime-green #ccff00, "
    "quantum-cyan #00ffff, vault-violet #7c5cff, on jet black. Subtle scanlines throughout. "
    "Premium investor-tier production. "

    "BEAT 1 (0-2s): A matte-black titanium carabiner-style keyfob — a JADE QUANTA — centered on a "
    "dark surface. Glowing lime-green LED accents trace its outer edge, two transparent windows "
    "reveal intricate green circuit boards inside, a fingerprint scanner on top, black nylon "
    "lanyard. The lime edges pulse once like a heartbeat. "

    "BEAT 2 (2-3s): The fingerprint scanner blooms cyan. From above the device, a single luminous "
    "ray fans upward and SPLITS into THREE translucent holographic operator panels arranged "
    "around the Quanta — LEFT panel, RIGHT panel, BOTTOM panel — all glowing softly. "

    "BEAT 3 (3-9s): SIMULTANEOUS SPLIT-SCREEN of three real ops scenes, all clearly happening in "
    "the same JADE OS UI system. "

    "LEFT PANEL — Outlook-style inbox auto-sorting. Header reads 'INBOX · AUTO-SORTED · 184 "
    "TODAY'. A column of chaotic mixed emails on top (subjects visible: 'Re: Invoice 4421', "
    "'Carrier confirmation', 'Demo request', 'Refund question', 'Net 30 approval') ANIMATES into "
    "cleanly labeled folders on the right side ('BILLING', 'SALES', 'SUPPORT', 'OPS') via "
    "neon-green arrow trails. Each email zooms into its correct folder as it gets tagged. "

    "RIGHT PANEL — Freight BOL extraction. Header reads 'BOL · EXTRACTED · 2,438 MTD'. A scanned "
    "shipping document fills the left half of the panel. JADE's lime-green fields light up "
    "sequentially over the doc — 'CARRIER: Schneider', 'PRO #: 84421-MSP', 'ORIGIN: Eagan MN', "
    "'DEST: Dallas TX', 'PIECES: 14', 'WEIGHT: 18,420 lbs' — each field traces from the doc into "
    "a clean JSON output panel on the right. "

    "BOTTOM PANEL — Support ticket triage. Header reads 'TICKETS · TRIAGED · 38s AVG'. A queue of "
    "red-dot tickets flows in from the left. JADE labels each one with a priority pill (P0/P1/P2), "
    "category (BILLING/AUTH/INTEGRATION), and routes them into colored buckets with kinetic dot "
    "trails. A small counter ticks 'RESPONSE DRAFTED' for each ticket. "

    "All three panels glow softly with violet light-trails connecting them back to the central "
    "Quanta. "

    "BEAT 4 (9-10s): The three panels collapse back into the Quanta in a clean motion. Industry "
    "sigils orbit briefly — freight truck, stethoscope, factory gear, judge's gavel, dollar sign. "

    "BEAT 5 (10-12s): Camera dollies forward through the holographic stack to a clean wordmark "
    "reveal: 'JADE OS' in massive bold geometric sans-serif lime-green on console-black with "
    "subtle scanlines. Below it, smaller caps: 'AI AGENTS FOR THE OPERATOR · ONEJADES.COM'. Final "
    "lime corner brackets frame the wordmark. Hold the logo. "

    "STYLE: Anamorphic lens flares, deliberate camera motion, depth-of-field, particle motes, "
    "faint film grain. NO PEOPLE, NO ROBOT HEADS, NO GLOWING BRAINS, NO GENERIC AI CLICHES. All "
    "typography in monospaced or geometric sans-serif. The energy is 'Bloomberg terminal meets "
    "Apple keynote'."
)


def run_ffmpeg(*args):
    cmd = ["ffmpeg", "-y", *args]
    print(">>> " + " ".join(cmd), flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, flush=True)
        raise RuntimeError(f"ffmpeg failed (exit {result.returncode})")
    return result


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

    if not AUDIO_PATH.exists():
        print(f"FATAL: audio not found at {AUDIO_PATH}", flush=True)
        sys.exit(1)

    print(f"[{started.isoformat()}] sora-2-pro · 1280x720 · 12s · split-screen real ops …", flush=True)
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

    # Save silent video, then mux audio
    vg.save_video(video_bytes, str(SILENT_PATH))
    print(f"[silent] {SILENT_PATH} ({SILENT_PATH.stat().st_size/1_000_000:.2f} MB)", flush=True)

    # Mux: replace any existing audio track in the sora output with the JADE voice
    run_ffmpeg(
        "-i", str(SILENT_PATH),
        "-i", str(AUDIO_PATH),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-map", "0:v:0",
        "-map", "1:a:0",
        str(OUT_PATH),
    )

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
        "version": 3,
        "audio_source": "jade_voice_12s.mp3 (first 12s of user-supplied JADE TTS)",
        "narration_snippet": "Hello, I'm Jade. Welcome to the JADE OS audio library…",
        "scene": "split-screen real ops · Outlook auto-sort + BOL extract + Support triage",
    }, indent=2))

    # Cleanup silent intermediate
    try: SILENT_PATH.unlink()
    except Exception: pass

    print(f"OK · {OUT_PATH} ({size_mb:.2f} MB) in {elapsed:.1f}s", flush=True)


if __name__ == "__main__":
    main()
