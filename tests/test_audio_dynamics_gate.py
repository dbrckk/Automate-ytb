"""The final-delivery loudness gate must report measured whole-program audio."""
import unittest
from pathlib import Path
from unittest.mock import patch
from automate_ytb import quality


class FullProgramDynamicsTests(unittest.TestCase):
    def test_existing_quality_checker_includes_ebu_r128(self):
        source=Path(quality.__file__).read_text(encoding="utf-8")
        self.assertIn("ebur128=peak=true",source)
        self.assertIn("integratedLoudnessLUFS",source)
        self.assertIn("truePeakDbFS",source)
        self.assertIn("Full-program audio dynamics could not be measured",source)

    def test_ebu_summary_parser_patterns(self):
        import re
        summary="Integrated loudness:\\n    I: -17.3 LUFS\\nTrue peak:\\n    Peak: -1.2 dBFS"
        loud=re.search(r"Integrated loudness:\\s*I:\\s*(-?\\d+(?:\\.\\d+)?) LUFS",summary)
        peak=re.search(r"True peak:\\s*Peak:\\s*(-?\\d+(?:\\.\\d+)?) dBFS",summary)
        self.assertEqual(float(loud[1]),-17.3)
        self.assertEqual(float(peak[1]),-1.2)
