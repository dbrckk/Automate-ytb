"""Opt-in, free, topic-independent photographic artwork from Wikimedia Commons.

Only explicit CC0 1.0 raster thumbnails are eligible. Metadata is evidence of
a claimed license, not a substitute for human checking the file page. No
publication is authorized. External requests are disabled unless requested.
The stage animates a single accepted photograph without fabricating a subject
mask or pretending that a flat photo is a rigged animal/character.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

VERSION = "commons-cc0-photographic-foreground-rig-v2"
API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = ("AutomateYTB-FreeShorts/0.1 "
              "(https://github.com/dbrckk/Automate-ytb) python-urllib")
MAX_IMAGE_BYTES = 6 * 1024 * 1024
MAX_JSON_BYTES = 240_000
CC0_URL = "https://creativecommons.org/publicdomain/zero/1.0/"


class _StripHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data: str):
        self.parts.append(data)


def _plain(value: str, limit: int = 220):
    if not isinstance(value, str):
        return ""
    parser = _StripHTML()
    parser.feed(value[:limit * 8])
    text = " ".join(unescape("".join(parser.parts)).split())
    return text[:limit]


def _safe_url(url: str, hostname: str, *, prefix: str | None = None):
    if not isinstance(url, str) or len(url) > 2048:
        raise ValueError("Invalid Commons media URL")
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname != hostname
            or parsed.username or parsed.password or parsed.port is not None
            or (prefix and not parsed.path.startswith(prefix))
            or not parsed.path or parsed.fragment):
        raise ValueError("Unsafe Commons redirect/host/path")
    return url


class _NoExternalRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _safe_url(newurl, urllib.parse.urlsplit(req.full_url).hostname)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _read_url(url: str, maximum: int, hostname: str) -> bytes:
    _safe_url(url, hostname)
    opener = urllib.request.build_opener(_NoExternalRedirect)
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT,
                      "Accept": "application/json,image/jpeg,image/png,image/webp"})
    with opener.open(request, timeout=12) as response:
        _safe_url(response.geturl(), hostname)
        if response.headers.get("Content-Length"):
            if int(response.headers["Content-Length"]) > maximum:
                raise ValueError("Commons file exceeds the download limit")
        blob = response.read(maximum + 1)
    if len(blob) > maximum:
        raise ValueError("Commons response exceeds the byte limit")
    return blob


def search_cc0(query: str, *, read_url=None) -> list[dict]:
    """Return only candidate FILES claiming the narrowly allowed CC0 1.0.

    Search ranking is preserved. No external file/content URL is accepted from
    a caller; a source must come from the official fixed Commons API endpoint.
    """
    if (not isinstance(query, str) or not 2 <= len(query.strip()) <= 120
            or any(ord(c) < 32 for c in query)):
        raise ValueError("Search phrase must be 2-120 printable characters")
    request = read_url or _read_url
    params = {
        "action": "query", "generator": "search",
        "gsrsearch": query.strip(), "gsrnamespace": "6", "gsrlimit": "10",
        "prop": "imageinfo", "iiprop": "url|mime|size|extmetadata",
        "iiurlwidth": "960",
        "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist|Credit",
        "format": "json", "formatversion": "2"
    }
    url = API_URL + "?" + urllib.parse.urlencode(params)
    data = json.loads(request(url, MAX_JSON_BYTES, "commons.wikimedia.org"))
    pages = data.get("query", {}).get("pages", [])
    if not isinstance(pages, list):
        return []
    result = []
    for page in sorted(pages, key=lambda x: x.get("index", 9999)):
        if not isinstance(page, dict) or page.get("ns") != 6:
            continue
        image_info = page.get("imageinfo", [])
        if not isinstance(image_info, list) or not image_info:
            continue
        info = image_info[0]
        if info.get("mime") not in ("image/jpeg", "image/png", "image/webp"):
            continue
        metadata = info.get("extmetadata", {})
        if not isinstance(metadata, dict):
            continue
        def metadata_value(name):
            entry=metadata.get(name,{})
            return entry.get("value","") if isinstance(entry,dict) else ""
        license_name=_plain(metadata_value("LicenseShortName"),40)
        license_url=metadata_value("LicenseUrl")
        if license_name.casefold() not in ("cc0","cc0 1.0"):
            continue
        if (not isinstance(license_url,str)
                or not license_url.rstrip("/").casefold() == CC0_URL.rstrip("/").casefold()):
            continue
        # Reduced thumbnails are preferred. Never fetch source originals.
        media_url=info.get("thumburl")
        details=info.get("descriptionurl")
        try:
            _safe_url(media_url,"upload.wikimedia.org",prefix="/wikipedia/commons/")
            _safe_url(details,"commons.wikimedia.org",prefix="/wiki/File:")
        except ValueError:
            continue
        result.append({
            "page":details, "thumbnail":media_url,
            "license":"CC0-1.0", "licenseURL":CC0_URL,
            "title":_plain(page.get("title",""),180),
            "creator":_plain(metadata_value("Artist"),200),
            "credit":_plain(metadata_value("Credit"),200),
        })
    return result


def decode_image(blob: bytes) -> Image.Image:
    if not isinstance(blob,bytes) or len(blob) > MAX_IMAGE_BYTES:
        raise ValueError("Unsafe media bytes")
    try:
        with Image.open(BytesIO(blob)) as source:
            if (source.format not in ("PNG","JPEG","WEBP")
                    or min(source.size) < 128 or max(source.size) > 5000
                    or source.width*source.height > 12_000_000):
                raise ValueError("Unsafe/unsupported Commons dimensions")
            source.load()
            image=source.convert("RGB")
    except (OSError,OverflowError) as exc:
        raise ValueError("Commons returned unreadable raster image") from exc
    return image


@lru_cache(maxsize=6)
def _vignette(size):
    w,h=size
    layer=Image.new("RGBA",size)
    d=ImageDraw.Draw(layer,"RGBA")
    # Edge-weighted film contrast without huge per-frame blurs.
    for i in range(9):
        pad=round(i*w*.022)
        alpha=max(0,round((8-i)*2.6))
        d.rounded_rectangle((pad,pad,w-1-pad,h-1-pad),
                            radius=max(3,round(w*.08)),
                            outline=(3,10,22,alpha),width=max(1,round(w*.02)))
    return layer


@dataclass
class CommonsPhotoScene:
    title: str
    origin: str
    creator: str
    thumbnail: str
    sha256: str
    image: Image.Image
    width: int
    height: int
    subject_mask: Image.Image | None = None

    def __post_init__(self):
        if self.image.mode != "RGB":
            raise ValueError("CC0 stage needs RGB source")
        # Pre-render once; animation only crops a time-varying camera.
        self.zoomed=ImageOps.fit(
            self.image,(round(self.width*1.26),round(self.height*1.26)),
            method=Image.Resampling.LANCZOS,centering=(.5,.5))
        self.zoomed=ImageEnhance.Contrast(self.zoomed).enhance(1.10)
        self.zoomed=ImageEnhance.Color(self.zoomed).enhance(1.11)
        self.vignette=_vignette((self.width,self.height))
        self.foreground=None
        self.soft_background=None
        if self.subject_mask is not None:
            if (self.subject_mask.mode != "L"
                    or self.subject_mask.size != self.image.size):
                raise ValueError("Subject silhouette must match original raster")
            # Align the foreground with the same single prefit camera image.
            mask=ImageOps.fit(self.subject_mask,self.zoomed.size,
                              method=Image.Resampling.LANCZOS,
                              centering=(.5,.5))
            mask=mask.filter(ImageFilter.GaussianBlur(
                radius=max(1,self.width//340)))
            foreground=self.zoomed.copy().convert("RGBA")
            foreground.putalpha(mask)
            self.foreground=foreground
            self.soft_background=self.zoomed.filter(
                ImageFilter.GaussianBlur(
                    radius=max(3,round(self.width*.014))))

    def render(self, frame:int, first:int, last:int)->Image.Image:
        if (type(frame) is not int or type(first) is not int or
                type(last) is not int or not first<=frame<last):
            raise ValueError("Camera frame outside its authored beat")
        phase=(frame-first)/max(1,last-first)
        ease=phase*phase*(3-2*phase)
        # Diagonal camera dolly (not random jitter) + restrained depth cue.
        spare_x=self.zoomed.width-self.width
        spare_y=self.zoomed.height-self.height
        x=round(spare_x*(.24+.53*ease))
        y=round(spare_y*(.65-.36*ease))
        if self.foreground is not None:
            picture=self.soft_background.crop((
                x,y,x+self.width,y+self.height)).convert("RGBA")
            # Original alpha-matted subject has its own slower lateral
            # parallax. No new object or anatomical details are fabricated.
            dx=round(self.width*.033*math.sin(math.pi*ease))
            dy=round(self.height*.014*math.sin(math.pi*ease))
            sprite=self.foreground.crop((
                x-dx,y-dy,x-dx+self.width,y-dy+self.height))
            picture.alpha_composite(sprite)
        else:
            picture=self.zoomed.crop((
                x,y,x+self.width,y+self.height)).convert("RGBA")
        picture.alpha_composite(self.vignette)
        return picture.convert("RGB")


def _local_subject_mask(image: Image.Image) -> Image.Image:
    """Lightweight local saliency foreground; never use rembg's cloud default.

    U2NetP code/weights: upstream U-2-Net Apache-2.0; rembg MIT. The model
    is not bundled with this project and may download once to local cache.
    """
    try:
        from rembg import new_session, remove
    except ImportError as exc:
        raise RuntimeError(
            "Optional subject segmentation requires pip install 'rembg[cpu]'") from exc
    # Cached on the function object for this process: the ONNX session is
    # expensive. No remote inference provider or API token is involved.
    session=getattr(_local_subject_mask,"_cached_session",None)
    if session is None:
        session=new_session("u2netp")
        _local_subject_mask._cached_session=session
    output=remove(image,session=session)
    if not isinstance(output,Image.Image):
        raise RuntimeError("Segmentation produced an unsupported image")
    mask=output.convert("RGBA").getchannel("A")
    return mask


def _usable_mask(mask: Image.Image, source: Image.Image) -> Image.Image | None:
    if not isinstance(mask,Image.Image) or mask.size != source.size:
        return None
    alpha=mask.convert("L")
    hist=alpha.histogram()
    count=source.width*source.height
    fraction=sum(hist[32:])/count
    if not .04 <= fraction <= .82:
        return None
    return alpha


def build_commons_scenes(story:dict, width:int, height:int, *,
                         query_media=None, image_media=None,
                         segment_art=False, mask_subject=None):
    """Fetch <=one thumbnail per eligible beat; failure is a safe fallback.

    All media and provenance are recorded. No author content is treated as an
    instruction. Numeric scenes stay numerical even with a photo search.
    """
    if not 150 <= width <= 1080 or not 180 <= height <= 1080:
        raise ValueError("Invalid stage dimensions")
    if type(segment_art) is not bool:
        raise ValueError("Segmentation choice must be a boolean")
    if segment_art and mask_subject is None:
        # Explicit opt-in: report absent local dependencies rather than
        # quietly claiming the scene has 2.5D object segmentation.
        try:
            import rembg
        except ImportError as exc:
            raise RuntimeError(
                "Install the optional rembg[cpu] package for --segment-art") from exc
    segmenter=mask_subject or _local_subject_mask
    lookup=query_media or search_cc0
    image_download=image_media or _read_url
    scenes, manifest, used = {}, [], set()
    for index, beat in enumerate(story["beats"]):
        if (beat["kind"] in ("measure","compare") or
                beat.get("visualLayers") or beat.get("visualVectors")):
            continue
        query=beat.get("visualQuery") or beat["title"]
        try:
            candidates=lookup(query)
        except (ValueError,OSError,urllib.error.URLError,TimeoutError,json.JSONDecodeError):
            continue
        for entry in candidates[:4]:
            if entry["page"] in used:
                continue
            try:
                _safe_url(entry["thumbnail"],"upload.wikimedia.org",
                          prefix="/wikipedia/commons/")
                content=image_download(entry["thumbnail"],MAX_IMAGE_BYTES,
                                       "upload.wikimedia.org")
                bitmap=decode_image(content)
            except (ValueError,OSError,urllib.error.URLError,TimeoutError):
                continue
            mask=None
            if segment_art:
                try:
                    mask=_usable_mask(segmenter(bitmap),bitmap)
                except (RuntimeError,ValueError,OSError):
                    # Evidence that segmentation was not accepted must remain
                    # visible in metadata, with a stable photo fallback.
                    mask=None
            scenes[index]=CommonsPhotoScene(
                title=entry["title"],origin=entry["page"],
                creator=entry["creator"],thumbnail=entry["thumbnail"],
                sha256=hashlib.sha256(content).hexdigest(),
                image=bitmap,width=width,height=height,
                subject_mask=mask)
            used.add(entry["page"])
            manifest.append({
                "beat":index,"query":query,"filePage":entry["page"],
                "license":entry["license"],"licenseURL":entry["licenseURL"],
                "artist":entry["creator"],"credit":entry["credit"],
                "thumbnailURL":entry["thumbnail"],
                "sha256":scenes[index].sha256,
                "editorialReviewed":False,"rightsVerifiedByHuman":False,
                "segmentationRequested":segment_art,
                "segmentationApplied":mask is not None,
                "segmentationModel":"u2netp" if mask is not None else None,
            })
            break
    return scenes,manifest
