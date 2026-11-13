"""Actual encoded flower QA and rejection of unverified release packages."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

from automate_ytb.universal_kinetic import produce

ROOT=Path(__file__).resolve().parents[1]
with patch.object(sys,"path",[str(ROOT/"scripts"),str(ROOT/"examples"),*sys.path]):
    import prepare_flower_delivery as delivery
    import build_articulated_flower_pilot as pilot


class FlowerDeliveryTests(unittest.TestCase):
    def test_package_digests_reject_replaced_assets_and_unsafe_names(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            names=("flower.mp4","flower.srt","flower-production.json","flower-contact-sheet.jpg")
            for name in names: (root/name).write_bytes(b"original asset")
            manifest={"status":"passed","releaseEligible":True,"files":{
                name:{"sha256":delivery.digest(root/name),"bytes":14} for name in names}}
            target=root/"flower-manifest.json"
            target.write_text(json.dumps(manifest))
            delivery.verify_package(root)
            (root/"flower.mp4").write_bytes(b"modified asset")
            with self.assertRaisesRegex(ValueError,"digest"):
                delivery.verify_package(root)
            manifest["files"]["../outside"]={"sha256":"bad","bytes":1}
            target.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,"package"):
                delivery.verify_package(root)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe") and
                         (shutil.which("espeak-ng") or shutil.which("espeak")),
                         "Real local speech and FFmpeg required")
    def test_real_mp4_full_decode_subtitles_mix_and_draft_release_block(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); story=pilot.story()
            for beat,text in zip(story["beats"],(
                "La fleur se prépare.","Les pétales se déploient.","La fleur est ouverte.")):
                beat["narration"]=text
            brief=root/"story.json"
            brief.write_text(json.dumps(story,separators=(",",":")),encoding="utf8")
            video=root/"draft.mp4"
            report=produce(brief,video,voice="espeak",width=720)
            self.assertEqual(report["actorCueCount"],7)
            self.assertEqual(report["foley"]["cueCount"],10)
            prepared=delivery.prepare(video,root/"review")
            self.assertTrue(prepared["fullDecode"])
            self.assertFalse(prepared["releaseEligible"])
            self.assertFalse(prepared["publicationApproved"])
            self.assertEqual(prepared["files"]["flower.mp4"]["sha256"],delivery.digest(video))
            with self.assertRaisesRegex(ValueError,"Kokoro"):
                delivery.prepare(video,root/"release",release=True)
            # An external subtitle edit must never silently become a release.
            with video.with_suffix(".srt").open("a") as out:
                out.write("99\n00:00:00,000 --> 00:00:01,000\nUnexpected overlap.\n\n")
            with self.assertRaisesRegex(ValueError,"digest"):
                delivery.prepare(video,root/"bad")


if __name__=="__main__": unittest.main()
