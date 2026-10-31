"""Prevent an actually static H.264 science insert from passing final review."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from production.solar_storm import review_motion


def report():
    scene_numbers=[0,0,1,1,2,2,3,3,4,4,4,5,5]
    names={1:"flare",5:"cme",7:"shield",9:"satellite",12:"connection"}
    return [{"scene":scene,"source":f"original_{names[i]}" if i in names
             else "sun171","duration":1.2,
             "source_type":"original science animation" if i in names
             else "NASA video",
             "original_science_animation":{"kind":names[i]} if i in names
             else None}
            for i,scene in enumerate(scene_numbers)]


class MasteredScienceMotionQualityTests(unittest.TestCase):
    def test_complete_final_review_accepts_five_genuinely_moving_shots(self):
        shots=report()
        with tempfile.TemporaryDirectory() as tmp:
            video=Path(tmp)/"real-master.mp4"
            video.write_bytes(b"input path verified by mock decoder")
            a=np.zeros((review_motion.H,review_motion.W,3),np.int16)
            b=np.full_like(a,75)
            with patch.object(review_motion,"_decode",
                              side_effect=[v for _ in range(5) for v in (a,b)]) as decode:
                out=review_motion.inspect_original_motion(video,shots,15.6)
                self.assertEqual(decode.call_count,10)
            self.assertEqual(out["status"],"passed")
            self.assertEqual(out["original_motion_shots"],5)
            self.assertTrue(all(x["pass"] for x in out["shots"]))
            self.assertFalse(out["editorial_approved"])

    def test_static_animation_or_inaccurate_provenance_cannot_pass(self):
        shots=report()
        with tempfile.TemporaryDirectory() as tmp:
            video=Path(tmp)/"still-master.mp4"
            video.write_bytes(b"input path verified by mock decoder")
            a=np.zeros((review_motion.H,review_motion.W,3),np.int16)
            with patch.object(review_motion,"_decode",return_value=a):
                with self.assertRaisesRegex(RuntimeError,"effectively still"):
                    review_motion.inspect_original_motion(video,shots,15.6)
            incomplete=report()
            incomplete[12]["original_science_animation"]=None
            with self.assertRaisesRegex(RuntimeError,"Expected 5"):
                review_motion.inspect_original_motion(video,incomplete,15.6)
            misleading=report()
            misleading[5]["source"]="sun171"
            with self.assertRaisesRegex(ValueError,"source attribution"):
                review_motion.inspect_original_motion(video,misleading,15.6)

    def test_missing_real_movie_is_rejected(self):
        with self.assertRaises(ValueError):
            review_motion.inspect_original_motion(
                Path("/definitely/nonexistent/test-video.mp4"),report(),15.6)


if __name__=="__main__":
    unittest.main()
