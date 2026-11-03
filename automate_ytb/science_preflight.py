"""Fast authored-scene contract before downloading neural speech or rendering.

The supported domain renderers require a semantic beat per scene. Check that
contract on the *same scene plan* the episode renderer will consume. This
prevents a costly, seemingly successful video with repeated generic pictures.
Never auto-rewrite scientific narration or assert its factual correctness.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .science_aurora import supports_topic as aurora_topic, classify as aurora_beat
from .science_volcano import supports_topic as volcano_topic, classify as volcano_beat
from .science_lightning import supports_topic as lightning_topic, classify as lightning_beat
from .science_rainbow import supports_topic as rainbow_topic, classify as rainbow_beat

VERSION="authored-science-scene-preflight-v1"

DOMAINS=(
    ("volcano",volcano_topic,volcano_beat),
    ("aurora",aurora_topic,aurora_beat),
    ("lightning",lightning_topic,lightning_beat),
    ("rainbow",rainbow_topic,rainbow_beat),
)


def inspect(plan:dict, *, style:str="science", resolution:str="shorts") -> dict:
    if not isinstance(plan,dict) or not isinstance(plan.get("topic"),str):
        raise ValueError("Missing original topic in scene plan")
    scenes=plan.get("scenes")
    if (not isinstance(scenes,list) or not 1<=len(scenes)<=150
            or plan.get("sceneCount")!=len(scenes)):
        raise ValueError("Invalid planned scene count")
    ids=set()
    for item in scenes:
        if not isinstance(item,dict) or not isinstance(item.get("narration"),str):
            raise ValueError("Missing authored narration in planned scene")
        if (not isinstance(item.get("id"),str) or item["id"] in ids
                or not item["narration"].strip()):
            raise ValueError("Invalid or duplicate scene identifier or narration")
        ids.add(item["id"])
    if style!="science" or resolution!="shorts":
        return {"schemaVersion":1,"version":VERSION,"status":"not-applicable",
                "reason":"Specialized science contracts apply only to science shorts",
                "publicationApproved":False}
    topic=plan["topic"]
    matching=[(name,classify) for name,supports,classify in DOMAINS
              if supports(topic)]
    if len(matching)>1:
        raise ValueError("Ambiguous science domain: "+", ".join(x[0] for x in matching))
    if not matching:
        # Earth/ocean has its own more flexible legacy storyboarding; leave
        # unsupported-topic rejection to PortraitScienceScene itself.
        return {"schemaVersion":1,"version":VERSION,"status":"delegated",
                "reason":"Domain is not one of the four strict beat classifiers",
                "publicationApproved":False}
    domain,classify=matching[0]
    classified=[{"sceneId":s["id"],"beat":classify(topic,s["narration"])}
                for s in scenes]
    missing=[x["sceneId"] for x in classified if x["beat"] is None]
    repeats=[classified[i]["sceneId"] for i in range(1,len(classified))
             if classified[i]["beat"]==classified[i-1]["beat"]
             and classified[i]["beat"] is not None]
    # Duplicate beats can be a deliberate second shot; warn but don't block.
    return {"schemaVersion":1,"version":VERSION,
            "status":"failed" if missing else "passed",
            "domain":domain,"sceneCount":len(scenes),
            "classifiedScenes":classified,
            "errors":[f"Scene {x} lacks a supported {domain} action"
                      for x in missing],
            "warnings":[f"Consecutive scenes repeat the same action: {x}"
                        for x in repeats],
            "humanEditorialReviewRequired":True,
            "publicationApproved":False}


def main(argv=None)->int:
    p=argparse.ArgumentParser(description="Validate scene-to-animation semantics before expensive TTS")
    p.add_argument("--plan",required=True,type=Path)
    p.add_argument("--style",required=True)
    p.add_argument("--resolution",required=True)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args(argv)
    data=json.loads(a.plan.read_text(encoding="utf-8"))
    result=inspect(data,style=a.style,resolution=a.resolution)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"domain":result.get("domain"),
                      "errors":result.get("errors",[]),
                      "warnings":result.get("warnings",[])},ensure_ascii=False))
    return 2 if result["status"]=="failed" else 0

if __name__=="__main__":
    raise SystemExit(main())
