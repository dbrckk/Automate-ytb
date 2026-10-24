"""Mobile-readable contact sheets sampled from the *actual encoded MP4*.

Sampling is intentionally bounded; technical checks cannot certify factual
accuracy, motion quality, licensing or artistic merit. No uploads or API calls.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageChops, ImageDraw, ImageOps, ImageStat, UnidentifiedImageError

from .media_qa import probe_media
from .production import _sha, _write_json, load_plan
from .studio import font

PAGE_W, PAGE_H = 1120, 2030
TILE_W, TILE_H = 520, 418
THUMB_W, THUMB_H = 480, 270
MARGIN = 30
GAP = 20
DARK_THRESHOLD = 0.985
FRAME_BYTES_MAX = 8_000_000


def _selection(scene_count: int, max_samples: int) -> list[int]:
    if not 2 <= max_samples <= 24:
        raise ValueError("Sample count must be between 2 and 24")
    wanted = min(scene_count, max_samples)
    return [(2*i + 1)*scene_count // (2*wanted) for i in range(wanted)]


def _frame_at(video: Path, second: float) -> Image.Image:
    process = subprocess.run([
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-ss", f"{second:.3f}", "-i", str(video),
        "-frames:v", "1", "-vf", "scale=640:360:flags=fast_bilinear",
        "-f", "image2pipe", "-vcodec", "png", "-"
    ], capture_output=True, timeout=90, check=False)
    if process.returncode != 0 or len(process.stdout) > FRAME_BYTES_MAX:
        raise RuntimeError("Unable to decode requested video frame")
    try:
        with Image.open(io.BytesIO(process.stdout)) as frame:
            frame.load()
            if frame.size != (640, 360):
                raise ValueError("Unexpected decoded frame dimensions")
            return frame.convert("RGB")
    except (OSError, UnidentifiedImageError, ValueError):
        raise RuntimeError("Video frame is unreadable") from None


def _metrics(image: Image.Image) -> dict:
    gray = ImageOps.grayscale(image.resize((96, 54)))
    histogram = gray.histogram()
    black_fraction = sum(histogram[:8]) / (96*54)
    return {
        "nearBlackFraction": round(black_fraction, 4),
        "meanLuminance": round(ImageStat.Stat(gray).mean[0], 1),
        "luminanceStdDev": round(ImageStat.Stat(gray).stddev[0], 1),
    }


def _wrap(draw: ImageDraw.ImageDraw, txt: str, width: int, size: int,
          max_lines: int) -> list[str]:
    f = font(size)
    words = txt.split()
    lines = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        # Break a very long uninterrupted token instead of overflowing.
        if draw.textbbox((0, 0), candidate, font=f)[2] <= width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
        while draw.textbbox((0, 0), word, font=f)[2] > width and len(word) > 1:
            split = max(1, len(word) // 2)
            while split > 1 and draw.textbbox((0, 0), word[:split], font=f)[2] > width:
                split -= 1
            lines.append(word[:split])
            word = word[split:]
        current = word
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and draw.textbbox((0, 0), last+"…", font=f)[2] > width:
            last = last[:-1]
        lines[-1] = last.rstrip()+"…"
    return lines


def _contact_page(frames: list[dict], *, page: int, total_pages: int,
                  title: str, dest: Path) -> None:
    image = Image.new("RGB", (PAGE_W, PAGE_H), (18, 25, 43))
    draw = ImageDraw.Draw(image)
    draw.text((MARGIN, 25), "AUTOMATE YTB  /  APERÇU VISUEL", font=font(33),
              fill=(249, 252, 255))
    draw.text((MARGIN, 79), _wrap(draw, title, PAGE_W-2*MARGIN, 23, 1)[0],
              font=font(23), fill=(180, 217, 242))
    draw.text((PAGE_W-195, 145), f"{page}/{total_pages}",
              font=font(22), fill=(178, 208, 234))
    for idx, item in enumerate(frames):
        col = idx % 2
        row = idx // 2
        x = MARGIN + col*(TILE_W + GAP)
        y = 195 + row*(TILE_H + GAP)
        draw.rounded_rectangle((x, y, x+TILE_W, y+TILE_H),
                               radius=18, fill=(32, 43, 66))
        thumb = ImageOps.fit(item["frame"], (THUMB_W, THUMB_H))
        image.paste(thumb, (x+20, y+16))
        draw.text((x+20, y+300), f"PLAN {item['sceneIndex']:03d}  •  {item['second']:.1f} s",
                  font=font(20), fill=(255, 204, 110))
        for line_num, line in enumerate(_wrap(draw, item["narration"], THUMB_W, 18, 3)):
            draw.text((x+20, y+338+line_num*23), line,
                      font=font(18), fill=(244, 246, 250))
    draw.text((MARGIN, PAGE_H-42),
              "ÉCHANTILLONS DU MP4 FINAL  •  VALIDATION ÉDITORIALE REQUISE",
              font=font(19), fill=(176, 195, 214))
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest, "JPEG", quality=87, optimize=True)


def generate(*, plan: Path, video: Path, destination: Path,
             max_samples: int = 12) -> dict:
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg and FFprobe required for contact sheets")
    data = load_plan(plan)
    media = probe_media(video)
    scenes = data["scenes"]
    actual = media["durationSeconds"]
    if abs(actual - scenes[-1]["endMs"] / 1000) > 0.85:
        raise ValueError("Video duration does not match scene plan")
    indices = _selection(len(scenes), max_samples)
    entries, errors, warnings = [], [], []
    previous_image = None
    duplicates = 0
    for idx in indices:
        scene = scenes[idx]
        second = (scene["startMs"] + scene["endMs"]) / 2000
        if second > actual:
            errors.append(f"Scene {idx+1} is outside the actual video")
            continue
        try:
            image = _frame_at(video, second)
        except RuntimeError:
            errors.append(f"Unable to decode middle of scene {idx+1}")
            continue
        metrics = _metrics(image)
        if metrics["nearBlackFraction"] >= DARK_THRESHOLD:
            warnings.append(f"Scene {idx+1} is nearly black; inspect manually")
        thumb_gray = ImageOps.grayscale(image.resize((64, 36)))
        if previous_image is not None:
            diff = ImageChops.difference(previous_image, thumb_gray)
            if ImageStat.Stat(diff).mean[0] < 1.0:
                duplicates += 1
        previous_image = thumb_gray
        entries.append({
            "sceneIndex": idx+1, "second": second,
            "narration": scene["narration"],
            "frame": image, "metrics": metrics,
        })
    if not entries:
        raise RuntimeError("No video frames could be extracted")
    dark_count = sum(x["metrics"]["nearBlackFraction"] >= DARK_THRESHOLD for x in entries)
    if len(entries) >= 3 and dark_count > len(entries) // 2:
        errors.append("Most sampled scenes appear almost completely black")
    if len(entries) >= 4 and duplicates >= len(entries)-1:
        warnings.append("Sampled scenes are visually identical; check scene transitions")
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    page_size = 8
    pages = []
    for start in range(0, len(entries), page_size):
        page_no = len(pages)+1
        filename = f"storyboard-{page_no:02d}.jpg"
        _contact_page(entries[start:start+page_size],page=page_no,
                      total_pages=(len(entries)+page_size-1)//page_size,
                      title=data["topic"],dest=destination/filename)
        pages.append(filename)
    report = {
        "schemaVersion": 1,
        "status": "failed" if errors else "review-required" if warnings else "sampled",
        "technicalVisualCheckPassed": not errors,
        "publicationApproved": False,
        "humanReviewRequired": True,
        "videoSha256": _sha(video),
        "sampledSceneCount": len(entries),
        "totalSceneCount": len(scenes),
        "nearBlackSceneCount": dark_count,
        "nearDuplicateNeighborCount": duplicates,
        "pages": pages,
        "frames": [{"sceneIndex": x["sceneIndex"],
                    "timeSeconds": round(x["second"], 3),
                    **x["metrics"]} for x in entries],
        "errors": errors, "warnings": warnings,
        "limitations": [
            "At most 24 sampled mid-scene frames; cannot detect every corrupted frame.",
            "Dark scenes and repeated compositions may be artistically intentional.",
            "No fact-checking, copyright assessment or automatic approval to publish.",
        ],
    }
    _write_json(destination/"visual-review.json", report)
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Review mobile contact sheets from actual MP4 frames")
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--video", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--max-samples", type=int, default=12)
    args = p.parse_args(argv)
    try:
        result = generate(plan=args.plan, video=args.video,
                          destination=args.output, max_samples=args.max_samples)
        print(json.dumps({"status": result["status"],
                          "sampledSceneCount": result["sampledSceneCount"],
                          "pages": result["pages"], "warnings": result["warnings"],
                          "errors": result["errors"]}, ensure_ascii=False))
        return 0 if result["technicalVisualCheckPassed"] else 2
    except (ValueError, RuntimeError, OSError) as exc:
        print("ERROR:", str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
