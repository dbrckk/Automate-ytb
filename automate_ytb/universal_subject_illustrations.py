"""Grounded, reusable original subject illustrations from explicit FR/EN nouns.

This is a deliberately bounded, deterministic **procedural illustration**
library, not an image model and not evidence for the truth of the narration.
Only recognized subject words in the supplied original text select a template.
No stock images, internet calls, paid credits, AI hallucinated objects or data.
Every subject uses the existing 2.5D vector, material, depth and actor rig.
Unknown topics retain the established honest generic visualization.
"""
from __future__ import annotations

from copy import deepcopy
import math
import re

VERSION = "original-source-anchored-procedural-subjects-v1"
CHAPTER_VERSION = "source-grounded-per-beat-illustration-sequence-v1"
RIGHTS = ("Original artwork generated locally by Automate-ytb procedural "
          "geometry authored in this repository; no external source images.")
# Intentionally concrete words only, not untrusted semantic or fuzzy matching.
_TERMS = {
    "maglev": ("maglev", "scmaglev", "magnetic levitation",
               "magnetic-levitation", "lévitation magnétique",
               "train à lévitation"),
    "botanical": ("forest","forests","tree","trees","seed","seeds",
                  "plant","plants","leaf","leaves","garden","gardens",
                  "forêt","forêts","arbre","arbres","graine","graines",
                  "plante","plantes","feuille","feuilles","jardin","jardins"),
    "celestial": ("planet","planets","moon","moons","orbit","orbits",
                  "galaxy","galaxies","space","solar","astronomy",
                  "planète","planètes","lune","lunes","orbite","orbites",
                  "galaxie","galaxies","espace","astronomie"),
    "rail": ("railway","railways","train","trains","locomotive",
             "railroad","railroads","rail","rails","chemin de fer",
             "ferroviaire","locomotives","voie ferrée"),
    "weather": ("cloud","clouds","storm","storms","rain","rains",
                "rainfall","thunder","nuage","nuages","orage","orages",
                "pluie","pluies","tempête","tempêtes"),
    "ocean": ("ocean","oceans","wave","waves","tide","tides",
              "sea","seas","marine","océan","océans","vague",
              "vagues","marée","marées","mer","mers"),
    "security": ("password","passwords","firewall","cybersecurity",
                 "authentication","login","encryption","secure",
                 "cybersécurité","authentification","chiffrement",
                 "mot de passe","pare-feu"),
}
_ORDER = tuple(_TERMS)
_PATTERN = {
    family:tuple(re.compile(r"(?<!\w)"+re.escape(term)+r"(?!\w)",re.I)
                 for term in terms)
    for family,terms in _TERMS.items()
}
_PALETTE = {
    "maglev": ("#070E22","#111D3B","#203D58","#40D6CF","#F2B67D"),
    "botanical": ("#092533","#174C50","#4D8173","#B8E5A2","#EBCA8A"),
    "celestial": ("#09142D","#26345A","#5F659F","#C3B7E8","#F9D7A0"),
    "rail": ("#141F38","#344A5C","#6C9295","#E2BB82","#F5E3C5"),
    "weather": ("#0C1E36","#325D76","#6594A9","#BBDDE2","#F4D9A5"),
    "ocean": ("#06283F","#12637A","#3D9FA6","#A4E9DF","#F4DDA9"),
    "security": ("#081C32","#1C5267","#39878B","#8DE0C9","#E8D4A2"),
}


def select_subject(topic: str, narration: str) -> str | None:
    """A noun must occur in the original script; topic only breaks ties.

    For negated explicit nouns we do not imply the negated object's presence.
    This is not NLP; it is a conservative finite template vocabulary.
    """
    if type(topic) is not str or type(narration) is not str:
        raise ValueError("Original text must be a string")
    content=narration.casefold()
    leading=topic.casefold()
    ranking=[]
    for family in _ORDER:
        matches=[]
        for pattern in _PATTERN[family]:
            for match in pattern.finditer(content):
                before=content[max(0,match.start()-30):match.start()]
                words=re.findall(r"[^\W_]+",before,re.UNICODE)
                if words[-1:] and words[-1] in ("no","not","sans","aucun","aucune"):
                    continue
                matches.append(match.group(0).casefold())
        if not matches:
            continue
        in_topic=sum(bool(p.search(leading)) for p in _PATTERN[family])
        ranking.append((len(set(matches))+min(2,len(matches))*.1+in_topic*2,
                        -_ORDER.index(family),family))
    # A source-explicit precise subject wins over a generic train mention.
    # No title-only guess: 'maglev' must really be in narrated text.
    if any(record[2]=="maglev" for record in ranking):
        return "maglev"
    return max(ranking)[2] if ranking else None


def _multi(colors, direction="radial", space="shape"):
    return {"colors":list(colors),"direction":direction,"space":space}


def _ell(x0,y0,x1,y1,fill,stroke=None,strokeWidth=0,opacity=1.):
    shape={"kind":"ellipse","box":[x0,y0,x1,y1],"fill":fill,
           "stroke":stroke,"strokeWidth":strokeWidth}
    if opacity!=1.:
        shape["opacity"]=opacity
    return shape


def _box(x0,y0,x1,y1,fill,radius=.03,stroke=None,strokeWidth=0):
    return {"kind":"roundedRect","box":[x0,y0,x1,y1],"radius":radius,
            "fill":fill,"stroke":stroke,"strokeWidth":strokeWidth}


def _poly(points,fill,stroke=None,strokeWidth=0,opacity=1.):
    shape={"kind":"polygon","points":points,"fill":fill,
           "stroke":stroke,"strokeWidth":strokeWidth}
    if opacity!=1.:
        shape["opacity"]=opacity
    return shape


def _line(points,color,width=.003,opacity=1.):
    shape={"kind":"line","points":points,"fill":None,
           "stroke":color,"strokeWidth":width}
    if opacity!=1.:
        shape["opacity"]=opacity
    return shape


def _bezier(points,fill,stroke=None,strokeWidth=0,opacity=1.):
    shape={"kind":"bezier","points":points,"closed":True,
           "fill":fill,"stroke":stroke,"strokeWidth":strokeWidth}
    if opacity!=1.:
        shape["opacity"]=opacity
    return shape


def _layer(family,z,ident,shapes,parallax=(.5,.23),material="none"):
    if not 1<=len(shapes)<=48:
        raise ValueError("Procedural illustrator exceeded bounded vector budget")
    return {"id":family+"-"+ident,"z":z,
            "parallaxX":parallax[0],"parallaxY":parallax[1],
            "material":material,"rights":RIGHTS,"rightsConfirmed":True,
            "shapes":shapes}


def _world(family):
    dark,deep,mid,light,gold=_PALETTE[family]
    sky=[_box(0,0,1,1,_multi([dark,deep,mid],"vertical","stage"),.002),
         _ell(.64,.065,.96,.385,_multi([gold,light,mid]),opacity=.57),
         _ell(.70,.124,.90,.315,_multi([gold,light]),opacity=.36)]
    for i in range(22):
        x=(.018+((i*73+19)%937)/1020)
        y=.04+((i*149+17)%887)/1650
        d=.0025+(i%4)*.0007
        sky.append(_ell(x,y,x+d,y+d,light if i%4 else gold,opacity=.68))
    terrain=[
        _poly([[0,.77],[.18,.67],[.38,.72],[.54,.64],[.72,.70],
               [.88,.61],[1,.66],[1,1],[0,1]],
              _multi([mid,deep,dark],"vertical","stage"),opacity=.63),
        _poly([[0,.86],[.16,.76],[.35,.82],[.53,.745],[.72,.815],
               [.89,.72],[1,.78],[1,1],[0,1]],
              _multi([deep,dark],"vertical","stage"),opacity=.80),
        _ell(.07,.75,.94,.88,mid,opacity=.12),
    ]
    if family=="celestial":
        terrain=[
            _ell(.06,.65,.93,.89,mid,opacity=.36),
            _ell(.20,.70,.83,.84,light,opacity=.20),
            _line([[.08,.89],[.28,.74],[.56,.76],[.9,.67]],light,.004,.23),
        ]
    elif family=="ocean":
        terrain=[
            _bezier([[0,.81],[.18,.71],[.33,.79],[.50,.73],
                     [.67,.67],[.84,.76],[1,.69],
                     [1,.87],[.3,.91],[0,.94]],
                    _multi([mid,deep,dark],"vertical"),opacity=.65),
            _line([[.04,.8],[.3,.77],[.56,.79],[.8,.73],[.96,.76]],
                  light,.003,.35),
        ]
    elif family=="rail":
        terrain=[
            _poly([[0,.805],[1,.805],[1,.93],[0,.93]],deep,opacity=.65),
            _line([[0,.84],[1,.84]],light,.008,.62),
            _line([[0,.89],[1,.89]],gold,.006,.49),
            _line([[.12,.81],[.28,.92]],mid,.009,.55),
            _line([[.46,.81],[.55,.92]],mid,.009,.55),
            _line([[.82,.81],[.77,.92]],mid,.009,.55),
        ]
    elif family=="security":
        terrain=[
            _poly([[0,.80],[.31,.78],[.47,.84],[.7,.73],[1,.78],
                   [1,.98],[0,.98]],_multi([deep,dark],"vertical"),opacity=.5),
            _line([[.08,.72],[.35,.72],[.52,.81],[.89,.81]],mid,.004,.43),
            _line([[.16,.88],[.37,.86],[.71,.91],[.95,.87]],light,.003,.27),
        ]
    return sky,terrain


def _botanical():
    dark,deep,mid,light,gold=_PALETTE["botanical"]
    trunk=[
        _bezier([[.475,.87],[.477,.75],[.469,.66],[.482,.53],
                 [.472,.43],[.485,.38],[.49,.33],
                 [.506,.39],[.507,.48],[.517,.57],
                 [.53,.68],[.527,.79],[.533,.87],
                 [.515,.889],[.494,.887],[.475,.87]],
                _multi(["#344C48","#6A8E6D","#263C3D"],"horizontal"),"#9DC3A0",.003),
        _line([[.496,.81],[.499,.58],[.493,.44]],"#B8D6AC",.003),
        _line([[.49,.54],[.444,.46],[.402,.40]],"#8ABFA2",.008),
        _line([[.504,.51],[.558,.432],[.616,.396]],"#8ABFA2",.008),
        _ell(.45,.835,.553,.89,deep,opacity=.45),
    ]
    leaves=[
        _bezier([[.50,.20],[.423,.20],[.355,.27],[.351,.348],
                 [.322,.427],[.433,.46],[.50,.43],
                 [.612,.473],[.71,.406],[.67,.318],
                 [.636,.21],[.58,.191],[.50,.20]],
                _multi(["#E0E8AD","#75B89E","#225E62","#143E4F"],
                       "radial"),"#C8E8B3",.003),
        _ell(.35,.27,.49,.43,_multi(["#D6E9B6","#599785","#1B515D"]),opacity=.75),
        _ell(.53,.25,.665,.405,_multi(["#C8DDA4","#4B9A82","#275F66"]),opacity=.72),
        _ell(.425,.20,.55,.345,_multi(["#EDF1C1","#97C99A","#487F75"]),opacity=.66),
    ]
    for i in range(14):
        x=.355+((i*53)%281)/1000
        y=.23+((i*29)%172)/1000
        sz=.007+(i%4)*.002
        leaves.append(_ell(x,y,x+sz,y+sz,light if i%3 else gold,opacity=.65))
    details=[]
    for i in range(19):
        x=.18+((i*71+31)%612)/1000
        y=.17+((i*41+23)%540)/1000
        d=.016+(i%5)*.004
        details.append(_ell(x,y,x+d,y+d,light if i%2 else gold,opacity=.40))
    return trunk,leaves,details


def _celestial():
    dark,deep,mid,light,gold=_PALETTE["celestial"]
    globe=[
        _ell(.325,.28,.70,.70,_multi(["#FFE0AB","#A38DC7","#465B98","#1E426A"],
                                    "radial"),"#BBCBEA",.003),
        _ell(.355,.323,.662,.625,_multi(["#E1CDA6","#6B80B7","#345A89"],
                                        "diagonal"),opacity=.55),
        _bezier([[.338,.46],[.428,.427],[.50,.46],[.676,.405],
                 [.677,.469],[.527,.524],[.347,.515],
                 [.321,.49],[.326,.48],[.338,.46]],
                "#94A5BC",opacity=.40),
        _bezier([[.345,.55],[.44,.516],[.512,.569],[.679,.536],
                 [.649,.61],[.481,.63],[.377,.607],
                 [.342,.592],[.338,.567],[.345,.55]],
                "#D7BEB5",opacity=.40),
        _ell(.39,.347,.476,.434,light,opacity=.13),
    ]
    orbit=[
        _ell(.245,.385,.785,.655,None,"#CBBCE3",.008,opacity=.67),
        _ell(.26,.398,.777,.644,None,"#F7E0AC",.003,opacity=.70),
        _ell(.70,.455,.765,.525,_multi([gold,mid,deep]),opacity=.91),
        _ell(.705,.465,.728,.488,light,opacity=.58),
    ]
    shine=[]
    for i in range(18):
        x=.23+((i*103+31)%555)/1000
        y=.17+((i*89+43)%640)/1000
        d=.019+(i%4)*.008
        shine.append(_ell(x,y,x+d,y+d,gold if i%3==0 else light,
                          opacity=.32+.09*(i%3)))
    return globe,orbit,shine


def _rail():
    dark,deep,mid,light,gold=_PALETTE["rail"]
    engine=[
        _box(.28,.49,.74,.68,_multi(["#7EADB0","#416878","#263B55"],
                                    "vertical"),.034,"#B7D4C6",.003),
        _box(.37,.385,.60,.54,_multi(["#C2DACC","#55888C","#24465E"],
                                     "diagonal"),.025,"#D9EBDD",.003),
        _box(.398,.41,.46,.488,"#B6DBD3",.008),
        _box(.487,.41,.558,.488,_multi([gold,light,mid],"radial"),.008),
        _box(.282,.61,.75,.69,"#20374B",.018),
        _box(.626,.435,.685,.504,"#B3916D",.009),
        _box(.622,.394,.693,.443,"#33495E",.011),
        _poly([[.73,.584],[.803,.643],[.736,.70],[.691,.688]],"#A17669"),
    ]
    for x in (.37,.54,.695):
        engine.extend([
            _ell(x-.049,.642,x+.049,.75,_multi(["#A9BBB5","#46576B","#132A3F"]),
                 "#D5E1D4",.003),
            _ell(x-.02,.672,x+.02,.716,gold,opacity=.7),
        ])
    machine=[
        _box(.38,.392,.468,.496,_multi(["#EFF3D6","#86B7B1","#285A6B"],
                                       "radial"),.013),
        _box(.483,.392,.58,.495,_multi(["#DFEACB","#84B8B3","#285C6C"],
                                       "radial"),.013),
        _ell(.724,.56,.783,.621,_multi([gold,light,mid],"radial"),opacity=.80),
        _line([[.286,.574],[.735,.574]],"#C3DCC9",.005),
    ]
    smoke=[]
    for i in range(16):
        x=.52+((i*59)%155)/1000
        y=.13+((i*73)%280)/1000
        d=.038+(i%4)*.012
        smoke.append(_ell(x,y,x+d,y+d,_multi([light,mid,deep]),
                          opacity=.18+.06*(i%3)))
    return engine,machine,smoke


def _weather():
    dark,deep,mid,light,gold=_PALETTE["weather"]
    body=[
        _ell(.28,.38,.54,.62,_multi([light,mid,deep],"radial")),
        _ell(.37,.29,.66,.61,_multi(["#E5EDF0",mid,deep],"radial")),
        _ell(.54,.38,.76,.615,_multi([light,mid,deep],"radial")),
        _box(.30,.47,.71,.624,_multi([mid,deep,dark],"vertical"),.052),
        _ell(.42,.31,.57,.43,light,opacity=.17),
    ]
    rain=[]
    for i in range(16):
        x=.29+i*.027
        y=.645+((i*11)%55)/1000
        rain.append(_line([[x,y],[x-.02,y+.057]],light,.005,opacity=.57))
    for i in range(8):
        x=.313+i*.051
        y=.682+((i*17)%48)/1000
        rain.append(_ell(x,y,x+.023,y+.032,
                         _multi([light,mid,deep],"vertical"),opacity=.52))
    details=[]
    for i in range(15):
        x=.30+(i*97%400)/1000
        y=.14+(i*37%280)/1000
        d=.020+(i%3)*.006
        details.append(_ell(x,y,x+d,y+d,light if i%2 else gold,opacity=.4))
    return body,rain,details


def _ocean():
    dark,deep,mid,light,gold=_PALETTE["ocean"]
    wave=[
        _bezier([[.13,.76],[.23,.52],[.36,.47],[.52,.46],
                 [.62,.43],[.75,.52],[.83,.70],
                 [.71,.66],[.63,.648],[.57,.677],
                 [.42,.73],[.29,.74],[.13,.76]],
                _multi(["#CBEEE1","#5EB5B6","#216C85","#123E62"],
                       "diagonal"),"#A1EDE1",.003),
        _bezier([[.30,.565],[.40,.455],[.51,.441],[.60,.447],
                 [.544,.492],[.424,.553],[.355,.635],
                 [.318,.644],[.305,.607],[.30,.565]],gold,opacity=.25),
        _ell(.358,.51,.456,.564,light,opacity=.22),
    ]
    foam=[
        _bezier([[.29,.506],[.399,.435],[.491,.423],[.615,.452],
                 [.56,.482],[.44,.468],[.378,.526],
                 [.342,.524],[.312,.521],[.29,.506]],
                "#D9F9E8",opacity=.84),
        _line([[.34,.566],[.416,.533],[.49,.504],[.566,.508],
               [.64,.554]],"#C7F4E6",.006,opacity=.72),
    ]
    drops=[]
    for i in range(22):
        x=.25+((i*43+19)%515)/1000
        y=.20+((i*87+7)%515)/1000
        d=.012+(i%5)*.004
        drops.append(_ell(x,y,x+d,y+d,light if i%3 else gold,
                          opacity=.28+.1*(i%3)))
    return wave,foam,drops


def _security():
    dark,deep,mid,light,gold=_PALETTE["security"]
    device=[
        _box(.35,.43,.68,.735,_multi([light,mid,deep,dark],"diagonal"),
             .045,"#B5EDDE",.004),
        _ell(.399,.264,.623,.549,None,"#B2D9D6",.024),
        _ell(.428,.297,.597,.51,None,gold,.006,opacity=.53),
        _box(.382,.47,.649,.695,_multi(["#83C9BA","#286C76","#173F58"],
                                       "radial"),.027),
        _ell(.476,.526,.55,.601,_multi([gold,light,mid],"radial")),
        _poly([[.501,.576],[.523,.576],[.541,.652],[.484,.652]],gold),
    ]
    circuit=[
        _line([[.16,.466],[.315,.466],[.36,.487]],light,.007,opacity=.71),
        _line([[.677,.489],[.75,.489],[.85,.429]],light,.007,opacity=.71),
        _line([[.17,.67],[.29,.67],[.347,.622]],gold,.006,opacity=.68),
        _line([[.681,.655],[.76,.655],[.836,.722]],gold,.006,opacity=.68),
        _ell(.14,.451,.18,.492,light),
        _ell(.815,.411,.858,.452,gold),
    ]
    signals=[]
    for i in range(16):
        x=.25+((i*47+21)%480)/1000
        y=.22+((i*73+19)%580)/1000
        d=.018+(i%4)*.005
        signals.append(_ell(x,y,x+d,y+d,gold if i%3 else light,
                            opacity=.32+.1*(i%4)))
    return device,circuit,signals


_BUILDERS={
    "botanical":_botanical,
    "celestial":_celestial,
    "rail":_rail,
    "weather":_weather,
    "ocean":_ocean,
    "security":_security,
}


def subject_layers(family: str) -> list[dict]:
    if family=="maglev":
        from .premium_maglev25d import maglev_scene
        sky,terrain,hero,mid,foreground=maglev_scene()
    elif family in _BUILDERS:
        sky,terrain=_world(family)
        hero,mid,foreground=_BUILDERS[family]()
    else:
        raise ValueError("Unsupported concrete original subject")
    return [
        _layer(family,5,"atmosphere",sky,(.12,.08)),
        _layer(family,25,"landscape",terrain,(.34,.17)),
        _layer(family,45,"hero",hero,(.82,.37)),
        _layer(family,65,"details",mid,(1.16,.54)),
        _layer(family,85,"particles",foreground,(1.42,.77)),
    ]


def _pose(z: int, moment: float) -> dict:
    # Continuous world clock from 0..1 shared by every narrated beat.
    # Sway and parallax travel are analytic, so end/start joins are exact.
    base={25:.55,45:1.0,65:1.2,85:1.55}[z]
    shift=math.tau*(base*moment+.07*(z%4))
    return {
        "x":round(.033*base*math.sin(shift),7),
        "y":round(-.033*moment + .016*math.sin(shift*.75),7),
        "scale":round(1.+.10*moment+.028*math.cos(shift),7),
        "angle":round(3.8*base*math.sin(shift),7),
    }


def subject_tracks(index: int, total: int, *,
                   family: str | None = None,
                   engine: str | None = None) -> list[dict]:
    """New original scripts use subject-specific actions; old JSON keeps v1.

    Existing serialized subject stories from v15 must remain playable. The
    legacy path uses precisely its prior generic track values and 3 keys.
    """
    if family is not None:
        from .universal_subject_motion import subject_motion_tracks
        if engine is None:
            return subject_motion_tracks(family,index,total)
        return subject_motion_tracks(family,index,total,engine=engine)
    if (type(index) is not int or type(total) is not int
            or not 2<=total<=12 or not 0<=index<total):
        raise ValueError("Invalid finite original storyboard clock")
    result=[]
    for z in (25,45,65,85):
        keys=[]
        for at in (0.,.5,1.):
            state=_pose(z,(index+at)/total)
            keys.append({"at":at,**state})
        result.append({"z":z,"keys":keys})
    return result


def apply_original_subjects(topic: str, beats: list[dict]) -> str | None:
    """Modify only original script compiler beats, never supplied user JSON."""
    if (type(beats) is not list or not 2<=len(beats)<=12
            or any(type(b) is not dict or type(b.get("narration")) is not str
                   for b in beats)):
        raise ValueError("Missing validated original storyboard")
    corpus=" ".join(b["narration"] for b in beats)
    family=select_subject(topic,corpus)
    if family is None:
        return None
    layers=subject_layers(family)
    for i,beat in enumerate(beats):
        if any(k in beat for k in ("visualLayers","visualVectors","actorTracks")):
            raise ValueError("Cannot overwrite editorial artwork")
        beat["visualVectors"]=deepcopy(layers)
        beat["actorTracks"]=subject_tracks(i,len(beats),family=family)
    return family


def subject_chapter_families(beats: list[dict]) -> list[str | None] | None:
    """Discover a mixed-topic visual sequence from the words in EACH beat.

    No title-only guess, conversational pronoun inference, or invented facts:
    an unrecognized beat has no concrete original illustration. Single-domain
    videos continue through the unchanged v17 continuous-world pipeline.
    """
    if (type(beats) is not list or not 2 <= len(beats) <= 12
            or any(type(b) is not dict or type(b.get("narration")) is not str
                   for b in beats)):
        raise ValueError("Invalid bounded original mixed-topic storyboard")
    families=[select_subject("",beat["narration"]) for beat in beats]
    return families if len({family for family in families if family}) >= 2 else None


def apply_chapter_subjects(beats: list[dict],
                           families: list[str | None]) -> None:
    """Attach original artwork and continuous global-time poses per beat.

    Same-family adjacent beats have exact matching end/start actor poses and
    source-image hashes. A changed or unrecognized family is a deliberate edit
    with no fabricated actor continuity.
    """
    if (type(families) is not list
            or families != subject_chapter_families(beats)):
        raise ValueError("Chapter art must match multiple narrated source subjects")
    total=len(beats)
    for index,(beat,family) in enumerate(zip(beats,families)):
        if any(key in beat for key in ("visualLayers","visualVectors","actorTracks")):
            raise ValueError("Cannot replace manually authored scene artwork")
        if family is None:
            continue
        beat["visualVectors"]=subject_layers(family)
        beat["actorTracks"]=subject_tracks(index,total,family=family)
