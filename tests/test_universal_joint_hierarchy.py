"""Original subject attachments: bounded graph, parent transforms and determinism."""
from __future__ import annotations

import math
import unittest

from automate_ytb.universal_joint_hierarchy import (
    resolved_actor_geometry, rotate_screen)
from automate_ytb.universal_actor_rig import (
    validate_actor_rig, validate_cut_continuity)

def key(t, x=0., y=0., scale=1., angle=0.):
    return {"at":t, "x":x,"y":y,"scale":scale,"angle":angle}

def layers():
    return [{"z":5,"file":"background.png"},
            {"z":45,"file":"body.png"},
            {"z":70,"file":"limb.png"},
            {"z":90,"file":"tool.png"}]

def tracks():
    return [
        {"z":45,"keys":[key(0,x=-.15,angle=-10),
                        key(1,x=.14,angle=15)]},
        {"z":70,"pivot":[.5,1.],"parentZ":45,
         "attach":[.5,.31],
         "keys":[key(0,angle=-25),key(1,angle=30)]},
        {"z":90,"pivot":[.5,1.],"parentZ":70,
         "attach":[.5,.15],
         "keys":[key(0,angle=0),key(1,angle=13)]},
    ]


class OriginalJointHierarchyTests(unittest.TestCase):
    def test_validated_multilevel_hierarchy_and_random_access(self):
        checked,_=validate_actor_rig(tracks(),[],layers())
        self.assertEqual(len(checked),3)
        self.assertEqual(checked[-1]["parentZ"],70)
        self.assertEqual(checked[-1]["attach"],[.5,.15])

    def test_untrusted_parent_graph_and_relative_attach_are_rejected(self):
        for broken in (
                {"parentZ":45,"attach":[.5,1.5]},
                {"parentZ":45,"attach":[float("nan"),.5]},
                {"parentZ":45,"attach":[True,.5]},
                {"parentZ":45,"attach":(.5,.5)},
                {"parentZ":45},
                {"attach":[.5,.5]},
                {"parentZ":90,"attach":[.5,.5]},
                {"parentZ":70,"attach":[.5,.5]},
                {"parentZ":False,"attach":[.5,.5]},
                {"parentZ":99,"attach":[.5,.5]},
        ):
            t=tracks()
            t[1].pop("parentZ")
            t[1].pop("attach")
            t[1].update(broken)
            with self.subTest(broken=broken),self.assertRaises(ValueError):
                validate_actor_rig(t,[],layers())

    def test_cumulative_scale_bound_enforced_pre_render(self):
        t=tracks()
        t[0]["keys"][-1]["scale"]=1.75
        t[1]["keys"][-1]["scale"]=1.75
        with self.assertRaisesRegex(ValueError,"scale"):
            validate_actor_rig(t,[],layers())

    def test_parent_joint_follows_rotation_translation_zoom(self):
        base=dict(layer=(110.,160.,1.,.5),stage_size=(400,600),
                  sprite_size=(80,60),camera_x=30,camera_y=15,
                  pivot=[.5,.5])
        zero=resolved_actor_geometry(
            **base,pose={"x":0.,"y":0.,"scale":1.,"angle":0.})
        rotated=resolved_actor_geometry(
            **base,pose={"x":.1,"y":-.1,"scale":1.5,"angle":90.})
        def child(parent):
            return resolved_actor_geometry(
                layer=(300,400,1.6,1.3),
                pose={"x":0.,"y":0.,"scale":1.,"angle":15.},
                pivot=[.5,1.],stage_size=(400,600),
                sprite_size=(20,30),camera_x=30,camera_y=15,
                parent=parent,attach=[1.,.5])
        a,b=child(zero),child(rotated)
        self.assertAlmostEqual(a["joint"][0],zero["joint"][0]+40,places=5)
        self.assertAlmostEqual(a["joint"][1],zero["joint"][1],places=5)
        self.assertAlmostEqual(b["joint"][0],rotated["joint"][0],places=5)
        self.assertAlmostEqual(b["joint"][1],rotated["joint"][1]-60,places=5)
        self.assertAlmostEqual(b["angle"],105)
        self.assertAlmostEqual(b["totalScale"],1.5)
        self.assertNotEqual(a["centre"],b["centre"])
        self.assertEqual(b,child(rotated))

    def test_nested_joint_inherits_all_parent_rotations(self):
        root=resolved_actor_geometry(
            layer=(80,90,0,0),pose={"x":0,"y":0,"scale":1,"angle":20},
            pivot=[.5,.5],stage_size=(300,500),sprite_size=(80,80),
            camera_x=0,camera_y=0)
        elbow=resolved_actor_geometry(
            layer=(0,0,0,0),pose={"x":0,"y":0,"scale":1,"angle":30},
            pivot=[.5,1],stage_size=(300,500),sprite_size=(20,50),
            camera_x=0,camera_y=0,parent=root,attach=[.5,.5])
        hand=resolved_actor_geometry(
            layer=(0,0,0,0),pose={"x":0,"y":0,"scale":1,"angle":-15},
            pivot=[.5,1],stage_size=(300,500),sprite_size=(10,20),
            camera_x=0,camera_y=0,parent=elbow,attach=[.5,.05])
        self.assertAlmostEqual(elbow["angle"],50)
        self.assertAlmostEqual(hand["angle"],35)
        self.assertEqual(elbow["joint"],root["joint"])
        self.assertLess(hand["joint"][1],elbow["joint"][1])

    def test_preserved_parent_and_attachment_between_continuous_shots(self):
        original=tracks()
        next_tracks=tracks()
        for old,new in zip(original,next_tracks):
            first=dict(old["keys"][-1],at=0)
            end=dict(first,at=1,angle=first["angle"]+1)
            new["keys"]=[first,end]
        a={"visualLayers":layers(),"actorTracks":original}
        b={"visualLayers":layers(),"actorTracks":next_tracks}
        self.assertEqual(validate_cut_continuity({"beats":[a,b]}),1)
        b["actorTracks"][1]["attach"]=[.4,.31]
        with self.assertRaisesRegex(ValueError,"attachment"):
            validate_cut_continuity({"beats":[a,b]})

    def test_screen_rotation_convention_matches_pillow(self):
        self.assertAlmostEqual(rotate_screen(10,0,90)[1],-10)
        self.assertAlmostEqual(rotate_screen(0,-10,90)[0],-10)


if __name__=="__main__":
    unittest.main()
