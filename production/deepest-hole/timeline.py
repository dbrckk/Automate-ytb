"""Picture frames and sound events share an integer clock."""
from bisect import bisect_right
from dataclasses import dataclass
import math

FPS=30
RATE=48000
SAMPLES=RATE//FPS
FRAME_COUNT=960
KOLA=12261
RADIUS=6371000

@dataclass(frozen=True)
class Cue:
    frame: int
    name: str
    depth: int
    label: str
    frequency: int

CUES=(
    Cue(26,"contact",0,"GROUND LEVEL",184),
    Cue(124,"tower",828,"BURJ KHALIFA HEIGHT",532),
    Cue(237,"canyon",1600,"GRAND CANYON · AVG DEPTH",390),
    Cue(367,"mine",3740,"MPONENG GOLD MINE",672),
    Cue(561,"record",KOLA,"KOLA SUPERDEEP BOREHOLE",282),
    Cue(674,"pullback",KOLA,"EARTH CUTAWAY",804),
    Cue(803,"reveal",KOLA,"EARTH RADIUS",412),
)
FRAMES=tuple(c.frame for c in CUES)

def ease(x):
    x=max(0.,min(1.,x))
    return x*x*(3-2*x)

def shot(frame):
    return max(0,bisect_right(FRAMES,frame)-1)

def depth(frame):
    index=shot(frame)
    a=CUES[index]
    if index>=4:
        return KOLA
    b=CUES[index+1]
    w=ease((frame-a.frame)/(b.frame-a.frame))
    return math.expm1(math.log1p(a.depth)+(math.log1p(b.depth)-math.log1p(a.depth))*w)
