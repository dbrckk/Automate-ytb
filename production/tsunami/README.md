# The Wave You Can't See
A new original 30-second vertical short, 1080×1920 at 30 fps, made with procedural animation rather than stills. Eight named cues share one 30 fps video / 48 kHz audio clock. Intro: undersea earthquake; then ship on nearly imperceptible open-ocean wave, shoaling and growth across the continental shelf, and an illustrative flooding reveal. Original stereo score and generated Foley. The animation is illustrative, not a numerical tsunami forecast; displayed heights and topology are exaggerated for storytelling. The speed display follows v ≈ sqrt(gh) and decreases as depth decreases. No downloaded photos, copyrighted music, or stock video.

## Reproduce
Use Python 3.12, ffmpeg, numpy, Pillow, opencv-python-headless. Run `python production/tsunami/render.py` from repo root. Outputs MP4, contact sheet and source-produced WAV (WAV removed after export) in `build/tsunami` by default. GitHub Actions handles release, decoding and metadata validation and records the video in repository history.

Science source: [NOAA JetStream, Tsunami Propagation](https://www.noaa.gov/jetstream/tsunamis/tsunami-propagation).
