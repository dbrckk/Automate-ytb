"""Flexible original 2.5D surfaces: deterministic hinge-safe deformation."""
from __future__ import annotations

from copy import deepcopy
import math
import unittest

from PIL import Image, ImageChops, ImageDraw

from automate_ytb.universal_deformation25d import (
    validate_deformation, warp_sway_sprite)
from automate_ytb.universal_actor_rig import (
    RiggedArtScene,validate_actor_rig,validate_cut_continuity)
from automate_ytb.scene25d import Layer25D,Scene25D


def _motion():
    return {"kind":"sway","amount":.095,"cycles":1.5,"offset":.15}


def _keys():
    return [
        {"at":0,"x":-.02,"y":0,"scale":1,"angle":-4},
        {"at":1,"x":.02,"y":0,"scale":1,"angle":4},
    ]


def _leaf():
    img=Image.new("RGBA",(100,160))
    draw=ImageDraw.Draw(img)
    draw.polygon([(43,151),(34,30),(44,9),(58,35),(57,151)],
                 fill=(83,158,116,235))
    draw.line((45,148,45,20),fill=(208,235,170,255),width=4)
    return img


class AuthoredDeformTests(unittest.TestCase):
    def test_unchanged_existing_rig_does_not_require_a_deformation(self):
        tracks,links=validate_actor_rig([{"z":40,"keys":_keys()}],[],
                                        [{"z":40}])
        self.assertNotIn("deform",tracks[0])
        self.assertEqual(links,[])

    def test_valid_finite_config_and_strict_bounded_input(self):
        expected=validate_deformation(_motion())
        self.assertEqual(expected["amount"],.095)
        self.assertIsNone(validate_deformation(None))
        for updates in (
                {"kind":"liquid"}, {"amount":0}, {"amount":.4},
                {"amount":True},{"amount":float("nan")},
                {"amount":float("inf")},{"cycles":0},{"cycles":4},
                {"offset":-1},{"offset":1.01},{"offset":None},
                {"offset":"0.5"},
        ):
            bad=dict(_motion(),**updates)
            with self.subTest(updates=updates),self.assertRaises(ValueError):
                validate_deformation(bad)
        for bad in ({},{"kind":"sway"},dict(_motion(),URL="https://bad.example"),
                    [],"sway",False):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                validate_deformation(bad)

    def test_rig_schema_safely_accepts_only_declared_flexible_geometry(self):
        spec={"z":40,"pivot":[.5,.9],"keys":_keys(),"deform":_motion()}
        tracks,_=validate_actor_rig([spec],[],[{"z":40}])
        self.assertEqual(tracks[0]["deform"],_motion())
        for bad in (None,{},dict(_motion(),cycles=0),
                    dict(_motion(),amount=1.0)):
            t=deepcopy(spec)
            t["deform"]=bad
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                validate_actor_rig([t],[],[{"z":40}])

    def test_sway_is_deterministic_and_preserves_authored_joint(self):
        img=_leaf()
        initial=img.tobytes()
        settings=_motion()
        a,pivot=warp_sway_sprite(
            img,pivot=[.5,.9],deform=settings,phase=.17)
        again,pivot2=warp_sway_sprite(
            img,pivot=[.5,.9],deform=settings,phase=.17)
        later,_=warp_sway_sprite(
            img,pivot=[.5,.9],deform=settings,phase=.37)
        self.assertEqual(a.tobytes(),again.tobytes())
        self.assertEqual(pivot,pivot2)
        self.assertNotEqual(a.tobytes(),later.tobytes())
        self.assertEqual(pivot[1],.9*img.height)
        self.assertGreater(pivot[0],img.width/2)
        self.assertEqual(img.tobytes(),initial)
        self.assertEqual(a.size,later.size)
        self.assertIsNotNone(a.getchannel("A").getbbox())
        self.assertLess(a.getchannel("A").getbbox()[2],a.width)

    def test_warp_anchor_is_pinned_at_its_original_horizontal_location(self):
        img=_leaf()
        settings={"kind":"sway","amount":.12,"cycles":1,
                  "offset":0}
        zero,p0=warp_sway_sprite(img,pivot=[.5,1.],deform=settings,phase=0)
        bent,p1=warp_sway_sprite(img,pivot=[.5,1.],deform=settings,phase=.25)
        self.assertEqual(p0,p1)
        # Zero displacement at the bottom pivot, but visible movement above.
        row=img.height-3
        alpha0=zero.getchannel("A").crop((0,row,zero.width,row+1))
        alpha1=bent.getchannel("A").crop((0,row,bent.width,row+1))
        self.assertLessEqual(abs(alpha0.getbbox()[0]-alpha1.getbbox()[0]),2)
        self.assertIsNotNone(ImageChops.difference(
            zero.getchannel("A"),bent.getchannel("A")).getbbox())

    def test_continuity_rejects_flexible_setting_changes_between_shots(self):
        first={"z":45,"pivot":[.5,.9],"keys":_keys(),"deform":_motion()}
        second=deepcopy(first)
        second["keys"]=[
            dict(first["keys"][-1],at=0),
            dict(first["keys"][-1],at=1,x=.03),
        ]
        layers=[{"file":"original.png","z":45}]
        beats=[
            {"visualLayers":layers,"visualVectors":[],"actorTracks":[first]},
            {"visualLayers":layers,"visualVectors":[],"actorTracks":[second]},
        ]
        self.assertEqual(validate_cut_continuity({"beats":beats}),1)
        beats[1]["actorTracks"][0]["deform"]["offset"]+=.1
        with self.assertRaisesRegex(ValueError,"deformation"):
            validate_cut_continuity({"beats":beats})

    def test_real_compositor_render_changes_deterministically_with_mesh(self):
        scene=Scene25D((160,240))
        bg=Layer25D("backdrop",5,Image.new("RGBA",(160,240),(18,31,47,255)))
        foreground=Image.new("RGBA",(160,240))
        foreground.alpha_composite(_leaf(),(30,32))
        hero=Layer25D("flexible-leaf",45,foreground)
        scene.add(bg)
        scene.add(hero)
        track={"z":45,"pivot":[.5,1],"keys":_keys(),"deform":_motion()}
        validated,_=validate_actor_rig([track],[],[{"z":45}])
        artwork=RiggedArtScene(scene,[bg,hero],validated,[])
        first=artwork.render(12,0,90)
        second=artwork.render(48,0,90)
        self.assertEqual(first.mode,"RGBA")
        self.assertEqual(first.size,(160,240))
        self.assertNotEqual(first.tobytes(),second.tobytes())
        self.assertEqual(first.tobytes(),artwork.render(12,0,90).tobytes())


if __name__=="__main__":
    unittest.main()
