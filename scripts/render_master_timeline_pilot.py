"""Render a real original 9:16 cross-beat audiovisual MasterTimeline pilot.

This is an engineering motion+sound proof, NOT a narrated publishable Short.
It uses no third-party media, remote service, mocked frame, or private input.
The story, glyphs, causally linked SFX, and every image frame are rendered.
"""
from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import wave

from PIL import Image, ImageDraw, ImageFont

from automate_ytb.master_timeline import (
    Beat, MasterTimeline, PropertyEvent, SoundCue, WorldObject, VERSION)

DURATION_FRAMES = 180
FPS = 30
AUDIO_RATE = 48000
TITLES = ("THE SIGNAL", "A NEW SCALE", "THE REVEAL")
CHAPTERS = ("GROWTH", "CAMERA FOLLOWS", "EVERYTHING CONNECTS")


def build_timeline() -> MasterTimeline:
    return MasterTimeline(
        total_frames=DURATION_FRAMES, fps=FPS,
        objects=[
            WorldObject("signal", {"x": 0, "value": 1, "scale": 1}, unit="units"),
            WorldObject("camera", {"x": 0, "zoom": 1}),
        ],
        beats=[Beat("growth", 0, 60), Beat("follow", 60, 120),
               Beat("reveal", 120, DURATION_FRAMES)],
        events=[
            PropertyEvent("signal-grow-one", "signal", "value", 15, 95, 1, 8),
            PropertyEvent("signal-grow-two", "signal", "value", 95, 170, 8, 64),
            PropertyEvent("signal-shift", "signal", "x", 35, 175, 0, 135),
            PropertyEvent("signal-scale", "signal", "scale", 20, 170, 1, 1.5),
            PropertyEvent("camera-follow", "camera", "x", 60, 175, 0, 98),
            PropertyEvent("camera-zoom", "camera", "zoom", 65, 170, 1, 1.4),
        ],
        cues=[
            SoundCue("growth-one-sfx", "signal-grow-one", "growth", offset_frames=1),
            SoundCue("follow-sfx", "camera-follow", "whoosh", offset_frames=3),
            SoundCue("growth-two-sfx", "signal-grow-two", "growth", offset_frames=1),
            SoundCue("reveal-sfx", "camera-zoom", "reveal", offset_frames=70),
        ],
    )


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(name, size)


def _background(width: int, height: int) -> Image.Image:
    plate = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(plate)
    for y in range(height):
        a = y / height
        draw.line((0, y, width, y),
                  fill=(round(7 + a * 8), round(17 + a * 15),
                        round(33 + a * 19)))
    for x in range(0, width, max(24, width // 13)):
        draw.line((x, height // 5, x, 4 * height // 5),
                  fill=(23, 48, 65), width=1)
    return plate


def frame_image(timeline: MasterTimeline, frame: int, width: int, height: int,
                backdrop: Image.Image) -> Image.Image:
    state = timeline.state_at(frame)
    signal, camera = state["objects"]["signal"], state["objects"]["camera"]
    picture = backdrop.copy()
    draw = ImageDraw.Draw(picture)
    zoom = camera["zoom"]
    cx = width * .5 + (signal["x"] - camera["x"]) * width / 350 * zoom
    cy = height * .59
    intensity = math.log2(signal["value"] + 1) / math.log2(65)
    radius = round(width * .11 * signal["scale"] * zoom)
    radius = min(radius, width // 3)
    aura = round(radius * (1.6 + .25 * math.sin(frame / 11)))
    for r, color in ((aura, (21, 77, 85)),
                     (round(aura * .73), (29, 110, 116)),
                     (round(radius * 1.16), (58, 173, 166))):
        draw.ellipse((int(cx-r), int(cy-r), int(cx+r), int(cy+r)),
                     fill=color)
    draw.ellipse((int(cx-radius), int(cy-radius),
                  int(cx+radius), int(cy+radius)),
                 fill=(133, 236, 212), outline=(235, 250, 224), width=3)
    # Dynamic measured-height column and pointer follow the same quantity
    # that powers the on-screen number, camera action and related sound cues.
    bottom = round(height * .79)
    tower_height = height * (.13 + .34 * intensity) * zoom
    x0, x1 = round(cx - width * .034), round(cx + width * .034)
    top = round(bottom - tower_height)
    draw.rounded_rectangle((x0, top, x1, bottom), radius=max(4, width // 90),
                           fill=(67, 188, 172))
    draw.rectangle((x0 + max(2, width // 120), top + 3,
                    x0 + max(3, width // 85), bottom - 3),
                   fill=(181, 248, 208))
    draw.line((round(width * .12), bottom, round(width * .88), bottom),
              fill=(188, 216, 212), width=max(2, width // 120))
    y_bar = round(height * .86)
    xleft, xright = round(width * .13), round(width * .87)
    draw.rounded_rectangle((xleft, y_bar, xright, y_bar + max(8, height // 60)),
                           radius=6, fill=(30, 70, 84))
    dx = round((xright - xleft) * intensity)
    draw.rounded_rectangle((xleft, y_bar, max(xleft+1, xleft+dx),
                            y_bar+max(8, height//60)),
                           radius=6, fill=(128, 240, 198))
    font_big = _font(max(28, round(width * .081)), True)
    font_small = _font(max(13, round(width * .044)), False)
    title_font = _font(max(18, round(width * .052)), True)
    draw.text((width*.11, height*.13), "A SIGNAL GROWS",
              font=title_font, fill=(239, 247, 250))
    chapter = CHAPTERS[("growth", "follow", "reveal").index(state["beatId"])]
    draw.text((width*.11, height*.21), chapter,
              font=font_small, fill=(247, 201, 113))
    draw.text((width*.11, height*.30), f'{signal["value"]:05.1f} units',
              font=font_big, fill=(151, 239, 205))
    draw.text((width*.11, height*.93), "MASTER TIMELINE  /  ORIGINAL ENGINEERING PILOT",
              font=_font(max(10, round(width * .023))),
              fill=(174, 196, 205))
    return picture


def render_foley(timeline: MasterTimeline, output: Path) -> dict:
    total_samples = DURATION_FRAMES * AUDIO_RATE // FPS
    buffer = [0.] * total_samples
    all_cues = timeline.audio_events()
    for cue in all_cues:
        start = cue["atSample"]
        freq = {"growth": 360., "whoosh": 150., "reveal": 520.}.get(cue["family"], 300.)
        duration = round((.22 if cue["family"] == "growth" else .33) * AUDIO_RATE)
        amplitude = min(.38, 10 ** (cue["gainDb"] / 20) * 1.7)
        for j in range(min(duration, total_samples-start)):
            t = j / AUDIO_RATE
            attack = min(1., j / (AUDIO_RATE * .008))
            decay = math.exp(-t * (12 if cue["family"] == "growth" else 8))
            chirp = (math.sin(2 * math.pi * (freq * t + 360 * t * t)) +
                     .24 * math.sin(2 * math.pi * freq * 2.1 * t))
            buffer[start+j] += amplitude * attack * decay * chirp
    pcm = array("h")
    for sample in buffer:
        v = round(max(-.8, min(.8, sample)) * 32767)
        pcm.extend((v, v))
    if sys.byteorder != "little":
        pcm.byteswap()
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), "wb") as target:
        target.setnchannels(2)
        target.setsampwidth(2)
        target.setframerate(AUDIO_RATE)
        target.writeframes(pcm.tobytes())
    return {"audioSampleRateHz": AUDIO_RATE, "stereo": True,
            "cueCount": len(all_cues), "sourceEvents": all_cues,
            "source": "original mathematical event-locked tone synthesis"}


def produce(output: Path, *, width: int = 360, height: int = 640) -> dict:
    if (type(width) is not int or type(height) is not int or
            width < 240 or width > 1080 or width * 16 != height * 9
            or width % 2 or height % 2):
        raise ValueError("Pilot requires an even 9:16 portrait size, 240–1080 px wide")
    timeline = build_timeline()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="original-timeline-") as temp:
        stem = Path(temp) / "sfx-original.wav"
        audio = render_foley(timeline, stem)
        args = ["ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}",
                "-r", str(FPS), "-i", "pipe:0",
                "-i", str(stem), "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                "-ar", str(AUDIO_RATE), "-ac", "2", "-movflags", "+faststart",
                str(output)]
        process = subprocess.Popen(args, stdin=subprocess.PIPE,
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.PIPE)
        backdrop = _background(width, height)
        try:
            for index in range(DURATION_FRAMES):
                picture = frame_image(timeline, index, width, height, backdrop)
                process.stdin.write(picture.tobytes())
        except (OSError, BrokenPipeError):
            process.kill()
            raise RuntimeError("FFmpeg failed to consume actual pilot frames") from None
        finally:
            if process.stdin and not process.stdin.closed:
                process.stdin.close()
        try:
            _, diagnostic = process.communicate(timeout=180)
        except ValueError:
            # communicate flushes stdin even when already closed; use wait.
            try:
                process.wait(timeout=180)
                diagnostic = process.stderr.read()
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                raise RuntimeError("Timed out encoding pilot video") from None
        if process.returncode != 0 or not output.is_file() or output.stat().st_size < 2048:
            raise RuntimeError("Real MP4 encoding failed: " +
                               diagnostic.decode("utf-8", "replace")[-800:])
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    result = {
        "engine": VERSION, "technicalPilotOnly": True,
        "publicationApproved": False, "humanReviewed": False,
        "narrationIncluded": False, "soundtrackIncluded": False,
        "durationSeconds": DURATION_FRAMES / FPS,
        "frames": DURATION_FRAMES, "width": width, "height": height, "fps": FPS,
        "audio": audio, "mp4Sha256": digest,
        "stateAtBeatBoundaries": [
            timeline.state_at(i) for i in (0, 59, 60, 119, 120, 179)],
    }
    report_path = output.with_suffix(".json")
    report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Real original cross-scene motion + causal SFX pilot")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--width", type=int, default=360)
    parser.add_argument("--height", type=int, default=640)
    args = parser.parse_args(argv)
    report = produce(args.output, width=args.width, height=args.height)
    print(json.dumps({"status": "technical-pilot-only",
                      "videoSha256": report["mp4Sha256"],
                      "audioCues": report["audio"]["cueCount"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
