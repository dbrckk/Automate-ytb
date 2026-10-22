"""Optional, budget-limited Hugging Face image provider for reviewed scene plans.

No tokens are logged or written to disk. Dry-run is the default; explicit --execute
and a finite hard budget are required before any API call.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import io
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

from .production import audit, ingest, load_plan

DEFAULT_MODEL = "black-forest-labs/FLUX.1-schnell"
ENDPOINT = "https://router.huggingface.co/hf-inference/models/"
MAX_IMAGE_BYTES = 25 * 1024 * 1024
MAX_RESPONSE_BYTES = MAX_IMAGE_BYTES + 1


def money(value: str) -> Decimal:
    try:
        n = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Invalid monetary amount") from None
    if not n.is_finite() or n < 0 or n > 10000:
        raise ValueError("Amount must be finite, nonnegative and <=10000")
    return n.quantize(Decimal("0.0001"))


def _request_image(*, model: str, prompt: str, token: str, timeout: int) -> bytes:
    if not model or len(model) > 180 or any(c not in
             "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-/"
             for c in model) or model.count("/") != 1:
        raise ValueError("Model must be a single Hugging Face namespace/model identifier")
    payload = json.dumps({"inputs": prompt, "parameters": {"num_inference_steps": 4}}).encode()
    request = urllib.request.Request(
        ENDPOINT + model, data=payload, method="POST",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "image/png,image/jpeg,image/webp",
            "User-Agent": "AutomateYTB/0.2",
        })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise RuntimeError(f"Image provider returned HTTP {response.status}")
            content_type = response.headers.get("Content-Type", "").split(";")[0].lower()
            if content_type not in ("image/png", "image/jpeg", "image/webp",
                                    "application/octet-stream"):
                raise RuntimeError(f"Image provider returned non-image content ({content_type})")
            content = response.read(MAX_RESPONSE_BYTES)
            if len(content) > MAX_IMAGE_BYTES:
                raise RuntimeError("Provider image exceeds 25MB limit")
            return content
    except urllib.error.HTTPError as error:
        # Avoid leaking provider responses, tokens or private prompts.
        raise RuntimeError(f"Image provider returned HTTP {error.code}") from None
    except urllib.error.URLError:
        raise RuntimeError("Image provider network request failed") from None


def generate(*, plan_path: Path, model: str = DEFAULT_MODEL,
             limit: int | None = None, execute: bool = False,
             budget_usd: str = "0", max_cost_per_image_usd: str = "0",
             rights_note: str = "", token: str | None = None,
             timeout: int = 120) -> dict:
    data = load_plan(plan_path)
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise ValueError("Scene limit must be a positive integer")
    if not 10 <= timeout <= 600:
        raise ValueError("Timeout must be between 10 and 600 seconds")
    scenes = data["scenes"][:limit]
    quote = money(max_cost_per_image_usd)
    budget = money(budget_usd)
    already = audit(plan_path)
    done = {r["sceneId"] for r in already["details"] if r["status"] == "ready"}
    pending = [s for s in scenes if s["id"] not in done]
    projected = quote * len(pending)
    result = {
        "provider": "huggingface-inference", "model": model,
        "mode": "execute" if execute else "dry-run",
        "total": len(scenes), "alreadyReady": len(scenes) - len(pending),
        "pending": len(pending), "maxUnitCostUsd": str(quote),
        "projectedUpperBoundUsd": str(projected),
        "budgetUsd": str(budget), "generated": 0,
        "publicationApproved": False,
    }
    if not execute:
        return result
    if not rights_note.strip() or len(rights_note.strip()) < 12:
        raise ValueError("Execution requires a documented rights/license statement")
    if not token:
        token = os.environ.get("HF_TOKEN")
    if not token:
        raise ValueError("HF_TOKEN required for provider execution")
    if quote <= 0 or budget <= 0 or projected > budget:
        raise ValueError("Positive per-image cost ceiling and sufficient hard budget required")
    if len(pending) > 150:
        raise ValueError("Limit each provider execution to 150 pending images")
    for scene in pending:
        # Verify again on each step: another process may have modified the plan.
        current = load_plan(plan_path)
        target = next(x for x in current["scenes"] if x["id"] == scene["id"])
        if target.get("assetApproved"):
            raise ValueError("Existing approved image must be manually reviewed, not replaced")
        content = _request_image(model=model, prompt=scene["imagePrompt"],
                                 token=token, timeout=timeout)
        import tempfile
        with tempfile.TemporaryDirectory(prefix="automate-ytb-image-") as temp:
            image = Path(temp) / "generated.png"
            image.write_bytes(content)
            ingest(plan_path=plan_path, scene_id=scene["id"], image_path=image,
                   provider="hf-inference", rights_note=rights_note,
                   cost_usd=str(quote), rights_confirmed=True)
        result["generated"] += 1
    result["remainingBudgetUsd"] = str(budget - quote * result["generated"])
    result["recordedCostsAreEstimates"] = True
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Explicitly budgeted Hugging Face scene generation")
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--execute", action="store_true", help="Send real provider requests")
    parser.add_argument("--budget-usd", default="0")
    parser.add_argument("--max-cost-per-image-usd", default="0")
    parser.add_argument("--rights-note", default="")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(generate(
            plan_path=args.plan, model=args.model, limit=args.limit,
            execute=args.execute, budget_usd=args.budget_usd,
            max_cost_per_image_usd=args.max_cost_per_image_usd,
            rights_note=args.rights_note, timeout=args.timeout
        ), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, RuntimeError, OSError) as error:
        print("ERROR:", error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
