"""Independently animated original 2D companion, with script-grounded motion.

No fabricated speech or unmentioned running: only explicit shared travel
activates articulated guest legs. This is offline Pillow/FFmpeg, not 3D IK.
"""
from __future__ import annotations

import re
import unicodedata

COMPANION_RIG_VERSION = "independent-companion-v2-foreground-shadow"

_SHARED = re.compile(r"\b(?:together|alongside|with|ensemble|avec|cote a cote)\b")
_RUN = re.compile(r"\b(?:run|runs|running|ran|sprint\w*|cour\w*|galop\w*)\b")
_WALK = re.compile(r"\b(?:walk\w*|stroll\w*|march\w*|promen\w*)\b")


def guest_action(narration: str, *, has_companion: bool) -> str:
    """Return walk/run only when two participants explicitly travel together."""
    if not isinstance(narration, str) or len(narration) > 150_000:
        raise ValueError("Invalid original companion narration")
    if not isinstance(has_companion, bool):
        raise ValueError("Invalid companion eligibility")
    if not has_companion:
        return "idle"
    decomposed = unicodedata.normalize("NFKD", narration.casefold())
    source = "".join(c for c in decomposed if not unicodedata.combining(c))
    if not _SHARED.search(source):
        return "idle"
    if _RUN.search(source):
        return "run"
    if _WALK.search(source):
        return "walk"
    return "idle"


def guest_animation_graph(*, prior: str, first_input: int, action: str) -> str:
    """Render companion ground shadow, tail, body, two feet and blink plate.

    Fixed input slots for one explicitly declared second animal:
      11 tail, 12 body, 13 left leg, 14 right leg, 15 blink body, 16 shadow.
    The foreground remains layered behind the main animal.
    """
    if prior != "shadowstage" or first_input != 11:
        raise ValueError("Unexpected companion graph topology")
    if action not in {"idle", "walk", "run"}:
        raise ValueError("Untrusted guest gesture")
    stride, cadence, lift = {
        "idle": (5, 0.66, 0),
        "walk": (11, 4.4, 13),
        "run": (20, 7.2, 21),
    }[action]
    root_x = f"813+{stride}*sin(t*{cadence})+1.5*sin(t*0.39)"
    body_y = "265+2*sin(t*1.06)"
    tail_y = "386+3*sin(t*1.7)+4*sin(t*0.63)"
    if lift:
        left_y = f"502-{lift}*max(0,sin(t*{cadence}))"
        right_y = f"502-{lift}*max(0,0-sin(t*{cadence}))"
        left_x = f"({root_x})+48+6*sin(t*{cadence})"
        right_x = f"({root_x})+131-6*sin(t*{cadence})"
    else:
        left_y = right_y = "502"
        left_x = f"({root_x})+48"
        right_x = f"({root_x})+131"
    return (
        f"[{prior}][{first_input+5}:v]overlay=x='({root_x})+18':"
        "y=571:eval=frame:format=auto[guestground];"
        f"[guestground][{first_input}:v]overlay=x='{root_x}':"
        f"y='{tail_y}':eval=frame:format=auto[guesttail];"
        f"[guesttail][{first_input+1}:v]overlay=x='{root_x}':"
        f"y='{body_y}':eval=frame:format=auto[guestbody];"
        f"[guestbody][{first_input+2}:v]overlay=x='{left_x}':"
        f"y='{left_y}':eval=frame:format=auto[guestleft];"
        f"[guestleft][{first_input+3}:v]overlay=x='{right_x}':"
        f"y='{right_y}':eval=frame:format=auto[companions];"
        f"[companions][{first_input+4}:v]overlay=x='{root_x}':"
        f"y='{body_y}':enable='lt(mod(t+0.65,3.4),0.12)':"
        "eval=frame:format=auto[guestblink]"
    )
