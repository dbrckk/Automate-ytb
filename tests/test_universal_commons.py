"""Fail-closed CC0 artwork ingestion and real deterministic 2.5D photo frames.

Every API fixture is local, not a fake claim about live Commons availability.
No remote images are fetched by CI. All security/licensing paths are exercised.
"""
from __future__ import annotations

from decimal import Decimal
from io import BytesIO
import json
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from automate_ytb.universal_commons import (
    CC0_URL, CommonsPhotoScene, _safe_url, build_commons_scenes,
    decode_image, search_cc0)
from automate_ytb.universal_kinetic import frame_image, timeline_for

THUMB="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/test.jpg/960px-test.jpg"
PAGE="https://commons.wikimedia.org/wiki/File:Illustrative_test.jpg"


def api(license_name="CC0", license_url=CC0_URL, thumbnail=THUMB,
        mime="image/jpeg", pages=1):
    return {"query":{"pages":[
        {"ns":6,"index":idx+1,"title":f"File:Illustrative_test_{idx}.jpg",
         "imageinfo":[
             {"mime":mime,"thumburl":thumbnail,
              "descriptionurl":PAGE+str(idx),
              "extmetadata":{
                  "LicenseShortName":{"value":license_name},
                  "LicenseUrl":{"value":license_url},
                  "Artist":{"value":"<b>Original creator</b>"}
              }}]} for idx in range(pages)
    ]}}


def media():
    image=Image.new("RGB",(600,400),(45,96,125))
    draw=ImageDraw.Draw(image)
    for x in range(0,600,6):
        draw.polygon(((x,370),(x,abs(x-300)//3),(x+3,400)),
                     fill=(x%200+30,120,75))
    b=BytesIO()
    image.save(b,format="JPEG")
    return b.getvalue()


def story():
    return {
        "topic":"An original forest story","language":"en",
        "beats":[
            {"kind":"concept","title":"A forest close-up",
             "narration":"Original words describing a photograph of a forest.",
             "items":["Forest","Sunlight","Trees"],"visualQuery":"forest canopy"},
            {"kind":"measure","title":"A measured scene",
             "narration":"The estimated total is measured independently here.",
             "label":"Sample","value":Decimal("9"),"scaleMax":Decimal("10"),
             "unit":"ms"},
        ]}


class WikimediaCommonsArtTests(unittest.TestCase):
    def test_search_uses_only_explicit_cc0_and_fixed_api(self):
        def mocked(url,maximum,host):
            self.assertTrue(url.startswith("https://commons.wikimedia.org/w/api.php?"))
            self.assertIn("iiurlwidth=960",url)
            self.assertEqual(host,"commons.wikimedia.org")
            self.assertLessEqual(maximum,240_000)
            return json.dumps(api()).encode()
        results=search_cc0("green meadow",read_url=mocked)
        self.assertEqual(len(results),1)
        self.assertEqual(results[0]["license"],"CC0-1.0")
        self.assertEqual(results[0]["creator"],"Original creator")
        self.assertEqual(results[0]["page"],PAGE+"0")
        for license_name,license_url in (
            ("CC BY-SA 4.0","https://creativecommons.org/licenses/by-sa/4.0/"),
            ("CC0","https://evil.example/cc0"),
            ("Public domain","https://commons.wikimedia.org/wiki/Public_domain"),
        ):
            result=search_cc0("forest",read_url=lambda *a:json.dumps(
                api(license_name,license_url)).encode())
            self.assertEqual(result,[])

    def test_untrusted_hosts_and_media_types_rejected(self):
        for host in (
            "https://upload.wikimedia.org.evil.test/wikipedia/commons/x.jpg",
            "http://upload.wikimedia.org/wikipedia/commons/test.jpg",
            "https://evil.example/wikipedia/commons/test.jpg",
            "https://upload.wikimedia.org/etc/passwd",
            "https://anonymous@upload.wikimedia.org/wikipedia/commons/test.jpg",
        ):
            with self.subTest(host=host),self.assertRaises(ValueError):
                _safe_url(host,"upload.wikimedia.org",
                          prefix="/wikipedia/commons/")
        for payload in (
            api(thumbnail="https://evil.example/malware.jpg"),
            api(mime="image/svg+xml"),
            api(license_name="CC BY 4.0"),
        ):
            result=search_cc0("forest",read_url=lambda *a:json.dumps(
                payload).encode())
            self.assertEqual(result,[])
        with self.assertRaises(ValueError):
            decode_image(b"<svg>alert(1)</svg>")

    def test_really_decoded_photo_animates_and_has_traceable_provenance(self):
        payload=media()
        traces=[]
        def fake_lookup(q):
            traces.append(q)
            return search_cc0(q,read_url=lambda *a:json.dumps(api()).encode())
        def fake_download(url,maximum,host):
            self.assertEqual(url,THUMB)
            self.assertEqual(host,"upload.wikimedia.org")
            self.assertGreater(maximum,len(payload))
            return payload
        scenes,manifest=build_commons_scenes(
            story(),400,460,query_media=fake_lookup,
            image_media=fake_download)
        self.assertEqual(traces,["forest canopy"])
        self.assertEqual(list(scenes),[0])
        self.assertEqual(len(manifest),1)
        self.assertFalse(manifest[0]["editorialReviewed"])
        self.assertFalse(manifest[0]["rightsVerifiedByHuman"])
        self.assertEqual(len(manifest[0]["sha256"]),64)
        a=scenes[0].render(5,0,90)
        b=scenes[0].render(70,0,90)
        self.assertEqual(a.size,(400,460))
        self.assertNotEqual(a.tobytes(),b.tobytes())
        self.assertEqual(scenes[0].render(5,0,90).tobytes(),a.tobytes())
        video_story=story()
        tm=timeline_for(video_story,[0,90,180])
        fa=frame_image(video_story,tm,[0,90,180],5,480,853,
                       commons_scenes={0:CommonsPhotoScene(
                           title=scenes[0].title,origin=scenes[0].origin,
                           creator=scenes[0].creator,thumbnail=scenes[0].thumbnail,
                           sha256=scenes[0].sha256,image=scenes[0].image,
                           width=480-2*round(480*.045),height=round(853*.495))})
        self.assertEqual(fa.size,(480,853))
        with self.assertRaises(ValueError):
            scenes[0].render(-1,0,90)

    def test_original_subject_mask_has_real_independent_parallax(self):
        payload=media()
        mask=Image.new("L",(600,400),0)
        painter=ImageDraw.Draw(mask)
        painter.ellipse((185,70,420,330),fill=255)
        photos,provenance=build_commons_scenes(
            story(),400,460,
            query_media=lambda *a:search_cc0(
                "forest",read_url=lambda *a:json.dumps(api()).encode()),
            image_media=lambda *a:payload,
            segment_art=True,mask_subject=lambda im:mask)
        self.assertEqual(len(photos),1)
        self.assertTrue(provenance[0]["segmentationRequested"])
        self.assertTrue(provenance[0]["segmentationApplied"])
        self.assertEqual(provenance[0]["segmentationModel"],"u2netp")
        self.assertIsNotNone(photos[0].foreground)
        a,b=photos[0].render(1,0,90),photos[0].render(50,0,90)
        self.assertNotEqual(a.tobytes(),b.tobytes())
        plain=CommonsPhotoScene(
            title="A",origin=PAGE,creator="Tester",thumbnail=THUMB,
            sha256="0"*64,image=photos[0].image,width=400,height=460)
        self.assertNotEqual(photos[0].render(50,0,90).tobytes(),
                            plain.render(50,0,90).tobytes())
        # An unusable all-white mask must fail closed to simple photo motion.
        blank=Image.new("L",(600,400),255)
        fallback,manifest=build_commons_scenes(
            story(),400,460,
            query_media=lambda *a:search_cc0(
                "forest",read_url=lambda *a:json.dumps(api()).encode()),
            image_media=lambda *a:payload,
            segment_art=True,mask_subject=lambda im:blank)
        self.assertFalse(manifest[0]["segmentationApplied"])
        self.assertIsNone(fallback[0].foreground)

    def test_no_license_no_source_no_photo_does_not_break_video(self):
        with patch("automate_ytb.universal_commons.search_cc0",
                   side_effect=OSError("Network unavailable")):
            scenes,manifest=build_commons_scenes(story(),400,460)
        self.assertEqual(scenes,{})
        self.assertEqual(manifest,[])
        with self.assertRaises(ValueError):
            search_cc0("A"*121,read_url=lambda *a:b"{}")
        scenes,manifest=build_commons_scenes(story(),400,460,
            query_media=lambda *a:[{
                "page":PAGE,"thumbnail":"https://evil.example/fake.png",
                "title":"Fake","license":"CC0-1.0","licenseURL":CC0_URL,
                "creator":"Unknown","credit":""}],
            image_media=lambda *a:media())
        self.assertEqual(scenes,{})
        self.assertEqual(manifest,[])


if __name__ == "__main__":
    unittest.main()
