"""Deterministic authored hierarchy for original articulated 2.5D subjects.

Connections refer to approved transparent source layers. Attached children
inherit the parent's actual local-to-world transform. Camera parallax affects
the root assembly only. No anatomy or object part is inferred.
"""
from __future__ import annotations

import math

VERSION = "authored-2d-joint-tree-v1"
MAX_ASSEMBLY_SCALE = 2.25


def rotate_screen(dx: float, dy: float, degrees: float) -> tuple[float, float]:
    """Positive Pillow angles rotate CCW, though screen +y points down."""
    angle=math.radians(degrees)
    c,s=math.cos(angle),math.sin(angle)
    return dx*c+dy*s, -dx*s+dy*c


def validate_joint_tree(tracks: list[dict]) -> None:
    """Fail closed on unknown parents, inverted depth and explosive scale."""
    by_z={t["z"]: t for t in tracks}
    for child in tracks:
        z=child["z"]
        parent=child.get("parentZ")
        if parent is None:
            continue
        if type(parent) is not int or parent not in by_z or parent>=z:
            raise ValueError("Joint parent must be a lower-Z rigged original actor")
        if "attach" not in child:
            raise ValueError("Joint child requires an explicit parent attachment")
        scale=1.
        cursor=child
        while True:
            scale*=max(k["scale"] for k in cursor["keys"])
            if scale>MAX_ASSEMBLY_SCALE:
                raise ValueError("Unsafe inherited articulated sprite scale")
            cursor=by_z.get(cursor.get("parentZ"))
            if cursor is None:
                break


def resolved_actor_geometry(*, layer, pose: dict, pivot: list[float],
                            stage_size: tuple[int,int],
                            sprite_size: tuple[int,int],
                            camera_x: float, camera_y: float,
                            parent: dict | None=None,
                            attach: list[float] | None=None) -> dict:
    """Compute hinge, visible centre, inherited rotation and scale.

    Root x/y are stage offsets. Child x/y are local offsets along the rotated
    parent axes. Attach is the normalized point of the unrotated parent crop
    and rotates around the parent's actual hinge. All outputs are pure.
    """
    sw,sh=stage_size
    if parent is None:
        total_scale=pose["scale"]
        angle=pose["angle"]
        cx=layer[0]+camera_x*layer[2]+pose["x"]*sw
        cy=layer[1]+camera_y*layer[3]+pose["y"]*sh
        w,h=sprite_size[0]*total_scale,sprite_size[1]*total_scale
        joint=(cx+(pivot[0]-.5)*w,cy+(pivot[1]-.5)*h)
    else:
        if attach is None:
            raise ValueError("An attached child requires a parent anchor")
        total_scale=parent["totalScale"]*pose["scale"]
        angle=parent["angle"]+pose["angle"]
        pw,ph=parent["spriteSize"]
        dx=(attach[0]-parent["pivot"][0])*pw
        dy=(attach[1]-parent["pivot"][1])*ph
        ax,ay=rotate_screen(dx,dy,parent["angle"])
        ox,oy=rotate_screen(pose["x"]*sw,pose["y"]*sh,parent["angle"])
        joint=(parent["joint"][0]+ax+ox,parent["joint"][1]+ay+oy)
        w,h=sprite_size[0]*total_scale,sprite_size[1]*total_scale
    if not math.isfinite(total_scale) or total_scale>MAX_ASSEMBLY_SCALE:
        raise ValueError("Unsafe cumulative articulated scale")
    ox,oy=rotate_screen((.5-pivot[0])*w,(.5-pivot[1])*h,angle)
    centre=(joint[0]+ox,joint[1]+oy)
    return {
        "joint":joint,"centre":centre,"pivot":tuple(pivot),
        "spriteSize":(w,h),"totalScale":total_scale,
        "angle":angle,
    }
