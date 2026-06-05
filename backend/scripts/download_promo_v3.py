"""Download an already-generated Sora video by ID (no regeneration).

If a previous run timed out on the final budget check but Sora successfully
finished the video, we can hit the /content endpoint again after the user tops
up. This avoids burning more budget on re-generation.
"""
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import requests

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

OUT_DIR = Path("/app/static")
OUT_DIR.mkdir(parents=True, exist_ok=True)
SILENT_PATH = OUT_DIR / "jadeos_promo_v3_silent.mp4"
OUT_PATH = OUT_DIR / "jadeos_promo_v3.mp4"
AUDIO_PATH = ROOT / "audio" / "jade_voice_12s.mp3"


def run_ffmpeg(*args):
    cmd = ["ffmpeg", "-y", *args]
    print(">>> " + " ".join(cmd), flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, flush=True)
        raise RuntimeError(f"ffmpeg failed (exit {result.returncode})")


def main():
    if len(sys.argv) < 2:
        print("usage: download_promo_v3.py <video_id>", flush=True)
        sys.exit(2)
    video_id = sys.argv[1]
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        print("FATAL: EMERGENT_LLM_KEY missing", flush=True)
        sys.exit(1)

    url = f"https://integrations.emergentagent.com/llm/openai/v1/videos/{video_id}/content"
    headers = {"Authorization": f"Bearer {key}"}
    print(f"Downloading {url} …", flush=True)
    r = requests.get(url, headers=headers, stream=True, timeout=180)
    print(f"status={r.status_code}", flush=True)
    if r.status_code != 200:
        print(r.text[:500], flush=True)
        sys.exit(3)
    with open(SILENT_PATH, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 64):
            if chunk:
                f.write(chunk)
    size = SILENT_PATH.stat().st_size
    print(f"silent video saved: {SILENT_PATH} ({size/1_000_000:.2f} MB)", flush=True)

    if not AUDIO_PATH.exists():
        print(f"warn: audio {AUDIO_PATH} missing, leaving silent file", flush=True)
        return
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
    try: SILENT_PATH.unlink()
    except Exception: pass
    print(f"OK · {OUT_PATH} ({OUT_PATH.stat().st_size/1_000_000:.2f} MB)", flush=True)


if __name__ == "__main__":
    main()
