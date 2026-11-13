"""Strict source-verb-triggered causal contact between original 2.5D actors.

No inferred interaction from noun co-occurrence: one of two finite source-text
verb patterns MUST explicitly describe the relationship. Generated tracks use
the existing independent actors and link-triggered glints + PCM Foley. These
are stylized illustrative events, not numerical physics or verified facts.
"""
from __future__ import annotations

from copy import deepcopy
import re

from .universal_subject_composition import (
    composition_families, composition_layers, composition_tracks)

VERSION = "source-verb-anchored-dual-actor-contact-v1"
_CONTACT_AT = .5
_KINDS = frozenset(("rain-waters-plant","wave-hits-train"))
_NEGATIVE = re.compile(
    r"(?<!\w)(?:no|not|never|without|sans|pas|aucun|aucune|jamais)(?!\w)",
    re.IGNORECASE)
_PATTERNS = {
    "rain-waters-plant":(
        re.compile(r"\b(?:rain|rainfall)\b.{0,72}\b"
                   r"(?:waters?|soaks?|nourishes?|feeds?|falls?\s+on)\b"
                   r".{0,72}\b(?:tree|trees|plant|plants|leaf|leaves|"
                   r"forest|garden|seed|seeds)\b",re.IGNORECASE),
        re.compile(r"\bpluie\b.{0,72}\b"
                   r"(?:arrose|nourrit|tombe\s+sur|humidifie)\b"
                   r".{0,72}\b(?:arbre|arbres|plante|plantes|feuille|"
                   r"feuilles|forêt|jardin|graine|graines)\b",re.IGNORECASE),
    ),
    "wave-hits-train":(
        re.compile(r"\b(?:wave|waves)\b.{0,72}\b"
                   r"(?:hits?|strikes?|crashes?\s+(?:into|against)|"
                   r"slams?\s+into|collides?\s+with)\b"
                   r".{0,72}\b(?:train|trains|locomotive|railway)\b",
                   re.IGNORECASE),
        re.compile(r"\b(?:vague|vagues)\b.{0,72}\b"
                   r"(?:heurte|frappe|percute|s'écrase\s+contre)\b"
                   r".{0,72}\b(?:train|locomotive)\b",re.IGNORECASE),
    ),
}
_REQUIRED = {
    "rain-waters-plant":frozenset(("weather","botanical")),
    "wave-hits-train":frozenset(("ocean","rail")),
}


def detect_contacts(beats: list[dict],
                    families: list[list[str]]) -> list[dict | None] | None:
    """Detect explicit, affirmative source-ordered causal contact events."""
    if (type(families) is not list
            or families!=composition_families(beats)):
        raise ValueError("Cannot assign causal event to unverified source families")
    events=[]
    for beat,pair in zip(beats,families):
        source=beat["narration"]
        kind=None
        if len(pair)==2 and not _NEGATIVE.search(source):
            for candidate in sorted(_KINDS):
                if (_REQUIRED[candidate]==frozenset(pair)
                        and any(p.search(source) for p in _PATTERNS[candidate])):
                    kind=candidate
                    break
        events.append({"kind":kind,"at":_CONTACT_AT} if kind else None)
    return events if any(events) else None


def contact_layers(families: list[str]) -> list[dict]:
    """Preserve six-layer budget while moving both actors nearer the middle."""
    output=deepcopy(composition_layers(families))
    if len(families)!=2:
        return output
    for layer in output:
        offset=(.09 if layer["z"] in (45,65) else
                -.09 if layer["z"] in (50,70) else 0.)
        if not offset:
            continue
        for shape in layer["shapes"]:
            if "box" in shape:
                shape["box"][0]=round(shape["box"][0]+offset,7)
                shape["box"][2]=round(shape["box"][2]+offset,7)
            else:
                for point in shape["points"]:
                    point[0]=round(point[0]+offset,7)
    return output


def _soft_step(t: float) -> float:
    q=max(0.,min(1.,t))
    return q*q*(3.-2.*q)


def _growth(index: int, at: float, events: list[dict | None]) -> float:
    """A watering event persists as canopy growth across later narration."""
    before=sum(e is not None and e["kind"]=="rain-waters-plant"
               for e in events[:index])
    current=(events[index] is not None
             and events[index]["kind"]=="rain-waters-plant")
    return round(min(.14,.07*(before+(
        _soft_step((at-.5)*2.) if current else 0.))),7)


def contact_tracks_and_links(
    families: list[str], index: int, total: int,
    events: list[dict | None]
) -> tuple[list[dict],list[dict]]:
    """Derive bounded contact motion and a true event-locked Foley link.

    All discontinuous-looking reaction impulses return to baseline at a shot
    boundary; growth remains as a verified persistent world-state change.
    """
    if (type(index) is not int or type(total) is not int
            or not 2<=total<=12 or not 0<=index<total
            or type(events) is not list or len(events)!=total
            or any(e is not None and (type(e) is not dict or
                    set(e)!={"kind","at"} or e["kind"] not in _KINDS
                    or e["at"]!=_CONTACT_AT) for e in events)):
        raise ValueError("Invalid deterministic contact action timeline")
    tracks=composition_tracks(families,index,total)
    lookup={t["z"]:t for t in tracks}
    action=events[index]
    if "botanical" in families:
        botanical_shift=(5 if len(families)==2
                         and families.index("botanical")==1 else 0)
        canopy=lookup[65+botanical_shift]
        for key in canopy["keys"]:
            key["scale"]=round(key["scale"]+_growth(index,key["at"],events),7)
    if action is None:
        return tracks,[]
    kind=action["kind"]
    if len(families)!=2 or _REQUIRED[kind]!=frozenset(families):
        raise ValueError("Causal event needs both correct source objects")
    at=_CONTACT_AT
    if kind=="rain-waters-plant":
        src="weather";dest="botanical";source_base=65;target_base=65
        shift_y=-.33
    else:
        src="ocean";dest="rail";source_base=45;target_base=45
        shift_y=.04
    def depth(family,base):
        return base+(5 if families.index(family)==1 else 0)
    from_z=depth(src,source_base)
    to_z=depth(dest,target_base)
    direction=1. if families.index(src)==0 else -1.
    pulse={0.:0.,.25:.52,.5:1.,.75:.36,1.:0.}
    for key in lookup[from_z]["keys"]:
        force=pulse[key["at"]]
        key["x"]=round(key["x"]+direction*.27*force,7)
        key["y"]=round(key["y"]+shift_y*force,7)
    if kind=="wave-hits-train":
        # A brief elastic reaction rather than a false state transition.
        reaction={0.:0.,.25:0.,.5:0.,.75:1.,1.:0.}
        for key in lookup[to_z]["keys"]:
            magnitude=reaction[key["at"]]
            key["y"]=round(key["y"]+.024*magnitude,7)
            key["angle"]=round(key["angle"]+4.*magnitude,7)
    return tracks,[{"fromZ":from_z,"toZ":to_z,"at":at}]


def apply_contacts(beats: list[dict], families: list[list[str]],
                   events: list[dict | None]) -> None:
    """Create authenticated source-aware storyboard with real audio links."""
    if events!=detect_contacts(beats,families):
        raise ValueError("Causal object interactions do not match source verbs")
    total=len(beats)
    for i,(beat,pair) in enumerate(zip(beats,families)):
        if any(key in beat for key in (
                "visualVectors","visualLayers","actorTracks","actorLinks")):
            raise ValueError("Cannot overwrite authored interaction scenes")
        if not pair:
            continue
        beat["visualVectors"]=contact_layers(pair)
        beat["actorTracks"],links=contact_tracks_and_links(
            pair,i,total,events)
        if links:
            beat["actorLinks"]=links
