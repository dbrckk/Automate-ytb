"""Actual cinematic kinetic stage regression; no mocked rendered frames.

Different source-authored topics share the same rendering contract. These
tests check temporal stability, grounded measurements and portrait-safe frames.
"""
from __future__ import annotations

from decimal import Decimal
import unittest

from automate_ytb.universal_motion25d import VERSION, render_stage, _decimal_label

PALETTE=((10,17,38),(26,49,78),(245,172,115),(126,222,223))


def beat(kind):
    basic={"title":"Original scene","narration":"These original words describe the real scene.",
           "kind":kind}
    if kind=="measure":
        return dict(basic,label="Authenticated sample budget",
                    value=Decimal("760"),scaleMax=Decimal("1000"),unit="ms")
    if kind=="compare":
        return dict(basic,left="Scenario Alpha",right="Scenario Beta",
                    leftValue=Decimal("120"),rightValue=Decimal("310"),unit="ms")
    if kind=="sequence":
        return dict(basic,items=["Extract","Transform","Validate","Deliver"])
    return dict(basic,items=["Client","Protocol","Server","Response"])


class CinematicMotionStageTests(unittest.TestCase):
    def sample(self, kind, frame, *, ratio=None, size=(320,320)):
        return render_stage(beat=beat(kind),frame=frame,
                            first=0,last=90,width=size[0],height=size[1],
                            palette=PALETTE,value_ratio=ratio)

    def test_all_four_visual_grammars_have_original_frame_motion(self):
        self.assertIn("cinematic",VERSION)
        for kind in ("measure","compare","sequence","concept"):
            with self.subTest(kind=kind):
                def image(f):
                    return self.sample(kind,f,ratio=f/90 if kind=="measure" else None)
                a,b,c=image(4),image(30),image(67)
                self.assertEqual(a.size,(320,320))
                self.assertEqual(a.mode,"RGB")
                self.assertNotEqual(a.tobytes(),b.tobytes())
                self.assertNotEqual(b.tobytes(),c.tobytes())
                self.assertEqual(image(30).tobytes(),b.tobytes())

    def test_data_drives_both_quantity_and_geometry(self):
        # The same authored source max yields a fixed output at a fixed ratio.
        before=self.sample("measure",30,ratio=.2)
        after=self.sample("measure",30,ratio=.8)
        self.assertNotEqual(before.tobytes(),after.tobytes())
        self.assertEqual(self.sample("measure",30,ratio=.8).tobytes(),
                         after.tobytes())
        self.assertEqual(_decimal_label(Decimal("12345678900000000000000000000")),
                         "1.235e28")
        self.assertEqual(_decimal_label(Decimal("0.012345")),"0.01")

    def test_long_labels_do_not_break_small_preview(self):
        long_label="A historical event with a deliberately long original authored description"
        for kind in ("measure","compare","sequence","concept"):
            b=beat(kind)
            if kind=="measure":
                b["label"]=long_label
            if kind=="compare":
                b["left"]=long_label
            if kind=="sequence" or kind=="concept":
                b["items"]=[long_label,"Other detailed original input"]
            with self.subTest(kind=kind):
                a=render_stage(beat=b,frame=30,first=0,last=90,
                               width=160,height=200,palette=PALETTE,
                               value_ratio=.4 if kind=="measure" else None)
                self.assertEqual(a.size,(160,200))

    def test_invalid_unbound_state_and_dimensions_fail(self):
        for frame in (-1,90,1.2):
            with self.subTest(frame=frame),self.assertRaises(ValueError):
                self.sample("concept",frame)
        for ratio in (None,float("nan"),float("inf"),-1,2,True):
            with self.subTest(ratio=ratio),self.assertRaises(ValueError):
                self.sample("measure",30,ratio=ratio)
        with self.assertRaises(ValueError):
            self.sample("concept",30,size=(120,320))


if __name__=="__main__":
    unittest.main()
