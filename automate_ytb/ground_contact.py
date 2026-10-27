"""Deterministic soft ground-contact shadows for original 2D animals.

A bounded blurred shadow sits beneath the moving rig. It follows horizontal
travel but stays on the ground during jumps and flying, making elevation
readable without misleading 3D physics or requiring downloaded textures.
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

GROUND_VERSION = "original-ground-contact-v2-height-aware"
ACTORS = ("owl", "fox", "rabbit", "cat")
WEATHERS = ("day", "night", "cloudy", "rain", "wind", "storm")
ACTIONS = ("idle", "walk", "run", "jump", "fly", "talk", "surprise", "rest")
SHADOW_SIZE = (280, 92)


def draw_contact_shadow(destination: Path, *, actor: str,
                        weather: str, action: str) -> None:
    """Generate an original, translucent contact halo, softly feathered."""
    if actor not in ACTORS or weather not in WEATHERS or action not in ACTIONS:
        raise ValueError("Unsupported original actor, action or weather")
    base_alpha = 58 if weather in ("night", "rain", "storm") else 85
    if action == "fly":
        base_alpha = round(base_alpha * 0.50)
    elif action == "jump":
        base_alpha = round(base_alpha * 0.74)
    shade = (16, 28, 35) if weather != "night" else (10, 18, 30)
    plate = Image.new("RGBA", SHADOW_SIZE, (0, 0, 0, 0))
    brush = ImageDraw.Draw(plate)
    brush.ellipse((23, 28, 257, 78), fill=(*shade, base_alpha))
    brush.ellipse((79, 43, 201, 69),
                  fill=(*shade, min(110, base_alpha + 17)))
    # Blur all edges to avoid a decal-like hard ellipse.
    plate = plate.filter(ImageFilter.GaussianBlur(radius=13))
    destination.parent.mkdir(parents=True, exist_ok=True)
    plate.save(destination, format="PNG", optimize=True)


def shadow_lift(action: str) -> str:
    """Normalized ground clearance for trusted action cues, in [0, 1].

    Jumps use the exact crouch/flight/descent timebase from choreography.
    When phases are present, `action_timeline.choreograph` reanchors this
    local clock and blends the values across authored action boundaries.
    """
    if action not in ACTIONS:
        raise ValueError("Unknown original ground-contact action")
    if action == "jump":
        clock = "mod(t,1.75)"
        rise = f"min(1,max(0,(({clock})-0.18)/0.57))"
        fall = f"min(1,max(0,(({clock})-0.75)/0.64))"
        smooth = lambda v: f"(({v})*({v})*(3-2*({v})))"
        return f"({smooth(rise)}-{smooth(fall)})"
    if action == "fly":
        # Flight remains elevated, with a mild bounded oscillation.
        return "0.60+0.15*sin(t*5.3)"
    return "0"


def shadow_stage(*, body_x: str, ground_y: int, offset_x: int,
                 image_index: int, lift: str = "0") -> str:
    """Composite a height-dependent contact shadow below the animated actor.

    The original RGBA plate remains untouched. During airborne motion FFmpeg
    scales only its width/height; the shadow keeps its ground-plane centre.
    Neither a narration string nor an external expression is accepted here:
    callers supply choreography-generated and validated pose formulas.
    """
    for expression in (body_x, lift):
        if not isinstance(expression, str) or not 1 <= len(expression) <= 25000:
            raise ValueError("Invalid reviewed character pose")
        if any(ch in expression for ch in ";[]'\\\"\\\\:\\r\\n"):
            raise ValueError("Unsafe character pose expression")
    if not isinstance(ground_y, int) or isinstance(ground_y, bool) or not 0 <= ground_y <= 670:
        raise ValueError("Invalid shadow stage location")
    if not isinstance(offset_x, int) or isinstance(offset_x, bool) or not -200 <= offset_x <= 200:
        raise ValueError("Invalid shadow stage location")
    if not isinstance(image_index, int) or isinstance(image_index, bool) or not 1 <= image_index <= 24:
        raise ValueError("Invalid shadow input index")
    if lift == "0":
        # Preserve the zero-cost static path for idle, speech and locomotion.
        return (f"[0:v][{image_index}:v]overlay="
                f"x='({body_x})+{offset_x}':y={ground_y}:"
                f"eval=frame:format=auto[shadowstage];")
    # Clamp after timeline blending to protect scale dimensions during edits.
    clearance = f"min(1,max(0,({lift})))"
    width = f"280-92*({clearance})"
    height = f"92-28*({clearance})"
    return (
        f"[{image_index}:v]scale=w='{width}':h='{height}':"
        "eval=frame[shadowresized];"
        f"[0:v][shadowresized]overlay="
        f"x='({body_x})+{offset_x}+(280-overlay_w)/2':"
        f"y='{ground_y}+(92-overlay_h)/2':"
        "eval=frame:format=auto[shadowstage];"
    )
