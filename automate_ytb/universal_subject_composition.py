"""Deterministic original two-subject compositions within one narrated beat.

Bounded to the existing six-layer and six-actor budget. Only two independently
recognized concrete source families may share a shot. If three distinct
families are present, fall back to a single source-grounded subject rather
than pretending to draw all three. All artwork is generated from this
repository's original geometry; no external images or inferred facts.
"""
from __future__ import annotations

from copy import deepcopy
import re

from .universal_subject_illustrations import (
    _ORDER, _PALETTE, _PATTERN, _box, _ell, _layer, _line, _multi,
    select_subject, subject_layers, subject_tracks)

VERSION = "source-grounded-dual-subject-six-layer-compositor-v1"
_NEGATIONS = frozenset(("no", "not", "without", "sans", "aucun", "aucune"))
# The established stage supports at most six visual vector layers.
# Reserve two unanimated layers, leaving two articulated parts per subject.
_X_SCALE = .54
_Y_SCALE = .88
_LEFT = .015
_RIGHT = .46
_VERTICAL = .06
_ACTOR_DEPTHS = (45, 65)
_SECONDARY_Z_OFFSET = 5


def _explicit_families(text: str) -> list[str]:
    """Rank the explicit, non-negated nouns from the original narration.

    Reuse exactly the same finite word patterns and lexical negation policy
    as the v17/v18 template selector, independently of the title.
    """
    if type(text) is not str:
        raise ValueError("Original beat narration must be a string")
    corpus=text.casefold()
    candidates=[]
    for index,family in enumerate(_ORDER):
        found=[]
        for expression in _PATTERN[family]:
            for match in expression.finditer(corpus):
                words=re.findall(r"[^\\W_]+",corpus[max(0,match.start()-30):match.start()],
                                 re.UNICODE)
                if words[-1:] and words[-1] in _NEGATIONS:
                    continue
                found.append(match.group(0).casefold())
        if found:
            score=len(set(found))+.1*min(2,len(found))
            candidates.append((-score,index,family))
    return [family for _,_,family in sorted(candidates)]


def composition_families(beats: list[dict]) -> list[list[str]] | None:
    """Return per-beat 0..2 families only if at least one beat truly needs two."""
    if (type(beats) is not list or not 2 <= len(beats) <= 12
            or any(type(b) is not dict or type(b.get("narration")) is not str
                   for b in beats)):
        raise ValueError("Invalid original multi-object storyboard")
    sequence=[]
    for beat in beats:
        matched=_explicit_families(beat["narration"])
        if len(matched)==2:
            sequence.append(matched)
        elif len(matched)>2:
            # A two-object drawing would omit a third explicit category.
            # Use the existing honest predominant-subject fallback.
            selected=select_subject("",beat["narration"])
            sequence.append([selected] if selected else [])
        else:
            sequence.append(matched)
    return sequence if any(len(item)==2 for item in sequence) else None


def _position_shape(shape: dict, left: float) -> dict:
    """Move a vector primitive into one of two side-by-side stage zones."""
    item=deepcopy(shape)
    def coord_x(x: float) -> float:
        return round(left+_X_SCALE*x,7)
    def coord_y(y: float) -> float:
        return round(_VERTICAL+_Y_SCALE*y,7)
    if "box" in item:
        x0,y0,x1,y1=item["box"]
        item["box"]=[coord_x(x0),coord_y(y0),coord_x(x1),coord_y(y1)]
        if "radius" in item:
            item["radius"]=round(item["radius"]*.76,7)
    else:
        item["points"]=[[coord_x(x),coord_y(y)]
                        for x,y in item["points"]]
    item["strokeWidth"]=round(item["strokeWidth"]*.76,7)
    return item


def composition_layers(families: list[str]) -> list[dict]:
    """Six cached vector layers: backdrop, stage, two actors per subject."""
    if (type(families) is not list or not 1<=len(families)<=2
            or len(set(families))!=len(families)
            or any(type(x) is not str or x not in _PALETTE for x in families)):
        raise ValueError("Composition supports one or two known distinct subjects")
    if len(families)==1:
        return subject_layers(families[0])
    first,second=families
    a,b=_PALETTE[first],_PALETTE[second]
    layers=[
        _layer("dual",5,"atmosphere",[
            _box(0.,0.,1.,1.,_multi([a[0],a[1],b[1],b[0]],"diagonal","stage"),.0),
            _ell(.04,.06,.49,.56,_multi([a[2],a[1]],"radial"),opacity=.29),
            _ell(.53,.10,.96,.59,_multi([b[2],b[1]],"radial"),opacity=.29),
        ],(.13,.08)),
        _layer("dual",25,"stage",[
            _line([[.49,.11],[.49,.90]],"#8296B0",.002,opacity=.25),
            _ell(.075,.75,.485,.94,a[2],opacity=.12),
            _ell(.515,.75,.925,.94,b[2],opacity=.12),
        ],(.25,.12)),
    ]
    for family,left,zshift in ((first,_LEFT,0),
                               (second,_RIGHT,_SECONDARY_Z_OFFSET)):
        originals=subject_layers(family)
        for z in _ACTOR_DEPTHS:
            original=next(layer for layer in originals if layer["z"]==z)
            adapted=deepcopy(original)
            adapted["id"]="dual-"+adapted["id"]
            adapted["z"]=z+zshift
            adapted["shapes"]=[_position_shape(shape,left)
                               for shape in original["shapes"]]
            layers.append(adapted)
    return layers


def composition_tracks(families: list[str], index: int,
                       total: int) -> list[dict]:
    """Independently animated original subjects on one continuous world clock."""
    # The illustration validator also validates ordering and family coverage.
    composition_layers(families)
    if (type(index) is not int or type(total) is not int
            or not 2<=total<=12 or not 0<=index<total):
        raise ValueError("Invalid multi-object storyboard clock")
    if len(families)==1:
        return subject_tracks(index,total,family=families[0])
    output=[]
    for family,zshift in ((families[0],0),
                          (families[1],_SECONDARY_Z_OFFSET)):
        original=subject_tracks(index,total,family=family)
        for track in original:
            if track["z"] not in _ACTOR_DEPTHS:
                continue
            item=deepcopy(track)
            item["z"]+=zshift
            for key in item["keys"]:
                key["x"]=round(key["x"]*_X_SCALE,7)
                key["y"]=round(key["y"]*_Y_SCALE,7)
            output.append(item)
    return output


def apply_compositions(beats: list[dict],
                       sequence: list[list[str]]) -> None:
    """Create original source-matched artwork without overriding editorial art."""
    if (type(sequence) is not list
            or sequence!=composition_families(beats)):
        raise ValueError("Two-subject story provenance does not match its source")
    for i,(beat,families) in enumerate(zip(beats,sequence)):
        if any(key in beat for key in ("visualVectors","visualLayers","actorTracks")):
            raise ValueError("Cannot overwrite authored artwork")
        if not families:
            continue
        beat["visualVectors"]=composition_layers(families)
        beat["actorTracks"]=composition_tracks(families,i,len(beats))
