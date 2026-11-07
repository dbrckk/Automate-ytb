"""No reference-video repetition: five genuinely different lightning actions."""
from __future__ import annotations

import unittest
from pathlib import Path
import tempfile
import re
from PIL import Image, ImageChops

from automate_ytb.scene_plan import beats
from automate_ytb.science_lightning import (
    BEATS, BADGES, PATH, LEADER_CHANNEL, UPWARD_STREAMER,
    CONNECTED_CHANNEL, TOWER_TOP, classify, supports_topic, draw_lightning,
    storm_background, STAGE_TOP, STAGE_BOTTOM,
)
from automate_ytb.science_portrait import PortraitScienceScene
from automate_ytb.cinematic_stage import camera_pose, camera_frame, CAMERA_VERSION

TOPIC="How Does Lightning Form?"
SCRIPT=(
    "Inside thunderclouds, colliding ice crystals and water droplets separate positive and negative electrical charges.",
    "As the electric field grows stronger, a faint stepped leader branches downward through the air toward the ground.",
    "Near the surface, upward streamers rise from tall objects, and one can connect with the descending leader.",
    "A powerful return stroke races upward along the connected channel, producing the brilliant flash we call lightning.",
    "The lightning channel superheats surrounding air, causing rapid expansion and a pressure wave that we hear as thunder.",
)


class OriginalLightningEpisodeTests(unittest.TestCase):
    def test_exact_five_unique_narration_actions(self):
        self.assertEqual(len(BEATS),5)
        self.assertEqual(set(BEATS),set(BADGES))
        self.assertEqual(len(PATH),57)
        self.assertTrue(supports_topic(TOPIC))
        self.assertTrue(supports_topic("How does lightning form?"))
        self.assertFalse(supports_topic("Why does the Earth stop?"))
        self.assertFalse(supports_topic("Why is the ocean blue?"))
        self.assertFalse(supports_topic("How do rainbows form?"))
        self.assertEqual(
            tuple(classify(TOPIC,text) for text in SCRIPT),BEATS)
        self.assertEqual(len(beats(" ".join(SCRIPT))),5)
        self.assertIsNone(classify(TOPIC,"A mysterious shape appears."))
        self.assertIsNone(classify("Earth stopped",SCRIPT[1]))
        for bad in ((None,SCRIPT[0]),(TOPIC,None)):
            with self.assertRaises(ValueError):
                classify(*bad)

    def test_discharge_has_one_geometrically_connected_path(self):
        # No teleporting bolt below the tower in the return shot.
        self.assertEqual(UPWARD_STREAMER[0], TOWER_TOP)
        self.assertEqual(UPWARD_STREAMER[-1], LEADER_CHANNEL[-1])
        self.assertEqual(CONNECTED_CHANNEL[0], TOWER_TOP)
        self.assertEqual(CONNECTED_CHANNEL[len(UPWARD_STREAMER)-1],
                         LEADER_CHANNEL[-1])
        self.assertEqual(CONNECTED_CHANNEL[-1], LEADER_CHANNEL[0])
        self.assertEqual(len(LEADER_CHANNEL), 41)
        self.assertEqual(len(set(CONNECTED_CHANNEL)),
                         len(CONNECTED_CHANNEL))

    def test_camera_stage_larger_and_uniform_with_safe_crop(self):
        self.assertIn("stage-camera", CAMERA_VERSION)
        source=Image.new("RGBA",(1080,930),(14,36,66,255))
        self.assertGreater(STAGE_BOTTOM-STAGE_TOP, 930)
        for beat in BEATS:
            start=camera_frame(source,beat,0,7)
            end=camera_frame(source,beat,7,7)
            self.assertEqual(start.size,(1080,1380))
            self.assertEqual(start.getchannel("A").getextrema(),(255,255))
            self.assertEqual(end.getchannel("A").getextrema(),(255,255))
            for second in (0,1/30,2/30,3,6.9):
                zoom,x,y=camera_pose(beat,second,7)
                self.assertGreaterEqual(zoom, 1.50)
                self.assertGreaterEqual(x-540/zoom,-.0001)
                self.assertLessEqual(x+540/zoom,1080.0001)
                self.assertGreaterEqual(y-690/zoom,-.0001)
                self.assertLessEqual(y+690/zoom,930.0001)
        with self.assertRaises(ValueError):
            camera_pose("invalid",0,7)
        with self.assertRaises(ValueError):
            camera_frame(Image.new("RGB",(1080,930)),"charge",0,7)

    def test_cinematic_camera_follows_electrical_event_in_both_directions(self):
        # The authored leader descends toward the mast; the return stroke
        # travels upward again. Focus Y must actually follow these events,
        # not remain fixed like a graphic slide with a lateral wobble.
        self.assertIn("vertical-action-follow", CAMERA_VERSION)
        descending_start=camera_pose("leader",0.,7.)
        descending_end=camera_pose("leader",7.,7.)
        upward_start=camera_pose("return",0.,7.)
        upward_end=camera_pose("return",7.,7.)
        self.assertGreater(descending_end[2]-descending_start[2],130)
        self.assertGreater(upward_start[2]-upward_end[2],100)
        self.assertGreater(descending_end[0],descending_start[0])
        self.assertGreater(upward_end[0],upward_start[0])
        # Camera movement is continuous even at 30fps and never crops
        # outside the true 930px moving source-space storm.
        for beat in BEATS:
            for frame in range(210):
                t=frame/30
                zoom,x,y=camera_pose(beat,t,7.)
                self.assertGreaterEqual(zoom,1.5)
                self.assertGreaterEqual(x-540/zoom,-.001)
                self.assertLessEqual(x+540/zoom,1080.001)
                self.assertGreaterEqual(y-690/zoom,-.001)
                self.assertLessEqual(y+690/zoom,930.001)
                if frame:
                    previous=camera_pose(beat,(frame-1)/30,7.)
                    self.assertLess(abs(x-previous[1]),8)
                    self.assertLess(abs(y-previous[2]),8)

    def test_lightning_episode_title_does_not_repeat_over_every_action(self):
        # Top-of-frame is independent from the rendered channel and captions.
        # Title appears for the first 2 seconds only, while later shots have
        # compact unique beat labels and unobtrusive step progress.
        first=PortraitScienceScene(topic=TOPIC,narration=SCRIPT[0],scene_index=1)
        second=PortraitScienceScene(topic=TOPIC,narration=SCRIPT[1],scene_index=2)
        top=(68,117,1017,290)
        title_crop=first.frame(.3,7.).crop(top)
        action_crop=first.frame(4.,7.).crop(top)
        leader_early=second.frame(.3,7.).crop(top)
        leader_late=second.frame(5.,7.).crop(top)
        self.assertNotEqual(title_crop.tobytes(),action_crop.tobytes())
        # Source-MP4 visual audit caught a collision between the long title
        # and the right-side step counter during the opening shot. The
        # counter is suppressed while the title is on screen; the uncovered
        # right edge of the header must now be darker than the later badge.
        self.assertLess(
            sum(title_crop.getpixel((906, 93))[:3]),
            sum(action_crop.getpixel((906, 93))[:3]))
        self.assertNotEqual(action_crop.tobytes(),leader_early.tobytes())
        self.assertEqual(leader_early.tobytes(),leader_late.tobytes())

    def test_new_episode_has_no_globe_and_five_distinct_frames(self):
        signatures=[]
        for i,(beat,phrase) in enumerate(zip(BEATS,SCRIPT),1):
            with self.subTest(beat=beat):
                shot=PortraitScienceScene(
                    topic=TOPIC,narration=phrase,scene_index=i)
                self.assertEqual(shot.lightning_beat,beat)
                self.assertIsNone(shot.earth_stop_beat)
                self.assertIsNone(shot.rainbow_beat)
                self.assertIsNone(shot.beat)
                self.assertTrue(shot.english)
                self.assertFalse(shot._globes)
                start=shot.frame(.3,6.8)
                end=shot.frame(5.8,6.8)
                self.assertEqual(start.size,(1080,1920))
                self.assertEqual(start.mode,"RGB")
                self.assertEqual(start.tobytes(),shot.frame(.3,6.8).tobytes())
                hero=(70,610,1010,1490)
                crop=start.crop(hero)
                signatures.append(crop.tobytes())
                self.assertIsNotNone(ImageChops.difference(
                    crop,end.crop(hero)).getbbox())
                # Captions are allowed to change with narration; demanding
                # a frozen caption crop incorrectly fails real speech cues.
                self.assertTrue(shot.active_caption(.3,6.8).strip())
                self.assertTrue(shot.active_caption(5.8,6.8).strip())
                self.assertEqual(start.size,end.size)
        self.assertEqual(len(set(signatures)),5)

    def test_storm_canvas_safe_text_and_no_earth_plate(self):
        base=storm_background()
        self.assertEqual(base.mode,"RGBA")
        self.assertEqual(base.size,(1080,1920))
        self.assertLess(base.getpixel((540,100))[2],100)
        for beat in BEATS:
            with self.subTest(beat=beat):
                frame=base.copy()
                draw_lightning(frame,beat,.4,6.8,False)
                self.assertEqual(frame.getchannel("A").getextrema(),(255,255))
                self.assertEqual(frame.crop((0,0,1080,STAGE_TOP)).tobytes(),
                                 base.crop((0,0,1080,STAGE_TOP)).tobytes())
                self.assertEqual(frame.crop((0,STAGE_BOTTOM,1080,1920)).tobytes(),
                                 base.crop((0,STAGE_BOTTOM,1080,1920)).tobytes())

    def test_real_production_script_has_five_authored_original_mechanisms(self):
        workflow=(Path(__file__).resolve().parents[1]/".github"/
                  "workflows"/"lightning-science-release-candidate.yml")
        text=workflow.read_text(encoding="utf-8")
        section=re.search(
            r"(?m)^      original_script: >-\n((?:^        .+\n){5})",
            text)
        self.assertIsNotNone(section, "Lightning workflow needs five scripts")
        authored=beats(" ".join(s.strip() for s in
                               section.group(1).splitlines()))
        self.assertEqual(len(authored),5)
        self.assertEqual(tuple(classify(TOPIC,x) for x in authored),BEATS)
        self.assertIn("      language: en",text)
        self.assertIn("      voice_name: af_heart",text)
        self.assertNotIn("What If Earth Suddenly Stopped",text)

    def test_real_science_artwork_approval_uses_lightning_not_earth(self):
        from automate_ytb.science_motion import render_character_poster
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/"storm.png"
            render_character_poster(
                topic=TOPIC,narration=SCRIPT[1],scene_index=2,
                scene_count=5,style="science",destination=target)
            self.assertTrue(target.is_file())
            with Image.open(target) as image:
                self.assertEqual(image.size,(1280,720))
                self.assertEqual(image.format,"PNG")
                self.assertIsNotNone(image.getbbox())

    def test_reject_unsupported_scene_and_bad_clock(self):
        frame=storm_background().copy()
        for beat,t,dur in [
            ("planet",1.,6.8),("leader",-1.,6.8),
            ("charge",6.9,6.8),("return",1.,0),
            ("thunder",float("nan"),6.8),
        ]:
            with self.subTest(beat=beat,t=t),self.assertRaises(ValueError):
                draw_lightning(frame,beat,t,dur,False)
        with self.assertRaises(ValueError):
            draw_lightning(Image.new("RGB",(1080,1920)),
                           "leader",1.,7.0,False)
        with self.assertRaises(ValueError):
            PortraitScienceScene(topic=TOPIC,
                narration="A story without a physical mechanism",
                scene_index=1)


if __name__=="__main__":
    unittest.main()
