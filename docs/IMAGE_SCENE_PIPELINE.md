# Image scene production kit (V1.1)

This feature builds on the original 150-shot planner derived from the complete user-provided reference video. It creates a **reviewable image batch**, not an imaginary "AI generated 150 images" promise.

## Android workflow

1. On GitHub, open **Actions > Prepare original image-scene batch > Run workflow**.
2. Enter an original topic, original recurring character, visual style, target duration and **your own complete narration**. At 900 seconds / 6 seconds per image, provide at least 150 distinct narration sentences (the planner will not invent facts or pad the runtime).
3. Download the **automate-ytb-scene-kit** artifact (JSON scene plan + JSONL prompts + audit report).
4. An external image service may generate the images after checking usage permissions, pricing and terms. **No service is called and no costs are incurred by preparing the kit.**
5. Once media is available, import each image, explicitly confirm rights, audit all files, and render a silent preview or supply licensed narration audio. The resulting MP4 is never uploaded automatically.

**Warning:** An Actions run on a public repository is not a secure storage location for unpublished scripts or sensitive information. Do not enter credentials or private information into workflow inputs.

## CLI examples

Create a plan (example assumes the narration is long enough):

~~~bash
python -m automate_ytb.scene_plan \
  --topic "Why do some animals glow?" \
  --script my-original-script.txt \
  --character "Original purple owl with round glasses and a scarf" \
  --duration 900 --shot-seconds 6 --output project/scene-plan.json

python -m automate_ytb.production prepare \
  --plan project/scene-plan.json --output project/image-prompts.jsonl
~~~

The JSONL records include exact IDs, timecodes, 16:9 image dimensions, original character/style bibles and textual prompts. Feed them into the permitted provider of your choice. Neither Star List listing nor a model's repository license establishes a right to commercial generated images.

Import images with an explicit declaration from the rights holder:

~~~bash
python -m automate_ytb.production ingest \
  --plan project/scene-plan.json --scene scene-001 \
  --image /path/to/my-art.png --provider original-illustrator \
  --rights-note "I created this original illustration and own its commercial usage rights." \
  --cost-usd 0.00 --confirm-rights

python -m automate_ytb.production audit --plan project/scene-plan.json

python -m automate_ytb.production render \
  --plan project/scene-plan.json --output project/render \
  --resolution 1080p --fps 24 --audio /path/to/approved-narration.wav
~~~

Each image is normalized to PNG, hashed, checked for basic format and dimensions, and stored as assets/scene-NNN.png. A changed image invalidates the earlier approval. Replacing an existing asset requires --replace.

### Rendering and costs

- **FFmpeg** creates per-shot video clips with gentle zoom movement and reuses cached clips when unchanged.
- Clips are concatenated to an MP4 preview. Output includes draft SRT subtitles, a render report and an audio flag.
- SRT is derived from planned text timecodes; it is **not** yet forced-aligned to the recorded narration.
- It records **user-supplied actual image costs** and can calculate a **quoted estimate**. These are not automatically measured provider charges.
- Rendering requires rights-confirmed images and matching checksums. It does **not** verify claims, music rights, provider terms or publication readiness.
- No YouTube publication, account access, unapproved downloading, provider API call, or secret is used.

### Commands

~~~text
python -m automate_ytb.production prepare --help
python -m automate_ytb.production ingest --help
python -m automate_ytb.production audit --help
python -m automate_ytb.production render --help
~~~

### Star List connections (review candidates, not bundled dependencies)

- Image/animation providers: StoryDiffusion, Toonflow, Viggle and the Hugging Face image models.
- Existing assembly engine: FFmpeg. Motion Canvas can complement generated images for vector animation.
- Optional voice: Kokoro or VoxCPM, with Whisper-based alignment in later releases.
- Orchestration concepts: MoneyPrinterTurbo and its Extended fork; avoid wholesale imports and license violations.
- Future providers must support explicit opt-in spending limits, retry/resume, stable scene IDs, provenance and final content review.

## Remaining gaps

The current version does **not** contact Higgsfield or any paid image service, auto-write original 15-minute scripts, create natural TTS, or perform YouTube uploads. These must be added with authenticated official APIs, disclosed price estimates, hard spending limits and review checkpoints.
