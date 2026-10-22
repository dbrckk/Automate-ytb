"""Fail a workflow if media or required metadata is missing."""
import json,subprocess,sys
from pathlib import Path
out=Path(sys.argv[1]);dirs=[x for x in out.iterdir() if x.is_dir()]
if len(dirs)!=1:raise SystemExit("Expected one job")
root=dirs[0];manifest=json.loads((root/"manifest.json").read_text(encoding="utf8"))
required=[root/"video-draft.mp4",root/"script.txt",root/"captions.srt",root/"youtube-metadata.json",root/"visual-generation-prompts.json"]+[root/path for path in manifest["thumbnails"]]
for p in required:
 if not p.is_file() or p.stat().st_size==0:raise SystemExit("Missing "+str(p))
duration=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(root/"video-draft.mp4")],text=True))
if not 29<=duration<=3700:raise SystemExit("Invalid duration")
if manifest["manualReviewRequired"] is not True or manifest["youtubeUploaded"] is not False:raise SystemExit("Missing review flags")
if len(manifest["scenes"])<2:raise SystemExit("Storyboard empty")
print("OK: complete export",round(duration,2),"seconds")
