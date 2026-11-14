"""Continuous original world camera, detailed artwork and honest source claims."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from automate_ytb.universal_scale_camera import (
    VERSION, _landmark_icon, camera_pose, landmark_reveal,
    render_cinematic_scale_frame, world_y)
from automate_ytb.universal_scale_journey import render_scale_frame
from automate_ytb.universal_script import compile_original_script
from automate_ytb.universal_kinetic import frame_image, read_story, timeline_for


SOURCE=Path(__file__).resolve().parents[1]/(
    "examples/universal_scale_journey_story.en.txt")
TITLE="What if a glowing thread kept growing?"
TIMES=[0,48,96,144,192,240,288]


def load(story: dict) -> dict:
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/"story.json"
        path.write_text(json.dumps(story,ensure_ascii=False),
                        encoding="utf8")
        return read_story(path)


class WorldCameraV22Tests(unittest.TestCase):
    def compiled(self):
        return compile_original_script(topic=TITLE,language="en",
                                       script=SOURCE.read_text(encoding="utf8"))

    def test_native_v22_routed_only_when_all_numbers_are_source_anchored(self):
        compiled=self.compiled()
        self.assertEqual(compiled["proceduralScaleCameraEngine"],VERSION)
        self.assertEqual(len(compiled["beats"]),6)
        self.assertFalse(compiled["factualResearchPerformed"])
        data=load(compiled)
        self.assertEqual(data["proceduralScaleCameraEngine"],VERSION)
        self.assertEqual(len(data["proceduralScaleJourney"]["points"]),6)
        self.assertTrue(all(not b["actorLinks"] and not b["visualVectors"]
                            for b in data["beats"]))
        unsupported=compile_original_script(
            topic="Coastal weather",language="en",
            script=("Rain waters the trees near a train station.\n\n"
                    "Ocean waves crash into a train beside the shore."))
        self.assertNotIn("proceduralScaleCameraEngine",unsupported)
        self.assertEqual(load(unsupported)["proceduralVisualFamily"],None)

    def test_one_camera_world_has_exact_cut_continuity(self):
        source=self.compiled()["proceduralScaleJourney"]
        n=len(source["points"])
        for i in range(1,n):
            end=camera_pose(source,i-1,1.)
            start=camera_pose(source,i,0.)
            self.assertEqual(end,start)
            for world in (0.,.23,.51,.84,1.):
                self.assertEqual(world_y(end,world),world_y(start,world))
        self.assertLess(camera_pose(source,0,0.)["progress"],
                        camera_pose(source,n-1,1.)["progress"])
        # Ground moves below frame while the tip moves up with world camera.
        start_y=world_y(camera_pose(source,0,0.),0.)
        final_y=world_y(camera_pose(source,n-1,1.),0.)
        self.assertGreater(final_y,start_y)
        with self.assertRaises(ValueError):
            world_y(camera_pose(source,0,0.),1.1)

    def test_landmarks_reveal_in_current_beat_and_persist_after_cut(self):
        self.assertEqual(landmark_reveal(2,1,.7),0.)
        self.assertEqual(landmark_reveal(2,2,0.),0.)
        self.assertGreater(landmark_reveal(2,2,.25),0.)
        self.assertEqual(landmark_reveal(2,2,.6),1.)
        self.assertEqual(landmark_reveal(2,2,1.),1.)
        self.assertEqual(landmark_reveal(2,3,0.),1.)
        with self.assertRaises(ValueError):
            landmark_reveal(2,2,1.2)

    def test_actual_original_raster_detail_for_all_source_landmarks(self):
        artwork={}
        for kind in ("ruler","human","tree","tower","mountain","earth","moon"):
            img=_landmark_icon(kind,160)
            self.assertEqual(img.size,(160,160))
            self.assertEqual(img.mode,"RGBA")
            self.assertIsNotNone(img.getbbox())
            self.assertGreater(sum(img.getchannel("A").getdata()),10000)
            artwork[kind]=img.tobytes()
        self.assertEqual(len(set(artwork.values())),len(artwork))
        self.assertEqual(
            _landmark_icon("tree",160).tobytes(),artwork["tree"])

    def test_pixels_change_as_camera_moves_but_frames_are_reproducible(self):
        story=load(self.compiled())
        timeline=timeline_for(story,TIMES)
        one=frame_image(story,timeline,TIMES,16,360,640)
        two=frame_image(story,timeline,TIMES,36,360,640)
        later=frame_image(story,timeline,TIMES,107,360,640)
        final=frame_image(story,timeline,TIMES,259,360,640)
        self.assertEqual(one.size,(360,640))
        self.assertEqual(one.mode,"RGB")
        self.assertNotEqual(one.tobytes(),two.tobytes())
        self.assertNotEqual(two.tobytes(),later.tobytes())
        self.assertNotEqual(later.tobytes(),final.tobytes())
        self.assertEqual(two.tobytes(),
                         frame_image(story,timeline,TIMES,36,360,640).tobytes())
        with self.assertRaises(ValueError):
            render_cinematic_scale_frame(
                story["proceduralScaleJourney"],TITLE,49,TIMES,
                0,360,640)

    def test_preexisting_v21_saved_story_renders_identical_legacy_pixels(self):
        original=self.compiled()
        original.pop("proceduralScaleCameraEngine")
        original.pop("proceduralScaleSpeechEngine")
        old=load(original)
        self.assertIsNone(old.get("proceduralScaleCameraEngine"))
        timeline=timeline_for(old,TIMES)
        for frame,position in ((5,0),(113,2),(281,5)):
            actual=frame_image(old,timeline,TIMES,frame,360,640)
            legacy=render_scale_frame(
                old["proceduralScaleJourney"],TITLE,
                frame,TIMES,position,360,640)
            # frame_image paints a fallback caption, so compare a central
            # pixel region safely above the >=69%-height caption panel.
            self.assertEqual(
                actual.crop((0,0,360,420)).tobytes(),
                legacy.crop((0,0,360,420)).tobytes())

    def test_forged_camera_provenance_or_unsourced_value_is_rejected(self):
        clean=self.compiled()
        for mutation in (
            lambda d:d.update(proceduralScaleCameraEngine="false-camera"),
            lambda d:d.update(proceduralScaleCameraEngine=None),
            lambda d:d["proceduralScaleJourney"]["points"][2].__setitem__(
                "metres","999"),
            lambda d:d["beats"][3].__setitem__(
                "narration","No measurements are present in this sentence."),
        ):
            damaged=deepcopy(clean)
            mutation(damaged)
            with self.subTest(mutation=str(mutation)),self.assertRaises(
                    ValueError):
                load(damaged)
        stripped=deepcopy(clean)
        stripped.pop("proceduralScaleJourney")
        with self.assertRaises(ValueError):
            load(stripped)
        orphan=deepcopy(clean)
        orphan.pop("proceduralScaleJourney")
        orphan.pop("proceduralScaleJourneyEngine")
        with self.assertRaises(ValueError):
            load(orphan)


if __name__=="__main__":
    unittest.main()
