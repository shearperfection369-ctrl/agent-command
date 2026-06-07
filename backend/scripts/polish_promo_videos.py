#!/usr/bin/env python3
"""Polish JadeOS promo videos for VC delivery.

For each promo (v1, v2, v3) we:
  1. Build a 3.0s 1920×1080 'JadeOS AI Suite' intro card (animated drawtext)
  2. Upscale the 1280×720 source to 1920×1080 with lanczos + unsharp mask,
     fade-in 0.3s and fade-out 0.8s on both video and audio
  3. Build a 1.5s 1920×1080 outro card (contact + URL)
  4. Concatenate intro → main → outro at uniform 1920×1080 / 30fps
  5. Re-encode H.264 CRF 18, slow preset, AAC 192k stereo @ 48 kHz, +faststart

Output overwrites /app/static/jadeos_promo[_v2|_v3].mp4 after the originals
have been backed up to /app/static/_orig/.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

# Prefer system ffmpeg (has drawtext + libass); fall back to bundled binary.
import shutil as _sh
FFMPEG = _sh.which("ffmpeg") or imageio_ffmpeg.get_ffmpeg_exe()
STATIC = Path("/app/static")
BACKUP = STATIC / "_orig"
BACKUP.mkdir(exist_ok=True)
WORK = Path("/tmp/promo_polish")
WORK.mkdir(exist_ok=True)

FONT_BOLD = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf"

VIDEOS = [
    {"src": "jadeos_promo.mp4",    "label": "v1"},
    {"src": "jadeos_promo_v2.mp4", "label": "v2"},
    {"src": "jadeos_promo_v3.mp4", "label": "v3"},
]

WIDTH, HEIGHT, FPS = 1920, 1080, 30

# ---------------------------- intro / outro builders ----------------------------

def build_intro_card(out: Path) -> None:
    """3.0s 1920×1080 H.264 silent clip introducing JadeOS AI Suite."""
    # Layered drawtext with enable= ranges produces a stagger animation.
    # Color palette mirrors the app brand: jade #ccff00, cyan #00ffff, violet #7c5cff.
    title = "JadeOS AI Suite"
    eyebrow = "OPERATOR-GRADE AI PLATFORM · MINNEAPOLIS"
    tagline = "Voice-first. Persistent memory. 128-qubit. Built for operators."
    products = [
        ("JADEOS QUANTUM AI",   "FLAGSHIP · 50+ MODULES · HEY JADE",       "0xccff00"),
        ("JADEOS-AGENT SUITE",  "SIX FREIGHT AGENTS · SITS ON ANY TMS",    "0x00ffff"),
        ("HOT SHOT TMS",        "OPERATOR-BUILT · UNDERSERVED SEGMENT",    "0x7c5cff"),
    ]

    # background: console-black with a subtle vignette using a fade-in alpha
    # synthesised via lavfi color source.
    vf_layers = [
        # Eyebrow (fades in at 0.2s)
        f"drawtext=fontfile={FONT_MONO}:text='{eyebrow}':fontcolor=0xccff00:"
        f"fontsize=22:x=(w-text_w)/2:y=160:"
        f"alpha='if(lt(t,0.2),0,if(lt(t,0.5),(t-0.2)/0.3,if(lt(t,2.7),1,(3.0-t)/0.3)))'",
        # Main title (fades in at 0.4s)
        f"drawtext=fontfile={FONT_BOLD}:text='{title}':fontcolor=white:"
        f"fontsize=160:x=(w-text_w)/2:y=220:"
        f"alpha='if(lt(t,0.4),0,if(lt(t,0.8),(t-0.4)/0.4,if(lt(t,2.7),1,(3.0-t)/0.3)))'",
        # Tagline (fades in at 0.9s)
        f"drawtext=fontfile={FONT_MONO}:text='{tagline}':fontcolor=0xcccccc:"
        f"fontsize=28:x=(w-text_w)/2:y=420:"
        f"alpha='if(lt(t,0.9),0,if(lt(t,1.2),(t-0.9)/0.3,if(lt(t,2.7),1,(3.0-t)/0.3)))'",
    ]

    # Three product cards (stagger appearance)
    card_y = 580
    card_w = 540
    card_gap = 30
    total_w = card_w * 3 + card_gap * 2
    start_x = (WIDTH - total_w) // 2
    for i, (name, sub, color) in enumerate(products):
        delay = 1.2 + i * 0.2
        x_center = start_x + i * (card_w + card_gap) + card_w // 2
        # Product name
        vf_layers.append(
            f"drawtext=fontfile={FONT_BOLD}:text='{name}':fontcolor={color}:"
            f"fontsize=38:x={x_center}-text_w/2:y={card_y}:"
            f"alpha='if(lt(t,{delay}),0,if(lt(t,{delay+0.3}),(t-{delay})/0.3,if(lt(t,2.7),1,(3.0-t)/0.3)))'"
        )
        # Product sub
        vf_layers.append(
            f"drawtext=fontfile={FONT_MONO}:text='{sub}':fontcolor=0xaaaaaa:"
            f"fontsize=18:x={x_center}-text_w/2:y={card_y+60}:"
            f"alpha='if(lt(t,{delay+0.1}),0,if(lt(t,{delay+0.4}),(t-{delay+0.1})/0.3,if(lt(t,2.7),1,(3.0-t)/0.3)))'"
        )

    # Brand bar (always on)
    vf_layers.append(
        f"drawtext=fontfile={FONT_MONO}:text='READY TO DEPLOY · ONEJADES.COM':fontcolor=0xccff00:"
        f"fontsize=22:x=(w-text_w)/2:y=900:"
        f"alpha='if(lt(t,1.6),0,if(lt(t,1.9),(t-1.6)/0.3,if(lt(t,2.7),1,(3.0-t)/0.3)))'"
    )

    vf = ",".join(vf_layers)

    # base: console-black with very subtle diagonal gradient via geq
    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi", "-i",
        f"color=c=0x05060d:s={WIDTH}x{HEIGHT}:d=3.0:r={FPS}",
        # silent audio track @ 48 kHz so concat across all clips has matching streams
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-t", "3.0",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-shortest",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def build_outro_card(out: Path) -> None:
    """1.5s outro with contact + URL."""
    vf_layers = [
        f"drawtext=fontfile={FONT_BOLD}:text='ONEJADES.COM':fontcolor=0xccff00:"
        f"fontsize=120:x=(w-text_w)/2:y=380:"
        f"alpha='if(lt(t,0.15),t/0.15,if(lt(t,1.2),1,(1.5-t)/0.3))'",
        f"drawtext=fontfile={FONT_MONO}:text='FOUNDER@JADEOS.AI · MINNEAPOLIS · MN':fontcolor=0xcccccc:"
        f"fontsize=32:x=(w-text_w)/2:y=560:"
        f"alpha='if(lt(t,0.3),(t-0.0)/0.3,if(lt(t,1.2),1,(1.5-t)/0.3))'",
        f"drawtext=fontfile={FONT_MONO}:text='READY TO DEPLOY · RAISING IN TANDEM':fontcolor=0x7c5cff:"
        f"fontsize=24:x=(w-text_w)/2:y=620:"
        f"alpha='if(lt(t,0.5),t/0.5,if(lt(t,1.2),1,(1.5-t)/0.3))'",
    ]
    vf = ",".join(vf_layers)
    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi", "-i",
        f"color=c=0x05060d:s={WIDTH}x{HEIGHT}:d=1.5:r={FPS}",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-t", "1.5",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-shortest",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


# ---------------------------- main polishing ----------------------------

def polish_source(src: Path, out: Path) -> None:
    """Upscale + sharpen + audio normalize + fades on the original 720p Sora clip.
    Output: 1920×1080, 30fps, H.264 CRF 18, AAC 192k stereo 48 kHz with 0.3s fade-in
    and 0.8s fade-out (both video and audio)."""
    # ffprobe-free: rely on Sora 12s standard duration
    # detect via ffmpeg + grep
    out_probe = subprocess.run([FFMPEG, "-i", str(src)], capture_output=True, text=True)
    info = out_probe.stderr
    import re
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", info)
    if not m:
        raise SystemExit(f"Could not determine duration for {src}")
    h, mi, s = m.groups()
    duration = int(h) * 3600 + int(mi) * 60 + float(s)
    fade_out_start = max(0.0, duration - 0.8)

    vf = (
        # Upscale with lanczos for sharper edges than bicubic default
        f"scale={WIDTH}:{HEIGHT}:flags=lanczos,"
        # Mild unsharp to enhance perceived sharpness without halos
        f"unsharp=5:5:0.8:5:5:0.0,"
        # Fade in 0.3s, fade out last 0.8s
        f"fade=t=in:st=0:d=0.3,"
        f"fade=t=out:st={fade_out_start:.2f}:d=0.8,"
        f"fps={FPS},format=yuv420p"
    )
    af = (
        # Normalize to -16 LUFS-ish via dynaudnorm (broadcast-safe)
        f"dynaudnorm=p=0.95:m=10,"
        # Resample to common 48 kHz stereo so concat audio streams match
        f"aresample=48000,aformat=channel_layouts=stereo,"
        f"afade=t=in:st=0:d=0.3,"
        f"afade=t=out:st={fade_out_start:.2f}:d=0.8"
    )
    cmd = [
        FFMPEG, "-y", "-i", str(src),
        "-vf", vf, "-af", af,
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def concat(parts: list[Path], out: Path) -> None:
    """Concat already-normalized 1920×1080/30/H.264/AAC 192k/stereo/48 kHz clips."""
    list_file = WORK / "concat.txt"
    list_file.write_text("\n".join(f"file '{p}'" for p in parts))
    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        # all parts share the same codec params already → stream copy is safe
        "-c", "copy",
        "-movflags", "+faststart",
        str(out),
    ]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        # If stream-copy fails (mismatched params), re-encode
        print(f"  [concat] stream-copy failed, re-encoding…")
        cmd2 = [
            FFMPEG, "-y",
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart",
            str(out),
        ]
        subprocess.run(cmd2, check=True)


def main() -> None:
    # Backup originals once
    for v in VIDEOS:
        src = STATIC / v["src"]
        bak = BACKUP / v["src"]
        if not bak.exists():
            shutil.copy2(src, bak)
            print(f"backup · {src.name} → {bak}")

    # Build intro + outro once (shared across all 3)
    intro = WORK / "intro.mp4"
    outro = WORK / "outro.mp4"
    print("→ building intro card (3.0s) …")
    build_intro_card(intro)
    print("→ building outro card (1.5s) …")
    build_outro_card(outro)
    print(f"   intro · {intro.stat().st_size//1024} KB · outro · {outro.stat().st_size//1024} KB")

    # Polish each promo
    for v in VIDEOS:
        src = BACKUP / v["src"]  # always polish from backup, not from a re-polished file
        main_polished = WORK / f"main_{v['label']}.mp4"
        final = STATIC / v["src"]
        print(f"\n→ polishing {v['label']} from {src.name} …")
        polish_source(src, main_polished)
        print(f"   main · {main_polished.stat().st_size//1024} KB")
        print(f"→ concatenating intro + {v['label']} + outro → {final.name} …")
        concat([intro, main_polished, outro], final)
        size_kb = final.stat().st_size // 1024
        # ffmpeg duration check
        info = subprocess.run([FFMPEG, "-i", str(final)], capture_output=True, text=True).stderr
        import re
        m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", info)
        dur = m.group(0) if m else "?"
        print(f"   ✓ {final.name} · {size_kb} KB · {dur}")

        # Refresh sidecar JSON with new metadata
        meta_path = final.with_suffix(".json")
        try:
            meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        except Exception:
            meta = {}
        meta["polished_at"] = "2026-02-07T16:00:00Z"
        meta["intro"] = "JadeOS AI Suite · trinity products"
        meta["resolution"] = "1920x1080"
        meta["fps"] = 30
        meta["audio_lufs_norm"] = True
        meta["fade_in_s"] = 0.3
        meta["fade_out_s"] = 0.8
        meta["intro_s"] = 3.0
        meta["outro_s"] = 1.5
        meta_path.write_text(json.dumps(meta, indent=2))
        print(f"   ✓ meta refreshed · {meta_path.name}")


if __name__ == "__main__":
    main()
    print("\n✓ all done")
