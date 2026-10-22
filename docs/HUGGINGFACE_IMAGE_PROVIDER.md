# Optional image provider: Hugging Face

\`automate_ytb.image_provider\` is an **opt-in adapter** for a Hugging Face inference endpoint. It is separate from the existing offline scene planner, image importer and FFmpeg renderer.

## Why this is not enabled by default

- Hugging Face routed inference requires a user-owned token and may require credits. Availability, model compatibility and pricing depend on the user's provider/account and can change.
- The adapter uses a **local preflight estimate**, not a real-time provider quote or a guaranteed financial spending cap. The configured amount is the user's assumed upper bound per image, not an API-enforced ceiling. **Use a provider-side spending cap or prepaid account before running.**
- No media is generated or charged in default dry-run mode.
- The model default is \`black-forest-labs/FLUX.1-schnell\`, selected as a candidate; the endpoint may not support that model for your account. Test a single image before a batch.
- Confirm applicable license and commercial usage rights for the model, output and upstream assets independently.
- The first version generates a single still image per scene. It does **not** guarantee consistent characters across scenes; a character reference adapter is still needed.

## Dry-run (no API requests)

~~~bash
python -m automate_ytb.image_provider \
  --plan project/scene-plan.json --limit 2 \
  --max-cost-per-image-usd 0.10 --budget-usd 0.20
~~~

The output reports the estimated number of pending images and the user-supplied upper-bound calculation.

## Explicit generation

Set \`HF_TOKEN\` privately in the execution environment. Never commit it, paste it into a public GitHub Actions input, or store it in the scene plan.

~~~bash
export HF_TOKEN='YOUR_PRIVATE_TOKEN'
python -m automate_ytb.image_provider \
  --plan project/scene-plan.json --limit 1 --execute \
  --max-cost-per-image-usd 0.10 --budget-usd 0.10 \
  --rights-note "I verified this model and its output usage terms for my intended commercial use."
~~~

**Warning:** The provider may charge more than your entered assumed cost. The adapter cannot stop external billing at a hard monetary threshold. \`--budget-usd\` prevents runs exceeding your *declared estimate*, not the provider's actual charges. Set limits in your provider account.

If the provider returns an error, existing approved scenes are preserved. On retry, the adapter skips ready scenes. A successfully returned image is imported as a normalized PNG with source hash and rights note; its recorded cost is the **user-supplied estimate**.

No YouTube upload or publication occurs.
