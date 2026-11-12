"""Real original transparent actor compositions across unrelated subjects.

Test artifacts are created by Pillow with original drawings; no third-party
images, network fetches, fake FFmpeg encoders or paid image-generation models.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from PIL import Image, ImageDraw, ImageChops, ImageStat

from automate_ytb.universal_actor_rig import (
    RiggedArtScene, sampled_pose, validate_actor_rig)
from automate_ytb.universal_art25d import (
    bind_actor_camera_world, load_art_scenes, render_art_stage)
from automate_ytb.universal_kinetic import frame_image, produce, read_story, timeline_for


RIGHTS="Made from scratch locally by the test author using original PIL shapes."


def layer(name, z, px, py):
    return {"file": f"original/{name}.png", "z": z,
            "parallaxX": px, "parallaxY": py,
            "material": "none", "rights": RIGHTS, "rightsConfirmed": True}


def key(at, x=0, y=0, scale=1, angle=0):
    return {"at": at, "x": x, "y": y, "scale": scale, "angle": angle}


def scene_story(topic, motions=True, links=True):
    layers=[layer("backdrop",5,.15,.08),
            layer("hero",45,1.0,.4),
            layer("other",75,1.4,.6)]
    first={
        "kind":"concept","title":"Two original subjects interact",
        "narration":"Two independently illustrated subjects approach each other as the camera follows.",
        "nodes":["Start","Approach","Connect"],"visualLayers":layers,
    }
    if motions:
        first["actorTracks"]=[
            {"z":45,"keys":[key(0,-.18,0,.78,-12),
                              key(.50,-.02,-.08,1.16,5),
                              key(1,.08,-.06,1.02,12)]},
            {"z":75,"keys":[key(0,.18,.08,.87,12),
                              key(.50,.03,-.06,1.06,-8),
                              key(1,-.06,0,.9,-17)]},
        ]
    if links:
        first["actorLinks"]=[{"fromZ":45,"toZ":75,"at":.54}]
    return {
        "schemaVersion":1,"topic":topic,"language":"en",
        "beats":[first, {
            "kind":"sequence","title":"The next causal stage",
            "narration":"The original demonstration continues toward a clearly defined final outcome.",
            "steps":["Observe","Verify","Deliver"],
        }],
    }


def original_assets(folder):
    folder.mkdir(parents=True,exist_ok=True)
    bg=Image.new("RGBA",(480,460),(14,28,56,255))
    d=ImageDraw.Draw(bg)
    for i in range(0,460,8):
        d.line((0,i,480,i),fill=(18+i//33,33+i//16,69+i//10,255))
    d.ellipse((300,50,420,170),fill=(238,191,113,255))
    bg.save(folder/"backdrop.png")
    hero=Image.new("RGBA",(480,460))
    d=ImageDraw.Draw(hero)
    d.ellipse((96,167,226,297),fill=(240,137,88,255),
              outline=(254,223,181,255),width=12)
    d.polygon([(161,105),(186,180),(138,180)],fill=(231,181,96,255))
    hero.save(folder/"hero.png")
    other=Image.new("RGBA",(480,460))
    d=ImageDraw.Draw(other)
    d.rounded_rectangle((262,200,396,331),radius=39,fill=(66,190,191,255),
                        outline=(175,245,235,255),width=8)
    d.ellipse((299,245,360,295),fill=(217,247,226,255))
    other.save(folder/"other.png")


class AuthoredActorRigTests(unittest.TestCase):
    def test_motion_parameter_safety_and_interaction_validation(self):
        art=scene_story("A free technology explainer")["beats"][0]
        valid,edges=validate_actor_rig(
            art["actorTracks"],art["actorLinks"],art["visualLayers"])
        self.assertEqual(len(valid),2)
        self.assertEqual(len(edges),1)
        self.assertEqual({t["z"] for t in valid},{45,75})
        for broken in (
                [{"z":45,"keys":[key(0),key(1,x=1.2)]}],
                [{"z":5,"keys":[key(0),key(1,x=.1)]}],
                [{"z":45,"keys":[key(0),key(.5),key(.4),key(1)]}],
                [{"z":45,"keys":[key(0),key(1,angle=float("nan"))]}],
                [{"z":45,"keys":[key(0),key(1,scale=True)]}],
                [{"z":45,"keys":[key(0),key(1,x=.2)]},
                 {"z":45,"keys":[key(0),key(1,x=.3)]}],
                [{"z":45,"keys":[key(0),key(1)]}],
                [{"z":99,"keys":[key(0),key(1,x=.1)]}]):
            with self.subTest(broken=broken),self.assertRaises(ValueError):
                validate_actor_rig(broken,[],art["visualLayers"])
        for bad in (
                [{"fromZ":45,"toZ":45,"at":.5}],
                [{"fromZ":45,"toZ":99,"at":.5}],
                [{"fromZ":45,"toZ":75,"at":float("inf")}],
                [{"fromZ":45,"toZ":75,"at":True}]):
            with self.subTest(link=bad),self.assertRaises(ValueError):
                validate_actor_rig(art["actorTracks"],bad,art["visualLayers"])

    def test_joint_pivots_are_bounded_and_survive_normalization(self):
        art=scene_story("A generic articulated illustration")["beats"][0]
        art["actorTracks"][0]["pivot"]=[.5,.95]
        tracks,_=validate_actor_rig(
            art["actorTracks"],art["actorLinks"],art["visualLayers"])
        self.assertEqual(tracks[0]["pivot"],[.5,.95])
        for pivot in ([1.2,.5],[-.1,.5],[float("nan"),.5],
                      [True,.5],["0.5",.5],[.5],(.5,.5)):
            art["actorTracks"][0]["pivot"]=pivot
            with self.subTest(pivot=pivot),self.assertRaises(ValueError):
                validate_actor_rig(
                    art["actorTracks"],art["actorLinks"],art["visualLayers"])

    def test_rotating_offcentre_joint_keeps_the_attachment_fixed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            original_assets(root/"original")
            story=scene_story("A simple joint")
            rig=story["beats"][0]["actorTracks"][0]
            rig["pivot"]=[.5,1.]
            rig["keys"]=[key(0,0,0,1,0),key(1,0,0,1,55)]
            path=root/"story.json"
            path.write_text(json.dumps(story),encoding="utf8")
            scenes,_=load_art_scenes(read_story(path),path,360,640)
            a=render_art_stage(scenes[0],0,0,90)
            b=render_art_stage(scenes[0],89,0,90)
            self.assertNotEqual(a.tobytes(),b.tobytes())
            self.assertEqual(render_art_stage(scenes[0],89,0,90).tobytes(),
                             b.tobytes())
            # Reusing the same picture with a different joint across cuts
            # is rejected rather than creating a discontinuous hinge.
            beat=story["beats"][0]
            after=json.loads(json.dumps(beat))
            for track in after["actorTracks"]:
                track["keys"][0]=dict(track["keys"][-1],at=0)
                track["keys"][-1]=dict(track["keys"][-1],at=1,x=.03)
            after["actorTracks"][0]["pivot"]=[.5,.25]
            story["beats"]=[beat,after]
            path.write_text(json.dumps(story),encoding="utf8")
            with self.assertRaisesRegex(ValueError,"pivot"):
                read_story(path)

    def test_random_access_and_transform_easing(self):
        keys=[key(0,-.2,0,.8,-10),key(.5,0,-.1,1.0,0),
              key(1,.2,0,1.2,10)]
        a=sampled_pose(keys,.25)
        self.assertAlmostEqual(a["x"],-.1)
        self.assertAlmostEqual(a["scale"],.9)
        self.assertEqual(sampled_pose(keys,.25),a)
        self.assertEqual(sampled_pose(keys,1)["angle"],10)
        for invalid in (-.1,1.1,float("nan")):
            with self.subTest(phase=invalid),self.assertRaises(ValueError):
                sampled_pose(keys,invalid)

    def test_real_original_multilayer_subject_animations_and_links(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            original_assets(root/"original")
            for topic in ("The journey of a food ingredient",
                          "An original satellite encounter"):
                with self.subTest(topic=topic):
                    request=root/"scene.json"
                    request.write_text(json.dumps(scene_story(topic)),encoding="utf8")
                    story=read_story(request)
                    scenes,provenance=load_art_scenes(story,request,360,640)
                    self.assertEqual(len(provenance),3)
                    self.assertIsInstance(scenes[0],RiggedArtScene)
                    self.assertEqual(len(scenes[0].tracks),2)
                    self.assertEqual(len(scenes[0].links),1)
                    a=render_art_stage(scenes[0],10,0,90)
                    b=render_art_stage(scenes[0],45,0,90)
                    c=render_art_stage(scenes[0],80,0,90)
                    self.assertEqual(a.mode,"RGBA")
                    self.assertNotEqual(a.tobytes(),b.tobytes())
                    self.assertNotEqual(b.tobytes(),c.tobytes())
                    self.assertEqual(render_art_stage(scenes[0],45,0,90).tobytes(),
                                     b.tobytes())
                    timeline=timeline_for(story,[0,90,180])
                    contacts=[x for x in timeline.audio_events()
                              if x["family"]=="contact"]
                    self.assertEqual(len(contacts),1)
                    self.assertLessEqual(abs(contacts[0]["atFrame"]-48),1)
                    self.assertEqual(contacts[0]["atSample"],
                                     contacts[0]["atFrame"]*1600)
                    frame=frame_image(story,timeline,[0,90,180],45,360,640,
                                      art_scenes=scenes)
                    self.assertEqual(frame.size,(360,640))
                    orig=scenes[0].links
                    scenes[0].links=()
                    self.assertNotEqual(b.tobytes(),
                                        render_art_stage(scenes[0],45,0,90).tobytes())
                    scenes[0].links=orig

    def test_cross_scene_audio_budget_rejected_before_media_io(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            # No real artwork or encoder needed: reject invalid complexity
            # before expensive source I/O and before Foley reaches its cap.
            one=scene_story("Generic original motion")["beats"][0]
            one["actorLinks"]=[{"fromZ":45,"toZ":75,"at":.12+i*.12}
                               for i in range(6)]
            data={"schemaVersion":1,"topic":"Too many causal links",
                  "language":"en","beats":[one for _ in range(12)]}
            path=root/"too-many-events.json"
            path.write_text(json.dumps(data),encoding="utf8")
            with self.assertRaisesRegex(ValueError,"audio cues"):
                read_story(path)

    def test_same_original_subject_continues_without_camera_cut_jump(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            original_assets(root/"original")
            data=scene_story("A continued original story")
            before=data["beats"][0]
            after=json.loads(json.dumps(before))
            after["title"]="The same two objects continue on screen"
            after["narration"]="Both original objects retain their positions while the camera follows their next movement."
            for track in after["actorTracks"]:
                start_pose=dict(track["keys"][-1])
                start_pose["at"]=0
                end_pose=dict(start_pose)
                end_pose["at"]=1
                end_pose["x"]-=.07
                track["keys"]=[start_pose,end_pose]
            data["beats"]=[before,after]
            path=root/"story.json"
            path.write_text(json.dumps(data),encoding="utf8")
            parsed=read_story(path)
            scenes,_=load_art_scenes(parsed,path,360,640)
            groups=bind_actor_camera_world(parsed,scenes,[0,90,180])
            self.assertEqual(len(groups),1)
            self.assertEqual(scenes[0].camera_window,(0,180))
            self.assertEqual(scenes[1].camera_window,(0,180))
            a=render_art_stage(scenes[0],89,0,90)
            b=render_art_stage(scenes[1],90,90,180)
            delta=ImageChops.difference(a,b).convert("RGB")
            self.assertLess(sum(ImageStat.Stat(delta).mean)/3,9.0)
            # A repeated actor cannot teleport across a narrated cut.
            data["beats"][1]["actorTracks"][0]["keys"][0]["x"]+=.12
            path.write_text(json.dumps(data),encoding="utf8")
            with self.assertRaisesRegex(ValueError,"jump"):
                read_story(path)

    def test_unapproved_or_opaque_actor_art_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            original_assets(root/"original")
            story=scene_story("A valid original visual")
            story["beats"][0]["actorTracks"][0]["z"]=5
            path=root/"story.json"
            path.write_text(json.dumps(story),encoding="utf8")
            with self.assertRaises(ValueError):
                read_story(path)
            story=scene_story("A valid original visual")
            story["beats"][0]["actorTracks"][0]["z"]=45
            opaque=Image.new("RGBA",(480,460),(200,50,20,255))
            opaque.save(root/"original"/"hero.png")
            path.write_text(json.dumps(story),encoding="utf8")
            with self.assertRaisesRegex(ValueError,"transparency"):
                load_art_scenes(read_story(path),path,360,640)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe")
                         and (shutil.which("espeak") or shutil.which("espeak-ng")),
                         "Open media encoders or speech binary unavailable")
    def test_real_encoded_9_16_mp4_with_original_actor_actions(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            original_assets(root/"original")
            req=root/"scene.json"
            req.write_text(json.dumps(scene_story("A test of cause and effect")),
                           encoding="utf8")
            target=root/"authored-actors.mp4"
            report=produce(req,target,width=720,voice="espeak")
            self.assertEqual(report["delivery"]["status"],"passed")
            self.assertGreater(target.stat().st_size,10000)
            self.assertEqual(report["artwork"]["authoredActionActors"],2)
            self.assertEqual(report["artwork"]["authoredActorLinks"],1)
            self.assertEqual(report["authoredContactCues"],1)
            self.assertFalse(report["publicationApproved"])
            self.assertTrue(target.with_suffix(".srt").is_file())


if __name__=="__main__":
    unittest.main()
