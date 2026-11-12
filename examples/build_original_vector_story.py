"""Produce a real topic-specific vector illustration with no source PNGs.

Original authored vector primitives become five depth layers and four
independently articulated subjects, including three parented components.
This is a fixture for the reusable vector interface, not a claim that
unstructured natural language already generates anatomically correct art.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

RIGHTS=("Original decorative vector artwork authored in this project "
        "using mathematical shapes, no images or external model.")
FILL=None


def rect(x0,y0,x1,y1,colors,radius=.025,stroke=None,width=0.):
    return {"kind":"roundedRect","box":[x0,y0,x1,y1],"radius":radius,
            "fill":colors,"stroke":stroke,"strokeWidth":width}


def ellipse(x0,y0,x1,y1,colors,stroke=None,width=0.):
    return {"kind":"ellipse","box":[x0,y0,x1,y1],
            "fill":colors,"stroke":stroke,"strokeWidth":width}


def path(points,colors,stroke=None,width=0.):
    return {"kind":"bezier","points":points,"closed":True,
            "fill":colors,"stroke":stroke,"strokeWidth":width}


def line(points,color,width=.0025):
    return {"kind":"line","points":points,"fill":None,
            "stroke":color,"strokeWidth":width}


def poly(points,colors,stroke=None,width=0):
    return {"kind":"polygon","points":points,
            "fill":colors,"stroke":stroke,"strokeWidth":width}


def art(ident,z,px,py,shapes,material="none"):
    return {
        "id":ident,"z":z,"parallaxX":px,"parallaxY":py,
        "material":material,"rights":RIGHTS,"rightsConfirmed":True,
        "shapes":shapes,
    }


def landscape():
    shapes=[
        rect(0,0,1,1,["#081C34","#244C5F"],.003),
        ellipse(.57,.05,.95,.39,["#FAD18C","#E58975"]),
        ellipse(.635,.092,.91,.33,["#FFE5B0","#F7BD82"]),
        poly([[0,.77],[.21,.59],[.38,.73],[.54,.55],[.79,.77],[1,.59],[1,1],[0,1]],
             ["#0C3946","#092932"]),
        poly([[0,.84],[.27,.67],[.57,.80],[.79,.70],[1,.78],[1,1],[0,1]],
             ["#194B55","#0C303C"]),
        rect(0,.79,1,1,["#285C57","#0B2D38"],.008),
        ellipse(.04,.83,.96,.97,["#2E6963","#102F38"]),
    ]
    # Original distributed botanical texture, sampled deterministically.
    for i in range(18):
        x=((i*131+47)%937)/937
        y=((i*71+83)%997)/997*.52+.08
        size=.0030+(.0015*(i%3))
        shapes.append(ellipse(x,y,x+size,y+size,
                             "#C9E7DC" if i%3 else "#F0C98D"))
    return art("gradient-garden",5,.12,.08,shapes)


def stem():
    return art("flower-stem",35,.77,.35,[
        path([[.485,.86],[.46,.74],[.49,.65],[.485,.50],
              [.49,.36],[.49,.32],[.512,.27],
              [.503,.40],[.52,.52],[.526,.64],
              [.54,.73],[.53,.84],[.515,.88],
              [.506,.88],[.495,.88],[.485,.86]],
             ["#76B98B","#24665D"],"#B4E0A1",.002),
        line([[.497,.78],[.50,.63],[.499,.47],[.499,.34]],
             "#B9E1AB",.003),
        ellipse(.484,.292,.518,.324,["#E4B474","#E7CB8D"]),
    ],"foliage")


def left_leaf():
    return art("left-leaf",55,.83,.45,[
        path([[.382,.635],[.32,.60],[.27,.545],[.21,.535],
              [.246,.65],[.294,.715],[.401,.694],
              [.446,.68],[.459,.66],[.382,.635]],
             ["#90CB9F","#266B66"],"#C3E5AC",.003),
        line([[.402,.678],[.327,.641],[.268,.58]],"#C6EDB6",.003),
        line([[.349,.651],[.343,.615]],"#8FCAA5",.002),
        line([[.313,.63],[.282,.631]],"#8FCAA5",.002),
        path([[.26,.575],[.286,.583],[.32,.625],[.349,.654],
              [.315,.625],[.29,.613],[.26,.575]],
             "#A9DAAE"),
    ],"foliage")


def right_leaf():
    return art("right-leaf",65,.93,.54,[
        path([[.537,.57],[.606,.527],[.677,.475],[.735,.481],
              [.717,.61],[.667,.668],[.557,.638],
              [.535,.627],[.517,.6],[.537,.57]],
             ["#8DC9A7","#185A60"],"#BEE5B0",.003),
        line([[.553,.607],[.636,.576],[.708,.512]],"#CDEBC4",.003),
        line([[.609,.585],[.617,.535]],"#8FC2A7",.002),
        line([[.66,.556],[.679,.605]],"#8FC2A7",.002),
        ellipse(.678,.515,.708,.553,["#E7C18A","#B2BD8F"]),
    ],"foliage")


def blossom():
    shapes=[
        # Multiple original, separated curved petals and independent rims
        path([[.505,.44],[.457,.375],[.433,.285],[.458,.21],
              [.507,.216],[.539,.282],[.505,.44]],
             ["#FDD3AE","#D97088"],"#FFDFB0",.004),
        path([[.501,.443],[.542,.35],[.597,.28],[.658,.296],
              [.652,.376],[.593,.435],[.501,.443]],
             ["#FBD2A5","#C96583"],"#FFE3BD",.004),
        path([[.505,.445],[.588,.435],[.68,.44],[.705,.52],
              [.636,.583],[.544,.533],[.505,.445]],
             ["#E3A2A5","#9E4D81"],"#F0C4AA",.004),
        path([[.5,.447],[.457,.524],[.386,.584],[.335,.535],
              [.317,.47],[.417,.425],[.5,.447]],
             ["#F2A6A1","#BC6085"],"#FFD2B3",.004),
        path([[.496,.449],[.407,.413],[.349,.358],[.371,.29],
              [.424,.283],[.475,.343],[.496,.449]],
             ["#FAC8A7","#C87691"],"#FCE0B4",.004),
        ellipse(.445,.388,.55,.49,["#FFF0BF","#DFB665"],"#FFE6AC",.003),
        ellipse(.465,.41,.525,.468,["#F9D891","#C98A56"]),
        ellipse(.477,.414,.487,.424,"#FFF5D9"),
        ellipse(.506,.45,.518,.461,"#FFF5D9"),
        ellipse(.517,.419,.528,.431,"#FFF5D9"),
        line([[.477,.363],[.486,.324],[.474,.292]],"#FFE0B7",.003),
        line([[.578,.399],[.608,.364],[.642,.354]],"#FFE0B7",.003),
        line([[.412,.486],[.369,.5],[.354,.52]],"#F7D5B9",.003),
    ]
    return art("detailed-bloom",85,1.12,.55,shapes,"foliage")


def k(at,x=0,y=0,scale=1,angle=0):
    return {"at":at,"x":x,"y":y,"scale":scale,"angle":angle}


def layers():
    return [landscape(),stem(),left_leaf(),right_leaf(),blossom()]


def beat(index):
    if index==0:
        title="An illustrated flower wakes"
        narration=("In a fictional garden, the layered flower lifts toward a warm light. "
                   "Its leaves turn gently while each painted petal keeps its soft color.")
        nodes=["Garden","Stem","Petals"]
        tracks=[
            {"z":35,"keys":[k(0,scale=.82,angle=-6),k(.5,y=-.014,scale=.94,angle=2),
                              k(1,y=-.027,scale=1.04,angle=7)]},
            {"z":55,"parentZ":35,"attach":[.33,.64],"pivot":[.93,.57],
             "keys":[k(0,angle=-18),k(.5,angle=5),k(1,angle=13)]},
            {"z":65,"parentZ":35,"attach":[.7,.43],"pivot":[.06,.50],
             "keys":[k(0,angle=16),k(.5,angle=-8),k(1,angle=-14)]},
            {"z":85,"parentZ":35,"attach":[.5,.10],"pivot":[.5,.96],
             "keys":[k(0,scale=.78,angle=-11),k(.5,scale=.9,angle=1),
                      k(1,scale=1.02,angle=7)]},
        ]
    else:
        title="Its layered petals unfold"
        narration=("The same flower remains on screen as the camera moves closer. "
                   "The petals open further, and the illustrated garden settles into light.")
        nodes=["Unfold","Light","Garden"]
        tracks=[
            {"z":35,"keys":[k(0,y=-.027,scale=1.04,angle=7),
                              k(.5,y=-.047,scale=1.10,angle=3),
                              k(1,y=-.044,scale=1.03,angle=-3)]},
            {"z":55,"parentZ":35,"attach":[.33,.64],"pivot":[.93,.57],
             "keys":[k(0,angle=13),k(.5,angle=27),k(1,angle=8)]},
            {"z":65,"parentZ":35,"attach":[.7,.43],"pivot":[.06,.50],
             "keys":[k(0,angle=-14),k(.5,angle=-28),k(1,angle=-9)]},
            {"z":85,"parentZ":35,"attach":[.5,.10],"pivot":[.5,.96],
             "keys":[k(0,scale=1.02,angle=7),k(.5,scale=1.18,angle=-3),
                      k(1,scale=1.11,angle=3)]},
        ]
    return {
        "kind":"concept","title":title,"narration":narration,
        "nodes":nodes,
        "visualVectors":layers(),
        "actorTracks":tracks,
        "actorLinks":[{"fromZ":55,"toZ":85,"at":.57}],
    }


def build(out: Path):
    out.mkdir(parents=True,exist_ok=True)
    path=out/"original-vector-story.json"
    story={"schemaVersion":1,"topic":"An original illustrated flower",
           "language":"en","beats":[beat(0),beat(1)]}
    path.write_text(json.dumps(story,indent=2,ensure_ascii=False)+"\n",
                    encoding="utf8")
    return path


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--out-dir",type=Path,required=True)
    args=cli.parse_args()
    print(build(args.out_dir))
