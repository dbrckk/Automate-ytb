"""Bounded, deterministic stereo score following PCM-derived story beats."""
from array import array
import math
from pathlib import Path
import sys
import wave

VERSION = "original-continuous-stereo-score-48k-v1"
RATE = 48000


def write_score(output: Path, boundaries: list[int], *, fps: int = 30):
    if (type(fps) is not int or not 1 <= fps <= 60
            or type(boundaries) is not list or not 3 <= len(boundaries) <= 13
            or any(type(n) is not int for n in boundaries)
            or boundaries[0] != 0 or boundaries[-1] > 180*fps
            or any(b <= a for a, b in zip(boundaries, boundaries[1:]))):
        raise ValueError("Score requires bounded contiguous beat boundaries")
    # Common tones and continuous oscillator phases avoid resetting at cuts.
    chords = ((130.8128, 195.9977, 261.6256),
              (130.8128, 164.8138, 220.0000),
              (130.8128, 164.8138, 195.9977))
    times = [f/fps for f in boundaries]
    total = round(times[-1]*RATE)
    with wave.open(str(output), "wb") as wav:
        wav.setparams((2, 2, RATE, 0, "NONE", "not compressed"))
        beat = 0
        for start in range(0, total, 4096):
            block = array("h")
            for index in range(start, min(start+4096, total)):
                t = index/RATE
                while beat+1 < len(times)-1 and t >= times[beat+1]:
                    beat += 1
                phase = min(1., (t-times[beat])/.7)
                blend = phase*phase*(3-2*phase)
                current = chords[min(2, beat*3//(len(times)-1))]
                previous = chords[min(2, max(0, beat-1)*3//(len(times)-1))]
                fade = min(1., t/.7, (times[-1]-t)/1.0)
                for channel in (0, 1):
                    def pad(chord):
                        return sum(math.sin(math.tau*f*t + channel*(j-1)*.12)
                                   * (.023 if j else .031) for j, f in enumerate(chord))
                    value = ((1-blend)*pad(previous)+blend*pad(current))*fade
                    block.append(round(max(-1., min(1., value))*32767))
            if sys.byteorder != "little":
                block.byteswap()
            wav.writeframesraw(block.tobytes())
