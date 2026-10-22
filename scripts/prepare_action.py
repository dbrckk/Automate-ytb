"""Convert GitHub Action fields into bounded input files."""
import json, os
from pathlib import Path
root=Path("build")
root.mkdir(exist_ok=True)
topic=os.getenv("YT_TOPIC","").strip()
angle=os.getenv("YT_ANGLE","").strip()
facts=json.loads(os.getenv("YT_FACTS_JSON","").strip() or "[]")
script=os.getenv("YT_SCRIPT","").strip()
if not isinstance(facts,list): raise SystemExit("facts_json must be a JSON list")
(root/"brief.json").write_text(json.dumps({"topic":topic,"angle":angle,"facts":facts},ensure_ascii=False,indent=2),encoding="utf8")
if script:
 if len(script)>17000:raise SystemExit("Script too long")
 (root/"script.txt").write_text(script,encoding="utf8")
print("Input prepared",len(facts),"sourced claims; custom script",bool(script))
