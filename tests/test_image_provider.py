"""Provider calls are mocked: tests never incur cost or require API credentials."""
import io
import json
from pathlib import Path
import tempfile
import unittest
import sys
import types
from unittest.mock import patch, Mock

from PIL import Image

from automate_ytb.image_provider import generate, _request_image
from automate_ytb.production import audit, load_plan
from automate_ytb.scene_plan import plan


class ImageProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.path = self.root / "scene-plan.json"
        data = plan(topic="Original birds", script="One sentence. Two sentences. Three sentences. Four sentences. Five sentences.",
                    duration=30, character="Original violet bird", shot_seconds=6)
        self.path.write_text(json.dumps(data), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_default_dry_run_makes_zero_requests(self):
        with patch("automate_ytb.image_provider._request_image") as request:
            result = generate(plan_path=self.path, budget_usd="1",
                              max_cost_per_image_usd="0.25")
        request.assert_not_called()
        self.assertEqual(result["projectedUpperBoundUsd"], "1.2500")
        self.assertEqual(result["generated"], 0)

    def test_execute_requires_budget_rights_and_token(self):
        with patch("automate_ytb.image_provider._request_image") as request:
            with self.assertRaisesRegex(ValueError, "rights"):
                generate(plan_path=self.path, execute=True)
            with self.assertRaisesRegex(ValueError, "HF_TOKEN"):
                generate(plan_path=self.path, execute=True,
                         rights_note="Original media usage allowed.")
            with self.assertRaisesRegex(ValueError, "budget"):
                generate(plan_path=self.path, execute=True, token="test",
                         rights_note="Original media usage allowed.")
            with self.assertRaisesRegex(ValueError, "budget"):
                generate(plan_path=self.path, execute=True, token="test",
                         budget_usd="0.1", max_cost_per_image_usd="0.25",
                         rights_note="Original media usage allowed.")
        request.assert_not_called()

    def test_mocked_generation_records_estimates_and_resume(self):
        buf = io.BytesIO()
        Image.new("RGB", (640, 360), (30, 80, 130)).save(buf, "PNG")
        with patch("automate_ytb.image_provider._request_image",
                   return_value=buf.getvalue()) as request:
            result = generate(plan_path=self.path, execute=True, token="test",
                              budget_usd="0.50", max_cost_per_image_usd="0.25",
                              limit=2,
                              rights_note="Original AI images permitted for my commercial use.")
            self.assertEqual(request.call_count, 2)
            self.assertEqual(result["generated"], 2)
            self.assertTrue(result["recordedCostsAreEstimates"])
            self.assertEqual(audit(self.path)["counts"]["ready"], 2)
            again = generate(plan_path=self.path, execute=True, token="test",
                             budget_usd="0.50", max_cost_per_image_usd="0.25",
                              limit=2,
                             rights_note="Original AI images permitted for my commercial use.")
            self.assertEqual(again["pending"], 0)
            self.assertEqual(request.call_count, 2)
            self.assertFalse(load_plan(self.path)["publicationApproved"])

    def test_rejects_nan_budget_and_invalid_limits(self):
        for amount in ("NaN", "Infinity", "-0.1", "999999"):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                generate(plan_path=self.path, budget_usd=amount)
        with self.assertRaisesRegex(ValueError, "positive"):
            generate(plan_path=self.path, limit=0)

    def test_request_rejects_invalid_model_without_network(self):
        with self.assertRaisesRegex(ValueError, "Model"):
            _request_image(model="https://attacker.invalid", prompt="hello",
                           token="test", timeout=30)

    def test_supported_sdk_routing_returns_valid_png(self):
        fake = types.ModuleType("huggingface_hub")
        client = Mock()
        client.text_to_image.return_value = Image.new("RGB", (1024, 576), (99, 170, 204))
        fake.InferenceClient = Mock(return_value=client)
        with patch.dict(sys.modules, {"huggingface_hub": fake}):
            content = _request_image(
                model="black-forest-labs/FLUX.1-schnell",
                prompt="Original purple bird on an original forest background",
                token="secret-token", timeout=20)
        self.assertEqual(Image.open(io.BytesIO(content)).size, (1024, 576))
        fake.InferenceClient.assert_called_once_with(
            api_key="secret-token", provider="auto", timeout=20)
        self.assertEqual(client.text_to_image.call_args.kwargs["width"], 1024)
        self.assertEqual(client.text_to_image.call_args.kwargs["height"], 576)

    def test_provider_error_is_sanitized(self):
        fake = types.ModuleType("huggingface_hub")
        fake.InferenceClient = Mock(side_effect=ValueError("SECRET_AUTH_DATA"))
        with patch.dict(sys.modules, {"huggingface_hub": fake}):
            with self.assertRaises(RuntimeError) as error:
                _request_image(model="owner/model", prompt="private original text",
                               token="secret-token", timeout=20)
        self.assertNotIn("SECRET_AUTH_DATA", str(error.exception))
        self.assertNotIn("private original text", str(error.exception))



if __name__ == "__main__":
    unittest.main()
