"""Offline one-click explainer previews: original procedural artwork + FFmpeg.

This intentionally does not pretend to synthesize AI artwork or factual research.
Every asset is drawn from local primitives, then passed through the existing
provenance/audit system. Publication is never authorized by this command.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

from .production import audit, ingest, load_plan, render
from .scene_plan import plan

SIZE = (1280, 720)
PALETTES = (
    ((17, 25, 61), (34, 77, 121), (255, 198, 91), (130, 219, 224)),
    ((19, 51, 69), (29, 112, 121), (255, 206, 116), (186, 236, 220)),
    ((45, 28, 76), (97, 57, 122), (255, 193, 116), (207, 173, 239)),
)
FONT_PATHS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)
ORIGIN_NOTE = ("Original vector illustration drawn using Automate YTB's "
               "built-in geometric art code; no third-party image source.")


def _font(size: int):
    for name in FONT_PATHS:
        if Path(name).is_file():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


def _wrap(draw, text: str, font, width: int, lines: int = 4) -> list[str]:
    words = str(text).replace("\n", " ").split()
    result, current = [], ""
    for word in words:
        candidate = (current + " " + word).strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= width:
            current = candidate
        else:
            if current:
                result.append(current)
            current = word
        if len(result) >= lines:
            break
    if current and len(result) < lines:
        result.append(current)
    if len(result) > lines:
        result = result[:lines]
    shown = " ".join(result)
    if shown != " ".join(words) and result:
        final = result[-1]
        while final and draw.textbbox((0, 0), final + "…", font=font)[2] > width:
            final = final[:-1]
        result[-1] = final.rstrip(" .,") + "…"
    return result


def _blend(c1, c2, t):
    return tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))


def _draw_mascot(draw, cx: int, cy: int, accent, scene_number: int):
    """Single original bird design, with repeatable silhouette and emotions."""
    # Floor shadow and ears/feather horns.
    draw.ellipse((cx - 150, cy + 166, cx + 145, cy + 201), fill=(12, 21, 42))
    body = (99, 119, 181)
    outline = (26, 38, 75)
    draw.polygon([(cx - 116, cy - 111), (cx - 112, cy - 199),
                  (cx - 32, cy - 151)], fill=body)
    draw.polygon([(cx + 116, cy - 111), (cx + 112, cy - 199),
                  (cx + 32, cy - 151)], fill=body)
    draw.ellipse((cx - 145, cy - 160, cx + 145, cy + 155),
                 fill=outline)
    draw.ellipse((cx - 137, cy - 155, cx + 137, cy + 145),
                 fill=body)
    draw.ellipse((cx - 107, cy - 29, cx + 107, cy + 137),
                 fill=(204, 215, 230))
    # Wing angle varies without losing character identity.
    wing_y = cy + (22 if scene_number % 3 else -21)
    draw.ellipse((cx - 174, wing_y - 26, cx - 111, wing_y + 90),
                 fill=(74, 94, 151))
    draw.ellipse((cx + 112, cy - 15, cx + 179, cy + 78),
                 fill=(74, 94, 151))
    # Thick consistent eye rings and pupils.
    for dx in (-61, 61):
        draw.ellipse((cx + dx - 48, cy - 103, cx + dx + 49, cy - 4),
                     fill=(33, 49, 89))
        draw.ellipse((cx + dx - 40, cy - 96, cx + dx + 41, cy - 12),
                     fill=(248, 249, 240))
        pupil_dx = (scene_number % 3 - 1) * 7
        draw.ellipse((cx + dx - 15 + pupil_dx, cy - 72,
                      cx + dx + 18 + pupil_dx, cy - 39),
                     fill=(21, 37, 63))
        draw.ellipse((cx + dx - 4 + pupil_dx, cy - 67,
                      cx + dx + 2 + pupil_dx, cy - 61),
                     fill=(255, 255, 255))
    draw.polygon([(cx - 20, cy - 20), (cx + 20, cy - 20),
                  (cx, cy + 20)], fill=accent)
    # Constant scarf and recognizable colored feathers.
    draw.rounded_rectangle((cx - 85, cy + 81, cx + 95, cy + 108),
                           radius=12, fill=accent)
    draw.polygon([(cx + 42, cy + 104), (cx + 81, cy + 157),
                  (cx + 108, cy + 110)], fill=accent)
    for x in (-77, 75):
        draw.line((cx + x, cy + 144, cx + x, cy + 176),
                  fill=(246, 178, 101), width=12)


def _scene_symbol(draw, symbol: str, cx: int, cy: int, accent):
    """Abstract visual cue based on words actually present in narration."""
    if symbol == "leaf":
        draw.ellipse((cx - 34, cy - 50, cx + 30, cy + 31),
                     fill=(103, 213, 165))
        draw.line((cx - 26, cy + 47, cx + 23, cy - 30),
                  fill=(23, 95, 91), width=7)
    elif symbol == "sun":
        draw.ellipse((cx - 29, cy - 29, cx + 29, cy + 29), fill=accent)
        for i in range(8):
            a = i * math.pi / 4
            draw.line((cx + int(36 * math.cos(a)), cy + int(36 * math.sin(a)),
                       cx + int(51 * math.cos(a)), cy + int(51 * math.sin(a))),
                      fill=accent, width=6)
    elif symbol == "book":
        draw.rounded_rectangle((cx - 44, cy - 32, cx + 45, cy + 34),
                               radius=7, fill=(246, 237, 220))
        draw.line((cx, cy - 30, cx, cy + 30),
                  fill=(105, 125, 156), width=5)
        for y in (-14, 2, 17):
            draw.line((cx - 35, cy + y, cx - 9, cy + y),
                      fill=(135, 149, 170), width=3)
    else:
        draw.ellipse((cx - 22, cy - 29, cx + 25, cy + 17),
                     outline=accent, width=9)
        draw.rounded_rectangle((cx - 4, cy + 30, cx + 7, cy + 42),
                               radius=3, fill=accent)


def _symbol_for(text: str) -> str:
    lowered = text.lower()
    if any(k in lowered for k in ("plant", "feuille", "arbre", "nature", "fleur", "tree")):
        return "leaf"
    if any(k in lowered for k in ("soleil", "lumière", "sun", "light", "énergie")):
        return "sun"
    if any(k in lowered for k in ("livre", "étude", "science", "research", "source", "étape")):
        return "book"
    return "question"


def draw_scene(*, topic: str, scene: dict, index: int, count: int, character: str,
               destination: Path) -> None:
    """Deterministic 16:9 editorial illustration; never embeds external media."""
    seed = int(hashlib.sha256((topic + "|" + character).encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed + index * 7189)
    top, bottom, gold, mint = PALETTES[seed % len(PALETTES)]
    image = Image.new("RGB", SIZE)
    draw = ImageDraw.Draw(image)
    for y in range(SIZE[1]):
        c = _blend(top, bottom, y / (SIZE[1] - 1))
        draw.line((0, y, SIZE[0], y), fill=c)
    # Atmospheric stage lighting, parallax-friendly foreground, and original particles.
    for i in range(28):
        x, y = rng.randrange(40, 1260), rng.randrange(25, 655)
        r = rng.randrange(2, 10)
        draw.ellipse((x-r, y-r, x+r, y+r),
                     fill=_blend(bottom, (221, 231, 246), 0.15 + r / 90))
    draw.ellipse((770, 125, 1240, 600), fill=_blend(bottom, mint, 0.28))
    draw.ellipse((815, 170, 1210, 565), fill=_blend(bottom, mint, 0.38))
    draw.rounded_rectangle((42, 38, 758, 666), radius=35,
                           fill=_blend(top, (10, 14, 38), 0.28),
                           outline=_blend(bottom, (220, 234, 255), 0.28), width=3)
    draw.rounded_rectangle((76, 73, 344, 116), radius=19, fill=gold)
    label_font = _font(17)
    draw.text((94, 83), "HISTOIRE ORIGINALE", font=label_font, fill=(29, 38, 68))
    draw.text((603, 83), f"{index + 1:02d} / {count:02d}",
              font=_font(20), fill=(220, 230, 250))
    title_font = _font(39)
    y = 146
    for line in _wrap(draw, topic, title_font, 616, lines=3):
        draw.text((77, y), line, font=title_font, fill=(251, 250, 246),
                  stroke_width=1, stroke_fill=top)
        y += 52
    y = max(330, y + 31)
    text_font = _font(26)
    for line in _wrap(draw, scene["narration"], text_font, 616, lines=7):
        draw.text((80, y), line, font=text_font,
                  fill=(222, 232, 246))
        y += 41
        if y > 620:
            break
    draw.rounded_rectangle((785, 76, 1207, 167), radius=30,
                           fill=_blend(bottom, (255, 255, 255), 0.16))
    draw.text((820, 100), "DÉCOUVRONS ENSEMBLE", font=_font(20),
              fill=(239, 242, 251))
    _draw_mascot(draw, 1010, 395, gold, index)
    draw.ellipse((1127, 522, 1235, 630),
                 fill=_blend(top, (255, 255, 255), 0.15))
    _scene_symbol(draw, _symbol_for(scene["narration"]), 1180, 578, gold)
    # Footer progress indicator: consistent across episodes.
    draw.rounded_rectangle((72, 684, 1208, 693), radius=4,
                           fill=_blend(bottom, (240, 246, 255), 0.15))
    step = round((index+1) / count * 1136)
    draw.rounded_rectangle((72, 684, 72+step, 693), radius=4, fill=gold)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG", optimize=True)


def _run(args: list[str], timeout: int = 120) -> str:
    complete = subprocess.run(args, capture_output=True, text=True,
                              check=False, timeout=timeout)
    if complete.returncode:
        raise RuntimeError(f"{args[0]} failed: {complete.stderr[-700:]}")
    return complete.stdout


def _media_duration(file: Path) -> float:
    value = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                  "-of", "default=noprint_wrappers=1:nokey=1", str(file)])
    return float(value.strip())


def _ffconcat_quote(file: Path) -> str:
    return "'" + str(file.resolve()).replace("'", "'\\''") + "'"


def make_narration(data: dict, output: Path, language: str) -> Path:
    """Generate timeboxed speech per scene; reject severely compressed narration."""
    if not shutil.which("espeak-ng") or not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("espeak-ng, ffmpeg and ffprobe are required for offline speech")
    if language not in {"fr", "en"}:
        raise ValueError("Supported voices: fr and en")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="narration-", dir=output.parent) as temp:
        root = Path(temp)
        segments = []
        for i, scene in enumerate(data["scenes"]):
            raw = root / f"raw-{i:03d}.wav"
            segment = root / f"segment-{i:03d}.wav"
            target = (scene["endMs"] - scene["startMs"]) / 1000
            _run(["espeak-ng", "-v", language, "-s", "165", "-w", str(raw),
                  scene["narration"]])
            original = _media_duration(raw)
            # Preserve natural cadence if short; only accelerate when necessary.
            pace = max(1.0, original / max(0.1, target - 0.18))
            if pace > 1.85:
                raise ValueError(f"Scene {scene['id']} has too much narration for "
                                 f"{target:.1f}s; increase shot duration or shorten it")
            _run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                  "-i", str(raw), "-af", f"atempo={pace:.5f},apad",
                  "-t", f"{target:.3f}", "-ar", "48000", "-ac", "1",
                  "-c:a", "pcm_s16le", str(segment)])
            segments.append(segment)
        concat = root / "audio.ffconcat"
        concat.write_text("ffconcat version 1.0\n" +
                          "".join(f"file {_ffconcat_quote(p)}\n" for p in segments),
                          encoding="utf-8")
        _run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
              "-f", "concat", "-safe", "0", "-i", str(concat),
              "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", str(output)])
    return output


def build(*, topic: str, script: str, character: str, directory: Path,
          duration: int = 60, shot_seconds: float = 7.5,
          language: str = "fr", silent: bool = False, resolution: str = "720p") -> dict:
    """Offline end-to-end preview. One source script; never invents factual claims."""
    if not 30 <= duration <= 3600:
        raise ValueError("Duration must be between 30 and 3600 seconds")
    if len(script) > 150000 or not script.strip():
        raise ValueError("Provide a nonempty original narration under 150000 chars")
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    plan_file = directory / "scene-plan.json"
    expected = plan(topic=topic, script=script, character=character,
                    duration=duration, shot_seconds=shot_seconds)
    if plan_file.exists():
        data = load_plan(plan_file)
        if (data["sourceScriptSha256"] != expected["sourceScriptSha256"] or
                data["targetDurationSeconds"] != duration or
                data["originalCharacterBible"] != character or
                data["topic"] != topic):
            raise ValueError("Existing project differs; select a new output folder")
    else:
        plan_file.write_text(json.dumps(expected, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
        data = expected
    statuses = {s["sceneId"]: s["status"] for s in audit(plan_file)["details"]}
    with tempfile.TemporaryDirectory(prefix="illustrations-", dir=directory) as temp:
        for i, scene in enumerate(data["scenes"]):
            state = statuses[scene["id"]]
            if state == "ready":
                continue
            if state != "missing":
                raise ValueError(f"Unreviewed or modified asset: {scene['id']} ({state})")
            image = Path(temp) / (scene["id"] + ".png")
            draw_scene(topic=topic, scene=scene, index=i, count=len(data["scenes"]),
                       character=character, destination=image)
            ingest(plan_path=plan_file, scene_id=scene["id"], image_path=image,
                   provider="original-vector-code", rights_note=ORIGIN_NOTE,
                   cost_usd="0", rights_confirmed=True)
    checked = audit(plan_file)
    if not checked["readyForPreview"]:
        raise RuntimeError("Some images are not ready for preview")
    audio = None if silent else make_narration(data, directory / "narration.wav", language)
    result = render(plan_path=plan_file, output=directory / "render", audio=audio,
                    resolution=resolution)
    cover = directory / "thumbnail-draft.png"
    if not cover.exists():
        shutil.copyfile(directory / data["scenes"][0]["imageAsset"], cover)
    result.update({
        "plan": str(plan_file), "thumbnailDraft": str(cover),
        "assetAudit": checked["counts"], "artEngine": "procedural-vector",
        "voiceEngine": "none" if silent else "espeak-ng",
        "licenseCostUsd": "0.0000", "externalApiRequests": 0,
        "voiceQuality": "synthetic fallback" if not silent else "silent",
        "editorialReviewRequired": True, "publicationApproved": False,
    })
    (directory / "episode-report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="One-click offline YouTube episode preview")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--script", type=Path, required=True,
                        help="Full original narration file, at least one sentence per scene")
    parser.add_argument("--character", default="An original violet owl with a golden scarf")
    parser.add_argument("--directory", type=Path, default=Path("outputs/offline-episode"))
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--shot-seconds", type=float, default=7.5)
    parser.add_argument("--language", choices=["fr", "en"], default="fr")
    parser.add_argument("--resolution", choices=["720p", "1080p"], default="720p")
    parser.add_argument("--silent", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = build(topic=args.topic, script=args.script.read_text(encoding="utf-8"),
                       character=args.character, directory=args.directory,
                       duration=args.duration, shot_seconds=args.shot_seconds,
                       language=args.language, silent=args.silent,
                       resolution=args.resolution)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, RuntimeError, OSError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
