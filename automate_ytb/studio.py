"""Build original, source-traceable storyboards and deliverable YouTube video drafts.

Only local/explicitly provided assets are used. No competitor media is downloaded.
FFmpeg and an optional espeak-compatible TTS binary power the render.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import textwrap
import unicodedata
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont, ImageOps


WIDTH, HEIGHT = 1280, 720
PALETTES = {
    "cinematic": ((14, 24, 46), (49, 89, 121), (244, 187, 104)),
    "cartoon": ((37, 41, 96), (96, 60, 151), (253, 201, 85)),
    "documentary": ((15, 42, 46), (30, 98, 98), (143, 226, 198)),
    "science": ((9, 27, 48), (19, 73, 105), (111, 225, 242)),
}
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def font(size: int):
    for candidate in FONT_PATHS:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    result = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return result[:64] or "nouvelle-video"


def _valid_web_source(value: str) -> bool:
    try:
        p = urlparse(value)
        return p.scheme == "https" and bool(p.hostname) and (
            p.hostname != "localhost" and not p.hostname.endswith(".local")
        )
    except ValueError:
        return False


def load_brief(path: Path | None, topic: str, angle: str) -> dict:
    brief = json.loads(path.read_text(encoding="utf8")) if path else {}
    if not isinstance(brief, dict):
        raise ValueError("The brief must be a JSON object.")
    facts = brief.get("facts") or []
    if not isinstance(facts, list) or len(facts) > 30:
        raise ValueError("facts must be a list of at most 30 entries.")
    validated = []
    for item in facts:
        if not isinstance(item, dict):
            raise ValueError("Each fact needs claim and source keys.")
        claim, source = item.get("claim"), item.get("source")
        if not isinstance(claim, str) or not 8 <= len(claim) <= 650:
            raise ValueError("A fact must have a claim between 8 and 650 characters.")
        if not isinstance(source, str) or not _valid_web_source(source):
            raise ValueError("Each fact must have a public HTTPS source URL.")
        validated.append({"claim": claim.strip(), "source": source})
    result_topic = topic or str(brief.get("topic") or "")
    result_angle = angle or str(brief.get("angle") or "")
    if not 3 <= len(result_topic.strip()) <= 160:
        raise ValueError("Provide a descriptive topic (3-160 characters).")
    return {"topic": result_topic.strip(),
            "angle": result_angle.strip()[:180] or "Une exploration claire et visuelle",
            "facts": validated}


def video_id_from_reference(raw: str) -> str | None:
    if not raw:
        return None
    p = urlparse(raw)
    if p.scheme != "https":
        raise ValueError("Reference video must use HTTPS.")
    host = (p.hostname or "").lower()
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if p.path == "/watch":
            from urllib.parse import parse_qs
            identifier = parse_qs(p.query).get("v", [""])[0]
        elif p.path.startswith(("/shorts/", "/live/")):
            identifier = p.path.split("/")[2]
        else:
            raise ValueError("Unsupported YouTube URL form.")
    elif host == "youtu.be":
        identifier = p.path.lstrip("/").split("/")[0]
    else:
        raise ValueError("Only a YouTube reference link is accepted.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", identifier):
        raise ValueError("Invalid YouTube video ID.")
    return identifier


def draft_scenes(brief: dict, supplied_script: str = "") -> list[dict]:
    """Build a traceable *draft*, avoiding unsupported research assertions."""
    topic, angle, facts = brief["topic"], brief["angle"], brief["facts"]
    if supplied_script.strip():
        chunks = [x.strip() for x in re.split(r"\n\s*\n", supplied_script) if x.strip()]
        if not 2 <= len(chunks) <= 18:
            raise ValueError("Separate an original script into 2-18 paragraphs.")
        if any(len(c) > 1100 for c in chunks):
            raise ValueError("A scene paragraph is too long (max 1,100 characters).")
        titles = ["INTRODUCTION"] + ["CHAPITRE " + str(i) for i in range(2, len(chunks))]
        titles.append("CONCLUSION")
        return [{"title": titles[i], "narration": text,
                 "evidenceUrls": []} for i, text in enumerate(chunks)]
    scenes = [
        {"title": "LE SUJET", "narration":
         "Aujourd'hui, nous explorons une question : " + topic
         + ". Notre approche : " + angle.rstrip(".") + ".",
         "evidenceUrls": []},
        {"title": "L'ENJEU", "narration":
         "Pour comprendre ce sujet, il faut distinguer les observations "
         "des hypothèses, puis regarder quelles informations peuvent être vérifiées.",
         "evidenceUrls": []},
    ]
    for fact in facts[:8]:
        scenes.append({"title": "LE POINT CLÉ", "narration": fact["claim"],
                       "evidenceUrls": [fact["source"]]})
    scenes.extend([
        {"title": "PRENDRE DU RECUL", "narration":
         "Les exemples et les explications ne remplacent pas la consultation "
         "des sources. Vérifiez les dates et le contexte avant de conclure.",
         "evidenceUrls": []},
        {"title": "POUR ALLER PLUS LOIN", "narration":
         "Cette exploration est un point de départ. Retrouvez les sources "
         "associées au projet, puis partagez les questions qui méritent un examen plus approfondi.",
         "evidenceUrls": []},
    ])
    return scenes


def distribute_duration(scenes: list[dict], seconds: float) -> list[float]:
    weights = [max(3, len(re.findall(r"\b[\wÀ-ÿ'-]+\b", s["narration"]))) for s in scenes]
    total = sum(weights)
    if seconds < len(scenes) * 3:
        seconds = len(scenes) * 3
    durations = [round(seconds * w / total, 2) for w in weights]
    durations[-1] = round(seconds - sum(durations[:-1]), 2)
    return durations


def duration_of_media(path: Path, ffprobe: str = "ffprobe") -> float:
    if path.suffix.lower() == ".wav":
        import wave
        try:
            with wave.open(str(path), "rb") as w:
                return w.getnframes() / w.getframerate()
        except (wave.Error, EOFError):
            pass
    if shutil.which(ffprobe):
        result = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            check=True, capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip())
    # A basic FFmpeg binary is sufficient for inspecting user-supplied audio.
    if shutil.which("ffmpeg"):
        proc = subprocess.run(
            ["ffmpeg", "-hide_banner", "-i", str(path)],
            capture_output=True, text=True, timeout=30
        )
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", proc.stderr)
        if match:
            return int(match[1]) * 3600 + int(match[2]) * 60 + float(match[3])
    raise RuntimeError("Could not determine narration duration.")


def _wrap(draw, text: str, size: int, max_width: int, max_lines: int = 5):
    f = font(size)
    words, lines = text.split(), []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if current and draw.textbbox((0, 0), candidate, font=f)[2] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        if size <= 24:
            lines = lines[:max_lines]
            lines[-1] = lines[-1][:max(0, len(lines[-1]) - 3)] + "..."
            return lines, f
        size = max(24, int(size * max_lines / len(lines)))
        return _wrap(draw, text, size, max_width, max_lines)
    return lines, f


def _gradient(back, front):
    image = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    for y in range(HEIGHT):
        a = min(1., y / HEIGHT)
        blend = tuple(int((1 - a) * b + a * f) for b, f in zip(back, front))
        draw.line([(0, y), (WIDTH, y)], fill=blend)
    return image


def render_art(title: str, narrative: str, scene_number: int, count: int,
               style: str, out: Path, background: Path | None = None):
    base, second, accent = PALETTES[style]
    if background:
        with Image.open(background) as input_image:
            image = ImageOps.fit(input_image.convert("RGB"), (WIDTH, HEIGHT))
        veil = Image.new("RGB", image.size, base)
        image = Image.blend(image, veil, 0.52)
    else:
        image = _gradient(base, second)
    draw = ImageDraw.Draw(image)
    for i in range(7):
        r = 95 + i * 48
        x, y = 1060 - i * 31, 250 + i * 16
        draw.ellipse((x-r, y-r, x+r, y+r), outline=tuple(
            min(255, int(c * (0.2 + i * .055))) for c in accent), width=4)
    draw.rounded_rectangle((56, 52, 354, 106), radius=26, fill=accent)
    draw.text((82, 62), "AUTOMATE  /  YTB", fill=base, font=font(24))
    draw.text((60, 164), title[:60], fill=accent, font=font(32))
    short = " ".join(narrative.split())
    while True:
        lines, f = _wrap(draw, short, 58, 1050, 5)
        if len(lines) <= 5:
            break
    top = 235
    for line in lines:
        draw.text((60, top), line, font=f, fill=(250, 252, 255),
                  stroke_width=1, stroke_fill=(12, 20, 34))
        top += f.size + 17
    draw.line((60, 635, WIDTH-60, 635), fill=accent, width=2)
    draw.text((62, 655), "VIDEO ORIGINALE  ·  BROUILLON A VERIFIER",
              font=font(19), fill=(226, 238, 247))
    draw.text((1120, 647), f"{scene_number:02d}/{count:02d}",
              font=font(26), fill=accent)
    image.save(out, format="PNG")


def make_thumbnails(topic: str, style: str, out_dir: Path):
    out = []
    short = topic[:95]
    designs = [
        ("LA QUESTION", short, style),
        ("COMPRENDRE", short, "cartoon" if style != "cartoon" else "documentary"),
        ("L'ESSENTIEL", short, "documentary" if style != "documentary" else "cinematic"),
    ]
    for idx, (header, body, theme) in enumerate(designs, start=1):
        target = out_dir / f"thumbnail-{idx}.png"
        render_art(header, body, idx, 3, theme, target)
        out.append(target)
    return out


def _srt_seconds(seconds: float) -> str:
    ms = max(0, round(seconds * 1000))
    hours, remain = divmod(ms, 3600000)
    minutes, remain = divmod(remain, 60000)
    secs, millis = divmod(remain, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def make_srt(scenes: list[dict], timings: list[float], out: Path):
    blocks, cursor = [], 0.
    for i, (scene, d) in enumerate(zip(scenes, timings), 1):
        blocks.append(f"{i}\n{_srt_seconds(cursor)} --> {_srt_seconds(cursor + d)}\n"
                      + scene["narration"] + "\n")
        cursor += d
    out.write_text("\n".join(blocks), encoding="utf8")


def synthesize_voice(text: str, output: Path, language: str, rate: int = 148) -> bool:
    program = shutil.which("espeak-ng") or shutil.which("espeak")
    if not program:
        return False
    input_file = output.parent / "narration.txt"
    input_file.write_text(text, encoding="utf8")
    subprocess.run([program, "-v", language, "-s", str(rate),
                    "-f", str(input_file), "-w", str(output)],
                   check=True, timeout=160, capture_output=True)
    return output.is_file() and output.stat().st_size > 1024


def render_video(images: list[Path], durations: list[float], target: Path,
                 narration: Path | None, ffmpeg: str = "ffmpeg"):
    if not shutil.which(ffmpeg):
        raise RuntimeError("FFmpeg not available. Install ffmpeg or use --plan-only.")
    concat = target.parent / "frames.ffconcat"
    parts = ["ffconcat version 1.0"]
    for image, duration in zip(images, durations):
        # All paths are generated locally, but escape for concat format anyway.
        absolute = str(image.resolve()).replace("'", "'\\''")
        parts += [f"file '{absolute}'", f"duration {duration:.3f}"]
    parts.append("file '" + str(images[-1].resolve()).replace("'", "'\\''") + "'")
    concat.write_text("\n".join(parts) + "\n", encoding="utf8")
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
           "-safe", "0", "-f", "concat", "-i", str(concat)]
    if narration:
        cmd += ["-i", str(narration)]
    cmd += ["-vf", "fps=24,format=yuv420p", "-c:v", "libx264",
            "-preset", "veryfast", "-crf", "21", "-movflags", "+faststart",
            "-t", str(round(sum(durations), 3))]
    cmd += ["-c:a", "aac", "-b:a", "160k"] if narration else ["-an"]
    cmd += [str(target)]
    subprocess.run(cmd, check=True, capture_output=True, timeout=360)
    if not target.is_file() or target.stat().st_size < 10_000:
        raise RuntimeError("FFmpeg did not produce a valid output.")


def build(topic: str, out_root: Path, *, brief_path: Path | None = None,
          angle: str = "", script_path: Path | None = None, assets_dir: Path | None = None,
          audio_file: Path | None = None, reference: str = "", style: str = "cinematic",
          language: str = "fr", duration: int = 90, plan_only: bool = False,
          tts: str = "espeak") -> dict:
    if style not in PALETTES:
        raise ValueError("Unsupported visual style.")
    if not 30 <= duration <= 3600:
        raise ValueError("Duration must be between 30 and 3600 seconds.")
    if language not in {"fr", "en"}:
        raise ValueError("Supported voice languages: fr, en.")
    video_id = video_id_from_reference(reference)
    brief = load_brief(brief_path, topic, angle)
    script = script_path.read_text(encoding="utf8") if script_path else ""
    scenes = draft_scenes(brief, script)
    if len(scenes) > 18:
        raise ValueError("Too many scenes.")
    root = out_root / slugify(brief["topic"])
    root.mkdir(parents=True, exist_ok=True)
    (root / "storyboard").mkdir(exist_ok=True)
    (root / "thumbnails").mkdir(exist_ok=True)
    combined = "\n\n".join(x["narration"] for x in scenes)
    (root / "script.txt").write_text(combined, encoding="utf8")
    voice_path = None
    voice_status = "none"
    warnings = ["Human verification required before publication.",
                "Reference URL is for creative analysis only; no third-party media is copied.",
                "No financial or reach estimates are inferred from competitor analytics."]
    if audio_file:
        if audio_file.suffix.lower() not in {".wav", ".mp3", ".m4a", ".flac"}:
            raise ValueError("Audio file must be WAV, MP3, M4A or FLAC.")
        voice_path = root / ("narration" + audio_file.suffix.lower())
        shutil.copyfile(audio_file, voice_path)
        voice_status = "provided"
    elif tts == "espeak" and not plan_only:
        voice_path = root / "narration.wav"
        if synthesize_voice(combined, voice_path, language):
            voice_status = "espeak-draft"
            warnings.append("Built-in espeak voice is a draft; replace it for professional output.")
        else:
            voice_path = None
            warnings.append("No espeak TTS available; video is silent.")
    elif tts not in {"off", "espeak"}:
        raise ValueError("TTS must be espeak or off.")
    final_duration = float(duration)
    if voice_path:
        final_duration = max(final_duration, math.ceil(duration_of_media(voice_path)) + 2)
    timing = distribute_duration(scenes, final_duration)
    assets = []
    for i, scene in enumerate(scenes, 1):
        target = root / "storyboard" / f"scene-{i:02d}.png"
        background = None
        if assets_dir:
            for ext in (".png", ".jpg", ".jpeg", ".webp"):
                candidate = assets_dir / f"scene-{i:02d}{ext}"
                if candidate.is_file():
                    background = candidate
                    break
        render_art(scene["title"], scene["narration"], i, len(scenes),
                   style, target, background)
        assets.append(target)
        scene["durationSeconds"] = timing[i-1]
        scene["image"] = str(target.relative_to(root))
    thumbs = make_thumbnails(brief["topic"], style, root / "thumbnails")
    # Production-ready prompt pack for external authorized visual generators:
    # no claim is made that the placeholder slide art is generative AI.
    visual_tone = {
        "cinematic": "cinematic editorial illustration, soft volumetric light",
        "cartoon": "original rounded 3D storybook characters, warm expressive shapes",
        "documentary": "clean documentary infographics and restrained cinematography",
    }[style]
    prompts = [{
        "scene": i, "durationSeconds": scene["durationSeconds"],
        "imagePrompt": (
            "Create an ORIGINAL 16:9 illustration for an educational YouTube video. "
            + visual_tone + ". Consistent character design, art direction and lighting. "
            "Visualize this narration faithfully (do not place text in image): "
            + scene["narration"][:500]
        ),
        "negativePrompt": (
            "No logos, watermarks, copyrighted characters, real-person likenesses, "
            "factual overlays or copied competitor frames."
        ),
        "editorialReviewRequired": True,
    } for i, scene in enumerate(scenes, 1)]
    (root / "visual-generation-prompts.json").write_text(
        json.dumps({"provider": "optional (Higgsfield or owned model)",
                    "providerExecuted": False, "visualStyle": style,
                    "shots": prompts, "thumbnailCount": 3},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )
    make_srt(scenes, timing, root / "captions.srt")
    title = brief["topic"][:94]
    description = (brief["angle"] + "\n\n"
                   + "Sources à vérifier :\n"
                   + "\n".join(sorted({x["source"] for x in brief["facts"]}))
                   + "\n\nContenu original · vérification éditoriale obligatoire.")
    (root / "youtube-metadata.json").write_text(json.dumps({
        "title": title, "description": description,
        "tags": [s for s in slugify(brief["topic"]).split("-") if len(s) > 3][:12],
        "visibilityRecommended": "private",
        "manualPublishRequired": True
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    manifest = {
        "version": "0.1", "createdAt": datetime.now(timezone.utc).isoformat(),
        "topic": brief["topic"], "angle": brief["angle"],
        "reference": {
            "url": reference or None, "youtubeVideoId": video_id,
            "analysisStatus": "manual-review-needed" if reference else "not-supplied",
            "originalMediaDownloaded": False
        }, "style": style, "language": language,
        "renderMode": "plan-only" if plan_only else "video-draft",
        "voiceStatus": voice_status, "requestedDurationSeconds": duration,
        "plannedDurationSeconds": round(sum(timing), 2),
        "facts": brief["facts"], "scenes": scenes,
        "thumbnails": [str(x.relative_to(root)) for x in thumbs],
        "manualReviewRequired": True, "youtubeUploaded": False,
        "warnings": warnings,
    }
    if not plan_only:
        target = root / "video-draft.mp4"
        render_video(assets, timing, target, voice_path)
        manifest["video"] = target.name
    (root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )
    return {"folder": str(root), "manifest": manifest}
