"""Original astronomy motion-infographic scenes, rendered offline at true frame rate.

Stylized planetary illustrations, not geospatial data or verified physics.
The user's authored narration controls labels and shot selection. Every
asset is generated locally. No third-party image, model or music is copied.
"""
from __future__ import annotations

import hashlib
from functools import lru_cache
import json
import math
from pathlib import Path
import random
import re
import shutil
import subprocess
import unicodedata
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SCIENCE_VERSION = "science-motion-v4-portrait-shorts"
SIZE = (1280, 720)
FULL_HD = (1920, 1080)
GOLD = (251, 200, 119)
CYAN = (113, 219, 244)


def _font(size: int, bold: bool = False):
    paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    if bold:
        paths.reverse()
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


class _ScaledDraw:
    """Draw original 1280x720 composition directly at target pixel density.

    This is a coordinate adapter, NOT an enlarged bitmap. Paths, line
    thicknesses, rounded corners and FreeType glyphs are rasterized on the
    actual 1920x1080 output for the full-HD export.
    """
    def __init__(self, picture: Image.Image, factor: float):
        self._draw = ImageDraw.Draw(picture, "RGBA")
        self.factor = factor

    def _coord(self, point):
        if point and isinstance(point[0], (tuple, list)):
            return [self._coord(x) for x in point]
        return tuple(round(float(x) * self.factor) for x in point)

    def _font(self, font):
        if font is not None and hasattr(font, "font_variant"):
            return font.font_variant(size=max(1, round(font.size * self.factor)))
        return font

    def ellipse(self, xy, **kwargs):
        self._draw.ellipse(self._coord(xy), **self._scaled_width(kwargs))

    def rectangle(self, xy, **kwargs):
        self._draw.rectangle(self._coord(xy), **self._scaled_width(kwargs))

    def polygon(self, xy, **kwargs):
        self._draw.polygon(self._coord(xy), **self._scaled_width(kwargs))

    def line(self, xy, **kwargs):
        self._draw.line(self._coord(xy), **self._scaled_width(kwargs))

    def arc(self, xy, start, end, **kwargs):
        self._draw.arc(self._coord(xy), start, end,
                       **self._scaled_width(kwargs))

    def rounded_rectangle(self, xy, radius, **kwargs):
        self._draw.rounded_rectangle(
            self._coord(xy), radius=round(radius * self.factor),
            **self._scaled_width(kwargs))

    def text(self, xy, text, *, font=None, **kwargs):
        self._draw.text(self._coord(xy), text, font=self._font(font), **kwargs)

    def textbbox(self, xy, text, *, font=None, **kwargs):
        box = self._draw.textbbox(
            self._coord(xy), text, font=self._font(font), **kwargs)
        return tuple(value / self.factor for value in box)

    def _scaled_width(self, kwargs):
        result = dict(kwargs)
        if "width" in result:
            result["width"] = max(1, round(result["width"] * self.factor))
        return result


def scene_mode(narration: str) -> str:
    if not isinstance(narration, str):
        raise ValueError("Narration must be original authored text")
    folded = unicodedata.normalize("NFKD", narration.casefold())
    s = "".join(ch for ch in folded if not unicodedata.combining(ch))
    if any(w in s for w in ("ocean", "vague", "maree", "wave", "sea ", "mer ")):
        return "ocean"
    if any(w in s for w in ("vent", "wind", "air ", "atmospher", "tempete")):
        return "atmosphere"
    if any(w in s for w in ("jour", "nuit", "night", "daylight", "darkness")):
        return "daylight"
    return "orbital"


def art_brief_sha256(*, topic: str, narration: str, scene_id: str,
                     character: str, style: str,
                     direction: dict | None = None,
                     held_prop: str | None = None,
                     landscape: str | None = None) -> str:
    if style != "science":
        raise ValueError("Not an original science infographic")
    data = [SCIENCE_VERSION, topic, narration, scene_id, character,
            direction, held_prop, landscape]
    return hashlib.sha256(json.dumps(
        data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _background(seed: int, size: tuple[int, int] = SIZE) -> Image.Image:
    """Create sky, stars and atmosphere directly at target resolution."""
    if size not in (SIZE, FULL_HD):
        raise ValueError("Unsupported original science canvas resolution")
    rng = random.Random(seed)
    width, height = size
    scale = width / SIZE[0]
    im = Image.new("RGBA", size, (7, 22, 43, 255))
    draw = ImageDraw.Draw(im)
    for y in range(height):
        p = y / height
        draw.line((0, y, width - 1, y),
                  fill=(7 + int(5*p), 22 + int(9*p),
                        43 + int(12*p), 255))
    for _ in range(round(225 * scale * scale)):
        x, y = rng.randrange(width), rng.randrange(
            round(30 * scale), round(655 * scale))
        n = rng.choice((1, 1, 1, 2))
        n = max(1, round(n * scale))
        b = rng.randrange(90, 190)
        draw.ellipse((x, y, x+n, y+n),
                     fill=(b//2, b, min(255, b+40), 255))
    halo = Image.new("RGBA", size)
    _ScaledDraw(halo, scale).ellipse(
        (200, 15, 1000, 650), fill=(28, 133, 195, 42))
    return Image.alpha_composite(
        im, halo.filter(ImageFilter.GaussianBlur(round(105 * scale))))

@lru_cache(maxsize=1)
def _planet_texture() -> Image.Image:
    """Immutable original continent atlas, shared by every rotating pose."""
    texture = Image.new("RGB", (768,384), (23,123,186))
    draw = ImageDraw.Draw(texture)
    continents = [
        [(-168,70),(-143,72),(-132,61),(-124,50),(-117,44),(-107,36),
         (-97,25),(-85,25),(-81,12),(-91,10),(-107,19),(-124,32),
         (-132,49),(-157,59)],
        [(-81,12),(-69,10),(-59,5),(-51,-3),(-48,-11),(-41,-19),
         (-48,-28),(-55,-35),(-68,-54),(-76,-46),(-75,-30),(-78,-16)],
        [(-12,36),(0,44),(7,54),(20,59),(33,57),(45,50),(70,56),
         (89,55),(106,49),(120,53),(148,38),(137,27),(122,23),
         (116,10),(101,0),(96,12),(76,8),(57,30),(45,30),
         (36,39),(19,42),(9,38)],
        [(-16,34),(0,37),(16,31),(32,20),(39,6),(34,-11),
         (26,-17),(20,-33),(14,-35),(8,-29),(0,-7),(-14,9)],
        [(112,-11),(127,-14),(140,-16),(153,-27),(150,-39),
         (136,-42),(116,-33)],
        [(-53,83),(-40,81),(-38,67),(-49,59),(-61,63),(-61,76)]]
    for i, shape in enumerate(continents):
        points = [(round((lon+180)/360*767),round((90-lat)/180*383))
                  for lon,lat in shape]
        draw.polygon(points, fill=(67+i%3*7,153+i%4*5,99+i%3*10))
    return texture


@lru_cache(maxsize=4)
def _planet_halo(size: int) -> Image.Image:
    """Resolution-specific soft glow; never mutate this cached template."""
    scale = size / 408
    margin = round(28 * scale)
    halo = Image.new("RGBA", (size + 2*margin, size + 2*margin))
    ImageDraw.Draw(halo).ellipse(
        (round(12*scale), round(12*scale),
         size + round(44*scale), size + round(44*scale)),
        fill=(46, 194, 239, 139))
    return halo.filter(ImageFilter.GaussianBlur(round(21*scale)))


def _planet(size: int = 408, yaw: float = 0.) -> Image.Image:
    """Approximate original sphere, sharing only yaw-independent atlas/glow."""
    lookup = _planet_texture().load()
    scale = size / 408
    margin = round(28 * scale)
    globe = _planet_halo(size).copy()
    surface=Image.new("RGBA",(size,size))
    pixels=surface.load()
    radius=size/2
    for y in range(size):
        ny=(radius-y)/radius
        # Latitude, sampling row, polar ice and latitudinal cloud phase do
        # not depend on x or planetary yaw. Compute each only once per row
        # rather than once for every pixel of native 680px portrait globes.
        lat=math.asin(max(-1,min(1,ny)))
        v=max(0,min(383,int((.5-lat/math.pi)*383)))
        ice=.30 if abs(lat)>1.3 else 0
        cloud_lat=math.sin(lat*6)*1.7
        for x in range(size):
            nx=(x-radius)/radius
            dist=nx*nx+ny*ny
            if dist>=.994:
                continue
            z=math.sqrt(1-dist)
            lon=math.atan2(nx,z)+yaw
            u=int(((lon/math.tau+.5)%1)*767)
            red,green,blue=lookup[u,v]
            light=max(.10,min(1.13,.14+.83*z-.55*nx+.18*ny))
            edge=(1-z)**5
            cloud=.12 if (math.sin(13*lon+cloud_lat)
                         +math.sin(9*lat+lon*3))>1.6 else 0
            pixels[x,y]=(min(255,int(red*light+(cloud+ice)*110+edge*22)),
                         min(255,int(green*light+(cloud+ice)*115+edge*48)),
                         min(255,int(blue*light+(cloud+ice)*120+edge*80)),
                         255)
    globe.alpha_composite(surface, (margin, margin))
    return globe


def _badge(draw: ImageDraw.ImageDraw, text: str) -> None:
    draw.rounded_rectangle((63,58,416,104),radius=19,
                           fill=(4,14,30,235))
    draw.text((83,70),text,font=_font(21,True),fill=GOLD)


def _caption(draw: ImageDraw.ImageDraw, text: str) -> None:
    """On-image editorial excerpt; full original captions remain SRT/VTT."""
    words=text.split()
    if not words:
        return
    f=_font(23)
    lines, line = [], ""
    for word in words:
        trial=(line+" "+word).strip()
        if line and draw.textbbox((0,0),trial,font=f)[2]>900:
            lines.append(line)
            line=word
        else:
            line=trial
    if line:
        lines.append(line)
    if len(lines)>2:
        lines=lines[:2]
        while draw.textbbox((0,0),lines[-1]+"…",font=f)[2]>880:
            lines[-1]=lines[-1][:-1]
        lines[-1]+="…"
    width=max(draw.textbbox((0,0),s,font=f)[2] for s in lines)+64
    height=34*len(lines)+24
    x=(1280-width)//2
    y=677-height
    draw.rounded_rectangle((x,y,x+width,y+height),
                           radius=14,fill=(3,12,27,236))
    for i,line in enumerate(lines):
        tw=draw.textbbox((0,0),line,font=f)[2]
        draw.text((640-tw//2,y+9+i*34),line,font=f,
                  fill=(237,247,255))


class ScienceScene:
    """Original motion graphics for an authored science storyboard beat."""
    def __init__(self, *, topic: str, narration: str, scene_index: int,
                 size: tuple[int, int] = SIZE):
        if not isinstance(topic,str) or not topic.strip() or len(topic)>180:
            raise ValueError("Science scene needs an authored topic")
        if not isinstance(narration,str) or not narration.strip() or len(narration)>9000:
            raise ValueError("Science scene needs authored narration")
        folded = unicodedata.normalize("NFKD",topic.casefold())
        folded = "".join(ch for ch in folded if not unicodedata.combining(ch))
        if not re.search(r"\b(earth|terre|oceans?|oceanique)\b", folded):
            raise ValueError(
                "Science V1 supports Earth/ocean topics only; choose another "
                "visual style for unrelated subjects instead of showing a false planet")
        if type(scene_index) is not int or not 1<=scene_index<=1200:
            raise ValueError("Invalid original scene number")
        if size not in (SIZE, FULL_HD):
            raise ValueError("Unsupported original science canvas resolution")
        self.size = size
        self.scale = size[0] / SIZE[0]
        self.topic, self.narration = topic, narration
        self.mode=scene_mode(narration)
        self.scene_index=scene_index
        self.english=bool(re.search(
            r"\b(the|would|what|earth|stopped|could|still|moving|because)\b",
            narration,flags=re.IGNORECASE))
        # Never insert external/unsourced numbers: only display quantities
        # explicitly authored in the narration itself.
        self.measurement=re.search(
            r"\b(\d{1,3}(?:[ ,]\d{3})*|\d{1,4})\s*(km/h|mph|m/s)\b",
            narration,flags=re.IGNORECASE)
        seed=int.from_bytes(hashlib.sha256(
            f"{topic}|{scene_index}".encode()).digest()[:8],"big")
        self.base=_background(seed, size=self.size)
        # Cache only the globe poses actually used in this shot. The previous
        # implementation precomputed 12 costly images even in ocean scenes
        # and then froze the globe when t exceeded 4.8 seconds.
        self._globes: dict[int, Image.Image] = {}
        self.city=random.Random(seed+29)

    def _globe_at(self, t: float) -> Image.Image:
        """Unbounded scene-time rotation with a small deterministic LRU cache."""
        index = int(t * 2.5)
        if index not in self._globes:
            if len(self._globes) >= 8:
                del self._globes[next(iter(self._globes))]
            self._globes[index] = _planet(
                size=round(408 * self.scale),
                yaw=(0.027 * index) % math.tau)
        return self._globes[index]

    def frame(self, t: float, duration: float) -> Image.Image:
        if not 0<=t<=duration<=3600:
            raise ValueError("Unsafe science animation clock")
        img=self.base.copy()
        d=_ScaledDraw(img, self.scale)
        fraction=t/max(.01,duration)
        travel=fraction*fraction*(3-2*fraction)
        cx=585+int(12*math.sin(t*.42))+int(30*(travel-.5))
        cy=350+int(6*math.sin(t*.62))
        if self.mode=="orbital":
            globe=self._globe_at(t)
            img.alpha_composite(
                globe, (round((cx-230)*self.scale),
                        round((cy-230)*self.scale)))
            d=_ScaledDraw(img, self.scale)
            for rad in (229,249):
                angle=int(t*18)
                d.arc((cx-rad,cy-rad,cx+rad,cy+rad),
                      60+angle,208+angle,fill=GOLD+(163,),width=2)
            for i in range(6):
                a=t*.40+i*math.tau/6
                px=cx+int(251*math.cos(a))
                py=cy+int(251*math.sin(a))
                d.ellipse((px-3,py-3,px+3,py+3),fill=GOLD+(215,))
            _badge(d,"PLANETARY MOTION" if self.english
                   else "MOUVEMENT PLANÉTAIRE")
            if self.measurement is not None:
                amount, units=self.measurement.groups()
                d.rounded_rectangle((914,263,1203,384),19,
                                    fill=(3,15,32,230))
                d.text((944,279),amount,font=_font(48,True),
                       fill=GOLD)
                d.text((946,346),units,font=_font(20),
                       fill=(176,221,231))
        elif self.mode=="daylight":
            globe=self._globe_at(t)
            img.alpha_composite(
                globe, (round(187*self.scale), round(127*self.scale)))
            dark=Image.alpha_composite(
                globe,Image.new("RGBA",globe.size,(3,7,30,112)))
            dark.putalpha(globe.getchannel("A"))
            img.alpha_composite(
                dark, (round(750*self.scale), round(127*self.scale)))
            d=_ScaledDraw(img, self.scale)
            for x,label,col in ((206,"ZONE ÉCLAIRÉE",GOLD),
                                (770,"ZONE SOMBRE",CYAN)):
                d.rounded_rectangle((x,76,x+252,112),12,fill=(4,16,33,235))
                if self.english:
                    label="DAYLIGHT" if x==206 else "DARKNESS"
                d.text((x+19,84),label,font=_font(18,True),fill=col)
            # Phase labels provide the shot title; a second top-left
            # badge here would overlap the illuminated-side label.
        else:
            d.rectangle((0,417,1280,605),fill=(10,32,55,242))
            rng=random.Random(self.scene_index*131)
            for i in range(66):
                x=i*22-16
                h=rng.randrange(36,169)
                d.rectangle((x,418-h,x+17,420),fill=(15,47,72,244))
                for j in range(3):
                    yy=418-h+17+j*27
                    if yy<411:
                        d.line((x+5,yy,x+9,yy),fill=(100,172,194,141),width=2)
            if self.mode=="atmosphere":
                _badge(d,"AIR IN MOTION" if self.english
                       else "CIRCULATION DE L’AIR")
                for i in range(36):
                    px=(i*43+t*(55+i%5*14))%1370-65
                    py=178+(i*41)%334
                    d.line((px,py,px+42+i%32,py-5),
                           fill=(128,220,242,135),width=2)
                    d.ellipse((px+40,py-5,px+44,py-1),
                              fill=(191,238,249,146))
            else:
                _badge(d,"OCEAN DYNAMICS" if self.english
                       else "DYNAMIQUE DES OCÉANS")
                wave_specs=[
                    ((25,125,168,195),29,.62,475),
                    ((45,170,204,210),36,.77,522),
                    ((14,107,157,242),22,.90,565)]
                for i,(color,amp,speed,base) in enumerate(wave_specs):
                    points=[(0,720)]
                    for x in range(0,1281,8):
                        y=base+amp*math.sin(x/169+speed*t+i*.7)
                        points.append((x,round(y)))
                    points.append((1280,720))
                    d.polygon(points,fill=color)
                    d.line(points[1:-1],fill=(156,242,246,129),width=2)
        d=_ScaledDraw(img, self.scale)
        for i in range(11):
            x=int((i*109+t*(i%3+1)*4)%1260)+8
            y=int((i*57+t*(i%4+1)*2)%600)+15
            d.ellipse((x,y,x+2,y+2),fill=(140,214,238,78))
        _caption(d,self.narration)
        return img.convert("RGB")


def render_character_poster(*, topic: str, narration: str,
                            scene_index: int, scene_count: int,
                            style: str, destination: Path,
                            direction: dict | None = None,
                            held_prop: str | None = None,
                            landscape: str | None = None) -> None:
    if style!="science":
        raise ValueError("Unsupported science visual style")
    from .science_rainbow import supports_topic as rainbow_topic
    if rainbow_topic(topic):
        # The approval poster is a separate 16:9 crop of ORIGINAL 9:16
        # artwork. Only the delivered Shorts MP4 is native full portrait.
        # Never substitute the old Earth globe for atmospheric optics.
        from .science_portrait import PortraitScienceScene
        shot = PortraitScienceScene(
            topic=topic, narration=narration, scene_index=scene_index)
        original = shot.frame(.2, 1.0)
        poster = original.crop((0, 690, 1080, 1298)).resize(
            (1280, 720), Image.Resampling.LANCZOS)
        destination.parent.mkdir(parents=True, exist_ok=True)
        poster.save(destination, format="PNG", optimize=True)
        return
    shot=ScienceScene(topic=topic,narration=narration,scene_index=scene_index)
    destination.parent.mkdir(parents=True,exist_ok=True)
    shot.frame(.2,1.0).save(destination,format="PNG",optimize=True)


def render_motion_clip(*, topic: str, narration: str, scene_index: int,
                       scene_count: int, style: str, duration: float,
                       width: int, height: int, fps: int, destination: Path,
                       direction: dict | None = None,
                       caption_segments: list[dict] | None = None,
                       scene_start_ms: int = 0, **_unused) -> None:
    if style!="science" or (width,height) not in ((1280,720),(1920,1080),(1080,1920)):
        raise ValueError("Unsupported science style or resolution")
    if fps not in (24,30) or not .1<=duration<=180:
        raise ValueError("Unsupported science duration or FPS")
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg required to render science animation")
    if (width, height) == (1080, 1920):
        from .science_portrait import PortraitScienceScene
        shot = PortraitScienceScene(
            topic=topic, narration=narration, scene_index=scene_index,
            caption_segments=caption_segments, scene_start_ms=scene_start_ms)
    else:
        shot = ScienceScene(topic=topic,narration=narration,scene_index=scene_index,
                            size=(width,height))
    destination.parent.mkdir(parents=True,exist_ok=True)
    frames=max(1,round(duration*fps))
    cmd=["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
         "-f","rawvideo","-pixel_format","rgb24",
         "-video_size",f"{width}x{height}","-framerate",str(fps),"-i","pipe:0",
         "-vf","format=yuv420p",
         "-frames:v",str(frames),"-c:v","libx264","-preset","veryfast",
         "-crf","19","-an",str(destination)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        assert proc.stdin is not None
        for n in range(frames):
            proc.stdin.write(shot.frame(n/fps,duration).tobytes())
        proc.stdin.close()
        diagnostics=proc.stderr.read() if proc.stderr else b""
        status=proc.wait(timeout=180)
        if status:
            raise RuntimeError("Science FFmpeg render failed: "+
                               diagnostics[-1400:].decode(errors="replace"))
    except BaseException:
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        destination.unlink(missing_ok=True)
        raise
