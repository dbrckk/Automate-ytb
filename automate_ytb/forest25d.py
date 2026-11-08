"""Original moving fox in a genuinely layered 2.5D meadow.

This is an integration of the *existing* animal artwork and the shared
Scene25D compositor with analytic, world-grounded IK. Unlike the legacy
FFmpeg oscillating foot overlays, paws stay fixed during stance while knees
solve their position in response to moving hips. The animation is a dedicated
motion pilot; it does not claim to have a Kokoro narration track.
"""
from __future__ import annotations

from functools import lru_cache
import math
from pathlib import Path
import tempfile

from PIL import Image, ImageDraw, ImageFilter

from .animated_forest import _sprite_body, _sprite_tail, _sprite_ear, COLORS
from .scene25d import Layer25D, Scene25D
from .rig25d import walking_leg, GROUND, PERIOD
from .forest_contact25d import IMPACT_TIME, flower_plates
from .forest_butterfly25d import butterfly_plate
from .forest_story25d import story_shot, story_overlay
from .forest_cinematic_world25d import (plates as cinematic_plates,
                                       drifting_clouds, living_light)
from .forest_cinematic_framing25d import cinematic_reframe

SIZE = (1080, 1920)
FPS = 30
SECONDS = 7.2
ORIGIN_X = 195.0
SPEED = 44.0
TORSO_Y = 915.0
VERSION = "forest-25d-cinematic-living-meadow-p36-v1"
KINDS = ("fox", "rabbit", "cat")


@lru_cache(maxsize=1)
def _animal(kind: str) -> dict[str, Image.Image]:
    if kind not in KINDS:
        raise ValueError("Unsupported original 2.5D forest animal")
    with tempfile.TemporaryDirectory(prefix=f"p3-{kind}-sprites-") as folder:
        p = Path(folder)
        paths = {name: p / (name + ".png") for name in
                 ("body", "blink", "tail", "left", "right")}
        _sprite_body(paths["body"], kind=kind, blink=False, emotion="happy",
                     gaze="forward", include_ears=False)
        _sprite_body(paths["blink"], kind=kind, blink=True, emotion="happy",
                     gaze="forward", include_ears=False)
        _sprite_tail(paths["tail"], kind=kind)
        for side in ("left", "right"):
            _sprite_ear(paths[side], kind=kind, side=side)
        return {name: Image.open(path).convert("RGBA").copy()
                for name, path in paths.items()}


def _landscape() -> dict[str, Image.Image]:
    """Reuse cached, authored P3.6 plates across every frame and animal."""
    return cinematic_plates()


@lru_cache(maxsize=1)
def _contact_shadow() -> Image.Image:
    shadow=Image.new("RGBA",(390,100))
    d=ImageDraw.Draw(shadow)
    d.ellipse((8,33,382,76),fill=(10,35,29,105))
    return shadow.filter(ImageFilter.GaussianBlur(17))


def _rotate_about(image: Image.Image, degrees: float,
                  pivot: tuple[int,int]) -> Image.Image:
    return image.rotate(degrees,center=pivot,
                        resample=Image.Resampling.BICUBIC,
                        expand=False)


def character_plate(t: float, *, kind: str = "fox",
                    interaction: bool = False) -> tuple[Image.Image, dict]:
    """Real sprite rig; rear paws articulate beneath the original fox torso."""
    if type(t) not in (int,float) or not math.isfinite(t) or not 0<=t<=SECONDS:
        raise ValueError("Invalid original fox clock")
    if kind not in KINDS or type(interaction) is not bool:
        raise ValueError("Unsupported original 2.5D forest animal or interaction")
    assets=_animal(kind)
    canvas=Image.new("RGBA",SIZE)
    draw=ImageDraw.Draw(canvas)
    x=ORIGIN_X+SPEED*t
    y=TORSO_Y+3*math.cos(4*math.pi*t/PERIOD)
    fur=COLORS[kind]["fur"]
    dark=COLORS[kind]["dark"]
    legs={}
    for side in ("left","right"):
        pose=walking_leg(t,side=side,origin_x=ORIGIN_X,
                         speed=SPEED,torso_y=TORSO_Y,ground_y=GROUND)
        legs[side]=pose
        line=(pose.hip,pose.knee,pose.foot)
        draw.line(line,fill=dark,width=36,joint="curve")
        draw.line(line,fill=fur,width=26,joint="curve")
        for node,radius in ((pose.hip,13),(pose.knee,15)):
            px,py=node
            draw.ellipse((px-radius,py-radius,px+radius,py+radius),
                         fill=fur,outline=dark,width=3)
        foot_x,foot_y=pose.foot
        draw.ellipse((foot_x-29,foot_y-10,foot_x+29,foot_y+9),
                     fill=fur,outline=dark,width=3)
        for offset in (-11,0,11):
            draw.line((foot_x+offset,foot_y+2,foot_x+offset+2,foot_y+8),
                      fill=dark,width=2)
    reaction=(math.exp(-((t-IMPACT_TIME-.16)/.29)**2)
              if interaction else 0.)
    tail=_rotate_about(assets["tail"],
                       8*math.sin(2.0*t-.7)+11*reaction,(197,202))
    if kind=="rabbit":
        # The legacy full-size rabbit tail is a very large detached disk in
        # this IK composition. Keep the species artwork but resize its plate
        # and anchor the fluffy silhouette behind the lower left torso.
        tail=tail.resize((138,144),Image.Resampling.LANCZOS)
        canvas.alpha_composite(tail,(round(x-18),round(y+230)))
    else:
        canvas.alpha_composite(tail,(round(x-141),round(y+165)))
    for side,offset in (("left",0),("right",200)):
        tilt=(4.5 if side=="left" else -4.5)*math.sin(t*3.6+.4)
        tilt+=(8 if side=="left" else -6)*reaction
        ear=_rotate_about(assets[side],tilt,(76,173))
        canvas.alpha_composite(ear,(round(x+offset),round(y)))
    blink=(t%3.1)<.105 or (interaction and IMPACT_TIME+.22<t<IMPACT_TIME+.33)
    canvas.alpha_composite(assets["blink" if blink else "body"],
                           (round(x),round(y)))
    return canvas,dict(kind=kind,bodyX=round(x,3),bodyY=round(y,3),
                       left=legs["left"],right=legs["right"])


def frame(t: float, *, kind: str = "fox",
          interaction: bool = False, story: bool = False,
          show_story_titles: bool = True) -> Image.Image:
    if type(story) is not bool or type(show_story_titles) is not bool:
        raise ValueError("Story and title flags must be boolean")
    if story and not interaction:
        raise ValueError("Causal story requires real paw-flower interaction")
    actor,meta=character_plate(t,kind=kind,interaction=interaction)
    landscape=_landscape()
    scene=Scene25D(SIZE)
    scene.add(Layer25D("sky",0,landscape["sky"]))
    scene.add(Layer25D("clouds",10,drifting_clouds(t),parallax_x=.18))
    scene.add(Layer25D("ridges",20,landscape["ridges"],parallax_x=.36))
    scene.add(Layer25D("sunbeams",25,landscape["sunbeams"],parallax_x=.42))
    scene.add(Layer25D("trees",30,landscape["trees"],parallax_x=.58))
    scene.add(Layer25D("understory",35,landscape["understory"],parallax_x=.67))
    scene.add(Layer25D("meadow",40,landscape["meadow"],parallax_x=.72))
    shadow=Image.new("RGBA",SIZE)
    shadow.alpha_composite(_contact_shadow(),
                           (round(meta["bodyX"]-12),round(GROUND-37)))
    scene.add(Layer25D("grounded-shadow",50,shadow))
    if interaction:
        behind,petals=flower_plates(
            t,origin_x=ORIGIN_X,speed=SPEED,torso_y=TORSO_Y)
        scene.add(Layer25D("responsive-flower",55,behind))
    scene.add(Layer25D("ik-"+kind,60,actor))
    # Ground reaction is driven by real contact, not arbitrary particles.
    ground_fx=Image.new("RGBA",SIZE)
    g=ImageDraw.Draw(ground_fx)
    for side in ("left","right"):
        paw=meta[side]
        if paw.planted and paw.phase<.10:
            f=1-paw.phase/.10
            xx,yy=paw.foot
            radius=round(14+32*(1-f))
            g.arc((xx-radius,yy-8,xx+radius,yy+8),190,350,
                  fill=(182,226,136,round(100*f)),width=3)
    scene.add(Layer25D("contact-reactions",70,ground_fx))
    if interaction:
        scene.add(Layer25D("released-petals",75,petals))
        scene.add(Layer25D(
            "reactive-butterfly",80,
            butterfly_plate(t,origin_x=ORIGIN_X,speed=SPEED,torso_y=TORSO_Y)))
    scene.add(Layer25D("living-light",85,living_light(t),parallax_x=.82))
    scene.add(Layer25D("grass-foreground",90,landscape["foreground"],
                       parallax_x=1.15))
    scene.add(Layer25D("filmic-grade",95,landscape["grade"]))
    # Event-directed camera uses the same physical contact and butterfly
    # timeline as the animated world. Legacy motion preview is unchanged.
    if story:
        shot=story_shot(t)
        rendered=scene.render(camera_x=shot.camera_x,camera_y=shot.camera_y)
        rendered=cinematic_reframe(rendered,t=t,beat=shot.beat,
                                   body_x=meta["bodyX"])
        if show_story_titles:
            rendered.alpha_composite(story_overlay(t))
    else:
        camera=30*math.sin(math.pi*t/SECONDS)
        rendered=scene.render(camera_x=camera,camera_y=4*camera/30)
    return rendered.convert("RGB")
