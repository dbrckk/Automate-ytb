# LIGHTNING MADE GLASS — original 2.5D animated short

Production: a 33-second portrait short at 1080×1920, 30 fps, original 128 BPM soundtrack and custom effects. A fast thunderstorm strike creates a branching natural glass tube (fulgurite) in silica-rich sand. The sequence follows the strike down into layered sand, dives inside the fused-glass tube, then orbits the excavated branching specimen. The timeline locks 12 named events in both audio and video: exactly 1,600 PCM samples per 30 fps frame at 48 kHz. Rendering uses original procedural multi-octave textures, moving camera maps, 3D-projected fulgurite branches, refractive 2.5D tunnel shaders, per-frame particles and lighting, and original synthesized stereo music and Foley. No images, stock footage, or licensed songs are incorporated.

The sequences are artistic **visualizations** of a real natural phenomenon, not a reconstruction of a documented individual lightning strike, a physical-speed simulation, or footage of a specimen. Lightning strikes silica-bearing sand or rock can fuse grains together to form delicate, often hollow, branching glass formations called fulgurites. Their real size and shape vary. The science was verified against US NPS and the Canadian meteorological service:

- https://home.nps.gov/articles/grsa-fulgurites.htm
- https://www.canada.ca/en/environment-climate-change/services/lightning/learn-more/fulgurites.html
- https://geology.utah.gov/map-pub/survey-notes/glad-you-asked/what-are-fulgurites-and-where-can-they-be-found/

## Generate

Requires Python 3.12, OpenCV, NumPy, Pillow, and `ffmpeg`/`ffprobe`. The program creates a storyboard contact sheet, a mastered AAC/H.264 MP4, and a QA JSON with cryptographic hash and cue clock mapping. All scratch and output files default to `build/fulgurite`, overridable by `FULGURITE_OUTPUT`.

```bash
FULGURITE_OUTPUT=build/fulgurite python production/fulgurite/render.py
```

The GitHub Actions workflow renders and verifies the complete release asset, including lossless byte-by-byte verification of public GitHub Release download. All captions are in English to match intended TikTok/Shorts audience; audio intentionally has no synthetic narrator to favor a high-energy reference-style kinetic score.