"""Original, repeatable botanical 2.5D actor-story example.

Illustrates the universal vector grammar. A garden seed, soil, roots and
leaves are authored as independent curved, shaded layers. No photos,
third-party assets, SVG parsing, credentials, or paid generation.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

VERSION="original-botanical-vector-reference-v1"


def shape(kind,geometry,fill=None,stroke=None,stroke_width=0,
          glow=0.,opacity=1.):
    return {"type":kind,"geometry":geometry,"fill":fill,
            "stroke":stroke,"strokeWidth":stroke_width,
            "glow":glow,"opacity":opacity}


def gradient(top,bottom):
    return {"top":top,"bottom":bottom}


def poly(points,fill,stroke=None,sw=0,glow=0,opacity=1.):
    return shape("polygon",points,fill,stroke,sw,glow,opacity)


def ellipse(box,fill,stroke=None,sw=0,glow=0,opacity=1.):
    return shape("ellipse",box,fill,stroke,sw,glow,opacity)


def move(x,y):
    return {"op":"M","p":[x,y]}


def line(x,y):
    return {"op":"L","p":[x,y]}


def curve(ax,ay,bx,by,x,y):
    return {"op":"C","c1":[ax,ay],"c2":[bx,by],"p":[x,y]}


def close():
    return {"op":"Z"}


def path(commands,fill,stroke=None,sw=0,glow=0,opacity=1.):
    return shape("path",commands,fill,stroke,sw,glow,opacity)


def vector(name,z,shapes,px,py):
    return {"name":name,"z":z,"parallaxX":px,"parallaxY":py,
            "material":"none","shapes":shapes}


def authored_vector_world():
    rng=random.Random(21837)
    sky=[
        poly([[0,0],[1,0],[1,1],[0,1]],
             gradient("#08162D","#246A7A")),
        ellipse([.11,.02,.96,.86],"#0C426A",glow=.038,opacity=.44),
        ellipse([.30,.07,.73,.46],"#93D7C3",glow=.054,opacity=.12),
        ellipse([.45,.19,.58,.32],"#EDFCDE",glow=.054,opacity=.45),
        path([move(-.1,.72),curve(.09,.58,.28,.64,.49,.73),
              curve(.71,.61,.90,.63,1.1,.70),
              line(1.1,1.1),line(-.1,1.1),close()],
             gradient("#26586A","#0B273E"),glow=.008),
    ]
    # Multiple freely reproducible distant plant silhouettes and air grains.
    for x in (.03,.14,.85,.95):
        sky.append(path([
            move(x-.036,.77),curve(x-.028,.55,x+.028,.54,x+.042,.76),
            line(x+.055,.88),line(x-.05,.88),close()],
            gradient("#315969","#112B40"),opacity=.58))
    for _ in range(18):
        x=rng.uniform(.01,.98)
        y=rng.uniform(.02,.62)
        r=rng.uniform(.002,.006)
        sky.append(ellipse([x-r,y-r,x+r,y+r],
                           "#D4EEE5",opacity=rng.uniform(.15,.53)))
    earth=[
        path([move(-.10,.70),curve(.11,.635,.31,.69,.50,.695),
              curve(.70,.66,.85,.64,1.1,.70),
              line(1.10,1.1),line(-.10,1.1),close()],
             gradient("#5E4C3B","#172A31"),stroke="#AF9071",
             sw=.005,glow=.005),
        path([move(-.05,.77),curve(.35,.71,.58,.80,1.05,.74),
              line(1.05,.82),curve(.73,.86,.35,.80,-.05,.87),
              close()],gradient("#443C34","#342D2C"),opacity=.75),
        path([move(-.05,.92),curve(.25,.87,.55,.98,1.05,.90),
              line(1.05,.98),curve(.67,1.06,.29,.98,-.05,1.05),
              close()],gradient("#594436","#2B2728"),opacity=.85),
    ]
    for i in range(30):
        x=rng.uniform(.02,.96)
        y=rng.uniform(.73,.99)
        r=rng.uniform(.004,.014)
        palette=("#D3A477","#65554B","#283D3D","#A07659")
        earth.append(ellipse([x-r,y-r*.65,x+r,y+r*.65],
                             palette[i%4],opacity=rng.uniform(.26,.68)))
    seed=[
        ellipse([.392,.500,.628,.730], "#1A141D",glow=.025,opacity=.45),
        path([move(.42,.60),curve(.35,.43,.56,.37,.65,.51),
              curve(.73,.66,.57,.73,.46,.68),
              curve(.425,.65,.43,.62,.42,.60),close()],
             gradient("#E7AD68","#85432F"),stroke="#FFDDA0",sw=.009,
             glow=.016),
        path([move(.462,.53),curve(.49,.47,.60,.46,.625,.52),
              curve(.58,.49,.52,.50,.462,.53),close()],
             gradient("#FDE7AE","#D79456"),opacity=.79),
        path([move(.487,.59),curve(.525,.64,.54,.665,.598,.666)],
             None,stroke="#5C2D25",sw=.006,opacity=.88),
        ellipse([.479,.548,.525,.58],"#FFF5CF",glow=.009,opacity=.74),
    ]
    root=[
        path([move(.519,.618),curve(.493,.68,.476,.745,.505,.84),
              curve(.523,.90,.488,.936,.457,.967),
              curve(.522,.947,.555,.9,.548,.819),
              curve(.54,.745,.561,.697,.545,.622),close()],
             gradient("#E4CFAB","#8B9E8E"),
             stroke="#F2DDB3",sw=.004,glow=.012),
        path([move(.523,.77),curve(.593,.79,.622,.825,.643,.858)],
             None,stroke="#BFC2A4",sw=.007),
        path([move(.51,.87),curve(.47,.879,.429,.911,.408,.949)],
             None,stroke="#9EA590",sw=.005),
        path([move(.524,.827),curve(.566,.86,.570,.896,.58,.919)],
             None,stroke="#E4CE9E",sw=.004,opacity=.74),
    ]
    plant=[
        path([move(.495,.640),curve(.481,.52,.506,.41,.516,.295),
              curve(.529,.24,.545,.225,.558,.206),
              curve(.553,.351,.529,.471,.55,.641),close()],
             gradient("#B5E68B","#38744F"),
             stroke="#D1F0A3",sw=.005,glow=.012),
        path([move(.533,.32),curve(.465,.212,.337,.159,.294,.253),
              curve(.28,.347,.414,.384,.533,.32),close()],
             gradient("#C9F69A","#277956"),
             stroke="#E7F9AE",sw=.006,glow=.016),
        path([move(.543,.296),curve(.597,.163,.762,.155,.808,.253),
              curve(.832,.342,.667,.371,.543,.296),close()],
             gradient("#D0F9A4","#2E8461"),
             stroke="#E4FFBE",sw=.006,glow=.017),
        path([move(.523,.323),curve(.444,.31,.377,.294,.308,.263)],
             None,stroke="#F1FFB9",sw=.004,opacity=.75),
        path([move(.551,.300),curve(.64,.296,.717,.272,.787,.250)],
             None,stroke="#F2FFBB",sw=.004,opacity=.78),
        path([move(.509,.47),curve(.46,.418,.407,.436,.38,.472),
              curve(.435,.483,.48,.511,.509,.47),close()],
             gradient("#92CE73","#287250"),glow=.006),
        path([move(.54,.416),curve(.61,.367,.675,.371,.691,.427),
              curve(.621,.445,.575,.468,.54,.416),close()],
             gradient("#A9E88B","#2D8A62"),glow=.006),
    ]
    droplets=[
        ellipse([.23,.35,.282,.417],
                gradient("#D4F9FC","#3698BA"),glow=.018,opacity=.82),
        ellipse([.74,.43,.794,.497],
                gradient("#E9FCF7","#459BB6"),glow=.018,opacity=.79),
        ellipse([.33,.245,.365,.29],
                gradient("#E6FFFF","#60B6C1"),glow=.015,opacity=.74),
        ellipse([.625,.36,.66,.406],
                gradient("#F0FFFA","#6ABFC8"),glow=.015,opacity=.75),
        ellipse([.855,.31,.90,.372],
                gradient("#E2FFF5","#4B9CB5"),glow=.014,opacity=.64),
        ellipse([.125,.425,.169,.482],
                gradient("#D8F8FA","#3C9DAD"),glow=.012,opacity=.79),
    ]
    return [
        vector("atmospheric-illustration",5,sky,.15,.06),
        vector("textured-earth",10,earth,.25,.14),
        vector("original-root",55,root,1.03,.65),
        vector("detailed-seed",65,seed,1.18,.62),
        vector("growing-leaf-rig",78,plant,1.35,.78),
        vector("water-droplets",92,droplets,1.6,.92),
    ]


def key(t,x,y,scale,angle,opacity=1.):
    return {"at":t,"x":x,"y":y,"scale":scale,
            "angle":angle,"opacity":opacity}


def build_story():
    vectors=authored_vector_world()
    first={
        "kind":"concept","title":"A seed wakes beneath the soil",
        "narration":"Water enters a dormant seed. A pale root emerges as its stored energy begins to support new growth.",
        "nodes":["Water","Root","Seed"],
        "visualVectors":vectors,
        "actorTracks":[
            {"z":55,"keys":[key(0,.015,.12,.45,5,.05),
                             key(.50,.008,.04,.62,1,.48),
                             key(1,.0,0,.87,0,.94)]},
            {"z":65,"keys":[key(0,0,.01,.94,-9,1),
                             key(.5,.0,.003,1.07,-3,1),
                             key(1,0,0,1.01,2,1)]},
            {"z":78,"keys":[key(0,.0,.17,.45,-8,.0),
                             key(.52,-.007,.08,.48,1,.22),
                             key(1,0,.0,.65,3,.56)]},
            {"z":92,"keys":[key(0,-.02,-.09,.85,0,.89),
                             key(.52,.00,.0,.72,1,.6),
                             key(1,.02,.045,.58,4,.22)]},
        ],
        "actorLinks":[{"fromZ":92,"toZ":65,"at":.56}],
    }
    second={
        "kind":"sequence","title":"The first leaves unfold",
        "narration":"The new shoot rises into the light. Its first leaves expand while the growing root reaches further into the soil.",
        "steps":["Shoot rises","Leaves unfold","Root extends"],
        "visualVectors":vectors,
        "actorTracks":[
            {"z":55,"keys":[key(0,0,0,.87,0,.94),
                             key(.5,-.01,-.02,1.1,-2,1),
                             key(1,-.015,-.04,1.24,-4,1)]},
            {"z":65,"keys":[key(0,0,0,1.01,2,1),
                             key(.5,.005,-.006,1.03,4,1),
                             key(1,.01,-.008,.98,6,1)]},
            {"z":78,"keys":[key(0,0,0,.65,3,.56),
                             key(.5,-.004,-.08,.94,0,.88),
                             key(1,-.005,-.13,1.22,-2,1)]},
            {"z":92,"keys":[key(0,.02,.045,.58,4,.22),
                             key(.5,.035,.085,.52,7,.13),
                             key(1,.042,.12,.50,9,0)]},
        ],
        "actorLinks":[{"fromZ":65,"toZ":78,"at":.63}],
    }
    return {
        "schemaVersion":1,"topic":"An original 2.5D botanical story",
        "language":"en","beats":[first,second],
    }


def main():
    parser=argparse.ArgumentParser(description="Make an original 2.5D botanical vector story")
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(build_story(),ensure_ascii=False,indent=2)+"\n",
                     encoding="utf8")
    print(a.out)


if __name__=="__main__":
    main()
