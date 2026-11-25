# Squeeze The Earth Into A Black Hole?

An original 32-second TikTok/YouTube Shorts animation: 960 unique frames in 2.5D at 1080×1920, 30 fps, with original procedural stereo audio at 48 kHz. Zero stock images, zero stock music. Eight events are locked to integer video frames [0,120,...,840], corresponding to [0,192000,...,1344000] audio samples. A continuous camera zoom accompanies a log-scale thought experiment, from Earth's physical radius (6,371 km) to the radius of the event horizon of an Earth-mass black hole (about 8.9 mm). A rotating planet, original textured geological matter, atmospheric haze, starfield, orbital lines, optical distortion, and an illustrative photon ring are generated entirely in code.

The compression is **hypothetical**, not a physical prediction. Earth cannot be compressed this way by any ordinary mechanism, and there is no implied matter supply or accretion disk; the visible bright disk is an artistic lensing illustration. Bodies are not drawn to identical scale across stages. Stages compare *radii* not diameters: Moon 1,737 km, Everest 8,848 m, Burj Khalifa 828 m, person 1.75 m, tennis ball 33.5 mm radius, coin 10 mm radius, and an Earth-mass Schwarzschild radius 8.87 mm.

## Build and verify

Requires Python 3.12, ffmpeg, numpy, Pillow, opencv-python-headless, scipy.

```bash
EARTH_BLACKHOLE_OUTPUT=build/earth-black-hole python production/earth-black-hole/render.py
```

The renderer exports an MP4 (H264/AAC), audio WAV, contact sheet, and JSON verification record, and fully decodes the final video and audio. GitHub Actions additionally verifies the direct public Release URL byte-for-byte. Voice-over intentionally omitted: the reference uses kinetic on-screen storytelling and scored music.

Scientific source: [NASA Imagine the Universe, Black Holes](https://imagine.gsfc.nasa.gov/science/objects/black_holes1.html), which states that compressing Earth's mass to a sphere of radius about 9 mm meets the black-hole condition.
