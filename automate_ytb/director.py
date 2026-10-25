"""Deterministic, conservative scene direction inferred from *authored* narration.

This is a visual-effects cue extractor, not factual research and not an LLM.
Explicit weather words affect the scene and persist until another cue; action
and mood affect only that beat. A visual cue never modifies narration itself.
"""
from __future__ import annotations

import re
import unicodedata

WEATHERS = frozenset({"day", "night", "cloudy", "rain", "wind", "storm"})
ACTIONS = frozenset({"idle", "fly", "walk", "run", "jump", "talk", "surprise", "rest"})
EMOTIONS = frozenset({"neutral", "curious", "happy", "worried", "surprised"})
SHOTS = frozenset({"wide", "medium", "closeup", "macro", "low", "shoulder"})

WEATHER_PATTERNS = (
    ("storm", r"\b(orage|tonnerre|eclair|tempete|storm|thunder|lightning)\w*\b"),
    ("rain", r"\b(pluie|pleut|pluvieux|averse|rain|raining|raindrop)\w*\b"),
    ("night", r"\b(nuit|nocturne|lune|etoile|minuit|night|moon|stars|midnight)\w*\b"),
    ("day", r"\b(journee|matin|soleil|ensoleill|aube|aurore|sunny|sunrise|daylight|morning)\w*\b"),
    ("wind", r"\b(vent|venteux|rafale|bourrasque|wind|gust|breeze)\w*\b"),
    ("cloudy", r"\b(nuage|couvert|brume|brouillard|cloud|fog|mist)\w*\b"),
)
ACTION_PATTERNS = (
    ("jump", r"\b(saute|sauter|bondit|bondir|saut|jump|jumps|jumping|hop|hops|leap)\w*\b"),
    ("run", r"\b(court|courir|cours|sprinte|course|run|running|runs|sprint|dash)\w*\b"),
    ("fly", r"\b(vole|voler|envole|plane|survole|fly|flying|flies|soar)\w*\b"),
    ("surprise", r"\b(soudain|surpris|etonne|incroyable|suddenly|surprise|astonish)\w*\b"),
    ("walk", r"\b(marche|traverse|explore|avance|promene|walk|walking|explore|cross)\w*\b"),
    ("talk", r"\b(parle|raconte|explique|dit|chuchote|talk|tell|explain|whisper)\w*\b"),
    ("rest", r"\b(repose|dort|dormir|calme|assis|rest|sleep|quiet|sit)\w*\b"),
)
EMOTION_PATTERNS = (
    ("surprised", r"\b(soudain|surpris|etonne|surprise|astonish)\w*\b"),
    ("happy", r"\b(heureux|joie|souri|joyeux|ravie|happy|smile|joy|delighted)\w*\b"),
    ("worried", r"\b(inquiet|peur|triste|terrifi|danger|worried|scared|fear|sad)\w*\b"),
    ("curious", r"\b(decouvre|cherche|question|mystere|observe|curieux|discover|wonder|curious|observe)\w*\b"),
)
SHOT_TRANSLATION = {
    "wide establishing": "wide",
    "medium": "medium",
    "close-up": "closeup",
    "macro": "macro",
    "low-angle": "low",
    "over-the-shoulder": "shoulder",
}


def _normalized(text: str) -> str:
    if not isinstance(text, str):
        raise ValueError("Narration must be text")
    stripped = unicodedata.normalize("NFKD", text.casefold())
    return "".join(ch for ch in stripped if not unicodedata.combining(ch))


def _choose(text: str, patterns, fallback: str) -> str:
    matches = [(re.search(pattern, text).start(), name)
               for name, pattern in patterns if re.search(pattern, text)]
    return min(matches)[1] if matches else fallback


def _emotion(text: str) -> str:
    # Prefer an explicit facial expression such as smiling or surprise over
    # the weaker "curious" category, regardless of the verb order.
    for label, pattern in EMOTION_PATTERNS:
        if re.search(pattern, text):
            return label
    return "neutral"


def direction_for(narration: str, *, prior_weather: str = "day",
                  camera: str = "medium") -> dict[str, str]:
    """Return a validated stable visual-only direction.

    Weather persists only if narration has no explicit weather cue.
    First matching mention wins when there are multiple weather events in the
    *same* beat; more precise temporal parsing needs explicit authored cues.
    """
    if prior_weather not in WEATHERS:
        raise ValueError("Invalid prior weather")
    if camera not in SHOT_TRANSLATION and camera not in SHOTS:
        raise ValueError("Unsupported camera value")
    clean = _normalized(narration)
    return {
        "weather": _choose(clean, WEATHER_PATTERNS, prior_weather),
        "action": _choose(clean, ACTION_PATTERNS, "idle"),
        "emotion": _emotion(clean),
        "shot": SHOT_TRANSLATION.get(camera, camera),
    }


def direct_scenes(scenes: list[dict]) -> list[dict]:
    """Direction metadata is generated without touching text or timings."""
    previous = "day"
    result = []
    for scene in scenes:
        if not isinstance(scene, dict):
            raise ValueError("Scenes must be objects")
        cue = direction_for(scene["narration"], prior_weather=previous,
                            camera=scene.get("camera", "medium"))
        previous = cue["weather"]
        result.append(cue)
    return result


def validate_direction(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"weather", "action", "emotion", "shot"}:
        raise ValueError("Invalid direction keys")
    if (value["weather"] not in WEATHERS or value["action"] not in ACTIONS
        or value["emotion"] not in EMOTIONS or value["shot"] not in SHOTS):
        raise ValueError("Unsupported director cue")
    return dict(value)
