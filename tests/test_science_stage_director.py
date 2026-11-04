"""Cinematic science camera is continuous, crop-safe, content preserving."""
import unittest
from PIL import Image, ImageChops
from automate_ytb.science_stage_director import FRAME_SIZE, SHOTS, VERSION, ACTION_CUES, EVENT_PROGRESS, camera_progress, action_envelope, pose, reframe


class ScienceDirectorTests(unittest.TestCase):
    def test_every_authored_shot_has_continuous_valid_crop(self):
        self.assertIn("science-director",VERSION)
        self.assertEqual(FRAME_SIZE,(1080,1380))
        for topic,beats in SHOTS.items():
            for beat in beats:
                with self.subTest(topic=topic,beat=beat):
                    previous=None
                    for frame in range(211):
                        t=frame/30
                        z,cx,cy=pose(topic,beat,t,7)
                        half_w,half_h=540/z,690/z
                        self.assertGreater(z,1.0)
                        self.assertGreaterEqual(cx-half_w,-1.e-6)
                        self.assertLessEqual(cx+half_w,1080+1.e-6)
                        self.assertGreaterEqual(cy-half_h,-1.e-6)
                        self.assertLessEqual(cy+half_h,1380+1.e-6)
                        if previous:
                            # Gentle travel, no jerky per-frame camera snap.
                            self.assertLess(abs(z-previous[0]),.009)
                            self.assertLess(abs(cx-previous[1]),4)
                            self.assertLess(abs(cy-previous[2]),8)
                        previous=z,cx,cy

    def test_deterministic_reframing_without_stretch_or_transparency(self):
        image=Image.new("RGBA",FRAME_SIZE,(20,30,50,255))
        d=__import__("PIL.ImageDraw",fromlist=["Draw"]).Draw(image)
        d.ellipse((355,400,555,600),fill=(220,90,34,255))
        first=reframe(image,"volcano","magma",0,7)
        again=reframe(image,"volcano","magma",0,7)
        last=reframe(image,"volcano","magma",7,7)
        self.assertEqual(first.size,FRAME_SIZE)
        self.assertEqual(first.getchannel("A").getextrema(),(255,255))
        self.assertEqual(first.tobytes(),again.tobytes())
        # Alpha remains 255: compare RGB, otherwise Pillow's getbbox() on
        # an RGBA difference incorrectly reports None (zero alpha difference).
        self.assertIsNotNone(ImageChops.difference(
            first.convert("RGB"),last.convert("RGB")).getbbox())
        self.assertEqual(first.getpixel((0,0))[3],255)

    def test_solar_wind_keeps_both_celestial_bodies_visible(self):
        # With Sun centre 214 radius 128, Earth centre 930 radius 102,
        # both must remain inside the scene even during the moving push.
        for frame in range(211):
            z, cx, cy = pose("aurora", "solar_wind", frame/30, 7)
            src_left=cx-540/z
            sun_left=(214-128-src_left)*z
            earth_right=(930+102-src_left)*z
            self.assertGreater(sun_left,10)
            self.assertLess(earth_right,1078)

    def test_invalid_camera_inputs_fail_explicitly(self):
        stage=Image.new("RGBA",FRAME_SIZE)
        for topic,beat,t,dur in (
            ("unknown","magma",0,7),("volcano","unknown",0,7),
            ("aurora","curtains",-1,7),("aurora","curtains",8,7),
            ("volcano","magma",0,float("nan")),
            ("volcano","magma",0,0)):
            with self.assertRaises(ValueError):
                pose(topic,beat,t,dur)
        with self.assertRaises(ValueError):
            reframe(Image.new("RGB",FRAME_SIZE),"volcano","magma",0,7)
        with self.assertRaises(ValueError):
            reframe(Image.new("RGBA",(1080,930)),"volcano","magma",0,7)

    def test_event_emphasis_is_localized_and_has_no_scene_boundary_jump(self):
        self.assertEqual(set(SHOTS),set(ACTION_CUES))
        for topic, beats in SHOTS.items():
            self.assertEqual(set(beats),set(ACTION_CUES[topic]))
            for beat in beats:
                with self.subTest(topic=topic,beat=beat):
                    center, push, _, _, width = ACTION_CUES[topic][beat]
                    self.assertGreater(action_envelope(topic,beat,center),.99)
                    self.assertEqual(action_envelope(topic,beat,0),0)
                    self.assertEqual(action_envelope(topic,beat,1),0)
                    self.assertEqual(action_envelope(topic,beat,max(0,center-width)),0)
                    self.assertEqual(action_envelope(topic,beat,min(1,center+width)),0)
                    start,end=pose(topic,beat,0,7),pose(topic,beat,7,7)
                    self.assertAlmostEqual(start[0],beats[beat][0])
                    self.assertAlmostEqual(end[0],beats[beat][1])
                    # The camera must be visibly distinct from simple smoothstep.
                    middle=pose(topic,beat,center*7,7)[0]
                    q=center
                    baseline=beats[beat][0]+(beats[beat][1]-beats[beat][0])*camera_progress(topic,beat,q)
                    self.assertGreater(middle-baseline,push*.95)

    def test_causal_camera_is_monotone_continuous_and_not_generic(self):
        self.assertEqual(set(EVENT_PROGRESS), set(SHOTS))
        authored_differences = []
        for topic, beats in EVENT_PROGRESS.items():
            self.assertEqual(set(beats), set(SHOTS[topic]))
            for beat, knots in beats.items():
                with self.subTest(topic=topic, beat=beat):
                    self.assertEqual(knots[0], (0., 0.))
                    self.assertEqual(knots[-1], (1., 1.))
                    self.assertTrue(all(
                        a[0] < b[0] and a[1] < b[1]
                        for a, b in zip(knots, knots[1:])))
                    progress = [camera_progress(topic,beat,i/600)
                                for i in range(601)]
                    self.assertEqual(progress[0], 0.)
                    self.assertEqual(progress[-1], 1.)
                    self.assertTrue(all(0 <= a <= b <= 1
                                        for a,b in zip(progress,progress[1:])))
                    self.assertLess(max(b-a for a,b in zip(progress,progress[1:])), .009)
                    for x,_ in knots[1:-1]:
                        # Velocity is zero at both sides of each authored knot.
                        self.assertLess(
                            camera_progress(topic,beat,x+.00001)
                            - camera_progress(topic,beat,x-.00001), .0001)
                    for q in (.2,.4,.6,.8):
                        generic=q*q*(3-2*q)
                        authored_differences.append(abs(camera_progress(topic,beat,q)-generic))
        self.assertGreater(max(authored_differences), .05)

    def test_invalid_causal_camera_clock_is_rejected(self):
        for value in (-1, 1.01, float("nan"), float("inf"), True, "0.5"):
            with self.assertRaises(ValueError):
                camera_progress("volcano","eruption",value)
        with self.assertRaises(ValueError):
            camera_progress("unsupported","eruption",.5)

    def test_invalid_event_envelopes_fail(self):
        for value in (-1,1.1,float("nan"),float("inf")):
            with self.assertRaises(ValueError):
                action_envelope("volcano","eruption",value)
        with self.assertRaises(ValueError):
            action_envelope("unknown","eruption",.5)

    def test_synced_camera_follows_measured_phrase_position(self):
        domain, beat="volcano","eruption"
        center=.68
        t=center*7
        with_audio=pose(domain,beat,t,7,event_progress=center)
        without=pose(domain,beat,t,7)
        self.assertNotEqual(with_audio,without)
        self.assertAlmostEqual(
            action_envelope(domain,beat,center,event_progress=center),1)
        self.assertLess(
            action_envelope(domain,beat,.1,event_progress=center),.001)
        for bad in (-.2,1.1,float("inf"),float("nan"),"0.5"):
            with self.assertRaises(ValueError):
                pose(domain,beat,2,7,event_progress=bad)
        # Time-locked change must preserve the same first/last poses.
        self.assertEqual(pose(domain,beat,0,7),pose(domain,beat,0,7,event_progress=center))
        self.assertEqual(pose(domain,beat,7,7),pose(domain,beat,7,7,event_progress=center))
