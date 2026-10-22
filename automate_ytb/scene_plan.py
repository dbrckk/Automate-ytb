"""Prepare reviewable original-image slideshow shot plans (no media generation)."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

STYLE = "Original cinematic 3D illustration, rounded character, soft film lighting"
CAMERAS = ("wide establishing", "medium", "close-up", "over-the-shoulder", "low-angle", "macro")


def beats(script: str) -> list[str]:
    if not isinstance(script, str) or not script.strip() or len(script) > 150_000:
        raise ValueError("Supply an original script with at most 150000 characters")
    text = re.sub(r"\s+", " ", script).strip()
    return [x.strip() for x in re.split(r'(?<=[.!?…])\s+(?=[A-ZÀ-ÖØ-Þ0-9"«])', text) if x.strip()]


def plan(*, topic: str, script: str, duration: int, character: str,
         style: str = STYLE, shot_seconds: float = 6.0) -> dict:
    if not topic.strip() or len(topic) > 180:
        raise ValueError("Invalid topic")
    if not 6 <= len(character.strip()) <= 500 or not 6 <= len(style.strip()) <= 500:
        raise ValueError("An original recurring character and visual style are required")
    if not 30 <= duration <= 3600 or not 3 <= shot_seconds <= 20:
        raise ValueError("Duration must be 30-3600s and shot_seconds must be 3-20s")
    units = beats(script)
    count = round(duration / shot_seconds)
    if len(units) < count:
        raise ValueError(f"Need {count} original narration beats; script contains {len(units)}. "
                         "Supply more script or increase shot_seconds.")
    narration = [" ".join(units[i * len(units) // count:(i + 1) * len(units) // count])
                 for i in range(count)]
    stamps = [round(i * duration * 1000 / count) for i in range(count + 1)]
    scenes = []
    for i, text in enumerate(narration):
        scenes.append({
            "id": f"scene-{i+1:03d}", "startMs": stamps[i], "endMs": stamps[i+1],
            "narration": text,
            "imagePrompt": f"{style}. Original recurring character: {character}. "
                           f"Original illustration of this narration beat: {text}. "
                           "No text or existing logos in the image.",
            "camera": CAMERAS[i % len(CAMERAS)],
            "imageAsset": f"assets/scene-{i+1:03d}.png",
            "assetApproved": False, "assetLicenseEvidence": None,
            "reviewStatus": "pending",
        })
    return {"schemaVersion": 1, "topic": topic, "status": "draft",
            "targetDurationSeconds": duration, "sceneCount": count,
            "sourceScriptSha256": hashlib.sha256(script.encode("utf-8")).hexdigest(),
            "originalCharacterBible": character, "visualStyleBible": style,
            "scenes": scenes, "generationProvider": None,
            "assetUseApproved": False, "publicationApproved": False,
            "warnings": [
                "Validate facts, likeness and rights before image generation.",
                "Prompts do not mean images have been generated.",
                "Subtitles must be aligned with the final narration recording."
            ]}


def main(argv=None):
    p = argparse.ArgumentParser(description="Plan original cinematic image sequences")
    p.add_argument("--topic", required=True)
    p.add_argument("--script", type=Path, required=True)
    p.add_argument("--character", required=True)
    p.add_argument("--style", default=STYLE)
    p.add_argument("--duration", type=int, required=True)
    p.add_argument("--shot-seconds", type=float, default=6.)
    p.add_argument("--output", type=Path, default=Path("scene-plan.json"))
    a = p.parse_args(argv)
    data = plan(topic=a.topic, script=a.script.read_text(encoding="utf-8"),
                character=a.character, style=a.style, duration=a.duration,
                shot_seconds=a.shot_seconds)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"Prepared {data['sceneCount']} original-image scene briefs: {a.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
