"""Optional motion-aware inbetweening of ORIGINAL Blender keyframes.

This uses local OpenCV Farneback bidirectional image flow, NOT new Blender
renders, generated video, a paid model, or geometry-accurate 30fps motion.
Unlike an unguarded optical-flow filter, production enables the algorithm
per science action only after comparison with *held-out real Cycles renders*.
"""
from __future__ import annotations

import math

from PIL import Image

VERSION = "original-blender-motion-v1-heldout-validated"


class MotionPair:
    """One pair of source-resolution RGBA plates with cached CPU optical flow.

    The two input images belong to the same authored scientific action;
    never run image flow across a scene cut. The fallback remains available
    from the caller for any shot that fails source-render validation.
    """

    def __init__(self, first: Image.Image, second: Image.Image):
        if (not isinstance(first, Image.Image) or
                not isinstance(second, Image.Image) or
                first.size != second.size or first.mode != "RGBA" or
                second.mode != "RGBA" or
                not 96 <= first.width <= 1080 or
                not 96 <= first.height <= 1380):
            raise ValueError("Unsafe or mismatched original 3D source images")
        try:
            import cv2
            import numpy as np
        except ImportError as exc:
            raise RuntimeError(
                "Motion-aware 3D rendering requires the free '[motion]' extra "
                "(numpy and opencv-python-headless)"
            ) from exc

        self._cv2 = cv2
        self._np = np
        self.first = np.asarray(first).copy()
        self.second = np.asarray(second).copy()
        h, w = self.first.shape[:2]
        flow_size = (max(80, w // 3), max(80, h // 3))

        def gray(rgba):
            small = cv2.resize(rgba, flow_size, interpolation=cv2.INTER_AREA)
            return cv2.cvtColor(small, cv2.COLOR_RGBA2GRAY)

        g0, g1 = gray(self.first), gray(self.second)
        # Consistent bidirectional flow, 1/3 native size, preserves CPU budget.
        options = (0.5, 3, 25, 4, 7, 1.5, 0)
        forward = cv2.calcOpticalFlowFarneback(g0, g1, None, *options)
        backward = cv2.calcOpticalFlowFarneback(g1, g0, None, *options)
        if not np.isfinite(forward).all() or not np.isfinite(backward).all():
            raise ValueError("Nonfinite optical flow from Blender source plates")

        grid_x, grid_y = np.meshgrid(
            np.arange(w, dtype=np.float32),
            np.arange(h, dtype=np.float32))
        small_x, small_y = np.meshgrid(
            np.arange(flow_size[0], dtype=np.float32),
            np.arange(flow_size[1], dtype=np.float32))
        # Forward-backward consistency detects collisions/occlusions and
        # suppresses the corresponding double-image flow artifacts.
        end_backward = cv2.remap(
            backward, small_x + forward[:, :, 0],
            small_y + forward[:, :, 1], cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE)
        consistency = np.sqrt(
            np.sum((forward + end_backward) ** 2, axis=2))
        displacement = np.sqrt(np.sum(forward ** 2, axis=2))
        reliability = np.clip(1.0 - consistency / 4.0, 0, 1)
        reliability *= np.clip((35.0 - displacement) / 10.0, 0, 1)
        # The mask is data-driven and soft. For unreliable pixels, use the
        # original source fade instead of distorting the foreground.
        self.mask = cv2.resize(
            reliability.astype(np.float32), (w, h),
            interpolation=cv2.INTER_LINEAR)[..., None]

        self.forward = cv2.resize(
            forward, (w, h), interpolation=cv2.INTER_LINEAR)
        self.backward = cv2.resize(
            backward, (w, h), interpolation=cv2.INTER_LINEAR)
        self.forward[:, :, 0] *= w / flow_size[0]
        self.forward[:, :, 1] *= h / flow_size[1]
        self.backward[:, :, 0] *= w / flow_size[0]
        self.backward[:, :, 1] *= h / flow_size[1]
        self.grid_x, self.grid_y = grid_x, grid_y
        self.p90_displacement_px = float(
            np.percentile(displacement, 90) * w / flow_size[0])
        self.reliable_fraction = float(np.mean(reliability > .5))

    def frame(self, fraction: float) -> Image.Image:
        if (type(fraction) not in (int, float) or
                not math.isfinite(fraction) or
                not 0 <= fraction <= 1):
            raise ValueError("Invalid interpolation fraction")
        if fraction <= 0:
            return Image.fromarray(self.first.copy(), "RGBA")
        if fraction >= 1:
            return Image.fromarray(self.second.copy(), "RGBA")

        cv2, np = self._cv2, self._np
        q = float(fraction)
        # Approximate backward sampling from BOTH keyframes to the
        # intermediate 2D motion field; not a fabricated 3D render.
        first = cv2.remap(
            self.first,
            self.grid_x - q * self.forward[:, :, 0],
            self.grid_y - q * self.forward[:, :, 1],
            cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        second = cv2.remap(
            self.second,
            self.grid_x - (1 - q) * self.backward[:, :, 0],
            self.grid_y - (1 - q) * self.backward[:, :, 1],
            cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        warped = cv2.addWeighted(first, 1 - q, second, q, 0)
        dissolve = cv2.addWeighted(self.first, 1 - q, self.second, q, 0)
        combined = np.clip(
            warped.astype(np.float32) * self.mask +
            dissolve.astype(np.float32) * (1 - self.mask), 0, 255
        ).astype(np.uint8)
        return Image.fromarray(combined, "RGBA")


def mean_absolute_error(candidate: Image.Image, reference: Image.Image) -> float:
    """Objective RGB error against a real *held-out* Cycles source frame."""
    if candidate.size != reference.size:
        raise ValueError("Cannot compare different render dimensions")
    import numpy as np
    a = np.asarray(candidate.convert("RGB"), dtype=np.int16)
    b = np.asarray(reference.convert("RGB"), dtype=np.int16)
    return float(np.mean(np.abs(a - b)))
