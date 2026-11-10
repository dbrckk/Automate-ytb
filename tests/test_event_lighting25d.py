"""P5.8: real narration/physical-action light in the universal 2.5D finish."""
import math
import unittest

from PIL import Image, ImageDraw

from automate_ytb.event_lighting25d import authored_light, event_envelope
from automate_ytb.finish25d import finish_world, LOOKS


class SharedEventLightIntegrationTests(unittest.TestCase):
    def _world(self):
        image=Image.new("RGBA",(320,320),(19,30,44,255))
        art=ImageDraw.Draw(image,"RGBA")
        art.polygon([(27,180),(121,62),(232,196),(292,128),
                     (312,277),(17,275)],fill=(65,88,123,255))
        art.ellipse((73,93,208,223),fill=(100,146,181,235))
        return image

    def test_no_authored_event_retains_original_shared_world_output(self):
        baseline=self._world()
        unset=baseline.copy()
        explicit=baseline.copy()
        kwargs=dict(bounds=(16,16,304,304),look="forest",t=1.5,duration=4.5)
        finish_world(unset,**kwargs)
        finish_world(explicit,**kwargs,event_fraction=None)
        self.assertEqual(unset.tobytes(),explicit.tobytes())

    def test_time_localized_light_changes_only_world_region(self):
        image=self._world()
        start=image.copy()
        middle=image.copy()
        end=image.copy()
        params=dict(bounds=(16,16,304,304),look="forest",duration=4.5,
                    event_fraction=.55)
        finish_world(start,t=0,**params)
        finish_world(middle,t=4.5*.55,**params)
        finish_world(end,t=4.5,**params)
        self.assertEqual(start.tobytes(),end.tobytes())
        self.assertNotEqual(start.tobytes(),middle.tobytes())
        self.assertEqual(image.getpixel((6,6)),middle.getpixel((6,6)))
        self.assertEqual(image.getchannel("A").tobytes(),
                         middle.getchannel("A").tobytes())
        self.assertNotEqual(image.tobytes(),middle.tobytes())

    def test_nonphysics_cue_does_not_invent_light(self):
        self.assertEqual(event_envelope(2.,6.,None),0.)
        self.assertEqual(event_envelope(0.,6.,.5),0.)
        self.assertEqual(event_envelope(6.,6.,.5),0.)
        self.assertGreater(event_envelope(3.,6.,.5),.99)
        self.assertIsNone(authored_light(width=320,height=320,
            t=3,duration=6,event_fraction=None,
            color=(255,205,170),focal_x=.5,focal_y=.5))

    def test_edge_speech_events_keep_their_original_measured_time(self):
        # A late spoken action at 93% must NOT flash at an invented 81%.
        duration=8.
        spoken=.93
        self.assertAlmostEqual(event_envelope(duration*spoken,duration,spoken),1.)
        self.assertEqual(event_envelope(duration*.81,duration,spoken),0.)
        self.assertEqual(event_envelope(0.,duration,0.),0.)
        self.assertEqual(event_envelope(duration,duration,1.),0.)

    def test_cross_topic_palettes_are_genuinely_distinct(self):
        self.assertNotEqual(LOOKS["volcano"].glow,LOOKS["forest"].glow)
        for name in ("volcano","ocean","rainbow","forest","storm","neutral"):
            look=LOOKS[name]
            cue=authored_light(width=288,height=288,t=2,duration=4,
                event_fraction=.5,color=look.glow,
                focal_x=look.focal_x,focal_y=look.focal_y)
            self.assertIsNotNone(cue)
            self.assertEqual(cue.color,look.glow)
            self.assertGreater(cue.strength,.5)

    def test_no_fake_timing_or_numerical_failure_fallback(self):
        for val in (float("nan"),float("inf"),-1.,1.2,True):
            with self.assertRaises(ValueError):
                event_envelope(2.,4.,val)
        for bad in (-1,5.,float("inf"),float("nan")):
            with self.assertRaises(ValueError):
                event_envelope(bad,4.,.5)
        with self.assertRaises(ValueError):
            authored_light(width=0,height=320,t=2,duration=4,
                event_fraction=.5,color=(255,211,192),
                focal_x=.5,focal_y=.5)


if __name__=="__main__":
    unittest.main()
