"""Original deterministic 2D layered owl rig and time-dependent FFmpeg animation.

No external assets or GPU inference; model-like claims are not made. The owl and
its moving wings, body bob and brief blinks are animated in the output video.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import tempfile

from PIL import Image, ImageDraw, ImageFont

from .studio import PALETTES, WIDTH, HEIGHT, font
from .director import validate_direction


RIG_VERSION = "owl-rig-v2-director"
OUTLINE = (50, 36, 86, 255)
PURPLE = (131, 86, 200, 255)
DARK_PURPLE = (98, 60, 161, 255)
LAVENDER = (224, 197, 242, 255)
TEAL = (82, 226, 213, 255)
GOLD = (248, 195, 79, 255)
INK = (23, 29, 54, 255)


def _wrap(draw: ImageDraw.ImageDraw, txt: str, max_width: int, max_lines: int):
    result, line = [], ""
    f = font(30)
    for word in txt.split():
        next_line = (line + " " + word).strip()
        if draw.textbbox((0, 0), next_line, font=f)[2] < max_width:
            line = next_line
        else:
            if line:
                result.append(line)
            line = word
    if line:
        result.append(line)
    if len(result) > max_lines:
        result = result[:max_lines]
        result[-1] = result[-1][:max(0, len(result[-1]) - 2)] + "…"
    return result


def _bg(path: Path, *, topic: str, narration: str, scene_index: int,
        scene_count: int, style: str, direction: dict | None = None):
    base, second, accent = PALETTES[style]
    seed = int.from_bytes(hashlib.sha256(
        f"{scene_index}|{topic}|{narration}".encode()).digest()[:8], "big")
    im = Image.new("RGB", (WIDTH, HEIGHT), base)
    draw = ImageDraw.Draw(im)
    for y in range(HEIGHT):
        t = y / HEIGHT
        color = tuple(round(a * (1-t*.8) + b * (t*.8)) for a,b in zip(base,second))
        draw.line((0,y,WIDTH,y),fill=color)
    draw.ellipse((895,90,1035,230),fill=accent)
    for layer in range(3):
        horizon = 388+layer*85
        dark = tuple(round(x*(.65+layer*.08)) for x in second)
        pts=[(0,HEIGHT),(0,horizon)]
        for x in range(0, WIDTH+100, 100):
            offset=(seed >> (x//100+layer*11) % 55) & 31
            pts.append((x,horizon+offset*2-28))
        pts.extend([(WIDTH,HEIGHT)])
        draw.polygon(pts, fill=dark)
    for j in range(9):
        x=seed >> (j*5) % 48 & 1023
        y=(seed >> (j*4+3) % 48) & 255
        draw.ellipse((x,y,x+3,y+3),fill=(230,230,235))
    if direction is not None:
        weather = direction["weather"]
        if weather == "night":
            dim = Image.new("RGBA", im.size, (3, 7, 31, 95))
            im = Image.alpha_composite(im.convert("RGBA"), dim).convert("RGB")
            draw = ImageDraw.Draw(im)
            # Celestial composition, generated procedurally, not AI imagery.
            draw.ellipse((926,111,1008,193),fill=(249,240,191))
            for j in range(17):
                sx = 40 + (seed >> ((j*3) % 49) & 1087)
                sy = 122 + (seed >> ((j*5+7) % 48) & 200)
                draw.ellipse((sx,sy,sx+3,sy+3),fill=(247,246,219))
        elif weather in ("rain", "storm", "cloudy"):
            haze = Image.new("RGBA", im.size,
                             (37, 47, 88, 65 if weather in ("rain", "storm") else 32))
            im = Image.alpha_composite(im.convert("RGBA"),haze).convert("RGB")
            draw = ImageDraw.Draw(im)
            for x,y in ((160,125),(520,140),(810,93),(1080,177)):
                draw.ellipse((x-100,y-28,x+112,y+43),fill=(154,173,201))
                draw.ellipse((x-58,y-59,x+66,y+38),fill=(167,184,210))
        elif weather == "wind":
            for k in range(14):
                x=50+((seed >> (k*3) % 48) & 1000)
                y=210+(k*31)%350
                draw.arc((x,y,x+85,y+27),180,345,
                         fill=(196,224,222),width=3)
    draw.ellipse((106,578,548,644),fill=(27,34,62))
    draw.rounded_rectangle((666,245,1220,607),radius=30,
                           fill=(18,29,55),outline=accent,width=3)
    draw.rounded_rectangle((43,36,624,106),radius=18,fill=(18,29,55))
    title=topic.strip()
    while draw.textbbox((0,0),title,font=font(29))[2] > 540 and len(title)>8:
        title=title[:-2]
    if len(title)<len(topic.strip()):
        title=title.rstrip()+"…"
    draw.text((65,54),title,fill=(254,251,238),font=font(29))
    draw.text((704,285),f"SCÈNE {scene_index:02d} / {scene_count:02d}",
              fill=accent,font=font(26))
    draw.line((702,328,1175,328),fill=accent,width=3)
    for i,line in enumerate(_wrap(draw,narration,462,6)):
        draw.text((702,351+i*39),line,fill=(247,250,255),font=font(30))
    draw.text((46,662),"APERÇU • PERSONNAGE ORIGINAL",
              fill=(242,242,250),font=font(19))
    im.save(path,"PNG",optimize=True)


def _wing(path: Path, *, right: bool):
    im=Image.new("RGBA",(164,212))
    d=ImageDraw.Draw(im)
    if right:
        d.ellipse((26,35,154,190),fill=DARK_PURPLE,outline=OUTLINE,width=5)
        d.ellipse((49,61,130,167),fill=PURPLE)
        for offset in range(3):
            d.arc((45+offset*20,100,100+offset*17,190),-75,125,fill=LAVENDER,width=4)
    else:
        d.ellipse((10,35,138,190),fill=DARK_PURPLE,outline=OUTLINE,width=5)
        d.ellipse((35,61,115,167),fill=PURPLE)
        for offset in range(3):
            d.arc((19+offset*20,100,80+offset*17,190),-75,125,fill=LAVENDER,width=4)
    im.save(path,"PNG")


def _body(path: Path, *, blink: bool, emotion: str = "neutral"):
    im=Image.new("RGBA",(322,430))
    d=ImageDraw.Draw(im)
    # Feet, horns, torso and a friendly, unmistakably original owl face.
    for x in (95,220):
        d.line((x,342,x,401),fill=GOLD,width=13)
        d.line((x-27,399,x+28,399),fill=GOLD,width=12)
    d.polygon([(51,143),(26,15),(132,84)],fill=DARK_PURPLE)
    d.polygon([(186,83),(289,14),(274,140)],fill=DARK_PURPLE)
    d.ellipse((44,84,278,371),fill=PURPLE,outline=OUTLINE,width=6)
    d.ellipse((86,243,232,362),fill=LAVENDER)
    for dx in (106,219):
        d.ellipse((dx-57,116,dx+57,225),fill=LAVENDER,outline=OUTLINE,width=3)
        if blink:
            d.arc((dx-35,162,dx+35,190),0,180,fill=INK,width=8)
        else:
            d.ellipse((dx-29,139,dx+29,197),fill=INK)
            d.ellipse((dx-20,146,dx-9,160),fill=(255,255,255,255))
        d.ellipse((dx-62,111,dx+62,231),outline=TEAL,width=9)
    d.line((163,165,163,189),fill=TEAL,width=8)
    d.polygon([(143,229),(180,229),(162,255)],fill=GOLD)
    # Expression belongs to the authored narration beat, not to a random timer.
    if emotion == "surprised":
        d.ellipse((151,265,174,296),fill=OUTLINE)
    elif emotion == "worried":
        d.arc((133,271,192,305),180,360,fill=OUTLINE,width=5)
    elif emotion == "happy":
        d.arc((126,259,196,301),0,180,fill=OUTLINE,width=7)
    elif emotion == "curious":
        d.arc((140,258,191,285),0,180,fill=OUTLINE,width=4)
    else:
        d.arc((130,256,195,290),0,180,fill=OUTLINE,width=5)
    d.arc((78,292,250,343),0,180,fill=GOLD,width=17)
    d.polygon([(234,306),(275,357),(254,376),(207,320)],fill=GOLD)
    im.save(path,"PNG")


def _weather_overlay(path: Path, *, seed: str, weather: str) -> None:
    """A transparent twice-height texture that scrolls over moving foreground."""
    from random import Random
    rand = Random(int.from_bytes(hashlib.sha256(seed.encode()).digest()[:8], "big"))
    image = Image.new("RGBA", (1280, 1440), (0,0,0,0))
    draw = ImageDraw.Draw(image)
    if weather in {"rain", "storm"}:
        for i in range(650 if weather == "storm" else 450):
            x = rand.randrange(1280)
            y = rand.randrange(1440)
            draw.line((x,y,x-8,y+27),fill=(194,222,255,105),width=2)
    elif weather == "wind":
        for i in range(75):
            x = rand.randrange(1280)
            y = rand.randrange(1440)
            draw.arc((x,y,x+70,y+22),start=175,end=355,
                     fill=(210,235,205,120),width=3)
    else:
        for i in range(12):
            x = rand.randrange(1280)
            y = rand.randrange(1440)
            draw.ellipse((x,y,x+125,y+31),fill=(225,233,245,51))
    image.save(path,"PNG")


def render_layers(folder: Path, *, topic: str, narration: str,
                  scene_index: int, scene_count: int, style: str,
                  direction: dict | None = None) -> dict[str, Path]:
    if style not in PALETTES:
        raise ValueError("Unsupported visual style")
    if direction is not None:
        direction = validate_direction(direction)
    folder.mkdir(parents=True,exist_ok=True)
    outputs={k:folder/(k+".png") for k in
             ("background","left","right","body","blink","effects")}
    _bg(outputs["background"],topic=topic,narration=narration,
        scene_index=scene_index,scene_count=scene_count,style=style,
        direction=direction)
    _wing(outputs["left"],right=False)
    _wing(outputs["right"],right=True)
    _body(outputs["body"],blink=False,
          emotion=direction["emotion"] if direction else "neutral")
    _body(outputs["blink"],blink=True,
          emotion=direction["emotion"] if direction else "neutral")
    return outputs


def render_motion_clip(*, topic: str, narration: str, scene_index: int,
                       scene_count: int, style: str,
                       duration: float, width: int, height: int,
                       fps: int, destination: Path,
                       direction: dict | None = None) -> None:
    if not 0 < duration <= 3600 or fps not in (24,30):
        raise ValueError("Unsupported animation parameters")
    if (width,height) not in ((1280,720),(1920,1080)):
        raise ValueError("Unsupported rendering dimensions")
    if direction is not None:
        direction = validate_direction(direction)
    from .production import _run
    with tempfile.TemporaryDirectory(prefix="automate-ytb-rig-") as folder:
        layers=render_layers(Path(folder),topic=topic,narration=narration,
                             scene_index=scene_index,scene_count=scene_count,
                             style=style,direction=direction)
        # Wings move independently while body bobs; a separate blink sprite
        # briefly overlays the open-eyed face every few seconds.
        action = direction["action"] if direction else "idle"
        wing_amplitude = {"fly": 64, "walk": 23, "talk": 12,
                          "surprise": 45, "rest": 3, "idle": 29}[action]
        wing_speed = 6.0 if action == "fly" else (1.3 if action == "rest" else 4.2)
        bob_amplitude = 25 if action == "fly" else (5 if action == "rest" else 8)
        f=(
          "[0:v][1:v]overlay=x='144+7*sin(t*1.7)':"
          f"y='348+{wing_amplitude}*sin(t*{wing_speed})':eval=frame:format=auto[a];"
          "[a][2:v]overlay=x='420-7*sin(t*1.7)':"
          f"y='350-{wing_amplitude}*sin(t*{wing_speed})':eval=frame:format=auto[b];"
          "[b][3:v]overlay=x='204+7*sin(t*1.3)':"
          f"y='186+{bob_amplitude}*sin(t*2.6)':eval=frame:format=auto[c];"
          "[c][4:v]overlay=x='204+7*sin(t*1.3)':"
          f"y='186+{bob_amplitude}*sin(t*2.6)':"
          "enable='lt(mod(t,4.0),0.13)':eval=frame:format=auto"
        )
        final_label = "d"
        if direction and direction["weather"] in {"rain", "storm", "wind", "cloudy"}:
            _weather_overlay(layers["effects"], seed=f"{topic}|{narration}|{scene_index}",
                             weather=direction["weather"])
            speed = 240 if direction["weather"] in {"rain", "storm"} else 35
            f += f"[d];[d][5:v]overlay=x=0:y='-720+mod(t*{speed},720)':eval=frame:format=auto[e]"
            final_label = "e"
        else:
            f += "[d]"
        crop = {"wide": (1280,720), "medium": (1248,702),
                "closeup": (1216,684), "macro": (1184,666),
                "low": (1248,702), "shoulder": (1224,689)}
        shot = direction["shot"] if direction else "wide"
        cw,ch = crop[shot]
        f += f";[{final_label}]crop={cw}:{ch}:{(1280-cw)//2}:{(720-ch)//2},"
        f += f"scale={width}:{height}:flags=lanczos,format=yuv420p[out]"
        args=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y"]
        keys = ["background","left","right","body","blink"]
        if direction and direction["weather"] in {"rain", "storm", "wind", "cloudy"}:
            keys.append("effects")
        for key in keys:
            args+=["-loop","1","-framerate",str(fps),"-i",str(layers[key])]
        args+=["-filter_complex",f,"-map","[out]","-frames:v",
               str(max(1,round(duration*fps))),"-r",str(fps),
               "-c:v","libx264","-preset","veryfast","-crf","21",
               "-pix_fmt","yuv420p","-an",str(destination)]
        _run(args)


def render_character_poster(*, topic: str, narration: str,
                            scene_index: int, scene_count: int,
                            style: str, destination: Path,
                            direction: dict | None = None) -> None:
    """The approved still is a true rest-pose composite of the moving rig.

    This makes the asset checksum representative of the animation's authored
    visual identity instead of approving a visually unrelated illustration.
    """
    with tempfile.TemporaryDirectory(prefix="automate-ytb-owl-poster-") as folder:
        layers = render_layers(
            Path(folder), topic=topic, narration=narration,
            scene_index=scene_index, scene_count=scene_count, style=style,
            direction=direction)
        with Image.open(layers["background"]) as b:
            composite = b.convert("RGBA")
        for name, position in (("left", (144,348)), ("right", (420,350)),
                               ("body", (204,186))):
            with Image.open(layers[name]) as sprite:
                composite.alpha_composite(sprite.convert("RGBA"),position)
        destination.parent.mkdir(parents=True, exist_ok=True)
        composite.convert("RGB").save(destination, format="PNG", optimize=True)


def art_brief_sha256(*, topic: str, narration: str,
                     character: str, style: str, scene_id: str,
                     direction: dict | None = None) -> str:
    """Bind original visuals to the immutable creative inputs of a scene."""
    payload = json.dumps(
        [topic, narration, character, style, scene_id] +
        ([validate_direction(direction)] if direction is not None else []),
        ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
