"""Independent original second-animal motion for explicitly shared actions.

Only narration with both supported animal species and an explicit shared
movement cue makes the guest walk/run. The guest never lip-syncs or speaks.
No external media, face generation, remote inference or untrusted FFmpeg.
"""
from __future__ import annotations

import re
import unicodedata

COMPANION_RIG_VERSION = "independent-guest-limbs-v1"

_SHARED = re.compile(r"\b(?:together|alongside|with|ensemble|avec|cote a cote)\b")
_RUN = re.compile(r"\b(?:run|runs|running|ran|sprint\w*|cour\w*|galop\w*)\b")
_WALK = re.compile(r"\b(?:walk\w*|stroll\w*|march\w*|promen\w*)\b")

def guest_action(narration: str, *, has_companion: bool) -> str:
    """Choose movement only if original narration explicitly shares it."""
    if not isinstance(narration, str) or len(narration) > 150_000:
        raise ValueError("Invalid original narration for ensemble")
    if not isinstance(has_companion, bool):
        raise ValueError("Invalid companion eligibility")
    if not has_companion:
        return "idle"
    folded = unicodedata.normalize("NFKD", narration.casefold())
    source = "".join(c for c in folded if not unicodedata.combining(c))
    if not _SHARED.search(source):
        return "idle"
    if _RUN.search(source):
        return "run"
    if _WALK.search(source):
        return "walk"
    return "idle"


def guest_animation_graph(*, prior: str, first_input: int,
                          action: str) -> str:
    """Overlay four independent RGBA guest body parts on a 1280x720 frame.

    The guest layer order is tail, torso/ears, left paw, right paw.
    Root movement is shared, but paws alternate and tail follows through.
    Called only by a trusted story renderer with fixed numeric input slots.
    """
    if prior != "shadowstage" or first_input != 11:
        raise ValueError("Untrusted companion renderer entry point")
    if action not in ("idle", "walk", "run"):
        raise ValueError("Untrusted companion gesture")
    stride, cadence, step, bob = {
        "idle": (5, 0.66, 0, 1.11),
        "walk": (11, 4.4, 13, 4.4),
        "run": (20, 7.2, 21, 7.2),
    }[action]
    x = f"813+{stride}*sin(t*{cadence})"
    body_y = f"265+3*sin(t*{bob})"
    tail_y = f"386+3*sin(t*1.7)+4*sin(t*0.63)"
    if step:
        # Positive lift of the swing foot; opposite phase for the other.
        # Stable contact and no reversed 'walking on air' bob.
        left_y = f"502-{step}*max(0,sin(t*{cadence}))"
        right_y = f"502-{step}*max(0,0-sin(t*{cadence}))"
        left_x = f"({x})+48+6*sin(t*{cadence})"
        right_x = f"({x})+131-6*sin(t*{cadence})"
    else:
        left_y, right_y = "502", "502"
        left_x, right_x = f"({x})+48", f"({x})+131"
    return (
        f"[{prior}][{first_input}:v]overlay=x='{x}':"
        f"y='{tail_y}':eval=frame:format=auto[guesttail];"
        f"[guesttail][{first_input+1}:v]overlay=x='{x}':"
        f"y='{body_y}':eval=frame:format=auto[guestbody];"
        f"[guestbody][{first_input+2}:v]overlay=x='{left_x}':"
        f"y='{left_y}':eval=frame:format=auto[guestleft];"
        f"[guestleft][{first_input+3}:v]overlay=x='{right_x}':"
        f"y='{right_y}':eval=frame:format=auto[companions]"
    )
