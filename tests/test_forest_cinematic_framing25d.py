"""Physical cinematic crops are real resamplings, not fake zoom metadata."""
import math
import unittest
from PIL import Image,ImageChops
from automate_ytb.forest_story25d import STORY
from automate_ytb.forest_butterfly25d import butterfly_pose
from automate_ytb.forest25d import ORIGIN_X, SPEED, TORSO_Y
from automate_ytb.rig25d import GROUND

from automate_ytb.forest_cinematic_framing25d import (
    SHOTS,SIZE,shot_crop,cinematic_reframe,VERSION,
)


class PhysicalCinematicFramingTests(unittest.TestCase):
    def test_every_shot_is_bounded_and_changes_optical_scale(self):
        sizes={}
        for name in SHOTS:
            x0,y0,x1,y1=shot_crop(2.5,beat=name,body_x=310.)
            self.assertGreaterEqual(x0,0)
            self.assertGreaterEqual(y0,0)
            self.assertLessEqual(x1,SIZE[0])
            self.assertLessEqual(y1,SIZE[1])
            self.assertLess(x1-x0,SIZE[0])
            sizes[name]=(x1-x0,y1-y0)
        self.assertGreater(sizes["discovery"][0],sizes["contact"][0])
        self.assertGreater(sizes["departure"][0],sizes["arrival"][0])

    def test_crops_track_real_actor_world_position(self):
        a=shot_crop(1.,beat="arrival",body_x=200.)
        b=shot_crop(5.,beat="arrival",body_x=500.)
        self.assertGreater(b[0],a[0])

    def test_optical_reframing_produces_real_pixels(self):
        im=Image.new("RGBA",SIZE,(25,75,110,255))
        for y in range(560,1360):
            for x in range(300,600):
                im.putpixel((x,y),(245,174,92,255))
        wide=cinematic_reframe(im,t=2.,beat="discovery",body_x=300.)
        close=cinematic_reframe(im,t=2.,beat="contact",body_x=300.)
        self.assertEqual(wide.size,SIZE)
        self.assertIsNotNone(ImageChops.difference(wide.convert("RGB"),close.convert("RGB")).getbbox())

    def test_event_camera_pushes_in_and_reveals_butterfly(self):
        for beat,start,end,*_ in STORY:
            center=(start+end)/2
            initial=shot_crop(start,beat=beat,body_x=320.)
            middle=shot_crop(center,beat=beat,body_x=320.)
            width=lambda rect:rect[2]-rect[0]
            if beat=="contact":
                self.assertLess(width(middle),width(initial))
            elif beat=="arrival":
                self.assertGreater(width(middle),width(initial))
            self.assertNotEqual(middle,initial)

    def test_dolly_has_no_abrupt_internal_frame_jumps(self):
        for beat,start,end,*_ in STORY:
            samples=[shot_crop(start+(end-start)*i/60,
                               beat=beat,body_x=320.) for i in range(61)]
            for a,b in zip(samples,samples[1:]):
                self.assertLessEqual(max(abs(x-y) for x,y in zip(a,b)),25)

    def test_p44_portrait_fills_screen_and_preserves_real_ground(self):
        self.assertIn("p44",VERSION)
        for beat,start,end,*_ in STORY:
            for q in (0.,.25,.5,.75,.999):
                t=start+(end-start)*q
                body=ORIGIN_X+SPEED*t
                x0,y0,x1,y1=shot_crop(t,beat=beat,body_x=body)
                w,h=x1-x0,y1-y0
                self.assertLess(h,1350)  # Avoid the old distant fox shot
                self.assertLess(h,SIZE[1])
                px=(body+175-x0)*SIZE[0]/w
                head_top=(TORSO_Y-y0)*SIZE[1]/h
                foot_y=(GROUND-y0)*SIZE[1]/h
                # Head, face and planted feet remain legible on a phone.
                self.assertGreater(px,380)
                self.assertLess(px,700)
                self.assertGreater(head_top,470)
                self.assertLess(head_top,830)
                self.assertGreater(foot_y,1300)
                self.assertLess(foot_y,1415) # No overlap with subtitles >=1438

    def test_contact_is_true_closeup_compared_with_discovery(self):
        opening=shot_crop(.7,beat="discovery",
                          body_x=ORIGIN_X+SPEED*.7)
        close_t=STORY[1][1]+(STORY[1][2]-STORY[1][1])/2
        contact=shot_crop(close_t,beat="contact",
                          body_x=ORIGIN_X+SPEED*close_t)
        self.assertGreater((opening[2]-opening[0])/
                           (contact[2]-contact[0]),1.13)

    def test_arrival_keeps_real_butterfly_and_face_inside_frame(self):
        name,start,end,*_=STORY[2]
        for i in range(26):
            t=start+(end-start)*i/25
            crop=shot_crop(t,beat=name,body_x=ORIGIN_X+SPEED*t)
            pose=butterfly_pose(t,origin_x=ORIGIN_X,
                                speed=SPEED,torso_y=TORSO_Y)
            self.assertTrue(pose.visible)
            # Current authored wing span is <= 66 world pixels; reserve 72.
            self.assertGreater(pose.x-72,crop[0])
            self.assertLess(pose.x+72,crop[2])

    def test_rejects_unbounded_clocks_subjects_and_fake_stages(self):
        for t in (math.nan,-1,8,True):
            with self.subTest(t=t),self.assertRaises(ValueError):
                shot_crop(t,beat="contact",body_x=300.)
        for x in (0,700,math.inf):
            with self.assertRaises(ValueError):
                shot_crop(2.,beat="contact",body_x=x)
        with self.assertRaises(ValueError):
            cinematic_reframe(Image.new("RGB",SIZE),t=2.,
                              beat="contact",body_x=300.)


if __name__=="__main__":
    unittest.main()
