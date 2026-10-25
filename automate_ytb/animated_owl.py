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
from random import Random
import tempfile

from PIL import Image, ImageDraw, ImageFont

from .studio import PALETTES, WIDTH, HEIGHT, font
from .director import validate_direction


RIG_VERSION = "owl-rig-v4-ambient-particles"
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
    # Full-screen storybook landscape. Narration belongs in the exported
    # SRT/VTT, not a large opaque paragraph covering half the scene.
    # Everything remains original, deterministic and royalty-free.
    rand = Random(seed)
    weather = direction["weather"] if direction else "day"
    night = weather in {"night", "storm"}
    trunk = (29, 44, 66) if night else (39, 65, 74)
    foliage = [(29, 87, 101), (35, 116, 119), (49, 133, 125)] if night else [
        (32, 98, 106), (40, 122, 106), (64, 145, 103)
    ]
    # Subtle mountains, atmospheric haze and landmarks add depth to the
    # empty right-hand space, which previously displayed a large text card.
    ridge = [(570, 575), (700, 460), (778, 518), (870, 413),
             (996, 525), (1144, 444), (1280, 527), (1280, 720)]
    draw.polygon(ridge, fill=(49, 79, 104) if night else (79, 128, 132))
    draw.line(ridge[:7], fill=(128, 177, 185), width=3)
    for x, bottom, radius in ((715, 630, 62), (863, 646, 75),
                              (1067, 668, 94), (1235, 640, 78)):
        top = bottom - (180 + rand.randint(10, 65))
        draw.line((x, bottom, x, top + 30), fill=trunk, width=18)
        draw.line((x, top + 96, x - radius * .5, top + 55),
                  fill=trunk, width=8)
        draw.line((x, top + 140, x + radius * .5, top + 78),
                  fill=trunk, width=7)
        for ox, oy, size, tone in (
            (-radius * .50, 55, radius * .72, foliage[0]),
            (radius * .39, 66, radius * .74, foliage[1]),
            (0, 25, radius, foliage[2]),
            (0, -10, radius * .68, foliage[1]),
        ):
            draw.ellipse((x + ox - size, top + oy - size,
                          x + ox + size, top + oy + size),
                         fill=tone)
        for _ in range(5):
            a = x + rand.randrange(-radius, radius + 1)
            b = top + rand.randrange(0, radius + 28)
            draw.ellipse((a, b, a + 4, b + 6), fill=(145, 192, 142))
    # Patches of grasses and firefly-like highlights frame the character.
    for _ in range(85):
        x = rand.randrange(20, 1280)
        y = rand.randrange(625, 718)
        blade = rand.randrange(8, 25)
        draw.line((x, y, x - 4, y - blade),
                  fill=(67, 159, 134), width=2)
        draw.line((x, y, x + 5, y - blade * .7),
                  fill=(107, 178, 134), width=2)
    for _ in range(32):
        x = rand.randrange(50, 1260)
        y = rand.randrange(350, 620)
        radius = rand.choice((2, 3, 4))
        color = (232, 229, 162) if night else (212, 238, 192)
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color)
    # Position the actor with a believable ground-contact shadow.
    draw.ellipse((106, 584, 548, 647), fill=(25, 34, 58))
    draw.ellipse((132, 597, 514, 635), fill=(45, 63, 78))

    title = topic.strip()
    while draw.textbbox((0, 0), title, font=font(27))[2] > 550 and len(title) > 8:
        title = title[:-2]
    if len(title) < len(topic.strip()):
        title = title.rstrip() + "…"
    title_width = draw.textbbox((0, 0), title, font=font(27))[2]
    draw.rounded_rectangle((34, 28, min(640, 74 + title_width), 90),
                           radius=21, fill=(20, 32, 54),
                           outline=(103, 146, 157), width=2)
    draw.text((55, 43), title, fill=(249, 247, 237), font=font(27))
    label = f"{scene_index:02d} / {scene_count:02d}"
    draw.rounded_rectangle((1104, 651, 1256, 696), radius=15,
                           fill=(20, 34, 53), outline=accent, width=2)
    draw.text((1130, 658), label, fill=(247, 246, 237), font=font(21))
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
    elif weather == "night":
        # Foreground fireflies sit below the skyline even while the
        # two-height texture scrolls. The sky and moon stay stable.
        for band in (0, 720):
            for _ in range(46):
                x = rand.randrange(42, 1237)
                y = band + rand.randrange(402, 664)
                radius = rand.choice((3, 4, 5, 7))
                draw.ellipse((x-radius*2, y-radius*2,
                              x+radius*2, y+radius*2),
                             fill=(242, 220, 119, 38))
                draw.ellipse((x-radius, y-radius, x+radius, y+radius),
                             fill=(255, 232, 136, 150))
                draw.ellipse((x-1, y-1, x+1, y+1),
                             fill=(255, 255, 223, 224))
    elif weather == "day":
        # Warm pollen and loose blossoms float past in the foreground.
        # Original local sprites, not downloaded footage or photographs.
        for band in (0, 720):
            for _ in range(58):
                x = rand.randrange(35, 1240)
                y = band + rand.randrange(390, 665)
                radius = rand.choice((2, 3, 4))
                color = rand.choice(((247, 224, 166, 128),
                                     (234, 249, 216, 115),
                                     (255, 202, 205, 109)))
                draw.ellipse((x-radius, y-radius,
                              x+radius, y+radius), fill=color)
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
        if direction and direction["weather"] in {"rain", "storm", "wind", "cloudy", "night", "day"}:
            _weather_overlay(layers["effects"], seed=f"{topic}|{narration}|{scene_index}",
                             weather=direction["weather"])
            speed = {"rain": 240, "storm": 310, "wind": 55,
                     "cloudy": 25, "night": 22, "day": 18}[direction["weather"]]
            f += f"[d];[d][5:v]overlay=x=0:y='-720+mod(t*{speed},720)':eval=frame:format=auto[e]"
            final_label = "e"
        else:
            f += "[d]"
        from .cinematic_camera import framing_filter
        shot = direction["shot"] if direction else "wide"
        camera = framing_filter(
            shot, width=width, height=height, fps=fps,
            scene_index=scene_index)
        f += f";[{final_label}]{camera}[out]"
        args=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y"]
        keys = ["background","left","right","body","blink"]
        if direction and direction["weather"] in {"rain", "storm", "wind", "cloudy", "night", "day"}:
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
        [RIG_VERSION, topic, narration, character, style, scene_id] +
        ([validate_direction(direction)] if direction is not None else []),
        ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
