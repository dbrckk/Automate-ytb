"""P3.9 geometry tests for curved anatomy with untouched world-foot IK."""
import math
import unittest
from PIL import Image,ImageDraw,ImageChops
from automate_ytb.forest_anatomical_limb25d import (
    VERSION,_curve_points,draw_anatomical_leg,
)
from automate_ytb.forest25d import character_plate
from automate_ytb.rig25d import walking_leg,GROUND
from automate_ytb.forest_contact25d import IMPACT_TIME


class AnatomicalLimbTests(unittest.TestCase):
    def test_curves_are_nonstraight_and_end_at_actual_bones(self):
        a=(180.,1200.)
        b=(235.,1255.)
        points=_curve_points(a,b,bulge=12)
        self.assertEqual(points[0],a)
        self.assertAlmostEqual(points[-1][0],b[0])
        self.assertAlmostEqual(points[-1][1],b[1])
        midpoint=points[len(points)//2]
        self.assertNotAlmostEqual(midpoint[0],(a[0]+b[0])/2)
        with self.assertRaises(ValueError):
            _curve_points(a,a,bulge=4)

    def test_curved_limb_paints_true_original_ik_targets(self):
        t=IMPACT_TIME+.21
        for kind in ("fox","rabbit","cat"):
            for side in ("left","right"):
                pose=walking_leg(t,side=side,origin_x=195.,
                                 speed=44.,torso_y=915.,ground_y=GROUND)
                image=Image.new("RGBA",(1080,1920))
                draw_anatomical_leg(ImageDraw.Draw(image),
                                   pose=pose,kind=kind,side=side)
                self.assertIsNotNone(image.getbbox())
                fx,fy=pose.foot
                self.assertGreater(image.getpixel((round(fx),round(fy)))[3],0)
                self.assertAlmostEqual(math.dist(pose.hip,pose.knee),72.)
                self.assertAlmostEqual(math.dist(pose.knee,pose.foot),72.)
        self.assertIn("p39",VERSION)

    def test_actual_characters_report_anatomical_upgrade(self):
        for kind in ("fox","rabbit","cat"):
            img,meta=character_plate(IMPACT_TIME+.21,kind=kind,
                                     interaction=True)
            self.assertEqual(img.size,(1080,1920))
            self.assertEqual(meta["anatomicalLimbs"],VERSION)
            self.assertEqual(meta["right"].foot[1],GROUND)
            self.assertGreater(meta["physicalRecoil"],0)

    def test_rejects_invalid_species_and_joint_geometry(self):
        pose=walking_leg(.3,side="left",origin_x=195.,
                         speed=44.,torso_y=915.,ground_y=GROUND)
        with self.assertRaises(ValueError):
            draw_anatomical_leg(ImageDraw.Draw(Image.new("RGBA",(1080,1920))),
                                pose=pose,kind="owl",side="left")
        with self.assertRaises(ValueError):
            draw_anatomical_leg(ImageDraw.Draw(Image.new("RGBA",(1080,1920))),
                                pose=pose,kind="fox",side="middle")


if __name__=="__main__":
    unittest.main()
