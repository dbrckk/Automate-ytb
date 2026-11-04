"""Real universal video editorial checks: cartoon, documentary, cinematic and science.

No neural service, YouTube account, external asset, or paid API is required.
"""
from __future__ import annotations

import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

from automate_ytb.editorial_camera import camera_filter, camera_metadata
from automate_ytb.editorial_cuts import choose_transition
from automate_ytb.transitions import transition_clips


class EditorialChoiceTests(unittest.TestCase):
    def test_adaptive_cut_avoids_distant_image_ghosting(self):
        red=Image.new("RGB",(320,180),(228,35,27))
        blue=Image.new("RGB",(320,180),(19,54,220))
        result=choose_transition(red,blue)
        self.assertEqual(result["mode"],"cut")
        self.assertEqual(result["reason"],"large-rgb-discontinuity")
        self.assertTrue(result["noAudioOrSubtitleShift"])
        self.assertFalse(result["editorialApproved"])

    def test_similar_shots_and_portrait_still_support_dissolves(self):
        first=Image.new("RGB",(1080,1920),(66,91,117))
        second=Image.new("RGB",(1080,1920),(75,93,123))
        result=choose_transition(first,second)
        self.assertEqual(result["mode"],"dissolve")
        self.assertEqual(result["sampleDimensions"],[90,160])

    def test_dark_bright_jump_and_bad_aspect_fail_closed(self):
        black=Image.new("RGB",(320,180),(2,3,4))
        white=Image.new("RGB",(320,180),(220,220,220))
        self.assertEqual(choose_transition(black,white)["mode"],"cut")
        with self.assertRaises(ValueError):
            choose_transition(black,Image.new("RGB",(320,240)))

    def test_safe_semantic_still_camera_for_all_poster_styles(self):
        choices=set()
        from automate_ytb.director import direction_for
        for scene_index,shot in enumerate(
                ("wide","medium","closeup","macro","low","shoulder")):
            cue=direction_for("A narrator explores a new discovery",camera=shot)
            graph=camera_filter(width=1920,height=1080,fps=30,
                                duration=6,scene_index=scene_index,direction=cue)
            choices.add(graph)
            meta=camera_metadata(scene_index=scene_index,duration=6,
                                 direction=cue)
            self.assertEqual(meta["shot"],shot)
            self.assertFalse(meta["actualThreeDimensionalGeometry"])
            self.assertFalse(meta["changesAudioOrCaptions"])
            self.assertLess(meta["zoomEnd"],1.08)
            self.assertIn("zoompan",graph)
            self.assertIn("format=yuv420p",graph)
        self.assertEqual(len(choices),6)
        with self.assertRaises(ValueError):
            camera_filter(width=1280,height=720,fps=24,duration=5,
                          scene_index=0,direction={"shot":"wide;movie=/tmp/x"})
        with self.assertRaises(ValueError):
            camera_filter(width=3840,height=2160,fps=24,duration=5,scene_index=0)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "Real FFmpeg is required")
class RealVideoEditorialTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="universal-editor-")
        self.root=Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _clip(self, color, name, seconds=1.0):
        path=self.root/name
        subprocess.run([
            "ffmpeg","-nostdin","-v","error","-y",
            "-f","lavfi","-i",
            f"color=c={color}:s=320x180:r=24:d={seconds}",
            "-c:v","libx264","-preset","ultrafast",
            "-pix_fmt","yuv420p",str(path),
        ],capture_output=True,check=True,timeout=50)
        return path

    def _duration(self,path):
        p=subprocess.run([
            "ffprobe","-v","error","-show_entries","format=duration",
            "-of","default=nw=1:nk=1",str(path)
        ],capture_output=True,text=True,check=True,timeout=30)
        return float(p.stdout)

    def test_adaptive_video_uses_clean_cut_for_visual_jump(self):
        old=self._clip("red","red.mp4")
        new=self._clip("blue","blue.mp4")
        clips,report=transition_clips(
            [old,new],cache=self.root/"cut-cache",fps=24,
            durations=[1,1],mode="adaptive")
        self.assertEqual(clips,[old,new])
        self.assertEqual(report["count"],0)
        self.assertEqual(report["cutCount"],1)
        self.assertEqual(report["boundaries"][0]["transition"],"cut")
        self.assertEqual(report["timelineShiftMs"],0)
        self.assertFalse(report["publicationApproved"])
        self.assertEqual(self._duration(clips[1]),1.)

    def test_adaptive_video_retains_dissolve_for_neighboring_colors(self):
        old=self._clip("0x647f9a","old.mp4")
        new=self._clip("0x6b829c","new.mp4")
        clips,report=transition_clips(
            [old,new],cache=self.root/"fade-cache",fps=24,
            durations=[1,1],mode="adaptive")
        self.assertEqual(report["count"],1)
        self.assertEqual(report["cutCount"],0)
        self.assertNotEqual(clips[1],new)
        self.assertAlmostEqual(self._duration(clips[1]),1.,delta=.06)
        self.assertEqual(report["boundaries"][0]["transition"],"dissolve")
        self.assertGreater(clips[1].stat().st_size,1000)

    def test_generic_documentary_camera_has_real_motion_and_exact_duration(self):
        still=self.root/"original.png"
        image=Image.new("RGB",(1280,720),(22,54,75))
        from PIL import ImageDraw
        draw=ImageDraw.Draw(image)
        for i in range(10):
            draw.rectangle((110+i*90,110+i*24,150+i*90,145+i*24),
                           fill=(180+i*5,70+i*4,140+i*3))
        image.save(still)
        graph=camera_filter(
            width=1280,height=720,fps=24,duration=2,scene_index=2,
            direction={"weather":"day","action":"walk","emotion":"curious",
                       "shot":"medium"})
        out=self.root/"documentary.mp4"
        subprocess.run([
            "ffmpeg","-nostdin","-v","error","-y",
            "-loop","1","-framerate","24","-i",str(still),
            "-t","2","-vf",graph,"-c:v","libx264","-preset","ultrafast",
            "-pix_fmt","yuv420p",str(out)
        ],capture_output=True,check=True,timeout=75)
        self.assertAlmostEqual(self._duration(out),2.,delta=.05)
        def frame(t):
            p=subprocess.run([
                "ffmpeg","-nostdin","-v","error","-ss",str(t),
                "-i",str(out),"-frames:v","1","-f","image2pipe",
                "-vcodec","png","-"
            ],capture_output=True,check=True,timeout=30)
            with Image.open(io.BytesIO(p.stdout)) as img:
                return img.convert("RGB").resize((160,90))
        self.assertNotEqual(frame(.05).tobytes(),frame(1.70).tobytes())


if __name__=="__main__":
    unittest.main()
