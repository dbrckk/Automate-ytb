"""Event-directed cinematic camera regression tests for native 2.5D Shorts."""
from __future__ import annotations

import math
import unittest

from PIL import Image, ImageChops, ImageDraw

from automate_ytb.camera25d import (
    SHOT_TRAVEL, event_envelope, shot_camera, point_on_path,
)
from automate_ytb.cinematic_stage import camera_pose, camera_frame, CAMERA_VERSION
from automate_ytb.science_lightning import (
    BEATS, LEADER_CHANNEL, UPWARD_STREAMER, CONNECTED_CHANNEL,
)


class EventDirectedCameraTests(unittest.TestCase):
    def test_every_shot_has_zero_motion_and_velocity_at_cuts(self):
        for beat in BEATS:
            with self.subTest(beat=beat):
                start=shot_camera(beat,0.,7.2,subject=(700.,690.))
                end=shot_camera(beat,7.2,7.2,subject=(700.,690.))
                for move in (start,end):
                    self.assertEqual(move.parallax_x,0.)
                    self.assertEqual(move.parallax_y,0.)
                    self.assertEqual(move.focus_dx,0.)
                    self.assertEqual(move.focus_dy,0.)
                    self.assertEqual(move.emphasis,0.)
                # A C1 start/end must not jump on the first 1/1000 of a
                # shot. This guards against abrupt one-frame camera snaps.
                near_start=shot_camera(beat,.0072,7.2,subject=(700.,690.))
                near_end=shot_camera(beat,7.1928,7.2,subject=(700.,690.))
                self.assertLess(abs(near_start.parallax_x),.01)
                self.assertLess(abs(near_end.parallax_x),.01)
                self.assertLess(abs(near_start.focus_dx),.01)

    def test_original_narrated_event_changes_camera_peak(self):
        early=shot_camera("leader",7.2*.3,7.2,
                          event_fraction=.3,subject=(550.,600.))
        late=shot_camera("leader",7.2*.7,7.2,
                         event_fraction=.7,subject=(550.,600.))
        self.assertAlmostEqual(early.emphasis,1.)
        self.assertAlmostEqual(late.emphasis,1.)
        self.assertAlmostEqual(early.parallax_x,SHOT_TRAVEL["leader"][0])
        self.assertAlmostEqual(late.parallax_x,SHOT_TRAVEL["leader"][0])
        self.assertLess(shot_camera("leader",7.2*.3,7.2,
                         event_fraction=.7).emphasis,1.)

    def test_far_near_parallax_separation_is_perceptible(self):
        at_event=shot_camera("leader",4.32,7.2,event_fraction=.6)
        # Genuine parallax: source-cloud shifts differ by > 50 px, then the
        # native portrait source-space camera magnifies that movement.
        far=at_event.parallax_x*.2
        near=at_event.parallax_x*.94
        self.assertGreater(abs(near-far),50)

    def test_camera_follows_authored_not_inferred_physical_path(self):
        start=point_on_path(LEADER_CHANNEL,0.)
        finish=point_on_path(LEADER_CHANNEL,1.)
        self.assertLess(start[1],finish[1])
        self.assertEqual(point_on_path(UPWARD_STREAMER,0.),(700.,695.))
        self.assertEqual(point_on_path(CONNECTED_CHANNEL,0.),(700.,695.))
        midpoint=point_on_path(LEADER_CHANNEL,.5)
        self.assertTrue(0 < midpoint[0] < 1080)
        move=shot_camera("leader",4.32,7.2,event_fraction=.6,
                         subject=finish)
        self.assertGreater(move.focus_dx,0.)
        self.assertGreater(move.focus_dy,0.)

    def test_bounded_world_space_tracking_never_exposes_bars(self):
        stage=Image.new("RGBA",(1080,930),(35,55,85,255))
        ImageDraw.Draw(stage).ellipse((520,320,660,460),
                                      fill=(255,219,80,255))
        original=camera_frame(stage,"leader",4.32,7.2)
        guided=camera_frame(stage,"leader",4.32,7.2,
                            focus_offset=(45.,25.))
        self.assertEqual(original.size,(1080,1380))
        self.assertEqual(guided.getchannel("A").getextrema(),(255,255))
        self.assertIsNotNone(ImageChops.difference(
            original.convert("RGB"),guided.convert("RGB")).getbbox())
        zoom,x,y=camera_pose("leader",4.32,7.2,
                             focus_offset=(45.,25.))
        self.assertGreaterEqual(x-540/zoom,0.)
        self.assertLessEqual(x+540/zoom,1080.)
        self.assertGreaterEqual(y-690/zoom,0.)
        self.assertLessEqual(y+690/zoom,930.)

    def test_cinematic_portrait_camera_tracks_downward_then_upward_action(self):
        self.assertIn("vertical-p50-smooth",CAMERA_VERSION)
        initial_leader=camera_pose("leader",0.,7.)
        final_leader=camera_pose("leader",7.,7.)
        initial_return=camera_pose("return",0.,7.)
        final_return=camera_pose("return",7.,7.)
        # Source-stage pixels: leader tracks falling bolt down, return
        # stroke reverses to follow the ascending light, not a static slide.
        self.assertGreater(final_leader[2]-initial_leader[2],110.)
        self.assertGreater(initial_return[2]-final_return[2],125.)
        self.assertGreater(final_leader[0],initial_leader[0])
        self.assertGreater(final_return[0],initial_return[0])
        self.assertNotEqual(initial_leader[1],final_leader[1])

    def test_every_vertical_camera_frame_is_continuous_and_safe_at_30fps(self):
        for beat in BEATS:
            with self.subTest(beat=beat):
                previous=None
                for frame in range(211):
                    t=min(7.,frame/30)
                    zoom,x,y=camera_pose(beat,t,7.)
                    self.assertGreaterEqual(zoom,1380/930)
                    self.assertGreaterEqual(x-540/zoom,-.0001)
                    self.assertLessEqual(x+540/zoom,1080.0001)
                    self.assertGreaterEqual(y-690/zoom,-.0001)
                    self.assertLessEqual(y+690/zoom,930.0001)
                    if previous is not None:
                        self.assertLess(abs(x-previous[1]),8.)
                        self.assertLess(abs(y-previous[2]),8.)
                        self.assertLess(abs(zoom-previous[0]),.03)
                    previous=(zoom,x,y)

    def test_return_stroke_camera_has_no_high_frequency_shake(self):
        # Native 30 FPS output must not contain the previous 27 rad/s
        # synthetic oscillation; this measures acceleration in source pixels.
        for beat in ("return","connection","thunder"):
            samples=[camera_pose(beat,frame/30.,7.)
                     for frame in range(211)]
            self.assertEqual(samples[0][1:],camera_pose(beat,0.,7.)[1:])
            for axis in (1,2):
                acceleration=[
                    abs(samples[i+1][axis]-2*samples[i][axis]+samples[i-1][axis])
                    for i in range(1,len(samples)-1)]
                self.assertLess(max(acceleration),.35,
                                f"{beat}: jerky optical camera axis {axis}")
            self.assertLess(abs(samples[1][1]-samples[0][1]),.2)
            self.assertLess(abs(samples[-1][1]-samples[-2][1]),.2)

    def test_invalid_script_timing_or_camera_subject_fails_closed(self):
        for bad in (math.nan,math.inf,-.01,1.01,True):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    event_envelope(.5,action_fraction=bad)
                with self.assertRaises(ValueError):
                    shot_camera("leader",1.,7.2,event_fraction=bad)
        for bad in (None,):  # No segment timing is explicitly supported.
            self.assertTrue(math.isfinite(
                shot_camera("leader",1.,7.2,event_fraction=bad).parallax_x))
        for bad in ((math.nan,40.),(-1.,80.),(1500.,60.),(0.,),[1.,2.]):
            with self.subTest(subject=bad), self.assertRaises(ValueError):
                shot_camera("leader",2.,7.2,subject=bad)
        with self.assertRaises(ValueError):
            shot_camera("unknown",1.,7.2)
        with self.assertRaises(ValueError):
            point_on_path(((0,0),(1,1)),float("nan"))
        with self.assertRaises(ValueError):
            point_on_path(((0,0),(1,1)),1.1)
        with self.assertRaises(ValueError):
            camera_pose("leader",1.,7.2,focus_offset=(math.nan,0.))
        with self.assertRaises(ValueError):
            camera_pose("leader",1.,7.2,focus_offset=(120.,0.))


if __name__=="__main__":
    unittest.main()
