"""Loop-safe jump dynamics for animated original characters."""
import math
import unittest
from automate_ytb.choreography import body_position, CHOREOGRAPHY_VERSION


def ff_eval(expr, t):
    safe={"t":t,"mod":lambda a,b:a%b,"min":min,"max":max,
          "sin":math.sin,"abs":abs,"pow":pow,"exp":math.exp}
    return eval(expr,{"__builtins__":{}},safe)


class ContinuousJumpTests(unittest.TestCase):
    def test_jump_lands_without_boundary_teleport(self):
        self.assertIn("v8",CHOREOGRAPHY_VERSION)
        x,y=body_position("jump",x=180,y=184)
        for edge in (0.0,1.75,3.5):
            self.assertAlmostEqual(ff_eval(y,edge),184,places=5)
        self.assertLess(abs(ff_eval(y,1.75-0.001)-ff_eval(y,1.75+0.001)),0.05)
        self.assertLess(ff_eval(y,0.60),140)
        self.assertGreater(ff_eval(y,0.18),190)
        self.assertGreater(ff_eval(y,1.40),184)
        self.assertNotIn(";",x+y)

    def test_other_actions_unchanged(self):
        for action in ("walk","run","fly","rest"):
            self.assertNotIn("mod(t,1.75)",body_position(action,x=180,y=184)[1])
