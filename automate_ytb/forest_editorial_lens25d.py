"""Subtle editorial rack-focus at voice-paced physical shot changes.

Unlike dissolving still pictures, every source frame retains live animation;
only a brief optical defocus eases the viewer into the next animated scene.
Captions are placed *after* this transform and always remain sharp.
"""
from __future__ import annotations

import math

from PIL import Image, ImageFilter

from .forest_voice_timeline import TimedBeat

VERSION="forest-25d-measured-cut-rack-focus-p47-v1"
SIZE=(1080,1920)
DURATION=.18


def focus_radius(t: float, beat: TimedBeat) -> float:
    if (type(t) not in (int,float) or not math.isfinite(t)
            or not isinstance(beat,TimedBeat)
            or not beat.start<=t<=beat.end+.50):
        raise ValueError("Invalid voice-paced cinematic lens clock")
    # Measured timeline beats use non-binary-exact decimal boundaries.
    # Snap the physically finished rack focus to exact zero at the cut end.
    # The measured narration leaves a natural 0.35s visual/audio tail
    # after the final speech. Preserve a sharp held end without mistaking
    # that intentional breathing room for an invalid shot clock.
    if t>=beat.end or beat.name=="discovery" or t-beat.start>=DURATION-1e-9:
        return 0.
    q=max(0.,min(1.,(t-beat.start)/DURATION))
    # A smoothly decaying blur, strongest immediately AFTER the hard cut.
    return 1.65*(1-q)**2


def editorial_focus(image: Image.Image, *, t: float,
                    beat: TimedBeat) -> Image.Image:
    if (not isinstance(image,Image.Image) or image.size!=SIZE
            or image.mode!="RGB"):
        raise ValueError("Rack focus requires the actual full-HD RGB frame")
    radius=focus_radius(t,beat)
    return image.filter(ImageFilter.GaussianBlur(radius)) if radius>.01 else image
