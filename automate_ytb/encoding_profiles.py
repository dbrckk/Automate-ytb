"""Trusted export encoding profiles for original scene clips and final MP4.

The 'high' preset improves the codec and frame rate options, not the source
illustration resolution or intrinsic animation quality. CPU-only and free.
"""
from __future__ import annotations

PROFILES = {
    "preview": {"preset": "veryfast", "crf": 21, "stillCrf": 20,
                "audioKbps": 192, "musicOnlyKbps": 160},
    "high": {"preset": "medium", "crf": 18, "stillCrf": 18,
             "audioKbps": 256, "musicOnlyKbps": 256},
}
VERSION = "video-encoding-profiles-v1"


def settings(profile: str) -> dict:
    if not isinstance(profile, str) or profile not in PROFILES:
        raise ValueError("Export profile must be preview or high")
    return dict(PROFILES[profile])


def video_args(profile: str, *, still: bool = False) -> list[str]:
    profile_settings = settings(profile)
    return ["-c:v", "libx264", "-preset", profile_settings["preset"],
            "-crf", str(profile_settings["stillCrf"] if still
                        else profile_settings["crf"]),
            "-pix_fmt", "yuv420p"]


def audio_bitrate(profile: str, *, music_only: bool = False) -> str:
    profile_settings = settings(profile)
    return str(profile_settings["musicOnlyKbps"] if music_only
               else profile_settings["audioKbps"]) + "k"
