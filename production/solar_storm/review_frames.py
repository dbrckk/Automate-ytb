"""Review actual decoded frames from a Solar Storm release, not source stills.

This is a technical/editorial aid only. It never approves footage for publishing.
"""
from __future__ import annotations

from io import BytesIO
import math
from pathlib import Path
import subprocess

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat


EXPECTED_SIZE = (1080, 1920)


def _frame(video: Path, second: float) -> Image.Image:
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{second:.3f}",
         "-i", str(video), "-an", "-frames:v", "1", "-f", "image2pipe",
         "-vcodec", "png", "pipe:1"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=100,
    )
    if not result.stdout:
        raise RuntimeError(f"MP4 frame missing at {second:.3f}s")
    with Image.open(BytesIO(result.stdout)) as raw:
        raw.load()
        image = raw.convert("RGB")
    if image.size != EXPECTED_SIZE:
        raise RuntimeError(f"Unexpected decoded frame size: {image.size}")
    return image


def _signature(image: Image.Image) -> int:
    gray = image.convert("L").resize((16, 16), Image.Resampling.LANCZOS)
    pixels = list(gray.getdata())
    average = sum(pixels) / len(pixels)
    return sum((value >= average) << index for index, value in enumerate(pixels))


def create_contact_sheet(video: Path, segments: list[dict], output: Path,
                         *, labels: list[str] | None = None) -> dict:
    """Fail on corrupt/fully black frames; flag suspicious visual repetition.

    The sampled middle frame is one per actual spoken scene. Images appear only
    in the external review artifact; no frame numbers are embedded into the MP4.
    """
    video, output = Path(video), Path(output)
    max_samples = 24 if labels is not None else 12
    if not video.is_file() or not 1 <= len(segments) <= max_samples:
        raise ValueError("Need an encoded video and a valid review timeline")
    if labels is not None and (len(labels) != len(segments) or
            any(not isinstance(label, str) or not 1 <= len(label) <= 35 or
                "\\n" in label or "\\r" in label for label in labels)):
        raise ValueError("Invalid review frame labels")
    entries: list[dict] = []
    signatures: list[int] = []
    thumbnails: list[Image.Image] = []
    tiles: list[Image.Image] = []
    previous_end = 0.0
    for index, segment in enumerate(segments):
        start, end = float(segment["start"]), float(segment["end"])
        if (not math.isfinite(start) or not math.isfinite(end) or
                start < previous_end - 0.05 or end <= start or end-start > 60):
            raise ValueError(f"Invalid narration scene timeline: {index + 1}")
        second = start + (end - start) / 2
        image = _frame(video, second)
        small = image.resize((90, 160), Image.Resampling.BILINEAR)
        # A dark NASA solar background is valid; an all-black failed encode is not.
        values = list(small.getdata())
        black = sum(max(pixel) <= 9 for pixel in values) / len(values)
        contrast = max(ImageStat.Stat(small).stddev)
        if black > 0.998 and contrast < 5.0:
            raise RuntimeError(f"Blank decoded Solar Storm frame: scene {index + 1}")
        signature = _signature(image)
        # AHash alone groups visually different NASA false-color sources.
        # Also require close actual RGB imagery before warning about repetition.
        thumb = image.resize((24, 24), Image.Resampling.BILINEAR)
        similarities = [i+1 for i, (earlier, old_thumb) in
                        enumerate(zip(signatures, thumbnails))
                        if (signature ^ earlier).bit_count() <= 4 and
                        sum(ImageStat.Stat(ImageChops.difference(
                            thumb, old_thumb)).mean) / 3 < 16]
        entries.append({"scene": index+1, "at_seconds": round(second, 3),
                        "black_fraction": round(black, 4),
                        "channel_contrast": round(contrast, 2),
                        "possible_duplicate_of": similarities})
        signatures.append(signature)
        thumbnails.append(thumb)
        tiles.append(image.resize((360, 640), Image.Resampling.LANCZOS))
        previous_end = end

    cols = min(3, len(tiles))
    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (cols*360, rows*686), (12, 19, 29))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    for index, tile in enumerate(tiles):
        x, y = (index % cols)*360, (index // cols)*686
        sheet.paste(tile, (x, y))
        item = entries[index]
        caption = (labels[index] if labels is not None else
                   f"SCENE {index+1}  •  {item['at_seconds']:.1f}s")
        draw.text((x+13, y+648),
                  caption,
                  font=font, fill=(232, 239, 247))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, format="JPEG", quality=88, optimize=True)
    return {
        "status": "decoded",
        "source": video.name,
        "sampled_scenes": len(entries),
        "external_contact_sheet": output.name,
        "frames": entries,
        "warnings": [f"Scenes {entry['possible_duplicate_of']} and {entry['scene']} may look similar"
                     for entry in entries if entry["possible_duplicate_of"]],
        "editorial_approved": False,
        "note": "Scene sampling cannot certify scientific correctness or rights; review the full MP4.",
    }
