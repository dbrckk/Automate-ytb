"""Original French flower pilot; ten layers, five independently hinged petals.

This fictional illustration demonstrates authored motion, not botanical growth.
The older vector flower fixture remains available as an unchanged comparison.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path

from build_original_vector_story import (
    art, beat as legacy_beat, ellipse, k, landscape, left_leaf, line, path, right_leaf, stem)


def layers():
    trunk = stem()
    trunk.update(z=20, parallaxX=0, parallaxY=0)
    left, right = left_leaf(), right_leaf()
    left["z"], right["z"] = 30, 35
    garden = landscape()
    garden.update(parallaxX=0, parallaxY=0)
    garden["shapes"][1]["box"] = [.73,.07,.94,.28]
    garden["shapes"][2]["box"] = [.76,.09,.92,.26]
    garden["shapes"].append(ellipse(.39,.854,.61,.91,["#102F38","#19483E"]))
    result = [garden, trunk, left, right]
    palettes = [
        ["#F5A7AC", "#B04F7D"], ["#FFD5AA", "#D37A94"],
        ["#FFE4B8", "#DD91A2"], ["#FFD0AF", "#C97191"],
        ["#F3A6B7", "#A94D7B"],
    ]
    for i, fill in enumerate(palettes):
        result.append(art(f"hinged-petal-{i+1}", 45+i*5, 1, .4, [
            path([[.5,.38],[.405,.31],[.385,.13],[.5,.10],
                  [.615,.13],[.595,.31],[.5,.38]],
                 fill, "#FFE2BF", .003),
            line([[.5,.355],[.493,.27],[.502,.17]], "#FFE2C6", .0025),
            line([[.49,.29],[.452,.22]], "#F3B7B8", .002),
            line([[.505,.265],[.546,.19]], "#FFE3BC", .002),
        ], "foliage"))
    result.append(art("flower-heart", 80, 1, .4, [
        ellipse(.449,.29,.551,.38,["#FFF0BF","#DDA552"],"#FFE6AC",.003),
        ellipse(.468,.306,.532,.365,["#F9D891","#C98A56"]),
        ellipse(.477,.312,.488,.323,"#FFF5D9"),
        ellipse(.508,.342,.52,.354,"#FFF5D9"),
        ellipse(.514,.314,.525,.325,"#FFF5D9"),
    ]))
    return result


def _attached(z, attach, pivot, keys):
    return {"z":z, "parentZ":20, "attach":attach, "pivot":pivot, "keys":keys}


def story():
    visuals = layers()
    titles = ["Une fleur encore refermée", "Cinq pétales, cinq mouvements", "La fleur trouve son équilibre"]
    narration = [
        "Dans ce jardin imaginaire, une fleur se prépare à éclore. Ses feuilles frémissent, mais sa tige reste ancrée dans le sol.",
        "Regardez ses cinq pétales. Ils s'écartent l'un après l'autre, chacun autour de sa propre attache, et entourent le cœur doré de la fleur.",
        "Le mouvement ralentit doucement. Les pétales se stabilisent, les feuilles se reposent. La même fleur reste devant nous, maintenant ouverte.",
    ]
    beats = []
    for stage in range(3):
        root_angles = ((-1, .3, .8), (.8, -.5, .4), (.4, -.15, 0))[stage]
        tracks = [{"z":20, "pivot":[.5,1.], "keys":[
            k(0, angle=root_angles[0]), k(.5, angle=root_angles[1]), k(1, angle=root_angles[2])]}]
        for z, attach, pivot, sign in (
            (30,[.33,.64],[.93,.57],1), (35,[.7,.43],[.06,.50],-1)):
            angles = ((-12, -3, 0), (0, 14, 8), (8,-2,0))[stage]
            tracks.append(_attached(z,attach,pivot,[
                k(0,angle=sign*angles[0]),k(.5,angle=sign*angles[1]),k(1,angle=sign*angles[2])]))
        cues = []
        for i, final_angle in enumerate((-62,-31,0,31,62)):
            z=45+i*5
            closed=(i-2)*4
            if stage == 0:
                keys=[k(0,scale=.55,angle=closed),k(.6,scale=.58,angle=closed-1),
                      k(1,scale=.60,angle=closed)]
            elif stage == 1:
                delay=.13+i*.085
                keys=[k(0,scale=.60,angle=closed),k(delay,scale=.60,angle=closed),
                      k(delay+.32,scale=1.02,angle=final_angle),
                      k(1,scale=1.,angle=final_angle)]
                cues.append({"z":z,"keyIndex":1,"family":"growth","gainDb":-30})
            else:
                keys=[k(0,angle=final_angle),k(.3,scale=.99,angle=final_angle+1),
                      k(.65,scale=1.002,angle=final_angle-.3),k(1,angle=final_angle)]
            tracks.append(_attached(z,[.5,.06],[.5,.99],keys))
        heart_scales=((.95,.97,1),(1,1.025,1.01),(1.01,1.005,1))[stage]
        tracks.append(_attached(80,[.5,.06],[.5,.5],[
            k(0,scale=heart_scales[0]),k(.5,scale=heart_scales[1]),k(1,scale=heart_scales[2])]))
        if stage == 0:
            cues=[{"z":30,"keyIndex":0,"family":"whoosh","gainDb":-33}]
        elif stage == 2:
            cues=[{"z":80,"keyIndex":0,"family":"reveal","gainDb":-32}]
        beats.append({"kind":"concept","title":titles[stage],"narration":narration[stage],
            "nodes":["Fleur","Pétales","Jardin"],"visualVectors":deepcopy(visuals),
            "actorTracks":tracks,"actorLinks":[],"actorCues":cues})
    return {"schemaVersion":1,"topic":"L'éveil d'une fleur imaginaire","language":"fr","beats":beats}


def baseline_story():
    """Same narration, old rigid blossom: comparison fixture, not a release."""
    baseline=story()
    old=[legacy_beat(0),legacy_beat(1)]
    third=deepcopy(old[-1])
    for track in third["actorTracks"]:
        last=deepcopy(track["keys"][-1])
        track["keys"]=[dict(last,at=0),dict(last,at=1,angle=last["angle"]+.1)]
    old.append(third)
    for before,after in zip(old,baseline["beats"]):
        after.update(visualVectors=before["visualVectors"],actorTracks=before["actorTracks"],
                     actorLinks=before["actorLinks"],actorCues=[])
    return baseline


def build(out: Path, *, baseline=False):
    out.mkdir(parents=True, exist_ok=True)
    target=out/("baseline-flower.story.json" if baseline else "articulated-flower.story.json")
    # Repeated immutable art remains within the existing 120 kB story budget.
    target.write_text(json.dumps(baseline_story() if baseline else story(),
                                ensure_ascii=False,separators=(",", ":"))+"\n",encoding="utf8")
    return target


if __name__ == "__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--out-dir",type=Path,required=True)
    cli.add_argument("--baseline",action="store_true")
    args=cli.parse_args()
    print(build(args.out_dir,baseline=args.baseline))
