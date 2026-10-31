"""Voice-synchronized original 2D motion graphics for the NASA Solar Storm Short.

ASS vector shapes are composited in the final FFmpeg render, not in NASA files.
Only authored, non-metric diagram cues are shown: no implied simulated measurements.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import re

# Scene index -> (heard token, animated title, short explanatory tag).
CUES = (
    ("sun", "SOLAR STORM", "SUN TO EARTH"),
    ("nasa", "NASA / SDO", "REAL SOLAR OBSERVATIONS"),
    ("plasma", "CORONAL MASS EJECTION", "PLASMA LEAVES THE SUN"),
    ("magnetic", "EARTH'S MAGNETIC SHIELD", "SCHEMATIC FIELD RESPONSE"),
    ("satellites", "SPACE WEATHER EFFECTS", "SATELLITES + AURORAS"),
    ("earth", "OUR CONNECTED SYSTEM", "SUN + EARTH"),
)
COLORS = ("&H0054CCFF&", "&H0093ECFF&", "&H003BB5FF&",
          "&H00DDBB78&", "&H00E8DE81&", "&H00E2D8BE&")
STYLE = (
    "Style: Motion,DejaVu Sans,42,&H00FFFFFF,&H00FFFFFF,&H00241911,"
    "&H700E111A,-1,0,0,0,100,100,0,0,1,3,1,7,74,74,360,1\n"
)


def _time(sec: float) -> str:
    cs = max(0, round(sec * 100))
    hours, rest = divmod(cs, 360000)
    mins, rest = divmod(rest, 6000)
    seconds, rest = divmod(rest, 100)
    return f"{hours}:{mins:02}:{seconds:02}.{rest:02}"


def _token(word: str) -> str:
    return re.sub("[^a-z]", "", word.lower())


def _cue_anchor(scene: dict, words: list[dict], token: str) -> tuple[float, str]:
    start, end = float(scene["start"]), float(scene["end"])
    matching = [float(w["start"]) for w in words
                if w.get("recognized") is True and
                _token(str(w.get("word", ""))) == token and
                start <= float(w.get("start", -1)) < end]
    if matching:
        return matching[0], "verified_acoustic_word"
    # The graphics still correspond to the right authored scene but we do not
    # falsely claim sub-word synchronization when the recognizer missed it.
    return start + min(0.55, (end - start) * 0.20), "narration_scene_fallback"


def _dialogue(layer: int, begin: float, end: float, payload: str) -> str:
    if not (0 <= begin < end and math.isfinite(begin) and math.isfinite(end)):
        raise ValueError("Invalid motion graphics cue timestamp")
    return f"Dialogue: {layer},{_time(begin)},{_time(end)},Motion,,0,0,0,,{payload}"


def _vector(path: str, color: str, *, opacity: str = "45",
            border: float = 3, blur: float = 2) -> str:
    if not re.fullmatch(r"(?:[mlb] [0-9 \-]+ ?)+", path.strip() + " "):
        raise ValueError("Unsafe or malformed vector graphics path")
    return (r"{\an7\pos(0,0)\p1\1a&HFF&\3a&H" + opacity +
            r"&\3c" + color + r"\bord" + str(border) + r"\blur" +
            str(blur) + r"\fad(200,280)}" + path + r"{\p0}")


def _animated_paths(scene_index: int, begin: float, end: float,
                    color: str) -> list[str]:
    """Schematic, restrained motion only during the relevant narrated beat."""
    lines = []
    span = end - begin
    if scene_index in (0, 1):
        # Tracking reticle: separate small corner lines, never a false data grid.
        strokes = ("m 724 770 l 724 830 m 724 770 l 784 770",
                   "m 1002 770 l 942 770 m 1002 770 l 1002 830",
                   "m 724 1130 l 724 1070 m 724 1130 l 784 1130",
                   "m 1002 1130 l 942 1130 m 1002 1130 l 1002 1070")
        for idx, path in enumerate(strokes):
            a = begin + 0.12 * idx
            b = min(end, a + span * 0.84)
            if b - a > 0.15:
                lines.append(_dialogue(1, a, b, _vector(path, color, opacity="72")))
    elif scene_index == 2:
        # Solar ejecta: directed trails and three moving specks, diagram only.
        for idx, y in enumerate((860, 950, 1040)):
            a = begin + 0.08 * idx
            b = min(end, a + span * 0.92)
            if b <= a + 0.2:
                continue
            path = f"m 115 {y} b 290 {y-75} 480 {y-160} 780 {y-210}"
            lines.append(_dialogue(1, a, b,
                                    _vector(path, color, opacity="73", border=3)))
            # Moving dots actually travel with the narrated solar material.
            dot = ("{\\an7\\move(200," + str(y-37) + ",770," + str(y-205) +
                   ",0," + str(round((b-a)*1000)) +
                   ")\\fad(90,210)\\1c" + color +
                   "\\bord0\\blur2\\p1}m -9 0 b -9 -12 9 -12 9 0 "
                   "b 9 12 -9 12 -9 0{\\p0}")
            lines.append(_dialogue(3, a, b, dot))
    elif scene_index == 3:
        # Schematized magnetic field lines, distinct from real NASA observations.
        for idx, displacement in enumerate((0, 65, 130)):
            a = begin + 0.12 * idx
            b = min(end, a + span * 0.85)
            if b <= a + 0.2:
                continue
            p = (f"m {735-displacement} 1145 "
                 f"b {680-displacement} 985 {680-displacement} 795 "
                 f"{740-displacement} 650")
            lines.append(_dialogue(1, a, b, _vector(p, color, opacity="83", border=3)))
    elif scene_index == 4:
        # Dotted orbital communication arcs. Label explicitly says "effects".
        for idx, y in enumerate((845, 925, 1005)):
            a = begin + 0.10 * idx
            b = min(end, a + span * 0.88)
            if b <= a + 0.2:
                continue
            path = f"m 775 {y} b 850 {y-60} 950 {y-60} 1010 {y}"
            lines.append(_dialogue(1, a, b, _vector(path, color, opacity="78")))
        for idx in range(4):
            a = begin + 0.22 * idx
            b = min(end, a + 0.75)
            if b > a + 0.15:
                lines.append(_dialogue(2, a, b, _vector(
                    f"m {815+idx*38} 1060 l {832+idx*38} 1060",
                    color, opacity="25", border=5, blur=4)))
    else:
        # Closing orbit lines for a visual return to the Sun/Earth connection.
        for idx in range(2):
            a = begin + idx * 0.2
            b = min(end, a + span * 0.85)
            if b > a + 0.2:
                path = ("m 750 870 b 850 780 970 810 1008 932 "
                        "b 1020 1060 900 1160 760 1090") if idx == 0 else (
                        "m 777 1100 b 695 1015 710 905 805 840")
                lines.append(_dialogue(1, a, b,
                                       _vector(path, color, opacity="82")))
    return lines


def build_motion_graphics(segments: list[dict], words: list[dict]) -> tuple[list[str], dict]:
    if len(segments) != len(CUES):
        raise ValueError("Solar motion graphics require exactly 6 narration scenes")
    if not isinstance(words, list):
        raise ValueError("Expected acoustic word alignment")
    rows: list[str] = []
    anchors = []
    last_end = 0.0
    for index, (scene, (token, title, subtitle)) in enumerate(zip(segments, CUES)):
        start, end = float(scene["start"]), float(scene["end"])
        if not (math.isfinite(start) and math.isfinite(end) and
                start >= last_end - 0.06 and end - start >= 1.1):
            raise ValueError(f"Invalid spoken scene {index+1}")
        anchor, origin = _cue_anchor(scene, words, token)
        begin = min(end-0.75, max(start+0.12, anchor-0.12))
        finish = min(end-0.12, begin+2.35)
        color = COLORS[index]
        if finish <= begin + .35:
            raise ValueError("Insufficient voice-timed graphic cue duration")
        title_tags = (r"{\an7\move(74,222,74,205,0,320)\fad(200,270)"
                      r"\blur0.35\1c" + color + r"}")
        sub_tags = (r"{\an7\move(78,288,78,273,0,370)\fad(220,280)"
                    r"\fs27\bord2\1c&H00FFFFFF&}")
        rows.append(_dialogue(7, begin, finish, title_tags + title))
        rows.append(_dialogue(6, begin+0.12, finish,
                              sub_tags + subtitle))
        # A lightweight horizontal rule visually ties the label to the footage.
        rows.append(_dialogue(2, begin+0.05, min(finish, begin+1.90),
                               _vector("m 76 322 l 395 322", color,
                                       opacity="90", border=2, blur=1)))
        rows.extend(_animated_paths(index, begin, finish, color))
        anchors.append({"scene": index+1, "word": token,
                        "source": origin, "start": round(begin, 3),
                        "end": round(finish, 3), "effect": title,
                        "vector_events": len(rows)})
        last_end = end
    return rows, {
        "engine": "narration-anchored-ass-v1",
        "events": len(rows),
        "spoken_cues": len(anchors),
        "verified_word_cues": sum(a["source"] == "verified_acoustic_word"
                                  for a in anchors),
        "cue_timeline": anchors,
        "overlays_only_in_final_video": True,
        "origin": "original ASS vector choreography; no generative video API",
        "editorial_approved": False,
    }


def apply_motion_graphics(captions_path: Path,
                          scenes: list[dict], words: list[dict]) -> dict:
    path = Path(captions_path)
    content = path.read_text(encoding="utf-8")
    if ("[V4+ Styles]" not in content or "\n[Events]" not in content or
            "Style: Motion," in content):
        raise ValueError("Missing ASS styles/events or already composited graphics")
    events, report = build_motion_graphics(scenes, words)
    # The older captions renderer also drew long-lived Context titles for
    # scenes 2-5. Once the voice-anchored Motion HUD is installed those become
    # repeated overprints (confirmed in the actual decoded NASA H.264 MP4).
    # Retire ONLY Context dialogue rows, never acoustic Voice subtitles,
    # timestamp rows, SRT captions, styles or source attribution metadata.
    legacy_context = re.compile(
        r"^Dialogue: [0-9]+,[^,\\n]+,[^,\\n]+,Context,")
    original_lines = content.splitlines(keepends=True)
    cleaned = [line for line in original_lines
               if not legacy_context.match(line)]
    report["suppressed_legacy_context_titles"] = (
        len(original_lines) - len(cleaned))
    content = "".join(cleaned)
    # ASS styles belong before [Events]; all motion event rows are appended.
    content = content.replace("\n[Events]", STYLE + "\n[Events]", 1)
    path.write_text(content.rstrip("\n") + "\n" + "\n".join(events) + "\n",
                    encoding="utf-8")
    return report
