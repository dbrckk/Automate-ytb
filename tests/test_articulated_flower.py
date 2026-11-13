"""Behavioral checks for independent petal motion and the shared AV clock."""
from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave
from array import array

from automate_ytb.universal_actor_rig import (
    actor_key_frames, fit_actor_camera, resolved_actor_geometry,
    sampled_frame_pose, validate_actor_cues, validate_actor_rig)
from automate_ytb.universal_art25d import load_art_scenes, bind_actor_camera_world
from automate_ytb.universal_kinetic import read_story, timeline_for
from automate_ytb.universal_score import write_score
from automate_ytb.universal_vector_art import validate_vector_layers

EXAMPLES = Path(__file__).resolve().parents[1]/"examples"
spec = importlib.util.spec_from_file_location("flower_pilot", EXAMPLES/"build_articulated_flower_pilot.py")
pilot = importlib.util.module_from_spec(spec)
with patch.object(sys, "path", [str(EXAMPLES), *sys.path]):
    spec.loader.exec_module(pilot)


class ArticulatedFlowerTests(unittest.TestCase):
    def load(self, story):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"story.json"
            p.write_text(json.dumps(story,separators=(",",":")),encoding="utf8")
            return read_story(p)

    def test_limits_accept_ten_distinct_layers_and_nine_actors(self):
        s=self.load(pilot.story())
        self.assertEqual(len(s["beats"][0]["visualVectors"]),10)
        self.assertEqual(len(s["beats"][0]["actorTracks"]),9)
        layers=deepcopy(pilot.layers())
        extra=deepcopy(layers[-1]); extra.update(id="extra-heart",z=99)
        with self.assertRaisesRegex(ValueError,"ten"):
            validate_vector_layers(layers+[extra])
        with self.assertRaisesRegex(ValueError,"sixteen"):
            validate_vector_layers(layers,[{"z":i} for i in range(7)])
        tracks=deepcopy(s["beats"][0]["actorTracks"])
        extra=deepcopy(tracks[-1]); extra["z"]=99
        with self.assertRaisesRegex(ValueError,"9 actors"):
            validate_actor_rig(tracks+[extra],[],layers)

    def test_cues_reject_invalid_stationary_terminal_and_duplicate_references(self):
        s=self.load(pilot.story())
        tracks=s["beats"][1]["actorTracks"]
        good={"z":45,"keyIndex":1,"family":"growth","gainDb":-30}
        for bad in (dict(good,z=999),dict(good,z=True),dict(good,keyIndex=True),
                    dict(good,keyIndex=-1),dict(good,keyIndex=3),dict(good,keyIndex=0),
                    dict(good,family=[]),dict(good,family="unknown"),
                    dict(good,gainDb=float("nan")),dict(good,gainDb=True),
                    dict(good,gainDb=1),dict(good,unexpected=1)):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                validate_actor_cues([bad],tracks)
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            validate_actor_cues([good,good],tracks)
        with self.assertRaisesRegex(ValueError,"collapse"):
            actor_key_frames([{"at":0},{"at":.001},{"at":1}],0,30)

    def test_actor_cues_follow_real_interpolated_properties_and_pcm_samples(self):
        s=self.load(pilot.story()); bounds=[0,181,422,610]
        timeline=timeline_for(s,bounds)
        cues=[e for e in timeline.audio_events() if e["id"].startswith("cue-actor-01")]
        self.assertEqual(len(cues),5)
        self.assertEqual(len(set(c["atFrame"] for c in cues)),5)
        for cue in cues:
            z=int(cue["sourceObjectId"].split("-")[-1])
            actor=next(t for t in s["beats"][1]["actorTracks"] if t["z"]==z)
            start=cue["atFrame"]
            self.assertEqual(start,181+round(actor["keys"][1]["at"]*241))
            self.assertEqual(cue["atSample"],start*1600)
            for f in (start,start+1,start+20,421):
                pose=sampled_frame_pose(actor["keys"],f,181,422)
                state=timeline.state_at(f)["objects"][cue["sourceObjectId"]]
                self.assertAlmostEqual(state["rotation"],pose["angle"],places=8)
                self.assertAlmostEqual(state["scale"],pose["scale"],places=8)

    def test_global_cue_budget_fails_before_render(self):
        s=pilot.story()
        # Repeated standalone opening scenes with unique identities avoid
        # intentionally introducing a continuity error in this budget test.
        opening=deepcopy(s["beats"][1])
        for t in opening["actorTracks"]:
            if t["z"] in (45,50,55,60,65):
                opening["actorCues"].append({"z":t["z"],"keyIndex":2,
                                             "family":"growth","gainDb":-30})
        s["beats"]=[deepcopy(opening) for _ in range(6)]
        # Removing artwork avoids the file-size limit: use validators directly
        # for the individual cue set, then compact the fixture shapes.
        for beat in s["beats"]:
            for layer in beat["visualVectors"]:
                layer["shapes"]=layer["shapes"][:1]
        with self.assertRaisesRegex(ValueError,"Too many event"):
            self.load(s)

    def test_independent_petals_fixed_root_and_safe_framing(self):
        with tempfile.TemporaryDirectory() as td:
            p=pilot.build(Path(td)); s=read_story(p)
            scenes,_=load_art_scenes(s,p,360,640)
            bounds=[0,90,210,300]
            self.assertEqual(len(bind_actor_camera_world(s,scenes,bounds)),1)
            samples={}
            for beat in range(3):
                for frame in range(bounds[beat],bounds[beat+1],9):
                    captured=[]
                    def capture(**kwargs):
                        g=resolved_actor_geometry(**kwargs)
                        captured.append(g)
                        return g
                    def framing(size,geometry,phase,overscan):
                        crop=fit_actor_camera(size,geometry,phase,overscan)
                        left,top,w,h=crop
                        for g in geometry.values():
                            a=math.radians(g["angle"]); sw,sh=g["spriteSize"]
                            rx=(abs(math.cos(a))*sw+abs(math.sin(a))*sh)/2
                            ry=(abs(math.sin(a))*sw+abs(math.cos(a))*sh)/2
                            x,y=g["centre"]
                            self.assertGreaterEqual(x-rx,left-1)
                            self.assertLessEqual(x+rx,left+w+1)
                            self.assertGreaterEqual(y-ry,top-1)
                            self.assertLessEqual(y+ry,top+h+1)
                        return crop
                    with patch("automate_ytb.universal_actor_rig.resolved_actor_geometry",side_effect=capture), \
                         patch("automate_ytb.universal_actor_rig.fit_actor_camera",side_effect=framing):
                        scenes[beat].render(frame,bounds[beat],bounds[beat+1])
                    samples[frame]=captured
            root=samples[0][0]["joint"]
            for geometry in samples.values():
                self.assertEqual(geometry[0]["joint"],root)
            # Relative-to-heart distances/angles change with camera factored out.
            a,b=samples[90],samples[198]
            for i in range(3,8):
                va=tuple(a[i]["centre"][j]-a[-1]["centre"][j] for j in (0,1))
                vb=tuple(b[i]["centre"][j]-b[-1]["centre"][j] for j in (0,1))
                self.assertGreater(math.dist(va,vb),8)
            self.assertEqual(scenes[1].render(150,90,210).tobytes(),
                             scenes[1].render(150,90,210).tobytes())

    def test_stereo_score_is_continuous_bounded_and_reproducible(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a.wav",Path(td)/"b.wav"
            write_score(a,[0,30,60,90]); write_score(b,[0,30,60,90])
            self.assertEqual(a.read_bytes(),b.read_bytes())
            with wave.open(str(a)) as wav:
                self.assertEqual((wav.getnchannels(),wav.getframerate(),wav.getnframes()),(2,48000,144000))
                pcm=array("h",wav.readframes(wav.getnframes()))
            if sys.byteorder!="little": pcm.byteswap()
            self.assertLess(max(abs(v) for v in pcm),5000)
            self.assertNotEqual(pcm[::2],pcm[1::2])
            for boundary in (48000,96000):
                self.assertLess(abs(pcm[boundary*2]-pcm[(boundary-1)*2]),200)
            for invalid in ([0,30,30],[0,True,90],[1,30,90],[0,30,999999]):
                with self.assertRaises(ValueError): write_score(a,invalid)


if __name__=="__main__": unittest.main()
